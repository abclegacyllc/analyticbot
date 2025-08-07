import logging
import sentry_sdk
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

# Loyihadagi kerakli modullarni import qilamiz
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.database.repositories import ChannelRepository

# Sentry'ni bu yerda ham ishga tushiramiz
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

# Asosiy sozlamalar
app = FastAPI()
bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
db_pool = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API server ishga tushganda va o'chganda ma'lumotlar bazasiga ulanish/uzish
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

# CORS (Cross-Origin Resource Sharing) sozlamasi
# Bu veb-ilovaning API'ga murojaat qilishiga ruxsat beradi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Rivojlantirish uchun. Ishga tushganda aniq manzil qo'yish kerak.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API so'rovi uchun model
class AddChannelRequest(BaseModel):
    channel_name: str
    user_id: int

# API endpoint'i (veb-ilova murojaat qiladigan manzil)
@app.post("/api/v1/channels")
async def add_channel_endpoint(request: AddChannelRequest):
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not initialized")

    channel_repo = ChannelRepository(db_pool)
    
    logger.info(f"API: Received request to add channel: {request.channel_name} for user: {request.user_id}")
    
    if not request.channel_name or not request.channel_name.startswith('@'):
        raise HTTPException(status_code=400, detail="Invalid format. Channel username must start with @")
    
    try:
        # --- 2. MUHIM O'ZGARISH ---
        # Telegram API'ga 10 soniyalik timeout bilan so'rov yuboramiz
        chat = await bot.get_chat(chat_id=request.channel_name, request_timeout=10)
        bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot.id, request_timeout=10)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            raise HTTPException(status_code=403, detail=f"Bot is not an admin in {request.channel_name}.")

        # Ma'lumotlar bazasiga yozish
        await channel_repo.create_channel(
            channel_id=chat.id,
            channel_name=chat.title,
            admin_id=request.user_id
        )
        
        return {"success": True, "message": f"Channel '{chat.title}' added successfully!"}

    except asyncio.TimeoutError:
        logger.error(f"API add_channel: Telegram API timed out for '{request.channel_name}'")
        raise HTTPException(status_code=504, detail="Could not connect to Telegram servers. Please try again later.")
    except TelegramBadRequest:
        logger.warning(f"API add_channel: Channel '{request.channel_name}' not found.")
        raise HTTPException(status_code=404, detail=f"Channel '{request.channel_name}' not found or the bot does not have access to it.")
    except Exception as e:
        logger.error(f"API Error in add_channel_endpoint: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
