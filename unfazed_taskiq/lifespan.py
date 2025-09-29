from unfazed.core import Unfazed
from unfazed.lifespan import BaseLifeSpan

from unfazed_taskiq.agent.handler import agents


class TaskiqLifeSpan(BaseLifeSpan):
    def __init__(self, unfazed: Unfazed) -> None:
        self.unfazed = unfazed
        agents.setup()
        self.agents = agents

    async def on_startup(self) -> None:
        await self.agents.startup()

    async def on_shutdown(self) -> None:
        await self.agents.shutdown()
