import asyncio
import logging
from asyncpg import Pool
from src.bot.config import settings
from src.bot.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The correct, sequential order for creating tables
CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        max_channels INTEGER DEFAULT 1,
        max_posts_per_month INTEGER DEFAULT 30
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        plan_id INTEGER DEFAULT 1 REFERENCES plans(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS channels (
        id BIGINT PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id),
        title VARCHAR(255),
        username VARCHAR(255) UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id),
        channel_id BIGINT REFERENCES channels(id),
        post_text TEXT,
        media_id VARCHAR(255),
        media_type VARCHAR(50),
        inline_buttons JSON,
        status VARCHAR(50) DEFAULT 'pending',
        schedule_time TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        views INTEGER DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sent_posts (
        id SERIAL PRIMARY KEY,
        scheduled_post_id INTEGER NOT NULL REFERENCES scheduled_posts(id),
        channel_id BIGINT NOT NULL REFERENCES channels(id),
        message_id BIGINT NOT NULL,
        sent_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """
]

async def main():
    """
    Connects to the database and manually creates all tables one by one.
    """
    logger.info("Connecting to the database...")
    db_pool: Pool = await db.create_pool()
    
    try:
        async with db_pool.acquire() as connection:
            logger.info("Starting table creation...")
            for i, statement in enumerate(CREATE_TABLE_STATEMENTS, 1):
                logger.info(f"Executing statement {i}/{len(CREATE_TABLE_STATEMENTS)}...")
                await connection.execute(statement)
            logger.info("✅ All tables created successfully!")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}", exc_info=True)
    finally:
        await db_pool.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
