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

        
# --- NEW BACKGROUND TASK TO UPDATE VIEW COUNTS ---

async def update_all_post_views():
    """
    A background job that periodically fetches view counts for all sent posts
    and updates the database.
    """
    logger.info("Starting background task: update_all_post_views")
    
    # Retrieve dependencies from the dispatcher context
    db_pool = dp['db_pool']
    # We need the full AnalyticsService to use its get_post_views logic
    analytics_service: AnalyticsService = dp['analytics_service']
    analytics_repo = AnalyticsRepository(db_pool)

    try:
        posts_to_update = await analytics_repo.get_posts_to_update_views()
        logger.info(f"Found {len(posts_to_update)} posts to update views for.")

        updated_count = 0
        for post in posts_to_update:
            post_id = post['post_id']
            admin_id = post['admin_id'] # Needed for get_post_views
            
            # Use the existing service method to fetch views from Telegram
            current_views = await analytics_service.get_post_views(post_id, admin_id)

            if current_views is not None:
                await analytics_repo.update_post_views(post_id, current_views)
                updated_count += 1
            
            # Be respectful to Telegram API: wait a bit between requests
            await asyncio.sleep(1) 

        logger.info(f"Successfully updated view counts for {updated_count} posts.")

    except Exception as e:
        logger.error(f"Error during update_all_post_views task: {e}", exc_info=True)
