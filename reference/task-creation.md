# 任务创建

## @task 装饰器

`unfazed_taskiq.decorators.task` 是创建任务的核心 API。

```python
from unfazed_taskiq.decorators import task
```

### 签名

```python
def task(
    func: Optional[Callable] = None,
    *,
    alias_name: Optional[str] = None,
    **task_kwargs: Any,          # 透传给 taskiq 的 broker.task()
) -> Callable:
```

### 参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `func` | `Callable` | 要装饰的 async 函数（`@task` 不带括号时传入） |
| `alias_name` | `str` | 指定 broker 别名，`None` 使用默认别名 |
| `**task_kwargs` | `Any` | 透传给底层 `broker.task()`，如 `schedule` |

### 内部行为

调用 `@task` 时内部执行：

1. `rs.register_broker(func, alias_name, **task_kwargs)` — 注册到 `RegistryTask`，提取函数签名、类型注解、docstring
2. `agents.get_agent(alias_name)` — 获取对应的 `TaskiqAgent`
3. `agent.broker.task(**task_kwargs)(func)` — 调用 taskiq 的 `broker.task()` 注册任务

### 基本用法

```python
# app/tasks.py
from unfazed_taskiq.decorators import task

# 不使用额外的 task_kwargs
@task
async def simple_task(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}"

# 等价写法：使用括号
@task()
async def another_task(x: int, y: int) -> int:
    return x * y
```

### 指定 broker 别名

```python
# 将任务注册到指定 broker
@task(alias_name="high_priority")
async def important_task(payload: dict) -> None:
    """This runs on the high_priority broker/queue."""
    ...
```

### 带调度配置（内联 schedule）

```python
# task_kwargs 透传给 brok er.task()，可以指定 schedule
@task(alias_name="default", schedule=[{"cron": "*/5 * * * *"}])
async def periodic_cleanup() -> None:
    """Runs every 5 minutes."""
    ...
```

### 执行任务（kiq）

```python
# 在业务代码中调用
from app.tasks import simple_task

async def my_service():
    # 异步执行，立即返回 AsyncTaskResult
    task = await simple_task.kiq("World")
    
    # 等待结果（需要 result backend）
    result = await task.wait_result()
    print(result)  # "Hello, World"
```

## RegistryTask（任务注册表）

任务被 `@task` 装饰后，会自动注册到全局 `RegistryTask` 单例 `rs`。

```python
from unfazed_taskiq.registry.task import rs

# 按路径查询
task_schema = rs.get("app.tasks.simple_task")

# 按关键字过滤
tasks = rs.filter_path("app.tasks")  # 返回所有匹配的 RegistryTaskSchema

# 结构
# RegistryTaskSchema:
#   - name: str              # 函数名
#   - alias_name: str|None   # broker 别名
#   - params: list[RegistryTaskParam]
#       - name: str
#       - hint_type: type
#       - required: bool
#       - default: Any
#   - docs: str|None         # docstring
#   - schedule: list[dict]|None
```
