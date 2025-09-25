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

        with (
            patch("unfazed_taskiq.lifespan.settings") as mock_settings_obj,
            patch("unfazed_taskiq.lifespan.agent") as mock_agent,
        ):
            mock_settings_obj.__getitem__.return_value = mock_taskiq_settings

            # Create TaskiqLifeSpan instance
            lifespan = TaskiqLifeSpan(mock_unfazed)

            # Verify initialization
            assert lifespan.unfazed is mock_unfazed
            assert lifespan.agent is mock_agent

            # Verify agent.setup was called with correct settings
            mock_agent.setup.assert_called_once()
            call_args = mock_agent.setup.call_args[0][0]
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

        with (
            patch("unfazed_taskiq.lifespan.settings") as mock_settings_obj,
            patch("unfazed_taskiq.lifespan.agent") as mock_agent,
        ):
            mock_settings_obj.__getitem__.return_value = mock_taskiq_settings
            mock_agent.startup = AsyncMock()

            # Create TaskiqLifeSpan instance
            lifespan = TaskiqLifeSpan(mock_unfazed)

            # Call on_startup
            await lifespan.on_startup()

            # Verify agent.startup was called
            mock_agent.startup.assert_called_once()

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

        with (
            patch("unfazed_taskiq.lifespan.settings") as mock_settings_obj,
            patch("unfazed_taskiq.lifespan.agent") as mock_agent,
        ):
            mock_settings_obj.__getitem__.return_value = mock_taskiq_settings
            mock_agent.shutdown = AsyncMock()

            # Create TaskiqLifeSpan instance
            lifespan = TaskiqLifeSpan(mock_unfazed)

            # Call on_shutdown
            await lifespan.on_shutdown()

            # Verify agent.shutdown was called
            mock_agent.shutdown.assert_called_once()
