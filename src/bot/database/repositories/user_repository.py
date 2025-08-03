# src/bot/database/repositories/user_repository.py

import asyncpg
from datetime import datetime, timezone
from typing import Optional

class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_user(
        self,
        user_id: int,
        username: Optional[str],
        role: str = "admin",
        referrer_id: Optional[int] = None
    ):
        """Creates a new user or does nothing if the user already exists."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, role, registration_date, is_banned, referrer_id)
                VALUES ($1, $2, $3, $4, FALSE, $5)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id, username, role, datetime.now(timezone.utc), referrer_id
            )

    async def get_user_role(self, user_id: int) -> Optional[str]:
        """Retrieves the role of a specific user."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT role FROM users WHERE user_id = $1", user_id)
            return row["role"] if row else None

    # --- YANGI METOD ---
    async def get_user_plan(self, user_id: int) -> Optional[str]:
        """Retrieves the user's current subscription plan."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT plan FROM users WHERE user_id = $1", user_id)
