import os

from unfazed.utils import import_setting

from .base import TaskiqAgent, agent
from .settings import UnfazedTaskiqSettings


def get_agent() -> TaskiqAgent:
    """
    interface for getting taskiq client

    Example:
        taskiq worker unfazed_taskiq.cli:broker
        taskiq worker unfazed_taskiq.cli:scheduler
    """

    if not os.environ.get("UNFAZED_SETTINGS_MODULE"):
        raise ValueError("UNFAZED_SETTINGS_MODULE is not set")

    # extract settings from unfazed settings
    settings_kv = import_setting("UNFAZED_SETTINGS_MODULE")

    # extract broker settings
    taskiq_settings = settings_kv["UNFAZED_TASKIQ_SETTINGS"]

    settings = UnfazedTaskiqSettings.model_validate(taskiq_settings)

    agent.reset()
    agent.setup(settings)

    return agent


_agent: TaskiqAgent = get_agent()


broker = _agent.broker

scheduler = _agent.scheduler
