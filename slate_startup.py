#!/usr/bin/env python3
# Modified: 2026-02-10T15:00:00Z | Author: COPILOT | Change: Add Docker auto-deployment on startup
"""
SLATE Startup Script for VSCode Integration
============================================
Automatically starts SLATE services when VSCode opens the workspace.

Usage:
    python slate_startup.py              # Start all services (auto-detects Docker)
    python slate_startup.py --docker     # Force Docker deployment
    python slate_startup.py --local      # Force local-only (no Docker)
    python slate_startup.py --stop       # Stop all services
    python slate_startup.py --status     # Check status
    python slate_startup.py --quick      # Quick start (dashboard only)
"""

import argparse
import subprocess
import sys
import os
import time
import socket
import json
from pathlib import Path
from datetime import datetime

# Workspace root
WORKSPACE = Path(__file__).parent
PYTHON = WORKSPACE / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = WORKSPACE / ".venv" / "bin" / "python"

# Service ports
DASHBOARD_PORT = 8080
OLLAMA_PORT = 11434

# PID file for tracking
PID_FILE = WORKSPACE / ".slate_startup.pid"
STATE_FILE = WORKSPACE / ".slate_startup_state.json"


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is open (service running)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def run_command(args: list[str], background: bool = False) -> subprocess.CompletedProcess | subprocess.Popen:
    """Run a command with proper encoding."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(WORKSPACE)
    env["SLATE_WORKSPACE"] = str(WORKSPACE)

    if background:
        return subprocess.Popen(
            args,
            cwd=str(WORKSPACE),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
    else:
        return subprocess.run(
            args,
            cwd=str(WORKSPACE),
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )


def save_state(state: dict):
    """Save startup state to file."""
    state["timestamp"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_state() -> dict:
    """Load startup state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def start_dashboard() -> bool:
    """Start the SLATE dashboard server."""
    if is_port_open(DASHBOARD_PORT):
        print(f"  Dashboard: Already running on port {DASHBOARD_PORT}")
        return True

    print(f"  Dashboard: Starting on port {DASHBOARD_PORT}...")
    try:
        # Modified: 2026-02-11T03:30:00Z | Author: COPILOT | Change: Use Athena server as sole dashboard
        proc = run_command([str(PYTHON), "agents/slate_athena_server.py"], background=True)

        # Wait for startup
        for _ in range(10):
            time.sleep(0.5)
            if is_port_open(DASHBOARD_PORT):
                print(f"  Dashboard: [OK] Running at http://127.0.0.1:{DASHBOARD_PORT}")
                return True

        print(f"  Dashboard: [WARN] Started but port not responding yet")
        return True
    except Exception as e:
        print(f"  Dashboard: [FAIL] {e}")
        return False


def check_ollama() -> bool:
    """Check if Ollama is running."""
    if is_port_open(OLLAMA_PORT):
        print(f"  Ollama:    [OK] Running on port {OLLAMA_PORT}")
        return True
    else:
        print(f"  Ollama:    [-] Not running (optional)")
        return False


def check_gpu() -> dict:
    """Check GPU availability."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpus.append({"name": parts[0], "memory": parts[1]})
            return {"available": True, "count": len(gpus), "gpus": gpus}
    except Exception:
        pass
    return {"available": False, "count": 0, "gpus": []}


def is_docker_available() -> bool:
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def is_slate_container_running() -> bool:
    """Check if SLATE container is already running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=slate", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "slate" in result.stdout
    except Exception:
        return False


def start_docker_services(use_gpu: bool = True) -> bool:
    """Start SLATE via Docker Compose."""
    compose_file = WORKSPACE / "docker-compose.yml"
    if not compose_file.exists():
        print("  Docker:    [FAIL] docker-compose.yml not found")
        return False

    if is_slate_container_running():
        print("  Docker:    [OK] SLATE container already running")
        return True

    print("  Docker:    Building and starting SLATE container...")
    
    try:
        # Build the image first
        build_result = subprocess.run(
            ["docker", "compose", "build", "--quiet"],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=300  # 5 min for build
        )
        
        if build_result.returncode != 0:
            print(f"  Docker:    [WARN] Build issues: {build_result.stderr[:200] if build_result.stderr else 'unknown'}")
        
        # Start services
        start_result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if start_result.returncode == 0:
            # Wait for container to be healthy
            for _ in range(20):
                time.sleep(1)
                if is_port_open(DASHBOARD_PORT):
                    print(f"  Docker:    [OK] SLATE container running at http://127.0.0.1:{DASHBOARD_PORT}")
                    return True
            
            print("  Docker:    [WARN] Container started but dashboard not responding yet")
            return True
        else:
            print(f"  Docker:    [FAIL] {start_result.stderr[:200] if start_result.stderr else 'Failed to start'}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  Docker:    [FAIL] Timeout waiting for Docker")
        return False
    except Exception as e:
        print(f"  Docker:    [FAIL] {e}")
        return False


def stop_docker_services() -> bool:
    """Stop SLATE Docker containers."""
    if not is_docker_available():
        return True
    
    print("  Docker:    Stopping containers...")
    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  Docker:    [OK] Containers stopped")
            return True
        else:
            print(f"  Docker:    [WARN] {result.stderr[:100] if result.stderr else 'Stop incomplete'}")
            return False
    except Exception as e:
        print(f"  Docker:    [FAIL] {e}")
        return False


def start_services(use_docker: bool | None = None):
    """Start all SLATE services."""
    print()
    print("=" * 50)
    print("  S.L.A.T.E. Starting...")
    print("=" * 50)
    print()

    state = {"services": {}}

    # Check GPU
    gpu = check_gpu()
    if gpu["available"]:
        print(f"  GPU:       [OK] {gpu['count']} GPU(s) detected")
        for g in gpu["gpus"]:
            print(f"             - {g['name']} ({g['memory']})")
    else:
        print("  GPU:       [-] No NVIDIA GPU detected")
    state["gpu"] = gpu

    # Determine whether to use Docker
    docker_available = is_docker_available()
    
    if use_docker is None:
        # Auto-detect: prefer Docker if available
        use_docker = docker_available
    
    if use_docker and not docker_available:
        print("  Docker:    [FAIL] Docker requested but not available")
        use_docker = False
    
    if use_docker:
        # Docker mode: Start via Docker Compose
        print("  Mode:      Docker (containerized)")
        state["mode"] = "docker"
        state["services"]["docker"] = start_docker_services(use_gpu=gpu["available"])
        
        if state["services"]["docker"]:
            # Docker handles everything, just verify services
            state["services"]["dashboard"] = is_port_open(DASHBOARD_PORT)
            state["services"]["ollama"] = is_port_open(OLLAMA_PORT)
        else:
            # Docker failed, fallback to local
            print("  Docker:    Falling back to local mode...")
            state["mode"] = "local"
            state["services"]["dashboard"] = start_dashboard()
            state["services"]["ollama"] = check_ollama()
    else:
        # Local mode: Start services directly
        print("  Mode:      Local (native Python)")
        state["mode"] = "local"
        state["services"]["dashboard"] = start_dashboard()
        state["services"]["ollama"] = check_ollama()

    print()
    print("=" * 50)
    print("  SLATE Ready!")
    print("=" * 50)
    print()
    print(f"  Mode:      {state.get('mode', 'local').upper()}")
    print(f"  Dashboard: http://127.0.0.1:{DASHBOARD_PORT}")
    print()

    save_state(state)
    return 0


def stop_services():
    """Stop all SLATE services."""
    print()
    print("=" * 50)
    print("  S.L.A.T.E. Stopping...")
    print("=" * 50)
    print()

    # Stop Docker containers if running
    if is_docker_available() and is_slate_container_running():
        stop_docker_services()

    # Use orchestrator stop for local services
    try:
        result = run_command([str(PYTHON), "slate/slate_orchestrator.py", "stop"])
        print(result.stdout if result.stdout else "  Local services stopped")
    except Exception as e:
        print(f"  Error stopping services: {e}")

    print()
    print("=" * 50)
    print()

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    return 0


def show_status():
    """Show current SLATE status."""
    print()
    print("=" * 50)
    print("  S.L.A.T.E. Status")
    print("=" * 50)
    print()

    # Docker status
    docker_ok = is_docker_available()
    container_running = is_slate_container_running() if docker_ok else False
    if docker_ok:
        if container_running:
            print("  Docker:    [OK] Container running")
        else:
            print("  Docker:    [OK] Available (container stopped)")
    else:
        print("  Docker:    [-] Not available")

    # Dashboard
    if is_port_open(DASHBOARD_PORT):
        print(f"  Dashboard: [OK] Running on port {DASHBOARD_PORT}")
    else:
        print(f"  Dashboard: [-] Not running")

    # Ollama
    if is_port_open(OLLAMA_PORT):
        print(f"  Ollama:    [OK] Running on port {OLLAMA_PORT}")
    else:
        print(f"  Ollama:    [-] Not running")

    # GPU
    gpu = check_gpu()
    if gpu["available"]:
        print(f"  GPU:       [OK] {gpu['count']} GPU(s) available")
    else:
        print("  GPU:       [-] No NVIDIA GPU")

    # Mode detection
    state = load_state()
    mode = state.get("mode", "unknown")
    if container_running:
        mode = "docker"
    elif is_port_open(DASHBOARD_PORT):
        mode = "local"
    print(f"  Mode:      {mode.upper()}")

    print()
    print("=" * 50)
    print()

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SLATE Startup for VSCode")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--quick", action="store_true", help="Quick start (dashboard only)")
    parser.add_argument("--docker", action="store_true", help="Force Docker deployment")
    parser.add_argument("--local", action="store_true", help="Force local mode (no Docker)")
    args = parser.parse_args()

    if args.stop:
        return stop_services()
    elif args.status:
        return show_status()
    else:
        # Determine Docker mode
        use_docker = None
        if args.docker:
            use_docker = True
        elif args.local:
            use_docker = False
        # Default: auto-detect (prefer Docker if available)
        return start_services(use_docker=use_docker)


if __name__ == "__main__":
    sys.exit(main())
