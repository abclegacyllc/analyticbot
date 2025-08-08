import asyncio
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from src.bot.database.models import metadata
from src.bot.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """
    Connects to the database and creates all tables based on models.py.
    """
    logger.info("Connecting to the database...")
    
    # SQLAlchemy 1.4/2.0 requires a sync engine for metadata.create_all()
    # We use a trick to create tables using a sync wrapper around the async driver.
    # Note: Pydantic v2 returns a string, so we convert it.
    db_url = str(settings.DATABASE_URL.unicode_string())
    sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        # Create a synchronous engine
        engine = create_engine(sync_db_url)
        
        # Create all tables
        logger.info("Creating tables...")
        metadata.create_all(engine)
        
        logger.info("✅ Tables created successfully!")
    except Exception as e:
        logger.error(f"❌ An error occurred while creating tables: {e}", exc_info=True)
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())