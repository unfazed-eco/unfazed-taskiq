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
