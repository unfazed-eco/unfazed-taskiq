import asyncio
from dataclasses import replace
from typing import Sequence

from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.scheduler.run import run_scheduler
from unfazed.core import Unfazed

from unfazed_taskiq.agent.handler import agents
from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs


class SchedulerCMD(TaskiqCMD):
    """Command for taskiq scheduler."""

    short_help = "Run task scheduler"

    async def init_unfazed(self) -> None:
        self.unfazed = Unfazed(silent=True)
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
            for alias, agent_model in agents.storage.items():
                if agent_model.scheduler is not None:
                    schedulers[alias] = agent_model.scheduler

            # if alias_name is not provided, run all schedulers
            if len(parsed.alias_name) == 0:
                parsed.alias_name = list(schedulers.keys())

            # init all schedulers
            for alias, scheduler_obj in schedulers.items():
                if alias in parsed.alias_name:
                    event_parsed = replace(parsed, scheduler=scheduler_obj)
                    tasks.append(asyncio.create_task(run_scheduler(event_parsed)))

            # run all schedulers
            if tasks:
                await asyncio.gather(*tasks)

        asyncio.run(_run_all_scheduler())
