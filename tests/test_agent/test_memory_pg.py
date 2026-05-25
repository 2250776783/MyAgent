"""PGVectorMemoryStore 集成测试。

需要运行中的 PostgreSQL 16 + pgvector 实例：
    docker compose up -d

运行方式：
    uv run pytest tests/test_agent/test_memory_pg.py -v
"""

import pytest

from src.agent.memory.types import MemoryItem

pytestmark = [
    pytest.mark.skipif(
        True, reason="需要运行中的 PostgreSQL 实例"
    ),
]


@pytest.fixture
async def pg_store():
    from src.agent.memory.stores.pgvector_store import PGVectorMemoryStore
    store = PGVectorMemoryStore()
    await store.connect()
    yield store
    await store.aclose()


@pytest.mark.asyncio
async def test_connect_and_close(pg_store):
    assert pg_store._connected


@pytest.mark.asyncio
async def test_save_and_get(pg_store):
    item = MemoryItem(
        content="用户喜欢 Python 异步编程",
        type="coding_preference",
        importance=0.8,
        metadata={"source": "test"},
    )
    mid = await pg_store.asave(item)
    assert mid is not None

    retrieved = await pg_store.aget(mid)
    assert retrieved is not None
    assert retrieved.content == item.content
    assert retrieved.type == item.type


@pytest.mark.asyncio
async def test_vector_search(pg_store):
    embedding = [0.1] * 1536
    item = MemoryItem(
        content="Python 异步编程最佳实践",
        type="technical_memory",
        importance=0.9,
        embedding=embedding,
    )
    await pg_store.asave(item)

    results = await pg_store.asearch(embedding, k=5)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_by_type(pg_store):
    embedding = [0.2] * 1536
    item = MemoryItem(
        content="FastAPI 路由设计",
        type="technical_memory",
        importance=0.7,
        embedding=embedding,
    )
    await pg_store.asave(item)

    results = await pg_store.asearch_by_type(embedding, "technical_memory", k=5)
    assert len(results) >= 1
    assert all(r.type == "technical_memory" for r in results)


@pytest.mark.asyncio
async def test_search_by_importance(pg_store):
    embedding = [0.3] * 1536
    item = MemoryItem(
        content="重要知识",
        type="project_memory",
        importance=0.95,
        embedding=embedding,
    )
    await pg_store.asave(item)

    results = await pg_store.asearch_by_importance(embedding, min_importance=0.9, k=5)
    assert len(results) >= 1
    assert all(r.importance >= 0.9 for r in results)


@pytest.mark.asyncio
async def test_update(pg_store):
    item = MemoryItem(content="旧内容", type="entity", importance=0.5)
    mid = await pg_store.asave(item)

    await pg_store.aupdate(mid, content="新内容", importance_score=0.9)
    updated = await pg_store.aget(mid)
    assert updated is not None
    assert updated.importance == 0.9


@pytest.mark.asyncio
async def test_delete(pg_store):
    item = MemoryItem(content="待删除", type="entity", importance=0.3)
    mid = await pg_store.asave(item)

    await pg_store.adelete(mid)
    retrieved = await pg_store.aget(mid)
    assert retrieved is None


@pytest.mark.asyncio
async def test_count(pg_store):
    count_before = await pg_store.acount()
    item = MemoryItem(content="计数测试", type="entity", importance=0.5)
    await pg_store.asave(item)
    count_after = await pg_store.acount()
    assert count_after == count_before + 1


@pytest.mark.asyncio
async def test_save_session_and_messages(pg_store):
    await pg_store.save_session(
        session_id="test-session-1",
        title="测试会话",
        status="active",
    )
    msg_id = await pg_store.save_message(
        session_id="test-session-1",
        role="user",
        content="你好",
        message_index=0,
        token_count=10,
    )
    assert msg_id is not None


@pytest.mark.asyncio
async def test_save_summary(pg_store):
    sid = await pg_store.save_summary(
        session_id="test-session-1",
        summary_text="对话摘要",
        summary_type="auto",
        importance=0.8,
        message_start=0,
        message_end=5,
    )
    assert sid is not None


@pytest.mark.asyncio
async def test_save_tool_call(pg_store):
    tid = await pg_store.save_tool_call(
        session_id="test-session-1",
        tool_name="web_search",
        tool_args={"query": "天气"},
        status="success",
        duration_ms=1500,
    )
    assert tid is not None


@pytest.mark.asyncio
async def test_knowledge_cache(pg_store):
    cid = await pg_store.save_knowledge_cache(
        query_text="什么是异步编程",
        result_text="异步编程是一种...",
        token_count=50,
        ttl_seconds=3600,
    )
    assert cid is not None

    cached = await pg_store.get_knowledge_cache("什么是异步编程")
    assert cached is not None
    assert cached["result_text"] == "异步编程是一种..."


@pytest.mark.asyncio
async def test_memory_links(pg_store):
    lid = await pg_store.save_memory_link(
        source_id="mem-1",
        target_id="mem-2",
        relation_type="related_to",
        strength=0.9,
    )
    assert lid is not None

    links = await pg_store.get_memory_links("mem-1")
    assert len(links) >= 1


@pytest.mark.asyncio
async def test_agent_state(pg_store):
    sid = await pg_store.save_agent_state(
        agent_id="agent-1",
        session_id="test-session-1",
        state_type="context",
        state_data={"goal": "完成测试"},
    )
    assert sid is not None

    state = await pg_store.get_latest_agent_state(
        agent_id="agent-1",
        session_id="test-session-1",
        state_type="context",
    )
    assert state is not None
    assert state["state_data"]["goal"] == "完成测试"


@pytest.mark.asyncio
async def test_decay(pg_store):
    item = MemoryItem(content="低重要性记忆", type="entity", importance=0.05)
    await pg_store.asave(item)

    deleted = await pg_store.adecay_memories(threshold=0.3)
    assert isinstance(deleted, int)


@pytest.mark.asyncio
async def test_reinforce_memory(pg_store):
    item = MemoryItem(content="强化测试", type="entity", importance=0.6)
    mid = await pg_store.asave(item)

    await pg_store.areinforce_memory(mid)
    retrieved = await pg_store.aget(mid)
    assert retrieved is not None
    assert retrieved.importance > 0.6


@pytest.mark.asyncio
async def test_get_tool_stats(pg_store):
    await pg_store.save_tool_call(
        session_id="test-session-1",
        tool_name="web_search",
        tool_args={"q": "test"},
        status="success",
        duration_ms=100,
    )
    stats = await pg_store.get_tool_stats()
    search_stats = [s for s in stats if s["tool_name"] == "web_search"]
    assert len(search_stats) >= 1
