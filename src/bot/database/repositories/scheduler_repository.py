import asyncpg
from datetime import datetime
# --- IMPORT LIST AND ANY ---
from typing import Optional, Dict, Any, List

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
# --- NEW METHOD 1: GET PENDING POSTS ---
    async def get_pending_posts_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves all posts with 'pending' status for a specific user."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT
                    sp.post_id,
                    sp.text,
                    sp.schedule_time,
                    c.channel_name
                FROM scheduled_posts sp
                JOIN channels c ON sp.channel_id = c.channel_id
                WHERE c.admin_id = $1 AND sp.status = 'pending'
                ORDER BY sp.schedule_time ASC;
                """,
                user_id
            )

    # --- NEW METHOD 2: DELETE POST ---
    async def delete_scheduled_post(self, post_id: int) -> bool:
        """Deletes a post from the database and returns True if successful."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM scheduled_posts WHERE post_id = $1", post_id)
            # The result is a string like 'DELETE 1', so we check if a row was deleted.
            return result != 'DELETE 0'
