from pydantic import field_serializer

from unfazed.serializer import Serializer

from . import models as m


class TaskiqResultSerializer(Serializer):

    class Meta:
        model = m.TaskiqResultModel

        # skip for JSON since result is bytes
        exclude = ["result"]
