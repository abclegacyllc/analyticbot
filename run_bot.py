import asyncio
import logging
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers, admin_handlers # import admin_handlers
from src.bot.database import create_pool
from src.bot.database.repository import UserRepository
from src.bot.services.guard_service import GuardService
from redis.asyncio import Redis
from src.bot.config import REDIS_URL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db_pool = await create_pool()
    redis_conn = Redis.from_url(REDIS_URL)

    # Services and Repositories
    user_repo = UserRepository(db_pool)
    guard_service = GuardService(redis_conn)

    # Inject dependencies into handlers
    user_handlers.user_repository = user_repo
    user_handlers.guard_service = guard_service
    admin_handlers.guard_service = guard_service

    # Register routers
    # IMPORTANT: More specific command routers (admin) must be registered before a general text handler (user)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    try:
        logger.info("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        logger.info("Bot is shutting down...")
        await db_pool.close()
        await redis_conn.close()
        await dp.storage.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
