"""Tests for contrib.result models and app."""

import pytest
from unfazed.core import Unfazed

from unfazed_taskiq.contrib.result.app import AppConfig
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result.serializer import TaskiqResultSerializer


class TestTaskStatus:
    def test_label_property(self) -> None:
        """Test TaskStatus.label returns enum name."""
        assert TaskStatus.STARTED.label == "STARTED"
        assert TaskStatus.SUCCESS.label == "SUCCESS"
        assert TaskStatus.FAILURE.label == "FAILURE"


def _make_serializer_row_kwargs(task_id: str, status: TaskStatus) -> dict:
    """Build kwargs for TaskiqResultModel.create."""
    return {
        "task_id": task_id,
        "status": status,
        "task_name": "test.task",
        "date_created": 1000,
        "date_done": 0,
        "schedule_id": "",
        "task_args": {},
        "task_kwargs": {},
        "traceback": "",
    }


class TestTaskiqResultSerializer:
    @pytest.mark.asyncio
    async def test_from_instance_dumps_status_as_value(self) -> None:
        """Test serializer from_instance produces valid dump with status as enum value."""
        row = await TaskiqResultModel.create(
            **_make_serializer_row_kwargs("serializer-test-001", TaskStatus.SUCCESS)
        )
        ser = TaskiqResultSerializer.from_instance(row)
        dumped = ser.model_dump()
        assert dumped["status"] == TaskStatus.SUCCESS
        assert dumped["task_id"] == "serializer-test-001"
        await row.delete()

    @pytest.mark.asyncio
    async def test_all_status_values_roundtrip(self) -> None:
        """Test serializer works for all TaskStatus values."""
        for status_enum in (TaskStatus.STARTED, TaskStatus.SUCCESS, TaskStatus.FAILURE):
            row = await TaskiqResultModel.create(
                **_make_serializer_row_kwargs(
                    f"serializer-test-{status_enum.name}", status_enum
                )
            )
            ser = TaskiqResultSerializer.from_instance(row)
            assert ser.model_dump()["status"] == status_enum
            await row.delete()

    @pytest.mark.asyncio
    async def test_return_value_from_db_column(self) -> None:
        """Serializer exposes return_value JSON column."""
        kwargs = _make_serializer_row_kwargs("serializer-rv-col", TaskStatus.SUCCESS)
        kwargs["return_value"] = {"x": 1}
        row = await TaskiqResultModel.create(**kwargs)
        ser = TaskiqResultSerializer.from_instance(row)
        assert ser.model_dump()["return_value"] == {"x": 1}
        await row.delete()


class TestAppConfig:
    @pytest.mark.asyncio
    async def test_ready(self, unfazed: Unfazed) -> None:
        """Test AppConfig.ready() completes without error."""
        config = AppConfig(unfazed, "unfazed_taskiq.contrib.result.app")
        await config.ready()
