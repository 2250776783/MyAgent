"""企业级日志系统 — AI Agent 可观测性基础设施。

架构: Adapter 接口解耦 + contextvars 隐式传播 + Pipeline + EventBus

用法::

    from src.logging import setup_logging
    adapter = setup_logging()
    adapter.info("system.event", "服务启动", version="1.0")
"""

from src.logging.adapter import LoggerAdapter, LoguruAdapter, NullAdapter
from src.logging.config import LogConfig
from src.logging.event import EventBus
from src.logging.pipeline import LogPipeline

_log_pipeline: LogPipeline | None = None
_event_bus: EventBus | None = None
_default_adapter: LoggerAdapter | None = None


def setup_logging(config: LogConfig | None = None) -> LoggerAdapter:
    """全局日志系统初始化。应用启动时调用一次。"""
    global _log_pipeline, _event_bus, _default_adapter

    cfg = config or LogConfig()

    _event_bus = EventBus()
    pipeline = LogPipeline()

    # Processors
    from src.logging.processors import Enricher, Sanitizer
    pipeline.add_processor(Sanitizer())
    pipeline.add_processor(Enricher())

    # Filters
    from src.logging.filters import LevelFilter
    pipeline.add_filter(LevelFilter(cfg.level))

    # Sinks
    from src.logging.sinks import ConsoleSink, FileSink
    json_format = cfg.format == "json"
    if cfg.output in ("console", "both"):
        pipeline.add_sink(ConsoleSink(json_format=json_format))
    if cfg.output in ("file", "both"):
        pipeline.add_sink(FileSink(
            log_dir=cfg.dir, file_name=cfg.file_name,
            rotation=cfg.rotation, retention=cfg.retention,
            json_format=json_format,
        ))

    _log_pipeline = pipeline
    adapter = LoguruAdapter()
    adapter.set_pipeline(pipeline)
    adapter.set_event_bus(_event_bus)
    _default_adapter = adapter
    return adapter


def get_default_adapter() -> LoggerAdapter:
    """获取默认日志适配器（非 DI 场景用）。"""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = setup_logging()
    return _default_adapter


def get_event_bus() -> EventBus | None:
    return _event_bus


def get_pipeline() -> LogPipeline | None:
    return _log_pipeline


def shutdown_logging() -> None:
    """关闭日志系统，释放资源。"""
    global _log_pipeline, _event_bus, _default_adapter
    if _log_pipeline:
        for sink in getattr(_log_pipeline, "sinks", []):
            if hasattr(sink, "stop"):
                sink.stop()
    _log_pipeline = None
    _event_bus = None
    _default_adapter = None


__all__ = [
    "LoggerAdapter", "LoguruAdapter", "NullAdapter",
    "LogConfig", "LogPipeline", "EventBus",
    "setup_logging", "get_default_adapter",
    "get_event_bus", "get_pipeline", "shutdown_logging",
]
