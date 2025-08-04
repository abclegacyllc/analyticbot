# FILE: src/bot/bot.py

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Import the single settings object
from .config import settings

# Only the Bot instance is created here.
# The Dispatcher will be created in run_bot.py where it belongs.
bot = Bot(
    token=settings.BOT_TOKEN.get_secret_value(), 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
