"""
Unit tests for middleware module.

This module contains tests for the UnfazedTaskiqExceptionMiddleware functionality,
covering error handling, logging, and Sentry integration.
"""

from unittest.mock import MagicMock, patch

import pytest
from taskiq import TaskiqMessage, TaskiqResult

from unfazed_taskiq.middleware import UnfazedTaskiqExceptionMiddleware


class TestUnfazedTaskiqExceptionMiddleware:
    """Test UnfazedTaskiqExceptionMiddleware functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.middleware = UnfazedTaskiqExceptionMiddleware()
        self.mock_message = MagicMock(spec=TaskiqMessage)
        self.mock_message.task_name = "test_task"
        self.mock_message.args = ("arg1", "arg2")
        self.mock_message.kwargs = {"key1": "value1", "key2": "value2"}

        self.mock_result = MagicMock(spec=TaskiqResult)
        self.test_exception = ValueError("Test error message")

    async def test_on_error_calls_capture_exception(self) -> None:
        """Test that on_error calls capture_exception with correct parameters."""
        with patch("unfazed_taskiq.middleware.capture_exception") as mock_capture:
            await self.middleware.on_error(
                self.mock_message, self.mock_result, self.test_exception
            )

            mock_capture.assert_called_once_with(
                self.test_exception, result=self.mock_result, message=self.mock_message
            )

    @pytest.mark.asyncio
    async def test_on_error_logs_error_with_correct_format(self) -> None:
        """Test that on_error logs error with correct format and extra data."""
        with patch("unfazed_taskiq.middleware.capture_exception"):
            with patch("unfazed_taskiq.middleware.log") as mock_logger:
                await self.middleware.on_error(
                    self.mock_message, self.mock_result, self.test_exception
                )

                # Verify error log was called
                mock_logger.error.assert_called_once()

                # Get the logged message and extra data
                call_args = mock_logger.error.call_args
                logged_message = call_args[0][0]
                extra_data = call_args[1]["extra"]

                # Verify message format
                expected_message = (
                    f"Task '{self.mock_message.task_name}' failed with "
                    f"{type(self.test_exception).__name__}: {self.test_exception}"
                )
                assert logged_message == expected_message

                # Verify extra data contains all required fields
                assert extra_data["task_name"] == self.mock_message.task_name
                assert extra_data["task_args"] == self.mock_message.args
                assert extra_data["task_kwargs"] == self.mock_message.kwargs
                assert (
                    extra_data["exception_type"] == type(self.test_exception).__name__
                )
                assert extra_data["exception"] == str(self.test_exception)
                assert "traceback" in extra_data
