import logging
from src.bot.bot import dp, bot  # Import the shared dispatcher and bot instances
from src.bot.database.repositories import SchedulerRepository

logger = logging.getLogger(__name__)

async def send_scheduled_message(post_id: int):
    """
    Executes a scheduled job using the main application's shared bot and database pool instances.
    It retrieves these dependencies from the dispatcher's context.
    """
    logger.info(f"Executing job for post_id: {post_id}")
    
    # --- Retrieve shared dependencies ---
    # Get the db_pool from the dispatcher context where it was placed in run_bot.py
    db_pool = dp['db_pool']
    repo = SchedulerRepository(db_pool)

    try:
        post = await repo.get_scheduled_post(post_id)

        if not post or post['status'] != 'pending':
            logger.warning(f"Post {post_id} not found or not in 'pending' state. Skipping.")
            return

        # Use the globally shared bot instance to send the message
        sent_message = await bot.send_message(
            chat_id=post["channel_id"],
            text=post["text"]
        )
        
        await repo.update_post_status(post_id, "sent")
        await repo.set_sent_message_id(post_id, sent_message.message_id)
        logger.info(f"Successfully sent post {post_id} (message_id: {sent_message.message_id}) to channel {post['channel_id']}")
    
    except Exception as e:
        # If an error occurs, update the status to 'failed'
        # The repository is already initialized, so we can safely use it
        await repo.update_post_status(post_id, "failed")
        logger.error(f"Failed to send post {post_id}: {e}", exc_info=True)
