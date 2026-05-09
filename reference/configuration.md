# 配置参考

## UNFAZED_TASKIQ_SETTINGS

在 Unfazed 的 settings 文件中配置，由 `unfazed_taskiq.settings.UnfazedTaskiqSettings` 解析。

```python
# entry/settings.py

UNFAZED_TASKIQ_SETTINGS = {
    "DEFAULT_TASKIQ_NAME": "default",       # 必填：默认 broker 别名
    "TASKIQ_CONFIG": {
        "<alias_name>": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",   # broker 类路径
                "OPTIONS": {                                   # 传给 broker 构造函数的参数
                    "url": "amqp://guest:guest@localhost:5672/",
                    "exchange_name": "my-exchange",
                    "queue_name": "my-queue",
                },
                "MIDDLEWARES": [                               # broker 中间件列表（类路径）
                    "unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware",
                ],
                "HANDLERS": [                                  # broker 事件处理器
                    {
                        "handler": "myapp.handlers.MyHandler",
                        "event": "taskiq.events.TaskiqEvents.ON_SUCCESS",
                    }
                ],
            },
            "SCHEDULER": {                    # 可选：定时调度配置
                "BACKEND": "taskiq.TaskiqScheduler",
                "SOURCES": [                  # ScheduleSource 实例或类路径
                    my_tortoise_source,
                ],
            },
            "RESULT": {                       # 可选：结果后端配置
                "BACKEND": "unfazed_taskiq.contrib.result.mysql.MySQLResultBackend",
                "OPTIONS": {},
            },
        },
        # 可配置多个 alias，每个对应独立的 broker
        "another_queue": { ... },
    },
}
```

### Broker

| 字段 | 类型 | 说明 |
|---|---|---|
| `BACKEND` | `str` | Broker 类完整路径，如 `taskiq_aio_pika.AioPikaBroker` |
| `OPTIONS` | `dict` | 传给 broker 构造函数的参数 |
| `MIDDLEWARES` | `list[str]` | 中间件类路径列表 |
| `HANDLERS` | `list[dict]` | 事件处理器，每个 dict 包含 `handler`（类路径）和 `event`（str 或 `TaskiqEvents`） |

### Scheduler（可选）

| 字段 | 类型 | 说明 |
|---|---|---|
| `BACKEND` | `str` | Scheduler 类路径，如 `taskiq.TaskiqScheduler` |
| `SOURCES` | `list` | `ScheduleSource` 实例或类路径列表 |

### Result（可选）

| 字段 | 类型 | 说明 |
|---|---|---|
| `BACKEND` | `str` | Result backend 类路径，如 `unfazed_taskiq.contrib.result.mysql.MySQLResultBackend` |
| `OPTIONS` | `dict` | 传给 result backend 构造函数的参数（如 `serializer`） |

## UNFAZED_SETTINGS 集成

需要将 `TaskiqLifeSpan` 注册到 Unfazed 的 LIFESPAN 配置：

```python
UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "DATABASE": {},  # 使用 scheduler 时必须配置 DATABASE
    "INSTALLED_APPS": [
        "unfazed_taskiq.contrib.scheduler",   # 启用定时任务 Admin
        "unfazed_taskiq.contrib.result",      # 启用结果 Admin
    ],
}
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `UNFAZED_SETTINGS_MODULE` | 必须设置，指向 Unfazed 配置模块路径 |

## 完整示例（多 broker + scheduler + result）

```python
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

AMQP_URL = "amqp://guest:guest@localhost:5672/"

default_source = TortoiseScheduleSource(schedule_alias="default")
high_prio_source = TortoiseScheduleSource(schedule_alias="high_priority")

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
                "MIDDLEWARES": [
                    "unfazed_taskiq.contrib.result.middleware.TaskiqResultPreSendMiddleware",
                ],
            },
            "SCHEDULER": {
                "BACKEND": "taskiq.TaskiqScheduler",
                "SOURCES": [default_source],
            },
            "RESULT": {
                "BACKEND": "unfazed_taskiq.contrib.result.mysql.MySQLResultBackend",
                "OPTIONS": {},
            },
        },
        "high_priority": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",
                "OPTIONS": {
                    "url": AMQP_URL,
                    "exchange_name": "high-prio",
                    "queue_name": "high-prio",
                },
            },
            "SCHEDULER": {
                "BACKEND": "taskiq.TaskiqScheduler",
                "SOURCES": [high_prio_source],
            },
        },
    },
}

UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "INSTALLED_APPS": [
        "unfazed_taskiq.contrib.result",
    ],
}
```
