# tests/test_claude_code_manager.py

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from slate.claude_code_manager import (
    get_user_claude_dir,
    get_project_claude_dir,
    HookResult,
    HookContext,
    HookRegistry,
)

@pytest.fixture
def mock_guard():
    return MagicMock()

@pytest.mark.parametrize(
    "platform, expected",
    [
        ("win32", Path("C:/Users/USERNAME/.claude")),
        ("linux", Path.home() / ".claude"),
    ],
)
def test_get_user_claude_dir(platform, expected):
    with patch.dict(os.environ, {"USERPROFILE": "" if platform == "win32" else None}):
        assert get_user_claude_dir() == expected

def test_get_project_claude_dir(tmp_path):
    workspace = tmp_path / "project"
    assert get_project_claude_dir(workspace) == workspace / ".claude"

def test_hook_registry_register_unregister(mock_guard):
    registry = HookRegistry(mock_guard)

    def mock_callback(_: HookContext) -> HookResult:
        return HookResult("allow")

    registry.register("PreToolUse", "Test", mock_callback)
    assert len(registry._hooks["PreToolUse"]) == 1
    assert registry.unregister("PreToolUse", "Test")
    assert len(registry._hooks["PreToolUse"]) == 0

    with pytest.raises(ValueError):
        registry.register("UnknownEvent", ".*", mock_callback)