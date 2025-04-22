import os
import typing as t

import pytest
from taskiq import InMemoryBroker
from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend

from unfazed_taskiq.cli import get_agent


@pytest.fixture
def setup_cli() -> t.Generator[None, None, None]:
    os.environ["UNFAZED_SETTINGS_MODULE"] = "tests.proj.entry.settings"

    yield

    del os.environ["UNFAZED_SETTINGS_MODULE"]


@pytest.fixture
def setup_cli2() -> t.Generator[None, None, None]:
    os.environ["UNFAZED_SETTINGS_MODULE"] = "tests.proj.entry2.settings"

    yield

    del os.environ["UNFAZED_SETTINGS_MODULE"]


def test_cli(setup_cli: t.Generator[None, None, None]) -> None:
    agent = get_agent()

    assert isinstance(agent.broker, InMemoryBroker)
    assert isinstance(agent.broker.result_backend, RedisAsyncResultBackend)
    assert isinstance(agent.scheduler, TaskiqScheduler)


def test_cli_without_env() -> None:
    if "UNFAZED_SETTINGS_MODULE" in os.environ:
        del os.environ["UNFAZED_SETTINGS_MODULE"]

    with pytest.raises(ValueError):
        get_agent()


def test_cli_without_scheduler(setup_cli2: t.Generator[None, None, None]) -> None:
    agent = get_agent()

    assert isinstance(agent.broker, InMemoryBroker)
    assert isinstance(agent.broker.result_backend, RedisAsyncResultBackend)
    assert agent.scheduler is None
