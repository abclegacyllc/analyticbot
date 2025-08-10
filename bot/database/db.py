import asyncpg
from bot.config import settings

async def create_pool():
    """
    Creates a connection pool to the PostgreSQL database.
    
    Converts the Pydantic PostgresDsn object to a string before passing it
    to asyncpg to ensure correct connection parsing.
    """
    # Pydantic v2'dagi maxsus URL obyektini oddiy matnga (string) o'giramiz
    dsn_string = str(settings.DATABASE_URL.unicode_string())
    
    return await asyncpg.create_pool(dsn=dsn_string)
