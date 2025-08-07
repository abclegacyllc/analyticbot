import asyncpg
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

class SchedulerRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # --- YECHIM: 'inline_buttons' argumenti qo'shildi ---
    async def create_scheduled_post(
        self,
        channel_id: int,
        schedule_time: datetime,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
        inline_buttons: Optional[str] = None  # JSON satri sifatida qabul qilamiz
    ) -> int:
        """
        Creates a new post in the database. Now accepts inline_buttons as a JSON string.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO scheduled_posts (channel_id, text, file_id, file_type, schedule_time, inline_buttons)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING post_id
                """,
                channel_id, text, file_id, file_type, schedule_time, inline_buttons
            )

    async def get_scheduled_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single scheduled post, including media info.
        """
        async with self.pool.acquire() as conn:
            # JOIN so'rovini qo'shamiz, chunki inline tugmalar uchun kanal nomi kerak bo'lishi mumkin
            return await conn.fetchrow(
                """
                SELECT sp.*, c.channel_name 
                FROM scheduled_posts sp
                JOIN channels c ON sp.channel_id = c.channel_id
                WHERE sp.post_id = $1
                """,
                post_id
            )

    async def update_post_status(self, post_id: int, status: str):
        """Updates the status of a post (e.g., 'pending', 'sent', 'failed')."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE scheduled_posts SET status = $1 WHERE post_id = $2",
                status, post_id
            )
            
    async def set_sent_message_id(self, post_id: int, message_id: int):
        """Stores the message_id of the post after it has been sent."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE scheduled_posts SET sent_message_id = $1 WHERE post_id = $2", message_id, post_id)

    async def get_pending_posts_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves all posts with 'pending' status for a specific user."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT
                    sp.post_id,
                    sp.text,
                    sp.file_id,
                    sp.file_type,
                    sp.schedule_time,
                    sp.inline_buttons,
                    c.channel_name
                FROM scheduled_posts sp
                JOIN channels c ON sp.channel_id = c.channel_id
                WHERE c.admin_id = $1 AND sp.status = 'pending'
                ORDER BY sp.schedule_time ASC;
                """,
                user_id
            )

    async def delete_scheduled_post(self, post_id: int) -> bool:
        """Deletes a post from the database and returns True if successful."""
        async with self.pool.acquire() as conn:
            # Bog'liqliklar sababli avval `post_views` dan o'chirishimiz kerak bo'lishi mumkin
            await conn.execute("DELETE FROM post_views WHERE post_id = $1", post_id)
            result = await conn.execute("DELETE FROM scheduled_posts WHERE post_id = $1", post_id)
            return result != 'DELETE 0'
            
    async def count_user_posts_this_month(self, user_id: int) -> int:
        """Counts how many posts a user has created in the current calendar month."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM scheduled_posts sp
                JOIN channels c ON sp.channel_id = c.channel_id
                WHERE c.admin_id = $1
                  AND sp.created_at >= date_trunc('month', CURRENT_DATE);
                """,
                user_id
            )
