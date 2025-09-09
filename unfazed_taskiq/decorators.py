import inspect
from typing import Any, get_type_hints, Optional
from typing import Callable

from taskiq import AsyncBroker

from unfazed_taskiq.agent import get_agent
from unfazed_taskiq.base import TaskiqAgent
from unfazed_taskiq.registry import rs
from unfazed_taskiq.schema.registry import RegistryTask, RegistryTaskParam


def task(broker_name: Optional[str] = None, **task_kwargs: Any) -> Callable:
    """
    use taskiq decorator to decorate task

    Args:
        broker_name: broker name, if None, use default broker
        **task_kwargs: other arguments for taskiq task decorator

    Example:
        @task(broker_name="high_priority")
        async def high_priority_task():
            pass

        @task(broker_name="low_priority", schedule=[{"cron": "*/5 * * * *"}])
        async def scheduled_task():
            pass
    """

    def register_borker(
        func: Callable,
        broker_name: str,
        **kwargs: Any,
    ) -> RegistryTask:
        params_info: list[RegistryTaskParam] = []
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        for name, param in sig.parameters.items():
            param_type = type_hints.get(name, Any)
            required = param.default is inspect.Parameter.empty
            default = None if required else param.default

            params_info.append(
                RegistryTaskParam(
                    **{
                        "name": name,
                        "hint_type": param_type,
                        "required": required,
                        "default": default,
                    }
                )
            )
        registry_task: RegistryTask = RegistryTask(
            name=func.__name__,
            broker_name=broker_name,
            params=params_info,
            docs=func.__doc__,
            schedule=task_kwargs.get("schedule", None),
        )

        task_path = f"{func.__module__}.{func.__name__}"

        rs.register(task_path, registry_task)

    def decorator(func: Callable) -> Callable:

        # get agent & broker
        agent: TaskiqAgent = get_agent()
        broker: AsyncBroker = agent.get_broker(broker_name)

        # get real broker name
        real_broker_name: str = (
            agent._default_taskiq_name if broker_name is None else broker_name
        )

        register_borker(func, real_broker_name, **task_kwargs)

        # decorate task
        return broker.task(**task_kwargs)(func)

    return decorator
