"""安全策略层。

提供工具执行前的安全检查、权限校验等能力。
"""

from .security import check_permission, should_confirm

__all__ = [
    "check_permission",
    "should_confirm",
]
