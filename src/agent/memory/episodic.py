"""情景记忆 - 会话级记忆。

记录"发生了什么"——会话摘要、关键事件、交互历史。
以时序索引为主，同时支持语义检索。
"""

import logging
import time
import uuid

from src.llm import LLMClient, Message

from .scorer import ImportanceScorer
from .stores.base import MemoryStore
from .summarizer import MemorySummarizer
from .types import Episode, MemoryItem

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """情景记忆。

    管理会话级的情景记忆：
    - 会话结束时会话摘要 → Episode
    - 关键事件提取（工具调用、错误、决策等）
    - 时序 + 语义双重检索

    Args:
        store: 持久化存储后端
        llm: LLM 客户端（用于摘要生成）
    """

    def __init__(self, store: MemoryStore, llm: LLMClient) -> None:
        self.store = store
        self.llm = llm
        self.summarizer = MemorySummarizer(llm)
        self.scorer = ImportanceScorer()

    def store_session(
        self,
        messages: list[Message],
        session_id: str | None = None,
    ) -> Episode:
        """存储一段会话为情景记忆。

        1. 摘要会话内容
        2. 提取关键事件
        3. 计算重要性
        4. 持久化存储

        Args:
            messages: 会话消息列表
            session_id: 会话 ID（可选）

        Returns:
            生成的 Episode
        """
        session_id = session_id or str(uuid.uuid4())
        start_time = time.time()
        token_count = sum(len(m.content or "") for m in messages)

        summary = self.summarizer.summarize_messages(messages)
        key_events = self._extract_key_events(messages)

        importance = self.scorer.estimate_llm_importance(summary)
        importance = min(importance + len(key_events) * 0.05, 1.0)

        episode = Episode(
            session_id=session_id,
            summary=summary,
            message_count=len(messages),
            token_count=token_count,
            start_time=start_time,
            end_time=time.time(),
            importance=importance,
            key_events=key_events,
        )

        item = episode.to_memory_item()
        self.store.save(item)

        return episode

    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        """按向量检索情景记忆。"""
        return self.store.search(query_embedding, k)

    def _extract_key_events(self, messages: list[Message]) -> list[dict]:
        events = []
        for msg in messages:
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    events.append({
                        "type": "tool_call",
                        "content": tc["function"]["name"],
                        "timestamp": time.time(),
                    })
            if msg.role == "tool" and "错误" in (msg.content or ""):
                events.append({
                    "type": "error",
                    "content": msg.content[:100],
                    "timestamp": time.time(),
                })
        return events
