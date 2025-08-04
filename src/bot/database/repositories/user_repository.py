from asyncpg.pool import Pool
from typing import Optional, Dict, Any

class UserRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(sql, user_id)

    async def create_user(self, user_id: int, username: str | None):
        sql = """
            INSERT INTO users (user_id, username, role)
            VALUES ($1, $2, 'user')
            ON CONFLICT (user_id) DO NOTHING;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(sql, user_id, username)

    async def get_user_plan_name(self, user_id: int) -> Optional[str]:
        """Retrieves the user's current plan name by joining with the plans table."""
        sql = """
            SELECT p.plan_name
            FROM users u
            JOIN plans p ON u.plan_id = p.plan_id
            WHERE u.user_id = $1;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(sql, user_id)
