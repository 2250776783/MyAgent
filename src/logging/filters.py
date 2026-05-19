"""日志过滤器。

决定哪些 LogRecord 应被处理，哪些应被丢弃。
"""

from src.logging.constants import level_number
from src.logging.pipeline import Filter
from src.logging.schema import LogRecord


class LevelFilter(Filter):
    """按日志级别过滤。低于 min_level 的日志被丢弃。"""

    def __init__(self, min_level: str = "INFO") -> None:
        self._min = level_number(min_level)

    def filter(self, record: LogRecord) -> bool:
        return level_number(record.level) >= self._min


class SamplingFilter(Filter):
    """采样过滤器，仅保留指定比例的日志。用于高频日志降噪。"""

    def __init__(self, rate: float = 1.0) -> None:
        if not 0.0 < rate <= 1.0:
            raise ValueError(f"采样率必须在 (0, 1] 范围内: {rate}")
        self._rate = rate
        self._counter = 0

    def filter(self, record: LogRecord) -> bool:
        if self._rate >= 1.0:
            return True
        self._counter += 1
        return (self._counter % int(1 / self._rate)) == 0


class ModuleFilter(Filter):
    """按 event_type 包含/排除。"""

    def __init__(self, included: list[str] | None = None, excluded: list[str] | None = None) -> None:
        self._included = set(included or [])
        self._excluded = set(excluded or [])

    def filter(self, record: LogRecord) -> bool:
        if self._excluded and record.event_type in self._excluded:
            return False
        if self._included and record.event_type not in self._included:
            return False
        return True
