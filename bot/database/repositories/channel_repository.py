import asyncpg
from typing import Optional, Dict, Any, List

class ChannelRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # --- UPDATED METHOD ---
    async def create_channel(self, channel_id: int, admin_id: int, channel_name: str):
        """Adds a new channel to the database for a specific admin."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO channels (channel_id, admin_id, channel_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (channel_id) DO UPDATE SET channel_name = EXCLUDED.channel_name
                """,
                channel_id, admin_id, channel_name
            )

    async def get_channel_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single channel by its ID."""
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("SELECT * FROM channels WHERE channel_id = $1", channel_id)
            return dict(record) if record else None

    async def count_user_channels(self, user_id: int) -> int:
        """Counts how many channels a user has registered."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM channels WHERE admin_id = $1", user_id)
            
    # --- NEW METHOD TO GET ALL CHANNELS ---
    async def get_user_channels(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves all channels registered by a user."""
        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT channel_id, channel_name FROM channels WHERE admin_id = $1", user_id)
            return [dict(record) for record in records]

    async def delete_channel(self, channel_id: int) -> bool:
        """Deletes a channel by its ID."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)
            return result != 'DELETE 0'