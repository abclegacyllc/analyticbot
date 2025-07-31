import asyncio
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers
from src.bot.database import create_pool
from src.bot.database.repository import UserRepository

async def main():
    # Create asyncpg pool
    pool = await create_pool()

    # Inject repository into handler module
    user_handlers.user_repository = UserRepository(pool)

    # Register routers
    dp.include_router(user_handlers.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
