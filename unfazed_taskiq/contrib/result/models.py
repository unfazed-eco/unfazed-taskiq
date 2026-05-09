from enum import IntEnum

from tortoise import fields, indexes, models


class TaskStatus(IntEnum):
    """Task status enum. Numeric code to string mapping:
    1 -> STARTED
    2 -> SUCCESS
    3 -> FAILURE
    """

    STARTED = 1
    SUCCESS = 2
    FAILURE = 3

    @property
    def label(self) -> str:
        return self.name


class TaskiqResultModel(models.Model):
    """Tortoise model for storing Taskiq task results in MySQL/TiDB."""

    class Meta:
        table = "taskiq_result"
        indexes = [
            indexes.Index(fields=["id"], name="idx_id"),
            indexes.Index(fields=["date_done"], name="idx_date_done"),
            indexes.Index(
                fields=["task_name", "date_done"], name="idx_task_name_date_done"
            ),
            indexes.Index(
                fields=["schedule_id", "date_done"], name="idx_schedule_id_date_done"
            ),
            indexes.Index(
                fields=["status"],
                name="idx_status",
            ),
        ]
        ordering = ["-date_created", "-date_done"]

    id = fields.IntField(primary_key=True)

    task_id = fields.CharField(
        max_length=255, unique=True, description="Task unique identifier"
    )
    status = fields.IntEnumField(
        TaskStatus,
        description="TaskStatus: 1=STARTED, 2=SUCCESS, 3=FAILURE",
    )
    result = fields.BinaryField(
        null=True,
        description="Serialized TaskiqResult from serializer.dumpb",
    )
    return_value = fields.JSONField(  # type: ignore[var-annotated]
        null=True,
        description="JSON-serializable return_value; "
        "full value may exist only in result blob",
    )
    date_done = fields.BigIntField(
        null=True,
        description="Timestamp when task completed",
    )
    date_created = fields.BigIntField(
        null=True,
        description="Timestamp when task was enqueued",
    )
    task_name = fields.CharField(
        max_length=255,
        null=True,
        description="Task definition name",
    )
    schedule_id = fields.CharField(
        max_length=255,
        null=True,
        description="Schedule id for periodic tasks (from labels)",
    )
    task_args = fields.JSONField(  # type: ignore[var-annotated]
        null=True,
        description="Task positional arguments: JSON array if serializable, else "
        "{__taskiq_json_str_fallback__: str(list)}",
    )
    task_kwargs = fields.JSONField(  # type: ignore[var-annotated]
        null=True,
        description="Task keyword arguments: JSON object if serializable, else "
        "{__taskiq_json_str_fallback__: str(dict)}",
    )
    traceback = fields.TextField(
        null=True,
        description="Traceback when task failed",
    )
