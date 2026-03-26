"""Tests for ``MySQLResultBackend``.

``set_result`` and ``get_result`` are exercised in separate test classes. Setup uses
``TaskiqResultModel.create`` / ORM (trusted) and ``PickleSerializer`` for blobs, not
``set_result``, so a failure in ``get_result`` tests cannot be attributed to ``set_result``.
"""

from unittest.mock import patch

import pytest
from taskiq.result import TaskiqResult
from taskiq.serializers import PickleSerializer
from tortoise.exceptions import IntegrityError as TortoiseIntegrityError
from tortoise.queryset import UpdateQuery

from unfazed_taskiq.contrib.result.exceptions import (
    ResultIsMissingError,
    ResultNotReadyError,
)
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result.mysql import MySQLResultBackend
from unfazed_taskiq.contrib.result.utils import (
    TASKIQ_JSON_STR_FALLBACK_KEY,
    encode_for_json_field,
)


class _OpaqueReturnValue:
    """Pickle-serializable, not JSON-serializable; for return_value column fallback tests."""

    def __str__(self) -> str:
        return "opaque-rv"


def _default_serializer() -> PickleSerializer:
    return PickleSerializer()


async def _seed_completed_row(
    *,
    task_id: str,
    return_value: object = 1,
    is_err: bool = False,
    log: str | None = None,
    task_name: str | None = None,
    schedule_id: str | None = None,
    execution_time: float = 1.0,
) -> None:
    """Insert a terminal-status row with a valid result blob (trusted test setup)."""
    ser = _default_serializer()
    tr = TaskiqResult(
        is_err=is_err,
        return_value=return_value,
        execution_time=execution_time,
        log=log,
    )
    blob = ser.dumpb(tr)
    status = TaskStatus.FAILURE if is_err else TaskStatus.SUCCESS
    rv_db = None if is_err else encode_for_json_field(return_value)
    await TaskiqResultModel.create(
        task_id=task_id,
        status=int(status),
        result=blob,
        date_done=123,
        traceback=log if is_err else None,
        return_value=rv_db,
        task_name=task_name,
        schedule_id=schedule_id,
    )


@pytest.fixture
def backend() -> MySQLResultBackend:
    return MySQLResultBackend()


@pytest.fixture
def backend_with_custom_serializer() -> MySQLResultBackend:
    return MySQLResultBackend(serializer=PickleSerializer())


@pytest.fixture(autouse=True)
async def cleanup() -> None:
    yield
    await TaskiqResultModel.all().delete()


class TestMySQLResultBackendSetResult:
    """Only ``set_result``; assertions via ORM read / ``loadb`` on ``row.result``."""

    async def test_set_result_inserts_when_no_row(self, backend: MySQLResultBackend) -> None:
        task_id = "test-create-only"
        result = TaskiqResult(
            is_err=False,
            return_value=123,
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert row.status == TaskStatus.SUCCESS
        assert row.result is not None
        assert _default_serializer().loadb(row.result).return_value == 123
        assert row.return_value == encode_for_json_field(123)

    async def test_set_result_updates_existing_started_row(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-update"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
        )
        result = TaskiqResult(
            is_err=False,
            return_value=99,
            execution_time=2.0,
            log=None,
        )
        await backend.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert row.status == TaskStatus.SUCCESS
        assert _default_serializer().loadb(row.result).return_value == 99
        assert await TaskiqResultModel.filter(task_id=task_id).count() == 1

    async def test_set_result_failure_persists_traceback_and_status(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-failure"
        result = TaskiqResult(
            is_err=True,
            return_value=None,
            execution_time=0.1,
            log="Traceback: error occurred",
        )
        await backend.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert row.status == TaskStatus.FAILURE
        assert row.traceback == "Traceback: error occurred"
        assert row.return_value is None
        loaded = _default_serializer().loadb(row.result)
        assert loaded.is_err is True

    async def test_set_result_string_return_value_column_uses_fallback_shape(
        self, backend_with_custom_serializer: MySQLResultBackend
    ) -> None:
        """Bare str for return_value uses JSONField fallback; covers explicit serializer in ``__init__``."""
        task_id = "test-rv-str-col"
        result = TaskiqResult(
            is_err=False,
            return_value="hello",
            execution_time=0,
            log=None,
        )
        await backend_with_custom_serializer.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert row.return_value == {TASKIQ_JSON_STR_FALLBACK_KEY: "hello"}

    async def test_set_result_non_json_return_value_column_fallback(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-rv-opaque"
        result = TaskiqResult(
            is_err=False,
            return_value=_OpaqueReturnValue(),
            execution_time=0,
            log=None,
        )
        await backend.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert isinstance(row.return_value, dict)
        assert TASKIQ_JSON_STR_FALLBACK_KEY in row.return_value
        assert "opaque-rv" in row.return_value[TASKIQ_JSON_STR_FALLBACK_KEY]

    async def test_set_result_integrity_error_retries_update(
        self, backend: MySQLResultBackend
    ) -> None:
        """Race: first update returns 0, create hits duplicate key, second update persists."""
        task_id = "integrity-set"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="t",
        )
        result = TaskiqResult(
            is_err=False,
            return_value=55,
            execution_time=0,
            log=None,
        )
        update_calls = [0]
        orig_execute = UpdateQuery._execute

        async def _execute_first_returns_zero(self: UpdateQuery) -> int:
            if self.model is TaskiqResultModel:
                update_calls[0] += 1
                if update_calls[0] == 1:
                    return 0
            return await orig_execute(self)

        with patch.object(UpdateQuery, "_execute", _execute_first_returns_zero):
            with patch.object(
                TaskiqResultModel,
                "create",
                side_effect=TortoiseIntegrityError("duplicate"),
            ):
                await backend.set_result(task_id, result)
        row = await TaskiqResultModel.get(task_id=task_id)
        assert row.status == TaskStatus.SUCCESS
        assert _default_serializer().loadb(row.result).return_value == 55


class TestMySQLResultBackendGetResult:
    """Only ``get_result`` / ``is_result_ready``; rows from ``_seed_completed_row`` (ORM)."""

    async def test_get_result_deserializes_return_value(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-get-rv"
        await _seed_completed_row(task_id=task_id, return_value=42)
        retrieved = await backend.get_result(task_id)
        assert retrieved.return_value == 42
        assert retrieved.is_err is False

    async def test_get_result_with_logs_true(self, backend: MySQLResultBackend) -> None:
        task_id = "test-task-logs"
        await _seed_completed_row(
            task_id=task_id,
            return_value=1,
            log="some log output",
        )
        retrieved = await backend.get_result(task_id, with_logs=True)
        assert retrieved.log == "some log output"

    async def test_get_result_with_logs_false_clears_log(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-task-no-logs"
        await _seed_completed_row(
            task_id=task_id,
            return_value=1,
            log="log content",
        )
        retrieved = await backend.get_result(task_id, with_logs=False)
        assert retrieved.log is None

    async def test_is_result_ready_true_when_completed(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-ready"
        await _seed_completed_row(task_id=task_id)
        assert await backend.is_result_ready(task_id) is True

    async def test_get_result_includes_task_name_in_labels(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-task-name-label"
        await _seed_completed_row(
            task_id=task_id,
            task_name="my.app.task",
        )
        retrieved = await backend.get_result(task_id)
        assert retrieved.labels.get("task_name") == "my.app.task"

    async def test_get_result_includes_schedule_id_in_labels(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-schedule-id-label"
        await _seed_completed_row(
            task_id=task_id,
            schedule_id="sched-xyz789",
        )
        retrieved = await backend.get_result(task_id)
        assert retrieved.labels.get("schedule_id") == "sched-xyz789"


class TestMySQLResultBackendReadinessAndErrors:
    """Missing rows, running tasks, inconsistent or corrupt DB state."""

    async def test_is_result_ready_false_when_no_record(
        self, backend: MySQLResultBackend
    ) -> None:
        assert await backend.is_result_ready("nonexistent-task") is False

    async def test_get_result_raises_when_no_record(self, backend: MySQLResultBackend) -> None:
        with pytest.raises(ResultIsMissingError, match="not found in database"):
            await backend.get_result("nonexistent-task")

    async def test_started_row_without_result_not_ready(
        self, backend: MySQLResultBackend
    ) -> None:
        """STARTED + no blob: ``is_result_ready`` false and ``get_result`` raises."""
        task_id = "test-started-no-result"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
            result=None,
        )
        assert await backend.is_result_ready(task_id) is False
        with pytest.raises(ResultNotReadyError, match="has not completed yet"):
            await backend.get_result(task_id)

    async def test_started_with_stale_blob_still_not_ready(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-inconsistent"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.STARTED),
            task_name="test.task",
            result=_default_serializer().dumpb(
                TaskiqResult(is_err=False, return_value=999, execution_time=0, log=None)
            ),
            date_done=12345,
            traceback="old error",
        )
        assert await backend.is_result_ready(task_id) is False
        with pytest.raises(ResultNotReadyError, match="has not completed yet"):
            await backend.get_result(task_id)

    async def test_terminal_status_without_result_blob_not_ready(
        self, backend: MySQLResultBackend
    ) -> None:
        task_id = "test-corrupt-success-no-blob"
        await TaskiqResultModel.create(
            task_id=task_id,
            status=int(TaskStatus.SUCCESS),
            result=None,
            date_done=1,
        )
        assert await backend.is_result_ready(task_id) is False
        with pytest.raises(ResultNotReadyError, match="has not completed yet"):
            await backend.get_result(task_id)
