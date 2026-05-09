# 结果后端（Result Backend）

## 概述

`unfazed_taskiq` 通过 `MySQLResultBackend` 将 taskiq 任务结果持久化到 MySQL/TiDB，并通过 `TaskiqResultPreSendMiddleware` 记录任务的创建时间和元数据。

## 数据库表

```sql
CREATE TABLE `taskiq_result` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `task_id` VARCHAR(255) NOT NULL UNIQUE,
    `status` SMALLINT NOT NULL,                      -- 1=STARTED, 2=SUCCESS, 3=FAILURE
    `result` BLOB NULL,                              -- 序列化的完整 TaskiqResult
    `return_value` JSON NULL,                        -- 任务的返回值（JSON 可序列化部分）
    `date_done` BIGINT NULL,                         -- 完成时间戳（毫秒）
    `date_created` BIGINT NULL,                      -- 入队时间戳（毫秒）
    `task_name` VARCHAR(255) NULL,                   -- 任务函数路径
    `schedule_id` VARCHAR(255) NULL,                 -- 定时任务关联的 schedule_id
    `task_args` JSON NULL,                           -- 参数列表
    `task_kwargs` JSON NULL,                         -- 关键字参数
    `traceback` TEXT NULL,                           -- 失败时的 traceback
    INDEX `idx_date_done` (`date_done`),
    INDEX `idx_task_name_date_done` (`task_name`, `date_done`),
    INDEX `idx_schedule_id_date_done` (`schedule_id`, `date_done`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 启用方式

两个步骤：配置 Result Backend + 添加 PreSendMiddleware。

```python
# entry/settings.py

UNFAZED_SETTINGS = {
    "INSTALLED_APPS": [
        "unfazed_taskiq.contrib.result",   # 启用 Admin
    ],
}

UNFAZED_TASKIQ_SETTINGS = {
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": {
                "BACKEND": "...",
                "OPTIONS": {...},
                "MIDDLEWARES": [
                    # 必须在 broker middlewares 中添加
                    "unfazed_taskiq.contrib.result.middleware.TaskiqResultPreSendMiddleware",
                ],
            },
            "RESULT": {
                "BACKEND": "unfazed_taskiq.contrib.result.mysql.MySQLResultBackend",
                "OPTIONS": {
                    # serializer: 可选，默认 PickleSerializer
                },
            },
        },
    },
}
```

## MySQLResultBackend

```python
from unfazed_taskiq.contrib.result.mysql import MySQLResultBackend

backend = MySQLResultBackend(serializer=None)  # None 时默认 PickleSerializer
```

### 关键方法

| 方法 | 说明 |
|---|---|
| `set_result(task_id, result)` | 存储任务结果（update-then-create upsert）：写入 `result` blob、`status`、`date_done`、`traceback`、`return_value` |
| `is_result_ready(task_id)` | 检查结果是否就绪（status 为 SUCCESS 或 FAILURE 且 result blob 不为空） |
| `get_result(task_id, with_logs=False)` | 获取结果；未就绪抛 `ResultNotReadyError`，记录不存在抛 `ResultIsMissingError` |

### 异常

| 异常 | 触发条件 |
|---|---|
| `ResultIsMissingError` | `task_id` 在数据库中不存在 |
| `ResultNotReadyError` | 记录存在但结果尚未就绪 |

## TaskiqResultPreSendMiddleware

在任务消息发送到 broker **之前**（`pre_send` 钩子），写入 `taskiq_result` 表的初始记录：

- `task_id`, `task_name`, `task_args`, `task_kwargs`
- `schedule_id`（从 `message.labels` 中提取）
- `date_created`（毫秒时间戳）
- `status = TaskStatus.STARTED (1)`
- `result`, `return_value`, `date_done`, `traceback` 清空为 `None`

使用 upsert（先 update，若 update 行数=0 则 create），处理并发创建时的 IntegrityError 竞态。

`on_error` 钩子：将异常 traceback 写入 `result.log`，随后由 `MySQLResultBackend.set_result` 持久化。

## TaskiqResultModel

```python
from unfazed_taskiq.contrib.result.models import TaskiqResultModel, TaskStatus

# TaskStatus 枚举
# TaskStatus.STARTED = 1
# TaskStatus.SUCCESS = 2
# TaskStatus.FAILURE = 3

# 按 task_id 查询
row = await TaskiqResultModel.filter(task_id="abc123").first()

# 按状态和任务名查询
rows = await TaskiqResultModel.filter(status=TaskStatus.FAILURE, task_name="app.tasks.foo").all()
```

## 获取任务结果

```python
task = await my_task.kiq("arg1", kw=42)
value = await task.wait_result()  # 阻塞等待直到返回结果
```

## Unfazed Admin 集成

在 `INSTALLED_APPS` 中添加 `"unfazed_taskiq.contrib.result"` 后，Admin UI 的 "TaskIQ" 标签下会有 `TaskiqResultAdmin`：
- 列表展示 `task_id`、`task_name`、`status`、`task_args`、`task_kwargs`、`return_value`、时间戳、`schedule_id`、`traceback`
- 支持按 `task_id`、`task_name`、`schedule_id` 搜索
- 只读模式（不可添加/编辑，可删除）
- `result` blob 字段不在 JSON 输出中暴露

## JSON 字段编码

`task_args`、`task_kwargs`、`return_value` 存入 Tortoise `JSONField` 时使用 `encode_for_json_field()`：

```python
from unfazed_taskiq.contrib.result.utils import encode_for_json_field

# 可 JSON 序列化的值 → 直接存储
encode_for_json_field([1, 2, 3])     # [1, 2, 3]

# 字符串 → 包装在 dict 中（Tortoise 会将裸 str 当 JSON 文本解析）
encode_for_json_field("hello")       # {"__taskiq_json_str_fallback__": "hello"}

# 不可序列化的值 → 转为字符串包装
encode_for_json_field(object())      # {"__taskiq_json_str_fallback__": "<object ...>"}

# None → None
encode_for_json_field(None)          # None
```
