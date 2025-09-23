import typing as t

from taskiq import AsyncBroker, ScheduleSource, TaskiqScheduler
from taskiq.events import TaskiqEvents
from unfazed.conf import settings
from unfazed.utils import import_string

from .settings import TaskiqConfig, UnfazedTaskiqSettings


class TaskiqAgent:
    def __init__(self) -> None:
        self._brokers: t.Dict[str, AsyncBroker] = {}
        self._schedulers: t.Dict[str, TaskiqScheduler] = {}
        self._ready = False
        self._default_taskiq_name: t.Optional[str] = None
        self._taskiq_configs: t.Dict[str, TaskiqConfig] = {}

    def get_broker(self, broker_name: t.Optional[str] = None) -> AsyncBroker:
        self.check_ready()
        if broker_name is None:
            if self._default_taskiq_name is None:
                raise ValueError("No found broker name configured")
            broker_name = self._default_taskiq_name

        broker = self._brokers.get(broker_name)
        if broker is None:
            raise ValueError(f"Broker '{broker_name}' not found")
        return broker

    def get_scheduler(self, scheduler_name: t.Optional[str] = None) -> TaskiqScheduler:
        self.check_ready()
        if scheduler_name is None:
            if self._default_taskiq_name is None:
                raise ValueError("No found scheduler name configured")
            scheduler_name = self._default_taskiq_name

        scheduler = self._schedulers.get(scheduler_name)
        if scheduler is None:
            raise ValueError(f"Scheduler '{scheduler_name}' not found")
        return scheduler

    def check_ready(self) -> None:
        if not self._ready:
            self.setup_from_property()

    def reset(self) -> None:
        self._brokers.clear()
        self._schedulers.clear()
        self._ready = False

    def setup_from_property(self) -> None:
        taskiq_settings: UnfazedTaskiqSettings = settings["UNFAZED_TASKIQ_SETTINGS"]
        self.setup(taskiq_settings)

    def setup(self, taskiq_settings: UnfazedTaskiqSettings) -> None:
        if self._ready:
            return

        self._default_taskiq_name = taskiq_settings.default_taskiq_name
        self._taskiq_configs = taskiq_settings.taskiq_config

        if taskiq_settings.taskiq_config:
            self._setup_queue_configs(taskiq_settings.taskiq_config)
        else:
            raise ValueError(
                "No taskiq configurations found. Please configure TASKIQ_CONFIG."
            )

        self._ready = True

    def _setup_queue_configs(self, taskiq_configs: t.Dict[str, TaskiqConfig]) -> None:
        for queue_name, queue_config in taskiq_configs.items():
            broker_cls = import_string(queue_config.broker.backend)
            broker_options = queue_config.broker.options or {}
            broker: AsyncBroker = broker_cls(**broker_options)

            for middleware_path in queue_config.broker.middlewares:
                middleware_cls = import_string(middleware_path)
                middleware = middleware_cls()
                broker.add_middlewares(middleware)

            for handler in queue_config.broker.handlers:
                handler_cls = import_string(handler["handler"])
                event = handler["event"]
                if isinstance(event, str):
                    event = TaskiqEvents(event)
                broker.add_event_handler(event, handler_cls)

            if queue_config.result:
                result_cls = import_string(queue_config.result.backend)
                result_options = queue_config.result.options or {}
                broker.with_result_backend(result_cls(**result_options))

            self._brokers[queue_name] = broker

            if queue_config.scheduler:
                scheduler_cls = import_string(queue_config.scheduler.backend)
                scheduler_sources = queue_config.scheduler.sources or []

                sources: t.List[ScheduleSource] = []
                for source in scheduler_sources:
                    if isinstance(source, ScheduleSource):
                        sources.append(source)
                    else:
                        source_cls = import_string(source)
                        sources.append(source_cls(broker))

                scheduler = scheduler_cls(broker=broker, sources=sources)
                self._schedulers[queue_name] = scheduler

    async def startup(self) -> None:
        # Start schedulers first (they will start their associated brokers)
        for scheduler in self._schedulers.values():
            if not isinstance(scheduler, TaskiqScheduler):
                continue
            await scheduler.startup()

        # Start brokers that don't have schedulers
        for broker_name, broker in self._brokers.items():
            if broker_name not in self._schedulers:
                await broker.startup()

    async def shutdown(self) -> None:
        # Shutdown schedulers first (they will shutdown their associated brokers)
        for scheduler in self._schedulers.values():
            if not isinstance(scheduler, TaskiqScheduler):
                continue
            await scheduler.shutdown()

        # Shutdown brokers that don't have schedulers
        for broker_name, broker in self._brokers.items():
            if broker_name not in self._schedulers:
                await broker.shutdown()


agent = TaskiqAgent()
