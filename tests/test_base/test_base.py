"""
Unit tests for TaskiqAgent class.

This module contains focused tests for the TaskiqAgent class,
covering core functionality: initialization, setup, broker/scheduler operations, and lifecycle.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from taskiq import InMemoryBroker
from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend

from unfazed_taskiq.base import TaskiqAgent
from unfazed_taskiq.settings import UnfazedTaskiqSettings
from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource


@pytest.fixture(autouse=True)
async def cleanup_agent():
    """Cleanup agent after each test to prevent connection leaks."""
    yield
    # Reset the singleton agent after each test
    from unfazed_taskiq.base import agent
    agent.reset()

# Test configuration constants
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379"


class TestTaskiqAgent:
    """Test TaskiqAgent core functionality."""

    @pytest.fixture
    def base_settings(self):
        """Base settings for single broker tests."""
        source = TortoiseScheduleSource(schedule_alias="default")
        return {
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
                            "redis_url": REDIS_URL,
                        },
                    },
                    "SCHEDULER": {
                        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
                        "SOURCES": [source],
                    },
                },
            },
        }

    def test_initialization(self) -> None:
        """Test TaskiqAgent initialization."""
        agent = TaskiqAgent()

        assert agent._brokers == {}
        assert agent._schedulers == {}
        assert agent._ready is False
        assert agent._default_taskiq_name is None
        assert agent._taskiq_configs == {}

    def test_setup_basic(self, base_settings) -> None:
        """Test basic setup functionality."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)

        agent.setup(settings)

        assert agent._ready is True
        assert agent._default_taskiq_name == "default"
        assert len(agent._brokers) == 1
        assert "default" in agent._brokers
        assert isinstance(agent._brokers["default"], InMemoryBroker)
        assert isinstance(
            agent._brokers["default"].result_backend, RedisAsyncResultBackend
        )

    def test_setup_without_configs_raises_error(self) -> None:
        """Test setup without configs raises ValueError."""
        agent = TaskiqAgent()
        empty_settings = UnfazedTaskiqSettings.model_validate({"TASKIQ_CONFIG": {}})

        with pytest.raises(ValueError, match="No taskiq configurations found"):
            agent.setup(empty_settings)

    def test_setup_is_idempotent(self, base_settings) -> None:
        """Test setup is idempotent."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)

        # First setup
        agent.setup(settings)
        first_broker_id = id(agent._brokers["default"])

        # Second setup
        agent.setup(settings)
        second_broker_id = id(agent._brokers["default"])

        assert first_broker_id == second_broker_id
        assert agent._ready is True

    def test_get_broker_with_name(self, base_settings) -> None:
        """Test get broker with specific name."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        broker = agent.get_broker("default")

        assert isinstance(broker, InMemoryBroker)
        assert broker is agent._brokers["default"]

    def test_get_broker_without_name_uses_default(self, base_settings) -> None:
        """Test get broker without name uses default."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        broker = agent.get_broker()

        assert isinstance(broker, InMemoryBroker)
        assert broker is agent._brokers["default"]

    def test_get_broker_no_default_raises_error(self, base_settings) -> None:
        """Test get broker without default raises error."""
        agent = TaskiqAgent()
        settings_data = base_settings.copy()
        del settings_data["DEFAULT_TASKIQ_NAME"]
        settings = UnfazedTaskiqSettings.model_validate(settings_data)
        agent.setup(settings)

        with pytest.raises(ValueError, match="No found broker name configured"):
            agent.get_broker()

    def test_get_broker_invalid_name_returns_none(self, base_settings) -> None:
        """Test get broker with invalid name returns None."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        broker = agent.get_broker("invalid")

        assert broker is None

    def test_get_scheduler_with_name(self, base_settings) -> None:
        """Test get scheduler with specific name."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        scheduler = agent.get_scheduler("default")

        assert isinstance(scheduler, TaskiqScheduler)
        assert scheduler is agent._schedulers["default"]

    def test_get_scheduler_without_name_uses_default(self, base_settings) -> None:
        """Test get scheduler without name uses default."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        scheduler = agent.get_scheduler()

        assert isinstance(scheduler, TaskiqScheduler)
        assert scheduler is agent._schedulers["default"]

    def test_get_scheduler_no_default_raises_error(self, base_settings) -> None:
        """Test get scheduler without default raises error."""
        agent = TaskiqAgent()
        settings_data = base_settings.copy()
        del settings_data["DEFAULT_TASKIQ_NAME"]
        settings = UnfazedTaskiqSettings.model_validate(settings_data)
        agent.setup(settings)

        with pytest.raises(ValueError, match="No found scheduler name configured"):
            agent.get_scheduler()

    def test_get_scheduler_invalid_name_returns_none(self, base_settings) -> None:
        """Test get scheduler with invalid name returns None."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        scheduler = agent.get_scheduler("invalid")

        assert scheduler is None

    def test_check_ready_calls_setup_when_not_ready(self) -> None:
        """Test check_ready calls setup when not ready."""
        agent = TaskiqAgent()

        with patch.object(agent, "setup_from_property") as mock_setup:
            agent.check_ready()
            mock_setup.assert_called_once()

    def test_check_ready_does_not_call_setup_when_ready(self) -> None:
        """Test check_ready does not call setup when ready."""
        agent = TaskiqAgent()
        agent._ready = True

        with patch.object(agent, "setup_from_property") as mock_setup:
            agent.check_ready()
            mock_setup.assert_not_called()

    def test_reset(self, base_settings) -> None:
        """Test reset functionality."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)

        agent.reset()

        assert agent._ready is False
        assert len(agent._brokers) == 0
        assert len(agent._schedulers) == 0

    def test_setup_from_property(self, base_settings) -> None:
        """Test setup_from_property calls setup."""
        agent = TaskiqAgent()
        
        with patch("unfazed.conf.settings") as mock_settings:
            mock_settings.__getitem__.return_value = base_settings
            with patch.object(agent, "setup") as mock_setup:
                agent.setup_from_property()
                # Verify setup was called with UnfazedTaskiqSettings object
                mock_setup.assert_called_once()
                call_args = mock_setup.call_args[0][0]
                assert isinstance(call_args, UnfazedTaskiqSettings)

    @pytest.mark.asyncio
    async def test_startup(self, base_settings) -> None:
        """Test startup lifecycle method."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)
        
        # Mock startup methods
        # In single broker test, broker startup is called through scheduler
        for scheduler in agent._schedulers.values():
            scheduler.startup = AsyncMock()  # type: ignore
        
        await agent.startup()
        
        # Verify scheduler startup was called (which will call broker startup)
        for scheduler in agent._schedulers.values():
            scheduler.startup.assert_called_once()  # type: ignore

    @pytest.mark.asyncio
    async def test_shutdown(self, base_settings) -> None:
        """Test shutdown lifecycle method."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(base_settings)
        agent.setup(settings)
        
        # Mock shutdown methods
        # In single broker test, broker shutdown is called through scheduler
        for scheduler in agent._schedulers.values():
            scheduler.shutdown = AsyncMock()  # type: ignore
        
        await agent.shutdown()
        
        # Verify scheduler shutdown was called (which will call broker shutdown)
        for scheduler in agent._schedulers.values():
            scheduler.shutdown.assert_called_once()  # type: ignore

    def test_singleton_agent(self) -> None:
        """Test singleton agent instance."""
        from unfazed_taskiq.base import agent as singleton_agent

        assert isinstance(singleton_agent, TaskiqAgent)

        # Test multiple imports return same instance
        from unfazed_taskiq.base import agent as agent2

        assert singleton_agent is agent2


class TestTaskiqAgentMultiBroker:
    """Test TaskiqAgent with multiple brokers."""

    @pytest.fixture
    def multi_broker_settings(self):
        """Multi-broker settings for testing multiple broker scenarios."""
        source = TortoiseScheduleSource(schedule_alias="default")
        return {
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
                            "redis_url": REDIS_URL,
                        },
                    },
                    "SCHEDULER": {
                        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
                        "SOURCES": [source],
                    },
                },
                "high_priority": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                    "RESULT": {
                        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
                        "OPTIONS": {
                            "redis_url": REDIS_URL,
                        },
                    },
                },
                "low_priority": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    },
                    "RESULT": {
                        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
                        "OPTIONS": {
                            "redis_url": REDIS_URL,
                        },
                    },
                },
            },
        }

    def test_setup_multiple_brokers(self, multi_broker_settings) -> None:
        """Test setup with multiple brokers."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        
        agent.setup(settings)
        
        assert agent._ready is True
        assert agent._default_taskiq_name == "default"
        assert len(agent._brokers) == 3
        assert "default" in agent._brokers
        assert "high_priority" in agent._brokers
        assert "low_priority" in agent._brokers
        
        # Verify all brokers are InMemoryBroker instances
        for broker in agent._brokers.values():
            assert isinstance(broker, InMemoryBroker)

    def test_get_different_brokers(self, multi_broker_settings) -> None:
        """Test getting different brokers by name."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        default_broker = agent.get_broker("default")
        high_priority_broker = agent.get_broker("high_priority")
        low_priority_broker = agent.get_broker("low_priority")
        
        # Verify all brokers are different instances
        assert isinstance(default_broker, InMemoryBroker)
        assert isinstance(high_priority_broker, InMemoryBroker)
        assert isinstance(low_priority_broker, InMemoryBroker)
        
        assert default_broker is not high_priority_broker
        assert default_broker is not low_priority_broker
        assert high_priority_broker is not low_priority_broker

    def test_get_default_broker_without_name(self, multi_broker_settings) -> None:
        """Test getting default broker without specifying name."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        default_broker = agent.get_broker()
        
        assert isinstance(default_broker, InMemoryBroker)
        assert default_broker is agent._brokers["default"]

    def test_get_invalid_broker_returns_none(self, multi_broker_settings) -> None:
        """Test getting invalid broker name returns None."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        invalid_broker = agent.get_broker("invalid_broker")
        
        assert invalid_broker is None

    def test_scheduler_only_on_default_queue(self, multi_broker_settings) -> None:
        """Test that scheduler is only configured for default queue."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        default_scheduler = agent.get_scheduler("default")
        high_priority_scheduler = agent.get_scheduler("high_priority")
        low_priority_scheduler = agent.get_scheduler("low_priority")
        
        # Only default queue should have scheduler
        assert isinstance(default_scheduler, TaskiqScheduler)
        assert high_priority_scheduler is None
        assert low_priority_scheduler is None

    def test_broker_isolation(self, multi_broker_settings) -> None:
        """Test that brokers are isolated from each other."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        default_broker = agent.get_broker("default")
        high_priority_broker = agent.get_broker("high_priority")
        
        # Verify brokers have different configurations
        assert default_broker is not high_priority_broker
        
        # Verify they have different queue names (if accessible)
        # Note: InMemoryBroker doesn't expose queue_name directly, 
        # but we can verify they are different instances

    @pytest.mark.asyncio
    async def test_startup_multiple_brokers(self, multi_broker_settings) -> None:
        """Test startup with multiple brokers."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        # Mock startup methods for brokers without schedulers
        with patch.object(agent._brokers["high_priority"], "startup", new_callable=AsyncMock) as high_mock, \
             patch.object(agent._brokers["low_priority"], "startup", new_callable=AsyncMock) as low_mock:
            
            await agent.startup()
            
            # Verify brokers without schedulers startup was called exactly once
            # (default broker startup is called through scheduler)
            high_mock.assert_called_once()
            low_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_multiple_brokers(self, multi_broker_settings) -> None:
        """Test shutdown with multiple brokers."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        # Mock shutdown methods for brokers without schedulers
        with patch.object(agent._brokers["high_priority"], "shutdown", new_callable=AsyncMock) as high_mock, \
             patch.object(agent._brokers["low_priority"], "shutdown", new_callable=AsyncMock) as low_mock:
            
            await agent.shutdown()
            
            # Verify brokers without schedulers shutdown was called exactly once
            # (default broker shutdown is called through scheduler)
            high_mock.assert_called_once()
            low_mock.assert_called_once()

    def test_reset_clears_all_brokers(self, multi_broker_settings) -> None:
        """Test reset clears all brokers."""
        agent = TaskiqAgent()
        settings = UnfazedTaskiqSettings.model_validate(multi_broker_settings)
        agent.setup(settings)
        
        # Verify brokers exist before reset
        assert len(agent._brokers) == 3
        
        agent.reset()
        
        # Verify all brokers are cleared
        assert agent._ready is False
        assert len(agent._brokers) == 0
        assert len(agent._schedulers) == 0
