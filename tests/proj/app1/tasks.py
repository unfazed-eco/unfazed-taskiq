from unfazed_taskiq.decorators import task


# Use get_broker method instead of broker property
@task
async def add(a: int, b: int) -> int:
    return a + b
