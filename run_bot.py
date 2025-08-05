import asyncio
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    # --- CONNECTIONS AND SETUP ---
    
    # 1. Create connections
    db_pool = await create_pool()
    redis_conn = Redis.from_url(settings.REDIS_URL.unicode_string())

    # 2. Create FSM Storage
    storage = RedisStorage(redis=redis_conn)

    # 3. Create Dispatcher instance
    dp = Dispatcher(storage=storage)

    # 4. Setup i18n middleware
    i18n_middleware.setup(dispatcher=dp)

    # 5. Setup Repositories and Services
    user_repo = UserRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    
    guard_service = GuardService(redis_conn)
    analytics_service = AnalyticsService(bot, analytics_repo, scheduler_repo)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)

    # 6. Setup Scheduler
    db_url_str = settings.DATABASE_URL.unicode_string()
    sqlalchemy_url = db_url_str.replace("postgresql://", "postgresql+psycopg2://")
    jobstores = { 'default': SQLAlchemyJobStore(url=sqlalchemy_url) }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    scheduler_service = SchedulerService(scheduler, scheduler_repo)

    # 7. Pass dependencies to handlers via middleware
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

    # 8. Setup background jobs
    scheduler.add_job(
        update_all_post_views, 
        trigger='interval', 
        hours=1, 
        id='update_views_job',
        replace_existing=True
    )

    # 9. Register routers
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # 10. Start everything
    try:
        scheduler.start()
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        if scheduler.running:
            scheduler.shutdown()
        
        # --- MUHIM TUZATISH SHU YERDA ---
        # Bot sessiyasini yopishning to'g'ri usuli (aiogram 3.x uchun)
        await bot.session.close()
        
        await db_pool.close()
        await redis_conn.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
