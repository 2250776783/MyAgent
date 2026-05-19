"""日志输出目标。

提供基于 loguru 的控制台和文件日志输出。
"""

import sys
from pathlib import Path

from loguru import logger as _loguru_logger

from src.logging.pipeline import Sink
from src.logging.schema import LogRecord


class ConsoleSink(Sink):
    """控制台日志输出（通过 loguru stdout sink）。"""

    def __init__(self, json_format: bool = True) -> None:
        self._json_format = json_format
        if json_format:
            self._sink_id = _loguru_logger.add(
                sys.stdout,
                format="{message}",
                serialize=True,
                colorize=False,
            )
        else:
            self._sink_id = _loguru_logger.add(
                sys.stdout,
                format="<green>{time:HH:mm:ss}</green> | <level>{level:<5}</level> | <cyan>{extra[event_type]:<20}</cyan> | {message}",
                colorize=True,
            )

    def write(self, record: LogRecord) -> None:
        bound = _loguru_logger.bind(event_type=record.event_type)
        log_method = getattr(bound, record.level.lower(), bound.info)
        log_method(record.message)

    def stop(self) -> None:
        _loguru_logger.remove(self._sink_id)


class FileSink(Sink):
    """文件日志输出（loguru 自动轮转）。"""

    def __init__(
        self,
        log_dir: str | Path = "./logs",
        file_name: str = "agent.log",
        rotation: str = "500 MB",
        retention: str = "30 days",
        json_format: bool = True,
    ) -> None:
        log_path = Path(log_dir) / file_name
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if json_format:
            self._sink_id = _loguru_logger.add(
                str(log_path),
                format="{message}",
                serialize=True,
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
            )
        else:
            self._sink_id = _loguru_logger.add(
                str(log_path),
                format="{time:HH:mm:ss} | {level:<5} | {extra[event_type]:<20} | {message}",
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
            )

    def write(self, record: LogRecord) -> None:
        bound = _loguru_logger.bind(event_type=record.event_type)
        log_method = getattr(bound, record.level.lower(), bound.info)
        log_method(record.message)

    def stop(self) -> None:
        _loguru_logger.remove(self._sink_id)
