import asyncpg
from aiogram import Bot
import logging
from src.bot.database.repository import SchedulerRepository
from src.bot.config import DATABASE_URL, BOT_TOKEN # Import config variables

logger = logging.getLogger(__name__)

async def send_scheduled_message(post_id: int):
    """
    This is the standalone function that APScheduler will execute.
    It is now fully self-contained.
    """
    logger.info(f"Executing job for post_id: {post_id}")
    db_pool = None
    # Create a new bot instance just for this task
    bot = Bot(token=BOT_TOKEN)
    try:
        # Create a temporary connection pool for this task
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        repo = SchedulerRepository(db_pool)
        post = await repo.get_scheduled_post(post_id)

        if not post or post['status'] != 'pending':
            logger.warning(f"Post {post_id} not found or not in 'pending' state. Skipping.")
            return

        sent_message = await bot.send_message(
            chat_id=post["channel_id"],
            text=post["text"]
        )
        await repo.update_post_status(post_id, "sent")
        await repo.set_sent_message_id(post_id, sent_message.message_id)
        logger.info(f"Successfully sent post {post_id} (message_id: {sent_message.message_id}) to channel {post['channel_id']}")
    
    except Exception as e:
        if db_pool and post_id:
            repo = SchedulerRepository(db_pool)
            await repo.update_post_status(post_id, "failed")
        logger.error(f"Failed to send post {post_id}: {e}")

    finally:
        # Ensure the temporary connection pool and bot session are always closed
        if db_pool:
            await db_pool.close()
        # Close the bot session to release connections
        await bot.session.close()
