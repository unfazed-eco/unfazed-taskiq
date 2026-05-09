# 定时调度

## 概述

定时调度基于 taskiq 的 `ScheduleSource` 协议，通过 `TortoiseScheduleSource` 从 MySQL/TiDB 的 `unfazed_taskiq_periodic_task` 表中读取调度配置。

## 数据库表

```sql
CREATE TABLE `unfazed_taskiq_periodic_task` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `description` text NOT NULL,
  `schedule_alias` varchar(255) NOT NULL,
  `task_name` varchar(255) NOT NULL,
  `task_args` text NOT NULL,
  `task_kwargs` text NOT NULL,
  `labels` text NOT NULL,
  `cron` varchar(255) DEFAULT NULL,
  `time` datetime(6) DEFAULT NULL,
  `last_run_at` datetime NOT NULL,
  `total_run_count` int(11) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `schedule_id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `idx_schedule_id` (`schedule_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 字段说明

| 字段 | 说明 |
|---|---|
| `schedule_alias` | 调度别名，与 `TortoiseScheduleSource(schedule_alias=...)` 对应 |
| `task_name` | 任务函数完整路径，如 `app.tasks.send_email` |
| `task_args` / `task_kwargs` | JSON 字符串，传递给任务的参数 |
| `labels` | JSON 字符串，标签（label 中可带 `schedule_id`） |
| `cron` | cron 表达式，如 `*/1 * * * *`（每分钟） |
| `time` | 一次性定时触发的具体时间 |
| `enabled` | `1`=启用，`0`=停用 |
| `schedule_id` | UUID，唯一标识一个调度 |

## TortoiseScheduleSource

```python
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

source = TortoiseScheduleSource(
    db_alias="default",           # Tortoise 数据库连接别名
    schedule_alias="default",     # 调度别名，用于过滤 unfazed_taskiq_periodic_task 表
    startup_handlers=[],          # 启动时执行的处理器（类路径列表）
    shutdown_handlers=[],         # 关闭时执行的处理器
    serializer=None,              # 自定义 TaskiqSerializer
)
```

### 主要方法

| 方法 | 说明 |
|---|---|
| `get_schedules()` | 从 DB 读取 `enabled=1` 且匹配 `schedule_alias` 的 `PeriodicTask`，转为 `ScheduledTask` 列表 |
| `add_schedule(task)` | 添加新调度（写入 DB） |
| `delete_schedule(schedule_id)` | 停用调度（`enabled=0`） |
| `pre_send(task)` | 发送前：更新 `last_run_at` |
| `post_send(task)` | 发送后：`total_run_count += 1`；非 cron 任务（一次性）设置 `enabled=0` |
| `startup()` | 初始化 Tortoise 连接，使 `self.alias` 可用 |
| `shutdown()` | 执行 shutdown_handlers |

### 配置示例

```python
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

my_source = TortoiseScheduleSource(schedule_alias="my_app")

UNFAZED_TASKIQ_SETTINGS = {
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": { ... },
            "SCHEDULER": {
                "BACKEND": "taskiq.TaskiqScheduler",
                "SOURCES": [my_source],
            },
        },
    },
}
```

## PeriodicTask ORM 模型

```python
from unfazed_taskiq.contrib.scheduler.models import PeriodicTask

# 创建定时任务
await PeriodicTask.create(
    task_name="app.tasks.send_email",
    task_args=json.dumps(["user@example.com", "Hello!"]),
    task_kwargs=json.dumps({}),
    labels=json.dumps({}),
    schedule_alias="my_app",       # 对应 TortoiseScheduleSource 的 schedule_alias
    cron="*/1 * * * *",            # 每分钟
    description="Send hello email every minute",
    name="hello-email-task",
)

# 查询
tasks = await PeriodicTask.filter(enabled=1, schedule_alias="my_app").all()
```

## 多调度源

通过不同 `schedule_alias` 区分不同调度来源，每个配置一个 `TortoiseScheduleSource`：

```python
source_a = TortoiseScheduleSource(schedule_alias="group_a")
source_b = TortoiseScheduleSource(schedule_alias="group_b")

# 在配置中注册到不同 broker
UNFAZED_TASKIQ_SETTINGS = {
    "TASKIQ_CONFIG": {
        "broker_a": {
            "SCHEDULER": { "SOURCES": [source_a] },
        },
        "broker_b": {
            "SCHEDULER": { "SOURCES": [source_b] },
        },
    },
}
```

## Unfazed Admin 集成

在 `UNFAZED_SETTINGS["INSTALLED_APPS"]` 中添加 `"unfazed_taskiq.contrib.scheduler"`，即可在 Admin UI 中管理 `PeriodicTask`。

```python
# unfazed_taskiq/contrib/scheduler/admin.py 已通过 @register 自动注册
# 路由标签: "TaskIQ"
# 支持: list, detail, search, create, edit, delete
```
