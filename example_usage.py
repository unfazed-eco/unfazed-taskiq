#!/usr/bin/env python3
"""
展示 @task 装饰器的不同使用方式
"""
from unfazed_taskiq.decorators import task


# 1. 简化用法：不需要参数时可以直接使用 @task
@task
async def simple_task():
    """简单的任务，使用默认 broker"""
    return "Hello from simple task!"


# 2. 带参数的任务
@task
async def add_numbers(a: int, b: int) -> int:
    """加法任务"""
    return a + b


# 3. 指定特定 broker
@task(broker_name="high_priority")
async def high_priority_task():
    """高优先级任务"""
    return "High priority task executed!"


# 4. 带调度配置的任务
@task(broker_name="scheduled", schedule=[{"cron": "*/5 * * * *"}])
async def scheduled_task():
    """定时任务，每5分钟执行一次"""
    return "Scheduled task executed!"


# 5. 带其他 taskiq 参数的任务
@task(broker_name="testtaskiq", max_retries=3)
async def retry_task():
    """带重试机制的任务"""
    return "Task with retry mechanism!"


if __name__ == "__main__":
    print("Task decorator examples:")
    print("1. @task - 简化用法")
    print("2. @task(broker_name='xxx') - 指定 broker")
    print("3. @task(schedule=[...]) - 定时任务")
    print("4. @task(max_retries=3) - 带重试机制")
