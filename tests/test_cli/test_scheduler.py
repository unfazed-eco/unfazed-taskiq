from dataclasses import replace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from taskiq.cli.common_args import LogLevel

from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs
from unfazed_taskiq.cli.scheduler.cmd import SchedulerCMD


class TestSchedulerCMD:
    def test_short_help(self) -> None:
        assert SchedulerCMD().short_help == "Run task scheduler"

    @pytest.mark.asyncio
    async def test_init_unfazed(self) -> None:
        cmd = SchedulerCMD()
        unfazed = AsyncMock()
        with patch("unfazed_taskiq.cli.scheduler.cmd.Unfazed", return_value=unfazed):
            await cmd.init_unfazed()
        unfazed.setup.assert_awaited_once()
        assert cmd.unfazed is unfazed

    def _run_exec(
        self, alias_name: list[str] | None, storage: dict[str, Any]
    ) -> MagicMock:
        cmd = SchedulerCMD()
        args = ["module", "pkg"] + (
            [] if alias_name is None else ["--scheduler-alias", *alias_name]
        )
        parsed = SchedulerEventArgs(
            scheduler="scheduler.path",
            modules=["pkg"],
            alias_name=[] if alias_name is None else alias_name,
        )
        run_spy = AsyncMock()
        agents = {alias: MagicMock(scheduler=sched) for alias, sched in storage.items()}
        with (
            patch("unfazed_taskiq.cli.scheduler.cmd.Unfazed", return_value=AsyncMock()),
            patch(
                "unfazed_taskiq.cli.scheduler.cmd.SchedulerEventArgs.from_cli",
                return_value=parsed,
            ),
            patch("unfazed_taskiq.cli.scheduler.cmd.agents.storage", agents),
            patch("unfazed_taskiq.cli.scheduler.cmd.run_scheduler", run_spy),
            patch("asyncio.create_task", side_effect=lambda coro: coro),
        ):
            cmd.exec(args)
        return run_spy

    def test_exec_with_alias(self) -> None:
        run_spy = self._run_exec(["alpha"], {"alpha": AsyncMock(), "beta": AsyncMock()})
        assert run_spy.await_count == 1

    def test_exec_without_alias(self) -> None:
        run_spy = self._run_exec(None, {"alpha": AsyncMock(), "beta": AsyncMock()})
        assert run_spy.await_count == 2


class TestSchedulerEventArgs:
    def test_defaults(self) -> None:
        args = SchedulerEventArgs(scheduler="path", modules=["pkg"])
        assert args.log_level == LogLevel.INFO.name
        assert args.tasks_pattern == ("**/tasks.py",)

    def test_override(self) -> None:
        args = SchedulerEventArgs(
            scheduler="path",
            modules=["p1", "p2"],
            log_level=LogLevel.DEBUG.name,
            configure_logging=False,
            fs_discover=True,
            tasks_pattern=("**/tasks.py", "**/jobs.py"),
            skip_first_run=True,
            update_interval=10,
            alias_name=("alpha",),
        )
        assert not args.configure_logging
        assert args.alias_name == ("alpha",)

    def test_from_cli_parsing(self) -> None:
        args = SchedulerEventArgs.from_cli(
            [
                "scheduler",
                "module",
                "--fs-discover",
                "--tasks-pattern",
                "**/jobs.py",
                "--log-level",
                "DEBUG",
                "--no-configure-logging",
                "--skip-first-run",
                "--update-interval",
                "30",
                "--alias-name",
                "alpha",
            ]
        )
        assert args.modules == ["module"]
        assert args.tasks_pattern == ["**/jobs.py"]
        assert args.alias_name == ["alpha"]
        assert args.update_interval == 30

    def test_replace(self) -> None:
        original = SchedulerEventArgs(scheduler="a", modules=["m"])
        updated = replace(original, log_level=LogLevel.WARNING.name, alias_name=("x",))
        assert updated.log_level == LogLevel.WARNING.name
        assert original.log_level == LogLevel.INFO.name
        assert updated.alias_name == ("x",)
