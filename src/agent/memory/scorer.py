"""重要性评分模块。

从多维度评估记忆的重要性，用于决定记忆的保留优先级和检索排序。
"""

import math
import time
from typing import Any

from .types import MemoryItem


class ImportanceScorer:
    """记忆重要性评分器。

    综合多个信号评估记忆的重要性（0-1）：
    - 语义重要性 (LLM 自评)
    - 访问频率
    - 时效性
    - 情感强度
    """

    def score(self, item: MemoryItem, **signals: Any) -> float:
        """计算综合的重要性分数。

        Args:
            item: 记忆条目
            **signals: 额外信号
                - access_frequency: 访问频率 (0-1)
                - emotional_intensity: 情感强度 (0-1)
                - entity_count: 关联实体数量
                - task_completed: 是否完成任务

        Returns:
            综合重要性分数 (0-1)
        """
        base = item.importance * 0.3

        access_freq = min(signals.get("access_frequency", item.access_count / 10), 1.0)
        access_score = access_freq * 0.2

        hours_elapsed = (time.time() - item.last_access) / 3600 if item.last_access else 0
        recency = math.exp(-hours_elapsed / 168.0)
        recency_score = recency * 0.25

        emotional = min(signals.get("emotional_intensity", 0), 1.0)
        emotional_score = emotional * 0.1

        entity_count = signals.get("entity_count", 0)
        entity_score = min(entity_count / 5, 1.0) * 0.05

        task_score = (1.0 if signals.get("task_completed") else 0.0) * 0.1

        total = base + access_score + recency_score + emotional_score + entity_score + task_score
        return min(total, 1.0)

    @staticmethod
    def estimate_llm_importance(content: str) -> float:
        """通过文本特征快速估算重要性（无需 LLM 调用）。"""
        score = 0.3

        if len(content) > 100:
            score += 0.1

        keywords = ["决定", "选择", "错误", "问题", "解决", "重要", "必须",
                    "decision", "error", "important", "fix", "critical"]
        for kw in keywords:
            if kw.lower() in content.lower():
                score += 0.05

        import re
        if re.search(r'\d+\.\d+\.\d+', content):
            score += 0.1

        return min(score, 1.0)
