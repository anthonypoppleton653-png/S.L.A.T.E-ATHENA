#!/usr/bin/env python3
# Modified: 2026-02-06T12:00:00Z | Author: COPILOT | Change: Create SLATE VSCode auto-start script
"""
SLATE Startup Script for VSCode Integration
============================================
Automatically starts SLATE services when VSCode opens the workspace.

Usage:
    python slate_startup.py          # Start all services
    python slate_startup.py --stop   # Stop all services
    python slate_startup.py --status # Check status
    python slate_startup.py --quick  # Quick start (dashboard only)
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
        proc = run_command([str(PYTHON), "agents/slate_dashboard_server.py"], background=True)

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


def start_services():
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

    # Start dashboard
    state["services"]["dashboard"] = start_dashboard()

    # Check Ollama (don't start, just check)
    state["services"]["ollama"] = check_ollama()

    print()
    print("=" * 50)
    print("  SLATE Ready!")
    print("=" * 50)
    print()
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

    # Use orchestrator stop if available
    try:
        result = run_command([str(PYTHON), "slate/slate_orchestrator.py", "stop"])
        print(result.stdout if result.stdout else "  Services stopped")
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
    args = parser.parse_args()

    if args.stop:
        return stop_services()
    elif args.status:
        return show_status()
    else:
        return start_services()


if __name__ == "__main__":
    sys.exit(main())
