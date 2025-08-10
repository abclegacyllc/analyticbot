from typing import List
from aiogram import Bot

from src.bot.database.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository, bot: Bot):
        self.analytics_repository = analytics_repository
        self.bot = bot

    async def update_all_post_views(self, channel_id: int):
        posts = await self.analytics_repository.get_all_posts(channel_id)

        if not posts:
            return

        for post in posts:
            message = await self.bot.forward_message(
                chat_id=post.channel_id,
                from_chat_id=post.channel_id,
                message_id=post.message_id,
            )
            await self.bot.delete_message(
                chat_id=message.chat.id, message_id=message.message_id
            )
            await self.analytics_repository.update_post_views(
                post_id=post.id, views=message.forward_from_message_id
            )

    async def get_posts_ordered_by_views(self, channel_id: int):
        return await self.analytics_repository.get_posts_ordered_by_views(channel_id)
