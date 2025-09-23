from typing import Any

from taskiq import TaskiqResult
from unfazed.http import HttpRequest, JsonResponse

from .tasks import add


async def add_endpoint(request: HttpRequest, a: int, b: int) -> JsonResponse:
    task: Any = await add.kiq(a, b)  # type: ignore[attr-defined]

    result: TaskiqResult = await task.wait_result(timeout=10)

    return JsonResponse({"result": result.return_value})
