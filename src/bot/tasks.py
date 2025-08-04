import logging
import asyncio
from aiogram import Bot

from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.database.repositories import SchedulerRepository, AnalyticsRepository
from src.bot.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


async def send_scheduled_message(post_id: int):
    """
    A self-sufficient task that creates its own bot and db connections to send a message.
    """
    logger.info(f"Executing self-sufficient job for post_id: {post_id}")

    temp_bot: Bot | None = None
    temp_pool = await create_pool()
    repo = SchedulerRepository(temp_pool)

    try:
        temp_bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        post = await repo.get_scheduled_post(post_id)
        if not post or post['status'] != 'pending':
            logger.warning(
                f"Post {post_id} not found or not in 'pending' state. Skipping."
            )
            return

        if post.get('file_id') and post.get('file_type') == 'photo':
            sent_message = await temp_bot.send_photo(
                chat_id=post["channel_id"],
                photo=post["file_id"],
                caption=post.get("text")
            )
        elif post.get('file_id') and post.get('file_type') == 'video':
            sent_message = await temp_bot.send_video(
                chat_id=post["channel_id"],
                video=post["file_id"],
                caption=post.get("text")
            )
        else:
            sent_message = await temp_bot.send_message(
                chat_id=post["channel_id"], text=post["text"]
            )

        await repo.update_post_status(post_id, "sent")
        await repo.set_sent_message_id(post_id, sent_message.message_id)
        logger.info(
            f"Successfully sent post {post_id} (message_id: {sent_message.message_id})"
        )

    except Exception as e:
        await repo.update_post_status(post_id, "failed")
        logger.error(f"Failed to send post {post_id}: {e}", exc_info=True)
    finally:
        if temp_pool:
            await temp_pool.close()
        # --- MUHIM TUZATISH ---
        # Bot sessiyasini yopish kodini olib tashladik.
        if temp_bot:
            await temp_bot.session.close()


async def update_all_post_views():
    """
    A self-sufficient background job that periodically fetches view counts.
    """
    logger.info("Starting background task: update_all_post_views")
    
    temp_bot: Bot | None = None
    temp_pool = await create_pool()

    try:
        temp_bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        analytics_repo = AnalyticsRepository(temp_pool)
        analytics_service = AnalyticsService(temp_bot, analytics_repo, SchedulerRepository(temp_pool))

        posts_to_update = await analytics_repo.get_posts_to_update_views()
        updated_count = 0
        for post in posts_to_update:
            post_id, admin_id = post['post_id'], post['admin_id']
            current_views = await analytics_service.get_post_views(post_id, admin_id)
            if current_views is not None:
                await analytics_repo.update_post_views(post_id, current_views)
                updated_count += 1
            await asyncio.sleep(1)
        logger.info(f"Successfully updated view counts for {updated_count} posts.")

    except Exception as e:
        logger.error(f"Error during update_all_post_views task: {e}", exc_info=True)
    finally:
        if temp_pool:
            await temp_pool.close()
        # --- MUHIM TUZATISH ---
        # Bu yerda ham bot sessiyasini yopish kodini olib tashladik.
        if temp_bot:
            await temp_bot.session.close()
