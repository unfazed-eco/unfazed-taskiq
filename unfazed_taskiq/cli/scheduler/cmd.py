import asyncio
from typing import Sequence

from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.scheduler.args import SchedulerArgs
from taskiq.cli.scheduler.run import run_scheduler
from unfazed.core import Unfazed


class SchedulerCMD(TaskiqCMD):
    """Command for taskiq scheduler."""

    short_help = "Run task scheduler"

    async def init_unfazed(self) -> None:
        self.unfazed = Unfazed()
        await self.unfazed.setup()

    def exec(self, args: Sequence[str]) -> None:
        """
        Run task scheduler.

        This function starts scheduler function.

        It periodically loads schedule for tasks
        and executes them.

        :param args: CLI arguments.
        """

        # setup unfazed
        asyncio.run(self.init_unfazed())
        # setup scheduler
        parsed: SchedulerArgs = SchedulerArgs.from_cli(args)
        asyncio.run(run_scheduler(parsed))
