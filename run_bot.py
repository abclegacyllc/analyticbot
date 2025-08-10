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
from src.bot.services import (
    AnalyticsService,
    GuardService,
    SchedulerService,
    SubscriptionService,
)


@asynccontextmanager
async def lifespan(bot: Bot):
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

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = RedisStorage(Redis.from_url(str(settings.REDIS_URL)))
    dp = Dispatcher(storage=storage, lifespan=lifespan(bot))

    # --- I18n (Lokalizatsiya) QISMINI YAXSHILAYMIZ ---
    # Loyihaning asosiy papkasiga to'g'ri yo'lni aniqlaymiz
    base_dir = Path(__file__).parent
    
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(
            path=base_dir / "src" / "bot" / "locales" / "{locale}",
            # locales_map ni bu yerga, ya'ni FluentRuntimeCore ga o'tkazamiz
            locales_map={
                "uz": "uz",
                "en": "en",
                "ru": "en"
            }
        ),
        default_locale="en"
    )
    # --------------------------------------------------

    dp.update.middleware(i18n_middleware) # O'zgarish
    
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

    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

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
