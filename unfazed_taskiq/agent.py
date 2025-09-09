import os
from typing import Optional

from unfazed.utils import import_setting
from taskiq import AsyncBroker, TaskiqScheduler

from .base import TaskiqAgent, agent
from .settings import UnfazedTaskiqSettings


_agent: Optional[TaskiqAgent] = None


def get_agent() -> TaskiqAgent:
    """
    interface for getting taskiq client

    Example:
        taskiq worker unfazed_taskiq.cli:broker
        taskiq worker unfazed_taskiq.cli:scheduler
    """

    global _agent

    if _agent is not None and _agent._ready:
        return _agent

    if not os.environ.get("UNFAZED_SETTINGS_MODULE"):
        raise ValueError("UNFAZED_SETTINGS_MODULE is not set")

    try:
        # extract settings from unfazed settings
        settings_kv = import_setting("UNFAZED_SETTINGS_MODULE")
    except ImportError as e:
        raise ImportError(f"Failed to import settings module: {e}")

    # extract broker settings
    taskiq_settings = settings_kv["UNFAZED_TASKIQ_SETTINGS"]

    try:
        settings: UnfazedTaskiqSettings = UnfazedTaskiqSettings.model_validate(
            taskiq_settings
        )
    except Exception as e:
        raise ValueError(f"Invalid settings configuration: {e}")

    agent.reset()
    agent.setup(settings)

    _agent = agent
    return agent


broker: AsyncBroker = get_agent().get_broker()
scheduler: TaskiqScheduler = get_agent().get_scheduler()
