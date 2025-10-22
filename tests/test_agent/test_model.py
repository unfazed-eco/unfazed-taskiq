import sys
from typing import Any, Awaitable, Callable, Iterable, List, Sequence
from unittest.mock import AsyncMock

import pytest
from taskiq import (
    AckableMessage,
    AsyncBroker,
    ScheduleSource,
    TaskiqEvents,
    TaskiqScheduler,
)
from taskiq.abc.middleware import TaskiqMiddleware
from taskiq.abc.result_backend import AsyncResultBackend
from taskiq.message import BrokerMessage
from taskiq.result import TaskiqResult
from taskiq.state import TaskiqState

from unfazed_taskiq.agent.model import TaskiqAgent
from unfazed_taskiq.settings import Broker, Result, Scheduler, TaskiqConfig


class SchedulerResult:
    def __init__(self) -> None:
        self.tasks: list[str] = []


class TestTaskiqAgent:
    def _build_config(self) -> TaskiqConfig:
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
    def doubles(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeResultBackend(AsyncResultBackend[Any]):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__()
                self.kwargs = kwargs
                self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

            async def set_result(self, task_id: str, result: TaskiqResult[Any]) -> None:
                self.calls.append(("set", (task_id, result), {}))

            async def is_result_ready(self, task_id: str) -> bool:
                self.calls.append(("ready", (task_id,), {}))
                return True

            async def get_result(
                self, task_id: str, with_logs: bool = False
            ) -> TaskiqResult[Any]:
                self.calls.append(("get", (task_id,), {"with_logs": with_logs}))
                return TaskiqResult(  # type: ignore
                    is_ok=True, return_value=None, execution_time=0, log=None
                )

        class FakeBroker(AsyncBroker):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__()
                self.kwargs = kwargs
                self.startup_mock: AsyncMock = AsyncMock()
                self.shutdown_mock: AsyncMock = AsyncMock()
                self.kick_mock: AsyncMock = AsyncMock()
                self.listen_result: Iterable[AckableMessage] = []

            async def kick(self, message: BrokerMessage) -> None:
                await self.kick_mock(message)

            async def listen(self) -> Iterable[AckableMessage]:  # type: ignore
                return self.listen_result

            async def startup(self) -> None:
                await self.startup_mock()
                await super().startup()

            async def shutdown(self) -> None:
                await self.shutdown_mock()
                await super().shutdown()

        class MiddlewareA(TaskiqMiddleware):
            async def pre_execute(self, message: BrokerMessage) -> BrokerMessage:  # type: ignore
                return message

        class MiddlewareB(TaskiqMiddleware):
            async def pre_execute(self, message: BrokerMessage) -> BrokerMessage:  # type: ignore
                return message

        class EventHandler:
            def __call__(self, state: TaskiqState) -> None:
                state.custom["called"] = True  # type: ignore[attr-defined]

        class SchedulerBackend(TaskiqScheduler):
            def __init__(
                self, broker: AsyncBroker, sources: Sequence[ScheduleSource]
            ) -> None:
                self.startup_mock: AsyncMock = AsyncMock()
                self.shutdown_mock: AsyncMock = AsyncMock()
                self.run_mock: AsyncMock = AsyncMock()
                super().__init__(broker, list(sources))

            async def add_task(self, task: Callable[..., Awaitable[None]]) -> None:
                self.run_mock(task)

            async def remove_task(self, task: Callable[..., Awaitable[None]]) -> None:
                self.run_mock(task)

            async def run(self) -> SchedulerResult:
                await self.run_mock()
                return SchedulerResult()

            async def startup(self) -> None:
                await self.startup_mock()

            async def shutdown(self) -> None:
                await self.shutdown_mock()

        class SourceFactory:
            def __init__(self, broker: AsyncBroker) -> None:
                self.broker = broker
                self.source = f"source-{id(broker)}"

        class BoundSource(ScheduleSource):
            def __init__(self, broker: AsyncBroker) -> None:
                self.broker = broker

            async def get_schedules(self) -> List[SchedulerResult]:  # type: ignore
                return []

        doubles_module = {
            "tests.doubles.FakeBroker": FakeBroker,
            "tests.doubles.MiddlewareA": MiddlewareA,
            "tests.doubles.MiddlewareB": MiddlewareB,
            "tests.doubles.EventHandler": EventHandler,
            "tests.doubles.ResultBackend": FakeResultBackend,
            "tests.doubles.SchedulerBackend": SchedulerBackend,
            "tests.doubles.SourceFactory": SourceFactory,
            "tests.doubles.BoundSource": BoundSource,
        }

        module = type(sys)("tests.doubles")
        for name, value in doubles_module.items():
            setattr(module, name.split(".")[-1], value)
        monkeypatch.setitem(sys.modules, "tests.doubles", module)

        def import_string_stub(path: str) -> Any:
            if path in doubles_module:
                return doubles_module[path]
            raise ImportError(path)

        monkeypatch.setattr(
            "unfazed_taskiq.agent.model.import_string", import_string_stub
        )

        self.fake_classes = {
            "broker": FakeBroker,
            "scheduler": SchedulerBackend,
            "result_backend": FakeResultBackend,
        }

    def test_setup_full_configuration(self) -> None:
        config = self._build_config()
        agent = TaskiqAgent.setup("alias", config)

        assert agent.alias_name == "alias"
        assert agent.config is config
        broker = agent.broker
        assert isinstance(broker, self.fake_classes["broker"])
        middleware_names = [
            middleware.__class__.__name__ for middleware in broker.middlewares
        ]
        assert middleware_names == ["MiddlewareA", "MiddlewareB"]
        assert broker.event_handlers[TaskiqEvents.WORKER_STARTUP]
        assert broker.event_handlers[TaskiqEvents.CLIENT_STARTUP]
        scheduler: TaskiqScheduler = agent.scheduler  # type: ignore
        assert isinstance(scheduler, self.fake_classes["scheduler"])
        assert scheduler.broker is broker
        assert len(scheduler.sources) == 2
        assert scheduler.sources[0].source.startswith("source-")  # type: ignore
        assert isinstance(scheduler.sources[1], ScheduleSource)

    def test_setup_without_optional_sections(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=None,
        )
        agent = TaskiqAgent.setup("alias", config)
        assert agent.scheduler is None
        assert isinstance(agent.broker, self.fake_classes["broker"])

    async def test_startup_and_shutdown(self) -> None:
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=Scheduler(BACKEND="tests.doubles.SchedulerBackend", SOURCES=[]),
        )
        agent = TaskiqAgent.setup("alias", config)

        await agent.startup()
        assert agent.scheduler is not None
        agent.scheduler.startup_mock.assert_awaited_once()  # type: ignore
        agent.broker.startup_mock.assert_awaited_once()  # type: ignore

        await agent.shutdown()
        agent.scheduler.shutdown_mock.assert_awaited_once()  # type: ignore
        agent.broker.shutdown_mock.assert_awaited_once()  # type: ignore

    async def test_lifecycle_without_scheduler(self) -> None:
        config = TaskiqConfig(
            BROKER=Broker(BACKEND="tests.doubles.FakeBroker"),
            RESULT=None,
            SCHEDULER=None,
        )
        agent = TaskiqAgent.setup("alias", config)

        await agent.startup()
        agent.broker.startup_mock.assert_awaited_once()  # type: ignore

        await agent.shutdown()
        agent.broker.shutdown_mock.assert_awaited_once()  # type: ignore
