from unfazed.core import Unfazed
from unfazed.lifespan import BaseLifeSpan

from .base import agent


class TaskiqLifeSpan(BaseLifeSpan):
    def __init__(self, unfazed: Unfazed) -> None:
        self.unfazed = unfazed
        agent.setup()
        self.agent = agent

    async def on_startup(self) -> None:
        await self.agent.broker.startup()

    async def on_shutdown(self) -> None:
        await self.agent.broker.shutdown()
