import pytest
from taskiq.message import TaskiqMessage
from taskiq.result import TaskiqResult

from unfazed_taskiq.contrib.result_backend.middleware import TaskiqResultPreSendMiddleware
from unfazed_taskiq.contrib.result_backend.models import TaskiqResultModel, TaskStatus


@pytest.fixture
def middleware() -> TaskiqResultPreSendMiddleware:
    return TaskiqResultPreSendMiddleware()


@pytest.fixture(autouse=True)
async def cleanup() -> None:
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
        """Test pre_send clears result/date_done/traceback when reusing task_id."""
        await TaskiqResultModel.create(
            task_id="msg-reuse",
            status=int(TaskStatus.SUCCESS),
            task_name="old.task",
            date_created=1000,
            date_done=2000,
            result=b"old-result",
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
