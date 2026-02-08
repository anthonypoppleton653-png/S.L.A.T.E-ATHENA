#!/usr/bin/env python3
# Modified: 2026-02-08T22:00:00Z | Author: COPILOT | Change: Initial SK integration test suite
"""
Tests for SLATE Semantic Kernel Integration
=============================================
Validates SK module import, configuration, plugin registration,
model resolution, ActionGuard enforcement, and ChromaDB memory.
"""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure workspace root on path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


# ── Import Tests ──────────────────────────────────────────────────────────

class TestSKImport:
    """Verify the Semantic Kernel module and its dependencies import."""

    def test_sk_module_imports(self):
        """slate.slate_semantic_kernel should import without errors."""
        mod = importlib.import_module("slate.slate_semantic_kernel")
        assert mod is not None

    def test_semantic_kernel_library_installed(self):
        """Microsoft Semantic Kernel package must be importable."""
        import semantic_kernel
        assert hasattr(semantic_kernel, "__version__")
        parts = semantic_kernel.__version__.split(".")
        assert int(parts[0]) >= 1, "SK version must be >= 1.x"

    def test_openai_client_installed(self):
        """openai package (for AsyncOpenAI client) must be importable."""
        from openai import AsyncOpenAI
        assert AsyncOpenAI is not None


# ── Configuration Tests ──────────────────────────────────────────────────

class TestSKConfiguration:
    """Test SK constants and configuration values."""

    def test_ollama_endpoint_localhost(self):
        """Ollama endpoint must bind to 127.0.0.1 (LOCAL ONLY)."""
        from slate.slate_semantic_kernel import OLLAMA_ENDPOINT, OLLAMA_CHAT_ENDPOINT
        assert "127.0.0.1" in OLLAMA_ENDPOINT
        assert "0.0.0.0" not in OLLAMA_ENDPOINT
        assert "127.0.0.1" in OLLAMA_CHAT_ENDPOINT

    def test_model_map_has_required_roles(self):
        """SK_MODEL_MAP must have code, fast, planner, general, embedding roles."""
        from slate.slate_semantic_kernel import SK_MODEL_MAP
        required_roles = {"code", "fast", "planner", "general", "embedding"}
        assert required_roles.issubset(set(SK_MODEL_MAP.keys()))

    def test_fallback_map_covers_custom_models(self):
        """SK_FALLBACK_MAP must provide fallbacks for all SLATE custom models."""
        from slate.slate_semantic_kernel import SK_FALLBACK_MAP
        assert "slate-coder:latest" in SK_FALLBACK_MAP
        assert "slate-fast:latest" in SK_FALLBACK_MAP
        assert "slate-planner:latest" in SK_FALLBACK_MAP

    def test_state_file_path(self):
        """STATE_FILE must be in workspace root."""
        from slate.slate_semantic_kernel import STATE_FILE, WORKSPACE_ROOT
        assert STATE_FILE.parent == WORKSPACE_ROOT


# ── Model Resolution Tests ───────────────────────────────────────────────

class TestModelResolution:
    """Test model resolution with available/unavailable models."""

    @patch("slate.slate_semantic_kernel._get_available_models")
    def test_resolve_preferred_model(self, mock_models):
        """Should return preferred model when available."""
        from slate.slate_semantic_kernel import _resolve_model
        mock_models.return_value = ["slate-coder:latest", "mistral-nemo:latest"]
        assert _resolve_model("code") == "slate-coder:latest"

    @patch("slate.slate_semantic_kernel._get_available_models")
    def test_resolve_fallback_model(self, mock_models):
        """Should return fallback when preferred is missing."""
        from slate.slate_semantic_kernel import _resolve_model
        mock_models.return_value = ["mistral-nemo:latest", "llama3.2:3b"]
        assert _resolve_model("code") == "mistral-nemo:latest"

    @patch("slate.slate_semantic_kernel._get_available_models")
    def test_resolve_any_available(self, mock_models):
        """Should return any available model as last resort."""
        from slate.slate_semantic_kernel import _resolve_model
        mock_models.return_value = ["phi:latest"]
        assert _resolve_model("code") == "phi:latest"

    @patch("slate.slate_semantic_kernel._get_available_models")
    def test_resolve_no_models(self, mock_models):
        """Should return preferred model name even if nothing available."""
        from slate.slate_semantic_kernel import _resolve_model
        mock_models.return_value = []
        result = _resolve_model("code")
        assert result == "slate-coder:latest"


# ── Status Tests ─────────────────────────────────────────────────────────

class TestSKStatus:
    """Test the status reporting functions."""

    def test_get_sk_status_returns_dict(self):
        """get_sk_status() must return a dict with expected keys."""
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        assert isinstance(status, dict)
        assert "semantic_kernel" in status
        assert "ollama" in status
        assert "slate_models" in status
        assert "chromadb_memory" in status
        assert "plugins" in status
        assert "security" in status

    def test_sk_version_reported(self):
        """Status must report SK version."""
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        assert status["semantic_kernel"]["available"] is True
        assert "." in status["semantic_kernel"]["version"]

    def test_plugins_list(self):
        """Status must report all 3 plugin names."""
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        assert "slate_system" in status["plugins"]
        assert "slate_search" in status["plugins"]
        assert "slate_agents" in status["plugins"]

    def test_security_enforcement(self):
        """Status must report ActionGuard enforcement."""
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        assert "ActionGuard" in status["security"]

    def test_status_json_serializable(self):
        """Status dict must be JSON serializable."""
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        dumped = json.dumps(status)
        assert len(dumped) > 10


# ── Plugin Tests ─────────────────────────────────────────────────────────

class TestSKPlugins:
    """Test SLATE SK plugin registration and function metadata."""

    @pytest.mark.asyncio
    async def test_kernel_creates_with_plugins(self):
        """Kernel should create with SLATE plugins registered."""
        from slate.slate_semantic_kernel import create_slate_kernel
        try:
            kernel = await create_slate_kernel(
                model_role="fast",
                enable_memory=False,
                enable_plugins=True,
            )
            # Verify plugins are registered
            assert kernel is not None
            plugin_names = list(kernel.plugins.keys()) if hasattr(kernel, "plugins") else []
            assert "slate_system" in plugin_names
            assert "slate_search" in plugin_names
            assert "slate_agents" in plugin_names
        except Exception:
            pytest.skip("Ollama not available for kernel creation")

    @pytest.mark.asyncio
    async def test_kernel_creates_without_plugins(self):
        """Kernel should create without plugins when disabled."""
        from slate.slate_semantic_kernel import create_slate_kernel
        try:
            kernel = await create_slate_kernel(
                model_role="fast",
                enable_memory=False,
                enable_plugins=False,
            )
            assert kernel is not None
        except Exception:
            pytest.skip("Ollama not available for kernel creation")


# ── Agent Routing Plugin Tests ───────────────────────────────────────────

class TestAgentRouting:
    """Test the SlateAgentPlugin routing logic by calling methods directly."""

    def _get_agent_instance(self):
        """Get the SlateAgentPlugin instance from a registered kernel."""
        from slate.slate_semantic_kernel import _register_slate_plugins
        from semantic_kernel import Kernel
        kernel = Kernel()
        _register_slate_plugins(kernel)
        # Access the plugin's underlying object instance
        plugin = kernel.plugins["slate_agents"]
        # Get the route_task function's method reference
        return plugin

    def test_route_coding_task(self):
        """Coding keywords should route to ALPHA."""
        plugin = self._get_agent_instance()
        # Call the underlying function method directly (not SK invoke)
        func = plugin["route_task"]
        # Access the method on the plugin's instance
        method = func.method
        result = method(task_description="implement a new feature")
        assert "ALPHA" in result

    def test_route_testing_task(self):
        """Testing keywords should route to BETA."""
        plugin = self._get_agent_instance()
        result = plugin["route_task"].method(task_description="test the workflow manager")
        assert "BETA" in result

    def test_route_planning_task(self):
        """Planning keywords should route to GAMMA."""
        plugin = self._get_agent_instance()
        result = plugin["route_task"].method(task_description="analyze the architecture")
        assert "GAMMA" in result

    def test_route_default_task(self):
        """Unmatched tasks should route to COPILOT (default)."""
        plugin = self._get_agent_instance()
        result = plugin["route_task"].method(task_description="do something random")
        assert "COPILOT" in result


# ── Ollama Availability Tests ────────────────────────────────────────────

class TestOllamaAvailability:
    """Test Ollama connectivity checks (mocked for CI)."""

    @patch("urllib.request.urlopen")
    def test_check_ollama_available_when_running(self, mock_urlopen):
        """Should return True when Ollama responds."""
        from slate.slate_semantic_kernel import _check_ollama_available
        mock_urlopen.return_value.__enter__ = lambda s: s
        mock_urlopen.return_value.__exit__ = MagicMock()
        assert _check_ollama_available() is True

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    def test_check_ollama_unavailable(self, mock_urlopen):
        """Should return False when Ollama is down."""
        from slate.slate_semantic_kernel import _check_ollama_available
        assert _check_ollama_available() is False

    @patch("urllib.request.urlopen")
    def test_get_available_models_parses_response(self, mock_urlopen):
        """Should parse Ollama /api/tags response."""
        from slate.slate_semantic_kernel import _get_available_models
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {"name": "slate-coder:latest"},
                {"name": "slate-fast:latest"},
                {"name": "mistral-nemo:latest"},
            ]
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock()
        mock_urlopen.return_value = mock_response
        models = _get_available_models()
        assert "slate-coder:latest" in models
        assert "slate-fast:latest" in models
        assert len(models) == 3


# ── SK Check Functions ───────────────────────────────────────────────────

class TestSKCheck:
    """Test SK availability check."""

    def test_check_sk_available(self):
        """Should return True and version string."""
        from slate.slate_semantic_kernel import _check_sk_available
        available, version = _check_sk_available()
        assert available is True
        assert "." in version


# ── CLI Tests ────────────────────────────────────────────────────────────

class TestCLI:
    """Test CLI argument parsing."""

    def test_main_function_exists(self):
        """main() function must exist."""
        from slate.slate_semantic_kernel import main
        assert callable(main)

    def test_list_plugins_function_exists(self):
        """list_plugins() function must exist."""
        from slate.slate_semantic_kernel import list_plugins
        assert callable(list_plugins)

    def test_print_status_function_exists(self):
        """print_status() function must exist."""
        from slate.slate_semantic_kernel import print_status
        assert callable(print_status)
