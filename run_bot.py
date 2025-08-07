import asyncio
import logging
import sentry_sdk
from redis.asyncio import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.bot import bot
from src.bot.handlers import user_handlers, admin_handlers
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.middlewares.i18n import i18n_middleware
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


async def main():
    # --- Sentry'ni ishga tushirish (Backend uchun) ---
    sentry_sdk.init(
        # @ belgisi bilan to'g'rilangan DSN kaliti
        dsn="https://d18b179e78010fcdb38a5890b2ba90d1@o4509801364324352.ingest.us.sentry.io/4509801430777856",
        traces_sample_rate=1.0,
    )

    # --- Loglashni sozlash ---
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    logger = logging.getLogger(__name__)
    logger.info("Bot starting with Sentry and all configurations...")

    # --- Asosiy sozlamalar ---
    db_pool = await create_pool()
    redis_conn = Redis.from_url(settings.REDIS_URL.unicode_string())
    storage = RedisStorage(redis=redis_conn)
    dp = Dispatcher(storage=storage)

    i18n_middleware.setup(dispatcher=dp)

    # --- Repositoriya va Servislarni sozlash ---
    user_repo = UserRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    
    guard_service = GuardService(redis_conn)
    analytics_service = AnalyticsService(bot, analytics_repo, scheduler_repo)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)
    
    db_url_str = settings.DATABASE_URL.unicode_string()
    sqlalchemy_url = db_url_str.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = { 'default': SQLAlchemyJobStore(url=sqlalchemy_url) }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    scheduler_service = SchedulerService(scheduler, scheduler_repo)

    # --- Middleware va Routerlarni ulash ---
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

    scheduler.add_job(
        update_all_post_views, 
        trigger='interval', 
        hours=1, 
        id='update_views_job',
        replace_existing=True
    )

    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # --- Botni ishga tushirish ---
    try:
        scheduler.start()
        
        # Telegramdan barcha kerakli yangilanishlarni qabul qilish uchun
        allowed_updates = dp.resolve_used_update_types(skip_events={"message_reaction", "message_reaction_count"})
        logger.info(f"Starting polling with allowed updates: {allowed_updates}")
        
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        logger.info("Shutting down...")
        if scheduler.running:
            scheduler.shutdown()
        
        await bot.session.close()
        await db_pool.close()
        await redis_conn.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped manually.")
