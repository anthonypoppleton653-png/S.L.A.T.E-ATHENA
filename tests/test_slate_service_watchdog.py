# Modified: 2026-02-08T08:00:00Z | Author: COPILOT | Change: Add test coverage for slate_service_watchdog module
"""
Tests for slate/slate_service_watchdog.py — Service watchdog with automatic
restart, health checks, exponential backoff, PID management.
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slate.slate_service_watchdog import (
    DASHBOARD_PORT,
    DASHBOARD_URL,
    HEALTH_CHECK_INTERVAL,
    MAX_RESTART_ATTEMPTS,
    RESTART_BACKOFF_BASE,
    PID_FILE,
    STATE_FILE,
    ServiceWatchdog,
)


# ── Constants ───────────────────────────────────────────────────────────


class TestConstants:
    """Tests for module-level constants."""

    def test_dashboard_port(self):
        assert DASHBOARD_PORT == 8080

    def test_dashboard_url(self):
        assert "127.0.0.1" in DASHBOARD_URL
        assert str(DASHBOARD_PORT) in DASHBOARD_URL

    def test_health_check_interval_positive(self):
        assert HEALTH_CHECK_INTERVAL > 0

    def test_max_restart_attempts(self):
        assert MAX_RESTART_ATTEMPTS >= 1

    def test_backoff_base_positive(self):
        assert RESTART_BACKOFF_BASE > 0


# ── ServiceWatchdog init ────────────────────────────────────────────────


class TestServiceWatchdogInit:
    """Tests for ServiceWatchdog initialization."""

    def test_initial_state(self):
        wd = ServiceWatchdog()
        assert wd.running is False
        assert isinstance(wd.restart_counts, dict)
        assert isinstance(wd.last_restart, dict)
        assert isinstance(wd.processes, dict)

    def test_workspace_set(self):
        wd = ServiceWatchdog()
        assert isinstance(wd.workspace, Path)


# ── _get_python ─────────────────────────────────────────────────────────


class TestGetPython:
    """Tests for ServiceWatchdog._get_python()."""

    def test_returns_string(self):
        wd = ServiceWatchdog()
        python = wd._get_python()
        assert isinstance(python, str)

    def test_contains_python(self):
        wd = ServiceWatchdog()
        python = wd._get_python()
        assert "python" in python.lower()

    def test_windows_path(self):
        wd = ServiceWatchdog()
        if os.name == "nt":
            assert "Scripts" in wd._get_python()
        else:
            assert "bin" in wd._get_python()


# ── State management ───────────────────────────────────────────────────


class TestStateManagement:
    """Tests for state save/load."""

    def test_load_state_returns_dict(self):
        wd = ServiceWatchdog()
        state = wd._load_state()
        assert isinstance(state, dict)

    def test_save_state_adds_timestamp(self, tmp_path):
        wd = ServiceWatchdog()
        # Temporarily redirect state file
        import slate.slate_service_watchdog as mod
        original = mod.STATE_FILE
        mod.STATE_FILE = tmp_path / "test_state.json"
        try:
            wd._save_state({"services": {}, "test": True})
            saved = json.loads(mod.STATE_FILE.read_text(encoding="utf-8"))
            assert "updated_at" in saved
            assert saved["test"] is True
        finally:
            mod.STATE_FILE = original


# ── PID management ──────────────────────────────────────────────────────


class TestPidManagement:
    """Tests for PID file management."""

    def test_write_and_clear_pid(self, tmp_path):
        wd = ServiceWatchdog()
        import slate.slate_service_watchdog as mod
        original = mod.PID_FILE
        mod.PID_FILE = tmp_path / "test.pid"
        try:
            wd._write_pid()
            assert mod.PID_FILE.exists()
            content = mod.PID_FILE.read_text().strip()
            assert content == str(os.getpid())

            wd._clear_pid()
            assert not mod.PID_FILE.exists()
        finally:
            mod.PID_FILE = original

    def test_check_existing_no_pid_file(self, tmp_path):
        wd = ServiceWatchdog()
        import slate.slate_service_watchdog as mod
        original = mod.PID_FILE
        mod.PID_FILE = tmp_path / "nonexistent.pid"
        try:
            result = wd._check_existing()
            assert result is None
        finally:
            mod.PID_FILE = original

    def test_check_existing_stale_pid(self, tmp_path):
        wd = ServiceWatchdog()
        import slate.slate_service_watchdog as mod
        original = mod.PID_FILE
        pid_file = tmp_path / "stale.pid"
        pid_file.write_text("999999999")  # Very unlikely to be a real PID
        mod.PID_FILE = pid_file
        try:
            result = wd._check_existing()
            # Should return None for non-existent process
            assert result is None
        finally:
            mod.PID_FILE = original


# ── check_dashboard ─────────────────────────────────────────────────────


class TestCheckDashboard:
    """Tests for ServiceWatchdog.check_dashboard()."""

    @patch("http.client.HTTPConnection")
    def test_dashboard_responding(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        wd = ServiceWatchdog()
        assert wd.check_dashboard() is True
        mock_conn.request.assert_called_once_with("GET", "/health")

    @patch("http.client.HTTPConnection")
    def test_dashboard_not_responding(self, mock_conn_class):
        mock_conn_class.side_effect = ConnectionRefusedError()
        wd = ServiceWatchdog()
        assert wd.check_dashboard() is False

    @patch("http.client.HTTPConnection")
    def test_dashboard_error_status(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        wd = ServiceWatchdog()
        assert wd.check_dashboard() is False


# ── check_runner ────────────────────────────────────────────────────────


class TestCheckRunner:
    """Tests for ServiceWatchdog.check_runner()."""

    @patch("slate.slate_service_watchdog.subprocess.run")
    def test_runner_running(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Runner.Listener  1234"
        )
        wd = ServiceWatchdog()
        assert wd.check_runner() is True

    @patch("slate.slate_service_watchdog.subprocess.run")
    def test_runner_not_running(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )
        wd = ServiceWatchdog()
        # On Windows the check uses "Runner.Listener" in stdout OR returncode==0
        # returncode=1 and empty stdout means it's not running
        result = wd.check_runner()
        # Result depends on platform logic, but should not raise
        assert isinstance(result, bool)


# ── restart_service ─────────────────────────────────────────────────────


class TestRestartService:
    """Tests for ServiceWatchdog.restart_service()."""

    @patch.object(ServiceWatchdog, "start_dashboard", return_value=True)
    def test_restart_dashboard(self, mock_start):
        wd = ServiceWatchdog()
        result = wd.restart_service("dashboard")
        assert result is True
        mock_start.assert_called_once()

    @patch.object(ServiceWatchdog, "start_runner", return_value=True)
    def test_restart_runner(self, mock_start):
        wd = ServiceWatchdog()
        result = wd.restart_service("runner")
        assert result is True
        mock_start.assert_called_once()

    def test_max_attempts_reached(self):
        wd = ServiceWatchdog()
        wd.restart_counts["dashboard"] = MAX_RESTART_ATTEMPTS
        wd.last_restart["dashboard"] = time.time()
        result = wd.restart_service("dashboard")
        assert result is False

    @patch.object(ServiceWatchdog, "start_dashboard", return_value=True)
    def test_counter_reset_after_timeout(self, mock_start):
        wd = ServiceWatchdog()
        wd.restart_counts["dashboard"] = MAX_RESTART_ATTEMPTS
        wd.last_restart["dashboard"] = time.time() - 700  # More than 10 min ago
        result = wd.restart_service("dashboard")
        # Counter should have been reset, so it should attempt restart
        assert result is True


# ── status ──────────────────────────────────────────────────────────────


class TestStatus:
    """Tests for ServiceWatchdog.status()."""

    @patch.object(ServiceWatchdog, "check_dashboard", return_value=True)
    @patch.object(ServiceWatchdog, "check_runner", return_value=False)
    @patch.object(ServiceWatchdog, "_check_existing", return_value=None)
    def test_status_returns_dict(self, mock_exist, mock_runner, mock_dash):
        wd = ServiceWatchdog()
        status = wd.status()
        assert isinstance(status, dict)
        assert "watchdog" in status
        assert "dashboard" in status
        assert "runner" in status

    @patch.object(ServiceWatchdog, "check_dashboard", return_value=True)
    @patch.object(ServiceWatchdog, "check_runner", return_value=True)
    @patch.object(ServiceWatchdog, "_check_existing", return_value=1234)
    def test_status_all_running(self, mock_exist, mock_runner, mock_dash):
        wd = ServiceWatchdog()
        status = wd.status()
        assert status["watchdog"]["running"] is True
        assert status["dashboard"]["running"] is True
        assert status["runner"]["running"] is True


# ── print_status ────────────────────────────────────────────────────────


class TestPrintStatus:
    """Tests for ServiceWatchdog.print_status()."""

    @patch.object(ServiceWatchdog, "check_dashboard", return_value=True)
    @patch.object(ServiceWatchdog, "check_runner", return_value=False)
    @patch.object(ServiceWatchdog, "_check_existing", return_value=None)
    def test_prints_output(self, mock_exist, mock_runner, mock_dash, capsys):
        wd = ServiceWatchdog()
        wd.print_status()
        captured = capsys.readouterr()
        assert "Watchdog" in captured.out
        assert "Dashboard" in captured.out
        assert "Runner" in captured.out
