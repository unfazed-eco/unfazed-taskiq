"""
Unit tests for decorators, registry, and schema modules.

This module contains tests for the task decorator functionality,
registry service, and schema models.
"""

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from unfazed_taskiq.decorators import task
from unfazed_taskiq.registry import RegistryService, rs
from unfazed_taskiq.schema.registry import RegistryTask, RegistryTaskParam


class TestRegistryTaskParam:
    """Test RegistryTaskParam model."""

    def test_registry_task_param_creation(self) -> None:
        """Test RegistryTaskParam model creation with all fields."""
        param = RegistryTaskParam(
            name="test_param", hint_type=str, required=True, default=None
        )

        assert param.name == "test_param"
        assert param.hint_type is str
        assert param.required is True
        assert param.default is None


class TestRegistryTask:
    """Test RegistryTask model."""

    def test_registry_task_creation(self) -> None:
        """Test RegistryTask model creation."""
        params = [
            RegistryTaskParam(name="arg1", hint_type=str, required=True, default=None),
            RegistryTaskParam(name="arg2", hint_type=int, required=False, default=0),
        ]

        task = RegistryTask(
            name="test_task",
            broker_name="default",
            params=params,
            docs="Test task documentation",
            schedule=None,
        )

        assert task.name == "test_task"
        assert task.broker_name == "default"
        assert len(task.params) == 2
        assert task.docs == "Test task documentation"
        assert task.schedule is None


class TestRegistryService:
    """Test RegistryService functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.registry = RegistryService()

    def test_register_and_get_task(self) -> None:
        """Test task registration and retrieval."""
        task = RegistryTask(
            name="test_task",
            broker_name="default",
            params=[],
            docs="Test task",
            schedule=None,
        )

        # Test successful registration
        self.registry.register("test.module.test_task", task)
        assert "test.module.test_task" in self.registry.tasks
        assert self.registry.tasks["test.module.test_task"] == task

        # Test getting existing task
        retrieved_task = self.registry.get("test.module.test_task")
        assert retrieved_task == task

        # Test getting non-existent task
        result = self.registry.get("nonexistent.task")
        assert result is None

    def test_register_duplicate_task_raises_error(self) -> None:
        """Test that registering duplicate task raises ValueError."""
        task1 = RegistryTask(
            name="task1",
            broker_name="default",
            params=[],
            docs="First task",
            schedule=None,
        )
        task2 = RegistryTask(
            name="task2",
            broker_name="default",
            params=[],
            docs="Second task",
            schedule=None,
        )

        self.registry.register("test.module.task", task1)

        with pytest.raises(
            ValueError, match="Task test.module.task already registered"
        ):
            self.registry.register("test.module.task", task2)

    def test_filter_path(self) -> None:
        """Test filter_path functionality."""
        task1 = RegistryTask(
            name="math_task", broker_name="math", params=[], docs=None, schedule=None
        )
        task2 = RegistryTask(
            name="string_task",
            broker_name="string",
            params=[],
            docs=None,
            schedule=None,
        )

        self.registry.register("math.module.task1", task1)
        self.registry.register("string.module.task2", task2)

        # Test filter without keyword
        all_results = self.registry.filter_path()
        assert len(all_results) == 2
        assert task1 in all_results
        assert task2 in all_results

        # Test filter with keyword
        math_results = self.registry.filter_path("math")
        assert len(math_results) == 1
        assert task1 in math_results
        assert task2 not in math_results


class TestTaskDecorator:
    """Test task decorator functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        # Reset registry before each test
        rs.tasks.clear()

    def test_task_decorator_basic_functionality(self) -> None:
        """Test basic task decorator functionality."""
        with patch("unfazed_taskiq.decorators.get_agent") as mock_get_agent:
            with patch("unfazed_taskiq.decorators.rs") as mock_rs:
                # Mock agent and broker
                mock_agent = MagicMock()
                mock_broker = MagicMock()
                mock_agent.get_broker.return_value = mock_broker
                mock_agent._default_taskiq_name = "default"
                mock_get_agent.return_value = mock_agent

                # Mock broker.task decorator
                mock_decorated_func = MagicMock()
                mock_broker.task.return_value = lambda func: mock_decorated_func

                @task
                async def test_function() -> str:
                    """Test function docstring."""
                    return "test result"

                # Verify agent and broker were called correctly
                mock_get_agent.assert_called_once()
                mock_agent.get_broker.assert_called_once_with(None)
                mock_broker.task.assert_called_once_with()

                # Verify task was registered
                mock_rs.register.assert_called_once()
                call_args = mock_rs.register.call_args
                task_path = call_args[0][0]
                registered_task = call_args[0][1]

                assert task_path.endswith(".test_function")
                assert registered_task.name == "test_function"
                assert registered_task.broker_name == "default"
                assert registered_task.docs == "Test function docstring."
                assert registered_task.schedule is None

    def test_task_decorator_with_parameters_and_schedule(self) -> None:
        """Test task decorator with parameters and schedule."""
        with patch("unfazed_taskiq.decorators.get_agent") as mock_get_agent:
            with patch("unfazed_taskiq.decorators.rs") as mock_rs:
                # Mock agent and broker
                mock_agent = MagicMock()
                mock_broker = MagicMock()
                mock_agent.get_broker.return_value = mock_broker
                mock_agent._default_taskiq_name = "default"
                mock_get_agent.return_value = mock_agent

                # Mock broker.task decorator
                mock_decorated_func = MagicMock()
                mock_broker.task.return_value = lambda func: mock_decorated_func

                schedule = [{"cron": "*/5 * * * *"}]

                @task(broker_name="high_priority", schedule=schedule)
                async def parameterized_task(
                    x: int, y: str = "default", z: Optional[bool] = None
                ) -> str:
                    """Task with parameters."""
                    return f"{x}-{y}-{z}"

                # Verify broker was called with specific name
                mock_agent.get_broker.assert_called_once_with("high_priority")

                # Verify task was registered with correct info
                mock_rs.register.assert_called_once()
                call_args = mock_rs.register.call_args
                registered_task = call_args[0][1]

                assert registered_task.broker_name == "high_priority"
                assert registered_task.schedule == schedule
                assert len(registered_task.params) == 3

                # Check parameter details
                param_names = [p.name for p in registered_task.params]
                assert "x" in param_names
                assert "y" in param_names
                assert "z" in param_names

    def test_global_registry_service(self) -> None:
        """Test that global registry service works correctly."""
        # Clear global registry
        rs.tasks.clear()

        # Test global registry functionality
        task: RegistryTask = RegistryTask(
            name="global_task",
            broker_name="global",
            params=[],
            docs="Global task",
            schedule=None,
        )

        rs.register("global.module.task", task)
        retrieved_task = rs.get("global.module.task")

        assert retrieved_task == task
        assert len(rs.filter_path()) == 1
