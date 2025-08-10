import asyncio
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.bot.database.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository, bot: Bot):
        self.analytics_repository = analytics_repository
        self.bot = bot

    async def update_all_post_views(self, channel_id: int):
        """
        Barcha postlarning ko'rishlar sonini to'g'ridan-to'g'ri Telegramdan so'rab olib,
        ma'lumotlar bazasini yangilaydi. Bu eng to'g'ri yondashuv.
        Telegram "flood limits" ga tushmaslik uchun har bir so'rov orasida kichik pauza qilinadi.
        """
        posts = await self.analytics_repository.get_all_posts(channel_id)

        if not posts:
            return

        for post in posts:
            try:
                # To'g'ridan-to'g'ri xabarni ID si orqali olishga harakat qilamiz.
                # get_messages xabarlar ro'yxatini qaytaradi.
                messages = await self.bot.get_messages(
                    chat_id=channel_id,
                    message_ids=[post.message_id]
                )
                
                if messages and messages[0].views is not None:
                    # Ma'lumotlar bazasidagi ko'rishlar sonini yangilaymiz
                    await self.analytics_repository.update_post_views(
                        post_id=post.id, views=messages[0].views
                    )
                
                # Telegramga bosimni kamaytirish uchun kutish
                await asyncio.sleep(0.5)

            except TelegramBadRequest as e:
                # Agar post o'chirilgan bo'lsa yoki boshqa xatolik yuz bersa
                print(f"Could not get message {post.message_id} from channel {channel_id}: {e}")
                # Bu postni DB'dan o'chirish logikasini qo'shish mumkin
                # await self.analytics_repository.delete_post(post.id)
                continue
            except Exception as e:
                print(f"An unexpected error occurred for post {post.id}: {e}")
                continue


    async def get_posts_ordered_by_views(self, channel_id: int):
        return await self.analytics_repository.get_posts_ordered_by_views(channel_id)
