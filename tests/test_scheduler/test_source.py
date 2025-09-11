from datetime import datetime
import json
import uuid
from taskiq import ScheduledTask
from tortoise import Tortoise
from unfazed_taskiq.contrib.scheduler.models import PeriodicTask
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource


def test_startup_handler():
    pass


async def test_async_startup_handler():
    pass


def test_shutdown_handler():
    pass


async def test_async_shutdown_handler():
    pass


class TestTortoiseScheduleSource(object):
    async def test_tortoise_schedule_source_init(self):
        """Test TortoiseScheduleSource initialization."""
        source = TortoiseScheduleSource(schedule_alias="test_task3")
        assert source is not None
        assert source.schedule_alias == "test_task3"
        assert source._alias == "default"
        assert source.startup_handlers == []
        assert source.shutdown_handlers == []

    async def test_tortoise_schedule_source_startup(self):
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

    async def test_tortoise_schedule_source_shutdown(self):
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
        self, test_scheduler_sample_data
    ):
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
        self, test_scheduler_sample_data
    ):
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
        self, test_scheduler_sample_data
    ):
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

    async def test_tortoise_schedule_source_pre_send(self, test_scheduler_sample_data):
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

        db_data = await PeriodicTask.filter(schedule_id=s_task.schedule_id).first()
        assert origin_db_data.last_run_at != db_data.last_run_at

    async def test_tortoise_schedule_source_post_send(self, test_scheduler_sample_data):
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

        origin_db_data = await PeriodicTask.filter(
            schedule_id=s_task.schedule_id
        ).first()

        await source.post_send(s_task)
        assert source.alias is not None
        assert source.alias == Tortoise.get_connection("default")

        db_data = await PeriodicTask.filter(schedule_id=s_task.schedule_id).first()
        assert origin_db_data.total_run_count + 1 == db_data.total_run_count
