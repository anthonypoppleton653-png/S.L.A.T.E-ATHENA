# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for slate_fork_sync module
"""
Tests for slate/slate_fork_sync.py — Fork sync with vendor deps
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.slate_fork_sync import (
        ForkInfo,
        FORK_REGISTRY,
        check_fork_status,
        get_all_fork_status,
        sync_all_forks,
        run_gh_command,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"slate_fork_sync not importable: {e}", allow_module_level=True)


class TestForkInfo:
    """Test ForkInfo dataclass."""

    def test_create_fork_info(self):
        info = ForkInfo(
            name="test-fork",
            upstream="openai/test",
            fork="SLA/test",
            purpose="Testing"
        )
        assert info.name == "test-fork"
        assert info.upstream == "openai/test"
        assert info.integration_files == []

    def test_fork_info_with_submodule(self):
        info = ForkInfo(
            name="test-fork",
            upstream="openai/test",
            fork="SLA/test",
            purpose="Testing",
            submodule_path="vendor/test"
        )
        assert info.submodule_path == "vendor/test"


class TestForkRegistry:
    """Test the fork registry."""

    def test_registry_is_list(self):
        assert isinstance(FORK_REGISTRY, list)

    def test_registry_has_entries(self):
        assert len(FORK_REGISTRY) > 0

    def test_registry_entries_are_fork_info(self):
        for fork in FORK_REGISTRY:
            assert isinstance(fork, ForkInfo)
            assert fork.name
            assert fork.upstream
            assert fork.fork


class TestCheckForkStatus:
    """Test check_fork_status function."""

    @patch("slate.slate_fork_sync.run_gh_command")
    def test_check_fork_status_success(self, mock_gh):
        mock_gh.return_value = {
            "success": True,
            "stdout": '{"name": "test", "default_branch": "main"}'
        }
        fork = ForkInfo(name="test", upstream="o/test", fork="s/test", purpose="Testing")
        result = check_fork_status(fork)
        assert isinstance(result, dict)

    @patch("slate.slate_fork_sync.run_gh_command")
    def test_check_fork_status_failure(self, mock_gh):
        mock_gh.return_value = {"success": False, "stderr": "not found"}
        fork = ForkInfo(name="test", upstream="o/test", fork="s/test", purpose="Testing")
        result = check_fork_status(fork)
        assert isinstance(result, dict)


class TestGetAllForkStatus:
    """Test get_all_fork_status function."""

    @patch("slate.slate_fork_sync.check_fork_status")
    def test_get_all_fork_status(self, mock_check):
        mock_check.return_value = {"name": "test", "status": "ok"}
        result = get_all_fork_status()
        assert isinstance(result, dict)

    @patch("slate.slate_fork_sync.check_fork_status")
    def test_get_all_fork_status_handles_errors(self, mock_check):
        mock_check.side_effect = Exception("Network error")
        result = get_all_fork_status()
        assert isinstance(result, dict)
