import asyncpg
from typing import Optional, Dict, Any

class AnalyticsRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_post_details(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves details needed for analytics, like channel_id and sent_message_id."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT channel_id, sent_message_id
                FROM scheduled_posts
                WHERE post_id = $1 AND status = 'sent'
                """,
                post_id
            )
