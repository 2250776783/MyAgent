"""Tool 错误类型层次。

提供结构化的错误分类，方便 runtime 层进行错误处理和重试决策。
"""


class ToolError(Exception):
    """工具错误基类。"""
    pass


class ToolTimeoutError(ToolError):
    """工具执行超时。"""
    pass


class ToolPermissionError(ToolError):
    """工具权限不足（安全策略阻止）。"""
    pass


class ToolExecutionError(ToolError):
    """工具执行过程中出错。"""
    pass


class ToolNotFoundError(ToolError):
    """未找到指定工具。"""
    pass


class ToolValidationError(ToolError):
    """工具参数校验失败。"""
    pass
