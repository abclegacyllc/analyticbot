from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
import redis.asyncio as redis

# Import the single settings object instead of individual variables
from .config import settings
from src.bot.middlewares.i18n import i18n_middleware

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL.unicode_string())
storage = RedisStorage(redis=redis_conn)

# Bot and Dispatcher instances
# Use .get_secret_value() to access the actual token from SecretStr
bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# Register I18nMiddleware
i18n_middleware.setup(dispatcher=dp)
