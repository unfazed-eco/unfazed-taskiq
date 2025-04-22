from unfazed.http import HttpRequest, JsonResponse

from .tasks import add


async def add_endpoint(request: HttpRequest, a: int, b: int) -> JsonResponse:
    task = await add.kiq(a, b)

    result = await task.wait_result(timeout=10)

    return JsonResponse({"result": result.return_value})
