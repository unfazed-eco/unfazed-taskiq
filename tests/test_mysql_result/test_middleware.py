from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from taskiq.message import TaskiqMessage
from taskiq.result import TaskiqResult
from tortoise.exceptions import IntegrityError as TortoiseIntegrityError
from tortoise.queryset import UpdateQuery

from unfazed_taskiq.contrib.result.middleware import TaskiqResultPreSendMiddleware
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result.utils import TASKIQ_JSON_STR_FALLBACK_KEY


@pytest.fixture
def middleware() -> TaskiqResultPreSendMiddleware:
    return TaskiqResultPreSendMiddleware()


@pytest.fixture(autouse=True)
async def cleanup() -> AsyncGenerator[None, None]:
    yield
    await TaskiqResultModel.all().delete()


class TestTaskiqResultPreSendMiddleware:
    async def test_pre_send_creates_record(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test pre_send creates record with date_created and metadata."""
        message = TaskiqMessage(
            task_id="msg-001",
            task_name="app.tasks.my_task",
            args=[1, 2],
            kwargs={"key": "value"},
            labels={"schedule_id": "sched-abc123"},
        )
        result = await middleware.pre_send(message)
        assert result is message

        row = await TaskiqResultModel.filter(task_id="msg-001").first()
        assert row is not None
        assert row.status == TaskStatus.STARTED
        assert row.task_name == "app.tasks.my_task"
        assert row.task_args == [1, 2]
        assert row.task_kwargs == {"key": "value"}
        assert row.schedule_id == "sched-abc123"
        assert row.date_created is not None

    async def test_pre_send_updates_existing(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test pre_send updates when record exists (query-first-then-write)."""
        await TaskiqResultModel.create(
            task_id="msg-002",
            status=int(TaskStatus.STARTED),
            task_name="old.task",
            date_created=1000,
        )
        message = TaskiqMessage(
            task_id="msg-002",
            task_name="new.task",
            args=[],
            kwargs={},
            labels={},
        )
        await middleware.pre_send(message)

        row = await TaskiqResultModel.filter(task_id="msg-002").first()
        assert row is not None
        assert row.task_name == "new.task"
        assert row.date_created != 1000
        count = await TaskiqResultModel.filter(task_id="msg-002").count()
        assert count == 1

    async def test_pre_send_clears_completion_fields_on_reuse(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test pre_send clears result/return_value/date_done/traceback when reusing task_id."""
        await TaskiqResultModel.create(
            task_id="msg-reuse",
            status=int(TaskStatus.SUCCESS),
            task_name="old.task",
            date_created=1000,
            date_done=2000,
            result=b"old-result",
            return_value={"done": True},
            traceback="old traceback",
        )
        message = TaskiqMessage(
            task_id="msg-reuse",
            task_name="new.task",
            args=[],
            kwargs={},
            labels={},
        )
        await middleware.pre_send(message)

        row = await TaskiqResultModel.filter(task_id="msg-reuse").first()
        assert row is not None
        assert row.status == TaskStatus.STARTED
        assert row.result is None
        assert row.return_value is None
        assert row.date_done is None
        assert row.traceback is None

    async def test_pre_send_schedule_id_from_labels(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test schedule_id from labels."""
        message = TaskiqMessage(
            task_id="msg-003",
            task_name="app.task",
            args=[],
            kwargs={},
            labels={"schedule_id": "sched-abc123"},
        )
        await middleware.pre_send(message)
        row = await TaskiqResultModel.filter(task_id="msg-003").first()
        assert row is not None
        assert row.schedule_id == "sched-abc123"

    async def test_pre_send_with_empty_args_kwargs_and_no_labels(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test pre_send with empty args/kwargs and labels - covers falsy branches."""
        message = TaskiqMessage(
            task_id="msg-004",
            task_name="minimal.task",
            args=[],
            kwargs={},
            labels={},
        )
        result = await middleware.pre_send(message)
        assert result is message
        row = await TaskiqResultModel.filter(task_id="msg-004").first()
        assert row is not None
        assert row.task_args is None  # empty list is falsy -> None
        assert row.task_kwargs is None  # empty dict is falsy -> None
        assert row.schedule_id is None

    async def test_on_error_writes_traceback_to_result_log(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Test on_error writes exception traceback to result.log for DB persistence."""
        message = TaskiqMessage(
            task_id="msg-error",
            task_name="app.tasks.failing_task",
            args=[],
            kwargs={},
            labels={},
        )
        result = TaskiqResult(
            is_err=True,
            return_value=None,
            execution_time=0.1,
            log=None,
        )
        try:
            raise ValueError("Task failed intentionally")
        except ValueError as exc:
            await middleware.on_error(message, result, exc)

        assert result.log is not None
        assert "ValueError" in result.log
        assert "Task failed intentionally" in result.log
        assert "Traceback" in result.log

    async def test_pre_send_task_args_fallback_when_not_json_serializable(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        class _NotJson:
            pass

        message = TaskiqMessage(
            task_id="msg-bad-args",
            task_name="app.task",
            args=[_NotJson()],
            kwargs={"ok": 1},
            labels={},
        )
        await middleware.pre_send(message)
        row = await TaskiqResultModel.filter(task_id="msg-bad-args").first()
        assert row is not None
        assert isinstance(row.task_args, dict)
        assert TASKIQ_JSON_STR_FALLBACK_KEY in row.task_args
        assert "_NotJson" in row.task_args[TASKIQ_JSON_STR_FALLBACK_KEY]
        assert row.task_kwargs == {"ok": 1}

    async def test_pre_send_task_kwargs_fallback_when_not_json_serializable(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        class _NotJson:
            pass

        message = TaskiqMessage(
            task_id="msg-bad-kwargs",
            task_name="app.task",
            args=[1],
            kwargs={"x": _NotJson()},
            labels={},
        )
        await middleware.pre_send(message)
        row = await TaskiqResultModel.filter(task_id="msg-bad-kwargs").first()
        assert row is not None
        assert row.task_args == [1]
        assert isinstance(row.task_kwargs, dict)
        assert TASKIQ_JSON_STR_FALLBACK_KEY in row.task_kwargs
        assert "_NotJson" in row.task_kwargs[TASKIQ_JSON_STR_FALLBACK_KEY]

    async def test_pre_send_integrity_error_retries_update(
        self, middleware: TaskiqResultPreSendMiddleware
    ) -> None:
        """Race: first update sees 0 rows, create loses duplicate-key, retry update applies."""
        await TaskiqResultModel.create(
            task_id="msg-integrity",
            status=int(TaskStatus.STARTED),
            task_name="before",
        )
        update_calls = [0]
        orig_execute = UpdateQuery._execute

        async def _execute_first_returns_zero(self: UpdateQuery) -> int:
            if self.model is TaskiqResultModel:
                update_calls[0] += 1
                if update_calls[0] == 1:
                    return 0
            return await orig_execute(self)

        message = TaskiqMessage(
            task_id="msg-integrity",
            task_name="after.race",
            args=[1],
            kwargs={},
            labels={},
        )
        with patch.object(UpdateQuery, "_execute", _execute_first_returns_zero):
            with patch.object(
                TaskiqResultModel,
                "create",
                side_effect=TortoiseIntegrityError("duplicate"),
            ):
                out = await middleware.pre_send(message)
        assert out is message
        row = await TaskiqResultModel.get(task_id="msg-integrity")
        assert row.task_name == "after.race"
        assert row.task_args == [1]
