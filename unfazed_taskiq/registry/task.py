import inspect
from typing import Any, Callable, List, Optional, get_type_hints

from unfazed.utils import Storage

from unfazed_taskiq.schema.registry.task import RegistryTaskParam, RegistryTaskSchema


class RegistryTask(Storage[RegistryTaskSchema]):
    def _register(self, path: str, task: RegistryTaskSchema) -> None:
        if path in self.storage:
            raise ValueError(f"Task {path} already registered")
        self.storage[path] = task

    def get(self, path: str) -> Optional[RegistryTaskSchema]:
        return self.storage.get(path, None)

    def filter_path(self, keyword: Optional[str] = None) -> List[RegistryTaskSchema]:
        res: List[RegistryTaskSchema] = []
        for k, v in self.storage.items():
            if keyword is None or keyword in k:
                res.append(v)
        return res

    def register_broker(
        self,
        func: Callable,
        alias_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        params_info: list[RegistryTaskParam] = []
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        for name, param in sig.parameters.items():
            param_type = type_hints.get(name, Any)
            required = param.default is inspect.Parameter.empty
            default = None if required else param.default

            params_info.append(
                RegistryTaskParam(
                    **{
                        "name": name,
                        "hint_type": param_type,
                        "required": required,
                        "default": default,
                    }
                )
            )
        registry_task: RegistryTaskSchema = RegistryTaskSchema(
            name=func.__name__,
            alias_name=alias_name,
            params=params_info,
            docs=func.__doc__ or "",
            schedule=kwargs.get("schedule", None),
        )

        task_path = f"{func.__module__}.{func.__name__}"

        self._register(task_path, registry_task)


rs = RegistryTask()
