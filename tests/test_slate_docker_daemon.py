# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for slate_docker_daemon module
"""
Tests for slate/slate_docker_daemon.py — Docker daemon management
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.slate_docker_daemon import (
        SlateDockerDaemon,
        COMPOSE_FILES,
        EXPECTED_CONTAINERS,
        HEALTH_ENDPOINTS,
        TRUSTED_REGISTRIES,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"slate_docker_daemon not importable: {e}", allow_module_level=True)


class TestConstants:
    """Test module constants."""

    def test_compose_files_defined(self):
        assert isinstance(COMPOSE_FILES, dict)
        assert "default" in COMPOSE_FILES
        assert "dev" in COMPOSE_FILES
        assert "prod" in COMPOSE_FILES

    def test_expected_containers_defined(self):
        assert isinstance(EXPECTED_CONTAINERS, dict)
        assert "default" in EXPECTED_CONTAINERS

    def test_health_endpoints_defined(self):
        assert isinstance(HEALTH_ENDPOINTS, dict)
        # All endpoints should be tuples of (host, port, path)
        for name, endpoint in HEALTH_ENDPOINTS.items():
            assert len(endpoint) == 3
            assert endpoint[0] == "127.0.0.1"  # SLATE security: local only

    def test_trusted_registries_defined(self):
        assert isinstance(TRUSTED_REGISTRIES, list)
        assert len(TRUSTED_REGISTRIES) > 0


class TestSlateDockerDaemon:
    """Test SlateDockerDaemon class."""

    @patch("slate.slate_docker_daemon.subprocess.run")
    def test_init(self, mock_run):
        daemon = SlateDockerDaemon()
        assert daemon is not None

    @patch("slate.slate_docker_daemon.subprocess.run")
    def test_detect_no_docker(self, mock_run):
        mock_run.side_effect = FileNotFoundError("docker not found")
        daemon = SlateDockerDaemon()
        result = daemon.detect()
        assert isinstance(result, dict)

    @patch("slate.slate_docker_daemon.subprocess.run")
    def test_list_containers_no_docker(self, mock_run):
        mock_run.side_effect = FileNotFoundError("docker not found")
        daemon = SlateDockerDaemon()
        daemon._docker_path = None
        result = daemon.list_containers()
        assert isinstance(result, list)

    @patch("slate.slate_docker_daemon.subprocess.run")
    def test_gpu_check(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="no GPU"
        )
        daemon = SlateDockerDaemon()
        result = daemon.gpu_check()
        assert isinstance(result, dict)

    @patch("slate.slate_docker_daemon.subprocess.run")
    def test_health_check(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"Names":"slate","State":"running"}]',
            stderr=""
        )
        daemon = SlateDockerDaemon()
        result = daemon.health_check()
        assert isinstance(result, dict)
