import pytest
import fakeredis.aioredis
from src.bot.services.guard_service import GuardService

@pytest.fixture
async def redis_conn():
    # Haqiqiy Redis o'rniga fake (soxta) Redis ishlatamiz
    return fakeredis.aioredis.FakeRedis()

@pytest.fixture
async def guard_service(redis_conn):
    return GuardService(redis_conn)

@pytest.mark.asyncio
async def test_add_and_list_words(guard_service: GuardService):
    channel_id = 12345
    await guard_service.add_word(channel_id, "test1")
    await guard_service.add_word(channel_id, "TEST2") # kichik harflarga o'tishi kerak

    words = await guard_service.list_words(channel_id)
    assert "test1" in words
    assert "test2" in words
    assert len(words) == 2

@pytest.mark.asyncio
async def test_remove_word(guard_service: GuardService):
    channel_id = 12345
    await guard_service.add_word(channel_id, "word_to_remove")
    
    # Olib tashlash
    await guard_service.remove_word(channel_id, "word_to_remove")
    words = await guard_service.list_words(channel_id)
    assert "word_to_remove" not in words

@pytest.mark.asyncio
async def test_is_blocked(guard_service: GuardService):
    channel_id = 54321
    await guard_service.add_word(channel_id, "spam")
    await guard_service.add_word(channel_id, "reklama")

    assert await guard_service.is_blocked(channel_id, "Bu oddiy xabar") == False
    assert await guard_service.is_blocked(channel_id, "Bu yerda SPAM bor") == True
    assert await guard_service.is_blocked(channel_id, "Eng yaxshi reklama bizda") == True
    assert await guard_service.is_blocked(channel_id, "Boshqa kanaldagi xabar") == False
