import os
import threading
from typing import Optional

from taskiq import AsyncBroker, TaskiqScheduler
from unfazed.utils import import_setting

from .base import TaskiqAgent, agent
from .settings import UnfazedTaskiqSettings

_agent: Optional[TaskiqAgent] = None
_agent_lock = threading.Lock()


def _initialize_agent() -> TaskiqAgent:
    """
    Initialize the TaskiqAgent with settings from environment.

    This function handles the actual initialization logic including:
    - Loading settings from UNFAZED_SETTINGS_MODULE
    - Validating configuration
    - Setting up the agent

    Returns:
        TaskiqAgent: The initialized agent instance
    """
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

    return agent


def get_agent() -> TaskiqAgent:
    """
    Get the TaskiqAgent instance, initializing it if necessary.

    This function uses double-checked locking pattern for thread safety.
    If the agent is already initialized and ready, it returns immediately.
    Otherwise, it initializes the agent in a thread-safe manner.

    Returns:
        TaskiqAgent: The agent instance
    """
    global _agent

    # First check (without lock, fast path)
    if _agent is not None and _agent._ready:
        return _agent

    # Double-checked locking pattern for thread safety
    with _agent_lock:
        # Second check (with lock, prevent duplicate initialization)
        if _agent is not None and _agent._ready:
            return _agent

        # Initialize the agent
        _agent = _initialize_agent()
        return _agent


broker: AsyncBroker = get_agent().get_broker()
scheduler: TaskiqScheduler = get_agent().get_scheduler()
