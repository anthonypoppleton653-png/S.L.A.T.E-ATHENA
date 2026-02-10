#!/usr/bin/env python3
"""SLATE-ATHENA Dashboard Server — Greek-themed control board for SLATE.
# Modified: 2026-02-10T14:30:00Z | Author: COPILOT | Change: Set default port to 8080 for clean access

Runs on port 8080 by default. Uses Jinja2 templates + static files for a clean,
modular architecture separate from the monolithic main dashboard.

Architecture:
    agents/slate_athena_server.py           ← This file (FastAPI entry point)
    agents/dashboards/slate_athena/
        templates/index.html                ← Jinja2 template (Greek-themed control board)
        static/css/main.css                 ← Greek-inspired dark color scheme
        static/js/main.js                   ← Dashboard logic, WebSocket, monitoring
        static/js/graph.js                  ← D3.js force-directed system graph
"""

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# ─── Workspace ────────────────────────────────────────────────────────────────

WORKSPACE = Path(__file__).resolve().parent.parent
TASKS_FILE = WORKSPACE / "current_tasks.json"
ATHENA_DIR = Path(__file__).resolve().parent / "dashboards" / "slate_athena"

# ─── Dependencies ─────────────────────────────────────────────────────────────

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("[!] Missing dependencies. Run: pip install fastapi uvicorn jinja2 aiofiles")
    sys.exit(1)

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="SLATE-ATHENA", version="0.1.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=str(ATHENA_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(ATHENA_DIR / "templates"))

# ─── Service URLs ─────────────────────────────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = f"http://{OLLAMA_URL}"

CHROMADB_URL = os.environ.get("CHROMADB_HOST", "http://127.0.0.1:8000")
if not CHROMADB_URL.startswith("http"):
    CHROMADB_URL = f"http://{CHROMADB_URL}"

# ─── WebSocket connections ────────────────────────────────────────────────────

_ws_clients: list[WebSocket] = []


async def _broadcast(data: dict):
    """Broadcast JSON to all connected WebSocket clients."""
    dead = []
    msg = json.dumps(data)
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_tasks() -> list[dict]:
    """Load tasks from current_tasks.json."""
    if TASKS_FILE.exists():
        try:
            data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("tasks", [])
        except Exception:
            pass
    return []


def _run_cmd(args: list[str], timeout: int = 10) -> str:
    """Run a command and return stdout."""
    try:
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            cwd=str(WORKSPACE), encoding="utf-8", errors="replace"
        )
        return r.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def _get_python() -> str:
    """Get the venv python path."""
    venv = WORKSPACE / ".venv" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable


def _http_get_json(url: str, timeout: float = 3.0) -> dict | None:
    """Quick HTTP GET returning parsed JSON, or None on failure."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Serve the SLATE-ATHENA control board."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok", "service": "slate-athena", "timestamp": time.time()}


@app.get("/api/status")
def api_status():
    """System status summary."""
    try:
        output = _run_cmd([_get_python(), "slate/slate_status.py", "--json"], timeout=15)
        return JSONResponse(json.loads(output))
    except Exception:
        return JSONResponse({"error": "Status check failed"}, status_code=500)


@app.get("/api/tasks")
def api_tasks():
    """Current task list."""
    tasks = _load_tasks()
    summary = {
        "total": len(tasks),
        "pending": sum(1 for t in tasks if t.get("status") == "pending"),
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "completed": sum(1 for t in tasks if t.get("status") == "completed"),
    }
    return {"tasks": tasks, "summary": summary}


@app.get("/api/gpu")
def api_gpu():
    """GPU information via nvidia-smi."""
    try:
        out = _run_cmd([
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], timeout=5)
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "memory_total": int(parts[2]),
                    "memory_used": int(parts[3]),
                    "memory_free": int(parts[4]),
                    "utilization": int(parts[5]),
                    "temperature": int(parts[6]),
                })
        return {"gpus": gpus}
    except Exception as e:
        return {"gpus": [], "error": str(e)}


@app.get("/api/ollama")
def api_ollama():
    """Ollama model list and status."""
    data = _http_get_json(f"{OLLAMA_URL}/api/tags")
    if data:
        models = []
        for m in data.get("models", []):
            models.append({
                "name": m.get("name", "unknown"),
                "size": m.get("size", 0),
                "modified": m.get("modified_at", ""),
                "family": m.get("details", {}).get("family", ""),
                "parameters": m.get("details", {}).get("parameter_size", ""),
            })
        return {"available": True, "models": models, "count": len(models)}
    return {"available": False, "models": [], "count": 0}


@app.get("/api/runner")
def api_runner():
    """GitHub Actions runner status."""
    runner_dir = WORKSPACE / "actions-runner"
    if not runner_dir.exists():
        return {"installed": False}
    # Check if runner process is active
    running = False
    try:
        out = _run_cmd(["powershell", "-Command",
                        "Get-Process -Name Runner.Worker -ErrorAction SilentlyContinue | Select-Object -First 1 Id"],
                       timeout=5)
        running = bool(out.strip())
    except Exception:
        pass
    return {"installed": True, "running": running, "path": str(runner_dir)}


@app.get("/api/services")
def api_services():
    """Check reachability of key SLATE services."""
    services = {}
    checks = {
        "ollama": f"{OLLAMA_URL}/api/tags",
        "chromadb": f"{CHROMADB_URL}/api/v2/heartbeat",
        "dashboard": "http://127.0.0.1:8080/health",
    }
    for name, url in checks.items():
        resp = _http_get_json(url, timeout=2)
        services[name] = {"status": "active" if resp is not None else "inactive", "url": url}
    return {"services": services}


@app.get("/api/graph")
def api_graph():
    """System topology graph data for D3.js force layout."""
    # Nodes represent SLATE components
    nodes = [
        {"id": "core", "label": "SLATE Core", "group": "core", "size": 30},
        {"id": "dashboard", "label": "Dashboard", "group": "ui", "size": 20},
        {"id": "athena", "label": "ATHENA", "group": "ui", "size": 22},
        {"id": "ollama", "label": "Ollama", "group": "ai", "size": 25},
        {"id": "chromadb", "label": "ChromaDB", "group": "data", "size": 18},
        {"id": "runner", "label": "GH Runner", "group": "ci", "size": 20},
        {"id": "gpu0", "label": "GPU 0", "group": "hardware", "size": 22},
        {"id": "gpu1", "label": "GPU 1", "group": "hardware", "size": 22},
        {"id": "orchestrator", "label": "Orchestrator", "group": "core", "size": 20},
        {"id": "workflow", "label": "Workflows", "group": "core", "size": 18},
        {"id": "autonomous", "label": "Autonomous", "group": "ai", "size": 18},
        {"id": "k8s", "label": "Kubernetes", "group": "infra", "size": 22},
    ]
    # Links represent connections between components
    links = [
        {"source": "core", "target": "dashboard", "type": "serves"},
        {"source": "core", "target": "athena", "type": "serves"},
        {"source": "core", "target": "orchestrator", "type": "manages"},
        {"source": "orchestrator", "target": "runner", "type": "starts"},
        {"source": "orchestrator", "target": "dashboard", "type": "starts"},
        {"source": "orchestrator", "target": "workflow", "type": "monitors"},
        {"source": "ollama", "target": "gpu0", "type": "uses"},
        {"source": "ollama", "target": "gpu1", "type": "uses"},
        {"source": "ollama", "target": "chromadb", "type": "RAG"},
        {"source": "autonomous", "target": "ollama", "type": "infers"},
        {"source": "autonomous", "target": "workflow", "type": "discovers"},
        {"source": "runner", "target": "core", "type": "CI/CD"},
        {"source": "k8s", "target": "core", "type": "deploys"},
        {"source": "k8s", "target": "ollama", "type": "hosts"},
        {"source": "k8s", "target": "chromadb", "type": "hosts"},
    ]
    return {"nodes": nodes, "links": links}


@app.get("/api/system/resources")
def api_resources():
    """System resource usage (CPU, memory, disk)."""
    import shutil
    resources: dict = {}
    try:
        import psutil
        resources["cpu"] = {"percent": psutil.cpu_percent(interval=0.5), "count": psutil.cpu_count()}
        mem = psutil.virtual_memory()
        resources["memory"] = {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "percent": mem.percent,
        }
    except ImportError:
        resources["cpu"] = {"percent": 0, "count": 0}
        resources["memory"] = {"total_gb": 0, "used_gb": 0, "percent": 0}
    try:
        disk = shutil.disk_usage(str(WORKSPACE))
        resources["disk"] = {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": round(disk.used / disk.total * 100, 1),
        }
    except Exception:
        resources["disk"] = {"total_gb": 0, "used_gb": 0, "percent": 0}
    return resources


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


# ─── Background broadcast loop ───────────────────────────────────────────────

async def _periodic_broadcast():
    """Push system updates to WebSocket clients every 10 seconds."""
    while True:
        await asyncio.sleep(10)
        if not _ws_clients:
            continue
        try:
            tasks = _load_tasks()
            gpu_data = api_gpu()
            payload = {
                "type": "update",
                "tasks_count": len(tasks),
                "tasks_pending": sum(1 for t in tasks if t.get("status") == "pending"),
                "gpus": gpu_data.get("gpus", []) if isinstance(gpu_data, dict) else [],
                "timestamp": time.time(),
            }
            await _broadcast(payload)
        except Exception:
            pass


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(_periodic_broadcast())


# ─── CLI ──────────────────────────────────────────────────────────────────────

# Modified: 2026-02-10T01:45:00Z | Author: COPILOT | Change: Enable SO_REUSEADDR so TIME_WAIT sockets don't block port reuse
def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def main():
    parser = argparse.ArgumentParser(description="SLATE-ATHENA Dashboard")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default=None)
    args = parser.parse_args()

    host = args.host or "127.0.0.1"

    # Find available port
    port = args.port
    if not _is_port_available(host, port):
        for p in range(port + 1, port + 20):
            if _is_port_available(host, p):
                print(f"  [NOTE] Port {port} in use, using {p}")
                port = p
                break
        else:
            print(f"  [ERROR] No available ports (tried {args.port}-{args.port + 19})")
            sys.exit(1)

    print()
    print("=" * 60)
    print("  S.L.A.T.E. ATHENA Dashboard")
    print("  Greek-Themed Control Board")
    print("=" * 60)
    print()
    print(f"  URL:       http://{host}:{port}")
    print(f"  WebSocket: ws://{host}:{port}/ws")
    print()
    print("  Press Ctrl+C to stop")
    print()

    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
