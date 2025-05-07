import typing as t

from taskiq import AsyncBroker, TaskiqScheduler
from taskiq.abc.schedule_source import ScheduleSource
from unfazed.conf import settings
from unfazed.utils import import_string

from .settings import UnfazedTaskiqSettings


class TaskiqAgent:
    def __init__(self) -> None:
        self._broker: t.Optional[AsyncBroker] = None
        self._scheduler: t.Optional[TaskiqScheduler] = None

        self._ready = False

    @property
    def broker(self) -> AsyncBroker:
        self.check_ready()
        return t.cast(AsyncBroker, self._broker)

    @property
    def scheduler(self) -> t.Optional[TaskiqScheduler]:
        self.check_ready()
        return self._scheduler

    def check_ready(self) -> None:
        if not self._ready:
            self.setup_from_property()

    def reset(self) -> None:
        self._broker = None
        self._scheduler = None
        self._ready = False

    def setup_from_property(self) -> None:
        taskiq_settings: UnfazedTaskiqSettings = settings["UNFAZED_TASKIQ_SETTINGS"]
        self.setup(taskiq_settings)

    def setup(self, taskiq_settings: UnfazedTaskiqSettings) -> None:
        if self._ready:
            return
        # setup broker
        broker_cls = import_string(taskiq_settings.broker.backend)
        broker_options = taskiq_settings.broker.options

        self._broker = t.cast(AsyncBroker, broker_cls(**broker_options))

        # setup result backend
        if taskiq_settings.result:
            result_cls = import_string(taskiq_settings.result.backend)
            result_options = taskiq_settings.result.options
            self._broker.with_result_backend(result_cls(**result_options))

        # setup scheduler
        if taskiq_settings.scheduler:
            scheduler_cls: t.Type[TaskiqScheduler] = import_string(
                taskiq_settings.scheduler.backend
            )
            scheduler_sources_cls = taskiq_settings.scheduler.sources_cls or []

            sources: t.List[ScheduleSource] = []
            source_cls: t.Type[ScheduleSource]
            for source_cls_str in scheduler_sources_cls:
                source_cls = import_string(source_cls_str)

                sources.append(source_cls(self._broker))  # type: ignore

            self._scheduler = scheduler_cls(self._broker, sources)
        else:
            self._scheduler = None

        self._ready = True

    async def startup(self) -> None:
        await self.broker.startup()
        if isinstance(self.scheduler, TaskiqScheduler):
            await self.scheduler.startup()

    async def shutdown(self) -> None:
        await self.broker.shutdown()
        if isinstance(self.scheduler, TaskiqScheduler):
            await self.scheduler.shutdown()


agent = TaskiqAgent()
