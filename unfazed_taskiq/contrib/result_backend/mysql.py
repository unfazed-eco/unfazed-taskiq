import time
from typing import Optional, TypeVar

from taskiq import AsyncResultBackend, TaskiqResult
from taskiq.abc.serializer import TaskiqSerializer
from taskiq.serializers import PickleSerializer

from unfazed_taskiq.contrib.result_backend.exceptions import (
    ResultIsMissingError,
    ResultNotReadyError,
)
from unfazed_taskiq.contrib.result_backend.models import TaskiqResultModel, TaskStatus

_ReturnType = TypeVar("_ReturnType")


class MySQLResultBackend(AsyncResultBackend[_ReturnType]):
    """Result backend for Taskiq using MySQL/TiDB via Tortoise ORM."""

    def __init__(self, serializer: Optional[TaskiqSerializer] = None) -> None:
        """
        Construct MySQL result backend.

        :param serializer: Serializer for TaskiqResult, defaults to PickleSerializer.
        """
        super().__init__()
        self.serializer: TaskiqSerializer = serializer or PickleSerializer()

    async def set_result(
        self,
        task_id: str,
        result: TaskiqResult[_ReturnType],
    ) -> None:
        """Store result. Query first, then update or create."""
        result_bytes = self.serializer.dumpb(result)
        status = TaskStatus.SUCCESS if not result.is_err else TaskStatus.FAILURE
        date_done = int(time.time() * 1000)
        traceback_val = result.log if result.is_err else None

        existing = await TaskiqResultModel.filter(task_id=task_id).first()
        if existing:
            await TaskiqResultModel.filter(task_id=task_id).update(
                result=result_bytes,
                status=int(status),
                date_done=date_done,
                traceback=traceback_val,
            )
        else:
            await TaskiqResultModel.create(
                task_id=task_id,
                result=result_bytes,
                status=int(status),
                date_done=date_done,
                traceback=traceback_val,
            )

    async def is_result_ready(self, task_id: str) -> bool:
        """Check if result exists for task_id and task has completed (SUCCESS or FAILURE)."""
        row = await TaskiqResultModel.filter(task_id=task_id).first()
        if row is None:
            return False
        return row.status in (TaskStatus.SUCCESS, TaskStatus.FAILURE)

    async def get_result(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskiqResult[_ReturnType]:
        """Retrieve result.

        :raises ResultIsMissingError: When task record is not found in database.
        :raises ResultNotReadyError: When task record exists but result is not ready
            (task still running).
        """
        row = await TaskiqResultModel.filter(task_id=task_id).first()
        if row is None:
            raise ResultIsMissingError(f"Task {task_id} not found in database")
        if row.result is None:
            raise ResultNotReadyError(
                f"Task {task_id} has not completed yet; result is not ready"
            )

        taskiq_result: TaskiqResult[_ReturnType] = self.serializer.loadb(row.result)
        if not with_logs:
            taskiq_result.log = None
        if row.task_name is not None:
            taskiq_result.labels["task_name"] = row.task_name
        if row.schedule_id is not None:
            taskiq_result.labels["schedule_id"] = row.schedule_id
        return taskiq_result
