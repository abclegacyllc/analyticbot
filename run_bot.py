import asyncio
import logging
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers, admin_handlers
from src.bot.database import create_pool
from src.bot.database.repositories import (
    UserRepository, 
    SchedulerRepository, 
    ChannelRepository, 
    AnalyticsRepository,
    PlanRepository # <-- QO'SHILDI
)
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.services.subscription_service import SubscriptionService # <-- QO'SHILDI
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from redis.asyncio import Redis
from src.bot.config import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from src.bot.tasks import update_all_post_views

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    db_pool = await create_pool()
    redis_conn = Redis.from_url(settings.REDIS_URL.unicode_string())
    
    # --- Repositories and Services Instantiation ---
    user_repo = UserRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    plan_repo = PlanRepository(db_pool) # <-- QO'SHILDI
    
    guard_service = GuardService(redis_conn)
    analytics_service = AnalyticsService(bot, analytics_repo, scheduler_repo)
    # <-- YANGI SERVIS YARATILDI -->
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)

    db_url_str = settings.DATABASE_URL.unicode_string()
    sqlalchemy_url = db_url_str.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = { 'default': SQLAlchemyJobStore(url=sqlalchemy_url) }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    scheduler_service = SchedulerService(scheduler, scheduler_repo)

    dp['db_pool'] = db_pool
    dp['analytics_service'] = analytics_service

    # --- Register Middlewares ---
    dependency_middleware = DependencyMiddleware(
        user_repo=user_repo,
        channel_repo=channel_repo,
        scheduler_repo=scheduler_repo,
        analytics_repo=analytics_repo,
        plan_repo=plan_repo, # <-- QO'SHILDI
        guard_service=guard_service,
        scheduler_service=scheduler_service,
        analytics_service=analytics_service,
        subscription_service=subscription_service, # <-- QO'SHILDI
    )
    dp.update.outer_middleware.register(dependency_middleware)

    scheduler.add_job(update_all_post_views, trigger='interval', hours=1, id='update_views_job')

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
