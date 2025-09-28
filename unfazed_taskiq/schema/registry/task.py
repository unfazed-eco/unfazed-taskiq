from typing import Any, Optional

from pydantic import BaseModel


class RegistryTaskParam(BaseModel):
    name: str
    hint_type: Any
    required: bool
    default: Any


class RegistryTaskSchema(BaseModel):
    name: str
    alias_name: Optional[str]
    params: list[RegistryTaskParam]
    docs: Optional[str]
    schedule: Optional[list[dict[str, Any]]]
