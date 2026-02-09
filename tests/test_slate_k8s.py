# test_slate_k8s.py

import pytest
from slate.slate_k8s import run, detect_provider, NAMESPACE

def test_run_command_success():
    # Arrange
    cmd = ["echo", "Hello, World!"]
    expected_output = "Hello, World!\n"

    # Act
    result = run(cmd, capture=True)

    # Assert
    assert result.returncode == 0
    assert result.stdout.strip() == expected_output

def test_run_command_failure():
    # Arrange
    cmd = ["false"]

    # Act
    result = run(cmd)

    # Assert
    assert result.returncode != 0
    assert "Command failed" in result.stderr

def test_detect_provider_kubectl_available():
    # Arrange
    kubectl_version_output = '{"clientVersion": {"gitVersion": "v1.23.6"}}'
    with open("/usr/local/bin/kubectl", "w") as f:
        f.write("kubectl\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = kubectl_version_output
        mock_run.return_value.returncode = 0

        # Act
        providers = detect_provider()

    # Assert
    assert "kubectl" in providers
    assert providers["kubectl"] == "v1.23.6"

def test_detect_provider_cluster_not_connected():
    # Arrange
    kubectl_version_output = '{"clientVersion": {"gitVersion": "v1.23.6"}}'
    with open("/usr/local/bin/kubectl", "w") as f:
        f.write("kubectl\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = kubectl_version_output
        mock_run.return_value.returncode = 0
        mock_run.side_effect = [
            subprocess.CompletedProcess(["kubectl", "version"], returncode=0, stdout=kubectl_version_output),
            subprocess.CompletedProcess(["kubectl", "cluster-info"], returncode=1, stderr="error"),
        ]

        # Act
        providers = detect_provider()

    # Assert
    assert not providers["cluster_connected"]
    assert providers["provider"] == "None (cluster not running)"