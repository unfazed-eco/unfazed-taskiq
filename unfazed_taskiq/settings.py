import typing as t

from pydantic import BaseModel, ConfigDict, Field
from taskiq import ScheduleSource
from unfazed.conf import register_settings


class Broker(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")


class Result(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")


class Scheduler(BaseModel):
    backend: str = Field(alias="BACKEND")
    sources: t.Optional[t.List[t.Union[str, ScheduleSource]]] = Field(
        default=None, alias="SOURCES"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


@register_settings("UNFAZED_TASKIQ_SETTINGS")
class UnfazedTaskiqSettings(BaseModel):
    broker: Broker = Field(alias="BROKER")
    result: t.Optional[Result] = Field(default=None, alias="RESULT")
    scheduler: t.Optional[Scheduler] = Field(default=None, alias="SCHEDULER")
