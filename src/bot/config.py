import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Multi-language support
SUPPORTED_LOCALES = ["en", "uz"]
DEFAULT_LOCALE = "uz"
