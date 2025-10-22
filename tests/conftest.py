import logging
import os
import sys
import typing as t
import uuid
from datetime import datetime

import pytest
from pytest import Item
from pytest_asyncio import is_async_test
from tortoise import Tortoise
from tortoise.connection import connections
from unfazed.core import Unfazed

from unfazed_taskiq.contrib.scheduler.models import PeriodicTask

logger = logging.getLogger("unfazed.taskiq")


# dont need decorate test functions with pytest.mark.asyncio
def pytest_collection_modifyitems(items: t.List[Item]) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    function_scope_marker = pytest.mark.asyncio(loop_scope="function")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(function_scope_marker, append=False)


# create a global unfazed
# use this fixture in your test functions
@pytest.fixture(autouse=True, scope="function")
async def unfazed() -> t.AsyncGenerator[Unfazed, None]:
    # Clear task registry before each test
    from unfazed_taskiq.agent import agents
    from unfazed_taskiq.registry.task import rs

    rs.clear()
    agents.reset()
    agents.check_ready()

    root_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(root_path)
    os.environ.setdefault("UNFAZED_SETTINGS_MODULE", "tests.proj.entry.settings")
    unfazed = Unfazed()
    await unfazed.setup()

    conn = connections.get("default")
    if os.getenv("DISABLE_DB_CREATE", "false") == "false":
        await conn.db_create()
    logger.info("Database created")
    await Tortoise.generate_schemas()
    logger.info("Schemas generated")

    yield unfazed

    await Tortoise._drop_databases()


@pytest.fixture()
async def test_scheduler_sample_data() -> t.Any:
    data: list[dict] = [
        {
            "description": "test_task1",
            "task_args": "[]",
            "task_name": "test.tasks:test_task1",
            "schedule_alias": "test_schedule1",
            "task_kwargs": '{"category": "00001"}',
            "labels": "{}",
            "cron": "* * * * *",
            "total_run_count": 0,
            "enabled": 0,
            "last_run_at": datetime.now(),
            "time": datetime.now(),
            "updated_at": datetime.now(),
            "created_at": datetime.now(),
            "schedule_id": str(uuid.uuid4().hex),
        },
        {
            "description": "test_task2",
            "task_args": "[]",
            "task_name": "test.tasks:test_task2",
            "schedule_alias": "test_schedule2",
            "task_kwargs": '{"keyword": "三角洲行动"}',
            "labels": "{}",
            "cron": "* * * * *",
            "total_run_count": 0,
            "enabled": 0,
            "last_run_at": datetime.now(),
            "time": datetime.now(),
            "updated_at": datetime.now(),
            "created_at": datetime.now(),
            "schedule_id": str(uuid.uuid4().hex),
        },
        {
            "description": "test_task3",
            "task_args": "[]",
            "task_name": "test.tasks:test_task3",
            "schedule_alias": "test_schedule3",
            "task_kwargs": '{"keyword": "三角洲行动"}',
            "labels": "{}",
            "cron": "* * * * *",
            "total_run_count": 0,
            "enabled": 1,
            "last_run_at": datetime.now(),
            "time": datetime.now(),
            "updated_at": datetime.now(),
            "created_at": datetime.now(),
            "schedule_id": str(uuid.uuid4().hex),
        },
        {
            "description": "test_task4",
            "task_args": "[]",
            "task_name": "test.tasks:test_task4",
            "schedule_alias": "test_schedule4",
            "task_kwargs": '{"keyword": "三角洲行动"}',
            "labels": "{}",
            "cron": "* * * * *",
            "total_run_count": 0,
            "enabled": 0,
            "last_run_at": datetime.now(),
            "time": datetime.now(),
            "updated_at": datetime.now(),
            "created_at": datetime.now(),
            "schedule_id": str(uuid.uuid4().hex),
        },
    ]

    for item in data:
        await PeriodicTask.create(**item)

    yield data

    await PeriodicTask.filter().delete()
