from typing import Any, Optional

from pydantic import Field
from unfazed.serializer import Serializer

from . import models as m


class TaskiqResultSerializer(Serializer):
    """Admin/API serializer; ``result`` blob excluded from JSON output."""

    # Tortoise JSONField maps to dict|list in unfazed-generated schema, which
    # rejects None; real DB values can be null or any JSON scalar/object/array.
    return_value: Optional[Any] = Field(default=None)

    class Meta:
        model = m.TaskiqResultModel
        exclude = ["result"]
