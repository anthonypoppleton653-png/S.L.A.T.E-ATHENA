#!/usr/bin/env python3
"""
Tests for SLATE Discord Bot module.

Tests validate slash command logic, feedback storage, and status sanitization
WITHOUT requiring a live Discord connection.
"""
# Modified: 2026-02-09T18:30:00Z | Author: Claude Opus 4.6 | Change: Create Discord bot test suite

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate.slate_discord_bot import (
    get_sanitized_status,
    get_tech_tree_summary,
    store_feedback,
    _load_feedback,
    SlateBot,
    DISCORD_AVAILABLE,
)


# ── Status Sanitization ──────────────────────────────────────────────

class TestSanitizedStatus:
    """Verify that status output contains NO system internals."""

    def test_status_returns_dict(self):
        status = get_sanitized_status()
        assert isinstance(status, dict)

    def test_status_has_required_keys(self):
        status = get_sanitized_status()
        assert "dashboard" in status
        assert "ai_backend" in status
        assert "gpu_count" in status
        assert "tech_tree_completion" in status

    def test_status_no_ip_addresses(self):
        status = get_sanitized_status()
        status_str = json.dumps(status)
        assert "127.0.0.1" not in status_str
        assert "192.168" not in status_str
        assert "0.0.0.0" not in status_str

    def test_status_no_port_numbers(self):
        status = get_sanitized_status()
        status_str = json.dumps(status)
        assert ":8080" not in status_str
        assert ":11434" not in status_str

    def test_status_no_file_paths(self):
        status = get_sanitized_status()
        status_str = json.dumps(status)
        assert "E:\\" not in status_str
        assert "/home/" not in status_str


# ── Tech Tree Summary ─────────────────────────────────────────────────

class TestTechTreeSummary:
    """Test tech tree public display."""

    def test_summary_returns_dict(self):
        summary = get_tech_tree_summary()
        assert isinstance(summary, dict)

    def test_summary_has_required_keys(self):
        summary = get_tech_tree_summary()
        assert "phases" in summary
        assert "total" in summary
        assert "complete" in summary

    def test_summary_no_file_paths(self):
        summary = get_tech_tree_summary()
        summary_str = json.dumps(summary)
        assert "E:\\" not in summary_str
        assert ".py" not in summary_str  # No source file paths


# ── Feedback Storage ──────────────────────────────────────────────────

class TestFeedbackStorage:
    """Test feedback ingestion and storage."""

    def test_store_feedback_returns_id(self, tmp_path):
        """Feedback storage creates a tracking ID."""
        with patch("slate.slate_discord_bot.FEEDBACK_DIR", tmp_path):
            with patch("slate.slate_discord_bot.FEEDBACK_FILE", tmp_path / "feedback.json"):
                fid = store_feedback("user123", "#feedback", "Great feature idea!")
                assert fid.startswith("df_")

    def test_user_id_hashed_in_storage(self, tmp_path):
        """Raw Discord user IDs are NEVER stored."""
        fb_file = tmp_path / "feedback.json"
        with patch("slate.slate_discord_bot.FEEDBACK_DIR", tmp_path):
            with patch("slate.slate_discord_bot.FEEDBACK_FILE", fb_file):
                store_feedback("user123456789", "#feedback", "Test feedback content")
                data = json.loads(fb_file.read_text())
                for event in data["events"]:
                    assert event["author_hash"] != "user123456789"
                    assert len(event["author_hash"]) == 16

    def test_feedback_content_stored(self, tmp_path):
        """Feedback content is persisted."""
        fb_file = tmp_path / "feedback.json"
        with patch("slate.slate_discord_bot.FEEDBACK_DIR", tmp_path):
            with patch("slate.slate_discord_bot.FEEDBACK_FILE", fb_file):
                store_feedback("user1", "#feedback", "SLATE needs dark mode")
                data = json.loads(fb_file.read_text())
                assert data["events"][0]["content"] == "SLATE needs dark mode"

    def test_feedback_metrics_updated(self, tmp_path):
        """Metrics are incremented on each feedback."""
        fb_file = tmp_path / "feedback.json"
        with patch("slate.slate_discord_bot.FEEDBACK_DIR", tmp_path):
            with patch("slate.slate_discord_bot.FEEDBACK_FILE", fb_file):
                store_feedback("u1", "#fb", "Feedback 1")
                store_feedback("u2", "#fb", "Feedback 2")
                data = json.loads(fb_file.read_text())
                assert data["metrics"]["total_feedback"] == 2

    def test_feedback_source_is_discord(self, tmp_path):
        """Source field identifies Discord origin."""
        fb_file = tmp_path / "feedback.json"
        with patch("slate.slate_discord_bot.FEEDBACK_DIR", tmp_path):
            with patch("slate.slate_discord_bot.FEEDBACK_FILE", fb_file):
                store_feedback("u1", "#fb", "Test")
                data = json.loads(fb_file.read_text())
                assert data["events"][0]["source"] == "discord"


# ── Bot Initialization ────────────────────────────────────────────────

class TestBotInit:
    """Test bot creation and configuration."""

    def test_slate_bot_creates(self):
        bot = SlateBot()
        assert bot.security is not None

    @pytest.mark.skipif(not DISCORD_AVAILABLE, reason="discord.py not installed")
    def test_bot_intents_minimal(self):
        slate_bot = SlateBot()
        bot = slate_bot.create_bot()
        assert not bot.intents.message_content
        assert not bot.intents.presences
        assert not bot.intents.members

    @pytest.mark.skipif(not DISCORD_AVAILABLE, reason="discord.py not installed")
    def test_bot_has_slash_commands(self):
        slate_bot = SlateBot()
        bot = slate_bot.create_bot()
        command_names = [c.name for c in bot.tree.get_commands()]
        assert "slate-status" in command_names
        assert "slate-feedback" in command_names
        assert "slate-tree" in command_names
        assert "slate-about" in command_names
