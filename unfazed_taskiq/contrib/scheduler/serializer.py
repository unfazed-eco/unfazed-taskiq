from unfazed.serializer import Serializer

from . import models as m


class PeriodicTaskSerializer(Serializer):
    class Meta:
        model = m.PeriodicTask
