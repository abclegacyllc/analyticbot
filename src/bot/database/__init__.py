import asyncpg
# Import the single settings object
from src.bot.config import settings

async def create_pool():
    # This function creates the database connection pool
    # Pydantic validates the URL format, so we can use it with confidence
    return await asyncpg.create_pool(settings.DATABASE_URL.unicode_string())
