import asyncpg
from datetime import datetime
from typing import Optional, Dict, Any

class SchedulerRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_scheduled_post(self, channel_id: int, text: str, schedule_time: datetime) -> int:
        """Saves a new post to the database and returns its unique ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO scheduled_posts (channel_id, text, schedule_time, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING post_id
                """,
                channel_id, text, schedule_time
            )
            return row["post_id"]

    async def get_scheduled_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single scheduled post by its ID."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM scheduled_posts WHERE post_id = $1", post_id)

    async def update_post_status(self, post_id: int, status: str):
        """Updates the status of a post (e.g., 'sent', 'failed')."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE scheduled_posts SET status = $1 WHERE post_id = $2", status, post_id)

    async def set_sent_message_id(self, post_id: int, message_id: int):
        """Saves the message_id of a sent post for analytics."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE scheduled_posts SET sent_message_id = $1 WHERE post_id = $2", message_id, post_id)

    # --- NEW METOD ---
    async def count_user_posts_this_month(self, user_id: int) -> int:
        """Counts how many posts a user has scheduled in the current month."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM scheduled_posts sp
                JOIN channels c ON sp.channel_id = c.channel_id
                WHERE c.admin_id = $1
                AND sp.schedule_time >= date_trunc('month', CURRENT_DATE)
                """,
                user_id
            )
