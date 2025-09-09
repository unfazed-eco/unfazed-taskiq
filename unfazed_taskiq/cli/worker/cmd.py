import asyncio
import logging
from typing import Optional, Sequence

from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.worker.args import WorkerArgs
from taskiq.cli.worker.run import run_worker
from unfazed_sentry import agent as sentry_agent
from unfazed.core import Unfazed
import asyncio
import typing as t


class WorkerCMD(TaskiqCMD):
    """Command to run workers."""

    short_help = "Helper to run workers"

    async def init_unfazed(self) -> None:
        self.unfazed = Unfazed()
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
        # setup sentry
        sentry_agent.setup()
        # setup worker
        wargs: WorkerArgs = WorkerArgs.from_cli(args)
        return run_worker(wargs)
