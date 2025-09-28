import typing as t

from pydantic import BaseModel, ConfigDict, Field
from taskiq import ScheduleSource
from taskiq.events import TaskiqEvents
from unfazed.conf import register_settings


class Broker(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")
    middlewares: t.List[str] = Field(
        default=[], alias="MIDDLEWARES"
    )  # unfazed_taskiq.middleware.UnfazedTaskiqExceptionMiddleware
    handlers: t.List[t.Dict[str, t.Union[str, TaskiqEvents]]] = Field(
        default=[], alias="HANDLERS"
    )


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
        alias="DEFAULT_ALIAS_NAME", default="default"
    )
