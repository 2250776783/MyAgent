"""日志处理流水线。

Pipeline 架构：emit → [processors] → [filters] → [sinks]。
按序处理每条 LogRecord，支持链式扩展。
"""

from abc import ABC, abstractmethod

from src.logging.schema import LogRecord


class Processor(ABC):
    """处理器：对 LogRecord 进行转换/增强。"""
    @abstractmethod
    def process(self, record: LogRecord) -> None: ...


class Filter(ABC):
    """过滤器：决定 LogRecord 是否被丢弃。"""
    @abstractmethod
    def filter(self, record: LogRecord) -> bool: ...


class Sink(ABC):
    """输出目标：将 LogRecord 写入外部系统。"""
    @abstractmethod
    def write(self, record: LogRecord) -> None: ...


class LogPipeline:
    """日志处理管道。

    流程: emit(record) → [processors] → [filters] → [sinks]
    """

    def __init__(self) -> None:
        self.processors: list[Processor] = []
        self.filters: list[Filter] = []
        self.sinks: list[Sink] = []

    def add_processor(self, processor: Processor) -> "LogPipeline":
        self.processors.append(processor)
        return self

    def add_filter(self, filter_: Filter) -> "LogPipeline":
        self.filters.append(filter_)
        return self

    def add_sink(self, sink: Sink) -> "LogPipeline":
        self.sinks.append(sink)
        return self

    def emit(self, record: LogRecord) -> None:
        """处理并输出一条日志记录。"""
        for f in self.filters:
            if not f.filter(record):
                return
        for p in self.processors:
            p.process(record)
        for s in self.sinks:
            if isinstance(s, Sink):
                s.write(record)
            elif callable(s):
                s(record)
