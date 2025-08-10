import asyncio
import logging

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

# Loyihamizning asosiy komponentlarini import qilamiz
from src.bot.container import container
# Endi 'settings' obyektini to'g'ridan-to'g'ri import qilamiz
from src.bot.config import settings
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from src.bot.utils.language_manager import LanguageManager
from src.bot.database.repositories import UserRepository


async def main():
    """Botni ishga tushiruvchi asosiy funksiya."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Konfiguratsiyani to'g'ridan-to'g'ri import qilingan 'settings' obyektidan olamiz
    config = settings

    # Sentry'ni sozlash (agar .env faylida DSN berilgan bo'lsa)
    if config.SENTRY_DSN:
        sentry_sdk.init(dsn=str(config.SENTRY_DSN), traces_sample_rate=1.0)
        logger.info("Sentry is configured.")

    # Aiogram komponentlarini sozlash
    # Bot obyektini endi DI konteyneridan olamiz, chunki u yerda registratsiya qilingan
    bot: Bot = container.resolve(Bot)
    storage = RedisStorage.from_url(config.REDIS_URL.unicode_string())
    dp = Dispatcher(storage=storage)

    # Tilni boshqarish menejerini konteynerdan bog'liqlik olib sozlaymiz
    user_repo = container.resolve(UserRepository)
    # LanguageManager'ga ham to'g'ridan-to'g'ri 'config' (ya'ni 'settings') obyektini uzatamiz
    language_manager = LanguageManager(user_repo=user_repo, config=config)

    # Middleware'larni o'rnatish
    # 1. DependencyMiddleware faqat konteynerning o'zini qabul qiladi
    dp.update.middleware(DependencyMiddleware(container=container))

    # 2. I18nMiddleware'ni sozlaymiz
    i18n_middleware = I18nMiddleware(
        # Lokalizatsiya fayllari yo'lini config'dan to'g'ri olish kerak.
        # Agar 'config'da 'locales_path' bo'lmasa, uni qo'shish kerak.
        # Hozircha statik yo'l qo'yamiz.
        core=FluentRuntimeCore(path="locales/{locale}/LC_MESSAGES"),
        default_locale=config.DEFAULT_LOCALE,
        manager=language_manager
    )
    # Dispatcherga i18n middleware'ni o'rnatamiz
    i18n_middleware.setup(dp)

    # Router'larni ulaymiz
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot is starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Bot is shutting down.")
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot was stopped by user.")
