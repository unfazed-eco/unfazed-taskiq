from unfazed_taskiq import agent


@agent.broker.task
async def add(a: int, b: int) -> int:
    return a + b
