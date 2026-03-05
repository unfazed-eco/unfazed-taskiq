import pytest
from taskiq.result import TaskiqResult
from taskiq.serializers import PickleSerializer

from unfazed_taskiq.contrib.result_backend.exceptions import (
    ResultIsMissingError,
    ResultNotReadyError,
)
from unfazed_taskiq.contrib.result_backend.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result_backend.mysql import MySQLResultBackend


@pytest.fixture
def backend() -> MySQLResultBackend:
    return MySQLResultBackend()


@pytest.fixture
def backend_with_custom_serializer() -> MySQLResultBackend:
    """Backend with explicit serializer for coverage of __init__ serializer param."""
    return MySQLResultBackend(serializer=PickleSerializer())


@pytest.fixture(autouse=True)
async def cleanup() -> None:
    yield
    await TaskiqResultModel.all().delete()


class TestMySQLResultBackend:
    async def test_set_result_and_get_result(self, backend: MySQLResultBackend) -> None:
        """Test set_result and get_result round-trip."""
        task_id = "test-task-001"
        result = TaskiqResult(
            is_err=False,
            return_value=42,
            execution_time=1.0,
            log=None,
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id)
        assert retrieved.return_value == 42
        assert retrieved.is_err is False

    async def test_set_result_and_get_result_with_logs(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result with_logs=True preserves log."""
        task_id = "test-task-logs"
        result = TaskiqResult(
            is_err=False,
            return_value=1,
            execution_time=0.5,
            log="some log output",
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id, with_logs=True)
        assert retrieved.log == "some log output"

    async def test_get_result_with_logs_false_clears_log(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result with_logs=False sets log to None."""
        task_id = "test-task-no-logs"
        result = TaskiqResult(
            is_err=False,
            return_value=1,
            execution_time=0.5,
            log="log content",
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id, with_logs=False)
        assert retrieved.log is None

    async def test_is_result_ready_true(self, backend: MySQLResultBackend) -> None:
        """Test is_result_ready returns True when result exists."""
        task_id = "test-ready"
        result = TaskiqResult(
            is_err=False,
            return_value=1,
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        assert await backend.is_result_ready(task_id) is True

    async def test_is_result_ready_false(self, backend: MySQLResultBackend) -> None:
        """Test is_result_ready returns False when result does not exist."""
        assert await backend.is_result_ready("nonexistent-task") is False

    async def test_get_result_raises_result_is_missing_when_no_record(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result raises ResultIsMissingError when task record does not exist."""
        with pytest.raises(ResultIsMissingError, match="not found in database"):
            await backend.get_result("nonexistent-task")

    async def test_query_first_then_write_update(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test set_result updates existing record (query-first-then-write)."""
        task_id = "test-update"
        # Create initial record via middleware flow (status=STARTED, no result)
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
        )
        # set_result should update, not create
        result = TaskiqResult(
            is_err=False,
            return_value=99,
            execution_time=2.0,
            log=None,
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id)
        assert retrieved.return_value == 99
        # Should still be one record
        count = await TaskiqResultModel.filter(task_id=task_id).count()
        assert count == 1

    async def test_query_first_then_write_create(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test set_result creates when record does not exist."""
        task_id = "test-create-only"
        result = TaskiqResult(
            is_err=False,
            return_value=123,
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id)
        assert retrieved.return_value == 123

    async def test_failure_result(self, backend: MySQLResultBackend) -> None:
        """Test storing and retrieving failed task result."""
        task_id = "test-failure"
        result = TaskiqResult(
            is_err=True,
            return_value=None,
            execution_time=0.1,
            log="Traceback: error occurred",
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id, with_logs=True)
        assert retrieved.is_err is True
        assert retrieved.log == "Traceback: error occurred"

    async def test_init_with_custom_serializer(
        self, backend_with_custom_serializer: MySQLResultBackend
    ) -> None:
        """Test backend works with explicit serializer (covers __init__ serializer param)."""
        task_id = "test-custom-serializer"
        result = TaskiqResult(
            is_err=False,
            return_value="serialized",
            execution_time=0,
            log=None,
        )
        await backend_with_custom_serializer.set_result(task_id, result)
        retrieved = await backend_with_custom_serializer.get_result(task_id)
        assert retrieved.return_value == "serialized"

    async def test_is_result_ready_false_when_started(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test is_result_ready returns False when record exists but status is STARTED."""
        task_id = "test-started"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
        )
        assert await backend.is_result_ready(task_id) is False

    async def test_get_result_raises_result_not_ready_when_task_still_running(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result raises ResultNotReadyError when record exists but result is None."""
        task_id = "test-no-result"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
            result=None,
        )
        with pytest.raises(ResultNotReadyError, match="has not completed yet"):
            await backend.get_result(task_id)

    async def test_get_result_includes_task_name_in_labels(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result adds task_name to labels when row has task_name."""
        task_id = "test-task-name-label"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="my.app.task",
        )
        result = TaskiqResult(
            is_err=False,
            return_value=1,
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id)
        assert retrieved.labels.get("task_name") == "my.app.task"

    async def test_get_result_includes_schedule_id_in_labels(
        self, backend: MySQLResultBackend
    ) -> None:
        """Test get_result adds schedule_id to labels when row has schedule_id."""
        task_id = "test-schedule-id-label"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            schedule_id="sched-xyz789",
        )
        result = TaskiqResult(
            is_err=False,
            return_value=1,
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        retrieved = await backend.get_result(task_id)
        assert retrieved.labels.get("schedule_id") == "sched-xyz789"
