import typing as t
from datetime import datetime

import orjson as json
from taskiq import ScheduledTask, ScheduleSource
from taskiq.abc.serializer import TaskiqSerializer
from taskiq.utils import maybe_awaitable
from tortoise import BaseDBAsyncClient, Tortoise
from tortoise.expressions import F
from unfazed.conf import UnfazedSettings, settings
from unfazed.utils import import_string

from unfazed_taskiq.contrib.scheduler import models as m
from unfazed_taskiq.logger import log


class TortoiseScheduleSource(ScheduleSource):
    def __init__(
        self,
        db_alias: str = "default",
        schedule_alias: str = "default",
        startup_handlers: t.List[str] = [],
        shutdown_handlers: t.List[str] = [],
        serializer: t.Optional[TaskiqSerializer] = None,
    ) -> None:
        """
        Initialize the TortoiseScheduleSource.

        :param db_alias: The alias of the database connection to use.
        :param schedule_alias: The alias of the schedule to use.
        :param startup_handlers: A list of handlers to execute during startup.
        :param shutdown_handlers: A list of handlers to execute during shutdown.
        :param serializer: The serializer to use.
        """
        unfazed_settings: UnfazedSettings = settings["UNFAZED_SETTINGS"]

        if unfazed_settings.DATABASE is None:
            raise RuntimeError("DATABASE is not set in UNFAZED_SETTINGS")

        if db_alias not in unfazed_settings.DATABASE.connections:
            raise RuntimeError(f"Database connection {db_alias} not found")
        self._alias: str = db_alias
        self.schedule_alias: str = schedule_alias
        self.startup_handlers: t.List[str] = startup_handlers
        self.shutdown_handlers: t.List[str] = shutdown_handlers

    async def startup(self) -> None:
        """Action to execute during startup."""
        for handler in self.startup_handlers:
            handler_cls = import_string(handler)
            await maybe_awaitable(handler_cls())

        if not Tortoise._inited:
            raise RuntimeError("Tortoise is not initialized")

        self.alias: BaseDBAsyncClient = Tortoise.get_connection(self._alias)

        log.info("TortoiseScheduleSource startup")

    async def shutdown(self) -> None:
        """Actions to execute during shutdown."""
        for handler in self.shutdown_handlers:
            handler_cls = import_string(handler)
            await maybe_awaitable(handler_cls())

        log.info("MysqlScheduleSource shutdown")

    async def get_schedules(self) -> t.List["ScheduledTask"]:
        """Get list of taskiq schedules."""

        schedules = await m.PeriodicTask.filter(
            enabled=1, schedule_alias=self.schedule_alias
        ).using_db(self.alias)
        return [schedule.to_taskiq_schedule_task() for schedule in schedules]

    async def add_schedule(
        self,
        schedule: "ScheduledTask",
    ) -> None:
        """
        Add a new schedule.

        This function is used to add new schedules.
        It's a convenient helper for people who want to add new schedules
        for the current source.

        As an example, if your source works with a database,
        you may want to add new rows to the table.

        Note that this function may do nothing.

        :param schedule: schedule to add.
        """

        schedule_id = schedule.schedule_id

        if (
            await m.PeriodicTask.filter(schedule_id=schedule_id)
            .using_db(self.alias)
            .exists()
        ):
            raise RuntimeError(f"Schedule {schedule_id} already exists")

        pt = m.PeriodicTask(
            task_name=schedule.task_name,
            task_args=json.dumps(schedule.args).decode(),
            task_kwargs=json.dumps(schedule.kwargs).decode(),
            labels=json.dumps(schedule.labels).decode(),
            schedule_id=schedule_id,
            schedule_alias=self.schedule_alias,
        )

        if schedule.cron is not None:
            pt.cron = schedule.cron
        elif schedule.time is not None:
            pt.time = schedule.time
        else:
            raise RuntimeError("No schedule found")

        await pt.save(using_db=self.alias)

    async def delete_schedule(self, schedule_id: str) -> None:
        """
        Method to delete schedule by id.

        This is useful for schedule cancelation.

        :param schedule_id: id of schedule to delete.
        """

        await (
            m.PeriodicTask.filter(schedule_id=schedule_id)
            .using_db(self.alias)
            .update(enabled=0)
        )

    async def pre_send(  # type: ignore
        self, task: "ScheduledTask"
    ) -> t.Union[  # type: ignore
        None, "t.CoroutineType[t.Any, t.Any, None]", t.Coroutine[t.Any, t.Any, None]
    ]:
        """
        Actions to execute before task will be sent to broker.

        This method may raise ScheduledTaskCancelledError.
        This cancels the task execution.

        :param task: task that will be sent
        """
        await (
            m.PeriodicTask.filter(schedule_id=task.schedule_id)
            .using_db(self.alias)
            .update(last_run_at=datetime.now())
        )

    async def post_send(  # type: ignore
        self, task: "ScheduledTask"
    ) -> t.Union[  # type: ignore
        None, "t.CoroutineType[t.Any, t.Any, None]", t.Coroutine[t.Any, t.Any, None]
    ]:
        """
        Actions to execute after task was sent to broker.

        :param task: task that just have sent
        """

        await (
            m.PeriodicTask.filter(schedule_id=task.schedule_id)
            .using_db(self.alias)
            .update(total_run_count=F("total_run_count") + 1)
        )
