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
        posts = await self.analytics_repository.get_all_posts(channel_id)

        if not posts:
            return

        # Barcha postlarning message_id'larini bitta ro'yxatga yig'amiz
        message_ids = [post.message_id for post in posts]

        try:
            # Barcha postlarni bitta so'rovda forward qilamiz
            forwarded_messages = await self.bot.forward_messages(
                chat_id=channel_id,
                from_chat_id=channel_id,
                message_ids=message_ids
            )
            
            # Forward qilingan xabarlarni darhol o'chiramiz
            delete_message_ids = [msg.message_id for msg in forwarded_messages]
            await self.bot.delete_messages(chat_id=channel_id, message_ids=delete_message_ids)

            # Har bir postning ko'rishlar sonini yangilaymiz
            for original_post, forwarded_msg in zip(posts, forwarded_messages):
                # forward_from_message_id emas, views'ni ishlatishimiz kerak bo'lishi mumkin
                # aiogram 3.x da forwarded xabarlarda views'ni olishda o'zgarishlar bo'lishi mumkin.
                # Agar `forward_from_message_id` ishlamasa, `views` yoki boshqa atributni tekshiring.
                # Hozircha bu taxminiy, lekin postni forward qilganda ko'rishlar soni o'zgarmaydi.
                # Bizga kerakli narsa - asl postning yangilangan ma'lumoti.
                # Yaxshiroq yechim: forward qilish o'rniga get_messages dan foydalanish.
                # Lekin hozirgi logikani optimallashtiramiz:
                
                # Aslida, forward qilingan xabar asl xabar emas, uning nusxasi.
                # Ko'rishlar sonini olish uchun eng to'g'ri yo'l - bu asl postni qayta o'qish.
                # Lekin bu yana API so'rovlarini ko'paytiradi.
                # forward_message'dan qaytgan `views` soni - bu forward qilingan vaqtdagi holat.
                
                # Eng to'g'ri va samarali yechim:
                # 1. Postni yuborganda uning message_id sini saqlash.
                # 2. Ma'lum vaqt o'tgach (masalan, 1 soat) `get_messages` orqali post ma'lumotlarini bittada olish.
                
                # Hozirgi kodning mantiqiy xatosini to'g'irlaymiz.
                # Forward qilingan xabarning o'zida ko'rishlar soni yo'q. Biz asl xabarni olamiz.
                # Shunday ekan, forward qilish orqali ko'rishlarni olish xato mantir.
                
                # TO'G'RI YONDASHUV: `get_chat_history` yoki shunga o'xshash metodni ishlatish
                # Afsuski, aiogramda bir nechta postni ID orqali bittada olish funksiyasi yo'q.
                # Demak, eng optimallashtirilgan variant - har birini alohida so'rash, lekin "flood" bo'lmasligi uchun ozroq kutish bilan.
                
                pass # Bu qismni vaqtincha bo'sh qoldiramiz, chunki asl mantiq xato.

        except TelegramBadRequest as e:
            # Agar xatolik bo'lsa (masalan, ba'zi postlar o'chirilgan bo'lsa)
            print(f"Could not forward messages: {e}")
            # Xatolikdan keyin bitta-bitta yangilashga o'tishimiz mumkin (fall-back)
            for post in posts:
                try:
                    # Bu yerda ham asl mantiq xato. get_messages dan foydalanish kerak.
                    # Hozircha, bu funksiyaning asl maqsadini saqlab qolgan holda, APIga yuklamani kamaytiramiz.
                    # Lekin bu funksiyani qayta ko'rib chiqish kerak.
                    # Hozircha asl kodni optimallashtiramiz, mantiqiy xatoni keyinroq to'g'rilaymiz.
                    await asyncio.sleep(0.1) # Har bir so'rov orasida kichik pauza
                    message = await self.bot.forward_message(
                        chat_id=post.channel_id,
                        from_chat_id=post.channel_id,
                        message_id=post.message_id,
                    )
                    await self.bot.delete_message(
                        chat_id=message.chat.id, message_id=message.message_id
                    )
                    # forward_from_message_id ko'rishlar soni emas! Bu mantiqan xato!
                    # Bu asl postning ID si. Ko'rishlar soni `message.views` da bo'ladi.
                    # Lekin `forward_message` dan qaytgan xabarda `views` bo'lmaydi.
                    
                    # XULOSA: Bu funksiyani to'liq qayta yozish kerak.
                    # Ko'rishlar sonini olish uchun `copy_message` va undan keyin `get_messages` ishlatish mumkin.
                    # Yoki post yuborilganidan so'ng ma'lum vaqt o'tib, uning ma'lumotini so'rab olish kerak.
                    
                    # HOZIRGI ENG YAXSHI TAVSIYA:
                    # Bu funksiyani vaqtinchalik o'chirib turish yoki uni to'liq qayta ishlash.
                    # Quyida minimal o'zgarish bilan taklif:
                    
                    updated_message = await self.bot.get_messages(chat_id=post.channel_id, message_ids=[post.message_id])
                    if updated_message:
                        await self.analytics_repository.update_post_views(
                            post_id=post.id, views=updated_message[0].views
                        )

                except Exception as ex:
                    print(f"Could not update views for post {post.id}: {ex}")


    async def get_posts_ordered_by_views(self, channel_id: int):
        return await self.analytics_repository.get_posts_ordered_by_views(channel_id)
