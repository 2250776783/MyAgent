"""反思系统。

定期从记忆中提炼高层次洞察、模式和知识。
是 Agent 的"学习"机制——将原始经验转化为结构化知识。
"""

import json
import logging
import time

from src.llm import LLMClient, Message

from .stores.base import MemoryStore
from .types import MemoryItem, Reflection

logger = logging.getLogger(__name__)


class ReflectionSystem:
    """反思系统。

    定期从累积的记忆中生成反思：
    - Insight Extraction: 发现模式和洞察
    - Knowledge Consolidation: 整合分散信息
    - Knowledge Gap: 识别知识缺口

    反射频率由新记忆数量和经过时间共同控制。
    """

    def __init__(
        self,
        store: MemoryStore,
        llm: LLMClient,
        min_memories_for_reflection: int = 5,
        min_interval_seconds: float = 3600,
    ) -> None:
        self.store = store
        self.llm = llm
        self.min_memories = min_memories_for_reflection
        self.min_interval = min_interval_seconds
        self._last_reflection: float = 0.0
        self._last_reflected_count: int = 0

    def should_reflect(self) -> bool:
        now = time.time()
        if now - self._last_reflection < self.min_interval:
            return False
        current_count = self.store.count()
        new_count = current_count - self._last_reflected_count
        return new_count >= self.min_memories

    def run(self) -> list[Reflection]:
        all_items = self.store.get_all()
        new_items = [item for item in all_items if item.timestamp > self._last_reflection]

        if not new_items:
            return []

        reflections: list[Reflection] = []
        insight = self._extract_insights(new_items)
        if insight:
            reflections.append(insight)

        self._last_reflection = time.time()
        self._last_reflected_count = self.store.count()

        for ref in reflections:
            self.store.save(ref.to_memory_item())

        return reflections

    def _extract_insights(self, memories: list[MemoryItem]) -> Reflection | None:
        if not memories:
            return None

        text = "\n".join(f"[{m.type}] {m.content}" for m in memories[:20])

        prompt = f"""你是一位分析专家。请分析以下记忆记录，提取高层次的模式、洞察和结论。

记忆记录：
{text}

请识别：
1. 重复出现的主题或模式
2. 用户偏好或工作方式的推论
3. 技术决策及其理由
4. 知识上的重要发现

对每个洞察，给出置信度 (0-1)。

只输出 JSON 列表：
[{{"insight": "洞察描述", "confidence": 0.8, "type": "pattern|preference|decision|discovery"}}]"""

        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            parsed = json.loads(response.content)

            if not parsed:
                return None

            combined = "; ".join(
                f"{item['insight']} (置信度: {item.get('confidence', 0.5)})"
                for item in parsed[:3]
            )

            source_ids = [m.id for m in memories[:10]]

            return Reflection(
                content=combined,
                reflection_type="insight",
                source_ids=source_ids,
                importance=min(0.5 + len(parsed) * 0.1, 0.9),
            )

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Insight extraction failed: %s", e)
            return None
