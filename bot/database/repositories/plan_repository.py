import asyncpg
from typing import Optional, Dict, Any

class PlanRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_plan_by_name(self, plan_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the limits for a specific plan by its name."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM plans WHERE plan_name = $1", plan_name)
