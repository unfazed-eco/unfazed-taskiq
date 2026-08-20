import re
import typing as t
import warnings
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from pydantic import BaseModel, ConfigDict, Field, model_validator
from taskiq import ScheduleSource
from taskiq.events import TaskiqEvents
from unfazed.conf import register_settings


def _version_at_least(version: str, minimum: tuple[int, int, int]) -> bool:
    """Compare the numeric part of a package version."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    return match is not None and tuple(map(int, match.groups())) >= minimum


class Broker(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")
    middlewares: t.List[str] = Field(
        default=[], alias="MIDDLEWARES"
    )  # unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware
    handlers: t.List[t.Dict[str, t.Union[str, TaskiqEvents]]] = Field(
        default=[], alias="HANDLERS"
    )

    @model_validator(mode="after")
    def normalize_aio_pika_options(self) -> "Broker":
        """Convert the legacy AioPika queue options to the current API.

        ``taskiq-aio-pika`` used to accept ``exchange_name`` and
        ``queue_name``.  Newer versions configure these through ``Exchange``
        and ``Queue`` objects instead.  Keep accepting the old settings
        format, but do not pass the legacy keys to the broker constructor.
        """
        if self.backend.rsplit(".", 1)[-1] != "AioPikaBroker":
            return self

        try:
            aio_pika_version = package_version("taskiq-aio-pika")
        except PackageNotFoundError:
            return self

        if not _version_at_least(aio_pika_version, (0, 6, 0)):
            warnings.warn(
                f"taskiq-aio-pika {aio_pika_version} (< 0.6.0) is deprecated: "
                "support for versions below 0.6.0 will be removed in a future "
                "release. Please upgrade to taskiq-aio-pika>=0.6.0.",
                FutureWarning,
                stacklevel=2,
            )
            return self

        options = dict(self.options or {})
        exchange_name = options.pop("exchange_name", None)
        queue_name = options.pop("queue_name", None)

        if exchange_name is None and queue_name is None:
            return self

        # Exchange/Queue/QueueType only exist in taskiq-aio-pika >= 0.6.0.
        # The import is guarded by the version check above, but mypy resolves
        # against whatever version is installed (e.g. the locked 0.4.2).
        from taskiq_aio_pika import (  # type: ignore[attr-defined]
            Exchange,
            Queue,
            QueueType,
        )

        if exchange_name is not None and "exchange" not in options:
            # type defaults to ExchangeType.TOPIC, matching the legacy default.
            options["exchange"] = Exchange(name=exchange_name)

        if queue_name is not None and "task_queues" not in options:
            options["task_queues"] = [
                Queue(
                    name=queue_name,
                    routing_key=queue_name,
                    type=QueueType.CLASSIC,
                ),
            ]

        self.options = options
        return self


class Result(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")


class Scheduler(BaseModel):
    backend: str = Field(alias="BACKEND")
    sources: t.Optional[t.List[t.Union[str, ScheduleSource]]] = Field(
        default=None, alias="SOURCES"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskiqConfig(BaseModel):
    broker: Broker = Field(alias="BROKER")
    result: t.Optional[Result] = Field(default=None, alias="RESULT")
    scheduler: t.Optional[Scheduler] = Field(default=None, alias="SCHEDULER")


@register_settings("UNFAZED_TASKIQ_SETTINGS")
class UnfazedTaskiqSettings(BaseModel):
    taskiq_config: t.Dict[str, TaskiqConfig] = Field(alias="TASKIQ_CONFIG")
    default_alias_name: t.Optional[str] = Field(
        alias="DEFAULT_TASKIQ_NAME", default="default"
    )
