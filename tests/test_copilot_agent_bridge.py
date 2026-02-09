# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for copilot_agent_bridge module
"""
Tests for slate/copilot_agent_bridge.py — Autonomous ↔ chat bridge task queue
"""

import pytest
import json
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.copilot_agent_bridge import CopilotAgentBridge
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"copilot_agent_bridge not importable: {e}", allow_module_level=True)


class TestCopilotAgentBridge:
    """Test CopilotAgentBridge class."""

    @patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE")
    @patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE")
    def test_init_creates_files(self, mock_results, mock_queue, tmp_path):
        mock_queue.__class__ = Path
        mock_results.__class__ = Path
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            assert queue_file.exists()
            assert results_file.exists()

    def test_enqueue_task(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            task = bridge.enqueue_task("Test Task", "Test Description")
            assert task["title"] == "Test Task"
            assert task["status"] == "pending"
            assert task["agent"] == "COPILOT_CHAT"
            assert "id" in task

    def test_get_pending_tasks(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            bridge.enqueue_task("Task 1")
            bridge.enqueue_task("Task 2")
            pending = bridge.get_pending_tasks()
            assert len(pending) == 2

    def test_mark_task_processing(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            task = bridge.enqueue_task("Task 1")
            result = bridge.mark_task_processing(task["id"])
            assert result is True

    def test_complete_task(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            task = bridge.enqueue_task("Task 1")
            bridge.complete_task(task["id"], True, "Done")

    def test_get_status(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            status = bridge.get_status()
            assert "pending" in status
            assert "total_results" in status

    def test_cleanup_stale(self, tmp_path):
        queue_file = tmp_path / "queue.json"
        results_file = tmp_path / "results.json"
        with patch("slate.copilot_agent_bridge.BRIDGE_QUEUE_FILE", queue_file), \
             patch("slate.copilot_agent_bridge.BRIDGE_RESULTS_FILE", results_file):
            bridge = CopilotAgentBridge()
            cleaned = bridge.cleanup_stale()
            assert isinstance(cleaned, int)
