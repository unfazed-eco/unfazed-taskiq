# 中间件

## UnfazedTaskiqExceptionMiddleware

路径：`unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware`

### 作用

任务执行失败时，捕获异常并上报到 Sentry（通过 `unfazed_sentry.capture_exception`），同时记录结构化日志。

### 使用

在 broker 配置的 `MIDDLEWARES` 列表中注册：

```python
UNFAZED_TASKIQ_SETTINGS = {
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": {
                "BACKEND": "taskiq_aio_pika.AioPikaBroker",
                "OPTIONS": { ... },
                "MIDDLEWARES": [
                    "unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware",
                ],
            },
        },
    },
}
```

### 行为

`on_error` 钩子被触发时：
1. 调用 `unfazed_sentry.capture_exception(exception, result=result, message=message)`
2. 通过 logger `unfazed.taskiq` 输出 error 级别日志，extra 包含：`task_name`、`task_args`、`task_kwargs`、`exception_type`、`exception`、`traceback`

> 注意：该中间件不会吞掉异常，异常在 taskiq 中正常传播。

### 依赖

需要安装 `unfazed-sentry`（作为 dev 依赖，未强制安装，使用时应确保环境中可用）。

---

## TaskiqResultPreSendMiddleware

路径：`unfazed_taskiq.contrib.result.middleware.TaskiqResultPreSendMiddleware`

### 作用

在任务发送到 broker 之前，在 `taskiq_result` 表中创建/更新初始记录；在任务失败时写入 traceback 到 `result.log`。

### 使用

需要在 broker 配置和 result backend 联合启用：

```python
UNFAZED_TASKIQ_SETTINGS = {
    "TASKIQ_CONFIG": {
        "default": {
            "BROKER": {
                "MIDDLEWARES": [
                    "unfazed_taskiq.contrib.result.middleware.TaskiqResultPreSendMiddleware",
                ],
            },
            "RESULT": {
                "BACKEND": "unfazed_taskiq.contrib.result.mysql.MySQLResultBackend",
            },
        },
    },
}
```

### 行为

| 钩子 | 行为 |
|---|---|
| `pre_send(message)` | 在 `taskiq_result` 表中 upsert 一条记录：写入 `task_id`、`task_name`、`task_args`、`task_kwargs`、`schedule_id`、`date_created`，status 设为 `STARTED` |
| `on_error(message, result, exception)` | 将异常 traceback 写入 `result.log`（格式化的字符串） |

两个钩子都有竞态保护：先 update，若受影响行 =0 则 create，遇到 `IntegrityError` 则重试 update。

### 关联模块

- `MySQLResultBackend`：存储最终结果时也会 upsert 同一条记录
- `TaskiqResultModel`：对应的 ORM 模型
- `TaskStatus`：状态枚举（STARTED=1, SUCCESS=2, FAILURE=3）
