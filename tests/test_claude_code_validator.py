# Modified: 2026-02-08T22:10:00Z | Author: COPILOT | Change: Add test coverage for slate/claude_code_validator.py
"""
Tests for slate/claude_code_validator.py — Claude Code configuration validator.
Tests focus on ValidationResult, ClaudeCodeConfig, ClaudeCodeValidator,
and security integration without modifying real config files.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestClaudeCodeValidatorImport:
    """Test module imports correctly."""

    def test_import_module(self):
        import slate.claude_code_validator
        assert hasattr(slate.claude_code_validator, 'ClaudeCodeValidator')
        assert hasattr(slate.claude_code_validator, 'ValidationResult')
        assert hasattr(slate.claude_code_validator, 'ClaudeCodeConfig')

    def test_import_functions(self):
        from slate.claude_code_validator import create_pretool_hook, create_claude_code_mcp_tool
        assert callable(create_pretool_hook)
        assert callable(create_claude_code_mcp_tool)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_create_valid_result(self):
        from slate.claude_code_validator import ValidationResult
        result = ValidationResult(valid=True, component="test", message="All good")
        assert result.valid is True
        assert result.component == "test"
        assert result.message == "All good"
        assert result.suggestions == []

    def test_create_invalid_result(self):
        from slate.claude_code_validator import ValidationResult
        result = ValidationResult(
            valid=False,
            component="broken",
            message="Something failed",
            suggestions=["Fix it", "Try again"]
        )
        assert result.valid is False
        assert len(result.suggestions) == 2

    def test_str_representation_pass(self):
        from slate.claude_code_validator import ValidationResult
        result = ValidationResult(valid=True, component="comp", message="OK")
        assert "[PASS]" in str(result)
        assert "comp" in str(result)

    def test_str_representation_fail(self):
        from slate.claude_code_validator import ValidationResult
        result = ValidationResult(valid=False, component="comp", message="Bad")
        assert "[FAIL]" in str(result)


class TestClaudeCodeConfig:
    """Test ClaudeCodeConfig dataclass."""

    def test_create_default_config(self):
        from slate.claude_code_validator import ClaudeCodeConfig
        config = ClaudeCodeConfig()
        assert config.settings_path is None
        assert config.settings == {}
        assert config.mcp_servers == {}
        assert config.permissions == {}
        assert config.plugins == []
        assert config.hooks == {}

    def test_config_with_values(self):
        from slate.claude_code_validator import ClaudeCodeConfig
        config = ClaudeCodeConfig(
            settings={"key": "value"},
            mcp_servers={"slate": {"command": "python"}},
        )
        assert config.settings["key"] == "value"
        assert "slate" in config.mcp_servers


class TestClaudeCodeValidator:
    """Test ClaudeCodeValidator class."""

    def test_validator_init_with_workspace(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        assert validator.workspace == workspace
        assert validator.config is not None

    def test_validator_loads_config(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        # Should have attempted to load .claude/settings.json
        assert isinstance(validator.config.settings, dict)

    def test_validate_all_returns_list(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_all()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_validate_all_returns_validation_results(self):
        from slate.claude_code_validator import ClaudeCodeValidator, ValidationResult
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_all()
        for r in results:
            assert isinstance(r, ValidationResult)

    def test_validate_settings(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_settings()
        assert isinstance(results, list)
        # Should check for settings.json existence
        assert any("settings" in r.component.lower() for r in results)

    def test_validate_mcp_servers(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_mcp_servers()
        assert isinstance(results, list)

    def test_validate_permissions(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_permissions()
        assert isinstance(results, list)

    def test_validate_hooks(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_hooks()
        assert isinstance(results, list)

    def test_validate_security_integration(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_security_integration()
        assert isinstance(results, list)
        # Should check ActionGuard
        assert any("action_guard" in r.component.lower() or "security" in r.component.lower()
                    for r in results)

    def test_validate_sdk_compatibility(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        workspace = Path(__file__).parent.parent
        validator = ClaudeCodeValidator(workspace=workspace)
        results = validator.validate_sdk_compatibility()
        assert isinstance(results, list)


class TestValidatorWithTempWorkspace:
    """Test validator with a temporary workspace directory."""

    def test_empty_workspace(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = ClaudeCodeValidator(workspace=Path(tmpdir))
            results = validator.validate_all()
            assert isinstance(results, list)
            # Should report missing settings
            assert any(not r.valid for r in results)

    def test_workspace_with_settings(self):
        from slate.claude_code_validator import ClaudeCodeValidator
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            settings = {"behavior": {"profile": "test"}}
            (claude_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")

            validator = ClaudeCodeValidator(workspace=Path(tmpdir))
            results = validator.validate_settings()
            assert any(r.valid and "settings" in r.component.lower() for r in results)


class TestCreatePretoolHook:
    """Test create_pretool_hook function."""

    def test_returns_dict(self):
        from slate.claude_code_validator import create_pretool_hook
        hook = create_pretool_hook()
        assert isinstance(hook, dict)


class TestValidateToolUse:
    """Test _validate_tool_use function."""

    def test_validate_safe_tool(self):
        from slate.claude_code_validator import _validate_tool_use
        result = _validate_tool_use("Read", {"path": "slate/slate_status.py"})
        assert isinstance(result, dict)

    def test_validate_bash_tool(self):
        from slate.claude_code_validator import _validate_tool_use
        result = _validate_tool_use("Bash", {"command": "python slate/slate_status.py"})
        assert isinstance(result, dict)


class TestCreateMCPTool:
    """Test create_claude_code_mcp_tool function."""

    def test_returns_dict(self):
        from slate.claude_code_validator import create_claude_code_mcp_tool
        tool = create_claude_code_mcp_tool()
        assert isinstance(tool, dict)
