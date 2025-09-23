from unittest.mock import Mock, patch

import pytest

from unfazed_taskiq.cli.scheduler.cmd import SchedulerCMD


class TestSchedulerCMD(object):
    def test_scheduler_cmd_init(self) -> None:
        """Test SchedulerCMD initialization."""
        cmd = SchedulerCMD()
        assert cmd is not None
        assert cmd.short_help == "Run task scheduler"

    @pytest.mark.asyncio
    async def test_init_unfazed(self) -> None:
        """Test init_unfazed method."""
        cmd = SchedulerCMD()

        with patch("unfazed_taskiq.cli.scheduler.cmd.Unfazed") as mock_unfazed:
            mock_unfazed_instance = Mock()
            # Make setup method a Mock that returns a coroutine
            mock_setup = Mock()

            async def async_setup() -> None:
                pass

            mock_setup.return_value = async_setup()
            mock_unfazed_instance.setup = mock_setup
            mock_unfazed.return_value = mock_unfazed_instance

            await cmd.init_unfazed()
            # Verify Unfazed was instantiated
            mock_unfazed.assert_called_once()
            # Verify setup was called
            mock_unfazed_instance.setup.assert_called_once()
            # Verify unfazed attribute was set
            assert cmd.unfazed == mock_unfazed_instance

    def test_exec_success_with_scheduler_alias(self) -> None:
        """Test exec method with specific scheduler aliases."""
        cmd = SchedulerCMD()
        args = [
            "unfazed_taskiq.cli:get_agent",
            "test_module",
            "--scheduler-alias",
            "default",
        ]

        with (
            patch("unfazed_taskiq.cli.scheduler.cmd.Unfazed") as mock_unfazed,
            patch(
                "unfazed_taskiq.cli.scheduler.cmd.SchedulerEventArgs"
            ) as mock_scheduler_args,
            patch("unfazed_taskiq.cli.scheduler.cmd.get_agent") as mock_get_agent,
            patch("unfazed_taskiq.cli.scheduler.cmd.run_scheduler"),
        ):
            # Setup Unfazed mock
            mock_unfazed_instance = Mock()

            async def mock_setup() -> None:
                pass

            mock_unfazed_instance.setup = mock_setup
            mock_unfazed.return_value = mock_unfazed_instance
            # Setup mocks
            mock_parsed = Mock()
            mock_parsed.scheduler_alias = ["default"]
            mock_scheduler_args.from_cli.return_value = mock_parsed

            mock_agent = Mock()
            mock_agent._schedulers = {"default": Mock(), "other": Mock()}
            mock_get_agent.return_value = mock_agent

            # Call exec
            cmd.exec(args)

            # Verify calls
            mock_scheduler_args.from_cli.assert_called_once_with(args)
            mock_get_agent.assert_called_once()

    def test_exec_success_without_scheduler_alias(self) -> None:
        """Test exec method without scheduler aliases (runs all schedulers)."""
        cmd = SchedulerCMD()
        args = ["unfazed_taskiq.cli:get_agent", "test_module"]

        with (
            patch("unfazed_taskiq.cli.scheduler.cmd.Unfazed") as mock_unfazed,
            patch(
                "unfazed_taskiq.cli.scheduler.cmd.SchedulerEventArgs"
            ) as mock_scheduler_args,
            patch("unfazed_taskiq.cli.scheduler.cmd.get_agent") as mock_get_agent,
            patch("unfazed_taskiq.cli.scheduler.cmd.run_scheduler"),
        ):
            # Setup Unfazed mock
            mock_unfazed_instance = Mock()

            async def mock_setup() -> None:
                pass

            mock_unfazed_instance.setup = mock_setup
            mock_unfazed.return_value = mock_unfazed_instance
            # Setup mocks
            mock_parsed = Mock()
            mock_parsed.scheduler_alias = []  # Empty aliases
            mock_scheduler_args.from_cli.return_value = mock_parsed

            mock_agent = Mock()
            mock_agent._schedulers = {"default": Mock(), "other": Mock()}
            mock_get_agent.return_value = mock_agent

            # Call exec
            cmd.exec(args)

            # Verify calls
            mock_scheduler_args.from_cli.assert_called_once_with(args)
            mock_get_agent.assert_called_once()


class TestSchedulerArgs(object):
    def test_scheduler_event_args_init(self) -> None:
        """Test SchedulerEventArgs initialization."""
        from taskiq.cli.common_args import LogLevel

        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        # Test with minimal args
        args = SchedulerEventArgs(scheduler="test.scheduler", modules=["test.module"])
        assert args.scheduler == "test.scheduler"
        assert args.modules == ["test.module"]
        assert args.log_level == LogLevel.INFO.name
        assert args.configure_logging
        assert not args.fs_discover
        assert args.tasks_pattern == ("**/tasks.py",)
        assert not args.skip_first_run
        assert args.update_interval is None
        assert args.scheduler_alias == ()

    def test_scheduler_event_args_with_all_params(self) -> None:
        """Test SchedulerEventArgs with all parameters."""
        from taskiq.cli.common_args import LogLevel

        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = SchedulerEventArgs(
            scheduler="test.scheduler",
            modules=["test.module1", "test.module2"],
            log_level=LogLevel.DEBUG.name,
            configure_logging=False,
            fs_discover=True,
            tasks_pattern=("**/tasks.py", "**/jobs.py"),
            skip_first_run=True,
            update_interval=30,
            scheduler_alias=("default", "worker"),
        )

        assert args.scheduler == "test.scheduler"
        assert args.modules == ["test.module1", "test.module2"]
        assert args.log_level == LogLevel.DEBUG.name
        assert not args.configure_logging
        assert args.fs_discover
        assert args.tasks_pattern == ("**/tasks.py", "**/jobs.py")
        assert args.skip_first_run
        assert args.update_interval == 30
        assert args.scheduler_alias == ("default", "worker")

    def test_from_cli_minimal_args(self) -> None:
        """Test from_cli with minimal arguments."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = ["test.scheduler", "test.module"]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        assert result.scheduler == "test.scheduler"
        assert result.modules == ["test.module"]
        assert result.log_level == "INFO"
        assert result.configure_logging
        assert not result.fs_discover
        assert result.tasks_pattern == ["**/tasks.py"]
        assert not result.skip_first_run
        assert result.update_interval is None
        assert result.scheduler_alias == []

    def test_from_cli_with_all_options(self) -> None:
        """Test from_cli with all command line options."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = [
            "test.scheduler",
            "test.module1",
            "test.module2",
            "--fs-discover",
            "--tasks-pattern",
            "**/tasks.py",
            "--tasks-pattern",
            "**/jobs.py",
            "--log-level",
            "DEBUG",
            "--no-configure-logging",
            "--skip-first-run",
            "--update-interval",
            "60",
            "--scheduler-alias",
            "default",
            "--scheduler-alias",
            "worker",
        ]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        assert result.scheduler == "test.scheduler"
        assert result.modules == ["test.module1", "test.module2"]
        assert result.log_level == "DEBUG"
        assert not result.configure_logging
        assert result.fs_discover
        assert result.tasks_pattern == ["**/tasks.py", "**/jobs.py"]
        assert result.skip_first_run
        assert result.update_interval == 60
        assert result.scheduler_alias == ["default", "worker"]

    def test_from_cli_with_short_options(self) -> None:
        """Test from_cli with short command line options."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = [
            "test.scheduler",
            "test.module",
            "-fsd",
            "-tp",
            "**/custom_tasks.py",
            "-sa",
            "default",
        ]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        assert result.scheduler == "test.scheduler"
        assert result.modules == ["test.module"]
        assert result.fs_discover
        assert result.tasks_pattern == ["**/custom_tasks.py"]
        assert result.scheduler_alias == ["default"]

    def test_from_cli_with_no_modules(self) -> None:
        """Test from_cli with no modules specified."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = ["test.scheduler"]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        assert result.scheduler == "test.scheduler"
        assert result.modules == []

    def test_from_cli_with_multiple_tasks_patterns(self) -> None:
        """Test from_cli with multiple tasks patterns."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = [
            "test.scheduler",
            "test.module",
            "--tasks-pattern",
            "**/tasks.py",
            "--tasks-pattern",
            "**/jobs.py",
            "--tasks-pattern",
            "**/cron.py",
        ]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        # Should remove the first default pattern
        assert result.tasks_pattern == ["**/tasks.py", "**/jobs.py", "**/cron.py"]

    def test_from_cli_with_single_tasks_pattern(self) -> None:
        """Test from_cli with single tasks pattern (should keep default)."""
        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        args = [
            "test.scheduler",
            "test.module",
            "--tasks-pattern",
            "**/custom_tasks.py",
        ]
        result: SchedulerEventArgs = SchedulerEventArgs.from_cli(args)

        # Should keep the default pattern
        assert result.tasks_pattern == ["**/custom_tasks.py"]

    def test_dataclass_replace(self) -> None:
        """Test dataclass replace functionality."""
        from dataclasses import replace

        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        # Create initial instance
        original = SchedulerEventArgs(
            scheduler="original.scheduler",
            modules=["original.module"],
            log_level="INFO",
            configure_logging=True,
            fs_discover=False,
            tasks_pattern=["**/tasks.py"],
            skip_first_run=False,
            update_interval=None,
            scheduler_alias=(),
        )

        # Test replacing single field
        updated = replace(original, log_level="DEBUG")
        assert updated.scheduler == "original.scheduler"
        assert updated.modules == ["original.module"]
        assert updated.log_level == "DEBUG"  # Changed
        assert updated.configure_logging
        assert not updated.fs_discover
        assert updated.tasks_pattern == ["**/tasks.py"]
        assert not updated.skip_first_run
        assert updated.update_interval is None
        assert updated.scheduler_alias == ()

        # Test replacing multiple fields
        updated2 = replace(
            original,
            scheduler="new.scheduler",
            modules=["new.module1", "new.module2"],
            log_level="WARNING",
            configure_logging=False,
            fs_discover=True,
            tasks_pattern=["**/custom_tasks.py"],
            skip_first_run=True,
            update_interval=120,
            scheduler_alias=("worker", "scheduler"),
        )

        assert updated2.scheduler == "new.scheduler"
        assert updated2.modules == ["new.module1", "new.module2"]
        assert updated2.log_level == "WARNING"
        assert not updated2.configure_logging
        assert updated2.fs_discover
        assert updated2.tasks_pattern == ["**/custom_tasks.py"]
        assert updated2.skip_first_run
        assert updated2.update_interval == 120
        assert updated2.scheduler_alias == ("worker", "scheduler")

        # Test that original is unchanged
        assert original.scheduler == "original.scheduler"
        assert original.log_level == "INFO"
        assert original.configure_logging

        # Test replacing with None values
        updated3 = replace(original, update_interval=None, scheduler_alias=())
        assert updated3.update_interval is None
        assert updated3.scheduler_alias == ()

        # Test replacing with empty collections
        updated4 = replace(original, modules=[], tasks_pattern=[], scheduler_alias=())
        assert updated4.modules == []
        assert updated4.tasks_pattern == []
        assert updated4.scheduler_alias == ()

    def test_dataclass_fields(self) -> None:
        """Test that SchedulerEventArgs has correct dataclass fields."""
        import dataclasses

        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        fields = dataclasses.fields(SchedulerEventArgs)
        field_names = [field.name for field in fields]

        expected_fields = [
            "scheduler",
            "modules",
            "log_level",
            "configure_logging",
            "fs_discover",
            "tasks_pattern",
            "skip_first_run",
            "update_interval",
            "scheduler_alias",
        ]

        for field_name in expected_fields:
            assert field_name in field_names

    def test_inheritance_from_scheduler_args(self) -> None:
        """Test that SchedulerEventArgs inherits from SchedulerArgs."""
        from taskiq.cli.scheduler.args import SchedulerArgs

        from unfazed_taskiq.cli.scheduler.args import SchedulerEventArgs

        assert issubclass(SchedulerEventArgs, SchedulerArgs)

        # Test that it can be used as SchedulerArgs
        args = SchedulerEventArgs(scheduler="test", modules=[])
        assert isinstance(args, SchedulerArgs)
