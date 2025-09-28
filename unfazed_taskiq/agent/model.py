from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from taskiq import AsyncBroker, ScheduleSource, TaskiqEvents, TaskiqScheduler
from unfazed.utils import import_string

from unfazed_taskiq.settings import TaskiqConfig


class TaskiqAgent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    alias_name: str
    broker: AsyncBroker
    scheduler: Optional[TaskiqScheduler]
    config: TaskiqConfig

    @classmethod
    def setup(cls, alias_name: str, config: TaskiqConfig) -> "TaskiqAgent":
        # setup broker
        broker_cls = import_string(config.broker.backend)
        broker_options = config.broker.options or {}
        broker: AsyncBroker = broker_cls(**broker_options)

        # setup middlewares
        for middleware_path in config.broker.middlewares:
            if middleware_path:  # Skip empty middleware paths
                middleware_cls = import_string(middleware_path)
                middleware = middleware_cls()
                broker.add_middlewares(middleware)

        # setup handlers
        for handler in config.broker.handlers:
            handler_cls = import_string(handler["handler"])
            event = handler["event"]
            if isinstance(event, str):
                event = TaskiqEvents(event)
            broker.add_event_handler(event, handler_cls)

        # setup result backend
        if config.result:
            result_cls = import_string(config.result.backend)
            result_options = config.result.options or {}
            broker.with_result_backend(result_cls(**result_options))

        # setup scheduler
        scheduler = None
        if config.scheduler:
            scheduler_cls: type[TaskiqScheduler] = import_string(
                config.scheduler.backend
            )
            scheduler_sources = config.scheduler.sources or []
            sources: List[ScheduleSource] = []
            for source in scheduler_sources:
                if isinstance(source, ScheduleSource):
                    sources.append(source)
                else:
                    source_cls = import_string(source)
                    sources.append(source_cls(broker))
            scheduler = scheduler_cls(broker=broker, sources=sources)

        return cls(
            alias_name=alias_name, broker=broker, scheduler=scheduler, config=config
        )

    async def startup(self) -> None:
        if self.scheduler and isinstance(self.scheduler, TaskiqScheduler):
            await self.scheduler.startup()
        await self.broker.startup()

    async def shutdown(self) -> None:
        if self.scheduler and isinstance(self.scheduler, TaskiqScheduler):
            await self.scheduler.shutdown()
        await self.broker.shutdown()
