import asyncio
import logging
from redis.asyncio import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from aiogram.fsm.storage.redis import RedisStorage # <-- NEW IMPORT

from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers, admin_handlers
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.database.repositories import (
    UserRepository,
    SchedulerRepository,
    ChannelRepository,
    AnalyticsRepository,
    PlanRepository
)
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.services.subscription_service import SubscriptionService
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from src.bot.tasks import update_all_post_views

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    # --- ALL CONNECTIONS AND SETUP ARE NOW CENTRALIZED HERE ---
    
    # 1. Create connections
    db_pool = await create_pool()
    redis_conn = Redis.from_url(settings.REDIS_URL.unicode_string())

    # 2. Configure FSM Storage and set it for the dispatcher
    storage = RedisStorage(redis=redis_conn)
    dp.storage = storage # <-- SETTING STORAGE HERE

    # 3. Setup Repositories and Services
    user_repo = UserRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    
    guard_service = GuardService(redis_conn)
    analytics_service = AnalyticsService(bot, analytics_repo, scheduler_repo)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)

    # 4. Setup Scheduler
    db_url_str = settings.DATABASE_URL.unicode_string()
    sqlalchemy_url = db_url_str.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = { 'default': SQLAlchemyJobStore(url=sqlalchemy_url) }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    scheduler_service = SchedulerService(scheduler, scheduler_repo)

    # 5. Pass dependencies to handlers via context (for background tasks) and middleware
    dp['db_pool'] = db_pool
    dp['analytics_service'] = analytics_service

    dp.update.outer_middleware.register(DependencyMiddleware(
        user_repo=user_repo,
        channel_repo=channel_repo,
        scheduler_repo=scheduler_repo,
        analytics_repo=analytics_repo,
        plan_repo=plan_repo,
        guard_service=guard_service,
        scheduler_service=scheduler_service,
        analytics_service=analytics_service,
        subscription_service=subscription_service,
    ))

    # 6. Setup and start background jobs
    scheduler.add_job(
        update_all_post_views, 
        trigger='interval', 
        hours=1, 
        id='update_views_job',
        replace_existing=True
    )

    # 7. Register routers
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # 8. Start everything
    try:
        logger.info("Starting scheduler...")
        scheduler.start()
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        if scheduler.running:
            scheduler.shutdown()
        await db_pool.close()
        await redis_conn.aclose()
        # No need to close dp.storage separately as redis_conn is now managed here

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
