import importlib
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def handler_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    alias = "test_alias"

    def fake_import_setting(key: str) -> Dict[str, Dict[str, object]]:
        assert key == "UNFAZED_SETTINGS_MODULE"
        return {
            "UNFAZED_TASKIQ_SETTINGS": {
                "DEFAULT_TASKIQ_NAME": alias,
                "TASKIQ_CONFIG": {
                    alias: {
                        "BROKER": {
                            "BACKEND": "taskiq.InMemoryBroker",
                            "OPTIONS": {},
                        },
                    }
                },
            }
        }

    monkeypatch.setenv("UNFAZED_SETTINGS_MODULE", "tests.proj.entry.settings")
    monkeypatch.setattr("unfazed.utils.import_setting", fake_import_setting)

    def fake_setup(setup_alias: str, config: object) -> SimpleNamespace:
        return SimpleNamespace(
            alias_name=setup_alias,
            broker=f"broker-{setup_alias}",
            scheduler=f"scheduler-{setup_alias}",
            startup=AsyncMock(name=f"startup-{setup_alias}"),
            shutdown=AsyncMock(name=f"shutdown-{setup_alias}"),
        )

    monkeypatch.setattr("unfazed_taskiq.agent.model.TaskiqAgent.setup", fake_setup)

    sys.modules.pop("unfazed_taskiq.agent.handler", None)
    module = importlib.import_module("unfazed_taskiq.agent.handler")
    return module


class TestAgentHandler:
    def _make_handler(self, module: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
        handler_cls = module.AgentHandler
        with patch.object(handler_cls, "check_ready", autospec=True) as mock_ready:
            mock_ready.side_effect = lambda self: None
            handler = handler_cls()
        return handler

    def test_module_singletons(self, handler_module: Any) -> None:
        alias = handler_module.agents.default_alias_name
        assert (
            handler_module.scheduler == handler_module.agents.storage[alias].scheduler
        )
        assert handler_module.broker == handler_module.agents.storage[alias].broker

    def test_init_triggers_check_ready(self, handler_module: Any) -> None:
        handler_cls = handler_module.AgentHandler
        with patch.object(handler_cls, "check_ready", autospec=True) as mock_ready:
            handler = handler_cls()
        mock_ready.assert_called_once()
        assert isinstance(handler, handler_cls)

    def test_register_and_duplicate(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        agents = MagicMock()
        handler.register("alpha", agents)
        assert handler.storage["alpha"] is agents
        with pytest.raises(ValueError, match="already registered"):
            handler.register("alpha", agents)

    def test_reset(self, handler_module: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler.register("alpha", MagicMock())
        handler.reset()
        assert handler.storage == {}
        assert handler._ready is False

    def test_setup_requires_env(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        monkeypatch.delenv("UNFAZED_SETTINGS_MODULE", raising=False)
        with pytest.raises(ValueError, match="is not set"):
            handler.setup()

    def test_setup_import_error(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        monkeypatch.setenv("UNFAZED_SETTINGS_MODULE", "module.path")
        monkeypatch.setattr(
            handler_module,
            "import_setting",
            MagicMock(side_effect=ImportError("boom")),
        )
        with pytest.raises(ImportError, match="Failed to import settings module: boom"):
            handler.setup()

    def test_setup_invalid_config(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        monkeypatch.setenv("UNFAZED_SETTINGS_MODULE", "module.path")
        monkeypatch.setattr(
            handler_module,
            "import_setting",
            lambda key: {"UNFAZED_TASKIQ_SETTINGS": {"DEFAULT_TASKIQ_NAME": "alpha"}},
        )

        def bad_validate(cls: Any, values: Any) -> Any:
            raise ValueError("bad config")

        monkeypatch.setattr(
            handler_module.UnfazedTaskiqSettings,
            "model_validate",
            classmethod(bad_validate),
        )

        with pytest.raises(
            ValueError, match="Invalid settings configuration: bad config"
        ):
            handler.setup()

    def test_setup_success(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        monkeypatch.setenv("UNFAZED_SETTINGS_MODULE", "module.path")
        config = {
            "DEFAULT_TASKIQ_NAME": "alpha",
            "TASKIQ_CONFIG": {
                "alpha": {
                    "BROKER": {
                        "BACKEND": "taskiq.InMemoryBroker",
                        "OPTIONS": {},
                    }
                }
            },
        }
        monkeypatch.setattr(
            handler_module,
            "import_setting",
            lambda _: {"UNFAZED_TASKIQ_SETTINGS": config},
        )

        fake_agent = SimpleNamespace(
            alias_name="alpha",
            broker="broker-alpha",
            scheduler="scheduler-alpha",
            startup=AsyncMock(),
            shutdown=AsyncMock(),
        )

        monkeypatch.setattr(
            handler_module.TaskiqAgent,
            "setup",
            MagicMock(return_value=fake_agent),
        )

        handler.setup()

        assert handler.default_alias_name == "alpha"
        assert handler.storage["alpha"] is fake_agent
        assert handler._ready is True

    def test_check_ready_paths(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        with (
            patch.object(handler, "reset") as mock_reset,
            patch.object(handler, "setup") as mock_setup,
        ):
            handler._ready = False
            handler.check_ready()
        mock_reset.assert_called_once()
        mock_setup.assert_called_once()

        with (
            patch.object(handler, "reset") as mock_reset,
            patch.object(handler, "setup") as mock_setup,
        ):
            handler._ready = True
            handler.check_ready()
        mock_reset.assert_not_called()
        mock_setup.assert_not_called()

    def test_get_agent_behaviour(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler.default_alias_name = "alpha"
        sentinel_agents = MagicMock()
        handler.storage["alpha"] = sentinel_agents
        handler._ready = True
        assert handler.get_agent(None) is sentinel_agents
        assert handler.get_agent("missing") is None

    def test_get_agent_triggers_ready(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler._ready = False
        with patch.object(handler, "check_ready") as mock_ready:
            handler.get_agent("alpha")
        mock_ready.assert_called_once()

    def test_scheduler_property(
        self, handler_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        node = SimpleNamespace(scheduler="scheduler-alpha")
        handler.storage["alpha"] = node
        handler.default_alias_name = "alpha"
        handler._ready = True
        assert handler.scheduler == "scheduler-alpha"

    def test_scheduler_triggers_ready(
        self, handler_module: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler.storage["alpha"] = SimpleNamespace(scheduler="S")
        handler.default_alias_name = "alpha"
        handler._ready = False

        def mark_ready() -> None:
            handler._ready = True

        with patch.object(handler, "check_ready", side_effect=mark_ready) as mock_ready:
            assert handler.scheduler == "S"
        mock_ready.assert_called_once()

    def test_broker_property(
        self, handler_module: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler.storage["alpha"] = SimpleNamespace(broker="broker-alpha")
        handler.default_alias_name = "alpha"
        handler._ready = True
        assert handler.broker == "broker-alpha"

    def test_broker_triggers_ready(
        self, handler_module: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        handler.storage["alpha"] = SimpleNamespace(broker="B")
        handler.default_alias_name = "alpha"
        handler._ready = False

        def mark_ready() -> None:
            handler._ready = True

        with patch.object(handler, "check_ready", side_effect=mark_ready) as mock_ready:
            assert handler.broker == "B"
        mock_ready.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_iterates_agents(
        self, handler_module: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        first = SimpleNamespace(startup=AsyncMock(), shutdown=AsyncMock())
        second = SimpleNamespace(startup=AsyncMock(), shutdown=AsyncMock())
        handler.storage = {"a": first, "b": second}

        await handler.startup()

        first.startup.assert_awaited_once()
        second.startup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shutdown_iterates_agents(
        self, handler_module: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        handler = self._make_handler(handler_module, monkeypatch)
        first = SimpleNamespace(startup=AsyncMock(), shutdown=AsyncMock())
        second = SimpleNamespace(startup=AsyncMock(), shutdown=AsyncMock())
        handler.storage = {"a": first, "b": second}

        await handler.shutdown()

        first.shutdown.assert_awaited_once()
        second.shutdown.assert_awaited_once()
