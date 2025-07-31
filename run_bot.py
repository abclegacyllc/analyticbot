import asyncio
import logging
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers, admin_handlers
from src.bot.database import create_pool
from src.bot.database.repository import UserRepository, SchedulerRepository, ChannelRepository, AnalyticsRepository
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from redis.asyncio import Redis
from src.bot.config import REDIS_URL, DATABASE_URL
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    db_pool = await create_pool()
    redis_conn = Redis.from_url(REDIS_URL)

    # --- APScheduler Setup ---
    sqlalchemy_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = { 'default': SQLAlchemyJobStore(url=sqlalchemy_url) }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")

    # --- Repositories and Services Instantiation ---
    user_repo = UserRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    guard_service = GuardService(redis_conn)
    scheduler_service = SchedulerService(scheduler, scheduler_repo)
    analytics_service = AnalyticsService(bot, analytics_repo)

    # --- Dependency Injection ---
    user_handlers.user_repository = user_repo
    user_handlers.guard_service = guard_service
    admin_handlers.guard_service = guard_service
    admin_handlers.scheduler_service = scheduler_service
    admin_handlers.channel_repository = channel_repo
    admin_handlers.analytics_service = analytics_service

    # --- Router Registration ---
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    try:
        logger.info("Starting scheduler...")
        scheduler.start()
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await db_pool.close()
        await redis_conn.close()
        await dp.storage.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
