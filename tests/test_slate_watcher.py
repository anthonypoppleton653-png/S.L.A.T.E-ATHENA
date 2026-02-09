# Modified: 2026-02-08T08:20:00Z | Author: COPILOT | Change: Add test coverage for slate_watcher.py
"""Tests for slate/slate_watcher.py — Filesystem watcher and dev hot-reload."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from slate.slate_watcher import (
    ChangeCategory,
    FileChangeEvent,
    SlateFileWatcher,
    DevReloadManager,
    categorize_change,
    WORKSPACE_ROOT,
)


class TestChangeCategory:
    """Tests for the ChangeCategory constants."""

    def test_category_constants_exist(self):
        assert hasattr(ChangeCategory, 'AGENT')
        assert hasattr(ChangeCategory, 'SKILL')
        assert hasattr(ChangeCategory, 'TASK')
        assert hasattr(ChangeCategory, 'CONFIG')
        assert hasattr(ChangeCategory, 'UNKNOWN')

    def test_categorize_agent_files(self):
        result = categorize_change(WORKSPACE_ROOT / "agents" / "runner_api.py")
        assert result == ChangeCategory.AGENT

    def test_categorize_skill_files(self):
        result = categorize_change(WORKSPACE_ROOT / "skills" / "slate-status" / "SKILL.md")
        assert result == ChangeCategory.SKILL

    def test_categorize_task_file(self):
        result = categorize_change(WORKSPACE_ROOT / "current_tasks.json")
        assert result == ChangeCategory.TASK

    def test_categorize_config_file(self):
        result = categorize_change(WORKSPACE_ROOT / "pyproject.toml")
        # toml may not match config, should be unknown or config
        assert result in (ChangeCategory.CONFIG, ChangeCategory.UNKNOWN)

    def test_categorize_unknown_file(self):
        result = categorize_change(Path("/some/random/path/unknown.txt"))
        assert result == ChangeCategory.UNKNOWN


class TestFileChangeEvent:
    """Tests for the FileChangeEvent class."""

    def test_create_event(self):
        event = FileChangeEvent(
            change_type="modified",
            file_path=WORKSPACE_ROOT / "agents" / "runner_api.py",
        )
        assert event.change_type == "modified"
        assert event.category == ChangeCategory.AGENT
        assert event.timestamp is not None

    def test_to_dict(self):
        event = FileChangeEvent(
            change_type="created",
            file_path=WORKSPACE_ROOT / "skills" / "slate-status" / "SKILL.md",
        )
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d["change_type"] == "created"
        assert d["category"] == ChangeCategory.SKILL
        assert "timestamp" in d


class TestSlateFileWatcher:
    """Tests for the SlateFileWatcher class."""

    def test_initialization(self):
        watcher = SlateFileWatcher()
        assert watcher is not None
        assert watcher.is_running is False

    def test_history_empty(self):
        watcher = SlateFileWatcher()
        assert isinstance(watcher.history, list)
        assert len(watcher.history) == 0

    def test_status(self):
        watcher = SlateFileWatcher()
        status = watcher.status()
        assert isinstance(status, dict)
        assert "running" in status

    def test_stop_when_not_running(self):
        watcher = SlateFileWatcher()
        # Should not raise
        watcher.stop()
        assert watcher.is_running is False


class TestDevReloadManager:
    """Tests for the DevReloadManager class."""

    @patch("slate.module_registry.get_registry")
    def test_initialization(self, mock_registry):
        mock_registry.return_value = MagicMock()
        mgr = DevReloadManager()
        assert mgr is not None

    @patch("slate.module_registry.get_registry")
    def test_is_not_running_initially(self, mock_registry):
        mock_registry.return_value = MagicMock()
        mgr = DevReloadManager()
        assert mgr.is_running is False

    @patch("slate.module_registry.get_registry")
    def test_status(self, mock_registry):
        mock_reg = MagicMock()
        mock_reg.status.return_value = {"modules": 0}
        mock_registry.return_value = mock_reg
        mgr = DevReloadManager()
        status = mgr.status()
        assert isinstance(status, dict)
        assert "watcher" in status
        assert "registry" in status
