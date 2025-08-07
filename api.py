import json
import logging
import sentry_sdk
import asyncio
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

# Loyihadagi kerakli modullarni import qilamiz
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.database.repositories import ChannelRepository, SchedulerRepository
from src.bot.services.scheduler_service import SchedulerService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# --- Sentry Sozlamasi ---
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

# --- Asosiy sozlamalar ---
app = FastAPI()
bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
db_pool = None
scheduler = None
scheduler_service = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Event Handlers (DB va Scheduler uchun) ---
@app.on_event("startup")
async def startup_event():
    global db_pool, scheduler, scheduler_service
    db_pool = await create_pool()

    db_url_str = settings.DATABASE_URL.unicode_string()
    sqlalchemy_url = db_url_str.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = {'default': SQLAlchemyJobStore(url=sqlalchemy_url)}
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    scheduler_service = SchedulerService(scheduler, SchedulerRepository(db_pool))
    scheduler.start()
    
    logger.info("FastAPI: Database pool and Scheduler created.")

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler and scheduler.running:
        scheduler.shutdown()
    if db_pool:
        await db_pool.close()
    logger.info("FastAPI: Database pool and Scheduler closed.")

# --- CORS Middleware (YANGI, TO'G'RI VERSIYASI) ---
# Veb-ilovamiz ishlayotgan aniq manzilni ko'rsatamiz
origins = [
    "https://fuzzy-adventure-5vgrx54q557f7vww-5173.app.github.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Endi "*" o'rniga aniq ro'yxatni ishlatamiz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Modellar ---
class AddChannelRequest(BaseModel):
    channel_name: str
    user_id: int

class Button(BaseModel):
    text: str
    url: str

class CreatePostRequest(BaseModel):
    channel_id: int
    text: Optional[str] = None
    schedule_time: datetime
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    inline_buttons: Optional[List[Button]] = []

# --- API Endpoints ---
@app.post("/api/v1/channels")
async def add_channel_endpoint(request: AddChannelRequest):
    # ... Bu funksiya avvalgidek qoladi ...
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not initialized")
    channel_repo = ChannelRepository(db_pool)
    logger.info(f"API: Received request to add channel: {request.channel_name} for user: {request.user_id}")
    if not request.channel_name or not request.channel_name.startswith('@'):
        raise HTTPException(status_code=400, detail="Invalid format. Channel username must start with @")
    try:
        chat = await bot.get_chat(chat_id=request.channel_name, request_timeout=10)
        bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot.id, request_timeout=10)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            raise HTTPException(status_code=403, detail=f"Bot is not an admin in {request.channel_name}.")
        await channel_repo.create_channel(
            channel_id=chat.id, channel_name=chat.title, admin_id=request.user_id
        )
        return {"success": True, "message": f"Channel '{chat.title}' added successfully!"}
    except asyncio.TimeoutError:
        logger.error(f"API add_channel: Telegram API timed out for '{request.channel_name}'")
        raise HTTPException(status_code=504, detail="Could not connect to Telegram servers.")
    except TelegramBadRequest:
        logger.warning(f"API add_channel: Channel '{request.channel_name}' not found.")
        raise HTTPException(status_code=404, detail=f"Channel '{request.channel_name}' not found.")
    except Exception as e:
        logger.error(f"API Error in add_channel_endpoint: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- YANGI ENDPOINT'LAR ---
@app.get("/api/v1/initial-data/{user_id}")
async def get_initial_data(user_id: int):
    """Foydalanuvchi uchun barcha kerakli ma'lumotlarni (kanallar, postlar) qaytaradi."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    channel_repo = ChannelRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    
    user_channels = await channel_repo.get_user_channels(user_id)
    pending_posts = await scheduler_repo.get_pending_posts_by_user(user_id)
    
    return {
        "channels": [{"id": str(ch["channel_id"]), "name": ch["channel_name"]} for ch in user_channels],
        "posts": [
            {
                "id": post["post_id"], "text": post["text"] or "",
                "schedule_time": post["schedule_time"].isoformat(),
                "channel_name": post["channel_name"],
                "file_id": post["file_id"], "file_type": post["file_type"],
                "inline_buttons": json.loads(post["inline_buttons"]) if post["inline_buttons"] else []
            } for post in pending_posts
        ]
    }

@app.post("/api/v1/posts")
async def create_post_endpoint(request: CreatePostRequest):
    """Yangi postni rejalashtiradi."""
    if not scheduler_service:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    await scheduler_service.schedule_post(
        channel_id=request.channel_id,
        text=request.text,
        schedule_time=request.schedule_time,
        file_id=request.file_id,
        file_type=request.file_type,
        inline_buttons=[btn.dict() for btn in request.inline_buttons] if request.inline_buttons else None
    )
    return {"success": True, "message": "Post scheduled successfully!"}

@app.delete("/api/v1/posts/{post_id}")
async def delete_post_endpoint(post_id: int):
    """Rejalashtirilgan postni o'chiradi."""
    if not scheduler_service:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
        
    await scheduler_service.delete_post(post_id)
    return {"success": True, "message": "Post deleted successfully!"}
