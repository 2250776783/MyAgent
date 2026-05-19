"""Pipeline 处理管道测试。"""

from src.logging.filters import LevelFilter
from src.logging.pipeline import LogPipeline
from src.logging.processors import Enricher, Sanitizer
from src.logging.schema import LogRecord


class TestLogPipeline:
    def test_emit_passes_through_processors(self) -> None:
        pipeline = LogPipeline()
        pipeline.add_processor(Enricher({"app": "test"}))

        record = LogRecord.create("INFO", "test.event", "msg")
        pipeline.emit(record)
        assert record.payload.get("app") == "test"

    def test_level_filter_drops_below_threshold(self) -> None:
        pipeline = LogPipeline()
        pipeline.add_filter(LevelFilter("WARNING"))

        records: list[LogRecord] = []
        pipeline.add_sink(records.append)

        pipeline.emit(LogRecord.create("DEBUG", "test", "skip"))
        pipeline.emit(LogRecord.create("INFO", "test", "skip"))
        pipeline.emit(LogRecord.create("WARNING", "test", "keep"))
        pipeline.emit(LogRecord.create("ERROR", "test", "keep"))

        assert len(records) == 2
        assert records[0].level == "WARNING"
        assert records[1].level == "ERROR"

    def test_sanitizer_redacts_api_key(self) -> None:
        sanitizer = Sanitizer()
        record = LogRecord.create("INFO", "test", 'api_key="sk-1234567890abcdef"')
        sanitizer.process(record)
        assert "sk-1234567890abcdef" not in record.message
        assert record.message == 'api_key="***"'

    def test_sanitizer_redacts_token(self) -> None:
        sanitizer = Sanitizer()
        record = LogRecord.create("INFO", "test", 'token="my-secret-token-123"')
        sanitizer.process(record)
        assert "***" in record.message

    def test_sanitizer_redacts_password_in_payload(self) -> None:
        sanitizer = Sanitizer()
        record = LogRecord.create("INFO", "test", "login", payload={"password": "supersecret"})
        sanitizer.process(record)
        assert record.payload["password"] != "supersecret"
        assert "***" in record.payload["password"]

    def test_full_pipeline_chain(self) -> None:
        pipeline = LogPipeline()
        pipeline.add_processor(Enricher({"env": "test"}))
        pipeline.add_processor(Sanitizer())
        pipeline.add_filter(LevelFilter("INFO"))

        outputs: list[LogRecord] = []
        pipeline.add_sink(outputs.append)

        record = LogRecord.create("INFO", "test", '正常消息 api_key="sk-1234567890abcdef"')
        pipeline.emit(record)

        assert len(outputs) == 1
        assert outputs[0].payload.get("env") == "test"
        assert "sk-1234567890abcdef" not in outputs[0].message
        assert "***" in outputs[0].message
