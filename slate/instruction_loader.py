#!/usr/bin/env python3
# Modified: 2026-02-08T18:00:00Z | Author: Claude Opus 4.5 | Change: Create instruction loader for K8s ConfigMap/local file abstraction
"""
SLATE Instruction Loader
=========================

Adaptive instruction loading from K8s ConfigMaps or local files.

This module abstracts where agent instructions come from:
- In Kubernetes: Reads from ConfigMap mounted at /config/instructions
- Locally: Falls back to CLAUDE.md, .github/copilot-instructions.md, etc.

Features:
- K8s environment detection
- ConfigMap volume reading
- Local file fallback
- Hot-reload via file watching
- Caching with configurable TTL
- Thread-safe access

Usage:
    from slate.instruction_loader import get_instruction_loader

    loader = get_instruction_loader()

    # Get agent prompts
    alpha_prompt = loader.get_agent_prompt("ALPHA")

    # Get MCP tool definitions
    tools = loader.get_mcp_tool_definitions()

    # Get full copilot instructions
    instructions = loader.get_copilot_instructions()

    # Watch for changes (hot-reload)
    loader.watch_for_changes(lambda: print("Instructions reloaded!"))
"""

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

__all__ = [
    "InstructionLoader",
    "InstructionSet",
    "get_instruction_loader",
]

logger = logging.getLogger("slate.instruction_loader")

# Workspace root (parent of slate/)
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()

# Default ConfigMap mount path in Kubernetes
K8S_CONFIG_PATH = Path("/config/instructions")

# Local fallback paths
LOCAL_CLAUDE_MD = WORKSPACE_ROOT / "CLAUDE.md"
LOCAL_COPILOT_INSTRUCTIONS = WORKSPACE_ROOT / ".github" / "copilot-instructions.md"
LOCAL_AGENTS_MD = WORKSPACE_ROOT / "AGENTS.md"


@dataclass
class InstructionSet:
    """Container for all loaded instructions."""
    claude_md: str = ""
    copilot_instructions: str = ""
    agents_md: str = ""
    agent_prompts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agent_configs: List[Dict[str, Any]] = field(default_factory=list)
    mcp_tools: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "default"  # "configmap" | "local" | "default"
    loaded_at: str = ""
    version: str = ""  # Content hash for change detection

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "claude_md_length": len(self.claude_md),
            "copilot_instructions_length": len(self.copilot_instructions),
            "agents_md_length": len(self.agents_md),
            "agent_count": len(self.agent_prompts),
            "agent_configs_count": len(self.agent_configs),
            "mcp_tools_count": len(self.mcp_tools),
            "source": self.source,
            "loaded_at": self.loaded_at,
            "version": self.version[:16] + "..." if len(self.version) > 16 else self.version,
        }


class InstructionLoader:
    """
    Adaptive instruction loader for SLATE agents.

    Sources (in priority order):
    1. K8s ConfigMap (mounted at /config/instructions)
    2. Local files (CLAUDE.md, .github/copilot-instructions.md)
    3. Hardcoded defaults (fallback)

    Thread-safe with caching and hot-reload support.
    """

    def __init__(
        self,
        config_path: Path = K8S_CONFIG_PATH,
        local_fallback: Path = WORKSPACE_ROOT,
        cache_ttl_seconds: int = 60,
    ):
        """
        Initialize the instruction loader.

        Args:
            config_path: Path where K8s ConfigMap is mounted
            local_fallback: Path to workspace root for local file fallback
            cache_ttl_seconds: How long to cache instructions before reloading
        """
        self.config_path = config_path
        self.local_fallback = local_fallback
        self.cache_ttl = cache_ttl_seconds

        # Cache state
        self._cache: Optional[InstructionSet] = None
        self._cache_time: float = 0
        self._lock = threading.RLock()

        # Watcher state
        self._watcher_thread: Optional[threading.Thread] = None
        self._watcher_stop = threading.Event()
        self._reload_callbacks: List[Callable[[], None]] = []

        # Initial load
        self._ensure_loaded()

    def is_k8s_environment(self) -> bool:
        """
        Detect if running inside Kubernetes.

        Checks for K8s environment markers in order:
        1. KUBERNETES_SERVICE_HOST env var (injected by K8s)
        2. Service account token file (mounted by K8s)
        3. ConfigMap mount path exists
        """
        # Check K8s service host env var
        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            return True

        # Check for service account token
        sa_token = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if sa_token.exists():
            return True

        # Check if ConfigMap mount exists
        if self.config_path.exists() and self.config_path.is_dir():
            return True

        return False

    def _ensure_loaded(self) -> InstructionSet:
        """Ensure instructions are loaded and cached."""
        with self._lock:
            now = time.time()
            if self._cache is None or (now - self._cache_time) > self.cache_ttl:
                self._cache = self._load_instructions()
                self._cache_time = now
            return self._cache

    def _load_instructions(self) -> InstructionSet:
        """Load instructions from appropriate source."""
        instructions = InstructionSet()
        instructions.loaded_at = datetime.now(timezone.utc).isoformat()

        if self.is_k8s_environment() and self.config_path.exists():
            # Load from K8s ConfigMap
            instructions = self._load_from_configmap(instructions)
            instructions.source = "configmap"
            logger.info(f"Loaded instructions from ConfigMap at {self.config_path}")
        else:
            # Load from local files
            instructions = self._load_from_local(instructions)
            instructions.source = "local"
            logger.info("Loaded instructions from local files")

        # Generate content hash for change detection
        content = (
            instructions.claude_md +
            instructions.copilot_instructions +
            instructions.agents_md +
            json.dumps(instructions.agent_prompts, sort_keys=True) +
            json.dumps(instructions.mcp_tools, sort_keys=True)
        )
        instructions.version = hashlib.sha256(content.encode()).hexdigest()

        return instructions

    def _load_from_configmap(self, instructions: InstructionSet) -> InstructionSet:
        """Load instructions from K8s ConfigMap mounted volume."""
        try:
            # Load claude.md
            claude_md_path = self.config_path / "claude.md"
            if claude_md_path.exists():
                instructions.claude_md = claude_md_path.read_text(encoding="utf-8")

            # Load copilot-instructions.md
            copilot_path = self.config_path / "copilot-instructions.md"
            if copilot_path.exists():
                instructions.copilot_instructions = copilot_path.read_text(encoding="utf-8")

            # Load agents.md
            agents_md_path = self.config_path / "agents.md"
            if agents_md_path.exists():
                instructions.agents_md = agents_md_path.read_text(encoding="utf-8")

            # Load agent prompts (YAML)
            agent_prompts_path = self.config_path / "agent-prompts.yaml"
            if agent_prompts_path.exists():
                instructions.agent_prompts = self._parse_yaml(
                    agent_prompts_path.read_text(encoding="utf-8")
                )
                # Convert to agent configs list
                instructions.agent_configs = self._prompts_to_configs(
                    instructions.agent_prompts
                )

            # Load MCP tools (YAML)
            mcp_tools_path = self.config_path / "mcp-tools.yaml"
            if mcp_tools_path.exists():
                tools_data = self._parse_yaml(
                    mcp_tools_path.read_text(encoding="utf-8")
                )
                instructions.mcp_tools = tools_data.get("tools", [])

        except Exception as e:
            logger.error(f"Error loading from ConfigMap: {e}")
            # Fall back to local
            return self._load_from_local(instructions)

        return instructions

    def _load_from_local(self, instructions: InstructionSet) -> InstructionSet:
        """Load instructions from local filesystem."""
        # Load CLAUDE.md
        if LOCAL_CLAUDE_MD.exists():
            try:
                instructions.claude_md = LOCAL_CLAUDE_MD.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read CLAUDE.md: {e}")

        # Load copilot-instructions.md
        if LOCAL_COPILOT_INSTRUCTIONS.exists():
            try:
                instructions.copilot_instructions = LOCAL_COPILOT_INSTRUCTIONS.read_text(
                    encoding="utf-8"
                )
            except Exception as e:
                logger.warning(f"Could not read copilot-instructions.md: {e}")

        # Load AGENTS.md
        if LOCAL_AGENTS_MD.exists():
            try:
                instructions.agents_md = LOCAL_AGENTS_MD.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read AGENTS.md: {e}")

        # For local mode, use default agent configs and MCP tools
        instructions.agent_prompts = self._get_default_agent_prompts()
        instructions.agent_configs = self._prompts_to_configs(instructions.agent_prompts)
        instructions.mcp_tools = self._get_default_mcp_tools()

        return instructions

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML content, with fallback to JSON parsing."""
        if YAML_AVAILABLE:
            try:
                return yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                logger.warning(f"YAML parse error, trying JSON: {e}")

        # Fallback to JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Could not parse content as YAML or JSON")
            return {}

    def _prompts_to_configs(
        self, prompts: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert agent prompts dict to CustomAgentConfig list format."""
        configs = []
        agents = prompts.get("agents", prompts)

        for name, config in agents.items():
            if isinstance(config, dict):
                configs.append({
                    "name": config.get("name", f"slate-{name.lower()}"),
                    "display_name": config.get("display_name", f"SLATE {name}"),
                    "description": config.get("description", ""),
                    "prompt": config.get("prompt", ""),
                    "tools": config.get("tools", []),
                })

        return configs

    def _get_default_agent_prompts(self) -> Dict[str, Any]:
        """Get default agent prompts (hardcoded fallback)."""
        return {
            "agents": {
                "ALPHA": {
                    "name": "slate-alpha",
                    "display_name": "SLATE Alpha (Coder)",
                    "description": "Coding agent - implements features, fixes bugs, builds components. GPU-accelerated.",
                    "prompt": (
                        "You are ALPHA, the SLATE coding agent. You implement code changes, fix bugs, "
                        "and build new features for the S.L.A.T.E. framework. Use the slate_* tools to "
                        "check system health before making changes. Always follow SLATE code edit rules: "
                        "include timestamp+author comments. Local-only operations (127.0.0.1)."
                    ),
                    "tools": ["slate_system_status", "slate_runtime_check", "slate_workflow",
                              "slate_agent_registry", "slate_security_audit"],
                },
                "BETA": {
                    "name": "slate-beta",
                    "display_name": "SLATE Beta (Tester)",
                    "description": "Testing agent - validates, verifies, runs coverage analysis. GPU-accelerated.",
                    "prompt": (
                        "You are BETA, the SLATE testing agent. You run tests, validate code changes, "
                        "verify integrations, and analyze test coverage. Use slate_benchmark for performance "
                        "testing. Ensure all 7 integrations pass before approving changes."
                    ),
                    "tools": ["slate_system_status", "slate_runtime_check", "slate_benchmark",
                              "slate_security_audit"],
                },
                "GAMMA": {
                    "name": "slate-gamma",
                    "display_name": "SLATE Gamma (Planner)",
                    "description": "Planning agent - analyzes, plans, researches, documents. No GPU required.",
                    "prompt": (
                        "You are GAMMA, the SLATE planning agent. You analyze codebases, create plans, "
                        "research solutions, and produce documentation. Use slate_workflow to manage tasks "
                        "and slate_chromadb for semantic code search."
                    ),
                    "tools": ["slate_system_status", "slate_workflow", "slate_chromadb",
                              "slate_agent_registry"],
                },
                "DELTA": {
                    "name": "slate-delta",
                    "display_name": "SLATE Delta (Integrator)",
                    "description": "External bridge agent - manages SDK integrations, MCP, Claude. No GPU required.",
                    "prompt": (
                        "You are DELTA, the SLATE integration agent. You manage SDK integrations, "
                        "MCP server configurations, and external tool bridges. Ensure all connections "
                        "bind to 127.0.0.1 only. Validate SDK sources against the approved publisher list."
                    ),
                    "tools": ["slate_system_status", "slate_runtime_check", "slate_security_audit"],
                },
                "COPILOT": {
                    "name": "slate-copilot",
                    "display_name": "SLATE Copilot (Full Orchestration)",
                    "description": "Full orchestration agent with access to all SLATE tools and agents.",
                    "prompt": (
                        "You are the SLATE Copilot, a full-orchestration agent with access to all "
                        "SLATE subsystems. You can delegate tasks to specialized agents (ALPHA, BETA, "
                        "GAMMA, DELTA) or execute them directly. Follow SLATE security protocols: "
                        "local-only (127.0.0.1), ActionGuard validation, SDK Source Guard compliance."
                    ),
                    "tools": ["*"],  # All tools
                },
            }
        }

    def _get_default_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get default MCP tool definitions (hardcoded fallback)."""
        return [
            {
                "name": "slate_status",
                "description": "Check the status of all SLATE services and system components (GPU, services, workflows)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["quick", "json", "full"],
                            "description": "Output format: quick (human readable), json (machine readable), full (detailed)",
                            "default": "quick"
                        }
                    }
                }
            },
            {
                "name": "slate_workflow",
                "description": "Manage the SLATE task workflow queue - view status, cleanup stale tasks, enforce rules",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["status", "cleanup", "enforce"],
                            "description": "Action to perform: status (view queue), cleanup (fix stale tasks), enforce (check rules)",
                            "default": "status"
                        }
                    }
                }
            },
            {
                "name": "slate_orchestrator",
                "description": "Control the SLATE orchestrator - start, stop, or check status of all services",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start", "stop", "status"],
                            "description": "Action to perform on the orchestrator",
                            "default": "status"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "slate_runner",
                "description": "Manage the GitHub Actions self-hosted runner - check status, setup, or dispatch workflows",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["status", "setup", "dispatch"],
                            "description": "Action to perform on the runner",
                            "default": "status"
                        },
                        "workflow": {
                            "type": "string",
                            "description": "Workflow file to dispatch (only used with dispatch action)",
                            "default": "ci.yml"
                        }
                    }
                }
            },
            {
                "name": "slate_ai",
                "description": "Execute AI tasks using SLATE's unified backend (routes to free local LLMs)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The AI task to execute"
                        },
                        "check_status": {
                            "type": "boolean",
                            "description": "Check AI backend status instead of executing task",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "slate_runtime",
                "description": "Check all SLATE runtime integrations and dependencies (Python, GPU, PyTorch, Ollama, venv)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["text", "json"],
                            "description": "Output format",
                            "default": "text"
                        }
                    }
                }
            },
            {
                "name": "slate_hardware",
                "description": "Detect GPUs and optimize hardware configuration for PyTorch/CUDA",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["detect", "optimize", "install-pytorch"],
                            "description": "detect: show GPU info, optimize: apply settings, install-pytorch: install correct PyTorch for GPU arch",
                            "default": "detect"
                        }
                    }
                }
            },
            {
                "name": "slate_benchmark",
                "description": "Run SLATE performance benchmarks (GPU, inference, system throughput)",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "slate_gpu",
                "description": "Manage dual-GPU load balancing for Ollama LLMs (2x RTX 5070 Ti)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["status", "configure", "preload"],
                            "description": "status: show GPU/model placement, configure: set up dual-GPU env, preload: warm models on GPUs",
                            "default": "status"
                        }
                    }
                }
            },
            {
                "name": "slate_claude_code",
                "description": "Validate and manage Claude Code configuration for SLATE",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["validate", "report", "status", "agent-options"],
                            "description": "validate: run checks, report: full report, status: integration status, agent-options: show Agent SDK config",
                            "default": "status"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "json"],
                            "description": "Output format",
                            "default": "text"
                        }
                    }
                }
            },
            {
                "name": "slate_spec_kit",
                "description": "Process specifications, run AI analysis on sections, and generate wiki pages",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["status", "process-all", "wiki", "analyze"],
                            "description": "status: show spec-kit state, process-all: parse and process all specs, wiki: generate wiki pages, analyze: run AI analysis",
                            "default": "status"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "json"],
                            "description": "Output format",
                            "default": "text"
                        }
                    }
                }
            },
            {
                "name": "slate_schematic",
                "description": "Generate circuit-board style system diagrams and architecture visualizations using SLATE locked theme",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["from-system", "from-tech-tree", "components"],
                            "description": "from-system: current system state, from-tech-tree: tech tree diagram, components: list available",
                            "default": "from-system"
                        },
                        "output": {
                            "type": "string",
                            "description": "Output file path (default: docs/assets/slate-schematic.svg)"
                        },
                        "theme": {
                            "type": "string",
                            "enum": ["blueprint", "dark", "light"],
                            "description": "Diagram theme",
                            "default": "blueprint"
                        }
                    }
                }
            },
        ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════════════════════

    def load_instructions(self) -> InstructionSet:
        """Load all instructions from appropriate source."""
        return self._ensure_loaded()

    def get_agent_prompt(self, agent_name: str) -> str:
        """
        Get the system prompt for a specific agent.

        Args:
            agent_name: Agent name (ALPHA, BETA, GAMMA, DELTA, COPILOT)

        Returns:
            Agent system prompt string
        """
        instructions = self._ensure_loaded()
        agents = instructions.agent_prompts.get("agents", instructions.agent_prompts)
        agent = agents.get(agent_name.upper(), {})
        return agent.get("prompt", "")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get the full configuration for a specific agent.

        Args:
            agent_name: Agent name (ALPHA, BETA, GAMMA, DELTA, COPILOT)

        Returns:
            Agent configuration dict (CustomAgentConfig format)
        """
        instructions = self._ensure_loaded()
        agents = instructions.agent_prompts.get("agents", instructions.agent_prompts)
        return agents.get(agent_name.upper(), {})

    def get_agent_configs(self) -> List[Dict[str, Any]]:
        """
        Get all agent configurations as a list.

        Returns:
            List of agent configs (CustomAgentConfig format)
        """
        return self._ensure_loaded().agent_configs

    def get_copilot_instructions(self) -> str:
        """
        Get the full copilot instructions markdown.

        Returns:
            Copilot instructions content
        """
        return self._ensure_loaded().copilot_instructions

    def get_claude_md(self) -> str:
        """
        Get the full CLAUDE.md content.

        Returns:
            CLAUDE.md content
        """
        return self._ensure_loaded().claude_md

    def get_agents_md(self) -> str:
        """
        Get the full AGENTS.md content.

        Returns:
            AGENTS.md content
        """
        return self._ensure_loaded().agents_md

    def get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get MCP tool definitions.

        Returns:
            List of tool definition dicts with name, description, input_schema
        """
        return self._ensure_loaded().mcp_tools

    def get_source(self) -> str:
        """Get the source of loaded instructions (configmap/local/default)."""
        return self._ensure_loaded().source

    def get_version(self) -> str:
        """Get the content hash of loaded instructions."""
        return self._ensure_loaded().version

    def get_status(self) -> Dict[str, Any]:
        """Get full status of the instruction loader."""
        instructions = self._ensure_loaded()
        return {
            "is_k8s": self.is_k8s_environment(),
            "config_path": str(self.config_path),
            "local_fallback": str(self.local_fallback),
            "cache_ttl_seconds": self.cache_ttl,
            "watcher_active": self._watcher_thread is not None and self._watcher_thread.is_alive(),
            "instructions": instructions.to_dict(),
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # Hot-Reload Support
    # ═══════════════════════════════════════════════════════════════════════════════

    def watch_for_changes(
        self,
        callback: Callable[[], None],
        poll_interval: float = 5.0,
    ) -> None:
        """
        Start watching for instruction changes (hot-reload).

        Args:
            callback: Function to call when instructions change
            poll_interval: Seconds between change checks
        """
        self._reload_callbacks.append(callback)

        if self._watcher_thread is not None and self._watcher_thread.is_alive():
            return  # Already watching

        self._watcher_stop.clear()

        def _watch_loop():
            last_version = self.get_version()
            while not self._watcher_stop.is_set():
                time.sleep(poll_interval)
                try:
                    self.force_reload()
                    new_version = self.get_version()
                    if new_version != last_version:
                        logger.info(f"Instructions changed: {last_version[:8]} -> {new_version[:8]}")
                        last_version = new_version
                        for cb in self._reload_callbacks:
                            try:
                                cb()
                            except Exception as e:
                                logger.error(f"Reload callback error: {e}")
                except Exception as e:
                    logger.warning(f"Watch loop error: {e}")

        self._watcher_thread = threading.Thread(
            target=_watch_loop,
            name="instruction-watcher",
            daemon=True,
        )
        self._watcher_thread.start()
        logger.info(f"Started instruction watcher (poll interval: {poll_interval}s)")

    def stop_watching(self) -> None:
        """Stop the file watcher."""
        self._watcher_stop.set()
        if self._watcher_thread is not None:
            self._watcher_thread.join(timeout=2.0)
            self._watcher_thread = None
        self._reload_callbacks.clear()
        logger.info("Stopped instruction watcher")

    def force_reload(self) -> InstructionSet:
        """Force reload instructions from source, bypassing cache."""
        with self._lock:
            self._cache = self._load_instructions()
            self._cache_time = time.time()
            return self._cache


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_loader_instance: Optional[InstructionLoader] = None
_loader_lock = threading.Lock()


def get_instruction_loader(
    config_path: Optional[Path] = None,
    local_fallback: Optional[Path] = None,
    cache_ttl_seconds: int = 60,
) -> InstructionLoader:
    """
    Get the singleton instruction loader instance.

    Args:
        config_path: Override K8s ConfigMap mount path
        local_fallback: Override workspace root for local files
        cache_ttl_seconds: Cache TTL in seconds

    Returns:
        InstructionLoader singleton instance
    """
    global _loader_instance

    with _loader_lock:
        if _loader_instance is None:
            _loader_instance = InstructionLoader(
                config_path=config_path or K8S_CONFIG_PATH,
                local_fallback=local_fallback or WORKSPACE_ROOT,
                cache_ttl_seconds=cache_ttl_seconds,
            )
        return _loader_instance


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(description="SLATE Instruction Loader")
    parser.add_argument("--status", action="store_true", help="Show loader status")
    parser.add_argument("--agent", type=str, help="Get prompt for agent (ALPHA, BETA, etc.)")
    parser.add_argument("--tools", action="store_true", help="List MCP tool definitions")
    parser.add_argument("--configs", action="store_true", help="List agent configs")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    loader = get_instruction_loader()

    if args.status:
        status = loader.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("SLATE Instruction Loader Status")
            print("=" * 40)
            print(f"K8s Environment: {status['is_k8s']}")
            print(f"Config Path: {status['config_path']}")
            print(f"Source: {status['instructions']['source']}")
            print(f"Version: {status['instructions']['version']}")
            print(f"Agents: {status['instructions']['agent_count']}")
            print(f"MCP Tools: {status['instructions']['mcp_tools_count']}")
            print(f"Watcher: {'Active' if status['watcher_active'] else 'Inactive'}")

    elif args.agent:
        prompt = loader.get_agent_prompt(args.agent)
        if args.json:
            print(json.dumps({"agent": args.agent, "prompt": prompt}))
        else:
            print(f"Agent: {args.agent}")
            print("-" * 40)
            print(prompt)

    elif args.tools:
        tools = loader.get_mcp_tool_definitions()
        if args.json:
            print(json.dumps(tools, indent=2))
        else:
            print("MCP Tool Definitions")
            print("=" * 40)
            for tool in tools:
                print(f"- {tool['name']}: {tool['description'][:60]}...")

    elif args.configs:
        configs = loader.get_agent_configs()
        if args.json:
            print(json.dumps(configs, indent=2))
        else:
            print("Agent Configurations")
            print("=" * 40)
            for config in configs:
                print(f"- {config['name']}: {config.get('display_name', 'N/A')}")

    else:
        parser.print_help()
