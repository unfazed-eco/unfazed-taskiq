import asyncio
import copy
from math import log
import traceback
from typing import Sequence
from dataclasses import replace
from taskiq import task
from taskiq.abc.cmd import TaskiqCMD
from taskiq.cli.scheduler.run import run_scheduler
from unfazed.core import Unfazed
from importlib import import_module

from unfazed_sentry import capture_exception
from unfazed_taskiq.base import TaskiqAgent
from unfazed_taskiq.agent import get_agent

from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs
from logging import getLogger

logger = getLogger(__name__)


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

        async def _run_all_scheduler():
            agent: TaskiqAgent = get_agent()
            tasks = []
            try:
                # if scheduler_alias is not provided, run all schedulers
                if len(parsed.scheduler_alias) == 0:
                    parsed.scheduler_alias = list(agent._schedulers.keys())

                # init all schedulers
                for alias, scheduler_obj in agent._schedulers.items():
                    if alias in parsed.scheduler_alias:
                        event_parsed = replace(parsed, scheduler=scheduler_obj)
                        tasks.append(asyncio.create_task(run_scheduler(event_parsed)))

                # run all schedulers
                if tasks:
                    await asyncio.gather(*tasks)
            except Exception as e:
                capture_exception(e)
                logger.error(f"Failed to start scheduler: {traceback.format_exc()}")

        asyncio.run(_run_all_scheduler())
