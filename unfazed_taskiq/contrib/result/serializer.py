from typing import Any, Optional

from pydantic import Field
from unfazed.serializer import Serializer

from . import models as m


class TaskiqResultSerializer(Serializer):
    """Admin/API serializer; ``result`` blob excluded from JSON output."""

    # Unfazed's generated schema does not add Optional for nullable ORM fields.
    date_done: Optional[int] = Field(
        default=None, json_schema_extra={"field_type": "BigIntField"}
    )
    date_created: Optional[int] = Field(
        default=None, json_schema_extra={"field_type": "BigIntField"}
    )
    task_name: Optional[str] = Field(default=None, max_length=255)
    schedule_id: Optional[str] = Field(default=None, max_length=255)
    task_args: Optional[dict | list] = Field(default=None)
    task_kwargs: Optional[dict | list] = Field(default=None)
    traceback: Optional[str] = Field(
        default=None, json_schema_extra={"field_type": "TextField"}
    )
    return_value: Optional[Any] = Field(default=None)
    labels: Optional[dict[str, Any]] = Field(default=None)

    class Meta:
        model = m.TaskiqResultModel
        exclude = ["result"]
