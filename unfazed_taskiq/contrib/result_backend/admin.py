from unfazed.contrib.admin.registry import ModelAdmin, register

from . import serializer as s


@register(s.TaskiqResultSerializer)
class TaskiqResultAdmin(ModelAdmin):
    route_label: str = "TaskIQ"
    component: str = "ModelAdmin"

    list_display: list[str] = [
        "task_id",
        "task_name",
        "status",
        "date_done",
        "date_created",
        "schedule_id",
    ]
    search_fields: list[str] = [
        "task_id",
        "task_name",
        "schedule_id",
    ]
    list_search: list[str] = [
        "task_id",
        "task_name",
        "schedule_id",
    ]
    detail_display: list[str] = [
        "task_id",
        "task_name",
        "status",
        "date_done",
        "date_created",
        "schedule_id",
        "task_args",
        "task_kwargs",
        "traceback",
    ]
    readonly_fields: list[str] = [
        "task_id",
        "status",
        "date_done",
        "date_created",
        "task_name",
        "schedule_id",
        "task_args",
        "task_kwargs",
        "traceback",
    ]
