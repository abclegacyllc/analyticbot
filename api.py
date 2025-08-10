import logging
from typing import Annotated
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Imports updated for the new project structure (without 'src')
from bot.config import settings, Settings
from bot.container import container
from bot.database.models import Channel, ScheduledPost, User, Plan
from bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    SchedulerRepository,
    PlanRepository,
)
from bot.models.twa import (
    InitialDataResponse,
    AddChannelRequest,
    SchedulePostRequest,
    ValidationErrorResponse,
    MessageResponse,
)
from bot.services import (
    GuardService,
    SubscriptionService,
)
from bot.services.auth_service import validate_init_data

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# --- FastAPI Dependencies ---

def get_settings() -> Settings:
    """Returns the application settings instance."""
    return settings

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
    return container.resolve(GuardService)

async def get_validated_user_data(
    authorization: Annotated[str, Header()],
    current_settings: Annotated[Settings, Depends(get_settings)]
) -> dict:
    """
    Validates the initData string from a TWA and returns the user data.
    """
    if not authorization or not authorization.startswith("TWA "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme.")
    
    init_data = authorization.split("TWA ", 1)[1]
    if not init_data:
        raise HTTPException(status_code=401, detail="initData is missing.")

    try:
        user_data = validate_init_data(init_data, current_settings.BOT_TOKEN.get_secret_value())
        return user_data
    except Exception as e:
        log.error(f"Could not validate initData: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid initData.")


# --- FastAPI Application ---

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

@app.post("/api/v1/media/upload", tags=["Media"])
async def upload_media_file(
    # --- SYNTAXERROR TUZATILDI: Argumentlar tartibi to'g'rilandi ---
    current_settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...)
):
    bot = Bot(token=current_settings.BOT_TOKEN.get_secret_value())
    
    try:
        if content_type and content_type.startswith("image/"):
            media_type = "photo"
            sent_message = await bot.send_photo(chat_id=current_settings.STORAGE_CHANNEL_ID, photo=file.file)
            file_id = sent_message.photo[-1].file_id
        elif content_type and content_type.startswith("video/"):
            media_type = "video"
            sent_message = await bot.send_video(chat_id=current_settings.STORAGE_CHANNEL_ID, video=file.file)
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
    guard_service: Annotated[GuardService, Depends(get_guard_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    user_id = user_data['id']
    channel_username = request_data.channel_username.strip()

    if not channel_username.startswith("@"):
        channel_username = f"@{channel_username}"

    await subscription_service.check_channel_limit(user_id)
    channel = await guard_service.check_bot_is_admin(channel_username, user_id)
    
    return channel

@app.post("/api/v1/schedule-post", response_model=ScheduledPost)
async def schedule_post(
    request: SchedulePostRequest,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
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
    user_id = user_data['id']
    channel = await channel_repo.get_channel_by_id(channel_id)
    if not channel or channel.user_id != user_id:
        raise HTTPException(status_code=404, detail="Channel not found or you don't have permission.")
    
    await channel_repo.delete_channel(channel_id)
    return MessageResponse(message="Channel deleted successfully")
