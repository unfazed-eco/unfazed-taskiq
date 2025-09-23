from unfazed.contrib.admin.registry import ModelAdmin, register

from . import serializer as s


@register(s.PeriodicTaskSerializer)
class PeriodicTaskAdmin(ModelAdmin):
    route_label = "TaskIQ"
    component = "ModelAdmin"
