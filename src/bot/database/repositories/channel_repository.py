import asyncpg
from typing import Optional, Dict, Any

class ChannelRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_channel(self, channel_id: int, admin_id: int, plan: str = "free"):
        """Adds a new channel to the database for a specific admin."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO channels (channel_id, admin_id, plan, status)
                VALUES ($1, $2, $3, 'active')
                ON CONFLICT (channel_id) DO NOTHING
                """,
                channel_id, admin_id, plan
            )

    async def get_channel_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single channel by its ID."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM channels WHERE channel_id = $1", channel_id)

    # --- NEW METOD ---
    async def count_user_channels(self, user_id: int) -> int:
        """Counts how many channels a user has registered."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM channels WHERE admin_id = $1", user_id)
