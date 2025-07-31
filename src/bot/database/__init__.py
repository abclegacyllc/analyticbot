import asyncpg
from src.bot.config import DATABASE_URL

async def create_pool():
    # Bu funksiya avval repository.py da edi, endi shu yerda bo'lishi kerak
    return await asyncpg.create_pool(DATABASE_URL)
