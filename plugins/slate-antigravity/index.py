# Modified: 2026-02-09T03:24:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Integrated dashboard_client for direct API access to SLATE dashboard
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
"""
SLATE Antigravity Plugin — Entry Point
=======================================
Provides Antigravity (Google AI Ultra) integration into the @slate extension
ecosystem. Connects to the Copilot Bridge web host at port 8083 and registers
as the ANTIGRAVITY agent in the SLATE agent registry.

Architecture:
  @slate Extension (VS Code)
       │
       ▼  HTTP POST to 127.0.0.1:8083/api/exec
  Copilot Bridge (K8s/Docker)
       │
       ▼  Agent Router → ANTIGRAVITY
  This Plugin (index.py)
       │
       ▼  Ollama (slate-coder 12B, slate-planner 7B, slate-fast 3B)
  Local GPU inference
"""

import json
import sys
import os
import datetime
from pathlib import Path

# Ensure workspace root is in path
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(WORKSPACE_ROOT))

# ─── Plugin Metadata ────────────────────────────────────────────────────────

PLUGIN_NAME = "slate-antigravity"
PLUGIN_VERSION = "1.2.0"
AGENT_NAME = "ANTIGRAVITY"
AGENT_TYPE = "architect"

# ─── Web Host Configuration ─────────────────────────────────────────────────

# The @slate extension v5.1.0 connects via K8s (copilot-bridge-svc:8083)
# or Docker (container: slate). This plugin registers endpoints that the
# Copilot Bridge routes to when tasks are classified as ANTIGRAVITY.

WEB_HOST_CONFIG = {
    "copilot_bridge_port": 8083,
    "dashboard_port": 8080,
    "agent_router_port": 8081,
    "ollama_host": os.environ.get("OLLAMA_HOST", "127.0.0.1:11434"),
    "bind_address": "127.0.0.1",  # SLATE local-only policy — NEVER 0.0.0.0
}

# ─── Ollama Model Config ────────────────────────────────────────────────────

MODELS = {
    "architect": "slate-coder",     # 12B — deep code analysis, refactoring
    "planner": "slate-planner",      # 7B — architecture planning, task routing
    "classifier": "slate-fast",      # 3B — quick classification, summaries
}

# ─── Agent Registration ─────────────────────────────────────────────────────

def get_agent_config():
    """Return the agent configuration for SLATE agent registry registration."""
    return {
        "name": AGENT_NAME,
        "type": AGENT_TYPE,
        "version": PLUGIN_VERSION,
        "patterns": ["architect", "refactor", "master", "design", "security"],
        "gpu_required": True,
        "models": MODELS,
        "capabilities": [
            "refactor",
            "design",
            "security",
            "architecture",
            "code_review",
            "prompt_engineering",
            "forge_collaboration",
        ],
        "web_host": WEB_HOST_CONFIG,
        "forge_path": str(WORKSPACE_ROOT / "FORGE.md"),
        "prompts_dir": str(WORKSPACE_ROOT / "prompts"),
    }


# ─── FORGE Integration ──────────────────────────────────────────────────────

def read_forge_log(last_n: int = 10):
    """Read the last N entries from FORGE.md for teammate sync."""
    forge_path = WORKSPACE_ROOT / "FORGE.md"
    if not forge_path.exists():
        return {"error": "FORGE.md not found", "entries": []}

    content = forge_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    entries = [l for l in lines if l.startswith("### [")]
    return {
        "total_entries": len(entries),
        "recent": entries[-last_n:] if entries else [],
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def append_forge_entry(action: str, details: str):
    """Append an entry to FORGE.md following the collaboration protocol."""
    forge_path = WORKSPACE_ROOT / "FORGE.md"
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entry = f"\n### [{AGENT_NAME}] {timestamp} | {action}\n\n{details}\n"

    with open(forge_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return {"status": "ok", "timestamp": timestamp, "action": action}


# ─── Prompt Loader ───────────────────────────────────────────────────────────

def load_prompt(prompt_name: str):
    """Load a super-prompt template from the prompts/ directory."""
    prompts_dir = WORKSPACE_ROOT / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.prompt.md"

    if not prompt_file.exists():
        return {"error": f"Prompt '{prompt_name}' not found", "available": list_prompts()}

    content = prompt_file.read_text(encoding="utf-8")

    # Parse YAML frontmatter
    parts = content.split("---", 2)
    if len(parts) >= 3:
        try:
            import yaml
            metadata = yaml.safe_load(parts[1])
        except Exception:
            metadata = {}
        body = parts[2].strip()
    else:
        metadata = {}
        body = content

    return {
        "name": prompt_name,
        "metadata": metadata,
        "body": body,
        "model": metadata.get("model", "slate-planner"),
    }


def list_prompts():
    """List all available super-prompts."""
    prompts_dir = WORKSPACE_ROOT / "prompts"
    if not prompts_dir.exists():
        return []
    return [f.stem for f in prompts_dir.glob("*.prompt.md")]


# ─── Ollama Integration ─────────────────────────────────────────────────────

def ollama_generate(prompt: str, model: str = None, timeout: int = 120):
    """Generate a response using local Ollama. Returns the response text.

    Uses urllib.request (no curl.exe per SLATE rules).
    """
    import urllib.request

    model = model or MODELS["architect"]
    ollama_url = f"http://{WEB_HOST_CONFIG['ollama_host']}/api/generate"

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048},
    }).encode("utf-8")

    req = urllib.request.Request(
        ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "response": data.get("response", ""),
                "model": model,
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ns": data.get("eval_duration", 0),
            }
    except Exception as e:
        return {"error": str(e), "model": model}


# ─── Web Host Endpoint Handlers ─────────────────────────────────────────────
# These endpoints are called by the Copilot Bridge when the @slate extension
# routes tasks to the ANTIGRAVITY agent.

def handle_task(task_payload: dict):
    """Handle a task routed to ANTIGRAVITY by the agent router.

    Called via Copilot Bridge → Agent Router → ANTIGRAVITY.
    """
    task_type = task_payload.get("task_type", "unknown")
    description = task_payload.get("description", "")

    # Route to appropriate model based on task type
    if task_type in ("code_generation", "bug_fix", "refactor"):
        model = MODELS["architect"]  # slate-coder 12B
    elif task_type in ("documentation", "infrastructure"):
        model = MODELS["planner"]    # slate-planner 7B
    else:
        model = MODELS["classifier"]  # slate-fast 3B

    # Log to FORGE
    append_forge_entry(
        f"TASK: {task_type}",
        f"**Description:** {description}\n**Model:** {model}\n**Status:** Processing..."
    )

    # Generate response
    result = ollama_generate(
        f"You are the ANTIGRAVITY architect agent for SLATE. "
        f"Task type: {task_type}. "
        f"Task: {description}. "
        f"Provide a detailed solution.",
        model=model,
    )

    # Log completion to FORGE
    status = "completed" if "error" not in result else "failed"
    append_forge_entry(
        f"OUTPUT: {task_type} — {status}",
        f"**Result:** {result.get('response', result.get('error', 'unknown'))[:500]}..."
    )

    return {
        "agent": AGENT_NAME,
        "task_type": task_type,
        "status": status,
        "result": result,
    }


def handle_prompt_exec(prompt_name: str, variables: dict = None):
    """Execute a super-prompt template with variable substitution."""
    prompt_data = load_prompt(prompt_name)
    if "error" in prompt_data:
        return prompt_data

    body = prompt_data["body"]
    model = prompt_data["model"]

    # Substitute variables
    if variables:
        for key, value in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(value))

    return ollama_generate(body, model=model)


# ─── Dashboard Client ───────────────────────────────────────────────────────

def get_dashboard():
    """Get a SlateDashboard client instance."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "dashboard_client",
        str(Path(__file__).parent / "dashboard_client.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SlateDashboard()


def query_dashboard(endpoint: str) -> dict:
    """Query any dashboard API endpoint."""
    d = get_dashboard()
    commands = {
        "status": d.status, "health": d.health, "tasks": d.tasks,
        "agents": d.agents, "gpu": d.gpu, "runner": d.runner,
        "services": d.services, "k8s": d.kubernetes, "docker": d.docker,
        "github": d.github, "workflows": d.workflows, "forks": d.forks,
        "activity": d.activity, "specs": d.specs, "tech": d.tech_tree,
        "report": d.full_report, "orchestrator": d.orchestrator,
        "multirunner": d.multirunner, "schematic": d.schematic_system,
    }
    fn = commands.get(endpoint)
    if fn:
        return fn()
    return d._get(f"/api/{endpoint}")


# ─── Plugin Entry Point ─────────────────────────────────────────────────────

def activate():
    """Activate the Antigravity plugin. Called by SLATE plugin loader."""
    config = get_agent_config()

    # Register with agent registry if available
    try:
        from slate.instruction_loader import get_instruction_loader
        loader = get_instruction_loader()
    except ImportError:
        pass  # Running outside full SLATE environment

    # Check dashboard connectivity
    try:
        dashboard = get_dashboard()
        dash_health = dashboard.health()
        dashboard_status = "connected" if dash_health.get("status") == "ok" else "degraded"
    except Exception:
        dashboard_status = "offline"

    return {
        "plugin": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "agent": config,
        "prompts": list_prompts(),
        "forge_status": read_forge_log(last_n=3),
        "web_host": WEB_HOST_CONFIG,
        "dashboard": {"url": "http://127.0.0.1:8080", "status": dashboard_status},
        "status": "active",
    }


def health_check():
    """Health check endpoint for K8s/Docker readiness probes."""
    try:
        dashboard = get_dashboard()
        dash_health = dashboard.health()
        dashboard_ok = dash_health.get("status") == "ok"
    except Exception:
        dashboard_ok = False

    return {
        "agent": AGENT_NAME,
        "status": "healthy",
        "version": PLUGIN_VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "web_host": WEB_HOST_CONFIG,
        "dashboard": {"connected": dashboard_ok, "url": "http://127.0.0.1:8080"},
        "models": MODELS,
        "prompts_count": len(list_prompts()),
    }


# ─── CLI Interface ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Antigravity Plugin")
    parser.add_argument("--activate", action="store_true", help="Activate the plugin")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--forge", action="store_true", help="Read FORGE.md log")
    parser.add_argument("--prompts", action="store_true", help="List available prompts")
    parser.add_argument("--exec-prompt", type=str, help="Execute a super-prompt")
    parser.add_argument("--task", type=str, help="Handle a task (JSON payload)")
    parser.add_argument("--dashboard", type=str, nargs="?", const="status",
                        help="Query dashboard API (status, tasks, agents, gpu, runner, services, report, etc.)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.activate:
        result = activate()
    elif args.health:
        result = health_check()
    elif args.forge:
        result = read_forge_log()
    elif args.prompts:
        result = {"prompts": list_prompts()}
    elif args.exec_prompt:
        result = handle_prompt_exec(args.exec_prompt)
    elif args.task:
        result = handle_task(json.loads(args.task))
    elif args.dashboard:
        result = query_dashboard(args.dashboard)
    else:
        result = activate()

    print(json.dumps(result, indent=2, default=str))
