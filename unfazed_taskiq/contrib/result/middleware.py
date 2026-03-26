import time
import traceback
from typing import TYPE_CHECKING, Any, Union

from taskiq.abc.middleware import TaskiqMiddleware
from tortoise.exceptions import IntegrityError as TortoiseIntegrityError

from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result.utils import encode_for_json_field

if TYPE_CHECKING:  # pragma: no cover
    from taskiq.message import TaskiqMessage
    from taskiq.result import TaskiqResult


class TaskiqResultPreSendMiddleware(TaskiqMiddleware):
    """Middleware that records date_created and task metadata in pre_send."""

    async def pre_send(self, message: "TaskiqMessage") -> "TaskiqMessage":
        """Insert or update task record with date_created before sending to broker."""
        task_id = message.task_id
        task_name = message.task_name
        raw_args: Union[list, None] = list(message.args) if message.args else None
        raw_kwargs: Union[dict, None] = (
            dict(message.kwargs) if message.kwargs else None
        )
        task_args = encode_for_json_field(raw_args)
        task_kwargs = encode_for_json_field(raw_kwargs)
        labels = message.labels or {}
        schedule_id = labels.get("schedule_id")
        date_created = int(time.time() * 1000)

        update_values = {
            "date_created": date_created,
            "task_name": task_name,
            "task_args": task_args,
            "task_kwargs": task_kwargs,
            "schedule_id": schedule_id,
            "status": int(TaskStatus.STARTED),
            "result": None,
            "return_value": None,
            "date_done": None,
            "traceback": None,
        }
        updated = await TaskiqResultModel.filter(task_id=task_id).update(
            **update_values
        )
        if updated == 0:
            try:
                await TaskiqResultModel.create(
                    task_id=task_id,
                    **update_values,
                )
            except TortoiseIntegrityError:
                await TaskiqResultModel.filter(task_id=task_id).update(
                    **update_values
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
