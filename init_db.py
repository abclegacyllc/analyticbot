# init_db.py
import asyncio
import logging
from asyncpg import Pool
from src.bot.config import settings
from src.bot.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1-QISM: Jadvallarni bog'liqliksiz (FOREIGN KEY'siz) yaratish
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
        plan_id INTEGER DEFAULT 1,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS channels (
        id BIGINT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        title VARCHAR(255),
        username VARCHAR(255) UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        channel_id BIGINT,
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
        scheduled_post_id INTEGER NOT NULL,
        channel_id BIGINT NOT NULL,
        message_id BIGINT NOT NULL,
        sent_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """
]

# 2-QISM: Jadvallar orasidagi bog'liqliklarni (FOREIGN KEY) qo'shish
ADD_CONSTRAINTS_STATEMENTS = [
    "ALTER TABLE users ADD CONSTRAINT fk_users_plan_id FOREIGN KEY (plan_id) REFERENCES plans(id);",
    "ALTER TABLE channels ADD CONSTRAINT fk_channels_user_id FOREIGN KEY (user_id) REFERENCES users(id);",
    "ALTER TABLE scheduled_posts ADD CONSTRAINT fk_scheduled_posts_user_id FOREIGN KEY (user_id) REFERENCES users(id);",
    "ALTER TABLE scheduled_posts ADD CONSTRAINT fk_scheduled_posts_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id);",
    "ALTER TABLE sent_posts ADD CONSTRAINT fk_sent_posts_scheduled_post_id FOREIGN KEY (scheduled_post_id) REFERENCES scheduled_posts(id);",
    "ALTER TABLE sent_posts ADD CONSTRAINT fk_sent_posts_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id);"
]


async def main():
    """Jadvallarni va keyin ular orasidagi bog'liqliklarni alohida-alohida yaratadi."""
    logger.info("Connecting to the database...")
    db_pool: Pool = await db.create_pool()
    
    try:
        async with db_pool.acquire() as connection:
            # 1-qismni bajaramiz
            logger.info("Step 1: Creating tables without constraints...")
            for i, statement in enumerate(CREATE_TABLE_STATEMENTS, 1):
                await connection.execute(statement)
            logger.info("✅ All tables created.")

            # 2-qismni bajaramiz
            logger.info("Step 2: Adding foreign key constraints...")
            for i, statement in enumerate(ADD_CONSTRAINTS_STATEMENTS, 1):
                await connection.execute(statement)
            logger.info("✅ All constraints added successfully!")

    except Exception as e:
        logger.error(f"❌ An error occurred: {e}", exc_info=True)
    finally:
        await db_pool.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(main())