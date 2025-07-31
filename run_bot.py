import asyncio
import logging
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers
from src.bot.database import create_pool
from src.bot.database.repository import UserRepository

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Create asyncpg pool
    pool = await create_pool()
    
    # Inject repository into handler module
    user_handlers.user_repository = UserRepository(pool)

    # Register routers
    dp.include_router(user_handlers.router)

    try:
        logger.info("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        logger.info("Bot is shutting down...")
        await pool.close()
        await dp.storage.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
