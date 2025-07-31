import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from datetime import date, timedelta

# This file does not need models for its raw SQL queries,
# so the problematic import has been removed.

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

            base_channels_query = "SELECT channel_id FROM channels WHERE admin_id = $1"
            query_params = [user_id]
            
            main_query = """
                SELECT
                    CAST(p.schedule_time AS DATE) AS view_date,
                    SUM(p.views) AS total_views
                FROM
                    scheduled_posts p
                WHERE
                    p.channel_id IN ({channels_query})
                    AND p.status = 'sent'
                    AND p.views IS NOT NULL
                    AND CAST(p.schedule_time AS DATE) BETWEEN ${param_start} AND ${param_end}
                GROUP BY
                    view_date
                ORDER BY
                    view_date;
            """

            if channel_id:
                channels_query = base_channels_query + " AND channel_id = $2"
                query_params.append(channel_id)
                param_start, param_end = 3, 4
            else:
                channels_query = base_channels_query
                param_start, param_end = 2, 3

            query_params.extend([start_date, end_date])
            
            final_stmt = main_query.format(
                channels_query=channels_query, 
                param_start=param_start, 
                param_end=param_end
            )

            # asyncpg fetchall() returns a list of Record objects, which behave like tuples
            return await conn.fetch(final_stmt, *query_params)
