#!/usr/bin/env python3
# Modified: 2026-02-08T22:00:00Z | Author: COPILOT | Change: Complete rewrite -- proper Copilot SDK integration with define_tool, SessionHooks, MCP bridge, custom agents, skills, infinite sessions
"""
SLATE Copilot SDK Integration
===============================
Connects SLATE to GitHub Copilot via the official Copilot SDK (github-copilot-sdk).

Architecture:
    +---------------------------------------------------------------+
    |  SLATE Tools (15x define_tool)                                |
    |       |                                                       |
    |  CopilotClient -- JSON-RPC --> Copilot CLI (Node.js) --> GitHub|
    |       |                                                       |
    |  ActionGuard (SessionHooks: PreToolUse, PostToolUse, etc.)     |
    |  MCP Server (slate/mcp_server.py via SessionConfig.mcp_servers)|
    |  Custom Agent ("SLATE" via SessionConfig.custom_agents)       |
    |  Skills (skills/ via SessionConfig.skill_directories)         |
    |  Infinite Sessions (persistent context)                       |
    +---------------------------------------------------------------+

Modes:
    python slate/slate_copilot_sdk.py                 # Start SLATE Copilot session (interactive)
    python slate/slate_copilot_sdk.py --status         # Plugin status (no Copilot CLI needed)
    python slate/slate_copilot_sdk.py --tool <name>    # Execute tool standalone
    python slate/slate_copilot_sdk.py --server          # Run as persistent agent server
    python slate/slate_copilot_sdk.py --verify          # Verify full SDK integration

Requirements:
    - github-copilot-sdk (pip)        -> CopilotClient, define_tool, SessionConfig
    - @github/copilot (npm -g)        -> Copilot CLI binary (Node.js server)
    - GitHub authentication           -> via git credential manager or GITHUB_TOKEN
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# --- Path Setup -------------------------------------------------------------

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

PYTHON = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"

VERSION = "2.4.0"

# --- Copilot SDK Imports ----------------------------------------------------

COPILOT_SDK_AVAILABLE = False
COPILOT_CLI_PATH: Optional[str] = None

try:
    from copilot import CopilotClient, CopilotSession, define_tool
    from copilot.types import (
        CustomAgentConfig,
        MCPLocalServerConfig,
        SessionConfig,
        SessionEvent,
        SessionHooks,
        Tool,
        ToolInvocation,
        ToolResult,
    )

    COPILOT_SDK_AVAILABLE = True
except ImportError:
    pass

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# --- Copilot CLI Detection --------------------------------------------------

def find_copilot_cli() -> Optional[str]:
    """
    Find the Copilot CLI binary. Search order:
      1. COPILOT_CLI_PATH env var
      2. npm global install (@github/copilot)
      3. VS Code extension bundled CLI
      4. vendor/copilot-sdk nodejs CLI
    Returns the path or None.
    """
    # 1. Environment variable
    env_path = os.environ.get("COPILOT_CLI_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 2. npm global install
    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            npm_root = result.stdout.strip()
            cli_index = Path(npm_root) / "@github" / "copilot" / "index.js"
            if cli_index.exists():
                return str(cli_index)
    except Exception:
        pass

    # 3. VS Code extension bundled CLI
    vscode_cli = Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "github.copilot-chat" / "copilotCli"
    for name in ["copilot.exe", "copilot"]:
        candidate = vscode_cli / name
        if candidate.exists():
            return str(candidate)

    # 4. vendor/copilot-sdk nodejs
    vendor_cli = WORKSPACE_ROOT / "vendor" / "copilot-sdk" / "nodejs" / "node_modules" / "@github" / "copilot" / "index.js"
    if vendor_cli.exists():
        return str(vendor_cli)

    return None


# Cache the CLI path at module load
COPILOT_CLI_PATH = find_copilot_cli()


# --- Command Runner ---------------------------------------------------------

def run_slate_command(module: str, *args: str, timeout: int = 60) -> dict[str, Any]:
    """Run a SLATE Python module and return structured result."""
    cmd = [str(PYTHON), f"slate/{module}"] + list(args)
    try:
        result = subprocess.run(
            cmd, cwd=str(WORKSPACE_ROOT),
            capture_output=True, text=True,
            timeout=timeout, encoding='utf-8'
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def fmt(result: dict[str, Any]) -> str:
    """Format command result to string."""
    if result["success"]:
        return result["stdout"] or "OK"
    return f"ERROR: {result['stderr']}" if result["stderr"] else "FAILED"


# --- Pydantic Parameter Models ---------------------------------------------
# These drive JSON schema generation for define_tool.

if PYDANTIC_AVAILABLE:
    class StatusParams(BaseModel):
        format: str = Field(default="quick", description="quick | json | full")

    class WorkflowParams(BaseModel):
        action: str = Field(default="status", description="status | cleanup | enforce")

    class OrchestratorParams(BaseModel):
        action: str = Field(default="status", description="start | stop | status")

    class RunnerParams(BaseModel):
        action: str = Field(default="status", description="status | detect | dispatch")
        workflow: str = Field(default="ci.yml", description="Workflow file for dispatch")

    class AIParams(BaseModel):
        task: str = Field(default="", description="AI task to execute")
        check_status: bool = Field(default=False, description="Check backend status instead")

    class RuntimeParams(BaseModel):
        format: str = Field(default="text", description="text | json")

    class HardwareParams(BaseModel):
        action: str = Field(default="detect", description="detect | optimize | install-pytorch")

    class BenchmarkParams(BaseModel):
        pass

    class GPUParams(BaseModel):
        action: str = Field(default="status", description="status | configure | preload")

    class ClaudeCodeParams(BaseModel):
        action: str = Field(default="status", description="validate | report | status | agent-options")
        format: str = Field(default="text", description="text | json")

    class SpecKitParams(BaseModel):
        action: str = Field(default="status", description="status | process-all | wiki | analyze")
        format: str = Field(default="text", description="text | json")

    class SchematicParams(BaseModel):
        action: str = Field(default="from-system", description="from-system | from-tech-tree | components")
        output: str = Field(default="docs/assets/slate-schematic.svg", description="Output file path")
        theme: str = Field(default="blueprint", description="blueprint | dark | light")

    class KubernetesParams(BaseModel):
        action: str = Field(default="status", description="status | deploy | health | teardown | logs | port-forward")
        component: str = Field(default="", description="Component name for logs")

    class AdaptiveInstructionsParams(BaseModel):
        action: str = Field(default="status", description="status | evaluate | sync | get-context | get-active | apply")

    class AutonomousParams(BaseModel):
        action: str = Field(default="status", description="status | discover | single | run")
        max_tasks: int = Field(default=10, description="Max tasks in run mode")


# ===========================================================================
# SLATE TOOLS -- Created via Copilot SDK define_tool()
# ===========================================================================
# Each tool is a proper Tool object that the Copilot CLI presents to the LLM.
# The LLM fills parameters (from Pydantic schema), Copilot SDK calls the handler.


def create_slate_tools() -> list:
    """
    Create all 15 SLATE tools using Copilot SDK define_tool().
    Returns list of Tool objects ready for SessionConfig.
    """
    if not COPILOT_SDK_AVAILABLE or not PYDANTIC_AVAILABLE:
        return []

    tools: list = []

    # 1. slate_status
    @define_tool(description="Check SLATE system health -- GPUs, services, workflows, Python env, K8s cluster, Ollama models")
    def slate_status(params: StatusParams) -> str:
        return fmt(run_slate_command("slate_status.py", f"--{params.format}"))
    tools.append(slate_status)

    # 2. slate_workflow
    @define_tool(description="Manage SLATE task queue -- view status, cleanup stale tasks, enforce completion rules before new work")
    def slate_workflow(params: WorkflowParams) -> str:
        return fmt(run_slate_command("slate_workflow_manager.py", f"--{params.action}"))
    tools.append(slate_workflow)

    # 3. slate_orchestrator
    @define_tool(description="Control SLATE services -- start/stop/status for dashboard, runner, monitor, autonomous loop")
    def slate_orchestrator(params: OrchestratorParams) -> str:
        return fmt(run_slate_command("slate_orchestrator.py", params.action))
    tools.append(slate_orchestrator)

    # 4. slate_runner
    @define_tool(description="Manage GitHub Actions self-hosted runner (slate-runner) -- status, detect, dispatch CI/CD workflows")
    def slate_runner(params: RunnerParams) -> str:
        if params.action == "dispatch":
            return fmt(run_slate_command("slate_runner_manager.py", "--dispatch", params.workflow))
        return fmt(run_slate_command("slate_runner_manager.py", f"--{params.action}"))
    tools.append(slate_runner)

    # 5. slate_ai
    @define_tool(description="Execute AI tasks using SLATE's local LLM backend (Ollama -- slate-coder 12B, slate-fast 3B, slate-planner 7B)")
    def slate_ai(params: AIParams) -> str:
        if params.check_status:
            return fmt(run_slate_command("ml_orchestrator.py", "--status"))
        if not params.task:
            return "ERROR: No task provided. Set task='your prompt' or check_status=true"
        return fmt(run_slate_command("ml_orchestrator.py", "--infer", params.task, timeout=120))
    tools.append(slate_ai)

    # 6. slate_runtime
    @define_tool(description="Verify all 7 SLATE runtime integrations: Python, GPU, PyTorch, Transformers, Ollama, ChromaDB, venv")
    def slate_runtime(params: RuntimeParams) -> str:
        args = ["--check-all"]
        if params.format == "json":
            args.append("--json")
        return fmt(run_slate_command("slate_runtime.py", *args))
    tools.append(slate_runtime)

    # 7. slate_hardware
    @define_tool(description="Detect GPUs (2x RTX 5070 Ti Blackwell), optimize CUDA settings, install correct PyTorch for compute 12.0")
    def slate_hardware(params: HardwareParams) -> str:
        if params.action == "optimize":
            return fmt(run_slate_command("slate_hardware_optimizer.py", "--optimize"))
        if params.action == "install-pytorch":
            return fmt(run_slate_command("slate_hardware_optimizer.py", "--install-pytorch", timeout=300))
        return fmt(run_slate_command("slate_hardware_optimizer.py"))
    tools.append(slate_hardware)

    # 8. slate_benchmark
    @define_tool(description="Run SLATE performance benchmarks -- GPU throughput, inference latency, system metrics")
    def slate_benchmark(params: BenchmarkParams) -> str:
        return fmt(run_slate_command("slate_benchmark.py", timeout=120))
    tools.append(slate_benchmark)

    # 9. slate_gpu
    @define_tool(description="Manage dual-GPU load balancing for Ollama LLMs -- model placement, VRAM monitoring, preload warmup")
    def slate_gpu(params: GPUParams) -> str:
        if params.action == "configure":
            return fmt(run_slate_command("slate_gpu_manager.py", "--configure"))
        if params.action == "preload":
            return fmt(run_slate_command("slate_gpu_manager.py", "--preload", timeout=120))
        return fmt(run_slate_command("slate_gpu_manager.py", "--status"))
    tools.append(slate_gpu)

    # 10. slate_claude_code
    @define_tool(description="Validate Claude Code configuration -- MCP server, permissions, ActionGuard hooks, behavior profile")
    def slate_claude_code(params: ClaudeCodeParams) -> str:
        args = [f"--{params.action}"]
        if params.format == "json":
            args.append("--json")
        return fmt(run_slate_command("claude_code_manager.py", *args))
    tools.append(slate_claude_code)

    # 11. slate_spec_kit
    @define_tool(description="Process specifications, run AI analysis, generate wiki pages from spec documents")
    def slate_spec_kit(params: SpecKitParams) -> str:
        action_map = {
            "status": ["--status"],
            "process-all": ["--process-all", "--wiki", "--analyze"],
            "wiki": ["--process-all", "--wiki"],
            "analyze": ["--process-all", "--analyze"],
        }
        args = action_map.get(params.action, ["--status"])
        if params.format == "json":
            args.append("--json")
        return fmt(run_slate_command("slate_spec_kit.py", *args, timeout=120))
    tools.append(slate_spec_kit)

    # 12. slate_schematic
    @define_tool(description="Generate SLATE system diagrams -- circuit-board style schematics of architecture")
    def slate_schematic(params: SchematicParams) -> str:
        if params.action == "components":
            return fmt(run_slate_command("schematic_sdk/cli.py", "components", "--list"))
        if params.action == "from-tech-tree":
            return fmt(run_slate_command("schematic_sdk/cli.py", "from-tech-tree", "--output", params.output, "--theme", params.theme))
        return fmt(run_slate_command("schematic_sdk/cli.py", "from-system", "--output", params.output, "--theme", params.theme))
    tools.append(slate_schematic)

    # 13. slate_kubernetes
    @define_tool(description="Manage SLATE Kubernetes cluster -- deploy manifests, health checks, teardown, pod logs, port-forwarding")
    def slate_kubernetes(params: KubernetesParams) -> str:
        action_map = {
            "deploy": ["--deploy"],
            "health": ["--health"],
            "teardown": ["--teardown"],
            "port-forward": ["--port-forward"],
            "logs": ["--logs", params.component] if params.component else ["--logs", "dashboard"],
        }
        args = action_map.get(params.action, ["--status"])
        return fmt(run_slate_command("slate_k8s_deploy.py", *args))
    tools.append(slate_kubernetes)

    # 14. slate_adaptive_instructions
    @define_tool(description="Manage K8s-driven adaptive instructions -- operating mode, agent availability, live directives")
    def slate_adaptive_instructions(params: AdaptiveInstructionsParams) -> str:
        flag_map = {
            "status": "--status", "evaluate": "--evaluate", "sync": "--sync",
            "get-context": "--get-context", "get-active": "--get-active", "apply": "--apply",
        }
        return fmt(run_slate_command("adaptive_instructions.py", flag_map.get(params.action, "--status")))
    tools.append(slate_adaptive_instructions)

    # 15. slate_autonomous
    @define_tool(description="Control the autonomous task loop -- discover tasks, execute one, run full loop with max limit")
    def slate_autonomous(params: AutonomousParams) -> str:
        if params.action == "discover":
            return fmt(run_slate_command("slate_unified_autonomous.py", "--discover"))
        if params.action == "single":
            return fmt(run_slate_command("slate_unified_autonomous.py", "--single", timeout=120))
        if params.action == "run":
            return fmt(run_slate_command("slate_unified_autonomous.py", "--run", "--max", str(params.max_tasks), timeout=300))
        return fmt(run_slate_command("slate_unified_autonomous.py", "--status"))
    tools.append(slate_autonomous)

    return tools


# Build tools once at module load (cheap -- no Copilot connection needed)
SLATE_TOOLS: list = create_slate_tools()
TOOL_NAMES: list[str] = [t.name for t in SLATE_TOOLS] if SLATE_TOOLS else []


# ===========================================================================
# ACTIONGUARD -- SessionHooks Implementation
# ===========================================================================
# Hooks use the exact signatures from copilot.types. Each returns None to allow
# or a dict to modify/deny.

BLOCKED_PATTERNS = [
    "rm -rf", "format c:", "del /s", "0.0.0.0",
    "eval(", "exec(os", "base64.b64decode",
]

SENSITIVE_TOOLS = {"slate_orchestrator", "slate_kubernetes", "slate_autonomous", "slate_hardware"}

PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "email"),
    (re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}"), "github_token"),
    (re.compile(r"sk-[A-Za-z0-9]{32,}"), "api_key"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "aws_key"),
]


def _guard_check_blocked(text: str) -> Optional[str]:
    """Check text against blocked patterns. Returns pattern name if blocked."""
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in lower:
            return pattern
    return None


def _guard_check_pii(text: str) -> Optional[str]:
    """Check text for PII. Returns PII type if found."""
    for regex, pii_type in PII_PATTERNS:
        if regex.search(text):
            return pii_type
    return None


def hook_pre_tool_use(hook_input: dict, env: dict) -> Optional[dict]:
    """PreToolUse hook -- ActionGuard validation before every tool call."""
    tool_name = hook_input.get("toolName", "")
    tool_args = hook_input.get("toolArgs", {})

    args_str = json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args)
    blocked = _guard_check_blocked(args_str)
    if blocked:
        return {
            "suppressOutput": True,
            "modifiedArgs": None,
            "additionalContext": f"[SLATE ActionGuard] BLOCKED: pattern '{blocked}' in {tool_name}",
        }

    if tool_name in SENSITIVE_TOOLS:
        action = tool_args.get("action", "") if isinstance(tool_args, dict) else ""
        if action in ("teardown", "stop", "run"):
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"[SLATE ActionGuard {ts}] Sensitive: {tool_name}.{action}", file=sys.stderr)

    return None


def hook_post_tool_use(hook_input: dict, env: dict) -> Optional[dict]:
    """PostToolUse hook -- audit log of every tool execution."""
    ts = datetime.now(timezone.utc).isoformat()
    tool_name = hook_input.get("toolName", "?")
    print(f"[SLATE Audit] {ts} | {tool_name}", file=sys.stderr)
    return None


def hook_user_prompt_submitted(hook_input: dict, env: dict) -> Optional[dict]:
    """UserPromptSubmitted hook -- scan prompts for PII and blocked patterns."""
    prompt = hook_input.get("prompt", "")

    pii = _guard_check_pii(prompt)
    if pii:
        return {
            "modifiedPrompt": "[REDACTED -- PII detected]",
            "additionalContext": f"[SLATE Security] PII type '{pii}' redacted from prompt",
        }

    blocked = _guard_check_blocked(prompt)
    if blocked:
        return {
            "additionalContext": f"[SLATE Security] Warning: blocked pattern '{blocked}' in prompt",
        }

    return None


def hook_session_start(hook_input: dict, env: dict) -> Optional[dict]:
    """SessionStart hook -- quick SLATE health check."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    source = hook_input.get("source", "new")
    print(f"[SLATE {ts}] Session started ({source})", file=sys.stderr)

    try:
        result = run_slate_command("slate_status.py", "--quick", timeout=10)
        if result["success"]:
            return {
                "additionalContext": f"SLATE System State:\n{result['stdout'][:500]}",
            }
    except Exception:
        pass
    return None


def hook_session_end(hook_input: dict, env: dict) -> Optional[dict]:
    """SessionEnd hook -- cleanup."""
    reason = hook_input.get("reason", "complete")
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[SLATE {ts}] Session ended ({reason})", file=sys.stderr)
    return None


def hook_error_occurred(hook_input: dict, env: dict) -> Optional[dict]:
    """ErrorOccurred hook -- log and optionally retry."""
    error = hook_input.get("error", "unknown")
    context = hook_input.get("errorContext", "system")
    recoverable = hook_input.get("recoverable", False)
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[SLATE Error] {ts} | {context} | {error}", file=sys.stderr)

    if recoverable and context == "tool_execution":
        return {"errorHandling": "retry", "retryCount": 1}
    return None


def create_session_hooks() -> dict:
    """Create SessionHooks dict with all SLATE ActionGuard handlers."""
    return {
        "on_pre_tool_use": hook_pre_tool_use,
        "on_post_tool_use": hook_post_tool_use,
        "on_user_prompt_submitted": hook_user_prompt_submitted,
        "on_session_start": hook_session_start,
        "on_session_end": hook_session_end,
        "on_error_occurred": hook_error_occurred,
    }


# ===========================================================================
# SYSTEM PROMPT AND CUSTOM AGENT
# ===========================================================================

SLATE_SYSTEM_PROMPT = """You are SLATE (Synchronized Living Architecture for Transformation and Evolution),
a local-first AI agent orchestration system.

## Hardware
- 2x NVIDIA GeForce RTX 5070 Ti (Blackwell, compute 12.0, 16GB VRAM each)
- Self-hosted GitHub Actions runner: slate-runner
- Python 3.11.9 in .venv

## Local LLMs (Ollama)
- slate-coder: 12B code generation (mistral-nemo, GPU 0, ~91 tok/s)
- slate-fast: 3B classification (llama3.2, GPU 1, ~308 tok/s)
- slate-planner: 7B planning (mistral, GPU 0, ~154 tok/s)

## Available Tools
{tool_list}

## Rules
- ALL operations LOCAL ONLY (127.0.0.1)
- Use the appropriate tool for every request
- Report results with pass/fail indicators
- For system health, always run slate_status first
- For deployments, check slate_kubernetes status before deploying
"""


def get_system_prompt() -> str:
    """Build the SLATE system prompt with tool list."""
    if SLATE_TOOLS:
        tool_list = "\n".join(f"- {t.name}: {t.description}" for t in SLATE_TOOLS)
    else:
        tool_list = "(tools unavailable -- Copilot SDK not installed)"
    return SLATE_SYSTEM_PROMPT.format(tool_list=tool_list)


def create_custom_agent() -> dict:
    """Create the SLATE custom agent config for SessionConfig."""
    return {
        "name": "slate",
        "display_name": "SLATE",
        "description": "SLATE system operator -- manages runner, CI/CD, GPU, services, K8s, autonomous loops",
        "prompt": get_system_prompt(),
        "tools": TOOL_NAMES or None,
    }


# ===========================================================================
# MCP SERVER CONFIG
# ===========================================================================

def create_mcp_config() -> dict[str, dict]:
    """Create MCP server config for SessionConfig.mcp_servers."""
    mcp_server_path = WORKSPACE_ROOT / "slate" / "mcp_server.py"
    if not mcp_server_path.exists():
        return {}

    return {
        "slate": {
            "type": "local",
            "command": str(PYTHON),
            "args": [str(mcp_server_path)],
            "cwd": str(WORKSPACE_ROOT),
            "tools": ["*"],
            "timeout": 60,
        }
    }


# ===========================================================================
# SESSION CONFIG BUILDER
# ===========================================================================

def create_session_config(
    model: str = "gpt-4.1",
    streaming: bool = True,
    infinite: bool = True,
) -> dict:
    """
    Build the full SessionConfig for a SLATE Copilot session.
    Wires together: tools + hooks + MCP + custom agent + skills + infinite sessions.
    """
    config: dict[str, Any] = {
        "model": model,
        "streaming": streaming,
        "working_directory": str(WORKSPACE_ROOT),
    }

    if SLATE_TOOLS:
        config["tools"] = SLATE_TOOLS

    config["hooks"] = create_session_hooks()

    mcp = create_mcp_config()
    if mcp:
        config["mcp_servers"] = mcp

    config["custom_agents"] = [create_custom_agent()]

    skills_dir = WORKSPACE_ROOT / "skills"
    if skills_dir.exists():
        config["skill_directories"] = [str(skills_dir)]

    config["system_message"] = {
        "mode": "append",
        "content": get_system_prompt(),
    }

    if infinite:
        config["infinite_sessions"] = {
            "enabled": True,
            "background_compaction_threshold": 0.80,
            "buffer_exhaustion_threshold": 0.95,
        }

    return config


# ===========================================================================
# SLATE COPILOT PLUGIN -- Main Class
# ===========================================================================

class SlateCopilotPlugin:
    """
    SLATE <-> Copilot SDK integration.

    Manages CopilotClient lifecycle, session creation with full SLATE config,
    and provides both interactive and server modes.
    """

    def __init__(self):
        self.client: Optional[Any] = None
        self.session: Optional[Any] = None
        self.cli_path: Optional[str] = COPILOT_CLI_PATH
        self._started = False

    async def start(self, github_token: Optional[str] = None) -> bool:
        """Start CopilotClient -- spawns Copilot CLI server."""
        if not COPILOT_SDK_AVAILABLE:
            print("[SLATE] Copilot SDK not installed. Run: pip install github-copilot-sdk", file=sys.stderr)
            return False

        if not self.cli_path:
            print("[SLATE] Copilot CLI not found. Run: npm install -g @github/copilot", file=sys.stderr)
            return False

        try:
            opts: dict[str, Any] = {
                "cli_path": self.cli_path,
                "cwd": str(WORKSPACE_ROOT),
                "log_level": "info",
            }
            if github_token:
                opts["github_token"] = github_token

            self.client = CopilotClient(opts)
            await self.client.start()
            self._started = True
            print(f"[SLATE] Copilot SDK connected (CLI: {self.cli_path})", file=sys.stderr)
            return True

        except Exception as e:
            print(f"[SLATE] Failed to start Copilot SDK: {e}", file=sys.stderr)
            return False

    async def create_session(self, model: str = "gpt-4.1") -> Optional[Any]:
        """Create a SLATE session with all tools, hooks, MCP, agent, skills."""
        if not self._started:
            ok = await self.start()
            if not ok:
                return None

        try:
            config = create_session_config(model=model)
            self.session = await self.client.create_session(config)
            print(f"[SLATE] Session created: {self.session.session_id}", file=sys.stderr)
            return self.session

        except Exception as e:
            print(f"[SLATE] Failed to create session: {e}", file=sys.stderr)
            return None

    async def send(self, prompt: str, timeout: float = 120.0) -> Optional[str]:
        """Send a message and wait for response."""
        if not self.session:
            session = await self.create_session()
            if not session:
                return None

        try:
            response = await self.session.send_and_wait(
                {"prompt": prompt},
                timeout=timeout,
            )
            if response and hasattr(response, 'data'):
                return getattr(response.data, 'content', str(response.data))
            return str(response) if response else None

        except asyncio.TimeoutError:
            return f"[SLATE] Timeout after {timeout}s waiting for response"
        except Exception as e:
            return f"[SLATE] Error: {e}"

    async def stop(self):
        """Stop the plugin -- destroy session and stop client."""
        try:
            if self.session:
                await self.session.destroy()
                self.session = None
            if self.client:
                await self.client.stop()
                self.client = None
            self._started = False
        except Exception as e:
            print(f"[SLATE] Stop error: {e}", file=sys.stderr)

    def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a SLATE tool directly (bypasses Copilot CLI)."""
        guard_result = hook_pre_tool_use(
            {"toolName": tool_name, "toolArgs": arguments, "timestamp": int(time.time()), "cwd": str(WORKSPACE_ROOT)},
            {},
        )
        if guard_result and guard_result.get("suppressOutput"):
            return f"BLOCKED: {guard_result.get('additionalContext', 'ActionGuard denied')}"

        for tool in SLATE_TOOLS:
            if tool.name == tool_name:
                try:
                    invocation = {"toolName": tool_name, "arguments": arguments}
                    result = asyncio.get_event_loop().run_until_complete(
                        tool.handler(invocation)
                    )
                    hook_post_tool_use(
                        {"toolName": tool_name, "toolArgs": arguments, "toolResult": result, "timestamp": int(time.time()), "cwd": str(WORKSPACE_ROOT)},
                        {},
                    )
                    if isinstance(result, dict):
                        return result.get("textResultForLlm", str(result))
                    return str(result)
                except Exception as e:
                    hook_error_occurred(
                        {"error": str(e), "errorContext": "tool_execution", "recoverable": False, "timestamp": int(time.time()), "cwd": str(WORKSPACE_ROOT)},
                        {},
                    )
                    return f"ERROR: {e}"

        return f"Unknown tool: {tool_name}. Available: {', '.join(TOOL_NAMES)}"

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive plugin status."""
        return {
            "copilot_sdk": {
                "installed": COPILOT_SDK_AVAILABLE,
                "version": "0.1.0" if COPILOT_SDK_AVAILABLE else None,
            },
            "copilot_cli": {
                "found": COPILOT_CLI_PATH is not None,
                "path": COPILOT_CLI_PATH,
            },
            "pydantic": {
                "installed": PYDANTIC_AVAILABLE,
            },
            "client": {
                "started": self._started,
                "session_active": self.session is not None,
            },
            "tools": {
                "count": len(SLATE_TOOLS),
                "names": TOOL_NAMES,
            },
            "hooks": {
                "pre_tool_use": "ActionGuard -- blocks dangerous patterns",
                "post_tool_use": "Audit log -- timestamps every tool call",
                "user_prompt_submitted": "PII scanner -- redacts tokens/emails/keys",
                "session_start": "Health check -- injects system state",
                "session_end": "Cleanup -- logs session reason",
                "error_occurred": "Recovery -- retries recoverable tool errors",
            },
            "mcp_server": {
                "configured": bool(create_mcp_config()),
                "command": f"{PYTHON} slate/mcp_server.py",
                "transport": "stdio",
            },
            "custom_agent": {
                "name": "slate",
                "display_name": "SLATE",
                "tools": TOOL_NAMES,
            },
            "skills": {
                "directory": str(WORKSPACE_ROOT / "skills"),
                "available": [d.name for d in (WORKSPACE_ROOT / "skills").iterdir() if d.is_dir()] if (WORKSPACE_ROOT / "skills").exists() else [],
            },
            "infinite_sessions": True,
            "workspace": str(WORKSPACE_ROOT),
        }


# ===========================================================================
# CLI INTERFACE
# ===========================================================================

def print_status(as_json: bool = False):
    """Print SLATE Copilot SDK status."""
    plugin = SlateCopilotPlugin()
    status = plugin.get_status()

    if as_json:
        print(json.dumps(status, indent=2))
        return

    sdk = status["copilot_sdk"]
    cli = status["copilot_cli"]
    tools = status["tools"]

    print("=" * 65)
    print("  SLATE Copilot SDK Integration")
    print("=" * 65)
    print()

    sdk_ok = "YES" if sdk["installed"] else "NO -- pip install github-copilot-sdk"
    cli_ok = "YES" if cli["found"] else "NO -- npm install -g @github/copilot"
    print(f"  Copilot SDK (pip):    {sdk_ok}")
    print(f"  Copilot CLI (npm):    {cli_ok}")
    if cli["path"]:
        print(f"  CLI Path:             {cli['path']}")
    print(f"  Pydantic:             {'YES' if status['pydantic']['installed'] else 'NO'}")
    print()

    print(f"  Tools ({tools['count']}):")
    for tool in SLATE_TOOLS:
        desc = tool.description[:55] if hasattr(tool, 'description') else ""
        print(f"    {tool.name:35s} {desc}")
    print()

    print("  Hooks (ActionGuard -> SessionHooks):")
    for hook_name, hook_desc in status["hooks"].items():
        print(f"    {hook_name:30s} {hook_desc}")
    print()

    mcp = status["mcp_server"]
    print(f"  MCP Server:           {'Configured' if mcp['configured'] else 'Not found'} ({mcp['transport']})")
    print(f"  Custom Agent:         {status['custom_agent']['display_name']} ({len(status['custom_agent']['tools'])} tools)")
    print(f"  Skills:               {', '.join(status['skills']['available']) or 'none'}")
    print(f"  Infinite Sessions:    {'Enabled' if status['infinite_sessions'] else 'Disabled'}")
    print(f"  Workspace:            {status['workspace']}")
    print()

    ready = sdk["installed"] and cli["found"] and tools["count"] > 0
    if ready:
        print("  STATUS: READY -- run `python slate/slate_copilot_sdk.py --server` to start")
    else:
        missing = []
        if not sdk["installed"]:
            missing.append("pip install github-copilot-sdk")
        if not cli["found"]:
            missing.append("npm install -g @github/copilot")
        if tools["count"] == 0:
            missing.append("pydantic required for tools")
        print(f"  STATUS: NOT READY -- install: {'; '.join(missing)}")

    print("=" * 65)


def verify_integration():
    """Run full integration verification."""
    print("SLATE Copilot SDK -- Integration Verification")
    print("=" * 50)

    checks = []

    print("\n1. Copilot SDK import...")
    if COPILOT_SDK_AVAILABLE:
        print("   PASS: CopilotClient, define_tool, SessionConfig available")
        checks.append(True)
    else:
        print("   FAIL: github-copilot-sdk not installed")
        checks.append(False)

    print("\n2. Copilot CLI binary...")
    if COPILOT_CLI_PATH:
        print(f"   PASS: {COPILOT_CLI_PATH}")
        checks.append(True)
    else:
        print("   FAIL: Copilot CLI not found")
        checks.append(False)

    print(f"\n3. SLATE tools ({len(SLATE_TOOLS)})...")
    if len(SLATE_TOOLS) >= 15:
        print(f"   PASS: {len(SLATE_TOOLS)} tools registered via define_tool()")
        checks.append(True)
    elif SLATE_TOOLS:
        print(f"   WARN: Only {len(SLATE_TOOLS)} tools (expected 15)")
        checks.append(True)
    else:
        print("   FAIL: No tools created (need pydantic + copilot SDK)")
        checks.append(False)

    print("\n4. Tool execution (slate_status)...")
    if SLATE_TOOLS:
        plugin = SlateCopilotPlugin()
        result = plugin.execute_tool("slate_status", {"format": "quick"})
        if "ERROR" not in result and "BLOCKED" not in result:
            print(f"   PASS: {result[:80]}...")
            checks.append(True)
        else:
            print(f"   FAIL: {result[:80]}")
            checks.append(False)
    else:
        print("   SKIP: No tools available")
        checks.append(False)

    print("\n5. ActionGuard hooks...")
    test_blocked = hook_pre_tool_use(
        {"toolName": "test", "toolArgs": {"cmd": "rm -rf /"}, "timestamp": 0, "cwd": "."},
        {},
    )
    test_allowed = hook_pre_tool_use(
        {"toolName": "slate_status", "toolArgs": {"format": "quick"}, "timestamp": 0, "cwd": "."},
        {},
    )
    if test_blocked and test_blocked.get("suppressOutput") and test_allowed is None:
        print("   PASS: Blocks 'rm -rf', allows 'slate_status'")
        checks.append(True)
    else:
        print("   FAIL: ActionGuard not working correctly")
        checks.append(False)

    print("\n6. PII scanner...")
    test_pii = hook_user_prompt_submitted(
        {"prompt": "my token is ghp_abc123456789012345678901234567890123", "timestamp": 0, "cwd": "."},
        {},
    )
    test_clean = hook_user_prompt_submitted(
        {"prompt": "check system status", "timestamp": 0, "cwd": "."},
        {},
    )
    if test_pii and "modifiedPrompt" in test_pii and test_clean is None:
        print("   PASS: Redacts GitHub tokens, passes clean prompts")
        checks.append(True)
    else:
        print("   FAIL: PII scanner not working")
        checks.append(False)

    print("\n7. MCP server config...")
    mcp = create_mcp_config()
    if mcp and "slate" in mcp:
        print("   PASS: slate MCP server via stdio")
        checks.append(True)
    else:
        print("   FAIL: MCP server config missing")
        checks.append(False)

    print("\n8. Custom agent config...")
    agent = create_custom_agent()
    if agent["name"] == "slate" and agent.get("tools"):
        print(f"   PASS: SLATE agent with {len(agent['tools'])} tools")
        checks.append(True)
    else:
        print("   FAIL: Agent config incomplete")
        checks.append(False)

    print("\n9. Skills directory...")
    skills_dir = WORKSPACE_ROOT / "skills"
    if skills_dir.exists():
        skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
        print(f"   PASS: {skill_count} skills in {skills_dir}")
        checks.append(True)
    else:
        print("   FAIL: skills/ directory not found")
        checks.append(False)

    print("\n10. SessionConfig builder...")
    try:
        config = create_session_config()
        has_tools = "tools" in config
        has_hooks = "hooks" in config
        has_mcp = "mcp_servers" in config
        has_agent = "custom_agents" in config
        has_skills = "skill_directories" in config
        has_infinite = "infinite_sessions" in config
        has_system = "system_message" in config

        features = [has_tools, has_hooks, has_mcp, has_agent, has_skills, has_infinite, has_system]
        feature_names = ["tools", "hooks", "mcp_servers", "custom_agents", "skill_directories", "infinite_sessions", "system_message"]
        present = [n for n, v in zip(feature_names, features) if v]
        missing = [n for n, v in zip(feature_names, features) if not v]

        if len(present) >= 5:
            print(f"   PASS: {len(present)}/7 features: {', '.join(present)}")
            if missing:
                print(f"         Missing: {', '.join(missing)}")
            checks.append(True)
        else:
            print(f"   FAIL: Only {len(present)}/7 features configured")
            checks.append(False)
    except Exception as e:
        print(f"   FAIL: {e}")
        checks.append(False)

    passed = sum(checks)
    total = len(checks)
    print(f"\n{'=' * 50}")
    print(f"  Result: {passed}/{total} checks passed")
    if passed == total:
        print("  STATUS: ALL CHECKS PASSED")
    else:
        print(f"  STATUS: {total - passed} FAILURES")
    print(f"{'=' * 50}")

    return passed == total


async def run_interactive():
    """Run an interactive SLATE Copilot session."""
    plugin = SlateCopilotPlugin()

    print("[SLATE] Starting Copilot SDK session...")
    ok = await plugin.start()
    if not ok:
        print("[SLATE] Cannot start -- falling back to standalone tool mode")
        print("[SLATE] Use: --tool <name> --args '{...}' for direct tool execution")
        return

    session = await plugin.create_session()
    if not session:
        print("[SLATE] Failed to create session")
        await plugin.stop()
        return

    print("[SLATE] Session ready. Type 'quit' to exit.")
    print()

    try:
        while True:
            try:
                prompt = input("SLATE> ")
            except (EOFError, KeyboardInterrupt):
                break

            if prompt.strip().lower() in ("quit", "exit", "q"):
                break
            if not prompt.strip():
                continue

            response = await plugin.send(prompt)
            if response:
                print(response)
            print()
    finally:
        await plugin.stop()
        print("[SLATE] Session ended.")


async def run_server():
    """Run SLATE as a persistent Copilot agent server."""
    plugin = SlateCopilotPlugin()

    print("[SLATE] Starting Copilot SDK agent server...")
    ok = await plugin.start()
    if not ok:
        print("[SLATE] Cannot start agent server")
        return

    session = await plugin.create_session()
    if not session:
        print("[SLATE] Failed to create session")
        await plugin.stop()
        return

    print(f"[SLATE] Agent server running -- session: {session.session_id}")
    print("[SLATE] Listening for tool calls via Copilot CLI...")
    print("[SLATE] Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await plugin.stop()
        print("[SLATE] Agent server stopped.")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SLATE Copilot SDK Integration -- connects SLATE to GitHub Copilot"
    )
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--json", action="store_true", help="JSON output for --status")
    parser.add_argument("--verify", action="store_true", help="Run full integration verification")
    parser.add_argument("--server", action="store_true", help="Run as persistent agent server")
    parser.add_argument("--tool", type=str, help="Execute a SLATE tool by name")
    parser.add_argument("--args", type=str, default="{}", help="JSON arguments for --tool")
    parser.add_argument("--list-tools", action="store_true", help="List all tools")

    args = parser.parse_args()

    if args.status:
        print_status(as_json=args.json)
        return

    if args.verify:
        success = verify_integration()
        sys.exit(0 if success else 1)

    if args.list_tools:
        if SLATE_TOOLS:
            for tool in SLATE_TOOLS:
                print(f"{tool.name}: {tool.description}")
        else:
            print("No tools available (install github-copilot-sdk + pydantic)")
        return

    if args.tool:
        plugin = SlateCopilotPlugin()
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {args.args}", file=sys.stderr)
            sys.exit(1)
        result = plugin.execute_tool(args.tool, tool_args)
        print(result)
        return

    if args.server:
        asyncio.run(run_server())
        return

    asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
