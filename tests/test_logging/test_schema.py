"""LogRecord 数据模型测试。"""

from src.logging.constants import EventType
from src.logging.schema import LogRecord


class TestLogRecord:
    def test_create_with_all_fields(self) -> None:
        record = LogRecord.create(
            level="INFO",
            event_type="agent.thought",
            message="测试消息",
            payload={"key": "value"},
            duration_ms=100.0,
        )
        assert record.level == "INFO"
        assert record.event_type == "agent.thought"
        assert record.message == "测试消息"
        assert record.payload == {"key": "value"}
        assert record.duration_ms == 100.0

    def test_create_auto_fills_timestamp(self) -> None:
        record = LogRecord.create("INFO", "test.event", "msg")
        assert record.timestamp != ""
        assert "T" in record.timestamp

    def test_to_dict_includes_at_timestamp(self) -> None:
        record = LogRecord.create("INFO", "test.event", "msg")
        d = record.to_dict()
        assert "@timestamp" in d
        assert d["@timestamp"] == record.timestamp

    def test_to_json_is_valid(self) -> None:
        import json

        record = LogRecord.create("ERROR", "system.error", "错误", exception="测试异常")
        js = record.to_json()
        parsed = json.loads(js)
        assert parsed["level"] == "ERROR"
        assert parsed["exception"] == "测试异常"
        assert parsed["event_type"] == "system.error"

    def test_default_values(self) -> None:
        record = LogRecord()
        assert record.level == "INFO"
        assert record.payload == {}
        assert record.duration_ms is None
        assert record.exception is None

    def test_event_type_enum_usage(self) -> None:
        record = LogRecord.create("INFO", EventType.AGENT_THOUGHT, "思考")
        assert record.event_type == "agent.thought"
