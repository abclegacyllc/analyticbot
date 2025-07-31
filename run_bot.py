import asyncio
from src.bot.bot import bot, dp
from src.bot.handlers import user_handlers

async def main():
    # Register user handlers
    dp.include_router(user_handlers.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
