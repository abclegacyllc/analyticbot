from asyncpg.pool import Pool

class UserRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_user(self, user_id: int):
        sql = "SELECT * FROM users WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(sql, user_id)

    async def create_user(self, user_id: int, username: str | None):
        """
        Creates a new user or does nothing if the user already exists.
        """
        # --- THIS IS THE CORRECTED SQL ---
        # We changed "registration_date" to "created_at" to match the database table.
        sql = """
            INSERT INTO users (user_id, username, created_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id) DO NOTHING;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(sql, user_id, username)

    async def update_user_plan(self, user_id: int, plan_id: int):
        sql = "UPDATE users SET plan_id = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, plan_id, user_id)
