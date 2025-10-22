# Unfazed Taskiq

taskiq wrapper with unfazed.

## Installation

```bash
pip install unfazed-taskiq
```

## Quick Start

This guide will help you get started with Unfazed Taskiq in just a few minutes.

### 1. Configure Settings

Add Taskiq configuration to your Unfazed settings file:

```python
AMQP_URL = os.getenv("AMQP_URL", DEFAULT_AMQP_URL)
# entry/settings.py
UNFAZED_TASKIQ_SETTINGS = {
    "DEFAULT_TASKIQ_NAME": "default",
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",
                "OPTIONS": {
                    "url": AMQP_URL,
                    "exchange_name": "unfazed-taskiq",
                    "queue_name": "unfazed-taskiq",
                },
            },
        },
    },
}

# Add Taskiq lifespan to your Unfazed settings
UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    # ... your other settings
}
```

### 2. Create Tasks

Define your tasks in your app's `tasks.py` file:

```python
# app/tasks.py
from unfazed_taskiq.decorators import task

@task
async def add_numbers(a: int, b: int) -> int:
    """Simple addition task."""
    return a + b
```

### 3. Start Worker

```shell
# auto discover all async task
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd

# auto discover all async task by task file
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd -tp backend/spider/tasks.py
```

### 4. Execute Tasks

```python
from xxx.task import add_numbers
async def your_service():
    # Execute task immediately
    result = await add_numbers.kiq(10, 20)
    print(f"Task result: {result}")
```

## How to use Scheduler

### 1. Configure Settings

Add Taskiq configuration to your Unfazed settings file:

```python
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

AMQP_URL = os.getenv("AMQP_URL", DEFAULT_AMQP_URL)
unfazedtaskiq_source = TortoiseScheduleSource(schedule_alias="unfazedtaskiq")
unfazedtaskiq_v2_source = TortoiseScheduleSource(schedule_alias="unfazedtaskiq_v2")

# entry/settings.py
UNFAZED_TASKIQ_SETTINGS = {
    "DEFAULT_TASKIQ_NAME": "default",
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",
                "OPTIONS": {
                    "url": AMQP_URL,
                    "exchange_name": "unfazedtaskiq",
                    "queue_name": "unfazedtaskiq",
                },
                "MIDDLEWARES": { # options: if you want use sentry collect error
                    "unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware"
                }
            },
            "SCHEDULER": {
                "SOURCES": [unfazedtaskiq_source],
                "BACKEND": "taskiq.TaskiqScheduler",
            },
        },
        "taskiq_task": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",
                "OPTIONS": {
                    "url": AMQP_URL,
                    "exchange_name": "unfazedtaskiq_v2",
                    "queue_name": "unfazedtaskiq_v2",
                },
                "MIDDLEWARES": { # options: if you want use sentry collect error
                    "unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware"
                }
            },
            "SCHEDULER": {
                "SOURCES": [unfazedtaskiq_v2_source],
                "BACKEND": "taskiq.TaskiqScheduler",
            },
        },
    },
}

# Add Taskiq lifespan to your Unfazed settings
UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    # ... your other settings
}
```

### 2. Create Tasks

Define your tasks in your app's `tasks.py` file:

```python
# app/tasks.py
from unfazed_taskiq.decorators import task

@task
async def send_email(email: str, content: str) -> None:
    """send some msg for some body."""
    ...

```

### 3. Schedule Tasks

You can schedule tasks using the database scheduler:

```python
# Create scheduled tasks in your database
from unfazed_taskiq.contrib.scheduler.models import PeriodicTask
import json

# Create a periodic task that runs every minute
# Also, can use Unfazed-admin UI config
await PeriodicTask.create(
    task_name="app.tasks.send_email",
    task_args=json.dumps(["test@gmail.com", "test content"]),
    task_kwargs=json.dumps({}),
    cron="*/1 * * * *",  # Every minute
    description="Add two numbers every minute",
)
```

### 4. Start Scheduler

Execute tasks from your application code:

- start all scheduler
  ```shell
  uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler
  ```
- start scheduler with alias_name (eg: default / taskiq_task)
  ```shell
  uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler --alias-name taskiq_task
  ```

### 5. Start Workers

Start the Taskiq worker to process tasks:

```bash
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd -tp app/tasks.py
```

## 📖 更多文档

pls read [taskiq document](https://taskiq-python.github.io/guide/)

## 📄 许可证

本项目基于 MIT 许可证开源。
