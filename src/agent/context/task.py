"""Task Context - 任务追踪器。

将目标分解为可执行任务，追踪状态、依赖和重试。
"""

from __future__ import annotations

import logging
from typing import Any

from .types import Task, TaskStatus, ContextSegment

logger = logging.getLogger(__name__)


class TaskTracker:
    """任务追踪器。

    Args:
        max_tasks: 最大追踪任务数
        max_iterations: 单任务最大重试次数
    """

    def __init__(self, max_tasks: int = 10, max_iterations: int = 3) -> None:
        self._tasks: list[Task] = []
        self.max_tasks = max_tasks
        self.max_iterations = max_iterations

    @property
    def active_tasks(self) -> list[Task]:
        return [t for t in self._tasks if t.status in (
            TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED,
        )]

    @property
    def completed_tasks(self) -> list[Task]:
        return [t for t in self._tasks if t.status == TaskStatus.COMPLETED]

    def add_task(self, description: str, goal_id: str = "",
                 depends_on: list[str] | None = None) -> Task:
        task = Task(
            description=description,
            goal_id=goal_id,
            depends_on=depends_on or [],
            max_iterations=self.max_iterations,
        )
        self._tasks.append(task)
        if task.depends_on:
            deps_done = all(
                any(t.id == dep_id and t.status == TaskStatus.COMPLETED
                    for t in self._tasks)
                for dep_id in task.depends_on
            )
            if not deps_done:
                task.status = TaskStatus.BLOCKED
        return task

    def start_task(self, task_id: str) -> None:
        for task in self._tasks:
            if task.id == task_id and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.IN_PROGRESS
                task.updated_at = __import__("time").time()
                break

    def complete_task(self, task_id: str, result: str = "") -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.updated_at = __import__("time").time()
                self._unblock_dependents(task_id)
                break

    def fail_task(self, task_id: str, error: str = "") -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.iteration += 1
                if task.iteration >= task.max_iterations:
                    task.status = TaskStatus.FAILED
                    task.result = f"失败: {error}"
                else:
                    task.status = TaskStatus.PENDING
                    task.result = f"重试 {task.iteration}/{task.max_iterations}: {error}"
                task.updated_at = __import__("time").time()
                break

    def detect_repeated_failures(self) -> bool:
        recent = [t for t in self._tasks if t.status == TaskStatus.FAILED]
        return len(recent) >= 3

    def build_context(self, max_tasks: int = 5) -> list[ContextSegment]:
        segments = []
        ordered = self.active_tasks + self.completed_tasks[-3:]
        for task in ordered[:max_tasks]:
            segments.append(task.to_context())
        return segments

    def _unblock_dependents(self, completed_id: str) -> None:
        for task in self._tasks:
            if task.status == TaskStatus.BLOCKED and completed_id in task.depends_on:
                task.depends_on.remove(completed_id)
                if not task.depends_on:
                    task.status = TaskStatus.PENDING
