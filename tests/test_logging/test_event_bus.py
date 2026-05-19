"""EventBus 事件总线测试。"""

from src.logging.event import EventBus
from src.logging.schema import LogRecord


class TestEventBus:
    def test_subscribe_and_publish(self) -> None:
        bus = EventBus(async_mode=False)
        received: list[LogRecord] = []

        bus.subscribe("test.event", received.append)
        record = LogRecord.create("INFO", "test.event", "hello")
        bus.publish(record)

        assert len(received) == 1
        assert received[0].message == "hello"

    def test_wildcard_subscriber(self) -> None:
        bus = EventBus(async_mode=False)
        received: list[LogRecord] = []

        bus.subscribe("*", received.append)
        bus.publish(LogRecord.create("INFO", "any.event", "msg"))

        assert len(received) == 1

    def test_wildcard_subscribe_all(self) -> None:
        bus = EventBus(async_mode=False)
        received: list[LogRecord] = []

        bus.subscribe("*", received.append)
        bus.publish(LogRecord.create("INFO", "agent.thought", "a"))
        bus.publish(LogRecord.create("INFO", "tool.call", "b"))

        assert len(received) == 2

    def test_unsubscribe_removes_handler(self) -> None:
        bus = EventBus(async_mode=False)
        received: list[LogRecord] = []
        handler = received.append

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        bus.publish(LogRecord.create("INFO", "test.event", "msg"))

        assert len(received) == 0

    def test_no_handlers_does_not_crash(self) -> None:
        bus = EventBus(async_mode=False)
        bus.publish(LogRecord.create("INFO", "unhandled", "msg"))

    def test_handler_exception_does_not_crash(self) -> None:
        bus = EventBus(async_mode=False)

        def failing(_record: LogRecord) -> None:
            raise ValueError("oops")

        bus.subscribe("test.event", failing)
        bus.publish(LogRecord.create("INFO", "test.event", "msg"))

    def test_multiple_handlers_same_event(self) -> None:
        bus = EventBus(async_mode=False)
        results: list[int] = []

        bus.subscribe("test.event", lambda _: results.append(1))
        bus.subscribe("test.event", lambda _: results.append(2))
        bus.publish(LogRecord.create("INFO", "test.event", "msg"))

        assert results == [1, 2]
