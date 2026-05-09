# API 速查

## 核心导入

```python
# 任务装饰器
from unfazed_taskiq.decorators import task

# 全局单例
from unfazed_taskiq.agent import agents, broker, scheduler

# LifeSpan（在 UNFAZED_SETTINGS.LIFESPAN 中配置）
from unfazed_taskiq.lifespan import TaskiqLifeSpan

# 配置模型
from unfazed_taskiq.settings import (
    UnfazedTaskiqSettings,
    TaskiqConfig,
    Broker,
    Scheduler,
    Result,
)

# 中间件 - 异常捕获
from unfazed_taskiq.middleware import UnfazedTaskiqExceptionMiddleware

# 注册表
from unfazed_taskiq.registry.task import rs  # RegistryTask 单例

# Schema
from unfazed_taskiq.schema.registry.task import RegistryTaskSchema, RegistryTaskParam
```

## Scheduler Contrib

```python
# 定时调度源
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

# ORM 模型
from unfazed_taskiq.contrib.scheduler.models import PeriodicTask, BaseModel

# Admin
from unfazed_taskiq.contrib.scheduler.admin import PeriodicTaskAdmin
from unfazed_taskiq.contrib.scheduler.serializer import PeriodicTaskSerializer
from unfazed_taskiq.contrib.scheduler.app import AppConfig
```

## Result Contrib

```python
# 结果后端
from unfazed_taskiq.contrib.result.mysql import MySQLResultBackend

# 中间件
from unfazed_taskiq.contrib.result.middleware import TaskiqResultPreSendMiddleware

# ORM 模型 + 枚举
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus
# TaskStatus.STARTED = 1, SUCCESS = 2, FAILURE = 3

# 异常
from unfazed_taskiq.contrib.result.exceptions import ResultIsMissingError, ResultNotReadyError

# 工具
from unfazed_taskiq.contrib.result.utils import encode_for_json_field

# Admin
from unfazed_taskiq.contrib.result.admin import TaskiqResultAdmin
from unfazed_taskiq.contrib.result.serializer import TaskiqResultSerializer
from unfazed_taskiq.contrib.result.app import AppConfig
```

## CLI 入口

```python
from unfazed_taskiq.cli.worker.cmd import WorkerCMD  # unfazed-worker
from unfazed_taskiq.cli.scheduler.cmd import SchedulerCMD  # unfazed-scheduler
from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs
```

## Agent 内部

```python
from unfazed_taskiq.agent.handler import AgentHandler  # Storage[TaskiqAgent]
from unfazed_taskiq.agent.model import TaskiqAgent  # 封装 broker + scheduler + config
```

## Logger

```python
from unfazed_taskiq.logger import log  # logging.getLogger("unfazed.taskiq")
```

## 配置 Key 速查

| 配置路径 | 说明 |
|---|---|
| `UNFAZED_SETTINGS["LIFESPAN"]` | 添加 `"unfazed_taskiq.lifespan.TaskiqLifeSpan"` |
| `UNFAZED_SETTINGS["INSTALLED_APPS"]` | 添加 `"unfazed_taskiq.contrib.scheduler"` / `"unfazed_taskiq.contrib.result"` |
| `UNFAZED_TASKIQ_SETTINGS["DEFAULT_TASKIQ_NAME"]` | 默认 broker 别名 |
| `UNFAZED_TASKIQ_SETTINGS["TASKIQ_CONFIG"]` | 多 broker 配置 dict |
| `TASKIQ_CONFIG["<alias>"]["BROKER"]["BACKEND"]` | Broker 类路径 |
| `TASKIQ_CONFIG["<alias>"]["BROKER"]["OPTIONS"]` | Broker 构造参数 |
| `TASKIQ_CONFIG["<alias>"]["BROKER"]["MIDDLEWARES"]` | 中间件类路径列表 |
| `TASKIQ_CONFIG["<alias>"]["BROKER"]["HANDLERS"]` | 事件处理器列表 |
| `TASKIQ_CONFIG["<alias>"]["SCHEDULER"]["BACKEND"]` | Scheduler 类路径 |
| `TASKIQ_CONFIG["<alias>"]["SCHEDULER"]["SOURCES"]` | ScheduleSource 列表 |
| `TASKIQ_CONFIG["<alias>"]["RESULT"]["BACKEND"]` | Result Backend 类路径 |
| `TASKIQ_CONFIG["<alias>"]["RESULT"]["OPTIONS"]` | Result Backend 构造参数 |

## 常用代码模式

### 创建简单任务

```python
from unfazed_taskiq.decorators import task

@task
async def my_task(x: int) -> int:
    return x * 2

# 调用
result = await my_task.kiq(42)
value = await result.wait_result()  # 需要 result backend
```

### 创建指定 broker 的任务

```python
@task(alias_name="high_priority")
async def urgent_task(payload: str) -> None:
    ...
```

### 创建定时任务记录

```python
from unfazed_taskiq.contrib.scheduler.models import PeriodicTask
import json

await PeriodicTask.create(
    task_name="app.tasks.my_task",
    task_args=json.dumps([42]),
    task_kwargs=json.dumps({}),
    labels=json.dumps({}),
    cron="*/5 * * * *",
    schedule_alias="default",
    name="my-periodic-task",
    description="Runs every 5 minutes",
)
```
