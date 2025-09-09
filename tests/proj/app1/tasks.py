from unfazed_taskiq.decorators import task


# Use get_broker method instead of broker property
@task(broker_name="testtaskiq")
async def add(a: int, b: int) -> int:
    return a + b


@task(broker_name="testtaskiq")
async def add_schedule_high_priority(a: int, b: int) -> int:
    return a + b
