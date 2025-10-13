from unfazed.contrib.admin.registry import ModelAdmin, register

from . import serializer as s


@register(s.PeriodicTaskSerializer)
class PeriodicTaskAdmin(ModelAdmin):
    route_label: str = "TaskIQ"
    component: str = "ModelAdmin"

    list_display: list[str] = [
        "schedule_alias",
        "name",
        "description",
        "task_name",
        "task_args",
        "task_kwargs",
        "labels",
        "cron",
        "last_run_at",
        "time",
        "total_run_count",
        "enabled",
    ]
    search_fields: list[str] = [
        "schedule_alias",
        "name",
        "task_name",
    ]
    list_search: list[str] = [
        "schedule_alias",
        "name",
        "task_name",
    ]
    detail_display: list[str] = [
        "schedule_alias",
        "name",
        "description",
        "task_name",
        "task_args",
        "task_kwargs",
        "labels",
        "cron",
        "time",
        "last_run_at",
        "total_run_count",
        "enabled",
        "schedule_id",
    ]
    readonly_fields: list[str] = [
        "last_run_at",
        "total_run_count",
        "schedule_id",
    ]
