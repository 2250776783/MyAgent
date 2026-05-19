"""OpenTelemetry 桥接导出器。

将 LogRecord 转换为 OTel Span/Log 并发送到 OTLP 端点。
需要安装 opentelemetry-api 和 opentelemetry-exporter-otlp-proto-grpc。

用法::

    exporter = OTelExporter(endpoint="http://localhost:4317")
    event_bus.subscribe("*", exporter)
"""

from typing import Any

from src.logging.schema import LogRecord

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import SpanKind, Status, StatusCode

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


_EVENT_TO_OTEL_KIND = {
    "llm.prompt": SpanKind.CLIENT if _OTEL_AVAILABLE else "CLIENT",
    "llm.response": SpanKind.CLIENT if _OTEL_AVAILABLE else "CLIENT",
    "tool.call": SpanKind.CLIENT if _OTEL_AVAILABLE else "CLIENT",
    "tool.result": SpanKind.CLIENT if _OTEL_AVAILABLE else "CLIENT",
    "http.request": SpanKind.SERVER if _OTEL_AVAILABLE else "SERVER",
}


class OTelExporter:
    """OpenTelemetry 导出器。

    将日志事件转换为 OTel Span：
    - trace_id → OTel trace_id
    - event_type → Span name
    - duration_ms → Span duration
    - exception → Span status error
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4317",
        service_name: str = "myagent",
        batch_size: int = 50,
    ) -> None:
        self._enabled = _OTEL_AVAILABLE
        if not self._enabled:
            return

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter, max_export_batch_size=batch_size)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(__name__)

    def __call__(self, record: LogRecord) -> None:
        if not self._enabled:
            return
        self._export(record)

    def _export(self, record: LogRecord) -> None:
        kind = _EVENT_TO_OTEL_KIND.get(record.event_type, SpanKind.INTERNAL)
        attributes = dict(record.payload)
        attributes.update({
            "event_type": record.event_type,
            "agent_name": record.agent_name,
            "session_id": record.session_id,
        })

        if record.exception:
            attributes["exception"] = record.exception

        with self._tracer.start_as_current_span(
            name=record.event_type,
            kind=kind,
            attributes=attributes,
        ) as span:
            if record.duration_ms is not None:
                span.set_attribute("duration_ms", record.duration_ms)
            if record.exception:
                span.set_status(Status(StatusCode.ERROR, record.exception))
