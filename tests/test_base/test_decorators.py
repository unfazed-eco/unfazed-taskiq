from types import SimpleNamespace

import pytest

from unfazed_taskiq import decorators


class DummyBroker:
    def __init__(self) -> None:
        self.calls = []

    def task(self, **kwargs):
        self.calls.append(kwargs)

        def _decorator(func):
            def _wrapper(*args, **inner_kwargs):
                return func(*args, **inner_kwargs)

            return _wrapper

        return _decorator


def test_task_decorator_with_parameters(monkeypatch):
    broker = DummyBroker()
    agent = SimpleNamespace(broker=broker)
    captured_aliases = []
    register_calls = []

    def fake_get_agent(alias_name):
        captured_aliases.append(alias_name)
        return agent

    def fake_register(func, alias_name, **kwargs):
        register_calls.append((func, alias_name, kwargs))

    monkeypatch.setattr(decorators.agent, "get_agent", fake_get_agent)
    monkeypatch.setattr(decorators.rs, "register_broker", fake_register)

    @decorators.task(alias_name="alpha", schedule=[{"cron": "* * * * *"}])
    def sample_task(value):
        return value + 1

    assert sample_task(2) == 3
    assert captured_aliases == ["alpha"]
    assert broker.calls == [{"schedule": [{"cron": "* * * * *"}]}]
    assert register_calls[0][0].__name__ == "sample_task"
    assert register_calls[0][1] == "alpha"
    assert register_calls[0][2] == {"schedule": [{"cron": "* * * * *"}]}


def test_task_decorator_without_parameters(monkeypatch):
    broker = DummyBroker()
    agent = SimpleNamespace(broker=broker)
    register_calls = []

    monkeypatch.setattr(decorators.agent, "get_agent", lambda alias_name: agent)
    monkeypatch.setattr(
        decorators.rs,
        "register_broker",
        lambda func, alias_name, **kwargs: register_calls.append((alias_name, kwargs)),
    )

    @decorators.task
    def bare_task():
        return "ok"

    assert bare_task() == "ok"
    assert register_calls == [(None, {})]
    assert broker.calls == [{}]


def test_task_decorator_missing_agent(monkeypatch):
    register_calls = []

    def fake_register(func, alias_name, **kwargs):
        register_calls.append((alias_name, kwargs))

    monkeypatch.setattr(decorators.agent, "get_agent", lambda alias_name: None)
    monkeypatch.setattr(decorators.rs, "register_broker", fake_register)

    def ghost_task() -> None:
        return "ghost"

    with pytest.raises(ValueError, match="Agent ghost not found"):
        decorators.task(alias_name="ghost")(ghost_task)

    assert register_calls == [("ghost", {})]
