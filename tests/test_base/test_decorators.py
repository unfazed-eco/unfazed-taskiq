from types import SimpleNamespace
from typing import Any, Callable

import pytest

from unfazed_taskiq import decorators


class DummyBroker:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def task(self, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        self.calls.append(kwargs)

        def _decorator(func: Any) -> Callable[..., Any]:
            def _wrapper(*args: Any, **inner_kwargs: Any) -> Any:
                return func(*args, **inner_kwargs)

            return _wrapper

        return _decorator


def test_task_decorator_with_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DummyBroker()
    agent = SimpleNamespace(broker=broker)
    captured_aliases: list = []
    register_calls: list = []

    def fake_get_agent(alias_name: str) -> Any:
        captured_aliases.append(alias_name)
        return agent

    def fake_register(func: Any, alias_name: str, **kwargs: Any) -> None:
        register_calls.append((func, alias_name, kwargs))

    monkeypatch.setattr(decorators.agents, "get_agent", fake_get_agent)
    monkeypatch.setattr(decorators.rs, "register_broker", fake_register)

    @decorators.task(alias_name="alpha", schedule=[{"cron": "* * * * *"}])
    def sample_task(value: int) -> int:
        return value + 1

    assert sample_task(2) == 3
    assert captured_aliases == ["alpha"]
    assert broker.calls == [{"schedule": [{"cron": "* * * * *"}]}]
    assert register_calls[0][0].__name__ == "sample_task"
    assert register_calls[0][1] == "alpha"
    assert register_calls[0][2] == {"schedule": [{"cron": "* * * * *"}]}


def test_task_decorator_without_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DummyBroker()
    agent = SimpleNamespace(broker=broker)
    register_calls = []

    monkeypatch.setattr(decorators.agents, "get_agent", lambda alias_name: agent)
    monkeypatch.setattr(
        decorators.rs,
        "register_broker",
        lambda func, alias_name, **kwargs: register_calls.append((alias_name, kwargs)),
    )

    @decorators.task
    def bare_task() -> str:
        return "ok"

    assert bare_task() == "ok"
    assert register_calls == [(None, {})]
    assert broker.calls == [{}]


def test_task_decorator_missing_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    register_calls = []

    def fake_register(_: Any, alias_name: str, **kwargs: Any) -> None:
        register_calls.append((alias_name, kwargs))

    monkeypatch.setattr(decorators.agents, "get_agent", lambda alias_name: None)
    monkeypatch.setattr(decorators.rs, "register_broker", fake_register)

    def ghost_task() -> str:
        return "ghost"

    with pytest.raises(ValueError, match="Agent ghost not found"):
        decorators.task(alias_name="ghost")(ghost_task)

    assert register_calls == [("ghost", {})]
