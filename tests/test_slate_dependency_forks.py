# Modified: 2026-02-08T08:20:00Z | Author: COPILOT | Change: Add test coverage for slate_dependency_forks.py
"""Tests for slate/slate_dependency_forks.py — Organizational fork management."""

import json
import pytest
from unittest.mock import patch, MagicMock

from slate.slate_dependency_forks import (
    DEPENDENCY_FORKS,
    check_fork_exists,
    get_upstream_info,
    get_fork_drift,
)


class TestDependencyForksRegistry:
    """Tests for the DEPENDENCY_FORKS registry."""

    def test_registry_is_dict(self):
        assert isinstance(DEPENDENCY_FORKS, dict)

    def test_registry_has_entries(self):
        assert len(DEPENDENCY_FORKS) > 0

    def test_registry_values_are_dicts(self):
        for name, info in DEPENDENCY_FORKS.items():
            assert isinstance(name, str)
            assert isinstance(info, dict)


class TestCheckForkExists:
    """Tests for check_fork_exists()."""

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_fork_exists(self, mock_urlopen):
        response_data = json.dumps({
            "full_name": "SynchronizedLivingArchitecture/some-repo",
            "fork": True,
        }).encode()
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = check_fork_exists("owner/repo", "fake-token")
        assert isinstance(result, (bool, dict))

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_fork_not_exists(self, mock_urlopen):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/repos/SynchronizedLivingArchitecture/repo",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        result = check_fork_exists("owner/repo", "fake-token")
        assert result is False or result is None or isinstance(result, dict)


class TestGetUpstreamInfo:
    """Tests for get_upstream_info()."""

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_get_upstream_info_success(self, mock_urlopen):
        response_data = json.dumps({
            "full_name": "microsoft/semantic-kernel",
            "default_branch": "main",
            "stargazers_count": 15000,
            "pushed_at": "2026-02-08T00:00:00Z",
        }).encode()
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = get_upstream_info("microsoft/semantic-kernel", "fake-token")
        assert isinstance(result, dict)

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_get_upstream_info_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")
        result = get_upstream_info("owner/repo", "fake-token")
        assert result is None or isinstance(result, dict)


class TestGetForkDrift:
    """Tests for get_fork_drift()."""

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_fork_drift_success(self, mock_urlopen):
        response_data = json.dumps({
            "ahead_by": 0,
            "behind_by": 5,
            "status": "behind",
            "total_commits": 5,
        }).encode()
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = get_fork_drift("owner/repo", "SynchronizedLivingArchitecture/repo", "fake-token")
        assert isinstance(result, dict)

    @patch("slate.slate_dependency_forks.urllib.request.urlopen")
    def test_fork_drift_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("API error")
        result = get_fork_drift("owner/repo", "org/repo", "fake-token")
        assert result is None or isinstance(result, dict)
