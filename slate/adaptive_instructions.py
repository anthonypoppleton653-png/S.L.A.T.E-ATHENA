#!/usr/bin/env python3
# Modified: 2026-02-09T06:00:00Z | Author: COPILOT | Change: Create adaptive instruction layer — K8s-driven dynamic instruction controller
"""
SLATE Adaptive Instruction Layer
==================================

Transforms static instruction files (AGENTS.md, copilot-instructions.md) into a
dynamic, K8s-driven adaptive instruction system. The instruction controller watches
cluster state and generates context-aware instruction overrides.

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    ADAPTIVE INSTRUCTION LAYER                          │
    │                                                                         │
    │  K8s ConfigMap ◄─── Instruction Controller ◄─── System State Watcher   │
    │  (slate-instructions)  (this module)             (GPU, K8s, workflows) │
    │       │                     ▲                                           │
    │       │                     │                                           │
    │       ▼                     │                                           │
    │  @slate extension      GitHub Workflows                                │
    │  (queries live          (trigger mutations                              │
    │   instructions)          on events)                                     │
    └─────────────────────────────────────────────────────────────────────────┘

Usage:
    # CLI
    python slate/adaptive_instructions.py --status       # Show instruction state
    python slate/adaptive_instructions.py --evaluate     # Evaluate system & generate instructions
    python slate/adaptive_instructions.py --apply        # Apply to K8s ConfigMap
    python slate/adaptive_instructions.py --get-context  # Get context-aware instruction block
    python slate/adaptive_instructions.py --sync         # Full sync: evaluate + apply + notify
    python slate/adaptive_instructions.py --json         # JSON output

    # Python API
    from slate.adaptive_instructions import AdaptiveInstructionController
    controller = AdaptiveInstructionController()
    context = controller.evaluate_system_state()
    instructions = controller.generate_instructions(context)
    controller.apply_to_configmap(instructions)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "AdaptiveInstructionController",
    "InstructionContext",
    "SystemState",
    "InstructionMode",
]

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE = Path(os.environ.get("SLATE_WORKSPACE", Path(__file__).parent.parent))
CONFIGMAP_NAME = "slate-instructions"
CONFIGMAP_NAMESPACE = "slate"
INSTRUCTION_CONTROLLER_NAME = "slate-instruction-controller"
STATE_FILE = WORKSPACE / ".slate_instruction_state.json"
CONTEXT_FILE = WORKSPACE / ".slate_instruction_context.json"


class InstructionMode(Enum):
    """Operating modes that determine instruction behavior."""
    NORMAL = "normal"           # Standard operations — all systems healthy
    DEGRADED = "degraded"       # Some services down — adjust instructions accordingly
    MAINTENANCE = "maintenance" # Maintenance mode — limit operations to health/repair
    AUTONOMOUS = "autonomous"   # Autonomous loop active — instructions optimized for AI agents
    EMERGENCY = "emergency"     # Critical failure — instructions focus on recovery
    DEVELOPMENT = "development" # Active dev mode — instructions prioritize coding/testing


class AgentAvailability(Enum):
    """Agent availability states based on system health."""
    FULL = "full"           # All agents available with GPU
    GPU_ONLY = "gpu-only"   # Only GPU agents available (services down)
    CPU_ONLY = "cpu-only"   # No GPU access — planning/integration agents only
    MINIMAL = "minimal"     # Minimal operations — status/health only


@dataclass
class SystemState:
    """Captured system state for instruction decisions."""
    # Infrastructure
    k8s_available: bool = False
    k8s_pods_total: int = 0
    k8s_pods_ready: int = 0
    k8s_deployments: int = 0
    k8s_deployments_ready: int = 0

    # GPU & Hardware
    gpu_count: int = 0
    gpu_available: bool = False
    gpu_memory_total_gb: float = 0.0
    gpu_memory_used_gb: float = 0.0
    cuda_version: str = ""

    # Services
    ollama_available: bool = False
    chromadb_available: bool = False
    dashboard_available: bool = False
    runner_online: bool = False

    # Workflows
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    stale_tasks: int = 0

    # Models
    models_loaded: List[str] = field(default_factory=list)

    # Metadata
    python_version: str = ""
    slate_version: str = "2.4.0"
    timestamp: str = ""

    @property
    def overall_health(self) -> str:
        """Calculate overall system health."""
        if not self.k8s_available:
            return "critical"
        required_ready = self.k8s_deployments_ready >= self.k8s_deployments * 0.7
        if self.gpu_available and self.ollama_available and required_ready:
            return "healthy"
        if self.gpu_available or required_ready:
            return "degraded"
        return "critical"


@dataclass
class InstructionContext:
    """Generated instruction context from system state analysis."""
    mode: InstructionMode = InstructionMode.NORMAL
    agent_availability: AgentAvailability = AgentAvailability.FULL
    system_state: Optional[SystemState] = None

    # Instruction overrides
    active_protocols: List[str] = field(default_factory=list)
    disabled_protocols: List[str] = field(default_factory=list)
    active_tools: List[str] = field(default_factory=list)
    disabled_tools: List[str] = field(default_factory=list)
    agent_routing_overrides: Dict[str, str] = field(default_factory=dict)

    # Behavioral directives
    priority_directives: List[str] = field(default_factory=list)
    caution_directives: List[str] = field(default_factory=list)
    enforcement_rules: List[str] = field(default_factory=list)

    # K8s-specific
    k8s_instructions: Dict[str, str] = field(default_factory=dict)
    configmap_version: str = ""

    timestamp: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Adaptive Instruction Controller
# ─────────────────────────────────────────────────────────────────────────────

class AdaptiveInstructionController:
    """
    Core controller that watches system state and generates adaptive instructions.

    The controller:
    1. Collects system state from K8s, GPU, services, workflows
    2. Evaluates the state to determine instruction mode
    3. Generates context-aware instruction overrides
    4. Applies instructions to the K8s ConfigMap
    5. Exposes the active instruction set for @slate and Copilot to consume
    """

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or WORKSPACE
        self.python_exe = self.workspace / ".venv" / "Scripts" / "python.exe"
        if not self.python_exe.exists():
            # Linux/macOS fallback
            self.python_exe = self.workspace / ".venv" / "bin" / "python"
        self._last_state: Optional[SystemState] = None
        self._last_context: Optional[InstructionContext] = None

    # ─── System State Collection ─────────────────────────────────────────

    def collect_system_state(self) -> SystemState:
        """Collect current system state from all SLATE subsystems."""
        state = SystemState(timestamp=datetime.now(timezone.utc).isoformat())

        # K8s state
        self._collect_k8s_state(state)

        # GPU state
        self._collect_gpu_state(state)

        # Service state
        self._collect_service_state(state)

        # Workflow state
        self._collect_workflow_state(state)

        # Python/SLATE version
        state.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        self._last_state = state
        return state

    def _collect_k8s_state(self, state: SystemState) -> None:
        """Collect Kubernetes cluster state."""
        try:
            # Check if kubectl is available
            result = subprocess.run(
                ["kubectl", "get", "deployments", "-n", "slate", "-o", "json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                state.k8s_available = True
                data = json.loads(result.stdout)
                items = data.get("items", [])
                state.k8s_deployments = len(items)
                state.k8s_deployments_ready = sum(
                    1 for d in items
                    if d.get("status", {}).get("readyReplicas", 0) > 0
                )

            # Pod count
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "slate", "-o", "json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                pods = data.get("items", [])
                state.k8s_pods_total = len(pods)
                state.k8s_pods_ready = sum(
                    1 for p in pods
                    if p.get("status", {}).get("phase") == "Running"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            state.k8s_available = False

    def _collect_gpu_state(self, state: SystemState) -> None:
        """Collect GPU state via nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=count,memory.total,memory.used,driver_version",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                state.gpu_count = len(lines)
                state.gpu_available = True
                total_mem = 0.0
                used_mem = 0.0
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        total_mem += float(parts[1]) / 1024  # MB to GB
                        used_mem += float(parts[2]) / 1024
                state.gpu_memory_total_gb = round(total_mem, 1)
                state.gpu_memory_used_gb = round(used_mem, 1)
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            state.gpu_available = False

        # CUDA version
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                state.cuda_version = result.stdout.strip().split("\n")[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _collect_service_state(self, state: SystemState) -> None:
        """Collect service availability state."""
        import urllib.request
        import urllib.error

        services = {
            "ollama": ("http://127.0.0.1:11434/api/tags", "ollama_available"),
            "dashboard": ("http://127.0.0.1:8080/health", "dashboard_available"),
        }

        for name, (url, attr) in services.items():
            try:
                req = urllib.request.Request(url, method="GET")
                req.add_header("User-Agent", "SLATE-AdaptiveInstructions/1.0")
                urllib.request.urlopen(req, timeout=3)
                setattr(state, attr, True)
            except Exception:
                setattr(state, attr, False)

        # ChromaDB — check via import
        try:
            result = subprocess.run(
                [str(self.python_exe), "-c",
                 "import chromadb; c = chromadb.Client(); print('ok')"],
                capture_output=True, text=True, timeout=10
            )
            state.chromadb_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            state.chromadb_available = False

        # Runner — check via process
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process -Name Runner.Listener -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { 'running' }"],
                capture_output=True, text=True, timeout=5
            )
            state.runner_online = "running" in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            state.runner_online = False

        # Ollama models
        if state.ollama_available:
            try:
                req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
                req.add_header("User-Agent", "SLATE-AdaptiveInstructions/1.0")
                resp = urllib.request.urlopen(req, timeout=5)
                data = json.loads(resp.read().decode())
                state.models_loaded = [m.get("name", "") for m in data.get("models", [])]
            except Exception:
                pass

    def _collect_workflow_state(self, state: SystemState) -> None:
        """Collect workflow/task state."""
        try:
            result = subprocess.run(
                [str(self.python_exe), str(self.workspace / "slate" / "slate_workflow_manager.py"),
                 "--status", "--json"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.workspace)
            )
            if result.returncode == 0:
                # Try to extract JSON from output
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            data = json.loads(line)
                            state.pending_tasks = data.get("pending", 0)
                            state.in_progress_tasks = data.get("in_progress", 0)
                            state.completed_tasks = data.get("completed", 0)
                            state.stale_tasks = data.get("stale", 0)
                            break
                        except json.JSONDecodeError:
                            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # ─── Instruction Evaluation ──────────────────────────────────────────

    def evaluate_system_state(self, state: Optional[SystemState] = None) -> InstructionContext:
        """
        Evaluate system state and generate an instruction context.

        This is the core intelligence of the adaptive layer. It analyzes
        the current system state and determines:
        - Which operating mode to use
        - Which agents are available
        - What protocols to activate/disable
        - Priority directives for Copilot sessions
        """
        if state is None:
            state = self.collect_system_state()

        ctx = InstructionContext(
            system_state=state,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # ── Determine operating mode ────────────────────────────────────
        health = state.overall_health
        if health == "critical":
            if not state.k8s_available:
                ctx.mode = InstructionMode.EMERGENCY
            else:
                ctx.mode = InstructionMode.MAINTENANCE
        elif health == "degraded":
            ctx.mode = InstructionMode.DEGRADED
        elif state.in_progress_tasks > 0:
            ctx.mode = InstructionMode.AUTONOMOUS
        else:
            ctx.mode = InstructionMode.NORMAL

        # ── Determine agent availability ────────────────────────────────
        if state.gpu_available and state.ollama_available:
            ctx.agent_availability = AgentAvailability.FULL
        elif state.gpu_available:
            ctx.agent_availability = AgentAvailability.GPU_ONLY
        elif state.k8s_available:
            ctx.agent_availability = AgentAvailability.CPU_ONLY
        else:
            ctx.agent_availability = AgentAvailability.MINIMAL

        # ── Generate protocol decisions ─────────────────────────────────
        self._generate_protocol_decisions(ctx, state)

        # ── Generate tool availability ──────────────────────────────────
        self._generate_tool_availability(ctx, state)

        # ── Generate behavioral directives ──────────────────────────────
        self._generate_directives(ctx, state)

        # ── Generate agent routing overrides ────────────────────────────
        self._generate_routing_overrides(ctx, state)

        # ── Generate K8s-specific instructions ──────────────────────────
        self._generate_k8s_instructions(ctx, state)

        self._last_context = ctx
        return ctx

    def _generate_protocol_decisions(self, ctx: InstructionContext, state: SystemState) -> None:
        """Decide which protocols to activate or disable."""
        # Always active
        ctx.active_protocols = [
            "session_start",       # Health check at start
            "code_edit_rules",     # Timestamp + author comments
            "security_enforcement", # ActionGuard, PII, SDK source
            "document_evolution",  # Append-only rules
        ]

        if state.k8s_available:
            ctx.active_protocols.append("k8s_health_gate")  # Gate operations on K8s health
            ctx.active_protocols.append("k8s_instruction_sync")  # Sync instructions from ConfigMap

        if state.runner_online:
            ctx.active_protocols.append("ci_cd_dispatch")  # Allow workflow dispatch

        if state.ollama_available:
            ctx.active_protocols.append("local_ai_inference")  # Enable local LLM ops

        # Disabled protocols
        if not state.ollama_available:
            ctx.disabled_protocols.append("local_ai_inference")
        if not state.runner_online:
            ctx.disabled_protocols.append("ci_cd_dispatch")
        if not state.chromadb_available:
            ctx.disabled_protocols.append("semantic_search")
        if ctx.mode == InstructionMode.EMERGENCY:
            ctx.disabled_protocols.extend(["autonomous_loop", "task_creation"])

    def _generate_tool_availability(self, ctx: InstructionContext, state: SystemState) -> None:
        """Determine which @slate tools are available."""
        # Always available
        ctx.active_tools = [
            "slate_systemStatus",
            "slate_runtimeCheck",
            "slate_hardwareInfo",
            "slate_workflow",
            "slate_securityAudit",
            "slate_runCommand",
            "slate_adaptiveInstructions",
        ]

        if state.k8s_available:
            ctx.active_tools.append("slate_kubernetes")

        if state.runner_online:
            ctx.active_tools.extend(["slate_runnerStatus", "slate_runProtocol"])

        if state.ollama_available:
            ctx.active_tools.extend([
                "slate_gpuManager",
                "slate_autonomous",
                "slate_agentBridge",
            ])

        if state.dashboard_available:
            ctx.active_tools.extend(["slate_orchestrator", "slate_startServices"])

        if state.gpu_available:
            ctx.active_tools.append("slate_benchmark")

        # Disabled tools
        all_tools = {
            "slate_systemStatus", "slate_runtimeCheck", "slate_hardwareInfo",
            "slate_runnerStatus", "slate_orchestrator", "slate_workflow",
            "slate_benchmark", "slate_runCommand", "slate_securityAudit",
            "slate_gpuManager", "slate_autonomous", "slate_agentBridge",
            "slate_kubernetes", "slate_adaptiveInstructions", "slate_runProtocol",
            "slate_startServices", "slate_executeWork", "slate_handoff",
            "slate_specKit", "slate_devCycle", "slate_codeGuidance",
            "slate_learningProgress", "slate_planContext", "slate_semanticKernel",
            "slate_githubModels", "slate_forkCheck",
        }
        ctx.disabled_tools = list(all_tools - set(ctx.active_tools))

    def _generate_directives(self, ctx: InstructionContext, state: SystemState) -> None:
        """Generate behavioral directives based on system state."""
        # Priority directives — what to focus on
        if ctx.mode == InstructionMode.EMERGENCY:
            ctx.priority_directives = [
                "CRITICAL: K8s cluster is unreachable. Focus on cluster recovery.",
                "Run 'kubectl cluster-info' to diagnose the issue.",
                "Check Docker Desktop and Kubernetes are running.",
                "Do NOT create new tasks until cluster is restored.",
            ]
        elif ctx.mode == InstructionMode.MAINTENANCE:
            ctx.priority_directives = [
                "System is in maintenance mode. Limited operations available.",
                f"K8s: {state.k8s_pods_ready}/{state.k8s_pods_total} pods ready.",
                "Focus on restoring unhealthy services before new work.",
            ]
        elif ctx.mode == InstructionMode.DEGRADED:
            degraded_services = []
            if not state.ollama_available:
                degraded_services.append("Ollama")
            if not state.dashboard_available:
                degraded_services.append("Dashboard")
            if not state.runner_online:
                degraded_services.append("Runner")
            ctx.priority_directives = [
                f"System degraded: {', '.join(degraded_services)} unavailable.",
                "Non-GPU tasks can proceed. GPU-dependent operations may fail.",
                "Consider running 'slate/slate_orchestrator.py start' to restore services.",
            ]
        elif ctx.mode == InstructionMode.AUTONOMOUS:
            ctx.priority_directives = [
                f"Autonomous loop active: {state.in_progress_tasks} tasks in progress.",
                "Coordinate with the autonomous loop — check bridge for pending tasks.",
                "Use slate_agentBridge tool to poll/complete tasks.",
            ]
        else:
            ctx.priority_directives = [
                f"All systems nominal. K8s: {state.k8s_deployments_ready}/{state.k8s_deployments} deployments ready.",
                f"GPU: {state.gpu_count}x available ({state.gpu_memory_used_gb:.1f}/{state.gpu_memory_total_gb:.1f} GB used).",
            ]
            if state.pending_tasks > 0:
                ctx.priority_directives.append(
                    f"{state.pending_tasks} pending tasks in queue — consider processing before new work."
                )
            if state.stale_tasks > 0:
                ctx.priority_directives.append(
                    f"WARNING: {state.stale_tasks} stale tasks detected. Run workflow cleanup."
                )

        # Caution directives — what to watch out for
        ctx.caution_directives = [
            "ALL network bindings: 127.0.0.1 ONLY — never 0.0.0.0",
            "Blocked patterns: eval(, exec(os, rm -rf /, base64.b64decode",
        ]
        if state.gpu_memory_used_gb > state.gpu_memory_total_gb * 0.8:
            ctx.caution_directives.append(
                f"GPU memory pressure: {state.gpu_memory_used_gb:.1f}/{state.gpu_memory_total_gb:.1f} GB used. "
                "Avoid loading additional models."
            )

        # Enforcement rules — always enforced
        ctx.enforcement_rules = [
            "All code edits MUST include: # Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description",
            "YAML paths use single quotes to avoid backslash escape issues",
            "Use encoding='utf-8' when opening files in Python on Windows",
            "Instructions are append-only living documents — never overwrite existing behaviors",
            "K8s ConfigMap is the source of truth for adaptive instructions",
        ]

    def _generate_routing_overrides(self, ctx: InstructionContext, state: SystemState) -> None:
        """Generate agent routing overrides based on availability."""
        if ctx.agent_availability == AgentAvailability.FULL:
            # No overrides needed — all agents available
            return

        if ctx.agent_availability == AgentAvailability.GPU_ONLY:
            # Ollama down but GPU available — route AI tasks to direct PyTorch
            ctx.agent_routing_overrides["ALPHA"] = "active-no-ollama"
            ctx.agent_routing_overrides["BETA"] = "active-no-ollama"

        elif ctx.agent_availability == AgentAvailability.CPU_ONLY:
            # No GPU — only planning/integration agents
            ctx.agent_routing_overrides["ALPHA"] = "suspended-no-gpu"
            ctx.agent_routing_overrides["BETA"] = "suspended-no-gpu"
            ctx.agent_routing_overrides["GAMMA"] = "active"
            ctx.agent_routing_overrides["DELTA"] = "active"
            ctx.agent_routing_overrides["COPILOT"] = "limited-no-gpu"

        elif ctx.agent_availability == AgentAvailability.MINIMAL:
            # Minimal — everything non-essential suspended
            for agent in ["ALPHA", "BETA", "GAMMA", "DELTA", "COPILOT"]:
                ctx.agent_routing_overrides[agent] = "suspended"

    def _generate_k8s_instructions(self, ctx: InstructionContext, state: SystemState) -> None:
        """Generate K8s-specific instruction content."""
        ctx.k8s_instructions = {
            "cluster_status": (
                f"kubernetes_ready={state.k8s_available}, "
                f"deployments={state.k8s_deployments_ready}/{state.k8s_deployments}, "
                f"pods={state.k8s_pods_ready}/{state.k8s_pods_total}"
            ),
            "instruction_source": "k8s:configmap/slate-instructions",
            "instruction_mode": ctx.mode.value,
            "agent_availability": ctx.agent_availability.value,
            "instruction_controller": INSTRUCTION_CONTROLLER_NAME,
        }

    # ─── Instruction Generation ──────────────────────────────────────────

    def generate_instruction_block(self, ctx: Optional[InstructionContext] = None) -> str:
        """
        Generate a consumable instruction block for Copilot / @slate sessions.

        This is the primary output consumed by the @slate extension. It produces
        a markdown-formatted instruction block that reflects the current system
        state and overrides static instructions where appropriate.
        """
        if ctx is None:
            ctx = self.evaluate_system_state()

        lines = []
        lines.append("## Adaptive Instruction Layer (K8s-Driven)")
        lines.append(f"<!-- Generated: {ctx.timestamp} | Mode: {ctx.mode.value} | "
                      f"Availability: {ctx.agent_availability.value} -->")
        lines.append("")

        # Mode banner
        mode_icons = {
            InstructionMode.NORMAL: "[OK]",
            InstructionMode.DEGRADED: "[!!]",
            InstructionMode.MAINTENANCE: "[MAINT]",
            InstructionMode.AUTONOMOUS: "[AUTO]",
            InstructionMode.EMERGENCY: "[EMERGENCY]",
            InstructionMode.DEVELOPMENT: "[DEV]",
        }
        lines.append(f"**System Mode**: {mode_icons.get(ctx.mode, '[?]')} {ctx.mode.value.upper()}")
        lines.append(f"**Agent Availability**: {ctx.agent_availability.value}")
        lines.append(f"**Instruction Source**: K8s ConfigMap `{CONFIGMAP_NAME}` in namespace `{CONFIGMAP_NAMESPACE}`")
        lines.append("")

        # Priority directives
        if ctx.priority_directives:
            lines.append("### Active Directives")
            for d in ctx.priority_directives:
                lines.append(f"- {d}")
            lines.append("")

        # Caution directives
        if ctx.caution_directives:
            lines.append("### Caution")
            for d in ctx.caution_directives:
                lines.append(f"- {d}")
            lines.append("")

        # Tool availability
        if ctx.disabled_tools:
            lines.append("### Tool Availability")
            lines.append(f"- **Active**: {len(ctx.active_tools)} tools")
            lines.append(f"- **Disabled**: {', '.join(sorted(ctx.disabled_tools)[:5])}{'...' if len(ctx.disabled_tools) > 5 else ''}")
            lines.append("")

        # Agent routing
        if ctx.agent_routing_overrides:
            lines.append("### Agent Routing Overrides")
            for agent, status in ctx.agent_routing_overrides.items():
                lines.append(f"- **{agent}**: {status}")
            lines.append("")

        # Enforcement
        if ctx.enforcement_rules:
            lines.append("### Enforcement Rules (Always Active)")
            for r in ctx.enforcement_rules:
                lines.append(f"- {r}")
            lines.append("")

        # K8s cluster info
        if ctx.k8s_instructions:
            lines.append("### K8s Cluster State")
            lines.append(f"- {ctx.k8s_instructions.get('cluster_status', 'unknown')}")
            lines.append(f"- Source: `{ctx.k8s_instructions.get('instruction_source', 'unknown')}`")
            lines.append("")

        return "\n".join(lines)

    # ─── K8s ConfigMap Operations ────────────────────────────────────────

    def apply_to_configmap(self, ctx: Optional[InstructionContext] = None) -> Tuple[bool, str]:
        """
        Apply the current instruction context to the K8s ConfigMap.

        Updates the `slate-instructions` ConfigMap with the active instruction
        state, making it available to all pods in the cluster.

        Returns:
            Tuple of (success, message)
        """
        if ctx is None:
            ctx = self._last_context or self.evaluate_system_state()

        # Build the instruction state data
        state_data = {
            "mode": ctx.mode.value,
            "agent_availability": ctx.agent_availability.value,
            "active_protocols": ctx.active_protocols,
            "disabled_protocols": ctx.disabled_protocols,
            "active_tools": ctx.active_tools,
            "disabled_tools": ctx.disabled_tools,
            "agent_routing_overrides": ctx.agent_routing_overrides,
            "priority_directives": ctx.priority_directives,
            "caution_directives": ctx.caution_directives,
            "enforcement_rules": ctx.enforcement_rules,
            "k8s_instructions": ctx.k8s_instructions,
            "timestamp": ctx.timestamp,
            "generated_by": INSTRUCTION_CONTROLLER_NAME,
        }

        # Write to state file for local access
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, default=str)
        except IOError as e:
            return False, f"Failed to write state file: {e}"

        # Apply to K8s ConfigMap via kubectl patch
        try:
            # Build the patch payload
            patch_data = {
                "data": {
                    "active-state.yaml": json.dumps(state_data, indent=2, default=str),
                    "instruction-block.md": self.generate_instruction_block(ctx),
                    "version": ctx.system_state.slate_version if ctx.system_state else "2.4.0",
                    "last_updated": ctx.timestamp,
                }
            }

            result = subprocess.run(
                ["kubectl", "patch", "configmap", CONFIGMAP_NAME,
                 "-n", CONFIGMAP_NAMESPACE,
                 "--type", "merge",
                 "-p", json.dumps(patch_data)],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                return True, f"ConfigMap {CONFIGMAP_NAME} updated successfully"
            else:
                return False, f"kubectl patch failed: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return False, "kubectl patch timed out"
        except FileNotFoundError:
            return False, "kubectl not found — K8s not available"

    def read_from_configmap(self) -> Optional[Dict[str, Any]]:
        """
        Read the active instruction state from K8s ConfigMap.

        Returns:
            Instruction state dict or None if unavailable
        """
        try:
            result = subprocess.run(
                ["kubectl", "get", "configmap", CONFIGMAP_NAME,
                 "-n", CONFIGMAP_NAMESPACE, "-o", "json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                cm = json.loads(result.stdout)
                data = cm.get("data", {})
                active_state = data.get("active-state.yaml", "{}")
                try:
                    return json.loads(active_state)
                except json.JSONDecodeError:
                    return {"raw": active_state}
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def read_local_state(self) -> Optional[Dict[str, Any]]:
        """Read instruction state from local file (fallback when K8s unavailable)."""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return None

    def get_active_instructions(self) -> Dict[str, Any]:
        """
        Get the currently active instruction set.

        Tries K8s ConfigMap first, falls back to local state file.
        This is the method called by the @slate extension.

        Returns:
            Active instruction state dict
        """
        # Try K8s first
        state = self.read_from_configmap()
        if state:
            state["source"] = "k8s-configmap"
            return state

        # Fallback to local state
        state = self.read_local_state()
        if state:
            state["source"] = "local-file"
            return state

        # No state available — generate fresh
        ctx = self.evaluate_system_state()
        return {
            "source": "live-evaluation",
            "mode": ctx.mode.value,
            "agent_availability": ctx.agent_availability.value,
            "priority_directives": ctx.priority_directives,
            "active_tools": ctx.active_tools,
            "timestamp": ctx.timestamp,
        }

    # ─── Full Sync ───────────────────────────────────────────────────────

    def sync(self) -> Dict[str, Any]:
        """
        Full synchronization: evaluate → generate → apply → report.

        This is the main entry point for the instruction controller loop.
        """
        # 1. Collect state
        state = self.collect_system_state()

        # 2. Evaluate
        ctx = self.evaluate_system_state(state)

        # 3. Apply to ConfigMap
        success, message = self.apply_to_configmap(ctx)

        # 4. Generate instruction block
        block = self.generate_instruction_block(ctx)

        # 5. Write context file for local consumption
        try:
            context_data = {
                "mode": ctx.mode.value,
                "agent_availability": ctx.agent_availability.value,
                "instruction_block": block,
                "sync_result": {"success": success, "message": message},
                "timestamp": ctx.timestamp,
            }
            with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2, default=str)
        except IOError:
            pass

        return {
            "mode": ctx.mode.value,
            "agent_availability": ctx.agent_availability.value,
            "health": state.overall_health,
            "k8s": f"{state.k8s_deployments_ready}/{state.k8s_deployments} deployments",
            "gpu": f"{state.gpu_count}x GPUs ({state.gpu_memory_used_gb:.1f}/{state.gpu_memory_total_gb:.1f} GB)",
            "configmap_sync": {"success": success, "message": message},
            "active_protocols": len(ctx.active_protocols),
            "active_tools": len(ctx.active_tools),
            "directives": len(ctx.priority_directives),
            "timestamp": ctx.timestamp,
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for the Adaptive Instruction Controller."""
    parser = argparse.ArgumentParser(
        description="SLATE Adaptive Instruction Layer — K8s-driven dynamic instruction controller"
    )
    parser.add_argument("--status", action="store_true",
                        help="Show current instruction state")
    parser.add_argument("--evaluate", action="store_true",
                        help="Evaluate system state and show instruction context")
    parser.add_argument("--apply", action="store_true",
                        help="Apply evaluated instructions to K8s ConfigMap")
    parser.add_argument("--get-context", action="store_true",
                        help="Get the context-aware instruction block")
    parser.add_argument("--sync", action="store_true",
                        help="Full sync: evaluate + apply + report")
    parser.add_argument("--get-active", action="store_true",
                        help="Get active instruction set (K8s → local fallback)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    controller = AdaptiveInstructionController()

    if args.sync:
        result = controller.sync()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("\n╔══════════════════════════════════════════════════════════════╗")
            print("║         SLATE Adaptive Instruction Sync                      ║")
            print("╚══════════════════════════════════════════════════════════════╝\n")
            for key, val in result.items():
                print(f"  {key}: {val}")
            print()

    elif args.evaluate:
        state = controller.collect_system_state()
        ctx = controller.evaluate_system_state(state)
        if args.json:
            data = {
                "mode": ctx.mode.value,
                "agent_availability": ctx.agent_availability.value,
                "active_protocols": ctx.active_protocols,
                "disabled_protocols": ctx.disabled_protocols,
                "active_tools": ctx.active_tools,
                "agent_routing_overrides": ctx.agent_routing_overrides,
                "priority_directives": ctx.priority_directives,
                "enforcement_rules": ctx.enforcement_rules,
                "k8s_instructions": ctx.k8s_instructions,
                "timestamp": ctx.timestamp,
            }
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"\nMode: {ctx.mode.value}")
            print(f"Agent Availability: {ctx.agent_availability.value}")
            print(f"\nActive Protocols: {', '.join(ctx.active_protocols)}")
            print(f"Disabled Protocols: {', '.join(ctx.disabled_protocols)}")
            print(f"\nActive Tools: {len(ctx.active_tools)}")
            print(f"Priority Directives: {len(ctx.priority_directives)}")
            for d in ctx.priority_directives:
                print(f"  → {d}")
            if ctx.agent_routing_overrides:
                print(f"\nRouting Overrides:")
                for agent, status in ctx.agent_routing_overrides.items():
                    print(f"  {agent}: {status}")
            print()

    elif args.apply:
        ctx = controller.evaluate_system_state()
        success, message = controller.apply_to_configmap(ctx)
        if args.json:
            print(json.dumps({"success": success, "message": message}))
        else:
            icon = "[OK]" if success else "[FAIL]"
            print(f"\n{icon} {message}")

    elif args.get_context:
        block = controller.generate_instruction_block()
        print(block)

    elif args.get_active:
        active = controller.get_active_instructions()
        if args.json:
            print(json.dumps(active, indent=2, default=str))
        else:
            print(f"\nSource: {active.get('source', 'unknown')}")
            print(f"Mode: {active.get('mode', 'unknown')}")
            print(f"Agent Availability: {active.get('agent_availability', 'unknown')}")
            print(f"Timestamp: {active.get('timestamp', 'unknown')}")
            if directives := active.get("priority_directives"):
                print(f"\nDirectives:")
                for d in directives:
                    print(f"  → {d}")
            print()

    else:
        # Default: --status
        active = controller.get_active_instructions()
        if args.json:
            print(json.dumps(active, indent=2, default=str))
        else:
            print("\n╔══════════════════════════════════════════════════════════════╗")
            print("║         SLATE Adaptive Instructions — Status                 ║")
            print("╚══════════════════════════════════════════════════════════════╝\n")
            print(f"  Source: {active.get('source', 'unknown')}")
            print(f"  Mode: {active.get('mode', 'unknown')}")
            print(f"  Agent Availability: {active.get('agent_availability', 'unknown')}")
            print(f"  Active Tools: {len(active.get('active_tools', []))}")
            print(f"  Timestamp: {active.get('timestamp', 'unknown')}")
            if directives := active.get("priority_directives"):
                print(f"\n  Directives:")
                for d in directives:
                    print(f"    → {d}")
            print()


if __name__ == "__main__":
    main()
