UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "ROOT_URLCONF": "entry.routes",
}


UNFAZED_TASKIQ_SETTINGS = {
    "BROKER": {
        "BACKEND": "taskiq_aio_pika.AioPikaBroker",
        "OPTIONS": {
            "url": "amqp://guest:guest@rabbitmq:5672",
        },
    },
}
