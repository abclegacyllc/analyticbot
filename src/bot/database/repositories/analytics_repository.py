import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from datetime import date, timedelta
from sqlalchemy import select, func, cast, Date

# We will need the Post model from the database to construct the query
from src/bot/database.models import Post, Channel


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

    async def get_daily_views(
        self, user_id: int, days: int = 30, channel_id: Optional[int] = None
    ) -> List[Tuple[date, int]]:
        """
        Retrieves the total daily views for a user's channels.
        Can be filtered by a specific channel_id.
        """
        async with self.pool.acquire() as conn:
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)

            # Base query to get channels owned by the user
            channels_query = "SELECT channel_id FROM channels WHERE admin_id = $1"
            query_params = [user_id]

            # If a specific channel is requested, add it to the filter
            if channel_id:
                channels_query += " AND channel_id = $2"
                query_params.append(channel_id)

            # The main query to fetch daily views
            stmt = f"""
                SELECT
                    CAST(p.schedule_time AS DATE) AS view_date,
                    SUM(p.views) AS total_views
                FROM
                    scheduled_posts p
                WHERE
                    p.channel_id IN ({channels_query})
                    AND p.status = 'sent'
                    AND p.views IS NOT NULL
                    AND CAST(p.schedule_time AS DATE) BETWEEN $3 AND $4
                GROUP BY
                    view_date
                ORDER BY
                    view_date;
            """
            # Add date range to query params
            query_params.extend([start_date, end_date])
            
            # Note: asyncpg uses $1, $2, etc. for parameter substitution. 
            # We need to adjust parameter numbering if channel_id is present.
            if channel_id:
                stmt = stmt.replace("$3", "$3").replace("$4", "$4") # No change needed if we add at the end
            else: # If no channel_id, we need to re-number the date params
                stmt = stmt.replace("$3", "$2").replace("$4", "$3")


            return await conn.fetch(stmt, *query_params)
