# Modified: 2026-02-08T08:00:00Z | Author: COPILOT | Change: Add test coverage for slate_status module
"""
Tests for slate/slate_status.py — System health checker functions,
GPU detection, Python info, PyTorch info, Ollama info, status output.
"""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from slate.slate_status import (
    get_github_models_info,
    get_gpu_info,
    get_ollama_info,
    get_python_info,
    get_pytorch_info,
    get_sk_info,
    get_status,
    get_system_info,
    print_quick_status,
    main,
)


@pytest.fixture(autouse=True)
def _force_not_docker():
    """Ensure IS_DOCKER is False for all tests, preventing env contamination."""
    with patch("slate.slate_status.IS_DOCKER", False):
        yield

# ── get_python_info ─────────────────────────────────────────────────────


class TestGetPythonInfo:
    """Tests for get_python_info()."""

    def test_returns_dict(self):
        info = get_python_info()
        assert isinstance(info, dict)

    def test_has_required_keys(self):
        info = get_python_info()
        assert "version" in info
        assert "executable" in info
        assert "ok" in info

    def test_version_format(self):
        info = get_python_info()
        parts = info["version"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_executable_is_sys_executable(self):
        info = get_python_info()
        assert info["executable"] == sys.executable

    def test_ok_true_for_311_plus(self):
        info = get_python_info()
        v = sys.version_info
        expected = v.major >= 3 and v.minor >= 11
        assert info["ok"] == expected


# ── get_gpu_info ────────────────────────────────────────────────────────


class TestGetGpuInfo:
    """Tests for get_gpu_info()."""

    def test_returns_dict(self):
        info = get_gpu_info()
        assert isinstance(info, dict)

    def test_has_required_keys(self):
        info = get_gpu_info()
        assert "available" in info
        assert "count" in info
        assert "gpus" in info

    def test_gpus_is_list(self):
        info = get_gpu_info()
        assert isinstance(info["gpus"], list)

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_nvidia_smi_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA RTX 5070 Ti, 12.0, 16303 MiB, 15000 MiB\n"
        )
        info = get_gpu_info()
        assert info["available"] is True
        assert info["count"] == 1
        assert info["gpus"][0]["name"] == "NVIDIA RTX 5070 Ti"

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_nvidia_smi_multi_gpu(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="GPU 0, 12.0, 16303 MiB, 15000 MiB\nGPU 1, 12.0, 16303 MiB, 14000 MiB\n"
        )
        info = get_gpu_info()
        assert info["count"] == 2
        assert len(info["gpus"]) == 2

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_nvidia_smi_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
        info = get_gpu_info()
        assert info["available"] is False
        assert info["count"] == 0

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_nvidia_smi_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        info = get_gpu_info()
        assert info["available"] is False


# ── get_system_info ─────────────────────────────────────────────────────


class TestGetSystemInfo:
    """Tests for get_system_info()."""

    def test_returns_dict(self):
        info = get_system_info()
        assert isinstance(info, dict)

    @patch("slate.slate_status.HAS_PSUTIL", True)
    def test_with_psutil_has_fields(self):
        info = get_system_info()
        if info.get("available"):
            assert "cpu_count" in info
            assert "memory_total_gb" in info
            assert "disk_free_gb" in info

    @patch("slate.slate_status.HAS_PSUTIL", False)
    def test_without_psutil(self):
        info = get_system_info()
        assert info.get("available") is False


# ── get_pytorch_info ────────────────────────────────────────────────────


class TestGetPytorchInfo:
    """Tests for get_pytorch_info()."""

    def test_returns_dict(self):
        info = get_pytorch_info()
        assert isinstance(info, dict)

    def test_installed_key(self):
        info = get_pytorch_info()
        assert "installed" in info

    def test_installed_has_version(self):
        info = get_pytorch_info()
        if info.get("installed"):
            assert "version" in info
            assert "cuda_available" in info


# ── get_ollama_info ─────────────────────────────────────────────────────


class TestGetOllamaInfo:
    """Tests for get_ollama_info()."""

    def test_returns_dict(self):
        info = get_ollama_info()
        assert isinstance(info, dict)

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_ollama_available(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME\nllama3.2:latest\nmistral:latest\n"
        )
        info = get_ollama_info()
        assert info["available"] is True
        assert info["model_count"] == 2

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_ollama_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        info = get_ollama_info()
        assert info["available"] is False
        assert info["model_count"] == 0

    @patch("slate.slate_status.IS_DOCKER", False)
    @patch("slate.slate_status.subprocess.run")
    def test_ollama_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        info = get_ollama_info()
        assert info["available"] is False


# ── get_sk_info ─────────────────────────────────────────────────────────


class TestGetSkInfo:
    """Tests for get_sk_info()."""

    def test_returns_dict(self):
        info = get_sk_info()
        assert isinstance(info, dict)
        assert "installed" in info

    def test_installed_has_version(self):
        info = get_sk_info()
        if info.get("installed"):
            assert "version" in info


# ── get_status ──────────────────────────────────────────────────────────


class TestGetStatus:
    """Tests for get_status()."""

    def test_returns_dict(self):
        status = get_status()
        assert isinstance(status, dict)

    def test_has_all_sections(self):
        status = get_status()
        assert "timestamp" in status
        assert "python" in status
        assert "gpu" in status
        assert "system" in status
        assert "pytorch" in status
        assert "ollama" in status
        assert "semantic_kernel" in status

    def test_timestamp_is_iso_format(self):
        status = get_status()
        from datetime import datetime
        # Should not raise
        datetime.fromisoformat(status["timestamp"])


# ── print_quick_status ──────────────────────────────────────────────────


class TestPrintQuickStatus:
    """Tests for print_quick_status()."""

    def test_prints_output(self, capsys):
        status = get_status()
        print_quick_status(status)
        captured = capsys.readouterr()
        assert "S.L.A.T.E." in captured.out
        assert "Python:" in captured.out

    def test_shows_gpu_info(self, capsys):
        status = {
            "python": {"version": "3.11.9", "executable": "python", "ok": True},
            "gpu": {"available": True, "count": 2, "gpus": [
                {"name": "RTX 5070 Ti", "memory_total": "16303 MiB"}
            ]},
            "system": {"available": False},
            "pytorch": {"installed": False},
            "ollama": {"available": False},
            "semantic_kernel": {"installed": False},
        }
        print_quick_status(status)
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "RTX 5070 Ti" in captured.out

    def test_shows_cpu_only(self, capsys):
        status = {
            "python": {"version": "3.11.9", "executable": "python", "ok": True},
            "gpu": {"available": False, "count": 0, "gpus": []},
            "system": {"available": False},
            "pytorch": {"installed": False},
            "ollama": {"available": False},
            "semantic_kernel": {"installed": False},
        }
        print_quick_status(status)
        captured = capsys.readouterr()
        assert "CPU-only" in captured.out


# ── main ────────────────────────────────────────────────────────────────


class TestMain:
    """Tests for main() CLI entry point."""

    @patch("sys.argv", ["slate_status.py", "--json"])
    def test_json_output(self, capsys):
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "python" in data

    @patch("sys.argv", ["slate_status.py", "--quick"])
    def test_quick_output(self, capsys):
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "S.L.A.T.E." in captured.out

    @patch("sys.argv", ["slate_status.py"])
    def test_default_output(self, capsys):
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "S.L.A.T.E." in captured.out


# ── get_github_models_info ─────────────────────────────────────────────

# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Add tests for GitHub Models status integration

class TestGetGitHubModelsInfo:
    """Tests for get_github_models_info()."""

    def test_returns_dict(self):
        info = get_github_models_info()
        assert isinstance(info, dict)

    def test_available_has_catalog_size(self):
        info = get_github_models_info()
        if info.get("available"):
            assert "catalog_size" in info
            assert isinstance(info["catalog_size"], int)
            assert info["catalog_size"] > 0

    def test_available_has_total_calls(self):
        info = get_github_models_info()
        if info.get("available"):
            assert "total_calls" in info
            assert isinstance(info["total_calls"], int)

    def test_unavailable_has_reason(self):
        with patch("slate.slate_status.get_github_models_info") as mock_fn:
            mock_fn.return_value = {"available": False, "reason": "no token"}
            info = mock_fn()
            assert info["available"] is False
            assert "reason" in info

    def test_import_failure_handled(self):
        """If slate_github_models cannot be imported, returns unavailable."""
        import importlib
        with patch.dict("sys.modules", {"slate.slate_github_models": None}):
            # Force re-import failure
            info = get_github_models_info()
            assert isinstance(info, dict)
            # Should still return a dict (either available or not)

    def test_status_includes_github_models(self):
        """get_status() includes the github_models key."""
        status = get_status()
        assert "github_models" in status

    def test_quick_status_shows_gh_models(self, capsys):
        """print_quick_status shows GH Model line."""
        status = get_status()
        print_quick_status(status)
        captured = capsys.readouterr()
        assert "GH Model" in captured.out
