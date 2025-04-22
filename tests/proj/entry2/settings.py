UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "ROOT_URLCONF": "entry.routes",
}


UNFAZED_TASKIQ_SETTINGS = {
    "BROKER": {
        "BACKEND": "taskiq.InMemoryBroker",
        "OPTIONS": {},
    },
    "RESULT": {
        "BACKEND": "taskiq_redis.RedisAsyncResultBackend",
        "OPTIONS": {
            "redis_url": "redis://redis:6379",
        },
    },
}
