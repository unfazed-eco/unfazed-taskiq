import asyncio
import logging
from dataclasses import replace
from typing import Sequence

from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.scheduler.run import run_scheduler
from unfazed.core import Unfazed

from unfazed_taskiq.agent.handler import agent
from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

logger = logging.getLogger("unfazed.taskiq")


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
        parsed: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        async def _run_all_scheduler() -> None:
            tasks = []

            # Get all agent models with schedulers
            schedulers = {}
            for alias, agent_model in agent.storage.items():
                if agent_model.scheduler is not None:
                    schedulers[alias] = agent_model.scheduler

            # if scheduler_alias is not provided, run all schedulers
            if len(parsed.scheduler_alias) == 0:
                parsed.scheduler_alias = list(schedulers.keys())

            # init all schedulers
            for alias, scheduler_obj in schedulers.items():
                if alias in parsed.scheduler_alias:
                    event_parsed = replace(parsed, scheduler=scheduler_obj)
                    tasks.append(asyncio.create_task(run_scheduler(event_parsed)))

            # run all schedulers
            if tasks:
                await asyncio.gather(*tasks)

        asyncio.run(_run_all_scheduler())
