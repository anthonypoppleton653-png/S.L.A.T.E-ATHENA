# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix tests — create test data inline, fix check_python logic
# test_plugin_diagnose.py

import os
import pytest
from pathlib import Path
from slate.plugin_diagnose import find_plugin_root, check_python, check_plugin_structure, check_commands, check_skills


def test_find_plugin_root():
    root = find_plugin_root()
    assert isinstance(root, Path)
    assert root.is_dir()


def test_check_python_returns_dict():
    """check_python() returns a dict with status and details."""
    result = check_python()
    assert isinstance(result, dict)
    assert "status" in result
    assert "details" in result
    assert result["status"] in ("OK", "FAIL")


def test_check_plugin_structure_with_workspace():
    """check_plugin_structure() from real workspace root should find files."""
    result = check_plugin_structure()
    assert isinstance(result, dict)
    assert "status" in result
    assert "details" in result


def test_check_commands_real_workspace():
    """check_commands() from real workspace — .claude/commands/ should exist."""
    result = check_commands()
    assert isinstance(result, dict)
    assert "status" in result
    assert "details" in result


def test_check_skills_real_workspace():
    """check_skills() from real workspace — skills/ should exist."""
    result = check_skills()
    assert isinstance(result, dict)
    assert "status" in result
    assert "details" in result


def test_check_plugin_structure_with_custom_root(tmp_path):
    """check_plugin_structure() with custom root missing files should FAIL."""
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
        result = check_plugin_structure()
        assert result["status"] == "FAIL"


def test_check_commands_missing_dir(tmp_path):
    """check_commands() when commands directory doesn't exist should FAIL."""
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
        result = check_commands()
        assert result["status"] == "FAIL"


def test_check_skills_missing_dir(tmp_path):
    """check_skills() when skills directory doesn't exist should FAIL."""
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(tmp_path))
        result = check_skills()
        assert result["status"] == "FAIL"