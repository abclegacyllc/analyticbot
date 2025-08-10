import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

import asyncpg
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import TelegramObject, User
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.managers import BaseManager

from src.bot.database.db import get_connection_pool
from src.bot.database.repositories.user_repository import UserRepository
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.locales.i18n_hub import I18N_HUB
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from src.bot.services import (AnalyticsService, GuardService, SchedulerService,
                            SubscriptionService)
from src.bot.config import settings

# --- BU QATORNI O'CHIRAMIZ ---
# from src.bot.middlewares.i18n import i18n_middleware

# Logger sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Sentry sozlamalari
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry is configured")


# --- LanguageManager KLASSI O'ZGARMAGAN ---
class LanguageManager(BaseManager):
    def __init__(self, user_repo: UserRepository):
        super().__init__()
        self.user_repo = user_repo

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        user: User | None = data.get("event_from_user")
        if user is None:
            return self.default_locale

        user_language = await self.user_repo.get_user_language(user.id)
        if user_language:
            return user_language

        if user.language_code and user.language_code in self.i18n.available_locales:
            return user.language_code

        return self.default_locale

    async def set_locale(self, locale: str, data: Dict[str, Any]) -> None:
        user: User | None = data.get("event_from_user")
        if user is None:
            return
        await self.user_repo.update_user_language(user_id=user.id, language_code=locale)


async def main() -> None:
    # Ma'lumotlar bazasi va Redis ulanishlarini o'rnatish
    db_pool: asyncpg.Pool = await get_connection_pool()
    redis_pool = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
    storage = RedisStorage(redis=redis_pool)

    # Repositoriy va servislarni yaratish
    user_repo = UserRepository(db_pool)
    # ... boshqa repositoriy va servislar ...

    # Dispatcher va Bot obyektlarini yaratish
    dp = Dispatcher(storage=storage)
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode="HTML")

    # --- O'ZGARTIRILGAN I18N SOZLAMALARI ---
    # Eski `i18n_middleware` importi o'rniga, uni shu yerda to'g'ri sozlaymiz
    i18n_middleware = I18nMiddleware(
        i18n=I18N_HUB,
        manager=LanguageManager(user_repo=user_repo), # LanguageManager'ni to'g'ridan-to'g'ri manager sifatida uzatamiz
        default_locale="en"
    )

    # Middleware'larni ro'yxatdan o'tkazish
    dp.update.middleware(
        DependencyMiddleware(
            db_pool=db_pool,
            redis_pool=redis_pool
        )
    )
    dp.update.middleware(i18n_middleware) # Yangi, to'g'ri sozlangan i18n_middleware

    # Router'larni ulash
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # Botni ishga tushirish
    try:
        logger.info("Bot ishga tushirildi...")
        await dp.start_polling(bot)
    finally:
        await db_pool.close()
        await redis_pool.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot jarayoni to'xtatildi.")
