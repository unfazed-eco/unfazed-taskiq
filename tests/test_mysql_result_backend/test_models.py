"""Tests for result_backend models and app."""

import pytest
from unfazed.core import Unfazed

from unfazed_taskiq.contrib.result_backend.app import AppConfig
from unfazed_taskiq.contrib.result_backend.models import TaskiqResultModel, TaskStatus
from unfazed_taskiq.contrib.result_backend.serializer import TaskiqResultSerializer


class TestTaskStatus:
    def test_label_property(self) -> None:
        """Test TaskStatus.label returns enum name."""
        assert TaskStatus.STARTED.label == "STARTED"
        assert TaskStatus.SUCCESS.label == "SUCCESS"
        assert TaskStatus.FAILURE.label == "FAILURE"


def _make_serializer_row_kwargs(task_id: str, status: TaskStatus) -> dict:
    """Build kwargs for TaskiqResultModel.create that satisfy serializer validation."""
    return {
        "task_id": task_id,
        "status": int(status),
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
    async def test_status_serialized_as_name(self) -> None:
        """Test serializer converts status int to TaskStatus name."""
        row = await TaskiqResultModel.create(
            **_make_serializer_row_kwargs("serializer-test-001", TaskStatus.SUCCESS)
        )
        ser = TaskiqResultSerializer.from_instance(row)
        dumped = ser.model_dump()
        assert dumped["status"] == "SUCCESS"
        await row.delete()

    @pytest.mark.asyncio
    async def test_status_all_values_serialized_as_name(self) -> None:
        """Test all TaskStatus values serialize to name."""
        for status_enum in (TaskStatus.STARTED, TaskStatus.SUCCESS, TaskStatus.FAILURE):
            row = await TaskiqResultModel.create(
                **_make_serializer_row_kwargs(
                    f"serializer-test-{status_enum.name}", status_enum
                )
            )
            ser = TaskiqResultSerializer.from_instance(row)
            assert ser.model_dump()["status"] == status_enum.name
            await row.delete()


class TestAppConfig:
    @pytest.mark.asyncio
    async def test_ready(self, unfazed: Unfazed) -> None:
        """Test AppConfig.ready() completes without error."""
        config = AppConfig(unfazed, "unfazed_taskiq.contrib.result_backend.app")
        await config.ready()
