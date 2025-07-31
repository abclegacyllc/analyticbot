import asyncpg
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# --- UserRepository ---
class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_user(self, user_id: int, username: Optional[str], role: str = "admin", referrer_id: Optional[int] = None):
        async with self.pool.acquire() as conn:
            await conn.execute(""" INSERT INTO users (user_id, username, role, registration_date, is_banned, referrer_id) VALUES ($1, $2, $3, $4, FALSE, $5) ON CONFLICT (user_id) DO NOTHING """, user_id, username, role, datetime.now(timezone.utc), referrer_id)

    async def get_user_role(self, user_id: int) -> Optional[str]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT role FROM users WHERE user_id = $1", user_id)
            return row["role"] if row else None

# --- ChannelRepository ---
class ChannelRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_channel(self, channel_id: int, admin_id: int, plan: str = "free"):
        async with self.pool.acquire() as conn:
            await conn.execute(""" INSERT INTO channels (channel_id, admin_id, plan, status) VALUES ($1, $2, $3, 'active') ON CONFLICT (channel_id) DO NOTHING """, channel_id, admin_id, plan)

# --- SchedulerRepository ---
class SchedulerRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_scheduled_post(self, channel_id: int, text: str, schedule_time: datetime) -> int:
        """Saves a new post to the database and returns its unique ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(""" INSERT INTO scheduled_posts (channel_id, text, schedule_time, status) VALUES ($1, $2, $3, 'pending') RETURNING post_id """, channel_id, text, schedule_time)
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
            await conn.execute(""" UPDATE scheduled_posts SET sent_message_id = $1 WHERE post_id = $2 """, message_id, post_id)

# --- NEW AnalyticsRepository ---
class AnalyticsRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_post_details(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves details needed for analytics, like channel_id and sent_message_id."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT channel_id, sent_message_id
                FROM scheduled_posts
                WHERE post_id = $1 AND status = 'sent'
            """, post_id)
