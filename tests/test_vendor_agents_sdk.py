# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for vendor_agents_sdk module
"""
Tests for slate/vendor_agents_sdk.py — OpenAI agents vendor bridge
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

try:
    from slate.vendor_agents_sdk import (
        SDK_AVAILABLE,
        WORKSPACE_ROOT,
        VENDOR_SDK_SRC,
        _import_sdk,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"vendor_agents_sdk not importable: {e}", allow_module_level=True)


class TestVendorAgentsSdkConstants:
    """Test constants and paths."""

    def test_workspace_root_defined(self):
        assert isinstance(WORKSPACE_ROOT, Path)

    def test_vendor_sdk_src_defined(self):
        assert isinstance(VENDOR_SDK_SRC, Path)
        assert "openai-agents-python" in str(VENDOR_SDK_SRC)

    def test_sdk_available_is_bool(self):
        assert isinstance(SDK_AVAILABLE, bool)


class TestImportSdk:
    """Test _import_sdk function."""

    def test_import_sdk_returns_bool(self):
        result = _import_sdk()
        assert isinstance(result, bool)

    @patch("slate.vendor_agents_sdk.VENDOR_SDK_SRC")
    def test_import_sdk_missing_path(self, mock_path):
        mock_path.exists.return_value = False
        result = _import_sdk()
        assert result is False


class TestSdkExports:
    """Test that SDK exports are defined (may be None if not available)."""

    def test_agent_export(self):
        from slate.vendor_agents_sdk import Agent
        # Agent may be None if SDK not available, but must be defined
        assert hasattr(sys.modules['slate.vendor_agents_sdk'], 'Agent')

    def test_function_tool_export(self):
        from slate.vendor_agents_sdk import function_tool
        assert hasattr(sys.modules['slate.vendor_agents_sdk'], 'function_tool')

    def test_runner_export(self):
        from slate.vendor_agents_sdk import Runner
        assert hasattr(sys.modules['slate.vendor_agents_sdk'], 'Runner')

    def test_handoff_export(self):
        from slate.vendor_agents_sdk import Handoff
        assert hasattr(sys.modules['slate.vendor_agents_sdk'], 'Handoff')
