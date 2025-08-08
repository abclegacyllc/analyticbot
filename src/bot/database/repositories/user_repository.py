from datetime import datetime
from asyncpg import Pool
from typing import List, Dict, Any, Optional

from src.bot.database.models import scheduled_posts

class SchedulerRepository:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create_scheduled_post(self, user_id: int, channel_id: int, post_text: str, schedule_time: datetime,
                                    media_id: Optional[str] = None, media_type: Optional[str] = None,
                                    inline_buttons: Optional[Dict[str, Any]] = None) -> int:
        query = """
            INSERT INTO scheduled_posts (user_id, channel_id, post_text, schedule_time, media_id, media_type, inline_buttons, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
            RETURNING id;
        """
        post_id = await self._pool.fetchval(query, user_id, channel_id, post_text, schedule_time, media_id,
                                            media_type, inline_buttons)
        return post_id

    async def get_scheduled_posts_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        query = "SELECT * FROM scheduled_posts WHERE user_id = $1 AND status = 'pending' ORDER BY schedule_time ASC;"
        return await self._pool.fetch(query, user_id)

    async def delete_scheduled_post(self, post_id: int, user_id: int) -> bool:
        query = "DELETE FROM scheduled_posts WHERE id = $1 AND user_id = $2;"
        result = await self._pool.execute(query, post_id, user_id)
        return result != 'DELETE 0'

    async def update_post_status(self, post_id: int, status: str):
        query = "UPDATE scheduled_posts SET status = $1 WHERE id = $2;"
        await self._pool.execute(query, status, post_id)

    async def get_pending_posts_to_send(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM scheduled_posts WHERE schedule_time <= NOW() AND status = 'pending';"
        return await self._pool.fetch(query)

    # --- YANGI METOD ---
    async def count_user_posts_this_month(self, user_id: int) -> int:
        """
        Foydalanuvchining joriy oyda yaratgan postlari sonini hisoblaydi.
        """
        query = """
            SELECT COUNT(*) FROM scheduled_posts
            WHERE user_id = $1 AND
                  created_at >= date_trunc('month', CURRENT_TIMESTAMP);
        """
        count = await self._pool.fetchval(query, user_id)
        return count or 0
