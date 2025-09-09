from unfazed.contrib.admin.registry import ModelAdmin, register

from . import serializer as s


@register(serializer_cls=s.PeriodicTaskSerializer)
class PeriodicTaskAdmin(ModelAdmin):
    list_display = ("task_name", "description", "cron", "time", "enabled")
