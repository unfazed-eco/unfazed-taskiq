import os
from typing import Optional

from taskiq import AsyncBroker, TaskiqScheduler
from unfazed.utils import Storage, import_setting

from unfazed_taskiq.agent.model import TaskiqAgent
from unfazed_taskiq.settings import UnfazedTaskiqSettings


class AgentHandler(Storage[TaskiqAgent]):
    def __init__(self) -> None:
        super().__init__()
        self.default_alias_name: str = "default"  # Default fallback
        self._ready = False
        self.check_ready()

    def register(self, alias_name: str, agent: TaskiqAgent) -> None:
        if alias_name in self.storage:
            raise ValueError(f"Agent {alias_name} already registered")
        self.storage[alias_name] = agent

    def reset(self) -> None:
        self.clear()
        self._ready = False

    def setup(self) -> None:
        if not os.environ.get("UNFAZED_SETTINGS_MODULE"):
            raise ValueError("UNFAZED_SETTINGS_MODULE is not set")

        try:
            # extract settings from unfazed settings
            settings_kv = import_setting("UNFAZED_SETTINGS_MODULE")
        except ImportError as e:
            raise ImportError(f"Failed to import settings module: {e}")

        # extract broker settings
        taskiq_settings = settings_kv["UNFAZED_TASKIQ_SETTINGS"]
        self.default_alias_name = taskiq_settings.get("DEFAULT_TASKIQ_NAME", "default")
        try:
            taskiq_config_settings = UnfazedTaskiqSettings.model_validate(
                taskiq_settings
            )
        except Exception as e:
            raise ValueError(f"Invalid settings configuration: {e}")

        for alias_name, taskiq_config in taskiq_config_settings.taskiq_config.items():
            taskiq_agent: TaskiqAgent = TaskiqAgent.setup(alias_name, taskiq_config)
            self.register(alias_name, taskiq_agent)
        self._ready = True

    def check_ready(self) -> None:
        if not self._ready:
            self.reset()
            self.setup()

    def get_agent(self, alias_name: Optional[str]) -> Optional[TaskiqAgent]:
        """Get the agent by alias name"""
        if not self._ready:
            self.check_ready()
        _alias_name = self.default_alias_name if alias_name is None else alias_name
        return self.storage.get(_alias_name, None)

    @property
    def scheduler(self) -> TaskiqScheduler:
        """Get the default scheduler"""
        if not self._ready:
            self.check_ready()
        return self.storage[self.default_alias_name].scheduler

    @property
    def broker(self) -> AsyncBroker:
        """Get the default broker"""
        if not self._ready:
            self.check_ready()
        return self.storage[self.default_alias_name].broker

    async def startup(self) -> None:
        for agent_model in self.storage.values():
            await agent_model.startup()

    async def shutdown(self) -> None:
        for agent_model in self.storage.values():
            await agent_model.shutdown()


agents = AgentHandler()
scheduler = agents.scheduler
broker = agents.broker
