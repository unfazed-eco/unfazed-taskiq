import pytest
from taskiq import InMemoryBroker
from taskiq.scheduler.scheduler import TaskiqScheduler

from unfazed_taskiq import TaskiqAgent
from unfazed_taskiq.settings import UnfazedTaskiqSettings

TEMP_SETTINGS = {
    "BROKER": {
        "BACKEND": "taskiq.InMemoryBroker",
        "OPTIONS": {},
    },
    "SCHEDULER": {
        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
        "OPTIONS": {},
    },
}


async def test_agent() -> None:
    agent = TaskiqAgent()

    with pytest.raises(ValueError):
        _ = agent.broker

    with pytest.raises(ValueError):
        _ = agent.scheduler

    settings = UnfazedTaskiqSettings.model_validate(TEMP_SETTINGS)
    agent.setup(settings)

    assert isinstance(agent.broker, InMemoryBroker)
    assert isinstance(agent.scheduler, TaskiqScheduler)

    await agent.startup()

    await agent.shutdown()
