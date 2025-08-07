import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.bot.database.repositories import SchedulerRepository
from src.bot.tasks import send_scheduled_message

class SchedulerService:
    # Endi bu servisga APScheduler keraksiz
    def __init__(self, repo: SchedulerRepository):
        self.repo = repo

    async def schedule_post(
        self,
        channel_id: int,
        text: Optional[str],
        schedule_time: datetime,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
        inline_buttons: Optional[List[Dict[str, str]]] = None
    ):
        buttons_json = json.dumps(inline_buttons) if inline_buttons else None

        post_id = await self.repo.create_scheduled_post(
            channel_id=channel_id,
            text=text,
            schedule_time=schedule_time,
            file_id=file_id,
            file_type=file_type,
            inline_buttons=buttons_json
        )
        
        # --- MUHIM O'ZGARISH: Vazifani Celery'ga yuborish ---
        # `apply_async` metodi vazifani belgilangan vaqtda ishga tushirishni ta'minlaydi
        send_scheduled_message.apply_async(args=[post_id], eta=schedule_time)

    async def delete_post(self, post_id: int):
        # Hozircha vazifani Celery'dan o'chirish murakkab.
        # Shuning uchun oddiyroq yechim qilamiz: postning statusini o'zgartiramiz.
        # send_scheduled_message funksiyasi statusni tekshirib, 'cancelled' bo'lsa,
        # postni yubormaydi.
        await self.repo.update_post_status(post_id, 'cancelled')
