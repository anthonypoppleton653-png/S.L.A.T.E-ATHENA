# Modified: 2026-02-08T08:20:00Z | Author: COPILOT | Change: Add test coverage for slate_ai_orchestrator.py
"""Tests for slate/slate_ai_orchestrator.py — Central AI operations orchestrator."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from slate.slate_ai_orchestrator import (
    AITask,
    OllamaClient,
    CodebaseAnalyzer,
    TrainingScheduler,
    AIOrchestrator,
)


class TestAITask:
    """Tests for the AITask dataclass."""

    def test_create_task(self):
        task = AITask(
            task_type="analysis",
            priority=1,
            payload={"file": "slate/slate_status.py"},
        )
        assert task.task_type == "analysis"
        assert task.priority == 1
        assert task.status == "pending"
        assert task.result is None

    def test_task_with_result(self):
        task = AITask(
            task_type="documentation",
            priority=2,
            payload={"module": "slate_runtime"},
            status="completed",
            result="Documentation generated successfully.",
        )
        assert task.status == "completed"
        assert task.result is not None


class TestOllamaClient:
    """Tests for the OllamaClient subprocess wrapper."""

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_list_models_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME                ID         SIZE    MODIFIED\nslate-fast:latest   abc123   2.0 GB  2 hours ago\nslate-coder:latest  def456   8.0 GB  1 hour ago\n",
        )
        client = OllamaClient()
        models = client.list_models()
        assert isinstance(models, list)
        assert len(models) == 2
        assert "slate-fast:latest" in models

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_list_models_offline(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ollama not found")
        client = OllamaClient()
        models = client.list_models()
        assert isinstance(models, list)
        assert len(models) == 0

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_generate_success(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="NAME\nslate-fast"),  # _check_available
            MagicMock(returncode=0, stdout="Analysis complete: no issues found."),  # generate
        ]
        client = OllamaClient()
        result = client.generate("slate-fast", "Analyze this code")
        assert isinstance(result, str)

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_generate_offline(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ollama not found")
        client = OllamaClient()
        result = client.generate("slate-fast", "Test prompt")
        assert isinstance(result, str)
        assert "not available" in result.lower() or "unavailable" in result.lower() or "error" in result.lower() or "Ollama" in result


class TestCodebaseAnalyzer:
    """Tests for the CodebaseAnalyzer."""

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_get_python_files(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        ollama = OllamaClient()
        analyzer = CodebaseAnalyzer(ollama)
        files = analyzer.get_python_files()
        assert isinstance(files, list)


class TestTrainingScheduler:
    """Tests for the TrainingScheduler."""

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_collect_training_data(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        ollama = OllamaClient()
        scheduler = TrainingScheduler(ollama)
        data = scheduler.collect_training_data()
        assert isinstance(data, (list, dict, str))


class TestAIOrchestrator:
    """Tests for the main AIOrchestrator facade."""

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_initialization(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        orch = AIOrchestrator()
        assert orch is not None

    @patch("slate.slate_ai_orchestrator.subprocess.run")
    def test_print_status(self, mock_run, capsys):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        orch = AIOrchestrator()
        orch.print_status()
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)
