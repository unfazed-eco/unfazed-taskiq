"""Tests for result_backend models and app."""

import pytest
from unfazed.core import Unfazed

from unfazed_taskiq.contrib.result_backend.app import AppConfig
from unfazed_taskiq.contrib.result_backend.models import TaskStatus


class TestTaskStatus:
    def test_label_property(self) -> None:
        """Test TaskStatus.label returns enum name."""
        assert TaskStatus.STARTED.label == "STARTED"
        assert TaskStatus.SUCCESS.label == "SUCCESS"
        assert TaskStatus.FAILURE.label == "FAILURE"


class TestAppConfig:
    @pytest.mark.asyncio
    async def test_ready(self, unfazed: Unfazed) -> None:
        """Test AppConfig.ready() completes without error."""
        config = AppConfig(unfazed, "unfazed_taskiq.contrib.result_backend.app")
        await config.ready()
