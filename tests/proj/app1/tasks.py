from unfazed_taskiq.decorators import task


# Use get_broker method instead of broker property
@task
async def add(a: int, b: int) -> int:
    """Regular task: positional args."""
    return a + b


@task
async def multiply(a: int, b: int) -> int:
    """Task with named parameters."""
    return a * b


@task
async def concat(*args: str) -> str:
    """Task with variable positional args."""
    return "".join(args)


@task
async def merge(**kwargs: str) -> dict:
    """Task with variable keyword args."""
    return dict(kwargs)


@task
async def mixed_args(a: int, b: int, *extra: int, prefix: str = "") -> str:
    """Task with positional, *args, and keyword param."""
    total = a + b + sum(extra)
    return f"{prefix}{total}"


@task
async def scheduled_echo(message: str) -> str:
    """Task intended for scheduler (with schedule_id in labels)."""
    return f"echo:{message}"


@task
async def failing_task(msg: str) -> None:
    """Task that raises an exception."""
    raise ValueError(msg)
