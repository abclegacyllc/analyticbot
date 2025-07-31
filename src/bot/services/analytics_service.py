from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from src.bot.database.repository import AnalyticsRepository, SchedulerRepository
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, bot: Bot, repository: AnalyticsRepository, scheduler_repository: SchedulerRepository):
        self.bot = bot
        self.repository = repository
        self.scheduler_repository = scheduler_repository

    async def get_post_views(self, post_id: int, admin_id: int) -> int | None:
        """
        Fetches the view count for a specific post using an invisible edit workaround.
        """
        post_details = await self.repository.get_post_details(post_id)

        if not post_details or not post_details.get("sent_message_id"):
            logger.warning(f"Post {post_id} not found or was not sent successfully.")
            return None

        channel_id = post_details["channel_id"]
        message_id = post_details["sent_message_id"]
        
        # We need the original text to perform the harmless edit
        full_post = await self.scheduler_repository.get_scheduled_post(post_id)
        if not full_post:
             return None
        post_text = full_post.get("text")

        # If there is no text, we can't edit, so we can't get views this way.
        if not post_text:
            logger.warning(f"Post {post_id} has no text to edit, cannot fetch views.")
            return None

        try:
            # Add a zero-width space to the end of the text to make it "different"
            edited_text = post_text + "\u200B"

            # Perform the invisible edit to get the updated message object
            updated_message = await self.bot.edit_message_text(
                text=edited_text,
                chat_id=channel_id,
                message_id=message_id
            )
            
            # The view count is in this updated message object
            return updated_message.views
        except TelegramBadRequest as e:
            logger.error(f"Telegram API error fetching views for message {message_id}: {e}")
            # Revert to the original text if the edit fails for some other reason
            await self.bot.edit_message_text(text=post_text, chat_id=channel_id, message_id=message_id)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching views for post {post_id}: {e}")
            return None
