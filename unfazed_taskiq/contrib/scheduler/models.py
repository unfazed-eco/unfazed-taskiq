import uuid

import orjson as json
from taskiq import ScheduledTask
from tortoise import fields, models


class BaseModel(models.Model):
    id = fields.IntField(pk=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True


class PeriodicTask(BaseModel):
    class Meta:
        table = "unfazed_taskiq_periodic_task"

    schedule_alias = fields.CharField(
        max_length=255,
        description="The alias of the schedule.",
        default="default",
    )

    name = fields.CharField(
        max_length=255,
        default="NOT_GIVEN",
        description="The name of the task. eg: FF-SG-YOUTUBE",
    )

    description = fields.TextField(
        description="The description of the task.",
        default="",
    )

    task_name = fields.CharField(
        max_length=255,
        description="The task to be executed. This is the path to the task function.",
    )

    task_args = fields.TextField(
        description="The args to be passed to the task function.",
    )

    task_kwargs = fields.TextField(
        description="The kwargs to be passed to the task function.",
    )

    labels = fields.TextField(
        description="The labels to be used to filter the tasks.",
    )

    cron = fields.CharField(
        max_length=255,
        description="The cron expression to be used to schedule the task.",
        default=None,
        null=True,
    )

    time = fields.DatetimeField(
        description="The time to be used to schedule the task.",
        default=None,
        null=True,
    )

    last_run_at = fields.DatetimeField(
        null=True,
        default="1970-01-01 00:00:00",
        description="The last time the task was run.",
    )
    total_run_count = fields.IntField(
        default=0,
        description="The total number of times the task has been run.",
    )

    enabled = fields.SmallIntField(
        default=1,
        description="Whether the task is enabled.",
    )

    schedule_id = fields.CharField(
        max_length=255,
        description="The id of the schedule.",
        default=lambda: str(uuid.uuid4().hex),
        unique=True,
    )

    def to_taskiq_schedule_task(self) -> ScheduledTask:
        base_data = {
            "task_name": self.task_name,
            "args": json.loads(self.task_args.encode()),
            "kwargs": json.loads(self.task_kwargs.encode()),
            "labels": json.loads(self.labels.encode()),
            "schedule_id": self.schedule_id,
        }

        if self.cron:
            base_data["cron"] = self.cron
            return ScheduledTask.model_validate(base_data)

        if self.time:
            base_data["time"] = self.time
            return ScheduledTask.model_validate(base_data)

        raise RuntimeError("No schedule found")
