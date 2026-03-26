from unfazed.contrib.admin.registry import ModelAdmin, register

from . import serializer as s


@register(s.TaskiqResultSerializer)
class TaskiqResultAdmin(ModelAdmin):
    route_label: str = "TaskIQ"
    component: str = "ModelAdmin"

    datetime_fields: list[str] = ["date_created", "date_done"]
    json_fields: list[str] = ["task_args", "task_kwargs", "return_value"]

    list_sort: list[str] = [
        "date_created",
        "date_done",
    ]

    can_add: bool = False
    can_delete: bool = True
    can_edit: bool = False

    list_display: list[str] = [
        "task_id",
        "task_name",
        "status",
        "task_args",
        "task_kwargs",
        "return_value",
        "date_created",
        "date_done",
        "schedule_id",
        "traceback",
    ]
    list_order: list[str] = [
        "task_id",
        "task_name",
        "status",
        "task_args",
        "task_kwargs",
        "return_value",
        "date_created",
        "date_done",
        "schedule_id",
        "traceback",
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
        "task_args",
        "task_kwargs",
        "return_value",
        "date_created",
        "date_done",
        "schedule_id",
        "traceback",
    ]
    detail_order: list[str] = [
        "task_id",
        "task_name",
        "status",
        "task_args",
        "task_kwargs",
        "return_value",
        "date_created",
        "date_done",
        "schedule_id",
        "traceback",
    ]
    readonly_fields: list[str] = [
        "task_id",
        "task_name",
        "status",
        "task_args",
        "task_kwargs",
        "return_value",
        "date_created",
        "date_done",
        "schedule_id",
        "traceback",
    ]
