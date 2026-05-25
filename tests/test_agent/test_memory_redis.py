"""RedisCache 集成测试。

需要运行中的 Redis 7 实例：
    docker compose up -d

运行方式：
    uv run pytest tests/test_agent/test_memory_redis.py -v
"""

import pytest

pytestmark = [
    pytest.mark.skipif(
        True, reason="需要运行中的 Redis 实例"
    ),
]


@pytest.fixture
async def redis_cache():
    from src.agent.memory.stores.redis_cache import RedisCache
    cache = RedisCache(env="test")
    await cache.connect()
    yield cache
    await cache.clear_all()
    await cache.close()


@pytest.mark.asyncio
async def test_connect_and_close(redis_cache):
    assert redis_cache._connected


@pytest.mark.asyncio
async def test_hot_memory(redis_cache):
    from src.agent.memory.types import MemoryItem
    memories = [
        MemoryItem(id="1", content="记忆1", type="entity", importance=0.9),
        MemoryItem(id="2", content="记忆2", type="entity", importance=0.8),
    ]
    await redis_cache.set_hot_memories("user1", memories)

    cached = await redis_cache.get_hot_memories("user1", k=10)
    assert len(cached) == 2
    assert cached[0]["content"] == "记忆1"


@pytest.mark.asyncio
async def test_session_cache(redis_cache):
    await redis_cache.set_session("session1", {"user_id": "u1", "status": "active"})

    data = await redis_cache.get_session("session1")
    assert data is not None
    assert data["user_id"] == "u1"


@pytest.mark.asyncio
async def test_session_messages(redis_cache):
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
    ]
    await redis_cache.cache_session_messages("session1", messages)

    cached = await redis_cache.get_session_messages("session1")
    assert cached is not None
    assert len(cached) == 2


@pytest.mark.asyncio
async def test_agent_state(redis_cache):
    await redis_cache.set_agent_state("agent1", "session1", {"goal": "测试"})

    state = await redis_cache.get_agent_state("agent1", "session1")
    assert state is not None
    assert state["goal"] == "测试"


@pytest.mark.asyncio
async def test_distributed_lock(redis_cache):
    acquired = await redis_cache.acquire_lock("test-lock")
    assert acquired is True

    re_acquired = await redis_cache.acquire_lock("test-lock")
    assert re_acquired is False

    released = await redis_cache.release_lock("test-lock")
    assert released is True


@pytest.mark.asyncio
async def test_lock_context_manager(redis_cache):
    async with redis_cache.lock("ctx-lock") as acquired:
        assert acquired is True

    async with redis_cache.lock("ctx-lock") as acquired:
        assert acquired is True


@pytest.mark.asyncio
async def test_rate_limit(redis_cache):
    allowed, remaining = await redis_cache.check_rate_limit(
        "user1", "llm", 3, 60
    )
    assert allowed is True
    assert remaining >= 0


@pytest.mark.asyncio
async def test_embedding_cache(redis_cache):
    await redis_cache.set_embedding_cache("hash123", [0.1, 0.2, 0.3])

    cached = await redis_cache.get_embedding_cache("hash123")
    assert cached is not None
    assert cached == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_cache_stats(redis_cache):
    await redis_cache.set_session("stats-test", {"data": "test"})

    stats = await redis_cache.get_cache_stats()
    assert "total_keys" in stats
    assert stats["connected"] is True


@pytest.mark.asyncio
async def test_clear_all(redis_cache):
    await redis_cache.set_session("clear-test", {"data": "test"})

    deleted = await redis_cache.clear_all()
    assert deleted >= 1
