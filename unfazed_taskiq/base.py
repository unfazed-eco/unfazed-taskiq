from taskiq import AsyncBroker, AsyncResultBackend, TaskiqScheduler
from unfazed.utils import import_string

from .settings import UnfazedTaskiqSettings


class TaskiqAgent:
    def __init__(self) -> None:
        self._broker: AsyncBroker = None
        self._result: AsyncResultBackend = None
        self._scheduler: TaskiqScheduler = None

    @property
    def broker(self) -> AsyncBroker:
        return self._broker

    @property
    def result(self) -> AsyncResultBackend:
        return self._result

    @property
    def scheduler(self) -> TaskiqScheduler:
        return self._scheduler

    def setup(self, taskiq_settings: UnfazedTaskiqSettings) -> None:
        # setup broker
        broker_cls = import_string(taskiq_settings.broker.backend)
        broker_options = taskiq_settings.broker.options

        self._broker = broker_cls(**broker_options)

        # setup result backend
        if taskiq_settings.result:
            result_cls = import_string(taskiq_settings.result.backend)
            result_options = taskiq_settings.result.options

            self._result = result_cls(**result_options)

        # setup scheduler
        if taskiq_settings.scheduler:
            scheduler_cls = import_string(taskiq_settings.scheduler.backend)
            scheduler_options = taskiq_settings.scheduler.options

            self._scheduler = scheduler_cls(**scheduler_options)


agent = TaskiqAgent()
