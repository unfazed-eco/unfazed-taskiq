from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from taskiq import AsyncBroker, ScheduleSource, TaskiqEvents, TaskiqScheduler

from unfazed_taskiq.agent.model import TaskiqAgent
from unfazed_taskiq.settings import Broker, Result, Scheduler, TaskiqConfig


class TestTaskiqAgent:
    def _build_config(self):
        return TaskiqConfig(
            BROKER=Broker(
                BACKEND="tests.doubles.FakeBroker",
                OPTIONS={"foo": "bar"},
                MIDDLEWARES=[
                    "tests.doubles.MiddlewareA",
                    "tests.doubles.MiddlewareB",
                    "",
                ],
                HANDLERS=[
                    {
                        "handler": "tests.doubles.EventHandler",
                        "event": TaskiqEvents.WORKER_STARTUP.value,
                    },
                    {
                        "handler": "tests.doubles.EventHandler",
                        "event": TaskiqEvents.CLIENT_STARTUP,
                    },
                ],
            ),
            RESULT=Result(BACKEND="tests.doubles.ResultBackend", OPTIONS={"ttl": 5}),
            SCHEDULER=Scheduler(
                BACKEND="tests.doubles.SchedulerBackend",
                SOURCES=[
                    "tests.doubles.SourceFactory",
                    "tests.doubles.BoundSource",
                ],
            ),
        )

    @pytest.fixture(autouse=True)
    def doubles(self, monkeypatch):
        class FakeBroker(AsyncBroker):
            def __init__(self, **kwargs):
                super().__init__()
                self.kwargs = kwargs
                self.middlewares_mock = MagicMock()
                self.handlers_mock = MagicMock()
                self.result_backend_mock = MagicMock()
                self.startup_mock = AsyncMock()
                self.shutdown_mock = AsyncMock()

            def add_middlewares(self, middleware):
                self.middlewares_mock(middleware)

            def add_event_handler(self, event, handler):
                self.handlers_mock(event, handler)

            async def kick(self) -> None:
                pass

            async def listen(self) -> None:
                pass

            async def startup(self) -> None:
                await self.startup_mock()

            async def shutdown(self) -> None:
                await self.shutdown_mock()

            def with_result_backend(self, backend):
                self.result_backend_mock(backend)

        class MiddlewareA:
            def __call__(self):
                return "middleware-A"

        class MiddlewareB:
            def __call__(self):
                return "middleware-B"

        class EventHandler:
            pass

        class ResultBackend:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class SchedulerBackend(TaskiqScheduler):
            def __init__(self, broker: Any, sources: list[Any]) -> None:
                self.startup_mock = AsyncMock()
                self.shutdown_mock = AsyncMock()
                self.run_mock = AsyncMock()
                super().__init__(broker, sources)

            async def add_task(self, task: Any) -> None:
                pass

            async def remove_task(self, task: Any) -> None:
                pass

            async def run(self) -> None:
                await self.run_mock()

            async def startup(self) -> None:
                await self.startup_mock()

            async def shutdown(self) -> None:
                await self.shutdown_mock()

        class SourceFactory:
            def __init__(self, broker):
                self.source = f"source-{id(broker)}"

        class BoundSource(ScheduleSource):
            def __init__(self, broker: Any) -> None:
                self.broker = broker

            async def get_schedules(self):
                return []

        monkeypatch.setattr(
            "unfazed_taskiq.agent.model.import_string",
            lambda path: {
                "tests.doubles.FakeBroker": FakeBroker,
                "tests.doubles.MiddlewareA": MiddlewareA,
                "tests.doubles.MiddlewareB": MiddlewareB,
                "tests.doubles.EventHandler": EventHandler,
                "tests.doubles.ResultBackend": ResultBackend,
                "tests.doubles.SchedulerBackend": SchedulerBackend,
                "tests.doubles.SourceFactory": SourceFactory,
                "tests.doubles.BoundSource": BoundSource,
            }[path],
        )

        self.fake_classes = {
            "broker": FakeBroker,
            "scheduler": SchedulerBackend,
        }

    def test_setup_full_configuration(self):
        config = self._build_config()
        agent = TaskiqAgent.setup("alias", config)

        assert agent.alias_name == "alias"
        assert agent.config is config
        broker = agent.broker
        assert isinstance(broker, self.fake_classes["broker"])
        middleware_calls = [
            call.args[0] for call in broker.middlewares_mock.call_args_list
        ]
        assert middleware_calls[0].__class__.__name__ == "MiddlewareA"
        assert middleware_calls[1].__class__.__name__ == "MiddlewareB"
        calls = broker.handlers_mock.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0].value == "WORKER_STARTUP"
        assert calls[1][0][0] == TaskiqEvents.CLIENT_STARTUP
        broker.result_backend_mock.assert_called_once()
        scheduler = agent.scheduler
        assert isinstance(scheduler, self.fake_classes["scheduler"])
        assert scheduler.broker is broker
        assert len(scheduler.sources) == 2
        assert hasattr(scheduler.sources[0], "source")
        assert isinstance(scheduler.sources[1], ScheduleSource)

    def test_setup_without_optional_sections(self, monkeypatch):
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=None,
        )
        agent = TaskiqAgent.setup("alias", config)
        assert agent.scheduler is None
        assert isinstance(agent.broker, self.fake_classes["broker"])
        agent.broker.result_backend_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_startup_and_shutdown(self):
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=Scheduler(BACKEND="tests.doubles.SchedulerBackend", SOURCES=[]),
        )
        agent = TaskiqAgent.setup("alias", config)

        await agent.startup()
        agent.scheduler.startup_mock.assert_awaited_once()
        agent.broker.startup_mock.assert_awaited_once()

        await agent.shutdown()
        agent.scheduler.shutdown_mock.assert_awaited_once()
        agent.broker.shutdown_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lifecycle_without_scheduler(self):
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=None,
        )
        agent = TaskiqAgent.setup("alias", config)

        await agent.startup()
        agent.broker.startup_mock.assert_awaited_once()

        await agent.shutdown()
        agent.broker.shutdown_mock.assert_awaited_once()
