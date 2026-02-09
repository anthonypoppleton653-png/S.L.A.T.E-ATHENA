# Modified: 2026-02-09T17:00:00Z | Author: ClaudeCode | Change: Create SLATE avatar state engine
"""
SLATE Avatar State Engine

Manages the living orrery avatar — a watchmaker mechanism that reflects system state.
The avatar evolves as the tech tree progresses and reacts to real-time service health.

Avatar Levels:
  Level 1: Basic orrery with 5 nodes
  Level 2: 12 nodes, outer ring appears
  Level 3: Full orrery, glass dome enclosure
  Level 4: Golden ratio spiral overlay, premium materials
  Level 5: Watchmaker masterpiece, all animations active
"""
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

IDENTITY_DIR = WORKSPACE_ROOT / ".slate_identity"
AVATAR_STATE_FILE = IDENTITY_DIR / "avatar_state.json"
TECH_TREE_FILE = WORKSPACE_ROOT / ".slate_tech_tree" / "tech_tree.json"
DESIGN_TOKENS_FILE = IDENTITY_DIR / "design-tokens.json"


# ── Service Node Definitions ─────────────────────────────────────────────────

AVATAR_NODES = [
    # Core ring (always visible)
    {"id": "core", "label": "SLATE Core", "ring": 0, "angle": 0, "type": "core",
     "color": "#B85A3C", "service": None, "level_req": 1},

    # Inner ring — primary services (Level 1+)
    {"id": "ollama", "label": "Ollama", "ring": 1, "angle": 0, "type": "ai",
     "color": "#4FC3F7", "service": "ollama", "port": 11434, "level_req": 1},
    {"id": "dashboard", "label": "Dashboard", "ring": 1, "angle": 72, "type": "ui",
     "color": "#4CAF50", "service": "dashboard", "port": 8080, "level_req": 1},
    {"id": "runner", "label": "Runner", "ring": 1, "angle": 144, "type": "infra",
     "color": "#FF9800", "service": "runner", "port": None, "level_req": 1},
    {"id": "chromadb", "label": "ChromaDB", "ring": 1, "angle": 216, "type": "data",
     "color": "#9C27B0", "service": "chromadb", "port": 8000, "level_req": 1},
    {"id": "mcp", "label": "MCP Server", "ring": 1, "angle": 288, "type": "bridge",
     "color": "#2196F3", "service": "mcp", "port": None, "level_req": 1},

    # Middle ring — extended services (Level 2+)
    {"id": "foundry", "label": "Foundry", "ring": 2, "angle": 30, "type": "ai",
     "color": "#00BCD4", "service": "foundry", "port": 5272, "level_req": 2},
    {"id": "k8s", "label": "Kubernetes", "ring": 2, "angle": 90, "type": "infra",
     "color": "#326CE5", "service": "k8s", "port": None, "level_req": 2},
    {"id": "agent-router", "label": "Agent Router", "ring": 2, "angle": 150, "type": "ai",
     "color": "#E91E63", "service": "agent-router", "port": 8081, "level_req": 2},
    {"id": "autonomous", "label": "Auto Loop", "ring": 2, "angle": 210, "type": "ai",
     "color": "#FF5722", "service": "autonomous", "port": 8082, "level_req": 2},
    {"id": "workflow", "label": "Workflow", "ring": 2, "angle": 270, "type": "infra",
     "color": "#795548", "service": "workflow", "port": 8084, "level_req": 2},
    {"id": "gpu-mgr", "label": "GPU Manager", "ring": 2, "angle": 330, "type": "hardware",
     "color": "#76B900", "service": "gpu", "port": None, "level_req": 2},
    {"id": "tokens", "label": "Token System", "ring": 2, "angle": 0, "type": "security",
     "color": "#FFC107", "service": "tokens", "port": None, "level_req": 2},

    # Outer ring — advanced (Level 3+)
    {"id": "trellis", "label": "TRELLIS.2", "ring": 3, "angle": 45, "type": "ai",
     "color": "#00E676", "service": "trellis", "port": 8086, "level_req": 3},
    {"id": "graphrag", "label": "GraphRAG", "ring": 3, "angle": 135, "type": "data",
     "color": "#7C4DFF", "service": "graphrag", "port": None, "level_req": 3},
    {"id": "llmlingua", "label": "LLMLingua", "ring": 3, "angle": 225, "type": "ai",
     "color": "#FF6D00", "service": "llmlingua", "port": None, "level_req": 3},
    {"id": "brand", "label": "Brand System", "ring": 3, "angle": 315, "type": "identity",
     "color": "#D4785A", "service": None, "level_req": 3},
]

AVATAR_CONNECTIONS = [
    # Core to inner ring
    {"from": "core", "to": "ollama", "type": "data", "level_req": 1},
    {"from": "core", "to": "dashboard", "type": "data", "level_req": 1},
    {"from": "core", "to": "runner", "type": "control", "level_req": 1},
    {"from": "core", "to": "chromadb", "type": "data", "level_req": 1},
    {"from": "core", "to": "mcp", "type": "control", "level_req": 1},

    # Inner ring interconnections
    {"from": "ollama", "to": "dashboard", "type": "status", "level_req": 1},
    {"from": "runner", "to": "dashboard", "type": "status", "level_req": 1},
    {"from": "chromadb", "to": "ollama", "type": "data", "level_req": 1},

    # Inner to middle ring
    {"from": "ollama", "to": "foundry", "type": "fallback", "level_req": 2},
    {"from": "runner", "to": "k8s", "type": "deploy", "level_req": 2},
    {"from": "core", "to": "agent-router", "type": "control", "level_req": 2},
    {"from": "agent-router", "to": "autonomous", "type": "task", "level_req": 2},
    {"from": "runner", "to": "workflow", "type": "control", "level_req": 2},
    {"from": "runner", "to": "gpu-mgr", "type": "hardware", "level_req": 2},
    {"from": "core", "to": "tokens", "type": "auth", "level_req": 2},

    # Middle ring interconnections
    {"from": "autonomous", "to": "workflow", "type": "task", "level_req": 2},
    {"from": "gpu-mgr", "to": "ollama", "type": "hardware", "level_req": 2},
    {"from": "tokens", "to": "mcp", "type": "auth", "level_req": 2},

    # Middle to outer ring
    {"from": "k8s", "to": "trellis", "type": "deploy", "level_req": 3},
    {"from": "chromadb", "to": "graphrag", "type": "data", "level_req": 3},
    {"from": "ollama", "to": "llmlingua", "type": "optimize", "level_req": 3},
    {"from": "core", "to": "brand", "type": "identity", "level_req": 3},
]


def _load_json(path: Path) -> dict:
    """Load JSON file safely."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def calculate_avatar_level(tech_tree: dict) -> int:
    """Calculate avatar evolution level from tech tree completion.

    Level 1: < 50% Phase 2 complete
    Level 2: 50%+ Phase 2 complete
    Level 3: 75%+ Phase 2 complete
    Level 4: Phase 2 100% complete
    Level 5: All specs and all phases complete
    """
    nodes = tech_tree.get("nodes", [])
    if not nodes:
        return 1

    phase2_nodes = [n for n in nodes if n.get("phase") == 2]
    phase2_complete = sum(1 for n in phase2_nodes if n.get("status") == "complete")
    phase2_total = len(phase2_nodes) if phase2_nodes else 1
    phase2_pct = phase2_complete / phase2_total

    phase3_nodes = [n for n in nodes if n.get("phase") == 3]
    phase3_complete = sum(1 for n in phase3_nodes if n.get("status") == "complete")

    all_complete = all(n.get("status") == "complete" for n in nodes)

    if all_complete:
        return 5
    elif phase2_pct >= 1.0:
        return 4
    elif phase2_pct >= 0.75:
        return 3
    elif phase2_pct >= 0.50:
        return 2
    else:
        return 1


def get_tech_tree_stats(tech_tree: dict) -> dict:
    """Extract statistics from tech tree for avatar display."""
    nodes = tech_tree.get("nodes", [])
    edges = tech_tree.get("edges", [])

    total = len(nodes)
    complete = sum(1 for n in nodes if n.get("status") == "complete")
    in_progress = sum(1 for n in nodes if n.get("status") == "in_progress")
    available = sum(1 for n in nodes if n.get("status") == "available")

    return {
        "total_nodes": total,
        "complete": complete,
        "in_progress": in_progress,
        "available": available,
        "completion_pct": round(complete / total * 100, 1) if total else 0,
        "total_edges": len(edges),
        "version": tech_tree.get("version", "0.0.0"),
    }


def check_service_health(node: dict) -> str:
    """Check if a service node is healthy. Returns: 'active', 'pending', 'error', 'unknown'."""
    import urllib.request

    port = node.get("port")
    service = node.get("service")

    if not service:
        return "active"  # Non-service nodes are always "active"

    if not port:
        # Services without ports — check by other means
        if service == "runner":
            runner_file = WORKSPACE_ROOT / ".runner"
            return "active" if runner_file.exists() else "pending"
        elif service == "tokens":
            token_store = WORKSPACE_ROOT / ".slate_tokens" / "token_store.json"
            return "active" if token_store.exists() else "pending"
        elif service == "gpu":
            return "active"  # Assume GPU is present
        elif service == "k8s":
            return "pending"  # K8s check is expensive, default pending
        return "unknown"

    # HTTP health check
    try:
        url = f"http://127.0.0.1:{port}/"
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "SLATE-Avatar/1.0")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return "active" if resp.status < 500 else "error"
    except Exception:
        return "pending"


def build_avatar_state(check_health: bool = False) -> dict:
    """Build the complete avatar state from system data.

    Args:
        check_health: If True, perform live HTTP health checks on services.
                      If False, mark all as 'unknown' (fast mode for export).
    """
    # Load tech tree
    tech_tree = _load_json(TECH_TREE_FILE)

    # Calculate level
    level = calculate_avatar_level(tech_tree)
    stats = get_tech_tree_stats(tech_tree)

    # Build nodes with health status
    visible_nodes = []
    for node in AVATAR_NODES:
        if node["level_req"] <= level:
            health = "unknown"
            if check_health:
                health = check_service_health(node)
            visible_nodes.append({
                **node,
                "health": health,
                "visible": True,
            })
        else:
            visible_nodes.append({
                **node,
                "health": "locked",
                "visible": False,
            })

    # Build connections
    visible_connections = []
    for conn in AVATAR_CONNECTIONS:
        if conn["level_req"] <= level:
            visible_connections.append({**conn, "active": True})
        else:
            visible_connections.append({**conn, "active": False})

    # Determine expression state
    active_count = sum(1 for n in visible_nodes if n["health"] == "active")
    visible_count = sum(1 for n in visible_nodes if n["visible"])
    health_ratio = active_count / visible_count if visible_count else 0

    if health_ratio >= 0.8:
        expression = "healthy"
        orbit_speed = 1.0
    elif health_ratio >= 0.5:
        expression = "degraded"
        orbit_speed = 0.7
    elif health_ratio > 0:
        expression = "stressed"
        orbit_speed = 1.5
    else:
        expression = "idle"
        orbit_speed = 0.3

    state = {
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "level_name": _level_name(level),
        "expression": expression,
        "orbit_speed": orbit_speed,
        "tech_tree": stats,
        "nodes": visible_nodes,
        "connections": visible_connections,
        "rings": {
            "core": {"radius": 0, "visible": True},
            "inner": {"radius": 120, "visible": level >= 1, "node_count": 5},
            "middle": {"radius": 220, "visible": level >= 2, "node_count": 7},
            "outer": {"radius": 320, "visible": level >= 3, "node_count": 4},
        },
        "design": {
            "primary": "#B85A3C",
            "blueprint_bg": "#0D1B2A",
            "blueprint_grid": "#1B3A4B",
            "jewel_active": "#4CAF50",
            "jewel_pending": "#FF9800",
            "jewel_error": "#F44336",
            "jewel_locked": "#424242",
        },
    }

    return state


def _level_name(level: int) -> str:
    """Get the display name for an avatar level."""
    names = {
        1: "Nascent Orrery",
        2: "Expanding Mechanism",
        3: "Full Orrery",
        4: "Golden Apparatus",
        5: "Watchmaker Masterpiece",
    }
    return names.get(level, "Unknown")


def export_avatar_state(check_health: bool = False) -> dict:
    """Build avatar state and save to disk."""
    state = build_avatar_state(check_health=check_health)
    _save_json(AVATAR_STATE_FILE, state)
    return state


def print_status(state: dict) -> None:
    """Print a human-readable avatar status."""
    print(f"\n{'='*60}")
    print(f"  SLATE Avatar — {state['level_name']}")
    print(f"  Level {state['level']} | Expression: {state['expression']}")
    print(f"{'='*60}")

    tt = state["tech_tree"]
    print(f"\n  Tech Tree: v{tt['version']} — {tt['completion_pct']}% complete")
    print(f"  Nodes: {tt['complete']}/{tt['total_nodes']} complete, "
          f"{tt['in_progress']} in progress, {tt['available']} available")

    print(f"\n  Rings:")
    for name, ring in state["rings"].items():
        status = "[+] visible" if ring["visible"] else "[-] locked"
        count = ring.get("node_count", 1)
        print(f"    {name:>8}: {status} ({count} nodes)")

    print(f"\n  Service Nodes:")
    for node in state["nodes"]:
        if node["visible"]:
            jewel = {"active": "[OK]", "pending": "[..]", "error": "[!!]", "unknown": "[??]"}.get(
                node["health"], "[--]")
            print(f"    {jewel} {node['label']:20s} ring={node['ring']} health={node['health']}")

    active_conns = sum(1 for c in state["connections"] if c["active"])
    total_conns = len(state["connections"])
    print(f"\n  Connections: {active_conns}/{total_conns} active")
    print(f"  Orbit Speed: {state['orbit_speed']}x")
    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="SLATE Avatar State Engine")
    parser.add_argument("--status", action="store_true", help="Show avatar status")
    parser.add_argument("--export", action="store_true", help="Export avatar state to JSON")
    parser.add_argument("--health", action="store_true", help="Include live health checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--level", action="store_true", help="Show current level only")
    args = parser.parse_args()

    if args.level:
        tech_tree = _load_json(TECH_TREE_FILE)
        level = calculate_avatar_level(tech_tree)
        print(f"Level {level}: {_level_name(level)}")
        return

    state = build_avatar_state(check_health=args.health)

    if args.export:
        export_avatar_state(check_health=args.health)
        print(f"Avatar state exported to {AVATAR_STATE_FILE}")

    if args.json:
        print(json.dumps(state, indent=2, default=str))
    elif args.status or not (args.export or args.json):
        print_status(state)


if __name__ == "__main__":
    main()
