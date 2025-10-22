import traceback
from typing import Any

from taskiq import TaskiqMessage, TaskiqResult
from taskiq.abc.middleware import TaskiqMiddleware
from unfazed_sentry import capture_exception

from unfazed_taskiq.logger import log


class UnfazedTaskiqExceptionMiddleware(TaskiqMiddleware):
    async def on_error(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
        exception: BaseException,
    ) -> None:
        capture_exception(exception, result=result, message=message)
        exception_type = type(exception).__name__

        log.error(
            f"Task '{message.task_name}' failed with {exception_type}: {exception}",
            extra={
                "task_name": message.task_name,
                "task_args": message.args,
                "task_kwargs": message.kwargs,
                "exception_type": exception_type,
                "exception": str(exception),
                "traceback": traceback.format_exc(),
            },
        )
