from asyncpg import Pool
from typing import List, Dict, Any

class AnalyticsRepository:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def log_sent_post(self, scheduled_post_id: int, channel_id: int, message_id: int):
        """
        Kanalga yuborilgan post haqidagi ma'lumotni 'sent_posts' jadvaliga yozadi.
        """
        query = """
            INSERT INTO sent_posts (scheduled_post_id, channel_id, message_id)
            VALUES ($1, $2, $3);
        """
        await self._pool.execute(query, scheduled_post_id, channel_id, message_id)

    async def get_all_trackable_posts(self, interval_days: int = 7) -> List[Dict[str, Any]]:
        """
        Ko'rishlar sonini tekshirish kerak bo'lgan barcha postlarni oladi.
        Masalan, oxirgi 7 kun ichida yuborilganlar.
        """
        query = """
            SELECT
                sp.id AS scheduled_post_id,
                sp.views,
                snt.channel_id,
                snt.message_id
            FROM scheduled_posts sp
            JOIN sent_posts snt ON sp.id = snt.scheduled_post_id
            WHERE snt.sent_at >= NOW() - ($1 || ' days')::INTERVAL;
        """
        return await self._pool.fetch(query, interval_days)

    async def update_post_views(self, scheduled_post_id: int, views: int):
        """
        Postning ko'rishlar sonini 'scheduled_posts' jadvalida yangilaydi.
        """
        query = "UPDATE scheduled_posts SET views = $1 WHERE id = $2;"
        await self._pool.execute(query, views, scheduled_post_id)
