import asyncio
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from redis.asyncio import Redis

from src.bot.config import settings
from src.bot.database import db
from src.bot.database.repositories import (
    AnalyticsRepository,
    ChannelRepository,
    PlanRepository,
    SchedulerRepository,
    UserRepository,
)
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from src.bot.services.analytics_service import AnalyticsService
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.subscription_service import SubscriptionService


@asynccontextmanager
async def lifespan(bot: Bot):
    # Bu yerga bot ishga tushishidan oldin va o'chishidan keyin bajariladigan
    # amallarni qo'shish mumkin (masalan, webhook o'rnatish)
    yield


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        logger.info("Sentry is configured")

    # Bot, Dispatcher va Storage
    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = RedisStorage(Redis.from_url(str(settings.REDIS_URL)))
    dp = Dispatcher(storage=storage, lifespan=lifespan(bot))

    # I18n (Lokalizatsiya)
    i18n_manager = FluentRuntimeCore(
        path="src/bot/locales/{locale}",
        raise_key_error=False,
        locales_map={"ru": "en"},
    )
    dp.update.middleware(I18nMiddleware(core=i18n_manager, default_locale="en"))

    # Ma'lumotlar bazasi va Redis ulanishlari
    db_pool = await db.create_pool()
    redis_pool = Redis.from_url(str(settings.REDIS_URL))

    # Repositories
    user_repo = UserRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)

    # Services
    guard_service = GuardService(redis_pool)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)
    scheduler_service = SchedulerService(bot, scheduler_repo, analytics_repo)
    analytics_service = AnalyticsService(bot, analytics_repo)

    # Middlewares
    dp.update.middleware(
        DependencyMiddleware(
            db_pool=db_pool,
            redis_pool=redis_pool,
            user_repo=user_repo,
            plan_repo=plan_repo,
            channel_repo=channel_repo,
            scheduler_repo=scheduler_repo,
            analytics_repo=analytics_repo,
            guard_service=guard_service,
            subscription_service=subscription_service,
            scheduler_service=scheduler_service,
            analytics_service=analytics_service
        )
    )

    # Routers
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # Botni ishga tushirish
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db_pool.close()
        await redis_pool.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user")
