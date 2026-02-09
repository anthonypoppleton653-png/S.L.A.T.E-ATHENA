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
    "platform, env_patch, expected",
    [
        ("win32", {"USERPROFILE": "C:/Users/USERNAME"}, Path("C:/Users/USERNAME/.claude")),
        ("linux", {"HOME": str(Path.home())}, Path.home() / ".claude"),
    ],
)
def test_get_user_claude_dir(platform, env_patch, expected):
    with patch("sys.platform", platform):
        with patch.dict(os.environ, env_patch):
            assert get_user_claude_dir() == expected

def test_get_project_claude_dir(tmp_path):
    workspace = tmp_path / "project"
    assert get_project_claude_dir(workspace) == workspace / ".claude"

def test_hook_registry_register_unregister(mock_guard):
    registry = HookRegistry(mock_guard)
    initial_count = len(registry._hooks["PreToolUse"])

    def mock_callback(_: HookContext) -> HookResult:
        return HookResult("allow")

    registry.register("PreToolUse", "Test", mock_callback)
    assert len(registry._hooks["PreToolUse"]) == initial_count + 1
    assert registry.unregister("PreToolUse", "Test")
    assert len(registry._hooks["PreToolUse"]) == initial_count

    with pytest.raises(ValueError):
        registry.register("UnknownEvent", ".*", mock_callback)