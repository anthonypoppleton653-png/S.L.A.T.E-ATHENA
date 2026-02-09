# Modified: 2026-02-08T08:00:00Z | Author: COPILOT | Change: Add test coverage for slate_fork_deps module
"""
Tests for slate/slate_fork_deps.py — Fork dependency manager,
fork status checking, sync operations, and CLI.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from slate.slate_fork_deps import (
    FORKED_DEPS,
    WORKSPACE_ROOT,
    SlateForkManager,
)


# ── FORKED_DEPS config ──────────────────────────────────────────────────


class TestForkedDeps:
    """Tests for FORKED_DEPS configuration."""

    def test_is_dict(self):
        assert isinstance(FORKED_DEPS, dict)

    def test_has_entries(self):
        assert len(FORKED_DEPS) > 0

    def test_each_entry_has_required_keys(self):
        for name, dep in FORKED_DEPS.items():
            assert "upstream" in dep, f"{name} missing upstream"
            assert "fork" in dep, f"{name} missing fork"
            assert "branch" in dep, f"{name} missing branch"
            assert "category" in dep, f"{name} missing category"

    def test_upstream_format(self):
        for name, dep in FORKED_DEPS.items():
            parts = dep["upstream"].split("/")
            assert len(parts) == 2, f"{name} upstream should be owner/repo"

    def test_fork_format(self):
        for name, dep in FORKED_DEPS.items():
            parts = dep["fork"].split("/")
            assert len(parts) == 2, f"{name} fork should be owner/repo"

    def test_categories_valid(self):
        valid = {"claude", "ai", "database", "github"}
        for name, dep in FORKED_DEPS.items():
            assert dep["category"] in valid, f"{name} has unknown category {dep['category']}"

    def test_known_forks_present(self):
        assert "transformers" in FORKED_DEPS
        assert "chroma" in FORKED_DEPS
        assert "runner" in FORKED_DEPS


# ── SlateForkManager init ──────────────────────────────────────────────


class TestSlateForkManagerInit:
    """Tests for SlateForkManager initialization."""

    def test_workspace_set(self):
        mgr = SlateForkManager()
        assert mgr.workspace == WORKSPACE_ROOT

    def test_gh_cli_is_string(self):
        mgr = SlateForkManager()
        assert isinstance(mgr.gh_cli, str)


# ── _find_gh_cli ────────────────────────────────────────────────────────


class TestFindGhCli:
    """Tests for SlateForkManager._find_gh_cli()."""

    def test_returns_string(self):
        mgr = SlateForkManager()
        result = mgr._find_gh_cli()
        assert isinstance(result, str)

    def test_default_is_gh(self):
        mgr = SlateForkManager()
        # If .tools/gh.exe doesn't exist, should fall back to "gh"
        from pathlib import Path
        local_gh = mgr.workspace / ".tools" / "gh.exe"
        if not local_gh.exists():
            assert mgr.gh_cli == "gh"


# ── check_auth ──────────────────────────────────────────────────────────


class TestCheckAuth:
    """Tests for SlateForkManager.check_auth()."""

    @patch.object(SlateForkManager, "_run_gh")
    def test_auth_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        mgr = SlateForkManager()
        assert mgr.check_auth() is True

    @patch.object(SlateForkManager, "_run_gh")
    def test_auth_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        mgr = SlateForkManager()
        assert mgr.check_auth() is False


# ── get_fork_status ────────────────────────────────────────────────────


class TestGetForkStatus:
    """Tests for SlateForkManager.get_fork_status()."""

    def test_unknown_fork(self):
        mgr = SlateForkManager()
        result = mgr.get_fork_status("nonexistent_fork")
        assert result["exists"] is False
        assert "error" in result or "Unknown" in str(result.get("error", ""))

    @patch.object(SlateForkManager, "_run_gh")
    def test_fork_exists(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"updatedAt": "2026-02-08T00:00:00Z"}'
        )
        mgr = SlateForkManager()
        result = mgr.get_fork_status("transformers")
        assert result["exists"] is True
        assert result["name"] == "transformers"
        assert "last_sync" in result

    @patch.object(SlateForkManager, "_run_gh")
    def test_fork_not_found(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )
        mgr = SlateForkManager()
        result = mgr.get_fork_status("transformers")
        assert result["exists"] is False
        assert "error" in result

    def test_returns_upstream_info(self):
        mgr = SlateForkManager()
        # Even with network issues, should return metadata
        result = mgr.get_fork_status("chroma")
        assert result["upstream"] == "chroma-core/chroma"
        assert result["fork"] == "SynchronizedLivingArchitecture/chroma"


# ── get_all_status ──────────────────────────────────────────────────────


class TestGetAllStatus:
    """Tests for SlateForkManager.get_all_status()."""

    @patch.object(SlateForkManager, "_run_gh")
    def test_returns_all_forks(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"updatedAt": "2026-02-08T00:00:00Z"}'
        )
        mgr = SlateForkManager()
        result = mgr.get_all_status()
        assert isinstance(result, dict)
        assert set(result.keys()) == set(FORKED_DEPS.keys())


# ── sync_fork ───────────────────────────────────────────────────────────


class TestSyncFork:
    """Tests for SlateForkManager.sync_fork()."""

    def test_unknown_fork_returns_false(self):
        mgr = SlateForkManager()
        assert mgr.sync_fork("nonexistent") is False

    @patch.object(SlateForkManager, "_run_gh")
    def test_sync_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mgr = SlateForkManager()
        result = mgr.sync_fork("transformers")
        assert result is True

    @patch.object(SlateForkManager, "_run_gh")
    def test_sync_already_up_to_date(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="already up to date")
        mgr = SlateForkManager()
        result = mgr.sync_fork("transformers")
        assert result is True  # "already" in stderr counts as success

    @patch.object(SlateForkManager, "_run_gh")
    def test_sync_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="permission denied")
        mgr = SlateForkManager()
        result = mgr.sync_fork("transformers")
        assert result is False


# ── sync_all ────────────────────────────────────────────────────────────


class TestSyncAll:
    """Tests for SlateForkManager.sync_all()."""

    @patch.object(SlateForkManager, "_run_gh")
    def test_returns_dict(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mgr = SlateForkManager()
        result = mgr.sync_all()
        assert isinstance(result, dict)
        assert len(result) == len(FORKED_DEPS)


# ── print_status ────────────────────────────────────────────────────────


class TestPrintStatus:
    """Tests for SlateForkManager.print_status()."""

    @patch.object(SlateForkManager, "check_auth", return_value=False)
    def test_no_auth_shows_warning(self, mock_auth, capsys):
        mgr = SlateForkManager()
        mgr.print_status()
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out

    @patch.object(SlateForkManager, "check_auth", return_value=True)
    @patch.object(SlateForkManager, "get_fork_status")
    def test_prints_fork_list(self, mock_status, mock_auth, capsys):
        mock_status.return_value = {"exists": True}
        mgr = SlateForkManager()
        mgr.print_status()
        captured = capsys.readouterr()
        assert "Forked Dependencies" in captured.out


# ── CLI main ────────────────────────────────────────────────────────────


class TestMain:
    """Tests for main() CLI entry point."""

    @patch("sys.argv", ["slate_fork_deps.py", "--list"])
    def test_list_flag(self, capsys):
        from slate.slate_fork_deps import main
        main()
        captured = capsys.readouterr()
        assert "transformers" in captured.out
        assert "chroma" in captured.out

    @patch("sys.argv", ["slate_fork_deps.py", "--json"])
    @patch.object(SlateForkManager, "_run_gh")
    def test_json_flag(self, mock_run, capsys):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"updatedAt": "2026-02-08T00:00:00Z"}'
        )
        from slate.slate_fork_deps import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, dict)
        assert "transformers" in data
