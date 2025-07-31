from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from src.bot.database.repository import AnalyticsRepository
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, bot: Bot, repository: AnalyticsRepository):
        self.bot = bot
        self.repository = repository

    async def get_post_views(self, post_id: int) -> int | None:
        """
        Fetches the view count for a specific post.
        Returns the view count or None if the post is not found or an error occurs.
        """
        post_details = await self.repository.get_post_details(post_id)

        if not post_details or not post_details.get("sent_message_id"):
            logger.warning(f"Post {post_id} not found or was not sent successfully.")
            return None

        channel_id = post_details["channel_id"]
        message_id = post_details["sent_message_id"]

        try:
            # This is a special method to get views without being a channel member
            message_views_result = await self.bot.get_message_views(
                chat_id=channel_id,
                message_ids=[message_id]
            )
            # The result is a list, we take the views of the first (and only) message
            return message_views_result[0].views
        except TelegramBadRequest as e:
            logger.error(f"Telegram API error fetching views for message {message_id} in channel {channel_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching views for post {post_id}: {e}")
            return None
