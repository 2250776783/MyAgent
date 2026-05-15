"""语义记忆 - 实体与偏好。

存储"知道什么"——实体知识、用户偏好、概念关系。
以语义索引为主，支持增量更新与冲突检测。
"""

import json
import logging
import time
import uuid

from src.llm import LLMClient, Message

from .stores.base import MemoryStore
from .types import MemoryItem

logger = logging.getLogger(__name__)


class SemanticMemory:
    """语义记忆。

    管理：
    - 实体知识（人物、项目、概念等）
    - 用户偏好（沟通风格、技术偏好）
    - 概念关系

    写入时自动检测并合并已有信息，避免冗余。
    """

    def __init__(self, store: MemoryStore, llm: LLMClient) -> None:
        self.store = store
        self.llm = llm

    def extract_from_messages(self, messages: list[Message]) -> list[MemoryItem]:
        """从消息中提取实体和偏好，返回新的记忆条目。"""
        if not messages:
            return []

        recent = messages[-20:]
        text = self._format_for_extraction(recent)

        prompt = """从以下对话中提取实体和用户偏好。

实体包括：人名、项目名、技术概念、工具名等。
偏好包括：技术偏好、沟通风格、工作方式等。

对话：
{text}

请按 JSON 格式输出：
{{
    "entities": [
        {{"name": "实体名", "type": "person|project|concept|tool",
          "observations": ["观察1", "观察2"]}}
    ],
    "preferences": [
        {{"category": "偏好类别", "value": "偏好描述"}}
    ]
}}

只输出 JSON，不要多余文字。""".format(text=text)

        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            parsed = json.loads(response.content)

            items: list[MemoryItem] = []
            for e in parsed.get("entities", []):
                items.append(self._make_entity_item(e))
            for p in parsed.get("preferences", []):
                items.append(self._make_preference_item(p))

            return items

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to extract entities: %s", e)
            return []

    def merge(self, new_items: list[MemoryItem]) -> list[MemoryItem]:
        """合并新提取的实体/偏好到已有记忆，去重。"""
        if not new_items:
            return []

        saved = []
        for item in new_items:
            existing = self._find_similar(item)
            if existing is None:
                item.id = str(uuid.uuid4())
                item.timestamp = time.time()
                self.store.save(item)
                saved.append(item)
            else:
                self._merge_into(existing, item)

        return saved

    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        return self.store.search(query_embedding, k)

    def _make_entity_item(self, data: dict) -> MemoryItem:
        observations = data.get("observations", [])
        content = f"[实体] {data['name']}({data.get('type', 'unknown')}): {'; '.join(observations)}"
        return MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            type="entity",
            importance=0.5,
            timestamp=time.time(),
            metadata={
                "entity_name": data["name"],
                "entity_type": data.get("type", "unknown"),
                "observations": observations,
            },
        )

    def _make_preference_item(self, data: dict) -> MemoryItem:
        return MemoryItem(
            id=str(uuid.uuid4()),
            content=f"[偏好] {data['category']}: {data['value']}",
            type="preference",
            importance=0.6,
            timestamp=time.time(),
            metadata={"category": data["category"], "value": data["value"]},
        )

    def _find_similar(self, item: MemoryItem) -> MemoryItem | None:
        ename = item.metadata.get("entity_name")
        if ename:
            for e in self.store.get_all():
                if e.metadata.get("entity_name") == ename:
                    return e

        cat = item.metadata.get("category")
        if cat:
            for e in self.store.get_all():
                if e.metadata.get("category") == cat:
                    return e

        return None

    def _merge_into(self, existing: MemoryItem, new_item: MemoryItem) -> None:
        if existing.type == "entity":
            old_obs = existing.metadata.get("observations", [])
            new_obs = new_item.metadata.get("observations", [])
            merged_obs = list(dict.fromkeys(old_obs + new_obs))

            existing.content = f"[实体] {existing.metadata['entity_name']}: {'; '.join(merged_obs)}"
            existing.metadata["observations"] = merged_obs
            existing.importance = min(existing.importance + 0.05, 1.0)
            existing.last_access = time.time()
            existing.access_count += 1

            self.store.update(
                existing.id,
                content=existing.content,
                importance=existing.importance,
                last_access=existing.last_access,
                access_count=existing.access_count,
                metadata=existing.metadata,
            )

    def _format_for_extraction(self, messages: list[Message]) -> str:
        lines = []
        for m in messages:
            role = {"user": "用户", "assistant": "助手", "tool": "工具"}.get(m.role, m.role)
            content = (m.content or "")[:200]
            if m.tool_calls:
                content = f"[调用 {', '.join(tc['function']['name'] for tc in m.tool_calls)}]"
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
