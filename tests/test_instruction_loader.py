#!/usr/bin/env python3
# Modified: 2026-02-08T18:00:00Z | Author: Claude Opus 4.5 | Change: Create tests for instruction loader
"""
Tests for slate/instruction_loader.py

Tests cover:
- K8s environment detection
- ConfigMap loading (when mounted)
- Local file fallback
- Agent prompt retrieval
- MCP tool definitions
- Caching with TTL
- Hot-reload support
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate.instruction_loader import (
    InstructionLoader,
    InstructionSet,
    get_instruction_loader,
    K8S_CONFIG_PATH,
    WORKSPACE_ROOT as LOADER_WORKSPACE_ROOT,
)


class TestEnvironmentDetection:
    """Test K8s environment detection."""

    def test_detects_k8s_via_env_var(self):
        """Should detect K8s when KUBERNETES_SERVICE_HOST is set."""
        with patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}):
            loader = InstructionLoader(cache_ttl_seconds=0)
            assert loader.is_k8s_environment() is True

    def test_detects_local_when_no_k8s_markers(self):
        """Should detect local environment when no K8s markers exist."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any K8s env vars
            env_clean = {k: v for k, v in os.environ.items()
                        if not k.startswith("KUBERNETES")}
            with patch.dict(os.environ, env_clean, clear=True):
                loader = InstructionLoader(
                    config_path=Path("/nonexistent/path"),
                    cache_ttl_seconds=0
                )
                # This will be False unless the config_path exists
                result = loader.is_k8s_environment()
                # In local test env, this should be False
                assert result is False


class TestLocalFallback:
    """Test loading instructions from local files."""

    def test_loads_from_local_when_no_configmap(self):
        """Should load from local files when ConfigMap not mounted."""
        loader = InstructionLoader(
            config_path=Path("/nonexistent/configmap"),
            local_fallback=LOADER_WORKSPACE_ROOT,
            cache_ttl_seconds=0
        )

        instructions = loader.load_instructions()

        # Should use local source
        assert instructions.source == "local"
        # Should have loaded CLAUDE.md if it exists
        claude_md_path = LOADER_WORKSPACE_ROOT / "CLAUDE.md"
        if claude_md_path.exists():
            assert len(instructions.claude_md) > 0

    def test_fallback_to_default_agent_prompts(self):
        """Should use default agent prompts in local mode."""
        loader = InstructionLoader(
            config_path=Path("/nonexistent/configmap"),
            cache_ttl_seconds=0
        )

        # Should have default agents
        configs = loader.get_agent_configs()
        assert len(configs) >= 4  # ALPHA, BETA, GAMMA, DELTA

        agent_names = [c["name"] for c in configs]
        assert "slate-alpha" in agent_names
        assert "slate-beta" in agent_names


class TestAgentPrompts:
    """Test agent prompt retrieval."""

    def test_get_agent_prompt_alpha(self):
        """Should return prompt for ALPHA agent."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        prompt = loader.get_agent_prompt("ALPHA")

        assert "ALPHA" in prompt or "coding" in prompt.lower()

    def test_get_agent_prompt_case_insensitive(self):
        """Should handle case-insensitive agent names."""
        loader = InstructionLoader(cache_ttl_seconds=0)

        prompt_upper = loader.get_agent_prompt("ALPHA")
        prompt_lower = loader.get_agent_prompt("alpha")

        # Both should return the same prompt
        assert prompt_upper == prompt_lower

    def test_get_agent_prompt_unknown_returns_empty(self):
        """Should return empty string for unknown agent."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        prompt = loader.get_agent_prompt("NONEXISTENT")

        assert prompt == ""

    def test_get_agent_config(self):
        """Should return full config for agent."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        config = loader.get_agent_config("BETA")

        assert isinstance(config, dict)
        if config:  # May be empty if agent not found
            assert "prompt" in config or "name" in config


class TestMCPTools:
    """Test MCP tool definition retrieval."""

    def test_get_mcp_tool_definitions(self):
        """Should return list of MCP tool definitions."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        tools = loader.get_mcp_tool_definitions()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        first_tool = tools[0]
        assert "name" in first_tool
        assert "description" in first_tool

    def test_mcp_tools_have_slate_prefix(self):
        """All MCP tools should have slate_ prefix."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        tools = loader.get_mcp_tool_definitions()

        for tool in tools:
            assert tool["name"].startswith("slate_"), f"Tool {tool['name']} missing slate_ prefix"

    def test_mcp_tools_have_input_schema(self):
        """Tools should have input_schema."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        tools = loader.get_mcp_tool_definitions()

        for tool in tools:
            assert "input_schema" in tool, f"Tool {tool['name']} missing input_schema"


class TestCaching:
    """Test instruction caching."""

    def test_caches_instructions(self):
        """Should cache instructions within TTL."""
        loader = InstructionLoader(cache_ttl_seconds=60)

        # First load
        instructions1 = loader.load_instructions()
        version1 = instructions1.version

        # Second load (should be cached)
        instructions2 = loader.load_instructions()
        version2 = instructions2.version

        assert version1 == version2

    def test_cache_expires_after_ttl(self):
        """Should reload after TTL expires."""
        loader = InstructionLoader(cache_ttl_seconds=1)

        # First load
        instructions1 = loader.load_instructions()
        loaded_at1 = instructions1.loaded_at

        # Wait for TTL to expire
        time.sleep(1.1)

        # Second load (should reload)
        instructions2 = loader.load_instructions()
        loaded_at2 = instructions2.loaded_at

        # Timestamps should be different (reloaded)
        assert loaded_at1 != loaded_at2

    def test_force_reload_bypasses_cache(self):
        """force_reload should bypass cache."""
        loader = InstructionLoader(cache_ttl_seconds=300)

        # First load
        instructions1 = loader.load_instructions()
        loaded_at1 = instructions1.loaded_at

        # Force reload immediately
        time.sleep(0.1)  # Small delay to ensure different timestamp
        instructions2 = loader.force_reload()
        loaded_at2 = instructions2.loaded_at

        # Should have reloaded
        assert loaded_at1 != loaded_at2


class TestConfigMapLoading:
    """Test loading from ConfigMap (simulated)."""

    def test_loads_from_configmap_when_mounted(self):
        """Should load from ConfigMap when mount path exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)

            # Create simulated ConfigMap files
            (config_path / "agent-prompts.yaml").write_text("""
agents:
  TEST_AGENT:
    name: slate-test
    display_name: Test Agent
    prompt: This is a test agent prompt
    tools: []
""")
            (config_path / "mcp-tools.yaml").write_text("""
tools:
  - name: slate_test_tool
    description: A test tool
    input_schema:
      type: object
      properties: {}
""")

            loader = InstructionLoader(
                config_path=config_path,
                cache_ttl_seconds=0
            )

            # Should detect as K8s environment (config path exists)
            assert loader.is_k8s_environment() is True

            # Should load from ConfigMap
            instructions = loader.load_instructions()
            assert instructions.source == "configmap"

    def test_configmap_agent_prompts_parsed(self):
        """Should parse agent prompts from ConfigMap YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)

            (config_path / "agent-prompts.yaml").write_text("""
agents:
  CUSTOM:
    name: slate-custom
    display_name: Custom Agent
    prompt: Custom prompt text
    tools:
      - slate_status
      - slate_workflow
""")

            loader = InstructionLoader(
                config_path=config_path,
                cache_ttl_seconds=0
            )

            prompt = loader.get_agent_prompt("CUSTOM")
            assert "Custom prompt text" in prompt


class TestHotReload:
    """Test hot-reload functionality."""

    def test_watch_for_changes_registers_callback(self):
        """Should register callback for changes."""
        loader = InstructionLoader(cache_ttl_seconds=0)

        callback_called = []
        def callback():
            callback_called.append(True)

        # Register callback
        loader.watch_for_changes(callback, poll_interval=1.0)

        # Should have started watcher
        assert loader._watcher_thread is not None
        assert loader._watcher_thread.is_alive()

        # Cleanup
        loader.stop_watching()

    def test_stop_watching_stops_thread(self):
        """Should stop watcher thread."""
        loader = InstructionLoader(cache_ttl_seconds=0)

        loader.watch_for_changes(lambda: None, poll_interval=1.0)
        assert loader._watcher_thread is not None

        loader.stop_watching()

        # Thread should be stopped
        assert loader._watcher_thread is None or not loader._watcher_thread.is_alive()


class TestInstructionSet:
    """Test InstructionSet dataclass."""

    def test_to_dict(self):
        """Should convert to dict for serialization."""
        instructions = InstructionSet(
            claude_md="# Test",
            source="local",
            loaded_at="2026-02-08T00:00:00Z",
            version="abc123def456",
        )

        d = instructions.to_dict()

        assert d["source"] == "local"
        assert d["claude_md_length"] == 6
        assert "abc123" in d["version"]


class TestSingleton:
    """Test singleton pattern."""

    def test_get_instruction_loader_returns_same_instance(self):
        """Should return same instance on repeated calls."""
        # Note: This test may interfere with other tests due to singleton
        # In real test suite, you'd want to reset the singleton between tests
        loader1 = get_instruction_loader()
        loader2 = get_instruction_loader()

        assert loader1 is loader2


class TestStatus:
    """Test status reporting."""

    def test_get_status(self):
        """Should return comprehensive status dict."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        status = loader.get_status()

        assert "is_k8s" in status
        assert "config_path" in status
        assert "instructions" in status
        assert "watcher_active" in status

    def test_get_source(self):
        """Should return instruction source."""
        loader = InstructionLoader(
            config_path=Path("/nonexistent"),
            cache_ttl_seconds=0
        )

        source = loader.get_source()
        assert source in ["configmap", "local", "default"]

    def test_get_version(self):
        """Should return content hash."""
        loader = InstructionLoader(cache_ttl_seconds=0)
        version = loader.get_version()

        # Should be SHA256 hex digest (64 chars)
        assert len(version) == 64
        assert all(c in "0123456789abcdef" for c in version)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
