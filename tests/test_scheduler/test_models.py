import json
from typing import Optional

from taskiq import ScheduledTask

from unfazed_taskiq.contrib.scheduler.models import PeriodicTask
from unfazed_taskiq.contrib.scheduler.serializer import PeriodicTaskSerializer


class TestPeriodicTaskModel(object):
    async def test_periodic_task_model(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        assert test_scheduler_sample_data is not None
        assert len(test_scheduler_sample_data) == 4

        db_data = await PeriodicTask.filter().all()

        assert len(db_data) == 4

        db_task_names = {item.task_name for item in db_data}
        sample_task_names = {item["task_name"] for item in test_scheduler_sample_data}
        assert db_task_names == sample_task_names

        db_task_corns = {item.cron for item in db_data}
        sample_task_corns = {item["cron"] for item in test_scheduler_sample_data}
        assert db_task_corns == sample_task_corns

        db_task_kwargs = {item.task_kwargs for item in db_data}
        sample_task_kwargs = {
            item["task_kwargs"] for item in test_scheduler_sample_data
        }
        assert db_task_kwargs == sample_task_kwargs

        db_task_schedule_aliases = {item.schedule_alias for item in db_data}
        sample_task_schedule_aliases = {
            item["schedule_alias"] for item in test_scheduler_sample_data
        }
        assert db_task_schedule_aliases == sample_task_schedule_aliases

    async def test_periodic_task_model_to_taskiq_schedule_task(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        assert test_scheduler_sample_data is not None
        assert len(test_scheduler_sample_data) == 4

        for item in test_scheduler_sample_data:
            pt_objs: Optional[PeriodicTask] = await PeriodicTask.filter(
                task_name=item["task_name"]
            ).first()
            assert pt_objs is not None
            schedule_data: ScheduledTask = pt_objs.to_taskiq_schedule_task()
            assert schedule_data.cron == item["cron"]
            assert schedule_data.task_name == item["task_name"]
            assert schedule_data.args == json.loads(item["task_args"])
            assert schedule_data.kwargs == json.loads(item["task_kwargs"])
            assert schedule_data.labels == json.loads(item["labels"])
            assert schedule_data.schedule_id == item["schedule_id"]

    async def test_periodic_task_model_to_taskiq_schedule_task_with_time(self) -> None:
        """Test to_taskiq_schedule_task method with time-based scheduling."""
        from datetime import datetime, timezone

        # Create a PeriodicTask with time-based scheduling (no cron)
        task_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        periodic_task = await PeriodicTask.create(
            task_name="test.time_task",
            task_args="[]",
            task_kwargs="{}",
            labels="{}",
            time=task_time,  # Set time instead of cron
            cron=None,  # Explicitly set cron to None
        )

        # Test the conversion
        scheduled_task = periodic_task.to_taskiq_schedule_task()

        # Verify the scheduled task properties
        assert scheduled_task.task_name == "test.time_task"
        assert scheduled_task.args == []
        assert scheduled_task.kwargs == {}
        assert scheduled_task.labels == {}
        assert scheduled_task.time == task_time
        assert scheduled_task.cron is None
        assert scheduled_task.schedule_id == periodic_task.schedule_id

    async def test_periodic_task_model_to_taskiq_schedule_task_no_schedule_error(
        self,
    ) -> None:
        """Test to_taskiq_schedule_task method raises RuntimeError when no schedule is found."""
        import pytest

        # Create a PeriodicTask with neither cron nor time
        periodic_task = await PeriodicTask.create(
            task_name="test.no_schedule_task",
            task_args="[]",
            task_kwargs="{}",
            labels="{}",
            cron=None,
            time=None,
        )

        # Test that RuntimeError is raised
        with pytest.raises(RuntimeError, match="No schedule found"):
            periodic_task.to_taskiq_schedule_task()


class TestPeriodicTaskSerializer(object):
    async def test_periodic_task_serializer(
        self, test_scheduler_sample_data: list[dict]
    ) -> None:
        assert test_scheduler_sample_data is not None
        assert len(test_scheduler_sample_data) == 4

        result = await PeriodicTaskSerializer.list(
            PeriodicTask.filter(), page=1, size=2
        )
        assert result is not None
        assert len(result.data) == 2
