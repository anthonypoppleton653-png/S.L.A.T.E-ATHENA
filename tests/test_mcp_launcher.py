# test_mcp_launcher.py

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from slate.mcp_launcher import main

@pytest.fixture
def mock_env(monkeypatch):
    def getenv(key, default=None):
        return {
            'SLATE_PLUGIN_ROOT': '/path/to/slate',
            'SLATE_PYTHON': '/usr/bin/python3',
        }.get(key, default)

    monkeypatch.setattr(os, 'environ', {**os.environ, **{'get': getenv}})

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_main_detects_workspace_root_with_env_var(mock_env):
    main()
    assert os.environ['SLATE_WORKSPACE'] == '/path/to/slate/../'

def test_main_finds_mcp_server(mock_env):
    main()
    assert os.path.exists(os.environ['PYTHONPATH'])

def test_main_runs_mcp_server(mock_env, mock_subprocess):
    main()
    mock_subprocess.assert_called_once()

def test_main_handles_python_not_found_error(mock_env, capsys):
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError
        main()
        captured = capsys.readouterr()
        assert "ERROR: Python not found" in captured.out