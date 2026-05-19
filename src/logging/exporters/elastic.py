"""Elasticsearch 导出器。

批量将 LogRecord 写入 Elasticsearch（通过 bulk API）。
支持自动索引名管理（按日期滚动：logs-YYYY.MM.DD）。

用法::

    exporter = ElasticExporter(hosts=["http://localhost:9200"])
    event_bus.subscribe("*", exporter)
"""

from datetime import datetime, timezone
from typing import Any

from src.logging.exporters.base import BaseExporter
from src.logging.schema import LogRecord

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk

    _ES_AVAILABLE = True
except ImportError:
    _ES_AVAILABLE = False


def _index_name(prefix: str = "logs") -> str:
    today = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    return f"{prefix}-{today}"


class ElasticExporter(BaseExporter):
    """Elasticsearch 批量导出器。

    LogRecord 被索引为 JSON 文档，@timestamp 用于 ES 时间轴。
    """

    def __init__(
        self,
        hosts: list[str] | None = None,
        index_prefix: str = "logs",
        batch_size: int = 100,
        **client_kwargs: Any,
    ) -> None:
        super().__init__(batch_size=batch_size)
        self._index_prefix = index_prefix
        self._enabled = _ES_AVAILABLE
        if self._enabled:
            self._client = Elasticsearch(hosts=hosts or ["http://localhost:9200"], **client_kwargs)

    def export(self, records: list[LogRecord]) -> None:
        if not self._enabled or not records:
            return

        actions = [
            {"_index": _index_name(self._index_prefix), "_source": record.to_dict()}
            for record in records
        ]
        try:
            bulk(self._client, actions)
        except Exception:
            pass

    def close(self) -> None:
        if self._enabled:
            self.flush()
            self._client.close()
