import os

from unfazed_taskiq.contrib.scheduler.sources import TortoiseScheduleSource

REDIS_HOST = os.getenv("REDIS_HOST", "redis")

UNFAZED_SETTINGS = {
    "LIFESPAN": [],
    "ROOT_URLCONF": "tests.proj.entry.routes",
    "INSTALLED_APPS": ["tests.proj.app1", "unfazed_taskiq.contrib.scheduler"],
    "DATABASE": {
        "CONNECTIONS": {
            "default": {
                "ENGINE": "tortoise.backends.mysql",
                "CREDENTIALS": {
                    "HOST": os.getenv("MYSQL_HOST", "mysql"),
                    "PORT": os.getenv("MYSQL_PORT", 3306),
                    "USER": os.getenv("MYSQL_USER", "root"),
                    "PASSWORD": os.getenv("MYSQL_PASSWORD", "app"),
                    "DATABASE": "test_app",
                },
            },
        },
    },
    # "LOGGING": {
    #     "formatters": {
    #         "taskiq_format": {
    #             "format": "[%(asctime)s][%(levelname)-7s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s"
    #         },
    #     },
    #     "handlers": {
    #         "_console": {
    #             "class": "logging.StreamHandler",
    #             "level": "DEBUG",
    #             "formatter": "taskiq_format",
    #         }
    #     },
    #     "loggers": {
    #         "taskiq": {
    #             "handlers": ["_console"],
    #             "level": "INFO",
    #         },
    #     },
    # },
}


DEFAULT_AMQP_URL = "amqp://app:app@rabbitmq:5672"
AMQP_URL = os.getenv("AMQP_URL", DEFAULT_AMQP_URL)


default_taskiq_name = "testtaskiq"
source = TortoiseScheduleSource(schedule_alias=default_taskiq_name)

UNFAZED_TASKIQ_SETTINGS = {
    "DEFAULT_TASKIQ_NAME": default_taskiq_name,
    "TASKIQ_CONFIG": {
        default_taskiq_name: {
            "BROKER": {
                "BACKEND": "taskiq.InMemoryBroker",
                "OPTIONS": {},
            },
            "SCHEDULER": {
                "SOURCES": [source],
                "BACKEND": "taskiq.TaskiqScheduler",
            },
        },
    },
}
