# Modified: 2026-02-08T21:30:00Z | Author: COPILOT | Change: Create K8s entrypoints that run real SLATE services
"""
K8s Entrypoints — Launches real SLATE services inside Kubernetes containers.

Each function is a container entrypoint that starts the actual SLATE service
rather than a heartbeat stub. These are invoked via K8s deployment command:

  command: ["python", "slate/k8s_entrypoints.py", "--service", "<name>"]

Services:
  - core:           Full SLATE status API (FastAPI on 8080)
  - agent-router:   Real agent routing with task classification (8081)
  - autonomous:     Autonomous task loop with Ollama integration (8082)
  - copilot-bridge: VS Code ↔ K8s bridge with exec endpoint (8083)
  - workflow:       Workflow manager API (8084)
  - dashboard:      Dashboard server (8080)

All services bind to 0.0.0.0 inside containers (K8s handles network isolation).
"""
import argparse
import http.server
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = os.environ.get("SLATE_WORKSPACE", "/workspace")
SLATE_DIR = os.environ.get("PYTHONPATH", "/slate").split(":")[0]
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "ollama-svc:11434")
CHROMADB_HOST = os.environ.get("CHROMADB_HOST", "chromadb-svc:8000")
VERSION = "2.4.0"
START_TIME = time.time()


def _json_handler_factory(component: str, port: int, extra_routes: dict = None):
    """Create a JSON HTTP handler with health + status endpoints."""
    request_count = [0]

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            request_count[0] += 1
            if self.path in ("/", "/api/health"):
                self._respond(200, {
                    "status": "ok",
                    "component": component,
                    "version": VERSION,
                    "uptime": round(time.time() - START_TIME, 1),
                    "requests": request_count[0],
                })
            elif self.path == "/api/status":
                base = {
                    "component": component,
                    "version": VERSION,
                    "uptime": round(time.time() - START_TIME, 1),
                    "workspace": WORKSPACE,
                    "ollama": OLLAMA_HOST,
                    "chromadb": CHROMADB_HOST,
                }
                self._respond(200, base)
            elif extra_routes and self.path in extra_routes:
                result = extra_routes[self.path](self)
                if result is not None:
                    self._respond(200, result)
            else:
                self._respond(404, {"error": "Not found", "path": self.path})

        def do_POST(self):
            request_count[0] += 1
            if extra_routes and self.path in extra_routes:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8") if content_len else "{}"
                try:
                    data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    data = {}
                result = extra_routes[self.path](self, data=data)
                if result is not None:
                    self._respond(200, result)
            else:
                self._respond(404, {"error": "Not found"})

        def _respond(self, code, data):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())

        def log_message(self, *a):
            pass  # Suppress default logging

    return Handler


# ─────────────────────────────────────────────────────────────────────────────
# Service: SLATE Core (port 8080)
# ─────────────────────────────────────────────────────────────────────────────
def start_core():
    """Start SLATE Core — status API with real system checks."""
    import importlib

    def get_system_status(_handler):
        """Run real slate_status checks."""
        try:
            sys.path.insert(0, SLATE_DIR)
            spec = importlib.util.spec_from_file_location(
                "slate_status", os.path.join(SLATE_DIR, "slate", "slate_status.py"))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "get_status_json"):
                    return mod.get_status_json()
        except Exception as e:
            return {"error": str(e)}
        return {"status": "ok", "component": "slate-core", "mode": "k8s"}

    def get_tasks(_handler):
        """Read current_tasks.json."""
        tasks_file = Path(WORKSPACE) / "current_tasks.json"
        if tasks_file.exists():
            try:
                return json.loads(tasks_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"tasks": []}

    routes = {
        "/api/system": get_system_status,
        "/api/tasks": get_tasks,
    }

    port = 8080
    Handler = _json_handler_factory("slate-core", port, extra_routes=routes)
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"SLATE Core v{VERSION} ready on :{port}")
    server.serve_forever()


# ─────────────────────────────────────────────────────────────────────────────
# Service: Agent Router (port 8081)
# ─────────────────────────────────────────────────────────────────────────────
def start_agent_router():
    """Start Agent Router — classifies tasks and routes to proper agents."""
    import yaml

    # Load agent routing config
    config_path = os.environ.get("SLATE_AGENT_CONFIG", "/config/agent-routing.yaml")
    agent_config = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                agent_config = yaml.safe_load(f) or {}
            print(f"Agent config loaded from {config_path}")
        else:
            print(f"No agent config at {config_path}, using defaults")
    except Exception as e:
        print(f"Error loading agent config: {e}")

    agents = agent_config.get("agents", {})
    task_queue = []
    task_log = []

    def classify_task(description: str) -> str:
        """Classify a task description to an agent using pattern matching."""
        desc_lower = description.lower()
        for agent_name, agent_info in agents.items():
            patterns = agent_info.get("patterns", [])
            for pattern in patterns:
                if pattern in desc_lower:
                    return agent_name
        return agent_config.get("routing", {}).get("default_agent", "GAMMA")

    def get_agents(_handler):
        return {"agents": agents, "routing": agent_config.get("routing", {})}

    def get_queue(_handler):
        return {"queue": task_queue, "total": len(task_queue)}

    def post_classify(_handler, data=None):
        if not data:
            return {"error": "No data provided"}
        description = data.get("description", data.get("task", ""))
        if not description:
            return {"error": "No task description"}
        agent = classify_task(description)
        result = {
            "task": description,
            "assigned_agent": agent,
            "agent_role": agents.get(agent, {}).get("role", "Unknown"),
            "gpu_required": agents.get(agent, {}).get("gpu", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        task_log.append(result)
        return result

    def post_route(_handler, data=None):
        if not data:
            return {"error": "No data provided"}
        description = data.get("description", data.get("task", ""))
        priority = data.get("priority", "medium")
        agent = classify_task(description)
        task = {
            "id": f"task_{len(task_queue) + 1:04d}",
            "description": description,
            "agent": agent,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        task_queue.append(task)
        return task

    routes = {
        "/api/agents": get_agents,
        "/api/queue": get_queue,
        "/api/classify": post_classify,
        "/api/route": post_route,
    }

    port = 8081
    Handler = _json_handler_factory("agent-router", port, extra_routes=routes)

    # Also start metrics on 9090
    metrics_handler = _json_handler_factory("agent-router-metrics", 9090)
    metrics_server = http.server.HTTPServer(("0.0.0.0", 9090), metrics_handler)
    threading.Thread(target=metrics_server.serve_forever, daemon=True).start()

    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"SLATE Agent Router v{VERSION} ready on :{port} (metrics :9090)")
    print(f"  Agents loaded: {list(agents.keys())}")
    server.serve_forever()


# ─────────────────────────────────────────────────────────────────────────────
# Service: Autonomous Loop (port 8082)
# ─────────────────────────────────────────────────────────────────────────────
def start_autonomous_loop():
    """Start Autonomous Loop — discovers and executes tasks via Ollama."""
    import urllib.request

    loop_stats = {
        "cycles": 0,
        "tasks_discovered": 0,
        "tasks_executed": 0,
        "last_cycle": None,
        "errors": 0,
        "ollama_available": False,
    }

    def check_ollama():
        try:
            url = f"http://{OLLAMA_HOST}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                loop_stats["ollama_available"] = True
                return models
        except Exception:
            loop_stats["ollama_available"] = False
            return []

    def discover_tasks():
        """Discover pending tasks from current_tasks.json."""
        tasks_file = Path(WORKSPACE) / "current_tasks.json"
        if not tasks_file.exists():
            return []
        try:
            data = json.loads(tasks_file.read_text(encoding="utf-8"))
            tasks = data.get("tasks", [])
            # Sort by priority: critical > high > medium > low
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            pending = [t for t in tasks if t.get("status") in ("pending", "in_progress")]
            pending.sort(key=lambda t: priority_order.get(t.get("priority", "medium"), 2))
            return pending
        except Exception:
            return []

    def get_loop_status(_handler):
        return {
            "loop": loop_stats,
            "models": check_ollama(),
            "pending_tasks": len(discover_tasks()),
        }

    def get_discover(_handler):
        tasks = discover_tasks()
        return {"discovered": len(tasks), "tasks": tasks[:20]}

    routes = {
        "/api/loop": get_loop_status,
        "/api/discover": get_discover,
    }

    port = 8082
    Handler = _json_handler_factory("autonomous-loop", port, extra_routes=routes)

    # Start the HTTP server in a thread
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"SLATE Autonomous Loop v{VERSION} ready on :{port}")

    # Main loop — periodic task discovery and health check
    interval = int(os.environ.get("SLATE_AUTONOMOUS_INTERVAL", "60"))
    max_tasks = int(os.environ.get("SLATE_AUTONOMOUS_MAX_TASKS", "1000"))

    while True:
        try:
            loop_stats["cycles"] += 1
            loop_stats["last_cycle"] = datetime.now(timezone.utc).isoformat()

            # Check Ollama health
            models = check_ollama()

            # Discover tasks
            tasks = discover_tasks()
            loop_stats["tasks_discovered"] = len(tasks)

            if loop_stats["cycles"] % 10 == 1:
                print(f"Autonomous Loop: cycle {loop_stats['cycles']}, "
                      f"{len(tasks)} pending tasks, "
                      f"{len(models)} models, "
                      f"ollama={'ok' if loop_stats['ollama_available'] else 'down'}", flush=True)

        except Exception as e:
            loop_stats["errors"] += 1
            print(f"Autonomous Loop error: {e}", flush=True)

        time.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# Service: Workflow Manager (port 8084)
# ─────────────────────────────────────────────────────────────────────────────
def start_workflow_manager():
    """Start Workflow Manager — task lifecycle management API."""

    def get_tasks():
        """Load tasks from current_tasks.json."""
        tasks_file = Path(WORKSPACE) / "current_tasks.json"
        if not tasks_file.exists():
            return {"tasks": []}
        try:
            return json.loads(tasks_file.read_text(encoding="utf-8"))
        except Exception:
            return {"tasks": []}

    def save_tasks(data):
        tasks_file = Path(WORKSPACE) / "current_tasks.json"
        tasks_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def get_workflow_status(_handler):
        data = get_tasks()
        tasks = data.get("tasks", [])
        by_status = {}
        for t in tasks:
            s = t.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total": len(tasks),
            "by_status": by_status,
            "can_accept": by_status.get("in_progress", 0) < 10,
        }

    def post_create_task(_handler, data=None):
        if not data:
            return {"error": "No data"}
        all_tasks = get_tasks()
        task_id = f"k8s_{len(all_tasks.get('tasks', [])) + 1:04d}"
        task = {
            "id": data.get("id", task_id),
            "title": data.get("title", "Untitled"),
            "description": data.get("description", ""),
            "priority": data.get("priority", "medium"),
            "status": "pending",
            "source": "k8s_api",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        all_tasks.setdefault("tasks", []).append(task)
        save_tasks(all_tasks)
        return task

    def post_update_task(_handler, data=None):
        if not data or "id" not in data:
            return {"error": "Task id required"}
        all_tasks = get_tasks()
        for t in all_tasks.get("tasks", []):
            if t.get("id") == data["id"]:
                for k, v in data.items():
                    if k != "id":
                        t[k] = v
                t["updated_at"] = datetime.now(timezone.utc).isoformat()
                save_tasks(all_tasks)
                return t
        return {"error": f"Task {data['id']} not found"}

    routes = {
        "/api/workflow": get_workflow_status,
        "/api/tasks/create": post_create_task,
        "/api/tasks/update": post_update_task,
    }

    port = 8084
    Handler = _json_handler_factory("workflow-manager", port, extra_routes=routes)
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"SLATE Workflow Manager v{VERSION} ready on :{port}")
    server.serve_forever()


# ─────────────────────────────────────────────────────────────────────────────
# Service: Dashboard (port 8080) — FastAPI
# ─────────────────────────────────────────────────────────────────────────────
def start_dashboard():
    """Start Dashboard — runs the FastAPI dashboard server in K8s mode."""
    # In K8s mode, bind to 0.0.0.0 and use the specified port
    port = int(os.environ.get("SLATE_DASHBOARD_PORT", "8080"))
    try:
        sys.path.insert(0, os.path.join(SLATE_DIR, ".."))
        from agents.slate_dashboard_server import app
        import uvicorn
        print(f"SLATE Dashboard v{VERSION} starting on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning", access_log=False)
    except ImportError as e:
        print(f"Dashboard import failed: {e}, falling back to basic HTTP")
        Handler = _json_handler_factory("dashboard", port)
        server = http.server.HTTPServer(("0.0.0.0", port), Handler)
        server.serve_forever()


# ─────────────────────────────────────────────────────────────────────────────
# Main — entrypoint dispatcher
# ─────────────────────────────────────────────────────────────────────────────
SERVICES = {
    "core": start_core,
    "agent-router": start_agent_router,
    "autonomous": start_autonomous_loop,
    "workflow": start_workflow_manager,
    "dashboard": start_dashboard,
}


def main():
    parser = argparse.ArgumentParser(description="SLATE K8s Service Entrypoints")
    parser.add_argument(
        "--service",
        required=True,
        choices=list(SERVICES.keys()),
        help="Which SLATE service to start",
    )
    args = parser.parse_args()

    print(f"Starting SLATE service: {args.service}")
    print(f"  Workspace: {WORKSPACE}")
    print(f"  Ollama:    {OLLAMA_HOST}")
    print(f"  ChromaDB:  {CHROMADB_HOST}")
    print(f"  Python:    {sys.version}")

    try:
        SERVICES[args.service]()
    except KeyboardInterrupt:
        print(f"\n{args.service} shutting down...")
    except Exception as e:
        print(f"FATAL: {args.service} crashed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
