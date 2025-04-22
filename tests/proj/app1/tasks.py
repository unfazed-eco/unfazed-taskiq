from unfazed_taskiq import agent


@agent.broker.task
async def add(a: int, b: int) -> int:
    return a + b


@agent.broker.task(schedule=[{"crontab": "*/1 * * * *", "args": [1, 2]}])
async def add_schedule(a: int, b: int) -> int:
    return a + b
