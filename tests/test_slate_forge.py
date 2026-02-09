# test_slate_forge.py

import pytest
from slate.slate_forge import read_forge, append_forge, forge_status

def test_read_forge_no_args(mocker):
    """Test reading FORGE.md without arguments."""
    mock_content = "# S.L.A.T.E. FORGE\n...\n"
    mocker.patch('pathlib.Path.read_text', return_value=mock_content)
    result = read_forge()
    assert result == mock_content

def test_read_forge_section(mocker):
    """Test reading FORGE.md with section argument."""
    mock_content = "# S.L.A.T.E. FORGE\n...\n| STATUS:\n| COPILOT: Entry 1\n| PLAN:\n| COPILOT: Entry 2\n"
    mocker.patch('pathlib.Path.read_text', return_value=mock_content)
    result = read_forge('STATUS')
    assert result == "| STATUS:\n| COPILOT: Entry 1"

def test_append_forge(mocker):
    """Test appending to FORGE.md."""
    mock_entry = "### [COPILOT] 2026-02-15T14:30:00Z | Test entry"
    mocker.patch('pathlib.Path.write_text')
    append_forge(mock_entry)
    assert slate_forge.FORGE_PATH.write_text.called_once

def test_forge_status_no_file(mocker):
    """Test forge_status when FORGE.md doesn't exist."""
    mocker.patch('pathlib.Path.exists', return_value=False)
    result = forge_status()
    assert result == "⚠️ FORGE.md not found. No collaboration history."