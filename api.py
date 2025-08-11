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
from bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    SchedulerRepository,
    PlanRepository,
)
from bot.models.twa import (
    AddChannelRequest,
    Channel,
    InitialDataResponse,
    MessageResponse,
    Plan,
    SchedulePostRequest,
    ScheduledPost,
    User,
    ValidationErrorResponse,
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
        content_type = file.content_type
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
    user_id = user_data["id"]
    username = user_data.get("username")

    # Ensure the user exists in the database
    await user_repo.create_user(user_id, username)

    # Fetch plan information
    plan = None
    plan_name = await user_repo.get_user_plan_name(user_id)
    if plan_name:
        plan_row = await plan_repo.get_plan_by_name(plan_name)
        if plan_row:
            plan = Plan(
                name=plan_row.get("plan_name") or plan_row.get("name"),
                max_channels=plan_row["max_channels"],
                max_posts_per_month=plan_row["max_posts_per_month"],
            )

    # Fetch channels and scheduled posts
    channel_rows = await channel_repo.get_user_channels(user_id)
    channels = [
        Channel(id=row["channel_id"], channel_name=row.get("channel_name") or row.get("title", ""))
        for row in (channel_rows or [])
    ]
    post_rows = await scheduler_repo.get_scheduled_posts_by_user(user_id)
    scheduled_posts = [
        ScheduledPost(
            id=row["id"],
            channel_id=row["channel_id"],
            text=row.get("post_text"),
            media_id=row.get("media_id"),
            media_type=row.get("media_type"),
            scheduled_at=row.get("schedule_time"),
            buttons=row.get("inline_buttons"),
        )
        for row in (post_rows or [])
    ]

    user = User(id=user_id, username=username)
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
    channel_data = await guard_service.check_bot_is_admin(channel_username, user_id)

    return Channel(id=channel_data["channel_id"], channel_name=channel_data.get("channel_name") or channel_data.get("title", ""))

@app.post("/api/v1/schedule-post", response_model=ScheduledPost)
async def schedule_post(
    request: SchedulePostRequest,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    user_id = user_data['id']
    await subscription_service.check_post_limit(user_id)
    
    post_id = await scheduler_repo.create_scheduled_post(
        user_id=user_id,
        channel_id=request.channel_id,
        post_text=request.text,
        schedule_time=request.scheduled_at,
        media_id=request.media_id,
        media_type=request.media_type,
        inline_buttons=[button.model_dump() for button in request.buttons] if request.buttons else None,
    )

    return ScheduledPost(
        id=post_id,
        channel_id=request.channel_id,
        text=request.text,
        media_id=request.media_id,
        media_type=request.media_type,
        scheduled_at=request.scheduled_at,
        buttons=request.buttons,
    )

@app.delete("/api/v1/posts/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: int,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    scheduler_repo: Annotated[SchedulerRepository, Depends(get_scheduler_repo)],
):
    user_id = user_data['id']
    success = await scheduler_repo.delete_scheduled_post(post_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or you don't have permission.")

    return MessageResponse(message="Post deleted successfully")

@app.delete("/api/v1/channels/{channel_id}", response_model=MessageResponse)
async def delete_channel(
    channel_id: int,
    user_data: Annotated[dict, Depends(get_validated_user_data)],
    channel_repo: Annotated[ChannelRepository, Depends(get_channel_repo)],
):
    user_id = user_data['id']
    channel_row = await channel_repo.get_channel_by_id(channel_id)
    if not channel_row or channel_row["admin_id"] != user_id:
        raise HTTPException(status_code=404, detail="Channel not found or you don't have permission.")

    success = await channel_repo.delete_channel(channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found or you don't have permission.")

    return MessageResponse(message="Channel deleted successfully")