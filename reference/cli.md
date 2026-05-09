# CLI 命令参考

`unfazed-taskiq` 通过 `pyproject.toml` 的 `[project.entry-points."taskiq_cli"]` 注册了两个自定义 CLI 命令：

```
[project.entry-points."taskiq_cli"]
unfazed-worker = "unfazed_taskiq.cli.worker:WorkerCMD"
unfazed-scheduler = "unfazed_taskiq.cli.scheduler:SchedulerCMD"
```

这两个命令作为 taskiq CLI 的子命令使用：

```bash
uv run taskiq unfazed-worker <args>
uv run taskiq unfazed-scheduler <args>
```

## unfazed-worker

启动 worker 进程，消费 broker 队列中的任务。

```bash
uv run taskiq unfazed-worker <broker_path> [modules] [options]
```

### 参数

| 参数 | 说明 |
|---|---|
| `broker_path` | Broker 实例路径，固定为 `unfazed_taskiq.agent:broker` |
| `modules` | 可选，额外的模块路径（查找任务） |

### 常用选项（继承自 taskiq `WorkerArgs`）

| 选项 | 说明 |
|---|---|
| `-fsd`, `--fs-discover` | 递归查找任务文件 |
| `-tp`, `--tasks-pattern` | 任务文件名 glob 模式，默认 `**/tasks.py` |
| `-w`, `--workers` | Worker 进程数 |
| `--log-level` | 日志级别 |

### 示例

```bash
# 自动发现所有 tasks.py
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd

# 自动发现 + 指定任务文件
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd -tp backend/spider/tasks.py

# 指定 workers 数量
uv run taskiq unfazed-worker unfazed_taskiq.agent:broker -fsd -w 4
```

### 内部流程

1. 初始化 Unfazed（`Unfazed(silent=True)` → `setup()`）
2. 解析 WorkerArgs
3. 调用 `taskiq.cli.worker.run.run_worker(wargs)` 启动 worker

## unfazed-scheduler

启动调度器，周期性从数据源读取调度配置并发送任务到 broker。

```bash
uv run taskiq unfazed-scheduler <scheduler_path> [modules] [options]
```

### 参数

| 参数 | 说明 |
|---|---|
| `scheduler_path` | Scheduler 实例路径，固定为 `unfazed_taskiq.agent:scheduler` |
| `modules` | 可选，额外的模块路径 |

### 专属选项

| 选项 | 说明 |
|---|---|
| `-an`, `--alias-name` | 指定要运行的 scheduler 别名（可多次使用）；不传则运行所有 |
| `-fsd`, `--fs-discover` | 递归查找任务文件 |
| `-tp`, `--tasks-pattern` | 任务文件名模式 |
| `--skip-first-run` | 跳过首次运行 |
| `--update-interval` | 检查新调度的时间间隔（秒），默认 60 |
| `--log-level` | 日志级别 |

### 示例

```bash
# 启动所有 scheduler
uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler

# 启动指定别名的 scheduler
uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler --alias-name default

# 启动多个指定别名的 scheduler
uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler --alias-name default --alias-name high_priority

# 跳过首次立即运行
uv run taskiq unfazed-scheduler unfazed_taskiq.agent:scheduler --skip-first-run
```

### 内部流程

1. 初始化 Unfazed（`Unfazed(silent=True)` → `setup()`）
2. 解析 `SchedulerEventArgs`
3. 遍历所有 `agents.storage` 中有 scheduler 的 agent
4. 如果未指定 `--alias-name`，运行所有；如指定，只运行匹配的
5. `asyncio.gather` 并发启动各 scheduler 的 `run_scheduler(event_parsed)`

## 全局单例导出

CLI 命令引用的 `unfazed_taskiq.agent` 模块导出了以下全局单例：

```python
from unfazed_taskiq.agent import agents, broker, scheduler

# agents: AgentHandler 单例，管理所有 TaskiqAgent
# broker: agents.broker 属性，默认 broker
# scheduler: agents.scheduler 属性，默认 scheduler
```

这些单例在 `TaskiqLifeSpan.on_startup` 时初始化（通过 `agents.setup()` 读取 UNFAZED_TASKIQ_SETTINGS 配置）。
