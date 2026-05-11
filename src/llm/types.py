"""LLM 模块数据模型定义。

提供 Message 数据类，作为系统中所有 LLM 消息的标准格式。
支持 user/assistant/system/tool 四种角色，以及 tool calling 相关字段。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    reasoning_content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.reasoning_content is not None:
            d["reasoning_content"] = self.reasoning_content
        return d
