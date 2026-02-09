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
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Container-aware status checks
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
IS_DOCKER = os.environ.get("SLATE_DOCKER") == "1"

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
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Use torch.cuda in Docker
    if IS_DOCKER:
        try:
            import torch
            if torch.cuda.is_available():
                gpus = []
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    gpus.append({
                        "name": props.name,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "memory_total": f"{props.total_mem // (1024**2)} MiB",
                        "memory_free": "N/A"
                    })
                return {"available": True, "count": len(gpus), "gpus": gpus}
            return {"available": False, "count": 0, "gpus": []}
        except (ImportError, Exception):
            return {"available": False, "count": 0, "gpus": []}
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
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Use HTTP in Docker/K8s
    if IS_DOCKER:
        try:
            host = os.environ.get("OLLAMA_HOST", "localhost:11434")
            if not host.startswith("http"):
                host = f"http://{host}"
            req = urllib.request.urlopen(f"{host}/api/tags", timeout=5)
            data = json.loads(req.read().decode())
            models = [m.get("name", "unknown") for m in data.get("models", [])]
            return {"available": True, "model_count": len(models), "models": models[:10]}
        except Exception:
            return {"available": False, "model_count": 0}
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


# Modified: 2026-02-09T02:52:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Add Antigravity plugin status
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
def get_antigravity_info():
    """Check Antigravity plugin status."""
    try:
        # Find plugin relative to workspace
        workspace = Path(os.environ.get("SLATE_WORKSPACE", str(Path(__file__).parent.parent)))
        plugin_json = workspace / "plugins" / "slate-antigravity" / "plugin.json"
        forge_path = workspace / "FORGE.md"
        prompts_dir = workspace / "prompts"

        if not plugin_json.exists():
            return {"installed": False, "reason": "plugin.json not found"}

        plugin_data = json.loads(plugin_json.read_text(encoding="utf-8"))
        version = plugin_data.get("version", "unknown")
        web_host = plugin_data.get("web_host", {})

        # FORGE.md status
        forge_entries = 0
        if forge_path.exists():
            content = forge_path.read_text(encoding="utf-8")
            forge_entries = content.count("### [")

        # Prompt count
        prompt_count = len(list(prompts_dir.glob("*.prompt.md"))) if prompts_dir.exists() else 0

        return {
            "installed": True,
            "version": version,
            "agent": plugin_data.get("agent", {}).get("name", "ANTIGRAVITY"),
            "web_host_enabled": web_host.get("enabled", False),
            "copilot_bridge_port": web_host.get("copilot_bridge_port", 8083),
            "forge_entries": forge_entries,
            "prompt_count": prompt_count,
            "models": plugin_data.get("models", {}),
        }
    except Exception as e:
        return {"installed": False, "reason": str(e)}


# Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add Kubernetes cluster info to system status
def get_kubernetes_info():
    """Check Kubernetes cluster status."""
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Container-aware K8s check
    if IS_DOCKER and os.environ.get("SLATE_K8S"):
        sa_token = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if sa_token.exists():
            return {"available": True, "deployments_ready": "in-cluster", "deployments_total": "in-cluster", "pods_running": "in-cluster"}
        return {"available": True, "reason": "SLATE_K8S env set"}
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
        # Modified: 2026-02-09T02:52:00-05:00 | Author: ANTIGRAVITY (Gemini)
        "antigravity": get_antigravity_info(),
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

    # Modified: 2026-02-09T02:52:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Display Antigravity plugin status
    # Antigravity Plugin
    ag = status.get("antigravity", {})
    if ag.get("installed"):
        web = "web" if ag.get("web_host_enabled") else "cli"
        print(f"  Antigrav: {OK} v{ag.get('version', '?')} ({web}, {ag.get('prompt_count', 0)} prompts, {ag.get('forge_entries', 0)} forge)")
    else:
        print(f"  Antigrav: {NONE} Not installed")

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
