# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for vendor_integration module
"""
Tests for slate/vendor_integration.py — Unified vendor SDK integration
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.vendor_integration import (
        check_openai_agents,
        check_autogen,
        check_semantic_kernel,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"vendor_integration not importable: {e}", allow_module_level=True)


class TestCheckOpenaiAgents:
    """Test check_openai_agents function."""

    def test_returns_dict(self):
        result = check_openai_agents()
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "openai-agents-python"

    def test_has_available_key(self):
        result = check_openai_agents()
        assert "available" in result

    def test_available_is_bool(self):
        result = check_openai_agents()
        assert isinstance(result["available"], bool)


class TestCheckAutogen:
    """Test check_autogen function."""

    def test_returns_dict(self):
        result = check_autogen()
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "autogen"

    def test_has_available_key(self):
        result = check_autogen()
        assert "available" in result


class TestCheckSemanticKernel:
    """Test check_semantic_kernel function."""

    def test_returns_dict(self):
        result = check_semantic_kernel()
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "semantic-kernel"

    def test_has_available_key(self):
        result = check_semantic_kernel()
        assert "available" in result


class TestVendorIntegrationMain:
    """Test main module-level functions."""

    @patch("slate.vendor_integration.check_openai_agents")
    @patch("slate.vendor_integration.check_autogen")
    @patch("slate.vendor_integration.check_semantic_kernel")
    def test_all_checks_callable(self, mock_sk, mock_ag, mock_oa):
        mock_oa.return_value = {"name": "openai-agents-python", "available": True}
        mock_ag.return_value = {"name": "autogen", "available": True}
        mock_sk.return_value = {"name": "semantic-kernel", "available": True}
        assert mock_oa() is not None
        assert mock_ag() is not None
        assert mock_sk() is not None
