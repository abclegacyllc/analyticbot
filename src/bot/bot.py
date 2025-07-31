from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
import redis.asyncio as redis
from .config import BOT_TOKEN, REDIS_URL
from src.bot.middlewares.i18n import i18n_middleware

# Redis connection
redis_conn = redis.from_url(REDIS_URL)
storage = RedisStorage(redis=redis_conn)

# Bot and Dispatcher instances
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# Register I18nMiddleware
i18n_middleware.setup(dispatcher=dp)
