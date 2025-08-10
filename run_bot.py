import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import TelegramObject, User
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from aiogram_i18n.managers import BaseManager
from redis.asyncio import Redis

from src.bot.config import settings
# --- 1-O'ZGARISH: Import to'g'irlandi ---
from src.bot.database.db import create_pool
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
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.middlewares.dependency_middleware import DependencyMiddleware


class LanguageManager(BaseManager):
    def __init__(self, user_repo: UserRepository):
        super().__init__()
        self.user_repo = user_repo

    async def get_locale(self, event: TelegramObject) -> str:
        from_user: User | None = None
        if hasattr(event, "from_user"):
            from_user = getattr(event, "from_user")
        elif hasattr(event, "message") and hasattr(event.message, "from_user"):
            from_user = getattr(event.message, "from_user")

        if from_user:
            user = await self.user_repo.get_or_create_user(
                from_user.id,
                from_user.username,
                from_user.language_code
            )
            if user and user.language_code in settings.SUPPORTED_LOCALES:
                return user.language_code
        
        return settings.DEFAULT_LOCALE

    async def set_locale(self, locale: str, event: TelegramObject) -> None:
        from_user: User | None = None
        if hasattr(event, "from_user"):
            from_user = getattr(event, "from_user")
        elif hasattr(event, "message") and hasattr(event.message, "from_user"):
            from_user = getattr(event.message, "from_user")

        if from_user:
            await self.user_repo.update_user_language(from_user.id, locale)


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

    # --- 2-O'ZGARISH: Funksiya chaqiruvi to'g'irlandi ---
    db_pool = await create_pool()
    redis_pool = Redis.from_url(str(settings.REDIS_URL))
    
    user_repo = UserRepository(db_pool)
    
    language_manager = LanguageManager(user_repo=user_repo)

    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path="src/bot/locales/{locale}"),
        default_locale=settings.DEFAULT_LOCALE,
        manager=language_manager
    )

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

    i18n_middleware.setup(dp)

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
