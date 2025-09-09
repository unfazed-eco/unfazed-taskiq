from pydantic import BaseModel
from typing import Any, Optional


class RegistryTaskParam(BaseModel):
    name: str
    hint_type: Any
    required: bool
    default: Any


class RegistryTask(BaseModel):
    name: str
    broker_name: str
    params: list[RegistryTaskParam]
    docs: Optional[str]
    schedule: Optional[list[dict[str, Any]]]
