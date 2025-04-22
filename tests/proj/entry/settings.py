import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")

UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "ROOT_URLCONF": "entry.routes",
    "INSTALLED_APPS": ["app1"],
}


UNFAZED_TASKIQ_SETTINGS = {
    "BROKER": {
        "BACKEND": "taskiq.InMemoryBroker",
        "OPTIONS": {},
    },
    "RESULT": {
        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
        "OPTIONS": {
            "redis_url": f"redis://{REDIS_HOST}:6379",
        },
    },
    "SCHEDULER": {
        "BACKEND": "taskiq.scheduler.scheduler.TaskiqScheduler",
        "SOURCES_CLS": ["taskiq.schedule_sources.LabelScheduleSource"],
    },
}
