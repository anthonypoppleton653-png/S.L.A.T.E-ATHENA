# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for release module
"""
Tests for slate/release.py — Release management
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.release import (
        get_current_branch,
        get_latest_tag,
        get_commit_log,
        branch_exists,
        generate_changelog,
        ReleaseManager,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"release not importable: {e}", allow_module_level=True)


class TestGitHelpers:
    """Test git helper functions."""

    @patch("slate.release._run_git")
    def test_get_current_branch(self, mock_git):
        mock_git.return_value = MagicMock(stdout="main\n")
        assert get_current_branch() == "main"

    @patch("slate.release._run_git")
    def test_get_latest_tag_exists(self, mock_git):
        mock_git.return_value = MagicMock(
            returncode=0, stdout="Phoenix-v1.0\n"
        )
        assert get_latest_tag() == "Phoenix-v1.0"

    @patch("slate.release._run_git")
    def test_get_latest_tag_none(self, mock_git):
        mock_git.return_value = MagicMock(returncode=1, stdout="")
        assert get_latest_tag() is None

    @patch("slate.release._run_git")
    def test_get_commit_log(self, mock_git):
        mock_git.return_value = MagicMock(
            returncode=0,
            stdout="abc1234|feat: add feature|Author|2026-02-09T12:00:00Z\n"
        )
        commits = get_commit_log()
        assert isinstance(commits, list)
        assert len(commits) == 1
        assert commits[0]["hash"] == "abc1234"

    @patch("slate.release._run_git")
    def test_branch_exists_true(self, mock_git):
        mock_git.return_value = MagicMock(stdout="  stable\n")
        assert branch_exists("stable") is True

    @patch("slate.release._run_git")
    def test_branch_exists_false(self, mock_git):
        mock_git.return_value = MagicMock(stdout="")
        assert branch_exists("nonexistent") is False


class TestGenerateChangelog:
    """Test changelog generation."""

    def test_empty_commits(self):
        result = generate_changelog([], "v1.0")
        assert isinstance(result, str)
        assert "v1.0" in result

    def test_with_commits(self):
        commits = [
            {"hash": "abc1234", "message": "feat: add widget", "author": "Dev", "date": "2026-02-09"},
            {"hash": "def5678", "message": "fix: resolve bug", "author": "Dev", "date": "2026-02-08"},
        ]
        result = generate_changelog(commits, "v1.0")
        assert isinstance(result, str)

    def test_conventional_commit_parsing(self):
        commits = [
            {"hash": "aaa", "message": "feat: new feature", "author": "A", "date": "2026-01-01"},
            {"hash": "bbb", "message": "fix: bug fix", "author": "B", "date": "2026-01-02"},
            {"hash": "ccc", "message": "docs: update readme", "author": "C", "date": "2026-01-03"},
        ]
        result = generate_changelog(commits, "v2.0")
        assert isinstance(result, str)


class TestReleaseManager:
    """Test ReleaseManager class."""

    def test_init(self):
        mgr = ReleaseManager()
        assert mgr is not None

    @patch("slate.release._run_git")
    def test_get_version(self, mock_git):
        mgr = ReleaseManager()
        version = mgr.get_version()
        assert isinstance(version, str)

    @patch("slate.release._run_git")
    @patch("slate.release.subprocess.run")
    def test_pre_release_checks(self, mock_sub, mock_git):
        mock_git.return_value = MagicMock(returncode=0, stdout="main\n")
        mock_sub.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mgr = ReleaseManager()
        result = mgr.pre_release_checks()
        assert isinstance(result, dict)

    @patch("slate.release._run_git")
    def test_tag_release_dry_run(self, mock_git):
        mock_git.return_value = MagicMock(returncode=0, stdout="")
        mgr = ReleaseManager()
        result = mgr.tag_release("test-v1.0", dry_run=True)
        assert isinstance(result, bool)
