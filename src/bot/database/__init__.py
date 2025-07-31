import asyncpg
from src.bot.config import DATABASE_URL

async def create_pool():
    # This function creates the database connection pool
    return await asyncpg.create_pool(DATABASE_URL)
