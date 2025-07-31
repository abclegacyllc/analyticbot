import redis.asyncio as redis
from typing import Set

class GuardService:
    def __init__(self, redis_conn: redis.Redis):
        self.redis = redis_conn

    def _key(self, channel_id: int) -> str:
        return f"blacklist:{channel_id}"

    async def add_word(self, channel_id: int, word: str):
        await self.redis.sadd(self._key(channel_id), word.lower())

    async def remove_word(self, channel_id: int, word: str):
        await self.redis.srem(self._key(channel_id), word.lower())

    async def list_words(self, channel_id: int) -> Set[str]:
        words = await self.redis.smembers(self._key(channel_id))
        # Redis'dan kelgan 'bytes' ni 'str' ga o'tkazamiz
        return {word.decode('utf-8') for word in words}

    async def is_blocked(self, channel_id: int, text: str) -> bool:
        blocked_words = await self.list_words(channel_id)
        if not blocked_words:
            return False
        
        text_lower = text.lower()
        # Har bir so'zni alohida tekshiramiz
        for word in text_lower.split():
            if word in blocked_words:
                return True
        return False
