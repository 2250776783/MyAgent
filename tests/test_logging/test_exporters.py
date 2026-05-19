"""导出器和重放系统测试。"""

import os
import tempfile

from src.logging.exporters.base import BaseExporter
from src.logging.replay.player import LogPlayer
from src.logging.replay.recorder import LogRecorder
from src.logging.schema import LogRecord


class TestBaseExporter:
    def test_batch_flush_on_count(self) -> None:
        exported: list[list[LogRecord]] = []

        class TestExporter(BaseExporter):
            def export(self, records: list[LogRecord]) -> None:
                exported.append(records)

        e = TestExporter(batch_size=3)
        e(LogRecord.create("INFO", "a", "1"))
        e(LogRecord.create("INFO", "b", "2"))
        assert len(exported) == 0  # not yet
        e(LogRecord.create("INFO", "c", "3"))  # triggers flush
        assert len(exported) == 1
        assert len(exported[0]) == 3

    def test_manual_flush(self) -> None:
        exported: list[list[LogRecord]] = []

        class TestExporter(BaseExporter):
            def export(self, records: list[LogRecord]) -> None:
                exported.append(records)

        e = TestExporter(batch_size=100)
        e(LogRecord.create("INFO", "a", "1"))
        e.flush()
        assert len(exported) == 1
        assert len(exported[0]) == 1

    def test_export_error_does_not_crash(self) -> None:
        class FailingExporter(BaseExporter):
            def export(self, records: list[LogRecord]) -> None:
                raise RuntimeError("fail")

        e = FailingExporter(batch_size=1)
        e(LogRecord.create("INFO", "a", "1"))  # should not raise


class TestReplayRoundtrip:
    def test_record_and_replay(self) -> None:
        tmpdir = tempfile.mkdtemp()

        rec = LogRecorder(tmpdir)
        rec(LogRecord.create("INFO", "test.a", "第一条消息"))
        rec(LogRecord.create("ERROR", "test.b", "第二条消息", exception="err"))
        rec.close()

        files = list(rec._log_dir.glob("*.jsonl"))
        assert len(files) == 1

        player = LogPlayer(files[0])
        records = list(player.replay())
        assert len(records) == 2
        assert records[0].event_type == "test.a"
        assert records[1].event_type == "test.b"
        assert records[1].exception == "err"

        # Cleanup
        files[0].unlink()
        os.rmdir(tmpdir)

    def test_replay_with_filter(self) -> None:
        tmpdir = tempfile.mkdtemp()

        rec = LogRecorder(tmpdir)
        rec(LogRecord.create("INFO", "llm.prompt", "p1"))
        rec(LogRecord.create("INFO", "tool.call", "t1"))
        rec(LogRecord.create("INFO", "llm.response", "r1"))
        rec.close()

        files = list(rec._log_dir.glob("*.jsonl"))
        player = LogPlayer(files[0])
        filtered = list(player.replay(event_filter={"llm.prompt", "llm.response"}))
        assert len(filtered) == 2
        assert all(r.event_type.startswith("llm.") for r in filtered)

        files[0].unlink()
        os.rmdir(tmpdir)

    def test_replay_empty_file(self) -> None:
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "empty.jsonl")
        open(path, "w").close()

        player = LogPlayer(path)
        records = list(player.replay())
        assert len(records) == 0

        os.unlink(path)
        os.rmdir(tmpdir)

    def test_replay_sorted(self) -> None:
        tmpdir = tempfile.mkdtemp()
        rec = LogRecorder(tmpdir)
        rec(LogRecord.create("INFO", "b", "second"))
        rec(LogRecord.create("INFO", "a", "first"))
        rec.close()

        files = list(rec._log_dir.glob("*.jsonl"))
        player = LogPlayer(files[0])
        sorted_records = player.replay_sorted()
        assert len(sorted_records) == 2

        files[0].unlink()
        os.rmdir(tmpdir)
