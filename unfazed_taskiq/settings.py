import typing as t

from pydantic import BaseModel, Field
from unfazed.conf import register_settings


class Broker(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")


class Result(BaseModel):
    backend: str = Field(alias="BACKEND")
    options: t.Optional[t.Dict[str, t.Any]] = Field(default=None, alias="OPTIONS")


class Scheduler(BaseModel):
    backend: str = Field(alias="BACKEND")
    sources_cls: t.Optional[t.List[str]] = Field(default=None, alias="SOURCES_CLS")


@register_settings("UNFAZED_TASKIQ_SETTINGS")
class UnfazedTaskiqSettings(BaseModel):
    broker: Broker = Field(alias="BROKER")
    result: t.Optional[Result] = Field(default=None, alias="RESULT")
    scheduler: t.Optional[Scheduler] = Field(default=None, alias="SCHEDULER")
