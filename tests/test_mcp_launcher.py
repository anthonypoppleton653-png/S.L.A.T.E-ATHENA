# test_mcp_launcher.py
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Rewrite tests to properly mock env and subprocess

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from slate.mcp_launcher import main


def test_main_detects_workspace_root_with_env_var(monkeypatch, tmp_path):
    """When SLATE_PLUGIN_ROOT is set, main() uses it as workspace root."""
    # Create the expected mcp_server.py file so main() doesn't exit early
    slate_dir = tmp_path / "slate"
    slate_dir.mkdir()
    (slate_dir / "mcp_server.py").write_text("# stub", encoding="utf-8")

    monkeypatch.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setenv("SLATE_PYTHON", sys.executable)

    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    with patch("slate.mcp_launcher.subprocess.run", mock_run):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    # Verify workspace was passed via env
    call_kwargs = mock_run.call_args
    env_passed = call_kwargs[1].get("env") or call_kwargs.kwargs.get("env", {})
    assert env_passed["SLATE_WORKSPACE"] == str(tmp_path)


def test_main_finds_mcp_server(monkeypatch, tmp_path):
    """main() finds mcp_server.py in the slate directory."""
    slate_dir = tmp_path / "slate"
    slate_dir.mkdir()
    mcp_server = slate_dir / "mcp_server.py"
    mcp_server.write_text("# stub", encoding="utf-8")

    monkeypatch.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setenv("SLATE_PYTHON", sys.executable)

    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    with patch("slate.mcp_launcher.subprocess.run", mock_run):
        with pytest.raises(SystemExit):
            main()

    # Verify mcp_server.py was passed as the script argument
    call_args = mock_run.call_args[0][0]
    assert str(mcp_server) in call_args[1]


def test_main_runs_mcp_server(monkeypatch, tmp_path):
    """main() invokes subprocess.run with the correct arguments."""
    slate_dir = tmp_path / "slate"
    slate_dir.mkdir()
    (slate_dir / "mcp_server.py").write_text("# stub", encoding="utf-8")

    monkeypatch.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setenv("SLATE_PYTHON", sys.executable)

    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    with patch("slate.mcp_launcher.subprocess.run", mock_run):
        with pytest.raises(SystemExit):
            main()

    mock_run.assert_called_once()


def test_main_handles_python_not_found_error(monkeypatch, tmp_path, capsys):
    """main() handles FileNotFoundError when python is not found."""
    slate_dir = tmp_path / "slate"
    slate_dir.mkdir()
    (slate_dir / "mcp_server.py").write_text("# stub", encoding="utf-8")

    monkeypatch.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setenv("SLATE_PYTHON", "/nonexistent/python")

    with patch("slate.mcp_launcher.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR: Python not found" in captured.err