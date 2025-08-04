# FILE: src/bot/tasks.py

import logging
import asyncio
from aiogram import Bot

# --- NEW IMPORTS ---
from src.bot.config import settings
from src.bot.database.db import create_pool
# --- END NEW IMPORTS ---

from src.bot.database.repositories import SchedulerRepository, AnalyticsRepository
from src.bot.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


async def send_scheduled_message(
    bot: Bot, 
    db_pool,
    post_id: int,
):
    """
    This function is called by the scheduler when a post is due.
    """
    logger.info(f"Executing job for post_id: {post_id}")
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
    finally:
        # Since we create a new pool for each job, we must close it
        if db_pool:
            await db_pool.close()


async def update_all_post_views():
    """
    A self-sufficient background job that creates its own connections.
    """
    logger.info("Starting background task: update_all_post_views")
    
    temp_bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    temp_pool = await create_pool()
    
    try:
        analytics_repo = AnalyticsRepository(temp_pool)
        scheduler_repo = SchedulerRepository(temp_pool)
        analytics_service = AnalyticsService(temp_bot, analytics_repo, scheduler_repo)

        posts_to_update = await analytics_repo.get_posts_to_update_views()
        logger.info(f"Found {len(posts_to_update)} posts to update views for.")

        updated_count = 0
        for post in posts_to_update:
            post_id = post['post_id']
            admin_id = post['admin_id']
            
            current_views = await analytics_service.get_post_views(post_id, admin_id)

            if current_views is not None:
                await analytics_repo.update_post_views(post_id, current_views)
                updated_count += 1
            
            await asyncio.sleep(1) 

        logger.info(f"Successfully updated view counts for {updated_count} posts.")

    except Exception as e:
        logger.error(f"Error during update_all_post_views task: {e}", exc_info=True)
    finally:
        await temp_pool.close()
        await (await temp_bot.get_session()).close()
