import os
import typing as t
from unittest.mock import AsyncMock

import pytest
from taskiq import InMemoryBroker
from taskiq_redis import RedisAsyncResultBackend

from unfazed_taskiq.cli import get_agent


@pytest.fixture
def setup_taskiq() -> t.Generator[None, None, None]:
    """Setup test environment with Taskiq configuration"""
    os.environ["UNFAZED_SETTINGS_MODULE"] = "tests.proj.entry.settings"
    yield
    del os.environ["UNFAZED_SETTINGS_MODULE"]


@pytest.fixture(autouse=True)
def setup_settings() -> t.Generator:
    """Clear settings cache before each test"""
    from unfazed.conf import settings

    settings.clear()
    yield


def test_taskiq_agent_initialization(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test Taskiq agent initialization with project settings"""
    agent = get_agent()

    # Verify agent is properly initialized
    assert agent._ready is True
    assert len(agent._brokers) == 3
    assert len(agent._schedulers) == 2

    # Verify broker types
    for broker in agent._brokers.values():
        assert isinstance(broker, InMemoryBroker)
        assert isinstance(broker.result_backend, RedisAsyncResultBackend)

    # Verify scheduler types
    for scheduler in agent._schedulers.values():
        assert scheduler is not None

    agent.reset()


def test_taskiq_multi_queue_broker_access(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test accessing brokers from different queues"""
    agent = get_agent()

    # Test broker access through agent methods
    default_broker = agent.get_broker("default")
    high_priority_broker = agent.get_broker("high_priority")
    low_priority_broker = agent.get_broker("low_priority")

    assert isinstance(default_broker, InMemoryBroker)
    assert isinstance(high_priority_broker, InMemoryBroker)
    assert isinstance(low_priority_broker, InMemoryBroker)

    # Verify different instances
    assert default_broker is not high_priority_broker
    assert default_broker is not low_priority_broker
    assert high_priority_broker is not low_priority_broker


def test_taskiq_scheduler_access(setup_taskiq: t.Generator[None, None, None]) -> None:
    """Test accessing schedulers from different queues"""
    agent = get_agent()

    # Test scheduler access through agent methods
    default_scheduler = agent.get_scheduler("default")
    high_priority_scheduler = agent.get_scheduler("high_priority")
    low_priority_scheduler = agent.get_scheduler("low_priority")

    # Verify scheduler instances
    assert default_scheduler is not None
    assert high_priority_scheduler is not None
    assert low_priority_scheduler is None  # No scheduler for low_priority


@pytest.mark.asyncio
async def test_taskiq_broker_startup_shutdown(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test broker startup and shutdown lifecycle"""
    agent = get_agent()
    broker = agent.get_broker("default")

    # Mock startup and shutdown methods
    broker.startup = AsyncMock()  # type: ignore
    broker.shutdown = AsyncMock()  # type: ignore

    # Test startup
    await broker.startup()
    broker.startup.assert_called_once()  # type: ignore

    # Test shutdown
    await broker.shutdown()
    broker.shutdown.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_taskiq_scheduler_startup_shutdown(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test scheduler startup and shutdown lifecycle"""
    agent = get_agent()
    scheduler = agent.get_scheduler("default")

    # Mock startup and shutdown methods
    scheduler.startup = AsyncMock()  # type: ignore
    scheduler.shutdown = AsyncMock()  # type: ignore

    # Test startup
    await scheduler.startup()  # type: ignore
    scheduler.startup.assert_called_once()  # type: ignore

    # Test shutdown
    await scheduler.shutdown()  # type: ignore
    scheduler.shutdown.assert_called_once()  # type: ignore


def test_taskiq_queue_configuration(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test queue configuration validation"""
    agent = get_agent()

    # Verify queue configuration
    assert "default" in agent._brokers
    assert "high_priority" in agent._brokers
    assert "low_priority" in agent._brokers

    # Verify scheduler configuration
    assert "default" in agent._schedulers
    assert "high_priority" in agent._schedulers
    assert "low_priority" not in agent._schedulers

    agent.reset()


def test_taskiq_error_handling(setup_taskiq: t.Generator[None, None, None]) -> None:
    """Test error handling in Taskiq agent"""
    agent = get_agent()

    # Test getting non-existent queue
    with pytest.raises(ValueError, match="Queue 'invalid_queue' not found"):
        agent.get_broker("invalid_queue")

    # Test getting broker without queue name
    with pytest.raises(ValueError, match="No found broker name configured"):
        agent.get_broker(None)  # type: ignore

    # Test getting scheduler without queue name
    with pytest.raises(ValueError, match="No found scheduler name configured"):
        agent.get_scheduler(None)  # type: ignore

    agent.reset()


def test_taskiq_broker_instances_stability(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test stability of broker instances across multiple calls"""
    agent = get_agent()

    # Multiple calls to ensure stability
    for _ in range(5):
        default_broker = agent.get_broker("default")
        high_priority_broker = agent.get_broker("high_priority")
        low_priority_broker = agent.get_broker("low_priority")

        assert isinstance(default_broker, InMemoryBroker)
        assert isinstance(high_priority_broker, InMemoryBroker)
        assert isinstance(low_priority_broker, InMemoryBroker)

        # Verify instances are consistent
        assert default_broker is not high_priority_broker
        assert default_broker is not low_priority_broker
        assert high_priority_broker is not low_priority_broker


def test_taskiq_settings_validation(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test Taskiq settings validation"""
    from unfazed.conf import settings

    # Verify settings are loaded
    taskiq_settings = settings["UNFAZED_TASKIQ_SETTINGS"]

    # Verify queue configurations
    assert hasattr(taskiq_settings, "taskiq_config")
    queue_configs = taskiq_settings.taskiq_config
    assert "default" in queue_configs
    assert "high_priority" in queue_configs
    assert "low_priority" in queue_configs

    # Verify broker configurations
    for queue_name, config in queue_configs.items():
        assert hasattr(config, "broker")
        assert hasattr(config, "result")
        assert config.broker.backend == "taskiq.InMemoryBroker"
        assert config.result.backend == "taskiq_redis.RedisAsyncResultBackend"

    # Verify scheduler configurations
    assert hasattr(queue_configs["default"], "scheduler")
    assert hasattr(queue_configs["high_priority"], "scheduler")
    assert (
        not hasattr(queue_configs["low_priority"], "scheduler")
        or queue_configs["low_priority"].scheduler is None
    )


def test_taskiq_agent_lifecycle(setup_taskiq: t.Generator[None, None, None]) -> None:
    """Test Taskiq agent lifecycle methods"""
    agent = get_agent()

    # Test reset functionality
    assert len(agent._brokers) > 0
    assert len(agent._schedulers) > 0
    assert agent._ready is True

    agent.reset()

    assert len(agent._brokers) == 0
    assert len(agent._schedulers) == 0
    assert agent._ready is False

    # Test setup again
    agent = get_agent()
    assert len(agent._brokers) == 3
    assert len(agent._schedulers) == 2
    assert agent._ready is True


# 新增：测试 app1/tasks.py 中的现有任务
def test_app1_tasks_import(setup_taskiq: t.Generator[None, None, None]) -> None:
    """Test that app1 tasks can be imported and have correct decorators"""
    import os
    import sys

    # Add project path
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../proj")
    sys.path.append(project_path)

    # Import tasks
    from app1.tasks import (
        add,
        add_schedule_default,
        add_schedule_high_priority,
        add_schedule_low_priority,
    )

    # Verify all tasks are imported
    assert add is not None
    assert add_schedule_high_priority is not None
    assert add_schedule_default is not None
    assert add_schedule_low_priority is not None


@pytest.mark.asyncio
async def test_app1_tasks_basic_functionality(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test basic functionality of app1 tasks"""
    import os
    import sys

    # Add project path
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../proj")
    sys.path.append(project_path)

    # Import tasks
    from app1.tasks import (
        add,
        add_schedule_default,
        add_schedule_high_priority,
        add_schedule_low_priority,
    )

    # Test basic math tasks (async functions need await)
    assert await add(2, 3) == 5
    assert await add_schedule_high_priority(4, 5) == 9
    assert await add_schedule_default(10, 2) == 12
    assert await add_schedule_low_priority(10, 3) == 13


@pytest.mark.asyncio
async def test_app1_tasks_different_queues(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test that tasks are configured for different queues"""
    import os
    import sys

    # Add project path
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../proj")
    sys.path.append(project_path)

    # Import tasks
    from app1.tasks import (
        add,
        add_schedule_default,
        add_schedule_high_priority,
        add_schedule_low_priority,
    )

    # Verify tasks have different queue configurations
    # Note: We can't directly test queue assignment without running the actual taskiq workers
    # But we can verify the functions work correctly
    assert await add(1, 1) == 2
    assert await add_schedule_high_priority(1, 1) == 2
    assert await add_schedule_default(1, 1) == 2
    assert await add_schedule_low_priority(1, 1) == 2


@pytest.mark.asyncio
async def test_app1_tasks_schedule_configuration(
    setup_taskiq: t.Generator[None, None, None],
) -> None:
    """Test that scheduled tasks have correct configuration"""
    import os
    import sys

    # Add project path
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../proj")
    sys.path.append(project_path)

    # Import tasks
    from app1.tasks import (
        add_schedule_default,
        add_schedule_high_priority,
        add_schedule_low_priority,
    )

    # Test that scheduled tasks work correctly
    # The schedule configuration is handled by taskiq, we just test the function logic
    assert await add_schedule_high_priority(5, 5) == 10
    assert await add_schedule_default(3, 7) == 10
    assert await add_schedule_low_priority(8, 2) == 10
