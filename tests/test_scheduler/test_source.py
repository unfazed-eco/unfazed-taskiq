import json
import uuid
from typing import Optional

from taskiq import ScheduledTask
from tortoise import Tortoise

from unfazed_taskiq.contrib.scheduler.models import PeriodicTask
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource


def test_startup_handler() -> None:
    pass


async def test_async_startup_handler() -> None:
    pass


def test_shutdown_handler() -> None:
    pass


async def test_async_shutdown_handler() -> None:
    pass


class TestTortoiseScheduleSource(object):
    async def test_tortoise_schedule_source_init(self) -> None:
        """Test TortoiseScheduleSource initialization."""
        source = TortoiseScheduleSource(schedule_alias="test_task3")
        assert source is not None
        assert source.schedule_alias == "test_task3"
        assert source._alias == "default"
        assert source.startup_handlers == []
        assert source.shutdown_handlers == []

    async def test_tortoise_schedule_source_startup(self) -> None:
        """Test TortoiseScheduleSource startup."""
        source = TortoiseScheduleSource(
            schedule_alias="test_task3",
            startup_handlers=[
                "tests.test_scheduler.test_source.test_startup_handler",
                "tests.test_scheduler.test_source.test_async_startup_handler",
            ],
        )
        await source.startup()
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

    async def test_tortoise_schedule_source_shutdown(self) -> None:
        """Test TortoiseScheduleSource shutdown."""
        source = TortoiseScheduleSource(
            schedule_alias="test_task3",
            shutdown_handlers=[
                "tests.test_scheduler.test_source.test_shutdown_handler",
                "tests.test_scheduler.test_source.test_async_shutdown_handler",
            ],
        )
        await source.startup()
        await source.shutdown()
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

    async def test_tortoise_schedule_source_get_schedules(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        """Test TortoiseScheduleSource get schedules."""
        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()

        assert len(test_scheduler_sample_data) == 4

        simple_data = list(
            filter(
                lambda x: x["schedule_alias"] == "test_schedule3",
                test_scheduler_sample_data,
            )
        )
        schedules = await source.get_schedules()

        assert len(schedules) == 1
        assert schedules[0].task_name == simple_data[0]["task_name"]
        assert schedules[0].args == json.loads(simple_data[0]["task_args"])
        assert schedules[0].kwargs == json.loads(simple_data[0]["task_kwargs"])
        assert schedules[0].labels == json.loads(simple_data[0]["labels"])
        assert schedules[0].schedule_id == simple_data[0]["schedule_id"]

    async def test_tortoise_schedule_source_add_schedule(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        """Test TortoiseScheduleSource add schedule."""
        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()
        s_task = ScheduledTask(
            task_name=test_scheduler_sample_data[0]["task_name"],
            args=json.loads(test_scheduler_sample_data[0]["task_args"]),
            kwargs=json.loads(test_scheduler_sample_data[0]["task_kwargs"]),
            labels=json.loads(test_scheduler_sample_data[0]["labels"]),
            schedule_id=str(uuid.uuid4().hex),
            cron=test_scheduler_sample_data[0]["cron"],
        )
        await source.add_schedule(s_task)
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

        schedules = await source.get_schedules()
        assert len(schedules) == 2

    async def test_tortoise_schedule_source_delete_schedule(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        """Test TortoiseScheduleSource delete schedule."""
        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()

        result_scheduler = list(
            filter(
                lambda x: x["schedule_alias"] == "test_schedule3",
                test_scheduler_sample_data,
            )
        )
        await source.delete_schedule(result_scheduler[0]["schedule_id"])
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

        schedules = await source.get_schedules()
        assert len(schedules) == 0

    async def test_tortoise_schedule_source_pre_send(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        """Test TortoiseScheduleSource pre send."""
        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()
        result_scheduler = list(
            filter(
                lambda x: x["schedule_alias"] == "test_schedule3",
                test_scheduler_sample_data,
            )
        )
        s_task = ScheduledTask(
            task_name=result_scheduler[0]["task_name"],
            args=json.loads(result_scheduler[0]["task_args"]),
            kwargs=json.loads(result_scheduler[0]["task_kwargs"]),
            labels=json.loads(result_scheduler[0]["labels"]),
            schedule_id=result_scheduler[0]["schedule_id"],
            cron=result_scheduler[0]["cron"],
        )
        origin_db_data = await PeriodicTask.filter(
            schedule_id=s_task.schedule_id
        ).first()

        await source.pre_send(s_task)
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

        db_data: Optional[PeriodicTask] = await PeriodicTask.filter(
            schedule_id=s_task.schedule_id
        ).first()
        assert db_data is not None
        assert origin_db_data.last_run_at != db_data.last_run_at  # type: ignore

    async def test_tortoise_schedule_source_post_send(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        """Test TortoiseScheduleSource post send."""
        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()
        result_scheduler = list(
            filter(
                lambda x: x["schedule_alias"] == "test_schedule3",
                test_scheduler_sample_data,
            )
        )
        s_task = ScheduledTask(
            task_name=result_scheduler[0]["task_name"],
            args=json.loads(result_scheduler[0]["task_args"]),
            kwargs=json.loads(result_scheduler[0]["task_kwargs"]),
            labels=json.loads(result_scheduler[0]["labels"]),
            schedule_id=result_scheduler[0]["schedule_id"],
            cron=result_scheduler[0]["cron"],
        )

        origin_db_data: Optional[PeriodicTask] = await PeriodicTask.filter(
            schedule_id=s_task.schedule_id
        ).first()
        assert origin_db_data is not None

        await source.post_send(s_task)
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

        db_data: Optional[PeriodicTask] = await PeriodicTask.filter(
            schedule_id=s_task.schedule_id
        ).first()
        assert db_data is not None
        assert origin_db_data.total_run_count + 1 == db_data.total_run_count


class TestTortoiseScheduleSourceErrors(object):
    """Test error conditions in TortoiseScheduleSource."""

    def test_tortoise_schedule_source_init_no_database_settings(self) -> None:
        """Test TortoiseScheduleSource initialization with no DATABASE settings."""
        from unittest.mock import MagicMock, patch

        import pytest

        # Mock settings to have no DATABASE configuration
        mock_unfazed_settings = MagicMock()
        mock_unfazed_settings.DATABASE = None

        with patch(
            "unfazed_taskiq.contrib.scheduler.sources.settings"
        ) as mock_settings_obj:
            mock_settings_obj.__getitem__.return_value = mock_unfazed_settings

            with pytest.raises(
                RuntimeError, match="DATABASE is not set in UNFAZED_SETTINGS"
            ):
                TortoiseScheduleSource()

    def test_tortoise_schedule_source_init_invalid_db_alias(self) -> None:
        """Test TortoiseScheduleSource initialization with invalid db_alias."""
        from unittest.mock import MagicMock, patch

        import pytest

        # Mock settings with DATABASE but without the requested alias
        mock_database = MagicMock()
        mock_database.connections = {"default": "some_connection"}  # Only has 'default'

        mock_unfazed_settings = MagicMock()
        mock_unfazed_settings.DATABASE = mock_database

        with patch(
            "unfazed_taskiq.contrib.scheduler.sources.settings"
        ) as mock_settings_obj:
            mock_settings_obj.__getitem__.return_value = mock_unfazed_settings

            with pytest.raises(
                RuntimeError, match="Database connection invalid_alias not found"
            ):
                TortoiseScheduleSource(db_alias="invalid_alias")

    async def test_tortoise_schedule_source_startup_tortoise_not_initialized(
        self,
    ) -> None:
        """Test TortoiseScheduleSource startup when Tortoise is not initialized."""
        from unittest.mock import patch

        import pytest

        source = TortoiseScheduleSource(schedule_alias="test")

        # Mock Tortoise._inited to be False
        with patch(
            "unfazed_taskiq.contrib.scheduler.sources.Tortoise"
        ) as mock_tortoise:
            mock_tortoise._inited = False

            with pytest.raises(RuntimeError, match="Tortoise is not initialized"):
                await source.startup()

    async def test_tortoise_schedule_source_add_schedule_duplicate_error(self) -> None:
        """Test TortoiseScheduleSource add_schedule with duplicate schedule_id."""
        import uuid

        import pytest

        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()

        # First create a task to ensure we have something to duplicate
        original_schedule_id = str(uuid.uuid4().hex)
        original_task = ScheduledTask(
            task_name="test.original_task",
            args=[],
            kwargs={},
            labels={},
            schedule_id=original_schedule_id,
            cron="0 0 * * *",
        )
        await source.add_schedule(original_task)

        # Now try to create a duplicate with the same schedule_id
        duplicate_task = ScheduledTask(
            task_name="test.duplicate_task",
            args=[],
            kwargs={},
            labels={},
            schedule_id=original_schedule_id,  # Use same schedule_id
            cron="0 1 * * *",
        )

        with pytest.raises(
            RuntimeError, match=f"Schedule {original_schedule_id} already exists"
        ):
            await source.add_schedule(duplicate_task)

    async def test_tortoise_schedule_source_add_schedule_with_time(self) -> None:
        """Test TortoiseScheduleSource add_schedule with time-based scheduling."""
        import uuid
        from datetime import datetime, timezone

        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()

        # Create a schedule task with time instead of cron
        task_time = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        time_task = ScheduledTask(
            task_name="test.time_based_task",
            args=[1, 2, 3],
            kwargs={"key": "value"},
            labels={"env": "test"},
            schedule_id=str(uuid.uuid4().hex),
            time=task_time,  # Use time instead of cron
        )

        await source.add_schedule(time_task)

        # Verify the task was added correctly
        added_task = await PeriodicTask.filter(
            schedule_id=time_task.schedule_id
        ).first()
        assert added_task is not None
        assert added_task.task_name == "test.time_based_task"
        assert added_task.time == task_time
        assert added_task.cron is None

    async def test_tortoise_schedule_source_add_schedule_no_schedule_error(
        self,
    ) -> None:
        """Test TortoiseScheduleSource add_schedule with no cron or time."""
        import uuid
        from unittest.mock import MagicMock

        import pytest

        source = TortoiseScheduleSource(schedule_alias="test_schedule3")
        await source.startup()

        # Create a mock ScheduledTask that bypasses Pydantic validation
        # to test the RuntimeError in add_schedule method
        mock_task = MagicMock()
        mock_task.task_name = "test.no_schedule_task"
        mock_task.args = []
        mock_task.kwargs = {}
        mock_task.labels = {}
        mock_task.schedule_id = str(uuid.uuid4().hex)
        mock_task.cron = None
        mock_task.time = None

        with pytest.raises(RuntimeError, match="No schedule found"):
            await source.add_schedule(mock_task)
