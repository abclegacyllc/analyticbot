import asyncpg
from datetime import datetime, timezone
from typing import Optional

class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_user(self, user_id: int, username: Optional[str], role: str = "admin", referrer_id: Optional[int] = None):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, role, registration_date, is_banned, referrer_id)
                VALUES ($1, $2, $3, $4, FALSE, $5)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, username, role, datetime.now(timezone.utc), referrer_id)

    async def get_user_role(self, user_id: int) -> Optional[str]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT role FROM users WHERE user_id = $1", user_id)
            return row["role"] if row else None

class ChannelRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_channel(self, channel_id: int, admin_id: int, plan: str = "free"):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO channels (channel_id, admin_id, plan, status)
                VALUES ($1, $2, $3, 'active')
                ON CONFLICT (channel_id) DO NOTHING
            """, channel_id, admin_id, plan)
