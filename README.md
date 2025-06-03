Unfazed Taskiq
===============

taskiq wrapper with unfazed.


Installation
------------

```bash
pip install unfazed-taskiq
```


Quick Start
-----

Add settings to your unfazed settings file:

```python

from taskiq_redis import ListRedisScheduleSource
redis_resource = ListRedisScheduleSource(url=f"redis://{REDIS_HOST}:6379")

# entry/settings.py
UNFAZED_TASKIQ_SETTINGS = {
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
    # Sources can be a list of strings or ScheduleSource instances
    "SCHEDULER": {
        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
        "SOURCES": ["taskiq.schedule_sources.LabelScheduleSource", redis_resource],
    },
}

# add lifespan to your settings
UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
}

```

Use UnfazedTaskiqAgent in your app's `tasks.py`:

> Note: Sources can be a list of strings or ScheduleSource instances, when it's a string, it will be imported and instantiated with args `broker` from `BROKER` in settings.

```python
# app/tasks.py
from unfazed_taskiq import agent

@agent.broker.task
async def add(a: int, b: int) -> int:
    return a + b


@agent.broker.task(schedule=[{"crontab": "*/1 * * * *", "args": [1, 2]}])
async def add_schedule(a: int, b: int) -> int:
    return a + b

```


Kick off tasks 

```python

from .tasks import add

async def your_service():
    await add.kiq(1, 2)

```


Start Taskiq Worker or Scheduler

```bash
taskiq worker unfazed_taskiq.cli:broker

# or
taskiq scheduler unfazed_taskiq.cli:scheduler
```


