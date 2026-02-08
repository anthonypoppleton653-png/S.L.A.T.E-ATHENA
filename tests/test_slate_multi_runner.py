# Modified: 2026-02-08T08:20:00Z | Author: COPILOT | Change: Add test coverage for slate_multi_runner.py
"""Tests for slate/slate_multi_runner.py — Multi-runner parallel coordination."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from slate.slate_multi_runner import (
    RunnerInstance,
    MultiRunnerConfig,
    MultiRunnerCoordinator,
)


class TestRunnerInstance:
    """Tests for the RunnerInstance dataclass."""

    def test_create_instance(self):
        runner = RunnerInstance(
            id="runner-1",
            name="slate-runner",
            profile="gpu-light",
            gpu_id=0,
        )
        assert runner.id == "runner-1"
        assert runner.status == "idle"
        assert runner.profile == "gpu-light"
        assert runner.gpu_id == 0

    def test_defaults(self):
        runner = RunnerInstance(
            id="runner-2",
            name="slate-cpu",
            profile="cpu",
            gpu_id=None,
        )
        assert runner.status == "idle"
        assert runner.current_task is None
        assert runner.started_at is None
        assert runner.tasks_completed == 0


class TestMultiRunnerConfig:
    """Tests for the MultiRunnerConfig dataclass."""

    def test_default_config(self):
        config = MultiRunnerConfig()
        assert isinstance(config.runners, list)
        assert len(config.runners) == 0
        assert config.max_parallel_workflows == 8
        assert isinstance(config.gpu_reservation, dict)

    def test_config_with_runners(self):
        runners = [
            RunnerInstance(id="r1", name="runner-1", profile="gpu-light", gpu_id=0),
            RunnerInstance(id="r2", name="runner-2", profile="cpu", gpu_id=None),
        ]
        config = MultiRunnerConfig(
            runners=runners,
            max_parallel_workflows=4,
        )
        assert len(config.runners) == 2
        assert config.max_parallel_workflows == 4


class TestMultiRunnerCoordinator:
    """Tests for the MultiRunnerCoordinator class."""

    def test_initialization(self):
        coord = MultiRunnerCoordinator()
        assert coord is not None
        assert coord.config is None  # Not initialized yet

    @patch("slate.slate_multi_runner.RunnerBenchmark")
    def test_get_status_with_config(self, mock_bench):
        mock_bench.return_value = MagicMock()
        coord = MultiRunnerCoordinator()
        # Manually set config instead of initializing (avoids benchmark)
        coord.config = MultiRunnerConfig(
            runners=[
                RunnerInstance(id="r1", name="runner-1", profile="gpu-light", gpu_id=0),
                RunnerInstance(id="r2", name="runner-2", profile="cpu", gpu_id=None, status="running", current_task="task-1"),
            ],
            gpu_reservation={0: ["r1"]},
        )
        status = coord.get_status()
        assert isinstance(status, dict)
        assert status["total_runners"] == 2
        assert status["running"] == 1
        assert status["idle"] == 1

    @patch("slate.slate_multi_runner.RunnerBenchmark")
    def test_assign_task(self, mock_bench):
        mock_bench.return_value = MagicMock()
        coord = MultiRunnerCoordinator()
        coord.config = MultiRunnerConfig(
            runners=[
                RunnerInstance(id="r1", name="runner-1", profile="cpu", gpu_id=None),
            ],
        )
        # Mock _save_config to avoid file I/O
        coord._save_config = MagicMock()
        runner = coord.assign_task("task-001", "cpu")
        assert runner is not None
        assert runner.id == "r1"
        assert runner.status == "running"
        assert runner.current_task == "task-001"

    @patch("slate.slate_multi_runner.RunnerBenchmark")
    def test_assign_task_no_available(self, mock_bench):
        mock_bench.return_value = MagicMock()
        coord = MultiRunnerCoordinator()
        coord.config = MultiRunnerConfig(
            runners=[
                RunnerInstance(id="r1", name="runner-1", profile="gpu-light", gpu_id=0, status="running", current_task="t1"),
            ],
        )
        coord._save_config = MagicMock()
        runner = coord.assign_task("task-002", "gpu-light")
        assert runner is None

    @patch("slate.slate_multi_runner.RunnerBenchmark")
    def test_complete_task(self, mock_bench):
        mock_bench.return_value = MagicMock()
        coord = MultiRunnerCoordinator()
        coord.config = MultiRunnerConfig(
            runners=[
                RunnerInstance(id="r1", name="runner-1", profile="cpu", gpu_id=None, status="running", current_task="t1"),
            ],
        )
        coord._save_config = MagicMock()
        coord.complete_task("r1", success=True)
        assert coord.config.runners[0].status == "idle"
        assert coord.config.runners[0].current_task is None
        assert coord.config.runners[0].tasks_completed == 1

    @patch("slate.slate_multi_runner.RunnerBenchmark")
    def test_print_status(self, mock_bench, capsys):
        mock_bench.return_value = MagicMock()
        coord = MultiRunnerCoordinator()
        coord.config = MultiRunnerConfig()
        coord.print_status()
        captured = capsys.readouterr()
        assert "Multi-Runner" in captured.out
