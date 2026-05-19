"""MemoryStore 抽象基类 — 统一存储后端接口。

支持同步（sync）和异步（async）两种调用模式：
- ChromaMemoryStore / SQLMemoryStore → 同步实现
- PGVectorMemoryStore                → 异步实现

扩展方式：继承 MemoryStore，实现所需的方法组（sync 或 async）。
"""

from abc import ABC, abstractmethod
from typing import Any

from ..types import MemoryItem


class MemoryStore(ABC):
    """记忆存储抽象基类。

    所有存储后端必须实现同步方法（save / get / search / delete / update / count / get_all）。
    异步方法默认抛出 NotImplementedError，异步后端应覆盖对应的 a* 方法。
    """

    # ── 同步接口（同步后端必须实现） ──────────────────────────────────

    @abstractmethod
    def save(self, item: MemoryItem) -> str:
        """保存一条记忆，返回 memory_id。"""

    def save_batch(self, items: list[MemoryItem]) -> list[str]:
        """批量保存记忆，默认逐条调用 save()。"""
        return [self.save(item) for item in items]

    @abstractmethod
    def get(self, memory_id: str) -> MemoryItem | None:
        """按 ID 获取记忆。"""

    @abstractmethod
    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        """按向量相似度搜索记忆。"""

    @abstractmethod
    def delete(self, memory_id: str) -> None:
        """删除一条记忆。"""

    @abstractmethod
    def update(self, memory_id: str, **updates) -> None:
        """更新记忆字段。"""

    @abstractmethod
    def count(self) -> int:
        """返回记忆总数。"""

    @abstractmethod
    def get_all(self) -> list[MemoryItem]:
        """返回所有记忆（用于后台维护任务）。"""

    # ── 异步接口（异步后端覆盖，同步后端可忽略） ────────────────────

    async def asave(self, item: MemoryItem) -> str:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async save"
        )

    async def asave_batch(self, items: list[MemoryItem]) -> list[str]:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async save_batch"
        )

    async def aget(self, memory_id: str) -> MemoryItem | None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async get"
        )

    async def asearch(
        self, query_embedding: list[float], k: int = 5
    ) -> list[MemoryItem]:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async search"
        )

    async def adelete(self, memory_id: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async delete"
        )

    async def aupdate(self, memory_id: str, **updates) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async update"
        )

    async def acount(self) -> int:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async count"
        )

    async def aget_all(self) -> list[MemoryItem]:
        raise NotImplementedError(
            f"{type(self).__name__} does not support async get_all"
        )

    # ── 生命周期 ──────────────────────────────────────────────────────

    async def aclose(self) -> None:
        """异步关闭连接池（异步后端应覆盖）。"""

    def close(self) -> None:
        """同步释放资源（同步后端可覆盖，异步后端无需实现）。"""

    # ── 工具方法 ──────────────────────────────────────────────────────

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """安全地将值转换为 float。"""
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        """安全地将值转换为 int。"""
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
