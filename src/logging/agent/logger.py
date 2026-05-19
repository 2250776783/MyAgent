"""Agent 日志器 — 思考、决策、反思。

记录 Agent 核心推理过程的专用日志接口。
"""

from typing import Any

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType


class AgentLogger:
    """Agent 推理过程日志器。

    用法::

        agent_logger = AgentLogger(adapter)
        agent_logger.thought("分析用户意图", iteration=1)
        agent_logger.decision("调用天气查询工具", reasoning="用户询问天气")
        agent_logger.reflection("工具返回结果不完整，需要追问")
    """

    def __init__(self, adapter: LoggerAdapter) -> None:
        self._adapter = adapter

    def thought(self, content: str, *, iteration: int = 0, **extra: Any) -> None:
        """记录 Agent 思考过程。"""
        self._adapter.info(
            EventType.AGENT_THOUGHT,
            content,
            iteration=iteration,
            **extra,
        )

    def decision(self, action: str, *, reasoning: str = "", **extra: Any) -> None:
        """记录 Agent 决策。"""
        self._adapter.info(
            EventType.AGENT_DECISION,
            f"决策: {action}",
            action=action,
            reasoning=reasoning,
            **extra,
        )

    def reflection(self, insight: str, **extra: Any) -> None:
        """记录 Agent 反思。"""
        self._adapter.info(
            EventType.AGENT_REFLECTION,
            insight,
            **extra,
        )
