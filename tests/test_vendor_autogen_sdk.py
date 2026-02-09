# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for vendor_autogen_sdk module
"""
Tests for slate/vendor_autogen_sdk.py — AutoGen vendor bridge
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

try:
    from slate.vendor_autogen_sdk import (
        SDK_AVAILABLE,
        WORKSPACE_ROOT,
        AUTOGEN_CORE_SRC,
        _import_sdk,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"vendor_autogen_sdk not importable: {e}", allow_module_level=True)


class TestVendorAutogenSdkConstants:
    """Test constants and paths."""

    def test_workspace_root_defined(self):
        assert isinstance(WORKSPACE_ROOT, Path)

    def test_autogen_core_src_defined(self):
        assert isinstance(AUTOGEN_CORE_SRC, Path)
        assert "autogen" in str(AUTOGEN_CORE_SRC)

    def test_sdk_available_is_bool(self):
        assert isinstance(SDK_AVAILABLE, bool)


class TestImportSdk:
    """Test _import_sdk function."""

    def test_import_sdk_returns_bool(self):
        result = _import_sdk()
        assert isinstance(result, bool)

    @patch("slate.vendor_autogen_sdk.AUTOGEN_CORE_SRC")
    def test_import_sdk_missing_path(self, mock_path):
        mock_path.exists.return_value = False
        result = _import_sdk()
        assert result is False


class TestSdkExports:
    """Test that SDK exports are defined."""

    def test_agent_export_defined(self):
        from slate.vendor_autogen_sdk import Agent
        assert hasattr(sys.modules['slate.vendor_autogen_sdk'], 'Agent')

    def test_base_agent_export_defined(self):
        from slate.vendor_autogen_sdk import BaseAgent
        assert hasattr(sys.modules['slate.vendor_autogen_sdk'], 'BaseAgent')

    def test_agent_runtime_export_defined(self):
        from slate.vendor_autogen_sdk import AgentRuntime
        assert hasattr(sys.modules['slate.vendor_autogen_sdk'], 'AgentRuntime')

    def test_closure_agent_export_defined(self):
        from slate.vendor_autogen_sdk import ClosureAgent
        assert hasattr(sys.modules['slate.vendor_autogen_sdk'], 'ClosureAgent')
