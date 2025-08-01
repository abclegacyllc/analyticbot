import logging
import asyncio # <-- ADDED IMPORT
from src.bot.bot import dp, bot
# --- ADDED IMPORTS FOR THE NEW TASK ---
from src.bot.database.repositories import SchedulerRepository, AnalyticsRepository
from src.bot.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


async def send_scheduled_message(post_id: int):
    """
    Executes a scheduled job to send a message.
    """
    logger.info(f"Executing job for post_id: {post_id}")
    db_pool = dp['db_pool']
    repo = SchedulerRepository(db_pool)

    try:
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
        logger.info(f"Successfully sent post {post_id} (message_id: {sent_message.message_id})")
    
    except Exception as e:
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
    analytics_service: AnalyticsService = dp['analytics_service']
    analytics_repo = AnalyticsRepository(db_pool)

    try:
        posts_to_update = await analytics_repo.get_posts_to_update_views()
        logger.info(f"Found {len(posts_to_update)} posts to update views for.")

        updated_count = 0
        for post in posts_to_update:
            post_id = post['post_id']
            admin_id = post['admin_id']
            
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
