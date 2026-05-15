"""记忆检索模块。

多层检索：通过 query expansion 从多个记忆层检索相关记忆，
经过 rerank 和 dedup 后返回最优结果。
"""

import json
import logging
import math
import time

from src.llm import LLMClient, Message

from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .stores.base import MemoryStore
from .types import MemoryItem, MemoryQuery

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """记忆检索器。

    多层检索流程：
    1. Query Expansion: 用 LLM 将用户输入扩展为多个检索 query
    2. Multi-Layer: 从 Episodic + Semantic 同时检索
    3. Score & Dedup: 加权排序 + 相似度去重
    4. Top-K: 截取最相关结果
    """

    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        store: MemoryStore,
        llm: LLMClient,
    ) -> None:
        self.episodic = episodic
        self.semantic = semantic
        self.store = store
        self.llm = llm

    def retrieve(self, query: MemoryQuery, query_embedding: list[float] | None = None) -> list[MemoryItem]:
        """执行多层记忆检索。"""
        queries = self._expand_query(query.query_text)
        all_results: list[MemoryItem] = []

        for q_text in queries:
            episodes = self.episodic.search(query_embedding or [], query.k)
            all_results.extend(episodes)

            semantics = self.semantic.search(query_embedding or [], query.k)
            all_results.extend(semantics)

            if query_embedding:
                store_results = self.store.search(query_embedding, query.k)
                all_results.extend(store_results)

        deduped = self._dedup(all_results, threshold=0.9)

        now = time.time()
        scored: list[tuple[MemoryItem, float]] = []
        for item in deduped:
            score = self._compute_score(item, query, now)
            scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [item for item, score in scored[:query.k] if score >= query.min_relevance]

        for item in top:
            self.store.update(
                item.id,
                access_count=item.access_count + 1,
                last_access=time.time(),
            )

        return top

    def _expand_query(self, query_text: str) -> list[str]:
        try:
            prompt = """基于用户的输入，生成 2-3 个检索查询来查找相关记忆。

用户输入: {query}

要求：
- 每个查询应覆盖用户提到的实体、意图、领域
- 直接输出 JSON 列表

输出格式: ["query1", "query2", "query3"]""".format(query=query_text)

            response = self.llm.chat([Message(role="user", content=prompt)])
            queries = json.loads(response.content)
            return [query_text] + (queries if isinstance(queries, list) else [])
        except (json.JSONDecodeError, Exception) as e:
            logger.debug("Query expansion failed: %s", e)
            return [query_text]

    def _compute_score(self, item: MemoryItem, query: MemoryQuery, now: float) -> float:
        relevance = 0.5
        hours_elapsed = (now - item.timestamp) / 3600
        recency = math.exp(-hours_elapsed / query.recency_decay_hours)
        return (
            relevance * query.relevance_weight
            + recency * query.recency_weight
            + item.importance * query.importance_weight
        )

    def _dedup(self, items: list[MemoryItem], threshold: float = 0.9) -> list[MemoryItem]:
        if not items:
            return []
        unique: list[MemoryItem] = []
        seen: set[str] = set()
        for item in items:
            fp = item.content[:50]
            if fp not in seen:
                seen.add(fp)
                unique.append(item)
        return unique
