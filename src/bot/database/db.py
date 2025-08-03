import asyncpg
from src.bot.config import settings

async def create_pool() -> asyncpg.Pool:
    """
    Creates and returns a connection pool to the PostgreSQL database.
    """
    return await asyncpg.create_pool(
        dsn=settings.DATABASE_URL.unicode_string(),
        min_size=5,  # The minimum number of connections in the pool
        max_size=20, # The maximum number of connections in the pool
    )
