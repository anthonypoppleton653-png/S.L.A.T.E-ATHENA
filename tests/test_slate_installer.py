# test_slate_installer.py
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix imports to match actual slate_installer exports

import pytest
import os

try:
    from slate.slate_installer import (
        detect_python, detect_git, detect_ollama, detect_docker,
        detect_vscode, detect_pytorch, detect_nvidia_gpu, detect_all,
        SlateInstaller
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False


@pytest.mark.skipif(not MODULE_AVAILABLE, reason="slate_installer not importable")
class TestSlateInstaller:

    def test_detect_python(self):
        python_info = detect_python()
        assert "installed" in python_info
        assert "version" in python_info

    def test_detect_git(self):
        git_info = detect_git()
        assert "installed" in git_info
        assert "version" in git_info

    def test_detect_ollama(self):
        ollama_info = detect_ollama()
        assert "installed" in ollama_info

    def test_detect_docker(self):
        docker_info = detect_docker()
        assert "installed" in docker_info

    def test_detect_vscode(self):
        vscode_info = detect_vscode()
        assert "installed" in vscode_info

    def test_detect_pytorch(self):
        pytorch_info = detect_pytorch()
        assert "installed" in pytorch_info

    def test_detect_nvidia_gpu(self):
        gpu_info = detect_nvidia_gpu()
        assert "installed" in gpu_info

    def test_detect_all(self):
        results = detect_all()
        assert isinstance(results, dict)
        # Should have entries for each detector
        assert len(results) >= 3

    def test_slate_installer_class(self):
        installer = SlateInstaller()
        assert hasattr(installer, 'run_check')
        assert hasattr(installer, 'run_install')
        assert hasattr(installer, 'run_update')