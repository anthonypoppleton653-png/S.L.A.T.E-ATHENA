# test_plugin_diagnose.py

import pytest
from pathlib import Path
from slate.plugin_diagnose import find_plugin_root, check_python, check_plugin_structure, check_commands, check_skills

def test_find_plugin_root():
    root = find_plugin_root()
    assert isinstance(root, Path)
    assert root.is_dir()

@pytest.mark.parametrize("env_var, expected_status", [
    ("SLATE_PLUGIN_ROOT", "OK"),
    (None, "FAIL")
])
def test_check_python(env_var, expected_status):
    with pytest.MonkeyPatch.context() as m:
        if env_var is not None:
            m.setenv("SLATE_PLUGIN_ROOT", "/path/to/plugin")
        result = check_python()
        assert result["status"] == expected_status

def test_check_plugin_structure():
    root = Path(__file__).resolve().parent / "test_data" / "plugin_with_files"
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(root))
        result = check_plugin_structure()
        assert result["status"] == "OK"

def test_check_commands():
    root = Path(__file__).resolve().parent / "test_data" / "plugin_with_files"
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(root))
        result = check_commands()
        assert result["status"] == "OK"
        assert len(result["details"]) > 0

def test_check_skills():
    root = Path(__file__).resolve().parent / "test_data" / "plugin_with_files"
    with pytest.MonkeyPatch.context() as m:
        m.setenv("SLATE_PLUGIN_ROOT", str(root))
        result = check_skills()
        assert result["status"] == "OK"
        assert len(result["details"]) > 0