"""Environment Context - 环境上下文。

收集 Agent 运行环境信息：时间、系统状态等。
"""

from __future__ import annotations

import datetime
import platform
from typing import Any

from .types import ContextSegment, ContextType, InjectionPhase


class EnvironmentContext:
    """环境上下文管理器。"""

    def __init__(self, extra_info: dict[str, str] | None = None) -> None:
        self.extra_info = extra_info or {}
        self._last_update: float = 0.0

    def build(self) -> ContextSegment:
        now = datetime.datetime.now()
        info: list[str] = [
            f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S %A')}",
            f"平台: {platform.system()} {platform.release()}",
        ]
        for key, value in self.extra_info.items():
            info.append(f"{key}: {value}")

        text = "\n".join(info)
        seg = ContextSegment.create(
            ContextType.ENVIRONMENT, text,
            priority=0.2, phase=InjectionPhase.ENVIRONMENT,
        )
        seg.token_count = len(text) // 4 + 1
        self._last_update = __import__("time").time()
        return seg
