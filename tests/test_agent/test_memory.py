"""测试记忆系统。"""

import time
from unittest.mock import MagicMock

from src.agent import Agent
from src.agent.memory import (
    ForgettingMechanism,
    ImportanceScorer,
    MemoryItem,
    MemoryQuery,
    PromptInjector,
    WorkingMemory,
)
from src.agent.memory.types import Episode, Reflection
from src.llm import Message


# =========================================================================
# WorkingMemory
# =========================================================================

class TestWorkingMemory:
    def test_init_defaults(self) -> None:
        wm = WorkingMemory()
        assert wm.max_tokens == 4096
        assert wm.reserve_tokens == 1024

    def test_budget(self) -> None:
        wm = WorkingMemory(max_tokens=3000, reserve_tokens=500)
        assert wm.budget == 2500

    def test_trim_under_budget_no_change(self) -> None:
        wm = WorkingMemory(max_tokens=10000)
        msgs = [
            Message(role="system", content="你是一个助手"),
            Message(role="user", content="你好"),
            Message(role="assistant", content="你好！有什么可以帮助你的？"),
        ]
        result = wm.trim(msgs)
        assert result == msgs  # 未超预算，不裁剪

    def test_trim_empty(self) -> None:
        wm = WorkingMemory()
        assert wm.trim([]) == []

    def test_trim_keeps_system_prompt(self) -> None:
        wm = WorkingMemory(max_tokens=50)  # 极小的预算
        msgs = [
            Message(role="system", content="sys"),
            Message(role="user", content="hello " * 100),
            Message(role="assistant", content="world " * 100),
        ]
        result = wm.trim(msgs)
        assert result[0].role == "system"
        assert result[0].content == "sys"

    def test_trim_keeps_at_least_one_user(self) -> None:
        wm = WorkingMemory(max_tokens=20)
        msgs = [
            Message(role="system", content="sys"),
            Message(role="user", content="hello " * 100),
        ]
        result = wm.trim(msgs)
        assert any(m.role == "user" for m in result)

    def test_reset_noop(self) -> None:
        wm = WorkingMemory()
        wm.reset()  # should not raise


# =========================================================================
# MemoryItem / MemoryQuery / Episode / Reflection
# =========================================================================

class TestMemoryTypes:
    def test_memory_item_defaults(self) -> None:
        item = MemoryItem(id="id1", content="hello", type="entity", importance=0.5, timestamp=100.0)
        assert item.access_count == 0
        assert item.last_access == 0.0
        assert item.embedding is None
        assert item.metadata == {}
        assert item.source_session is None

    def test_memory_query_defaults(self) -> None:
        q = MemoryQuery(query_text="test")
        assert q.k == 5
        assert q.recency_weight == 0.3
        assert q.relevance_weight == 0.5
        assert q.importance_weight == 0.2
        assert q.min_relevance == 0.6

    def test_episode_to_memory_item(self) -> None:
        ep = Episode(
            session_id="s1",
            summary="test session",
            message_count=3,
            token_count=100,
            start_time=0.0,
            end_time=10.0,
            importance=0.6,
        )
        item = ep.to_memory_item()
        assert item.type == "episode"
        assert "test session" in item.content
        assert item.importance == 0.6

    def test_reflection_to_memory_item(self) -> None:
        ref = Reflection(
            content="user prefers short answers",
            reflection_type="preference",
            source_ids=["s1"],
            importance=0.8,
            timestamp=100.0,
        )
        item = ref.to_memory_item()
        assert item.type == "reflection"
        assert "user prefers short answers" in item.content


# =========================================================================
# ImportanceScorer
# =========================================================================

class TestImportanceScorer:
    def test_score_with_signals(self) -> None:
        scorer = ImportanceScorer()
        item = MemoryItem(id="i1", content="test", type="entity", importance=0.5, timestamp=100.0)
        score = scorer.score(item, recency_hours=1.0)
        assert 0.0 <= score <= 1.0

    def test_estimate_llm_importance_keywords(self) -> None:
        scorer = ImportanceScorer()
        high = scorer.estimate_llm_importance("这个重要的决定解决了关键错误问题")
        assert high >= 0.4

    def test_estimate_llm_importance_generic(self) -> None:
        scorer = ImportanceScorer()
        low = scorer.estimate_llm_importance("你好")
        assert low == 0.3


# =========================================================================
# PromptInjector
# =========================================================================

class TestPromptInjector:
    def test_inject_empty_memories(self) -> None:
        injector = PromptInjector()
        result = injector.inject_memory("system prompt", [])
        assert result == "system prompt"

    def test_inject_with_memories(self) -> None:
        injector = PromptInjector()
        memories = [
            MemoryItem(id="i1", content="用户喜欢Python", type="preference", importance=0.8, timestamp=100.0),
        ]
        result = injector.inject_memory("system prompt", memories, max_tokens=1024)
        assert "用户喜欢Python" in result
        assert "=== 记忆上下文 ===" in result

    def test_inject_respects_token_budget(self) -> None:
        injector = PromptInjector()
        memories = [
            MemoryItem(id="i1", content="a" * 5000, type="preference", importance=0.9, timestamp=100.0),
            MemoryItem(id="i2", content="b" * 5000, type="entity", importance=0.1, timestamp=100.0),
        ]
        result = injector.inject_memory("sys", memories, max_tokens=10)
        assert result == "sys"

    def test_format_memory(self) -> None:
        injector = PromptInjector()
        item = MemoryItem(id="i1", content="hello", type="preference", importance=0.75, timestamp=100.0)
        formatted = injector._format_memory(item)
        assert "[preference]" in formatted
        assert "hello" in formatted
        assert "0.8" in formatted


# =========================================================================
# ForgettingMechanism
# =========================================================================

class TestForgettingMechanism:
    def test_should_run_initially(self) -> None:
        decay = ForgettingMechanism()
        assert decay.should_run() is True

    def test_should_run_recently(self) -> None:
        decay = ForgettingMechanism()
        decay.should_run()
        assert decay.should_run() is False

    def test_apply_high_importance_no_decay(self) -> None:
        decay = ForgettingMechanism()
        item = MemoryItem(id="i1", content="test", type="entity", importance=0.8, timestamp=100.0)
        result = decay.apply(item)
        assert result == 0.8

    def test_apply_medium_importance_decay(self) -> None:
        decay = ForgettingMechanism()
        item = MemoryItem(
            id="i1", content="test", type="entity", importance=0.5, timestamp=100.0,
            last_access=time.time() - 14 * 86400,
        )
        result = decay.apply(item)
        assert result < 0.5

    def test_apply_low_importance_decay(self) -> None:
        decay = ForgettingMechanism()
        item = MemoryItem(
            id="i1", content="test", type="entity", importance=0.3, timestamp=100.0,
            last_access=time.time() - 7 * 86400,
        )
        result = decay.apply(item)
        assert result < 0.3


# =========================================================================
# Agent + Memory 集成
# =========================================================================

class TestAgentMemoryIntegration:
    """测试 Agent 与 MemoryManager 的集成。"""

    def test_agent_accepts_memory_param(self) -> None:
        """Agent 接受可选的 memory 参数。"""
        llm = MagicMock()
        memory = MagicMock()
        agent = Agent(llm=llm, memory=memory)
        assert agent.memory is memory
        memory.start_session.assert_called_once()

    def test_agent_without_memory_still_works(self) -> None:
        """不传入 memory 时 Agent 行为不变。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="你好")
        agent = Agent(llm=llm)
        result = agent.chat("hi")
        assert result == "你好"

    def test_chat_calls_on_chat_start(self) -> None:
        """chat() 通过 ContextManager 触发记忆检索。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="你好")
        memory = MagicMock()
        memory.on_chat_start.return_value = ""
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory)
        agent.chat("hi")

        # memory.on_chat_start 通过 MemoryContext.retrieve 间接调用
        memory.on_chat_start.assert_called_once()

    def test_chat_calls_on_chat_end(self) -> None:
        """chat() 调用 memory.on_chat_end。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="回答")
        memory = MagicMock()
        memory.on_chat_start.return_value = ""
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory)
        agent.chat("hi")

        memory.on_chat_end.assert_called_once()

    def test_chat_calls_trim_messages(self) -> None:
        """chat() 调用 memory.trim_messages。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="回答")
        memory = MagicMock()
        memory.on_chat_start.return_value = ""
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory)
        agent.chat("hi")

        memory.trim_messages.assert_called_once()

    def test_chat_injects_memory_context(self) -> None:
        """MemoryContext 检索到的记忆注入到 system prompt。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="回答")
        memory = MagicMock()
        memory.on_chat_start.return_value = "[preference] 用户喜欢Python"
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory, system_prompt="你是一个助手")
        # 查询需要 >5 字符以激活 MEMORY 上下文类型
        agent.chat("帮我查一下订单")

        sys_msg = agent.messages[0]
        assert "用户喜欢Python" in sys_msg.content
        assert "你是一个助手" in sys_msg.content

    def test_reset_calls_on_reset(self) -> None:
        """reset() 调用 memory.on_reset。"""
        llm = MagicMock()
        memory = MagicMock()
        memory.on_chat_start.return_value = ""
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory)
        agent.reset()
        memory.on_reset.assert_called_once()

    def test_chat_stream_calls_memory(self) -> None:
        """chat_stream() 通过 ContextManager 触发记忆生命周期。"""
        llm = MagicMock()
        llm.chat.return_value = Message(role="assistant", content="流式回答")
        memory = MagicMock()
        memory.on_chat_start.return_value = ""
        memory.trim_messages.side_effect = lambda msgs: msgs

        agent = Agent(llm=llm, memory=memory)
        list(agent.chat_stream("hi"))

        memory.on_chat_start.assert_called_once()
        memory.on_chat_end.assert_called_once()
        memory.trim_messages.assert_called_once()
