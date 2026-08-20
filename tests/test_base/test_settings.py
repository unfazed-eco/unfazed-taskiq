import enum
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any

import pytest

from unfazed_taskiq import settings as settings_module
from unfazed_taskiq.settings import Broker

AIO_PIKA_BACKEND = "taskiq_aio_pika.AioPikaBroker"


def _build_broker(options: dict[str, Any] | None) -> Broker:
    return Broker(BACKEND=AIO_PIKA_BACKEND, OPTIONS=options)


def _patch_version(monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    monkeypatch.setattr(settings_module, "package_version", lambda _name: version)


def _install_fake_aio_pika_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Fake the symbols imported by the new-version conversion branch.

    ``normalize_aio_pika_options`` does ``from taskiq_aio_pika import Exchange,
    Queue, QueueType`` only when the installed version is >= 0.6.0. Faking the
    module keeps the conversion logic testable regardless of which version is
    actually installed in the test environment.
    """

    class QueueType(str, enum.Enum):
        QUORUM = "quorum"
        CLASSIC = "classic"

    @dataclass(frozen=True)
    class Exchange:
        name: str = "taskiq"
        type: str = "topic"

    @dataclass(frozen=True)
    class Queue:
        name: str = "taskiq"
        routing_key: str | None = None
        type: QueueType = QueueType.QUORUM

    module = ModuleType("taskiq_aio_pika")
    setattr(module, "Exchange", Exchange)
    setattr(module, "Queue", Queue)
    setattr(module, "QueueType", QueueType)
    monkeypatch.setitem(sys.modules, "taskiq_aio_pika", module)
    return module


def test_version_at_least() -> None:
    assert settings_module._version_at_least("0.4.2", (0, 6, 0)) is False
    assert settings_module._version_at_least("0.5.0", (0, 6, 0)) is False
    assert settings_module._version_at_least("0.6.0", (0, 6, 0)) is True
    assert settings_module._version_at_least("0.6.0rc0", (0, 6, 0)) is True


def test_new_version_converts_legacy_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_aio_pika_module(monkeypatch)
    _patch_version(monkeypatch, "0.6.0")
    broker = _build_broker(
        {"url": "amqp://x", "exchange_name": "ex", "queue_name": "q"}
    )

    options = broker.options
    assert options is not None
    assert "exchange_name" not in options
    assert "queue_name" not in options

    exchange = options["exchange"]
    assert exchange.name == "ex"
    # The legacy default exchange type was TOPIC.
    assert exchange.type == "topic"

    queue = options["task_queues"][0]
    assert queue.name == "q"
    assert queue.routing_key == "q"
    # The legacy default had no x-queue-type, i.e. classic.
    assert queue.type.value == "classic"


def test_old_version_passes_legacy_keys_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_version(monkeypatch, "0.5.0")
    broker = _build_broker({"exchange_name": "ex", "queue_name": "q"})

    assert broker.options == {"exchange_name": "ex", "queue_name": "q"}


def test_old_version_emits_deprecation_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_version(monkeypatch, "0.5.0")
    with pytest.warns(FutureWarning, match="below 0.6.0"):
        _build_broker({"exchange_name": "ex", "queue_name": "q"})


def test_new_version_does_not_override_new_style_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_aio_pika_module(monkeypatch)
    _patch_version(monkeypatch, "0.6.0")
    broker = _build_broker(
        {
            "exchange_name": "legacy-ex",
            "queue_name": "legacy-q",
            "exchange": "NEW_EXCHANGE",
            "task_queues": ["NEW_QUEUE"],
        }
    )

    assert broker.options is not None
    assert broker.options["exchange"] == "NEW_EXCHANGE"
    assert broker.options["task_queues"] == ["NEW_QUEUE"]
    assert "exchange_name" not in broker.options
    assert "queue_name" not in broker.options


def test_other_backend_is_untouched(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_version(monkeypatch, "0.6.0")
    broker = Broker(
        BACKEND="taskiq.InMemoryBroker",
        OPTIONS={"exchange_name": "ex", "queue_name": "q"},
    )

    assert broker.options == {"exchange_name": "ex", "queue_name": "q"}


def test_missing_package_is_untouched(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str) -> str:
        raise settings_module.PackageNotFoundError("taskiq-aio-pika")

    monkeypatch.setattr(settings_module, "package_version", _raise)
    broker = _build_broker({"exchange_name": "ex", "queue_name": "q"})

    assert broker.options == {"exchange_name": "ex", "queue_name": "q"}
