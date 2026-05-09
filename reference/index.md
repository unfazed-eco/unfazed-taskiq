# Unfazed Taskiq — Reference for LLM

> `unfazed-taskiq` 是一个将 [taskiq](https://taskiq-python.github.io/guide/) 集成到 [Unfazed](https://github.com/unfazed-eco/unfazed) 框架的插件，提供多 broker、定时调度（基于 MySQL/TiDB）、结果持久化、Admin UI 管理等能力。

## 目录结构

```
unfazed_taskiq/
├── __init__.py
├── decorators.py          # @task 装饰器（任务注册入口）
├── lifespan.py            # Unfazed LifeSpan，管理 broker/scheduler 启停
├── logger.py              # 日志 logger（unfazed.taskiq）
├── middleware.py           # 异常捕获中间件（Sentry）
├── settings.py            # 配置模型（Pydantic）
├── agent/
│   ├── __init__.py        # 导出 agents, broker, scheduler 全局单例
│   ├── handler.py         # AgentHandler：管理所有 TaskiqAgent 实例
│   └── model.py           # TaskiqAgent：单个 broker + scheduler 的封装
├── cli/
│   ├── scheduler/         # unfazed-scheduler CLI 命令
│   │   ├── cmd.py
│   │   └── args.py
│   └── worker/            # unfazed-worker CLI 命令
│       └── cmd.py
├── registry/
│   └── task.py            # RegistryTask：任务注册表（供 admin 展示）
├── schema/
│   └── registry/
│       └── task.py        # RegistryTaskSchema / RegistryTaskParam 数据模型
└── contrib/
    ├── scheduler/         # 定时任务 contrib 模块
    │   ├── sources.py     # TortoiseScheduleSource: 从 DB 读取调度
    │   ├── models.py      # PeriodicTask ORM 模型
    │   ├── admin.py       # Unfazed Admin 注册
    │   ├── serializer.py  # API 序列化器
    │   └── app.py         # AppConfig
    └── result/            # 结果持久化 contrib 模块
        ├── middleware.py  # TaskiqResultPreSendMiddleware：写入 task 元数据
        ├── mysql.py       # MySQLResultBackend：存储/读取 task 结果
        ├── models.py      # TaskiqResultModel ORM 模型 + TaskStatus 枚举
        ├── admin.py       # Unfazed Admin 注册
        ├── serializer.py  # API 序列化器
        ├── utils.py       # JSON 字段编码工具
        ├── exceptions.py  # ResultIsMissingError / ResultNotReadyError
        └── app.py         # AppConfig
```

## 核心概念

| 概念 | 说明 |
|---|---|
| **Broker** | 消息队列 backend（如 `taskiq_aio_pika.AioPikaBroker`），支持多 broker |
| **Scheduler** | 定时调度器，通过 `TortoiseScheduleSource` 从 MySQL 表中读取定时任务配置 |
| **Task** | 通过 `@task` 装饰器定义，底层调用 taskiq 的 `broker.task()` |
| **Result Backend** | MySQL 持久化任务结果，通过 `MySQLResultBackend` 实现 |
| **Agent** | `TaskiqAgent` 封装一个 broker + 可选的 scheduler + result backend |
| **AgentHandler** | 管理多个 `TaskiqAgent` 的单例（全局 `agents`） |
| **LifeSpan** | `TaskiqLifeSpan` 跟随 Unfazed 应用生命周期启动/关闭所有 agent |

## 数据流

```
  用户代码
    │ @task 装饰器 → 注册到 RegistryTask + TaskiqAgent.broker
    │ func.kiq(args) → 发送消息到 Broker（AMQP）
    ▼
  Broker (RabbitMQ)
    │ Worker 消费消息 → 执行函数
    │ Middleware 链：
    │   - TaskiqResultPreSendMiddleware → 写入 taskiq_result 表（status=STARTED）
    │   - UnfazedTaskiqExceptionMiddleware → 捕获异常 → Sentry
    ▼
  MySQL/TiDB
    ├── taskiq_result 表 ← MySQLResultBackend 写入结果
    └── unfazed_taskiq_periodic_task 表 ← TortoiseScheduleSource 读取调度
```

## 快速链接

- [配置参考](./configuration.md) — `UNFAZED_TASKIQ_SETTINGS` 完整配置项
- [任务创建](./task-creation.md) — `@task` 装饰器用法
- [定时调度](./scheduler.md) — `TortoiseScheduleSource` + `PeriodicTask` 模型
- [结果后端](./result-backend.md) — `MySQLResultBackend` + 结果表结构
- [CLI 命令](./cli.md) — `unfazed-worker` / `unfazed-scheduler`
- [中间件](./middleware.md) — 内置中间件说明
- [API 速查](./api-reference.md) — 所有可导入符号的一览表
