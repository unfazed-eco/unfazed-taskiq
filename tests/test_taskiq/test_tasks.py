"""
Task tests covering: regular, scheduled, args/kwargs, schedule_id, failing tasks.

Reference: https://taskiq-python.github.io/guide/testing-taskiq.html
"""

from unfazed.core import Unfazed
from unfazed.test import Requestfactory

from tests.proj.app1.tasks import (
    add,
    concat,
    failing_task,
    merge,
    mixed_args,
    multiply,
    scheduled_echo,
)
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus


async def test_api(unfazed: Unfazed) -> None:
    """Test API endpoint that invokes add task."""
    async with Requestfactory(unfazed) as rf:
        resp = await rf.get("/app1/add?a=1&b=2")

        assert resp.status_code == 200
        assert resp.json() == {"result": 3}


async def test_regular_task_positional_args(unfazed: Unfazed) -> None:
    """Regular task with positional arguments."""
    task = await add.kiq(3, 5)  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == 8


async def test_regular_task_named_params(unfazed: Unfazed) -> None:
    """Task with named parameters."""
    task = await multiply.kiq(a=4, b=7)  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == 28


async def test_task_variable_positional_args(unfazed: Unfazed) -> None:
    """Task with *args."""
    task = await concat.kiq("a", "b", "c")  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == "abc"


async def test_task_variable_keyword_args(unfazed: Unfazed) -> None:
    """Task with **kwargs."""
    task = await merge.kiq(x="1", y="2", z="3")  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == {"x": "1", "y": "2", "z": "3"}


async def test_task_mixed_args(unfazed: Unfazed) -> None:
    """Task with positional, *args, and keyword param."""
    task = await mixed_args.kiq(1, 2, 3, 4, prefix="sum=")  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == "sum=10"


async def test_task_with_schedule_id(unfazed: Unfazed) -> None:
    """Task with schedule_id in labels (simulates scheduled task)."""
    schedule_id = "sched-test-001"
    task = (
        await scheduled_echo.kicker().with_labels(schedule_id=schedule_id).kiq("hello")  # type: ignore[attr-defined]
    )
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == "echo:hello"

    # Verify schedule_id persisted in result backend
    row = await TaskiqResultModel.filter(task_id=task.task_id).first()
    assert row is not None
    assert row.schedule_id == schedule_id
    assert row.status == TaskStatus.SUCCESS


async def test_scheduled_task_via_scheduler(
    unfazed: Unfazed, test_scheduler_sample_data: list
) -> None:
    """Scheduled task triggered by scheduler (PeriodicTask with schedule_id)."""
    from unfazed_taskiq.contrib.scheduler.models import PeriodicTask

    # Get an enabled schedule
    enabled = await PeriodicTask.filter(enabled=1).first()
    assert enabled is not None

    # Manually kick with same schedule_id as scheduler would
    task = (
        await scheduled_echo.kicker()  # type: ignore[attr-defined]
        .with_labels(schedule_id=enabled.schedule_id)
        .kiq("scheduled")  # type: ignore[attr-defined]
    )
    result = await task.wait_result(timeout=10)

    assert result.is_err is False
    assert result.return_value == "echo:scheduled"

    row = await TaskiqResultModel.filter(task_id=task.task_id).first()
    assert row is not None
    assert row.schedule_id == enabled.schedule_id


async def test_failing_task(unfazed: Unfazed) -> None:
    """Task that raises exception - check return_value, traceback, DB."""
    task = await failing_task.kiq("intentional failure")  # type: ignore[attr-defined]
    result = await task.wait_result(timeout=10, with_logs=True)

    assert result.is_err is True
    assert result.return_value is None
    assert result.log is not None
    assert "ValueError" in result.log
    assert "intentional failure" in result.log
    assert "Traceback" in result.log

    # Verify traceback persisted in result backend
    row = await TaskiqResultModel.filter(task_id=task.task_id).first()
    assert row is not None
    assert row.status == TaskStatus.FAILURE
    assert row.traceback is not None
    assert "ValueError" in row.traceback
    assert "intentional failure" in row.traceback
