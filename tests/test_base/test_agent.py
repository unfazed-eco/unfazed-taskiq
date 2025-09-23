"""
Unit tests for agent module.

This module contains tests for the agent module functionality,
covering get_agent function, environment variable handling, and global variables.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from taskiq import AsyncBroker, TaskiqScheduler

from unfazed_taskiq.base import TaskiqAgent
from unfazed_taskiq.settings import UnfazedTaskiqSettings


class TestAgentModule:
    """Test agent module functionality."""

    def test_get_agent_returns_cached_agent_when_ready(self) -> None:
        """Test get_agent returns cached agent when already ready."""
        # Arrange
        mock_agent = MagicMock(spec=TaskiqAgent)
        mock_agent._ready = True

        with patch("unfazed_taskiq.agent._agent", mock_agent):
            from unfazed_taskiq.agent import get_agent

            # Act
            result = get_agent()

            # Assert
            assert result is mock_agent

    def test_get_agent_initializes_agent_when_not_ready(self) -> None:
        """Test get_agent initializes agent when not ready."""
        # Arrange
        mock_settings = {
            "DEFAULT_TASKIQ_NAME": "default",
            "TASKIQ_CONFIG": {
                "default": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                    "RESULT": {
                        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
                        "OPTIONS": {
                            "redis_url": "redis://localhost:6379",
                        },
                    },
                },
            },
        }

        with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": "test_settings"}):
            with patch("unfazed_taskiq.agent.import_setting") as mock_import_setting:
                mock_import_setting.return_value = {
                    "UNFAZED_TASKIQ_SETTINGS": mock_settings
                }

                with patch("unfazed_taskiq.agent._agent", None):
                    with patch("unfazed_taskiq.agent.agent") as mock_agent:
                        mock_agent.reset = MagicMock()
                        mock_agent.setup = MagicMock()

                        from unfazed_taskiq.agent import get_agent

                        # Act
                        result = get_agent()

                        # Assert
                        assert result is mock_agent
                        mock_agent.reset.assert_called_once()
                        mock_agent.setup.assert_called_once()
                        assert isinstance(
                            mock_agent.setup.call_args[0][0], UnfazedTaskiqSettings
                        )

    def test_get_agent_handles_import_setting_error(self) -> None:
        """Test get_agent handles import_setting errors gracefully."""
        # Arrange
        with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": "test_settings"}):
            with patch("unfazed_taskiq.agent.import_setting") as mock_import_setting:
                mock_import_setting.side_effect = ImportError("Module not found")

                with patch("unfazed_taskiq.agent._agent", None):
                    from unfazed_taskiq.agent import get_agent

                    # Act & Assert
                    with pytest.raises(
                        ImportError, match="Failed to import settings module"
                    ):
                        get_agent()

    def test_get_agent_handles_invalid_settings(self) -> None:
        """Test get_agent handles invalid settings gracefully."""
        # Arrange
        invalid_settings = {"invalid": "data"}

        with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": "test_settings"}):
            with patch("unfazed_taskiq.agent.import_setting") as mock_import_setting:
                mock_import_setting.return_value = {
                    "UNFAZED_TASKIQ_SETTINGS": invalid_settings
                }

                with patch("unfazed_taskiq.agent._agent", None):
                    from unfazed_taskiq.agent import get_agent

                    # Act & Assert
                    with pytest.raises(
                        ValueError, match="Invalid settings configuration"
                    ):
                        get_agent()

    def test_get_agent_caches_agent_instance(self) -> None:
        """Test get_agent caches the agent instance."""
        # Arrange
        mock_settings = {
            "DEFAULT_TASKIQ_NAME": "default",
            "TASKIQ_CONFIG": {
                "default": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                },
            },
        }

        with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": "test_settings"}):
            with patch("unfazed_taskiq.agent.import_setting") as mock_import_setting:
                mock_import_setting.return_value = {
                    "UNFAZED_TASKIQ_SETTINGS": mock_settings
                }

                with patch("unfazed_taskiq.agent._agent", None):
                    with patch("unfazed_taskiq.agent.agent") as mock_agent:
                        mock_agent.reset = MagicMock()
                        mock_agent.setup = MagicMock()

                        from unfazed_taskiq.agent import get_agent

                        # Act - First call
                        result1 = get_agent()

                        # Act - Second call
                        result2 = get_agent()

                        # Assert
                        assert result1 is result2
                        assert result1 is mock_agent
                        # setup should only be called once due to caching
                        mock_agent.setup.assert_called_once()

    def test_global_variables_are_correct_types(self) -> None:
        """Test global variables broker and scheduler are correct types."""
        # Arrange
        mock_settings = {
            "DEFAULT_TASKIQ_NAME": "default",
            "TASKIQ_CONFIG": {
                "default": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                    "SCHEDULER": {
                        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
                        "SOURCES": [],
                    },
                },
            },
        }

        with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": "test_settings"}):
            with patch("unfazed_taskiq.agent.import_setting") as mock_import_setting:
                mock_import_setting.return_value = {
                    "UNFAZED_TASKIQ_SETTINGS": mock_settings
                }

                with patch("unfazed_taskiq.agent._agent", None):
                    with patch("unfazed_taskiq.agent.agent") as mock_agent:
                        mock_broker = MagicMock(spec=AsyncBroker)
                        mock_scheduler = MagicMock(spec=TaskiqScheduler)
                        mock_agent.get_broker.return_value = mock_broker
                        mock_agent.get_scheduler.return_value = mock_scheduler

                        # Act - Import and call get_agent to set up the global variables
                        from unfazed_taskiq.agent import get_agent

                        get_agent()  # This will set up the global variables

                        # Test that get_agent returns the correct agent
                        result_agent = get_agent()
                        result_broker = result_agent.get_broker()
                        result_scheduler = result_agent.get_scheduler()

                        # Assert
                        assert result_agent is mock_agent
                        assert result_broker is mock_broker
                        assert result_scheduler is mock_scheduler
                        assert isinstance(result_broker, AsyncBroker)
                        assert isinstance(result_scheduler, TaskiqScheduler)
                        mock_agent.get_broker.assert_called()
                        mock_agent.get_scheduler.assert_called()

    def test_get_agent_with_different_settings_modules(self) -> None:
        """Test get_agent works with different settings modules."""
        # Arrange
        mock_settings = {
            "DEFAULT_TASKIQ_NAME": "test",
            "TASKIQ_CONFIG": {
                "test": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                },
            },
        }

        test_modules = ["test_settings", "another_settings", "custom_settings"]

        for module_name in test_modules:
            with patch.dict(os.environ, {"UNFAZED_SETTINGS_MODULE": module_name}):
                with patch(
                    "unfazed_taskiq.agent.import_setting"
                ) as mock_import_setting:
                    mock_import_setting.return_value = {
                        "UNFAZED_TASKIQ_SETTINGS": mock_settings
                    }

                    with patch("unfazed_taskiq.agent._agent", None):
                        with patch("unfazed_taskiq.agent.agent") as mock_agent:
                            mock_agent.reset = MagicMock()
                            mock_agent.setup = MagicMock()

                            from unfazed_taskiq.agent import get_agent

                            # Act
                            result = get_agent()

                            # Assert
                            assert result is mock_agent
                            mock_import_setting.assert_called_with(
                                "UNFAZED_SETTINGS_MODULE"
                            )
