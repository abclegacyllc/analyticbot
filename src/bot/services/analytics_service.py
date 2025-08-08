import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from src.bot.database.repositories import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, bot: Bot, analytics_repo: AnalyticsRepository):
        self.bot = bot
        self.analytics_repo = analytics_repo

    async def update_all_post_views(self):
        """
        Kuzatishdagi barcha postlarning ko'rishlar sonini yangilaydi.
        Bu metod Celery vazifasi orqali vaqti-vaqti bilan chaqiriladi.
        """
        trackable_posts = await self.analytics_repo.get_all_trackable_posts()
        if not trackable_posts:
            logger.info("No trackable posts found to update views.")
            return

        updated_count = 0
        for post in trackable_posts:
            try:
                # Postni o'z-o'ziga forward qilish orqali uning oxirgi holatini (va views sonini) olish
                # Bu bot uchun maxfiy "log" kanali bo'lsa yanada yaxshi.
                # Hozircha o'ziga forward qilish eng oddiy usul.
                forwarded_message = await self.bot.forward_message(
                    chat_id=post['channel_id'], # O'ziga forward qilish
                    from_chat_id=post['channel_id'],
                    message_id=post['message_id']
                )
                
                # Forward qilingan xabarni darhol o'chiramiz
                await self.bot.delete_message(
                    chat_id=forwarded_message.chat.id,
                    message_id=forwarded_message.message_id
                )
                
                # Original xabardagi ko'rishlar sonini olamiz
                current_views = forwarded_message.forward_from_message_id and forwarded_message.forward_origin.views or 0

                if current_views > post['views']:
                    await self.analytics_repo.update_post_views(post['scheduled_post_id'], current_views)
                    updated_count += 1

            except TelegramAPIError as e:
                # Xatoliklar bo'lishi mumkin: post o'chirilgan, bot kanaldan chiqarilgan va hokazo.
                logger.warning(
                    f"Could not update views for post {post['scheduled_post_id']} "
                    f"in channel {post['channel_id']}. Reason: {e.message}"
                )
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while updating views for post {post['scheduled_post_id']}: {e}",
                    exc_info=True
                )
        
        logger.info(f"Views update task finished. Updated {updated_count} posts.")
