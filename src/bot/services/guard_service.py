import redis.asyncio as redis

class GuardService:
    def __init__(self, redis_conn: redis.Redis):
        self.redis = redis_conn

    def _key(self, channel_id: int) -> str:
        return f"blacklist:{channel_id}"

    async def add_word(self, channel_id: int, word: str):
        await self.redis.sadd(self._key(channel_id), word.lower())

    async def remove_word(self, channel_id: int, word: str):
        await self.redis.srem(self._key(channel_id), word.lower())

    async def list_words(self, channel_id: int):
        return await self.redis.smembers(self._key(channel_id))

    async def is_blocked(self, channel_id: int, text: str) -> bool:
        blocked_words = await self.list_words(channel_id)
        text = text.lower()
        return any(word in text for word in blocked_words)
