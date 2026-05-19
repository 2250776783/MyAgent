"""Grafana Loki 导出器。

通过 HTTP Push API 将日志批量发送到 Loki。
使用 event_type 作为标签，便于 Loki 查询过滤。

用法::

    exporter = LokiExporter(url="http://localhost:3100")
    event_bus.subscribe("*", exporter)
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from src.logging.exporters.base import BaseExporter
from src.logging.schema import LogRecord


class LokiExporter(BaseExporter):
    """Grafana Loki 批量导出器（HTTP Push API）。

    通过 event_type/level/agent_name 标签组织日志流。
    """

    def __init__(
        self,
        url: str = "http://localhost:3100",
        batch_size: int = 200,
        tenant_id: str | None = None,
    ) -> None:
        super().__init__(batch_size=batch_size)
        self._url = url.rstrip("/") + "/loki/api/v1/push"
        self._tenant_id = tenant_id

    def export(self, records: list[LogRecord]) -> None:
        if not records:
            return

        streams: dict[str, list[list[str]]] = {}
        for r in records:
            labels = f'{{event_type="{r.event_type}",level="{r.level}",agent="{r.agent_name}"}}'
            ts = str(int(datetime.fromisoformat(r.timestamp).timestamp() * 1e9)) if r.timestamp else "0"
            streams.setdefault(labels, []).append([ts, r.to_json()])

        payload = {"streams": [{"stream": json.loads(k), "values": v} for k, v in streams.items()]}
        data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(
                self._url, data=data, headers={"Content-Type": "application/json"},
            )
            if self._tenant_id:
                req.add_header("X-Scope-OrgID", self._tenant_id)
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
