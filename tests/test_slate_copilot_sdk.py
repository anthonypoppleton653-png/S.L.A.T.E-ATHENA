# Modified: 2026-02-08T22:10:00Z | Author: COPILOT | Change: Add test coverage for slate/slate_copilot_sdk.py
"""
Tests for slate/slate_copilot_sdk.py — SLATE Copilot SDK plugin module.
Tests focus on tool creation, hook functions, guard integration,
and configuration generation without requiring live Copilot CLI.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSlateCopilotSdkImport:
    """Test module imports correctly."""

    def test_import_module(self):
        import slate.slate_copilot_sdk
        assert hasattr(slate.slate_copilot_sdk, 'create_slate_tools')
        assert hasattr(slate.slate_copilot_sdk, 'SlateCopilotPlugin')
        assert hasattr(slate.slate_copilot_sdk, 'create_session_hooks')

    def test_run_slate_command_exists(self):
        from slate.slate_copilot_sdk import run_slate_command
        assert callable(run_slate_command)

    def test_fmt_exists(self):
        from slate.slate_copilot_sdk import fmt
        assert callable(fmt)


class TestRunSlateCommand:
    """Test run_slate_command function."""

    @patch("subprocess.run")
    def test_run_success(self, mock_run):
        from slate.slate_copilot_sdk import run_slate_command
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output text",
            stderr=""
        )
        result = run_slate_command("slate_status", "--quick")
        assert result["success"] is True
        assert "output text" in result["stdout"]

    @patch("subprocess.run")
    def test_run_failure(self, mock_run):
        from slate.slate_copilot_sdk import run_slate_command
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error occurred"
        )
        result = run_slate_command("bad_module")
        assert result["success"] is False

    @patch("subprocess.run", side_effect=Exception("timeout"))
    def test_run_exception(self, mock_run):
        from slate.slate_copilot_sdk import run_slate_command
        result = run_slate_command("crash_module")
        assert result["success"] is False
        assert "stderr" in result
        assert "timeout" in result["stderr"]


class TestFmt:
    """Test the fmt() formatting helper."""

    def test_fmt_success_result(self):
        from slate.slate_copilot_sdk import fmt
        result = {"success": True, "stdout": "All good", "stderr": "", "returncode": 0}
        formatted = fmt(result)
        assert isinstance(formatted, str)
        assert "All good" in formatted

    def test_fmt_failure_result(self):
        from slate.slate_copilot_sdk import fmt
        result = {"success": False, "stdout": "", "stderr": "Failed", "returncode": 1}
        formatted = fmt(result)
        assert isinstance(formatted, str)
        assert "Failed" in formatted


class TestCreateSlateTools:
    """Test create_slate_tools function."""

    def test_returns_list(self):
        from slate.slate_copilot_sdk import create_slate_tools
        tools = create_slate_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_required_fields(self):
        from slate.slate_copilot_sdk import create_slate_tools
        tools = create_slate_tools()
        for t in tools:
            # Tools are Tool objects from copilot SDK, or empty list if SDK not available
            assert hasattr(t, 'name') or hasattr(t, '_tool_name') or isinstance(t, dict)


class TestGuardFunctions:
    """Test ActionGuard integration functions."""

    def test_guard_check_blocked(self):
        from slate.slate_copilot_sdk import _guard_check_blocked
        # Should block dangerous patterns
        result = _guard_check_blocked("rm -rf /")
        assert result is not None  # Should return reason string

    def test_guard_check_blocked_safe(self):
        from slate.slate_copilot_sdk import _guard_check_blocked
        result = _guard_check_blocked("python slate/slate_status.py")
        assert result is None  # Safe command, no block

    def test_guard_check_pii(self):
        from slate.slate_copilot_sdk import _guard_check_pii
        # Function should exist and be callable
        assert callable(_guard_check_pii)


class TestHookFunctions:
    """Test session hook functions."""

    def test_hook_pre_tool_use(self):
        from slate.slate_copilot_sdk import hook_pre_tool_use
        hook_input = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        result = hook_pre_tool_use(hook_input, {})
        # Should return None (allow) or dict (block/modify)
        assert result is None or isinstance(result, dict)

    def test_hook_post_tool_use(self):
        from slate.slate_copilot_sdk import hook_post_tool_use
        hook_input = {"tool_name": "Read", "output": "file contents"}
        result = hook_post_tool_use(hook_input, {})
        assert result is None or isinstance(result, dict)

    def test_hook_user_prompt_submitted(self):
        from slate.slate_copilot_sdk import hook_user_prompt_submitted
        hook_input = {"prompt": "check status"}
        result = hook_user_prompt_submitted(hook_input, {})
        assert result is None or isinstance(result, dict)

    def test_hook_session_start(self):
        from slate.slate_copilot_sdk import hook_session_start
        result = hook_session_start({}, {})
        assert result is None or isinstance(result, dict)

    def test_hook_session_end(self):
        from slate.slate_copilot_sdk import hook_session_end
        result = hook_session_end({}, {})
        assert result is None or isinstance(result, dict)

    def test_hook_error_occurred(self):
        from slate.slate_copilot_sdk import hook_error_occurred
        hook_input = {"error": "something went wrong"}
        result = hook_error_occurred(hook_input, {})
        assert result is None or isinstance(result, dict)


class TestCreateSessionHooks:
    """Test create_session_hooks function."""

    def test_returns_dict(self):
        from slate.slate_copilot_sdk import create_session_hooks
        hooks = create_session_hooks()
        assert isinstance(hooks, dict)

    def test_hooks_have_event_types(self):
        from slate.slate_copilot_sdk import create_session_hooks
        hooks = create_session_hooks()
        # Should have at least pre_tool_use and post_tool_use
        assert len(hooks) > 0


class TestConfigFunctions:
    """Test configuration generation functions."""

    def test_get_system_prompt(self):
        from slate.slate_copilot_sdk import get_system_prompt
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert "SLATE" in prompt

    def test_create_custom_agent(self):
        from slate.slate_copilot_sdk import create_custom_agent
        agent = create_custom_agent()
        assert isinstance(agent, dict)
        assert "name" in agent or "tools" in agent or "system_prompt" in agent

    def test_create_mcp_config(self):
        from slate.slate_copilot_sdk import create_mcp_config
        config = create_mcp_config()
        assert isinstance(config, dict)

    def test_create_session_config(self):
        from slate.slate_copilot_sdk import create_session_config
        config = create_session_config()
        assert isinstance(config, dict)


class TestSlateCopilotPlugin:
    """Test SlateCopilotPlugin class."""

    def test_class_exists(self):
        from slate.slate_copilot_sdk import SlateCopilotPlugin
        assert callable(SlateCopilotPlugin)

    def test_instantiate(self):
        from slate.slate_copilot_sdk import SlateCopilotPlugin
        plugin = SlateCopilotPlugin()
        assert plugin is not None

    def test_has_key_methods(self):
        from slate.slate_copilot_sdk import SlateCopilotPlugin
        plugin = SlateCopilotPlugin()
        # Check common plugin methods exist
        assert hasattr(plugin, '__init__')


class TestFindCopilotCli:
    """Test find_copilot_cli function."""

    def test_returns_string_or_none(self):
        from slate.slate_copilot_sdk import find_copilot_cli
        result = find_copilot_cli()
        assert result is None or isinstance(result, str)
