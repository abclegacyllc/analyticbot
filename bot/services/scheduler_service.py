from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
import logging

from src.bot.database.repositories import SchedulerRepository, AnalyticsRepository # AnalyticsRepository'ni import qilamiz

logger = logging.getLogger(__name__)

class SchedulerService:
    # __init__ metodini o'zgartiramiz
    def __init__(self, bot: Bot, scheduler_repo: SchedulerRepository, analytics_repo: AnalyticsRepository):
        self.bot = bot
        self.scheduler_repo = scheduler_repo
        self.analytics_repo = analytics_repo

    async def send_post_to_channel(self, post_data: dict):
        """Rejalashtirilgan postni kanalga yuboradi va natijani log qiladi."""
        try:
            # Postni yuborish logikasi (sizning postingiz media yoki matn bo'lishiga qarab)
            if post_data.get('media_id'):
                # Media bilan yuborish
                sent_message = await self.bot.send_photo(
                    chat_id=post_data['channel_id'],
                    photo=post_data['media_id'],
                    caption=post_data['post_text'],
                    reply_markup=post_data.get('inline_buttons')
                )
            else:
                # Oddiy matn yuborish
                sent_message = await self.bot.send_message(
                    chat_id=post_data['channel_id'],
                    text=post_data['post_text'],
                    reply_markup=post_data.get('inline_buttons'),
                    disable_web_page_preview=True
                )
            
            # Post yuborilganini bazaga yozamiz
            await self.analytics_repo.log_sent_post(
                scheduled_post_id=post_data['id'],
                channel_id=sent_message.chat.id,
                message_id=sent_message.message_id
            )

            await self.scheduler_repo.update_post_status(post_data['id'], 'sent')
            logger.info(f"Successfully sent post {post_data['id']} to channel {post_data['channel_id']}")

        except TelegramAPIError as e:
            await self.scheduler_repo.update_post_status(post_data['id'], 'error')
            logger.error(f"Failed to send post {post_data['id']}: {e}", exc_info=True)
