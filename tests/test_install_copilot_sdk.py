# Modified: 2026-02-08T22:10:00Z | Author: COPILOT | Change: Add test coverage for slate/install_copilot_sdk.py
"""
Tests for slate/install_copilot_sdk.py — SLATE Copilot SDK installer.
Tests focus on check_dependency, check_install_status, and path validation
without running actual pip installs.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestInstallCopilotSdkImport:
    """Test module imports correctly."""

    def test_import_module(self):
        import slate.install_copilot_sdk
        assert hasattr(slate.install_copilot_sdk, 'check_dependency')
        assert hasattr(slate.install_copilot_sdk, 'check_install_status')
        assert hasattr(slate.install_copilot_sdk, 'install_dependency')
        assert hasattr(slate.install_copilot_sdk, 'main')

    def test_workspace_root_defined(self):
        from slate.install_copilot_sdk import WORKSPACE_ROOT
        assert isinstance(WORKSPACE_ROOT, Path)
        assert WORKSPACE_ROOT.exists()

    def test_python_path_defined(self):
        from slate.install_copilot_sdk import PYTHON
        assert isinstance(PYTHON, Path)


class TestCheckDependency:
    """Test check_dependency function."""

    def test_check_existing_package(self):
        from slate.install_copilot_sdk import check_dependency
        # json is always available
        assert check_dependency("json") is True

    def test_check_nonexistent_package(self):
        from slate.install_copilot_sdk import check_dependency
        assert check_dependency("nonexistent_package_xyz_12345") is False

    def test_check_with_import_name(self):
        from slate.install_copilot_sdk import check_dependency
        # os module is always available
        assert check_dependency("os-module", import_name="os") is True

    def test_check_bad_import_name(self):
        from slate.install_copilot_sdk import check_dependency
        assert check_dependency("some-package", import_name="zzzz_not_real") is False


class TestInstallDependency:
    """Test install_dependency function (mocked)."""

    @patch("subprocess.run")
    def test_install_success(self, mock_run):
        from slate.install_copilot_sdk import install_dependency
        mock_run.return_value = MagicMock(returncode=0)
        result = install_dependency("some-package")
        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_failure(self, mock_run):
        from slate.install_copilot_sdk import install_dependency
        mock_run.return_value = MagicMock(returncode=1)
        result = install_dependency("bad-package")
        assert result is False

    @patch("subprocess.run", side_effect=Exception("timeout"))
    def test_install_exception(self, mock_run):
        from slate.install_copilot_sdk import install_dependency
        result = install_dependency("crash-package")
        assert result is False


class TestCheckInstallStatus:
    """Test check_install_status returns expected structure."""

    def test_status_structure(self):
        from slate.install_copilot_sdk import check_install_status
        status = check_install_status()
        assert isinstance(status, dict)
        assert "python" in status
        assert "python_exists" in status
        assert "dependencies" in status
        assert "files" in status
        assert "integrations" in status

    def test_status_dependencies_checked(self):
        from slate.install_copilot_sdk import check_install_status
        status = check_install_status()
        deps = status["dependencies"]
        assert isinstance(deps, dict)
        # These dependency names should be checked
        assert "pydantic" in deps

    def test_status_files_checked(self):
        from slate.install_copilot_sdk import check_install_status
        status = check_install_status()
        files = status["files"]
        assert isinstance(files, dict)
        assert "slate_copilot_sdk" in files
        assert "mcp_server" in files

    def test_status_integrations_checked(self):
        from slate.install_copilot_sdk import check_install_status
        status = check_install_status()
        integrations = status["integrations"]
        assert isinstance(integrations, dict)
        assert "vscode_extension" in integrations

    def test_status_python_exists(self):
        from slate.install_copilot_sdk import check_install_status
        status = check_install_status()
        assert isinstance(status["python_exists"], bool)


class TestPrintCheckStatus:
    """Test print_check_status output."""

    def test_print_runs_without_error(self, capsys):
        from slate.install_copilot_sdk import print_check_status
        print_check_status()
        captured = capsys.readouterr()
        assert "SLATE Copilot SDK" in captured.out


class TestMain:
    """Test main() CLI."""

    def test_main_check_flag(self):
        from slate.install_copilot_sdk import main
        with patch("sys.argv", ["install_copilot_sdk.py", "--check"]):
            # Should not raise
            main()
