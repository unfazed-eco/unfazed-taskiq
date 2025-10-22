from typing import Any, Callable, Optional

from unfazed_taskiq.agent.handler import agents
from unfazed_taskiq.agent.model import TaskiqAgent
from unfazed_taskiq.registry.task import rs


def task(
    func: Optional[Callable] = None,
    *,
    alias_name: Optional[str] = None,
    **task_kwargs: Any,
) -> Callable:
    """
    use taskiq decorator to decorate task

    Args:
        func: function to decorate (when used without parentheses)
        alias_name: alias name, if None, use default alias
        **task_kwargs: other arguments for taskiq task decorator

    Example:
        @task
        async def simple_task():
            pass

        @task(alias_name="high_priority")
        async def high_priority_task():
            pass

        @task(alias_name="low_priority", schedule=[{"cron": "*/5 * * * *"}])
        async def scheduled_task():
            pass
    """

    def decorator(func: Callable) -> Callable:
        _agent: Optional[TaskiqAgent] = agents.get_agent(alias_name)
        rs.register_broker(func, alias_name, **task_kwargs)
        # decorate task
        if _agent is None:
            raise ValueError(f"Agent {alias_name} not found")
        return _agent.broker.task(**task_kwargs)(func)

    # Support @task and @task()
    return decorator if func is None else decorator(func)
