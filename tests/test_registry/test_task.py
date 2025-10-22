import pytest

from unfazed_taskiq.registry.task import RegistryTask, RegistryTaskSchema


def sample_task(x: int, y: str = "hi") -> None:
    """Sample task used for registry tests."""


def auxiliary_task(flag: bool) -> None:
    pass


class TestRegistryTask:
    def setup_method(self) -> None:
        self.registry = RegistryTask()

    def test_register_broker_creates_schema(self) -> None:
        schedule = [{"cron": "* * * * *"}]
        self.registry.register_broker(
            sample_task, alias_name="alpha", schedule=schedule
        )
        path = f"{sample_task.__module__}.{sample_task.__name__}"
        schema = self.registry.get(path)
        assert isinstance(schema, RegistryTaskSchema)
        assert schema.name == "sample_task"
        assert schema.alias_name == "alpha"
        assert schema.docs == "Sample task used for registry tests."
        assert schema.schedule == schedule
        assert len(schema.params) == 2
        first, second = schema.params
        assert (
            first.name == "x"
            and first.required
            and first.default is None
            and first.hint_type is int
        )
        assert (
            second.name == "y"
            and not second.required
            and second.default == "hi"
            and second.hint_type is str
        )

    def test_duplicate_registration_raises(self) -> None:
        self.registry.register_broker(sample_task)
        with pytest.raises(ValueError):
            self.registry.register_broker(sample_task)

    def test_get_and_filter_path(self) -> None:
        self.registry.register_broker(sample_task, alias_name="alpha")
        self.registry.register_broker(auxiliary_task, alias_name="beta")
        assert self.registry.get("missing") is None
        assert len(self.registry.filter_path()) == 2
        filtered = self.registry.filter_path("auxiliary_task")
        assert len(filtered) == 1 and filtered[0].name == "auxiliary_task"
        assert self.registry.filter_path("absent") == []
