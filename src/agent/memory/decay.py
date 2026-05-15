"""遗忘衰减机制。

模拟人类遗忘过程，根据时间流逝和访问频率降低记忆的重要性分数。
低分记忆最终被归档或删除。
"""

import logging
import time

from .stores.base import MemoryStore
from .types import MemoryItem

logger = logging.getLogger(__name__)


class ForgettingMechanism:
    """遗忘衰减机制。

    分层遗忘策略：
    - High (importance >= 0.7): 不衰减
    - Medium (0.4 <= importance < 0.7): 每月 10% 衰减
    - Low (0.1 <= importance < 0.4): 每周 15% 衰减
    - Archived (< 0.1): 建议删除

    Args:
        half_life_days: 中等重要度的半衰期（天）
        check_interval: 维护检查间隔（秒），用于节流
    """

    def __init__(self, half_life_days: float = 30.0, check_interval: float = 86400) -> None:
        self.half_life_days = half_life_days
        self.check_interval = check_interval
        self._last_check: float = 0.0

    def should_run(self) -> bool:
        now = time.time()
        if now - self._last_check >= self.check_interval:
            self._last_check = now
            return True
        return False

    def apply(self, item: MemoryItem) -> float:
        if item.importance >= 0.7:
            return item.importance

        days_since_last = (time.time() - item.last_access) / 86400 if item.last_access else 0

        if item.importance >= 0.4:
            decay_rate = 0.05
        else:
            decay_rate = 0.15

        weeks = days_since_last / 7
        decayed = item.importance * (1 - decay_rate) ** weeks
        return max(decayed, 0.0)

    def run_maintenance(self, store: MemoryStore) -> tuple[int, int]:
        all_items = store.get_all()
        updated = 0
        deleted = 0

        for item in all_items:
            new_score = self.apply(item)
            if new_score < 0.1:
                store.delete(item.id)
                deleted += 1
            elif abs(new_score - item.importance) > 0.01:
                store.update(item.id, importance=new_score)
                updated += 1

        if updated or deleted:
            logger.info("Decay maintenance: %d updated, %d deleted", updated, deleted)

        return updated, deleted
