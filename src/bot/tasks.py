import asyncpg
from aiogram import Bot
import logging
from src.bot.database.repository import SchedulerRepository

logger = logging.getLogger(__name__)

async def send_scheduled_message(post_id: int, bot: Bot, db_pool: asyncpg.Pool):
    """
    This is the standalone function that APScheduler will execute.
    """
    logger.info(f"Executing job for post_id: {post_id}")
    repo = SchedulerRepository(db_pool)
    post = await repo.get_scheduled_post(post_id)

    if not post or post['status'] != 'pending':
        logger.warning(f"Post {post_id} not found or not in 'pending' state. Skipping.")
        return

    try:
        sent_message = await bot.send_message(
            chat_id=post["channel_id"],
            text=post["text"]
        )
        await repo.update_post_status(post_id, "sent")
        # Save the message_id for analytics
        await repo.set_sent_message_id(post_id, sent_message.message_id)
        logger.info(f"Successfully sent post {post_id} (message_id: {sent_message.message_id}) to channel {post['channel_id']}")
    except Exception as e:
        await repo.update_post_status(post_id, "failed")
        logger.error(f"Failed to send post {post_id} to channel {post['channel_id']}: {e}")
