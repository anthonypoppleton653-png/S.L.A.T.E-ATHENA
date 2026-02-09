# Modified: 2026-02-08T08:20:00Z | Author: COPILOT | Change: Add test coverage for slate_fork_intelligence.py
"""Tests for slate/slate_fork_intelligence.py — AI-powered fork monitoring."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from slate.slate_fork_intelligence import (
    ForkChange,
    ForkIntelligenceState,
    LocalAIAnalyzer,
    ForkIntelligence,
)


class TestForkChange:
    """Tests for the ForkChange dataclass."""

    def test_create_fork_change(self):
        fc = ForkChange(
            repo="owner/repo",
            direction="upstream",
            commit_count=3,
            files_changed=["file1.py", "file2.py"],
            summary="Added new feature",
        )
        assert fc.repo == "owner/repo"
        assert fc.direction == "upstream"
        assert fc.commit_count == 3

    def test_fork_change_defaults(self):
        fc = ForkChange(
            repo="owner/repo",
            direction="downstream",
            commit_count=1,
            files_changed=[],
            summary="Minor fix",
        )
        assert fc.breaking is False
        assert fc.recommendation == ""
        assert fc.ai_analysis == ""

    def test_fork_change_to_dict(self):
        fc = ForkChange(
            repo="owner/repo",
            direction="upstream",
            commit_count=5,
            files_changed=["README.md"],
            summary="Doc update",
            breaking=True,
            recommendation="review",
        )
        d = asdict(fc)
        assert d["repo"] == "owner/repo"
        assert d["breaking"] is True
        assert d["recommendation"] == "review"


class TestForkIntelligenceState:
    """Tests for the ForkIntelligenceState dataclass."""

    def test_default_state(self):
        state = ForkIntelligenceState()
        assert state.last_run == ""
        assert state.upstream_commits == {}
        assert state.downstream_forks == []
        assert state.pending_actions == []


class TestLocalAIAnalyzer:
    """Tests for the LocalAIAnalyzer Ollama client."""

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_analyze_success(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="NAME\nslate-fast"),
            MagicMock(returncode=0, stdout="Summary: No breaking changes.\nRisk: LOW\nAction: SYNC"),
        ]
        analyzer = LocalAIAnalyzer()
        result = analyzer.analyze("Check for breaking changes", "diff content")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_analyze_ollama_unavailable(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ollama not found")
        analyzer = LocalAIAnalyzer()
        assert analyzer.available is False
        result = analyzer.analyze("test", "test")
        assert "unavailable" in result.lower() or "AI" in result


class TestForkIntelligence:
    """Tests for the ForkIntelligence main class."""

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_initialization(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        fi = ForkIntelligence()
        assert fi.state is not None
        assert isinstance(fi.state, ForkIntelligenceState)

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_get_upstream_forks(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="origin\thttps://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git (fetch)\n",
        )
        fi = ForkIntelligence()
        upstreams = fi.get_upstream_forks()
        assert isinstance(upstreams, list)

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_get_downstream_forks(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        fi = ForkIntelligence()
        result = fi.get_downstream_forks()
        assert isinstance(result, list)

    @patch("slate.slate_fork_intelligence.subprocess.run")
    def test_generate_report(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        fi = ForkIntelligence()
        report = fi.generate_report()
        assert isinstance(report, str)
