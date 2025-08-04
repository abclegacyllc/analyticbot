from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Import the single settings object
from .config import settings
from src.bot.middlewares.i18n import i18n_middleware

# Bot and Dispatcher instances are created here, but storage is configured later.
bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Register I18nMiddleware
i18n_middleware.setup(dispatcher=dp)
