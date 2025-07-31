from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from src.bot.database.repository import AnalyticsRepository
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, bot: Bot, repository: AnalyticsRepository):
        self.bot = bot
        self.repository = repository

    async def get_post_views(self, post_id: int, admin_id: int) -> int | None:
        """
        Fetches the view count for a specific post using a forward-and-delete workaround.
        """
        post_details = await self.repository.get_post_details(post_id)

        if not post_details or not post_details.get("sent_message_id"):
            logger.warning(f"Post {post_id} not found or was not sent successfully.")
            return None

        channel_id = post_details["channel_id"]
        message_id = post_details["sent_message_id"]

        try:
            # Use forward_messages (plural) as it returns the message with the .views attribute
            forwarded_messages = await self.bot.forward_messages(
                chat_id=admin_id,
                from_chat_id=channel_id,
                message_ids=[message_id],
                disable_notification=True
            )
            
            # The result is a list, so we get the first item
            forwarded_message = forwarded_messages[0]
            view_count = forwarded_message.views

            # Immediately delete the forwarded message so the admin doesn't see it
            await self.bot.delete_message(
                chat_id=admin_id,
                message_id=forwarded_message.message_id
            )

            return view_count
        except (TelegramBadRequest, IndexError) as e:
            logger.error(f"API error fetching views for message {message_id} in channel {channel_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching views for post {post_id}: {e}")
            return None
