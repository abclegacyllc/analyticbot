import logging
import sentry_sdk
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from asyncpg import Pool

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

# Loyihadagi kerakli modullarni import qilamiz
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.database.repositories import ChannelRepository, SchedulerRepository, UserRepository

# Sentry sozlamasi
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

# Asosiy sozlamalar
app = FastAPI(title="AnalyticBot TWA Backend")
db_pool: Optional[Pool] = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event Handlers (DB ulanishini boshqarish uchun)
@app.on_event("startup")
async def startup_event():
    global db_pool
    db_pool = await create_pool()
    logger.info("FastAPI: Database pool created.")

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
    logger.info("FastAPI: Database pool closed.")

# Dependency (har bir so'rov uchun DB pool'ni ta'minlaydi)
def get_db_pool():
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database connection is not available")
    return db_pool

# CORS Middleware (TWA bilan bog'lanish uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Production'da aniq manzilga o'zgartirish kerak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Modellar (so'rovlar uchun) ---
class AddChannelRequest(BaseModel):
    username: str

class CreatePostRequest(BaseModel):
    user_id: int
    channel_id: int
    post_text: Optional[str] = None
    schedule_time: datetime
    media_id: Optional[str] = None
    media_type: Optional[str] = None
    inline_buttons: Optional[Dict[str, Any]] = None

# --- API Endpoints ---
@app.post("/api/v1/media/upload", tags=["Media"])
async def upload_media_file(file: UploadFile = File(...)):
    """TWA'dan media faylni qabul qilib, uni "ombor" kanalga yuboradi va file_id qaytaradi."""
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    content_type = file.content_type
    
    try:
        if content_type and content_type.startswith("image/"):
            media_type = "photo"
            sent_message = await bot.send_photo(chat_id=settings.STORAGE_CHANNEL_ID, photo=file.file)
            file_id = sent_message.photo[-1].file_id
        elif content_type and content_type.startswith("video/"):
            media_type = "video"
            sent_message = await bot.send_video(chat_id=settings.STORAGE_CHANNEL_ID, video=file.file)
            file_id = sent_message.video.file_id
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
        
        return {"ok": True, "file_id": file_id, "media_type": media_type}
    except TelegramAPIError as e:
        logger.error(f"Telegram API error while uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Telegram API error: {e.message}")
    finally:
        await bot.session.close()

@app.get("/api/v1/initial-data/{user_id}", tags=["TWA"])
async def get_initial_data(user_id: int, pool: Pool = Depends(get_db_pool)):
    """TWA uchun boshlang'ich ma'lumotlarni (kanallar va rejalashtirilgan postlar) qaytaradi."""
    channel_repo = ChannelRepository(pool)
    scheduler_repo = SchedulerRepository(pool)
    
    user_channels = await channel_repo.get_user_channels(user_id)
    pending_posts = await scheduler_repo.get_scheduled_posts_by_user(user_id)
    
    return {
        "ok": True,
        "data": {
            "channels": [{"id": ch["id"], "title": ch["title"], "username": ch["username"]} for ch in user_channels],
            "posts": [dict(post) for post in pending_posts]
        }
    }

@app.post("/api/v1/channels/{user_id}", tags=["Channels"])
async def add_channel_endpoint(user_id: int, request: AddChannelRequest, pool: Pool = Depends(get_db_pool)):
    """Yangi kanal qo'shadi, botni tekshiradi va bazaga saqlaydi."""
    channel_repo = ChannelRepository(pool)
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    
    try:
        if not request.username or not request.username.startswith('@'):
            raise HTTPException(status_code=400, detail="Invalid format. Channel username must start with @")

        chat = await bot.get_chat(chat_id=request.username)
        bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot.id)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            raise HTTPException(status_code=403, detail=f"Bot is not an admin in {request.username}.")

        await channel_repo.create_channel(user_id=user_id, channel_id=chat.id, title=chat.title, username=chat.username)
        return {"ok": True, "message": f"Channel '{chat.title}' added successfully!"}
    
    except TelegramBadRequest:
        raise HTTPException(status_code=404, detail=f"Channel '{request.username}' not found or bot has no access.")
    except Exception as e:
        logger.error(f"API Error in add_channel_endpoint: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")
    finally:
        await bot.session.close()

@app.post("/api/v1/posts", tags=["Posts"])
async def create_post_endpoint(request: CreatePostRequest, pool: Pool = Depends(get_db_pool)):
    """Yangi postni rejalashtiradi."""
    scheduler_repo = SchedulerRepository(pool)
    
    try:
        post_id = await scheduler_repo.create_scheduled_post(
            user_id=request.user_id,
            channel_id=request.channel_id,
            post_text=request.post_text,
            schedule_time=request.schedule_time,
            media_id=request.media_id,
            media_type=request.media_type,
            inline_buttons=request.inline_buttons
        )
        return {"ok": True, "message": "Post scheduled successfully!", "post_id": post_id}
    except Exception as e:
        logger.error(f"API Error in create_post_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule post.")


@app.delete("/api/v1/posts/{post_id}/{user_id}", tags=["Posts"])
async def delete_post_endpoint(post_id: int, user_id: int, pool: Pool = Depends(get_db_pool)):
    """Rejalashtirilgan postni o'chiradi."""
    scheduler_repo = SchedulerRepository(pool)
    
    success = await scheduler_repo.delete_scheduled_post(post_id=post_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or you don't have permission to delete it.")
        
    return {"ok": True, "message": "Post deleted successfully!"}