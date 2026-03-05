import time
import traceback
from typing import TYPE_CHECKING, Any, Union

from taskiq.abc.middleware import TaskiqMiddleware

from unfazed_taskiq.contrib.result_backend.models import TaskiqResultModel, TaskStatus

if TYPE_CHECKING:  # pragma: no cover
    from taskiq.message import TaskiqMessage
    from taskiq.result import TaskiqResult


class TaskiqResultPreSendMiddleware(TaskiqMiddleware):
    """Middleware that records date_created and task metadata in pre_send."""

    async def pre_send(self, message: "TaskiqMessage") -> "TaskiqMessage":
        """Insert or update task record with date_created before sending to broker."""
        task_id = message.task_id
        task_name = message.task_name
        task_args: Union[list, None] = list(message.args) if message.args else None
        task_kwargs: Union[dict, None] = (
            dict(message.kwargs) if message.kwargs else None
        )
        labels = message.labels or {}
        schedule_id = labels.get("schedule_id")
        date_created = int(time.time() * 1000)

        existing = await TaskiqResultModel.filter(task_id=task_id).first()
        if existing:
            await TaskiqResultModel.filter(task_id=task_id).update(
                date_created=date_created,
                task_name=task_name,
                task_args=task_args,
                task_kwargs=task_kwargs,
                schedule_id=schedule_id,
                status=int(TaskStatus.STARTED),
            )
        else:
            await TaskiqResultModel.create(
                task_id=task_id,
                date_created=date_created,
                task_name=task_name,
                task_args=task_args,
                task_kwargs=task_kwargs,
                schedule_id=schedule_id,
                status=int(TaskStatus.STARTED),
            )

        return message

    async def on_error(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
        exception: BaseException,
    ) -> None:
        """Write traceback to result.log so it is persisted in set_result."""
        result.log = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
