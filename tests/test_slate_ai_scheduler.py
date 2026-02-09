# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for slate_ai_scheduler module
"""
Tests for slate/slate_ai_scheduler.py — AI task scheduler
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.slate_ai_scheduler import (
        TaskStatus,
        AITask,
        GPUState,
        GPUHealthStatus,
        AIScheduler,
        OllamaClient,
        GPU_CONFIG,
        MODEL_VRAM,
        TASK_MODELS,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"slate_ai_scheduler not importable: {e}", allow_module_level=True)


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_pending_status(self):
        assert TaskStatus.PENDING.value is not None

    def test_has_running_status(self):
        assert hasattr(TaskStatus, "RUNNING") or hasattr(TaskStatus, "ACTIVE")


class TestAITask:
    """Test AITask dataclass."""

    def test_create_task(self):
        task = AITask(
            id="test_1",
            task_type="code_generation",
            prompt="Write a function",
            priority=5,
        )
        assert task.id == "test_1"
        assert task.task_type == "code_generation"

    def test_task_to_dict(self):
        task = AITask(
            id="test_1",
            task_type="analysis",
            prompt="Analyze code",
            priority=3,
        )
        d = task.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "test_1"

    def test_task_from_dict(self):
        data = {
            "id": "test_2",
            "task_type": "summarization",
            "prompt": "Summarize",
            "priority": 7,
        }
        task = AITask.from_dict(data)
        assert task.id == "test_2"
        assert task.priority == 7


class TestGPUConfig:
    """Test GPU configuration constants."""

    def test_gpu_config_has_two_gpus(self):
        assert 0 in GPU_CONFIG
        assert 1 in GPU_CONFIG

    def test_gpu_config_has_vram(self):
        for gpu_id, config in GPU_CONFIG.items():
            assert "vram_mb" in config
            assert config["vram_mb"] > 0

    def test_gpu_config_has_preferred_tasks(self):
        for gpu_id, config in GPU_CONFIG.items():
            assert "preferred_tasks" in config
            assert isinstance(config["preferred_tasks"], list)


class TestModelVRAM:
    """Test model VRAM requirements."""

    def test_model_vram_is_dict(self):
        assert isinstance(MODEL_VRAM, dict)

    def test_model_vram_has_entries(self):
        assert len(MODEL_VRAM) > 0

    def test_slate_models_included(self):
        # At least some SLATE models should be defined
        model_names = list(MODEL_VRAM.keys())
        slate_models = [m for m in model_names if "slate" in m.lower()]
        assert len(slate_models) > 0


class TestOllamaClient:
    """Test OllamaClient class."""

    def test_init(self):
        client = OllamaClient()
        assert client is not None

    @patch("slate.slate_ai_scheduler.urllib.request.urlopen")
    def test_is_running_true(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"models":[]}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock()
        mock_urlopen.return_value = mock_response
        client = OllamaClient()
        assert client.is_running() is True

    @patch("slate.slate_ai_scheduler.urllib.request.urlopen")
    def test_is_running_false(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")
        client = OllamaClient()
        assert client.is_running() is False


class TestAIScheduler:
    """Test AIScheduler class."""

    @patch("slate.slate_ai_scheduler.subprocess.run")
    def test_init(self, mock_run, tmp_path):
        with patch("slate.slate_ai_scheduler.STATE_FILE", tmp_path / "state.json"), \
             patch("slate.slate_ai_scheduler.QUEUE_FILE", tmp_path / "queue.json"):
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            scheduler = AIScheduler()
            assert scheduler is not None
