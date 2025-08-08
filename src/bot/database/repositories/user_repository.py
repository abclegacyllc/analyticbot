import asyncpg
from typing import Optional

class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_user(self, user_id: int, username: Optional[str]):
        """
        Creates a new user in the database if they don't already exist.
        """
        query = """
            INSERT INTO users (id, username)
            VALUES ($1, $2)
            ON CONFLICT (id) DO NOTHING
        """
        await self._pool.execute(query, user_id, username)

    async def user_exists(self, user_id: int) -> bool:
        """
        Checks if a user with the given user_id exists in the database.
        """
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)"
        return await self._pool.fetchval(query, user_id)

    async def get_user_plan_name(self, user_id: int) -> Optional[str]:
        """
        Retrieves the name of the user's current subscription plan.
        """
        query = """
            SELECT p.name
            FROM users u
            JOIN plans p ON u.plan_id = p.id
            WHERE u.id = $1
        """
        return await self._pool.fetchval(query, user_id)
