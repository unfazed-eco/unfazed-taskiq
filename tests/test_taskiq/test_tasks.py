import pytest
from unfazed.core import Unfazed
from unfazed.test import Requestfactory


@pytest.mark.asyncio
async def test_api(unfazed: Unfazed) -> None:
    async with Requestfactory(unfazed) as rf:
        resp = await rf.get("/app1/add?a=1&b=2")

        assert resp.status_code == 200
        assert resp.json() == {"result": 3}
