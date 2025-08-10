import asyncio
import logging
from aiogram import Bot

# Loyihaning asosiy sozlamalarini import qilamiz
from bot.config import settings

# Logger sozlamasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Asosiy asinxron funksiya."""
    bot_token = settings.BOT_TOKEN.get_secret_value()
    logger.info(f"Attempting to clear webhook for bot with token ending in ...{bot_token[-6:]}")
    
    bot = Bot(token=bot_token)
    try:
        # Webhook'ni o'chiramiz va kutilayotgan yangilanishlarni tozalaymiz
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook was successfully deleted.")
        logger.info("You can now run the bot in polling mode.")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
