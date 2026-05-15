"""记忆冲突解决。

检测并解决记忆中的矛盾信息，确保知识一致性。
"""

import logging
from typing import Any

from src.llm import LLMClient, Message

logger = logging.getLogger(__name__)


class ConflictResolution:
    """冲突解决方案。"""
    resolved_content: str
    superseded_ids: list[str]
    confidence: float


class ConflictResolver:
    """记忆冲突解决器。

    检测同一实体的矛盾观察，并通过 LLM 判断哪个更可信，
    或生成统一的解释。
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def detect_and_resolve(
        self,
        entity_name: str,
        existing_observations: list[str],
        new_observations: list[str],
    ) -> ConflictResolution | None:
        """检测并尝试解决矛盾。"""
        all_obs = existing_observations + new_observations
        if len(set(all_obs)) == len(all_obs) and len(all_obs) <= 3:
            return None

        prompt = f"""检查以下关于同一实体的观察是否矛盾：

实体: {entity_name}
已有观察: {existing_observations}
新观察: {new_observations}

请判断：
1. 是否矛盾？如果矛盾，输出 "conflict: true"
2. 能否统一解释？给出最合理的统一描述。
3. 如果无法统一，哪个观察更可信？为什么？

输出 JSON:
{{"has_conflict": true/false, "resolution": "统一描述", "confidence": 0.8}}"""

        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            import json
            parsed = json.loads(response.content)

            if parsed.get("has_conflict"):
                resolution = ConflictResolution()
                resolution.resolved_content = parsed["resolution"]
                resolution.confidence = parsed.get("confidence", 0.5)
                resolution.superseded_ids = []
                return resolution

        except Exception as e:
            logger.warning("Conflict resolution failed: %s", e)

        return None
