import asyncio
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock, patch

from unfazed_taskiq.cli.worker.cmd import WorkerCMD


class TestWorkerCMD(object):
    def test_init_unfazed(self) -> None:
        """Test init_unfazed method."""
        cmd = WorkerCMD()

        with patch("unfazed_taskiq.cli.worker.cmd.Unfazed") as mock_unfazed:
            mock_unfazed_instance = Mock()
            mock_unfazed_instance.setup = AsyncMock(return_value=None)
            mock_unfazed.return_value = mock_unfazed_instance

            # Test the async method using asyncio.run
            # Create a new event loop to avoid conflicts
            asyncio.run(cmd.init_unfazed())

            # Verify Unfazed was instantiated
            mock_unfazed.assert_called_once()
            # Verify setup was called
            mock_unfazed_instance.setup.assert_called_once()
            # Verify unfazed attribute was set
            assert cmd.unfazed == mock_unfazed_instance

    def test_exec_success(self) -> None:
        """Test exec method with successful execution."""
        cmd = WorkerCMD()
        args = ["test_broker", "test_module"]

        with (
            patch("unfazed_taskiq.cli.worker.cmd.WorkerArgs") as mock_worker_args,
            patch("unfazed_taskiq.cli.worker.cmd.asyncio.run") as mock_asyncio_run,
            patch("unfazed_taskiq.cli.worker.cmd.run_worker") as mock_run_worker,
        ):
            # Setup mocks
            mock_worker_args_instance = Mock()
            mock_worker_args.from_cli.return_value = mock_worker_args_instance
            mock_run_worker.return_value = 0

            # Mock asyncio.run to properly handle coroutines
            def mock_asyncio_run_func(coro: Any) -> Any:
                if asyncio.iscoroutine(coro):
                    # Create a new event loop and run the coroutine
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(coro)
                    finally:
                        loop.close()
                return coro

            mock_asyncio_run.side_effect = mock_asyncio_run_func

            # Call exec
            result: Optional[int] = cmd.exec(args)

            # Verify calls
            mock_asyncio_run.assert_called_once()
            mock_worker_args.from_cli.assert_called_once_with(args)
            mock_run_worker.assert_called_once_with(mock_worker_args_instance)

            # Verify return value
            assert result == 0
