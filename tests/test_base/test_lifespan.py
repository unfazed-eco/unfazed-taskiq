"""
Unit tests for TaskiqLifeSpan class.

This module contains tests for the TaskiqLifeSpan class functionality,
covering initialization, startup, and shutdown operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from unfazed_taskiq.lifespan import TaskiqLifeSpan


class TestTaskiqLifeSpan:
    """Test TaskiqLifeSpan functionality."""

    def test_taskiq_lifespan_init(self) -> None:
        """Test TaskiqLifeSpan initialization."""
        mock_unfazed = MagicMock()

        with patch("unfazed_taskiq.lifespan.agents") as agent_mock:
            agent_mock.setup.return_value = None

            lifespan = TaskiqLifeSpan(mock_unfazed)

            assert lifespan.unfazed is mock_unfazed
            assert lifespan.agents is agent_mock

            agent_mock.setup.assert_called_once_with()

    async def test_taskiq_lifespan_on_startup(self) -> None:
        """Test TaskiqLifeSpan on_startup method."""
        mock_unfazed = MagicMock()

        with patch("unfazed_taskiq.lifespan.agents") as agent_mock:
            agent_mock.setup.return_value = None
            agent_mock.startup = AsyncMock()

            lifespan = TaskiqLifeSpan(mock_unfazed)

            await lifespan.on_startup()

            agent_mock.startup.assert_awaited_once_with()

    async def test_taskiq_lifespan_on_shutdown(self) -> None:
        """Test TaskiqLifeSpan on_shutdown method."""
        mock_unfazed = MagicMock()

        with patch("unfazed_taskiq.lifespan.agents") as agent_mock:
            agent_mock.setup.return_value = None
            agent_mock.shutdown = AsyncMock()

            lifespan = TaskiqLifeSpan(mock_unfazed)

            await lifespan.on_shutdown()

            agent_mock.shutdown.assert_awaited_once_with()
