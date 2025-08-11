import asyncpg
from typing import Optional, Dict, Any, List

class ChannelRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_channel(
        self, channel_id: int, user_id: int, title: str, username: str | None = None
    ) -> None:
        """Adds a new channel to the database for a specific user.

        If the channel already exists, its title and username are refreshed.
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO channels (id, user_id, title, username)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE
                    SET title = EXCLUDED.title,
                        username = EXCLUDED.username
                """,
                channel_id,
                user_id,
                title,
                username,
            )

    async def get_channel_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single channel by its ID."""

        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("SELECT * FROM channels WHERE id = $1", channel_id)
            return dict(record) if record else None

    async def count_user_channels(self, user_id: int) -> int:
        """Count how many channels a user has registered."""

        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM channels WHERE user_id = $1", user_id
            )

    async def get_user_channels(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all channels registered by a user."""

        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT id, title, username FROM channels WHERE user_id = $1",
                user_id,
            )
            return [dict(record) for record in records]

    async def delete_channel(self, channel_id: int) -> bool:
        """Delete a channel by its ID."""

        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM channels WHERE id = $1", channel_id)
            return result != "DELETE 0"