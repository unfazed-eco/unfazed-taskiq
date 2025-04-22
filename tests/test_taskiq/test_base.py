from taskiq import InMemoryBroker
from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend

from unfazed_taskiq import TaskiqAgent
from unfazed_taskiq.settings import UnfazedTaskiqSettings

TEMP_SETTINGS = {
    "BROKER": {
        "BACKEND": "taskiq.InMemoryBroker",
        "OPTIONS": {},
    },
    "RESULT": {
        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
        "OPTIONS": {
            "redis_url": "redis://redis:6379",
        },
    },
    "SCHEDULER": {
        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
        "SOURCES_CLS": ["taskiq.schedule_sources.LabelScheduleSource"],
    },
}


async def test_agent() -> None:
    agent = TaskiqAgent()

    settings = UnfazedTaskiqSettings.model_validate(TEMP_SETTINGS)
    agent.setup(settings)

    assert isinstance(agent.broker, InMemoryBroker)
    assert isinstance(agent.broker.result_backend, RedisAsyncResultBackend)
    assert isinstance(agent.scheduler, TaskiqScheduler)

    await agent.startup()

    await agent.shutdown()
