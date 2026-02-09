# test_slate_forge.py

import pytest
from unittest.mock import patch
from slate.slate_forge import read_forge, append_forge, forge_status

def test_read_forge_no_args():
    """Test reading FORGE.md without arguments."""
    mock_content = "# S.L.A.T.E. FORGE\n...\n"
    with patch('pathlib.Path.read_text', return_value=mock_content), \
         patch('pathlib.Path.exists', return_value=True):
        result = read_forge()
        assert result == mock_content

def test_read_forge_section():
    """Test reading FORGE.md with section argument."""
    mock_content = "# S.L.A.T.E. FORGE\n...\n| STATUS:\n| COPILOT: Entry 1\n| PLAN:\n| COPILOT: Entry 2\n"
    with patch('pathlib.Path.read_text', return_value=mock_content), \
         patch('pathlib.Path.exists', return_value=True):
        result = read_forge('STATUS')
        assert '| STATUS:' in result

def test_append_forge():
    """Test appending to FORGE.md."""
    mock_entry = "### [COPILOT] 2026-02-15T14:30:00Z | Test entry"
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value="# FORGE\n"), \
         patch('builtins.open', create=True):
        result = append_forge(mock_entry)
        assert isinstance(result, str)

def test_forge_status_no_file():
    """Test forge_status when FORGE.md doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = forge_status()
        assert "not found" in result.lower() or "FORGE" in result