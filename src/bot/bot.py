import asyncio
import logging
from asyncpg import Pool

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.handlers import admin_handlers, user_handlers
from src.bot.middlewares.dependency_middleware import DependencyMiddleware

# YAKUNIY TUZATISH: i18n_middleware'ni import qilamiz
from src.bot.middlewares.i18n import i18n_middleware

# Logger sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """
    Botni ishga tushiruvchi asosiy funksiya.
    """
    # Ma'lumotlar bazasi bilan ulanish (connection pool)
    pool: Pool = await create_pool()
    
    # Redis'ga ulanish (FSM holatlari uchun)
    storage = RedisStorage.from_url(
        settings.REDIS_DSN,
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )

    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(storage=storage)

    # Handlers (buyruqlarga javob beruvchilar) ro'yxatdan o'tkaziladi
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    
    # Middleware'lar ulanadi
    # 1. Tashqi bog'liqliklar (DB, Redis) uchun
    dp.update.outer_middleware(DependencyMiddleware(pool=pool))
    
    # 2. Lokalizatsiya (i18n) uchun
    # YAKUNIY TUZATISH: i18n_middleware'ni dispatcher'ga ulaymiz
    i18n_middleware.setup(dispatcher=dp)

    logger.info("Bot ishga tushirildi.")
    
    try:
        # Botni ishga tushirish
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # To'xtatilganda ulanishlarni yopish
        await dp.storage.close()
        await bot.session.close()
        await pool.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
