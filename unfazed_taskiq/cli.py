import os

from unfazed.utils import import_setting

from .base import TaskiqAgent
from .settings import UnfazedTaskiqSettings


def get_broker():
    """
    interface for getting broker from taskiq client

    Example:
        taskiq worker unfazed_taskiq.cli:broker
    """

    if not os.environ.get("UNFAZED_SETTINGS"):
        raise ValueError("UNFAZED_SETTINGS is not set")

    # extract settings from unfazed settings
    settings_kv = import_setting("UNFAZED_SETTINGS")

    # extract broker settings
    broker_settings = settings_kv["UNFAZED_TASKIQ_SETTINGS"]

    settings = UnfazedTaskiqSettings.model_validate(broker_settings)

    agent = TaskiqAgent()
    agent.setup(settings)

    return agent.broker


broker = get_broker()
