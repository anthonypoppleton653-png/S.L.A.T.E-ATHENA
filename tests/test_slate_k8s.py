# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Rewrite test_slate_k8s.py — fix Linux-only paths, missing imports, wrong assertions
# test_slate_k8s.py

import subprocess
import pytest
from unittest.mock import patch, MagicMock
from slate.slate_k8s import run, detect_provider, NAMESPACE


def test_namespace_is_slate():
    """NAMESPACE constant should be 'slate'."""
    assert NAMESPACE == "slate"


def test_run_command_success():
    """run() with a simple echo should succeed."""
    result = run(["echo", "Hello"], capture=True, check=False)
    assert result.returncode == 0
    assert "Hello" in result.stdout.strip()


def test_run_command_not_found():
    """run() with a nonexistent command should return returncode=1."""
    result = run(["__nonexistent_command_12345__"], check=False, capture=True)
    assert result.returncode == 1


def test_detect_provider_kubectl_available():
    """detect_provider() should return kubectl version when available."""
    mock_kubectl_version = subprocess.CompletedProcess(
        ["kubectl", "version"], returncode=0,
        stdout='{"clientVersion": {"gitVersion": "v1.23.6"}}', stderr=""
    )
    mock_cluster_info = subprocess.CompletedProcess(
        ["kubectl", "cluster-info"], returncode=0, stdout="running", stderr=""
    )
    mock_context = subprocess.CompletedProcess(
        ["kubectl", "config", "current-context"], returncode=0,
        stdout="docker-desktop", stderr=""
    )
    mock_helm = subprocess.CompletedProcess(
        ["helm", "version"], returncode=0, stdout="v3.12.0", stderr=""
    )
    # Modified: 2026-02-10T14:00:00Z | Author: COPILOT | Change: Add docker/nvidia mock values for detect_provider
    mock_docker = subprocess.CompletedProcess(
        ["docker", "version"], returncode=0, stdout="24.0.7", stderr=""
    )
    mock_nvidia = subprocess.CompletedProcess(
        ["nvidia-smi"], returncode=0, stdout="NVIDIA GeForce RTX 5070 Ti", stderr=""
    )

    with patch("slate.slate_k8s.run") as mock_run:
        mock_run.side_effect = [mock_kubectl_version, mock_cluster_info, mock_context, mock_helm, mock_docker, mock_nvidia]
        providers = detect_provider()

    assert providers["kubectl"] == "v1.23.6"
    assert providers["cluster_connected"] is True


def test_detect_provider_cluster_not_connected():
    """detect_provider() should report cluster not connected when cluster-info fails."""
    mock_kubectl_version = subprocess.CompletedProcess(
        ["kubectl", "version"], returncode=0,
        stdout='{"clientVersion": {"gitVersion": "v1.23.6"}}', stderr=""
    )
    mock_cluster_info = subprocess.CompletedProcess(
        ["kubectl", "cluster-info"], returncode=1, stdout="", stderr="error"
    )
    mock_helm = subprocess.CompletedProcess(
        ["helm", "version"], returncode=1, stdout="", stderr="not found"
    )
    # Modified: 2026-02-10T14:00:00Z | Author: COPILOT | Change: Add docker/nvidia mock values for detect_provider (cluster disconnected)
    mock_docker = subprocess.CompletedProcess(
        ["docker", "version"], returncode=0, stdout="24.0.7", stderr=""
    )
    mock_nvidia = subprocess.CompletedProcess(
        ["nvidia-smi"], returncode=1, stdout="", stderr="not found"
    )

    with patch("slate.slate_k8s.run") as mock_run:
        mock_run.side_effect = [mock_kubectl_version, mock_cluster_info, mock_helm, mock_docker, mock_nvidia]
        providers = detect_provider()

    assert providers["cluster_connected"] is False
    assert providers["provider"] == "None (cluster not running)"