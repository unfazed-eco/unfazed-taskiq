import typing as t
from unfazed_taskiq.schema.registry import RegistryTask


class RegistryService(object):
    def __init__(self) -> None:
        self.tasks: t.Dict[str, RegistryTask] = {}

    def register(self, path: str, task: RegistryTask) -> None:
        if path in self.tasks:
            raise ValueError(f"Task {path} already registered")
        self.tasks[path] = task

    def get(self, path: str) -> t.Optional[RegistryTask]:
        return self.tasks.get(path, None)

    def filter_path(self, keyword: t.Optional[str] = None) -> t.List[RegistryTask]:
        res: t.List[RegistryTask] = []
        for k, v in self.tasks.items():
            if keyword is None or keyword in k:
                res.append(v)
        return res



rs = RegistryService()