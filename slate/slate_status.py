#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# CELL: slate_status [python]
# Author: COPILOT | Created: 2026-02-06T00:30:00Z | Modified: 2026-02-06T00:30:00Z
# Purpose: Quick status check for SLATE system
# ═══════════════════════════════════════════════════════════════════════════════
"""
SLATE Status Checker
====================
Quick system status check.

Usage:
    python slate/slate_status.py --quick
    python slate/slate_status.py --json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_python_info():
    """Get Python version info."""
    version = sys.version_info
    return {
        "version": f"{version.major}.{version.minor}.{version.micro}",
        "executable": sys.executable,
        "ok": version.major >= 3 and version.minor >= 11
    }


def get_gpu_info():
    """Detect NVIDIA GPUs."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,compute_cap,memory.total,memory.free", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append({
                        "name": parts[0],
                        "compute_capability": parts[1],
                        "memory_total": parts[2],
                        "memory_free": parts[3]
                    })
            return {"available": True, "count": len(gpus), "gpus": gpus}
        return {"available": False, "count": 0, "gpus": []}
    except Exception:
        return {"available": False, "count": 0, "gpus": []}


def get_system_info():
    """Get system resource info."""
    if not HAS_PSUTIL:
        return {"available": False}

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path.cwd()))

    return {
        "available": True,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_total_gb": round(mem.total / (1024**3), 1),
        "memory_available_gb": round(mem.available / (1024**3), 1),
        "memory_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_free_gb": round(disk.free / (1024**3), 1)
    }


def get_pytorch_info():
    """Check PyTorch installation."""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        return {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": cuda_available,
            "cuda_version": torch.version.cuda if cuda_available else None,
            "device_count": torch.cuda.device_count() if cuda_available else 0
        }
    except ImportError:
        return {"installed": False}


def get_ollama_info():
    """Check Ollama status."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            models = [line.split()[0] for line in lines[1:] if line.strip()]
            return {"available": True, "model_count": len(models), "models": models[:10]}
        return {"available": False, "model_count": 0}
    except Exception:
        return {"available": False, "model_count": 0}


# Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: Add Semantic Kernel status to system health check
def get_sk_info():
    """Check Semantic Kernel installation."""
    try:
        import semantic_kernel
        return {
            "installed": True,
            "version": semantic_kernel.__version__,
        }
    except ImportError:
        return {"installed": False}


# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Add GitHub Models to system status
def get_github_models_info():
    """Check GitHub Models integration."""
    try:
        from slate.slate_github_models import GitHubModelsClient
        client = GitHubModelsClient()
        if client.authenticated:
            return {
                "available": True,
                "catalog_size": len(client.list_available_models()),
                "total_calls": client.status().get("total_calls", 0),
            }
        return {"available": False, "reason": "no token"}
    except Exception:
        return {"available": False, "reason": "not installed"}


# Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add Kubernetes cluster info to system status
def get_kubernetes_info():
    """Check Kubernetes cluster status."""
    try:
        r = subprocess.run(
            ["kubectl", "get", "deployments", "-n", "slate",
             "-o", "jsonpath={range .items[*]}{.status.readyReplicas}/{.status.replicas} {end}"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if r.returncode == 0 and r.stdout.strip():
            pairs = r.stdout.strip().split()
            total = len(pairs)
            ready = sum(1 for p in pairs if p.split("/")[0] == p.split("/")[1])
            # Get pod count
            pods = subprocess.run(
                ["kubectl", "get", "pods", "-n", "slate", "--field-selector=status.phase=Running",
                 "-o", "jsonpath={.items[*].metadata.name}"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace"
            )
            pod_count = len(pods.stdout.strip().split()) if pods.stdout.strip() else 0
            return {
                "available": True,
                "deployments_ready": ready,
                "deployments_total": total,
                "pods_running": pod_count,
            }
        return {"available": False, "reason": "no slate namespace"}
    except FileNotFoundError:
        return {"available": False, "reason": "kubectl not found"}
    except Exception:
        return {"available": False, "reason": "cluster unreachable"}


def get_status():
    """Get full system status."""
    return {
        "timestamp": datetime.now().isoformat(),
        "python": get_python_info(),
        "gpu": get_gpu_info(),
        "system": get_system_info(),
        "pytorch": get_pytorch_info(),
        "ollama": get_ollama_info(),
        "semantic_kernel": get_sk_info(),
        "github_models": get_github_models_info(),
        "kubernetes": get_kubernetes_info(),
    }


def print_quick_status(status: dict):
    """Print quick status summary."""
    # Use ASCII-safe icons for Windows console compatibility
    OK = "[OK]"
    FAIL = "[X]"
    NONE = "[-]"

    print()
    print("=" * 50)
    print("  S.L.A.T.E. Status")
    print("=" * 50)
    print()

    # Python
    py = status["python"]
    icon = OK if py["ok"] else FAIL
    print(f"  Python:   {icon} {py['version']}")

    # GPU
    gpu = status["gpu"]
    if gpu["available"]:
        print(f"  GPU:      {OK} {gpu['count']} NVIDIA GPU(s)")
        for g in gpu["gpus"]:
            print(f"            - {g['name']} ({g['memory_total']})")
    else:
        print(f"  GPU:      {NONE} CPU-only mode")

    # System
    sys_info = status["system"]
    if sys_info.get("available"):
        print(f"  CPU:      {sys_info['cpu_count']} cores ({sys_info['cpu_percent']}% used)")
        print(f"  Memory:   {sys_info['memory_available_gb']}/{sys_info['memory_total_gb']} GB free")
        print(f"  Disk:     {sys_info['disk_free_gb']}/{sys_info['disk_total_gb']} GB free")

    # PyTorch
    pt = status["pytorch"]
    if pt.get("installed"):
        cuda_status = f"CUDA {pt['cuda_version']}" if pt.get("cuda_available") else "CPU"
        print(f"  PyTorch:  {OK} {pt['version']} ({cuda_status})")
    else:
        print(f"  PyTorch:  {NONE} Not installed")

    # Ollama
    ollama = status["ollama"]
    if ollama.get("available"):
        print(f"  Ollama:   {OK} {ollama['model_count']} models")
    else:
        print(f"  Ollama:   {NONE} Not available")

    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: Display Semantic Kernel in quick status
    # Semantic Kernel
    sk = status.get("semantic_kernel", {})
    if sk.get("installed"):
        print(f"  SK:       {OK} v{sk['version']}")
    else:
        print(f"  SK:       {NONE} Not installed")

    # Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Display GitHub Models in quick status
    # GitHub Models
    gm = status.get("github_models", {})
    if gm.get("available"):
        print(f"  GH Model: {OK} {gm.get('catalog_size', 0)} models ({gm.get('total_calls', 0)} calls)")
    else:
        print(f"  GH Model: {NONE} Not available")

    # Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Display Kubernetes in quick status
    # Kubernetes
    k8s = status.get("kubernetes", {})
    if k8s.get("available"):
        print(f"  K8s:      {OK} {k8s.get('deployments_ready', 0)}/{k8s.get('deployments_total', 0)} deploys ({k8s.get('pods_running', 0)} pods)")
    else:
        print(f"  K8s:      {NONE} Not available")

    print()
    print("=" * 50)
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SLATE Status Checker")
    parser.add_argument("--quick", action="store_true", help="Quick status")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    status = get_status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print_quick_status(status)

    return 0


if __name__ == "__main__":
    sys.exit(main())
