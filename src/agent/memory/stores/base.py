"""MemoryStore 抽象基类。

定义存储后端的统一接口，支持 ChromaDB 和 SQLite 两种实现。
"""

from abc import ABC, abstractmethod

from ..types import MemoryItem


class MemoryStore(ABC):
    """记忆存储抽象基类。"""

    @abstractmethod
    def save(self, item: MemoryItem) -> str:
        """保存一条记忆，返回 memory_id。"""

    @abstractmethod
    def save_batch(self, items: list[MemoryItem]) -> list[str]:
        """批量保存记忆。"""

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
