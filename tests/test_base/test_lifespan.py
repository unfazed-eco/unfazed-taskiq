"""
Unit tests for TaskiqLifeSpan class.

This module contains tests for the TaskiqLifeSpan class functionality,
covering initialization, startup, and shutdown operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from unfazed_taskiq.lifespan import TaskiqLifeSpan
from unfazed_taskiq.settings import Broker, TaskiqConfig, UnfazedTaskiqSettings


class TestTaskiqLifeSpan:
    """Test TaskiqLifeSpan functionality."""

    def test_taskiq_lifespan_init(self) -> None:
        """Test TaskiqLifeSpan initialization."""
        mock_unfazed = MagicMock()

        # Create a real UnfazedTaskiqSettings instance
        mock_taskiq_settings = UnfazedTaskiqSettings(
            DEFAULT_TASKIQ_NAME="default",
            TASKIQ_CONFIG={
                "default": TaskiqConfig(
                    BROKER=Broker(
                        BACKEND="taskiq.InMemoryBroker",
                        OPTIONS={},
                    ),
                ),
            },
        )

        with patch("unfazed_taskiq.lifespan.settings") as settings_mock:
            with patch("unfazed_taskiq.lifespan.agent") as agent_mock:
                settings_mock.__getitem__.return_value = mock_taskiq_settings

                lifespan = TaskiqLifeSpan(mock_unfazed)

                assert lifespan.unfazed is mock_unfazed
                assert lifespan.agent is agent_mock

                agent_mock.setup.assert_called_once()
                call_args = agent_mock.setup.call_args[0][0]
                assert isinstance(call_args, UnfazedTaskiqSettings)

    async def test_taskiq_lifespan_on_startup(self) -> None:
        """Test TaskiqLifeSpan on_startup method."""
        mock_unfazed = MagicMock()

        mock_taskiq_settings = UnfazedTaskiqSettings(
            DEFAULT_TASKIQ_NAME="default",
            TASKIQ_CONFIG={
                "default": TaskiqConfig(
                    BROKER=Broker(
                        BACKEND="taskiq.InMemoryBroker",
                        OPTIONS={},
                    ),
                ),
            },
        )

        with patch("unfazed_taskiq.lifespan.settings") as settings_mock:
            with patch("unfazed_taskiq.lifespan.agent") as agent_mock:
                settings_mock.__getitem__.return_value = mock_taskiq_settings
                agent_mock.startup = AsyncMock()

                lifespan = TaskiqLifeSpan(mock_unfazed)

                await lifespan.on_startup()

                agent_mock.startup.assert_called_once()

    async def test_taskiq_lifespan_on_shutdown(self) -> None:
        """Test TaskiqLifeSpan on_shutdown method."""
        mock_unfazed = MagicMock()

        mock_taskiq_settings = UnfazedTaskiqSettings(
            DEFAULT_TASKIQ_NAME="default",
            TASKIQ_CONFIG={
                "default": TaskiqConfig(
                    BROKER=Broker(
                        BACKEND="taskiq.InMemoryBroker",
                        OPTIONS={},
                    ),
                ),
            },
        )

        with patch("unfazed_taskiq.lifespan.settings") as settings_mock:
            with patch("unfazed_taskiq.lifespan.agent") as agent_mock:
                settings_mock.__getitem__.return_value = mock_taskiq_settings
                agent_mock.shutdown = AsyncMock()

                lifespan = TaskiqLifeSpan(mock_unfazed)

                await lifespan.on_shutdown()

                agent_mock.shutdown.assert_called_once()
