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
from src.bot.container import container  # Asosiy DI konteynerimiz
from src.bot.config import Config
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.middlewares.dependency_middleware import DependencyMiddleware
from src.bot.utils.language_manager import LanguageManager # Tilni boshqarish uchun alohida klass
from src.bot.database.repositories import UserRepository


async def main():
    """Botni ishga tushiruvchi asosiy funksiya."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Konfiguratsiyani DI konteyneridan olamiz
    config: Config = container.resolve(Config)

    # Sentry'ni sozlash (agar .env faylida DSN berilgan bo'lsa)
    if config.sentry.dsn:
        sentry_sdk.init(dsn=str(config.sentry.dsn), traces_sample_rate=1.0)
        logger.info("Sentry is configured.")

    # Aiogram komponentlarini sozlash
    bot = Bot(
        token=config.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = RedisStorage.from_url(config.redis.dsn())
    dp = Dispatcher(storage=storage)

    # Tilni boshqarish menejerini konteynerdan bog'liqlik olib sozlaymiz
    user_repo = container.resolve(UserRepository)
    language_manager = LanguageManager(user_repo=user_repo, config=config)

    # Middleware'larni o'rnatish
    # 1. DependencyMiddleware faqat konteynerning o'zini qabul qiladi
    dp.update.middleware(DependencyMiddleware(container=container))

    # 2. I18nMiddleware'ni sozlaymiz
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path=config.bot.locales_path),
        default_locale=config.bot.default_locale,
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
