import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from redis.asyncio import Redis

# Asosiy sozlamalarni import qilamiz
from src.bot.config import settings
from src.bot.database import db

# Barcha repozitoriy va servislarni import qilamiz
from src.bot.database.repositories import (
    AnalyticsRepository,
    ChannelRepository,
    PlanRepository,
    SchedulerRepository,
    UserRepository,
)
from src.bot.services import (
    AnalyticsService,
    GuardService,
    SchedulerService,
    SubscriptionService,
)

# Barcha handlerlarni import qilamiz
from src.bot.handlers import admin_handlers, user_handlers

# Middleware'larni import qilamiz
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
# Mukammal qilingan i18n tizimini import qilamiz
from src.bot.middlewares.i18n import i18n_middleware


@asynccontextmanager
async def lifespan(bot: Bot):
    yield


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=str(settings.SENTRY_DSN), traces_sample_rate=1.0)
        logger.info("Sentry is configured")

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = RedisStorage(Redis.from_url(str(settings.REDIS_URL)))
    dp = Dispatcher(storage=storage, lifespan=lifespan(bot))

    # Barcha kerakli obyektlarni yaratamiz
    db_pool = await db.create_pool()
    redis_pool = Redis.from_url(str(settings.REDIS_URL))
    
    user_repo = UserRepository(db_pool)
    plan_repo = PlanRepository(db_pool)
    channel_repo = ChannelRepository(db_pool)
    scheduler_repo = SchedulerRepository(db_pool)
    analytics_repo = AnalyticsRepository(db_pool)
    guard_service = GuardService(redis_pool)
    subscription_service = SubscriptionService(settings, user_repo, plan_repo, channel_repo, scheduler_repo)
    scheduler_service = SchedulerService(bot, scheduler_repo, analytics_repo)
    analytics_service = AnalyticsService(bot, analytics_repo)

    # --- MIDDLEWARE'LARNI TO'G'RI TARTIBDA ULASH ---
    # 1. Avval barcha kerakli obyektlarni har bir so'rovga qo'shib beramiz.
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

    # 2. Keyin, tayyor i18n tizimini ulaymiz.
    i18n_middleware.setup(dp)

    # Routerlarni (handlerlarni) ulaymiz
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot ishga tushirildi...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db_pool.close()
        await redis_pool.close()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot foydalanuvchi tomonidan to'xtatildi.")
