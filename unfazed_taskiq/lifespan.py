from unfazed.conf import settings
from unfazed.core import Unfazed
from unfazed.lifespan import BaseLifeSpan

from .base import agent
from .settings import UnfazedTaskiqSettings


class TaskiqLifeSpan(BaseLifeSpan):
    def __init__(self, unfazed: Unfazed) -> None:
        self.unfazed = unfazed
        taskiq_settings: UnfazedTaskiqSettings = settings["UNFAZED_TASKIQ_SETTINGS"]

        agent.setup(taskiq_settings)
        self.agent = agent

    async def on_startup(self) -> None:
        await self.agent.startup()

    async def on_shutdown(self) -> None:
        await self.agent.shutdown()
