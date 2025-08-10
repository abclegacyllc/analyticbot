import logging
from typing import Annotated

from aiogram import Bot
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.bot.config import Config
from src.bot.container import container  # DI konteynerini import qilamiz
from src.bot.database.models import Channel, ScheduledPost, User, Plan
from src.bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    SchedulerRepository,
    PlanRepository,
)
from src.bot.models.twa import (
    InitialDataResponse,
    AddChannelRequest,
    SchedulePostRequest,
    ValidationErrorResponse,
    MessageResponse
)
from src.bot.services import (
    GuardService,
    SubscriptionService,
)
# initData'ni tekshirish uchun yangi servisni import qilamiz
from src.bot.services.auth_service import validate_init_data

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# --- DI konteyneridan foydalanadigan funksiyalar ---

def get_config() -> Config:
    return container.resolve(Config)

def get_user_repo() -> UserRepository:
    return container.resolve(UserRepository)

def get_channel_repo() -> ChannelRepository:
    return container.resolve(ChannelRepository)

def get_plan_repo() -> PlanRepository:
    return container.resolve(PlanRepository)

def get_scheduler_repo() -> SchedulerRepository:
    return container.resolve(SchedulerRepository)

def get_subscription_service() -> SubscriptionService:
    return container.resolve(SubscriptionService)

def get_guard_service() -> GuardService:
    # Bu servis Bot obyektiga bog'liq, shuning uchun uni alohida yaratamiz
    config = get_config()
    bot_instance = Bot(token=config.bot.token, parse_mode="HTML")
    # Servisni konteynerdan olib, bot obyektini unga o'rnatamiz.
    # Yoki GuardService'ni ham konteynerga bog'liqlik bilan registratsiya qilish mumkin.
    # Hozircha shu usul oddiyroq.
    return GuardService(bot=bot_instance, channel_repo=get_channel_repo())

# --- TWA Autentifikatsiya Dependency ---

async def get_validated_user_data(
    authorization: Annotated[str, Header()]
) -> dict:
    """
    Har bir so'rovdan oldin `initData`'ni tekshiradi va tasdiqlangan
    foydalanuvchi ma'lumotlarini (словарь ko'rinishida) qaytaradi.
    """
    if not authorization or not authorization.startswith("TWA "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme.")
    
    init_data = authorization.split("TWA ", 1)[1]
    if not init_data:
        raise HTTPException(status_code=401, detail="initData is missing.")

    config = get_config()
    try:
        user_data = validate_init_data(init_data, config.bot.token)
        return user_data
    except HTTPException as e:
        # Validatsiya xatoligini to'g'ridan-to'g'ri qaytaramiz
        raise e
    except Exception as e:
        log.error(f"Could not validate initData: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during validation.")


# --- FastAPI ilovasi ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("API is starting up...")
    yield
    log.info("API is shutting down...")


app = FastAPI(
    lifespan=lifespan,
    responses={422: {"description": "Validation Error", "model": ValidationErrorResponse}},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production uchun buni aniqroq qiling
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints (Yangilangan) ---

@app.post("/api/v1/media/upload", tags=["Media"])
async def upload_media_file(
    file: UploadFile = File(...)
):
    """
    TWA'dan media faylni qabul qilib, uni "ombor" kanalga yuboradi va file_id qaytaradi.
    Bu endpointga initData tekshiruvi shart emas, chunki u faqat faylni saqlaydi.
    """
    config = get_config()
    bot = Bot(token=config.bot.token.get_secret_value())
    content_type = file.content_type
    
    try:
        if content_type and content_type.startswith("image/"):
            media_type = "photo"
            sent_message = await bot.send_photo(chat_id=config.bot.storage_channel_id, photo=file.file)
            file_id = sent_message.photo[-1].file_id
        elif content_type and content_type.startswith("video/"):
            media_type = "video"
            sent_message = await bot.send_video(chat_id=config.bot.storage_channel_id, video=file.file)
            file_id = sent_message.video.file_id
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
        
        return {"ok": True, "file_id": file_id, "media_type": media_type}
    except TelegramAPIError as e:
        log.error(f"Telegram API error while uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Telegram API error: {e.args[0]}")
    finally:
        await bot.session.close()

@app.get("/api/v1/initial-data", response_model=InitialDataResponse)
async def get_initial_data(
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    channel_repo: Annotated[ChannelRepository, Depends(get_channel_repo)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
    plan_repo: Annotated[PlanRepository, Depends(get_plan_repo)],
):
    """Foydalanuvchi uchun barcha boshlang'ich ma'lumotlarni qaytaradi."""
    user_id = user_data['id']
    user: User = await user_repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please restart the bot.")

    channels: list[Channel] = await channel_repo.get_user_channels(user_id)
    scheduled_posts: list[ScheduledPost] = await scheduler_repo.get_user_scheduled_posts(user_id)
    plan: Plan = await plan_repo.get_plan_by_id(user.plan_id)

    return InitialDataResponse(
        user=user,
        plan=plan,
        channels=channels,
        scheduled_posts=scheduled_posts,
    )


@app.post("/api/v1/channels", response_model=Channel)
async def add_channel(
    request_data: AddChannelRequest,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    channel_repo: Annotated[ChannelRepository, Depends(get_channel_repo)],
    guard_service: Annotated[GuardService, Depends(get_guard_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Yangi kanal qo'shadi."""
    user_id = user_data['id']
    channel_username = request_data.channel_username.strip()

    if not channel_username.startswith("@"):
        channel_username = f"@{channel_username}"

    # Cheklovlarni tekshirish
    await subscription_service.check_channel_limit(user_id)
    await guard_service.check_bot_is_admin(channel_username, user_id)

    channel = await channel_repo.add_channel(user_id, channel_username)
    return channel


@app.post("/api/v1/schedule-post", response_model=ScheduledPost)
async def schedule_post(
    request: SchedulePostRequest,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Postni rejalashtiradi."""
    user_id = user_data['id']
    await subscription_service.check_post_limit(user_id)
    
    post = await scheduler_repo.create_scheduled_post(
        user_id=user_id,
        channel_id=request.channel_id,
        text=request.text,
        media_type=request.media_type,
        media_id=request.media_id,
        scheduled_at=request.scheduled_at,
        buttons=request.buttons
    )
    return post


@app.delete("/api/v1/posts/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: int,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
):
    """Rejalashtirilgan postni o'chiradi."""
    user_id = user_data['id']
    post = await scheduler_repo.get_scheduled_post(post_id)
    if not post or post.user_id != user_id:
        raise HTTPException(status_code=404, detail="Post not found or you don't have permission.")
    
    await scheduler_repo.delete_scheduled_post(post_id)
    return MessageResponse(message="Post deleted successfully")


@app.delete("/api/v1/channels/{channel_id}", response_model=MessageResponse)
async def delete_channel(
    channel_id: int,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    channel_repo: Annotated[ChannelRepository, Depends(get_channel_repo)],
):
    """Kanalni o'chiradi."""
    user_id = user_data['id']
    channel = await channel_repo.get_channel_by_id(channel_id)
    if not channel or channel.user_id != user_id:
        raise HTTPException(status_code=404, detail="Channel not found or you don't have permission.")
    
    await channel_repo.delete_channel(channel_id)
    return MessageResponse(message="Channel deleted successfully")