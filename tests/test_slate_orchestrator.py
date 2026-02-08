# Modified: 2026-02-08T08:00:00Z | Author: COPILOT | Change: Add test coverage for slate_orchestrator module
"""
Tests for slate/slate_orchestrator.py — SLATE system orchestrator,
mode detection, service lifecycle, PID management, status reporting.
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slate.slate_orchestrator import (
    WORKSPACE_ROOT,
    PID_FILE,
    STATE_FILE,
    detect_mode,
    SlateOrchestrator,
)


# ── detect_mode ─────────────────────────────────────────────────────────


class TestDetectMode:
    """Tests for detect_mode()."""

    @patch.dict(os.environ, {"SLATE_MODE": "dev"})
    def test_env_dev(self):
        assert detect_mode() == "dev"

    @patch.dict(os.environ, {"SLATE_MODE": "development"})
    def test_env_development(self):
        assert detect_mode() == "dev"

    @patch.dict(os.environ, {"SLATE_MODE": "prod"})
    def test_env_prod(self):
        assert detect_mode() == "prod"

    @patch.dict(os.environ, {"SLATE_MODE": "production"})
    def test_env_production(self):
        assert detect_mode() == "prod"

    @patch.dict(os.environ, {"SLATE_MODE": "", "SLATE_DOCKER": "1"})
    def test_docker_detection(self):
        assert detect_mode() == "prod"

    @patch.dict(os.environ, {"SLATE_MODE": ""}, clear=False)
    def test_venv_implies_dev(self):
        # If .venv exists and no env override, should be dev
        if (WORKSPACE_ROOT / ".venv").exists():
            assert detect_mode() == "dev"

    def test_returns_string(self):
        mode = detect_mode()
        assert mode in ("dev", "prod")


# ── SlateOrchestrator init ──────────────────────────────────────────────


class TestSlateOrchestratorInit:
    """Tests for SlateOrchestrator initialization."""

    def test_default_mode(self):
        orch = SlateOrchestrator()
        assert orch.mode in ("dev", "prod")

    def test_explicit_mode(self):
        orch = SlateOrchestrator(mode="prod")
        assert orch.mode == "prod"

    def test_initial_state(self):
        orch = SlateOrchestrator()
        assert orch.running is False
        assert isinstance(orch.processes, dict)
        assert isinstance(orch._restart_counts, dict)

    def test_workspace_set(self):
        orch = SlateOrchestrator()
        assert orch.workspace == WORKSPACE_ROOT


# ── _get_python ─────────────────────────────────────────────────────────


class TestGetPython:
    """Tests for SlateOrchestrator._get_python()."""

    def test_returns_string(self):
        orch = SlateOrchestrator()
        assert isinstance(orch._get_python(), str)

    def test_contains_python(self):
        orch = SlateOrchestrator()
        assert "python" in orch._get_python().lower()


# ── State management ───────────────────────────────────────────────────


class TestStateManagement:
    """Tests for state save/load."""

    def test_load_state_returns_dict(self):
        orch = SlateOrchestrator()
        state = orch._load_state()
        assert isinstance(state, dict)

    def test_save_state_writes_file(self, tmp_path):
        orch = SlateOrchestrator()
        import slate.slate_orchestrator as mod
        original = mod.STATE_FILE
        mod.STATE_FILE = tmp_path / "test_state.json"
        try:
            orch._save_state({"status": "test", "services": {}})
            assert mod.STATE_FILE.exists()
            saved = json.loads(mod.STATE_FILE.read_text(encoding="utf-8"))
            assert saved["status"] == "test"
            assert "updated_at" in saved
        finally:
            mod.STATE_FILE = original


# ── PID management ──────────────────────────────────────────────────────


class TestPidManagement:
    """Tests for PID file operations."""

    def test_write_and_clear_pid(self, tmp_path):
        orch = SlateOrchestrator()
        import slate.slate_orchestrator as mod
        original = mod.PID_FILE
        mod.PID_FILE = tmp_path / "test.pid"
        try:
            orch._write_pid()
            assert mod.PID_FILE.exists()
            assert mod.PID_FILE.read_text().strip() == str(os.getpid())

            orch._clear_pid()
            assert not mod.PID_FILE.exists()
        finally:
            mod.PID_FILE = original

    def test_check_existing_no_file(self, tmp_path):
        orch = SlateOrchestrator()
        import slate.slate_orchestrator as mod
        original = mod.PID_FILE
        mod.PID_FILE = tmp_path / "nonexistent.pid"
        try:
            assert orch._check_existing() is None
        finally:
            mod.PID_FILE = original

    def test_check_existing_stale_pid(self, tmp_path):
        orch = SlateOrchestrator()
        import slate.slate_orchestrator as mod
        original = mod.PID_FILE
        pid_file = tmp_path / "stale.pid"
        pid_file.write_text("999999999")
        mod.PID_FILE = pid_file
        try:
            result = orch._check_existing()
            assert result is None  # Process doesn't exist
        finally:
            mod.PID_FILE = original


# ── _auto_restart_service ───────────────────────────────────────────────


class TestAutoRestartService:
    """Tests for exponential backoff auto-restart."""

    @patch.object(SlateOrchestrator, "start_dashboard", return_value=True)
    def test_first_restart_succeeds(self, mock_start):
        orch = SlateOrchestrator()
        result = orch._auto_restart_service("dashboard")
        assert result is True
        assert orch._restart_counts["dashboard"] == 1

    def test_max_restarts_blocks(self):
        orch = SlateOrchestrator()
        orch._restart_counts["dashboard"] = 5
        orch._last_restart["dashboard"] = time.time()
        result = orch._auto_restart_service("dashboard")
        assert result is False

    @patch.object(SlateOrchestrator, "start_dashboard", return_value=True)
    def test_counter_resets_after_timeout(self, mock_start):
        orch = SlateOrchestrator()
        orch._restart_counts["dashboard"] = 5
        orch._last_restart["dashboard"] = time.time() - 700  # >10 min
        result = orch._auto_restart_service("dashboard")
        assert result is True

    @patch.object(SlateOrchestrator, "start_dashboard", return_value=True)
    def test_backoff_prevents_rapid_restart(self, mock_start):
        orch = SlateOrchestrator()
        orch._restart_counts["dashboard"] = 2
        orch._last_restart["dashboard"] = time.time()  # Just now
        result = orch._auto_restart_service("dashboard")
        assert result is False  # Backoff should prevent restart


# ── status ──────────────────────────────────────────────────────────────


class TestStatus:
    """Tests for SlateOrchestrator.status()."""

    def test_returns_dict(self):
        orch = SlateOrchestrator()
        status = orch.status()
        assert isinstance(status, dict)

    def test_has_all_sections(self):
        orch = SlateOrchestrator()
        status = orch.status()
        assert "orchestrator" in status
        assert "runner" in status
        assert "dashboard" in status
        assert "workflow" in status
        assert "docker" in status

    def test_orchestrator_has_mode(self):
        orch = SlateOrchestrator(mode="dev")
        status = orch.status()
        assert status["orchestrator"]["mode"] == "dev"

    def test_skip_dashboard_check(self):
        orch = SlateOrchestrator()
        status = orch.status(skip_dashboard_check=True)
        assert status["dashboard"]["running"] is True


# ── print_status ────────────────────────────────────────────────────────


class TestPrintStatus:
    """Tests for SlateOrchestrator.print_status()."""

    def test_prints_output(self, capsys):
        orch = SlateOrchestrator()
        orch.print_status()
        captured = capsys.readouterr()
        assert "SLATE System Status" in captured.out
        assert "Orchestrator" in captured.out
        assert "Runner" in captured.out
        assert "Dashboard" in captured.out
        assert "Workflow" in captured.out

    def test_shows_mode(self, capsys):
        orch = SlateOrchestrator(mode="dev")
        orch.print_status()
        captured = capsys.readouterr()
        assert "DEV" in captured.out


# ── stop ────────────────────────────────────────────────────────────────


class TestStop:
    """Tests for SlateOrchestrator.stop()."""

    def test_stop_sets_shutdown_event(self):
        orch = SlateOrchestrator()
        orch.stop()
        assert orch._shutdown_event.is_set()

    def test_stop_clears_pid(self, tmp_path):
        orch = SlateOrchestrator()
        import slate.slate_orchestrator as mod
        original = mod.PID_FILE
        pid_file = tmp_path / "test.pid"
        pid_file.write_text(str(os.getpid()))
        mod.PID_FILE = pid_file
        try:
            orch.stop()
            assert not pid_file.exists()
        finally:
            mod.PID_FILE = original


# ── CLI main ────────────────────────────────────────────────────────────


class TestMain:
    """Tests for main() CLI entry point."""

    @patch("sys.argv", ["slate_orchestrator.py", "status", "--json"])
    def test_status_json(self, capsys):
        from slate.slate_orchestrator import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "orchestrator" in data

    @patch("sys.argv", ["slate_orchestrator.py", "status"])
    def test_status_text(self, capsys):
        from slate.slate_orchestrator import main
        main()
        captured = capsys.readouterr()
        assert "SLATE System Status" in captured.out
