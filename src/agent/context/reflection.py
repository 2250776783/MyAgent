"""Reflection Context - 反思上下文管理。

集成 ReflectionSystem，管理反思触发和注入。
"""

from __future__ import annotations

import logging

from src.agent.memory.reflection import ReflectionSystem
from src.llm import TokenCounter

from .types import ContextSegment, ContextType, InjectionPhase

logger = logging.getLogger(__name__)


class ReflectionContext:
    """反思上下文管理器。

    Args:
        reflection_system: ReflectionSystem 实例
        token_counter: Token 计数器
    """

    def __init__(
        self,
        reflection_system: ReflectionSystem | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self._reflection_system = reflection_system
        self.token_counter = token_counter or TokenCounter()
        self._last_reflection: float = 0.0
        self._cached_segments: list[ContextSegment] = []

    def should_reflect(self) -> bool:
        if self._reflection_system:
            try:
                return self._reflection_system.should_reflect()
            except Exception as e:
                logger.debug("ReflectionSystem.should_reflect failed: %s", e)
                return False
        now = __import__("time").time()
        return (now - self._last_reflection) > 3600

    def run(self, force: bool = False) -> list[ContextSegment]:
        if not force and not self.should_reflect():
            return self._cached_segments

        if self._reflection_system:
            try:
                reflections = self._reflection_system.run()
                self._cached_segments = []
                for ref in reflections:
                    content = ref.content if hasattr(ref, "content") else str(ref)
                    seg = ContextSegment.create(
                        ContextType.REFLECTION, content,
                        priority=getattr(ref, "importance", 0.5),
                        phase=InjectionPhase.REFLECTION,
                        metadata={
                            "reflection_type": getattr(ref, "reflection_type", "insight"),
                        },
                    )
                    seg.token_count = self.token_counter.count(content)
                    self._cached_segments.append(seg)
            except Exception as e:
                logger.warning("Reflection failed: %s", e)

        self._last_reflection = __import__("time").time()
        return self._cached_segments

    def build_drift_context(self, drift_message: str) -> ContextSegment:
        text = f"[警告] 检测到潜在的目标偏离: {drift_message}"
        seg = ContextSegment.create(
            ContextType.REFLECTION, text,
            priority=0.8, phase=InjectionPhase.REFLECTION,
        )
        seg.token_count = self.token_counter.count(text)
        return seg
