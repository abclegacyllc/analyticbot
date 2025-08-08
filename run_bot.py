import asyncio
import logging
import sentry_sdk
from redis.asyncio import Redis
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.bot import bot
from src.bot.handlers import user_handlers, admin_handlers
from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.middlewares.i18n import i18n_middleware
from src.bot.database.repositories import (
    UserRepository, PlanRepository, ChannelRepository, SchedulerRepository, 
    AnalyticsRepository
)
from src.bot.services.guard_service import GuardService
from src.bot.services.subscription_service import SubscriptionService
from src.bot.middlewares.dependency_middleware import DependencyMiddleware


async def main():
    # Sentry'ni ishga tushirish
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

    # Loglashni sozlash
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    logger = logging.getLogger(__name__)
    logger.info("Bot starting...")

    # Asosiy sozlamalar
    db_pool = await create_pool()
    redis_conn = Redis.from_url(settings.REDIS_URL.unicode_string())
    storage = RedisStorage(redis=redis_conn)
    dp = Dispatcher(storage=storage)

    i18n_middleware.setup(dispatcher=dp)

    # Repozitoriya va Servislarni sozlash
    # E'tibor bering: Scheduler va Analytics bilan bog'liq qismlar olib tashlandi
    user_repo = UserRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    
    guard_service = GuardService(redis_conn)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, None) # SchedulerRepo olib tashlandi

    # Middleware orqali bog'liqliklarni o'tkazish
    dp.update.outer_middleware.register(DependencyMiddleware(
        user_repo=user_repo,
        channel_repo=channel_repo,
        plan_repo=plan_repo,
        guard_service=guard_service,
        subscription_service=subscription_service,
    ))
    
    # Routerlarni ulash
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # Botni ishga tushirish
    try:
        allowed_updates = dp.resolve_used_update_types(skip_events={"message_reaction", "message_reaction_count"})
        logger.info(f"Starting polling with allowed updates: {allowed_updates}")
        
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        logger.info("Shutting down...")
        await bot.session.close()
        await db_pool.close()
        await redis_conn.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped manually.")
