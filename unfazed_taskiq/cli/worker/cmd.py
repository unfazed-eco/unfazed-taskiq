import asyncio
from typing import Optional, Sequence

from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.worker.args import WorkerArgs
from taskiq.cli.worker.run import run_worker
from unfazed.core import Unfazed


class WorkerCMD(TaskiqCMD):
    """Command to run workers."""

    short_help = "Helper to run workers"

    async def init_unfazed(self) -> None:
        self.unfazed = Unfazed(silent=True)
        await self.unfazed.setup()

    def exec(self, args: Sequence[str]) -> Optional[int]:
        """
        Start worker process.

        Worker process creates several small
        processes in which tasks are actually processed.

        :param args: CLI arguments.
        :returns: status code.
        """
        # setup unfazed
        asyncio.run(self.init_unfazed())
        # setup worker
        wargs: WorkerArgs = WorkerArgs.from_cli(args)
        return run_worker(wargs)
