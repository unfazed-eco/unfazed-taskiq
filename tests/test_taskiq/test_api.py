import os
import sys
import typing as t

import pytest
from unfazed.core import Unfazed
from unfazed.test import Requestfactory


@pytest.fixture
async def unfazed() -> t.AsyncGenerator[Unfazed, None]:
    os.environ["UNFAZED_SETTINGS_MODULE"] = "tests.proj.entry.settings"

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../proj")

    sys.path.append(path)

    unfazed = Unfazed()
    await unfazed.setup()

    yield unfazed


async def test_api(unfazed: Unfazed) -> None:
    async with Requestfactory(unfazed) as rf:
        resp = await rf.get("/app1/add?a=1&b=2")

        assert resp.status_code == 200
        assert resp.json() == {"result": 3}
