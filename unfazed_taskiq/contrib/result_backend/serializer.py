from unfazed.serializer import Serializer

from . import models as m


class TaskiqResultSerializer(Serializer):

    class Meta:
        model = m.TaskiqResultModel

        # result 为 BinaryField(bytes)，JSON 无法序列化，故排除
        exclude = ["result"]
