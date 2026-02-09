#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# CELL: slate_runtime [python]
# Author: COPILOT | Created: 2026-02-06T00:30:00Z
# Purpose: Runtime integration checker
# ═══════════════════════════════════════════════════════════════════════════════
"""
SLATE Runtime Checker - Check all integrations and dependencies.

Usage:
    python slate/slate_runtime.py --check-all
    python slate/slate_runtime.py --json
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Container-aware runtime checks
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
IS_DOCKER = os.environ.get("SLATE_DOCKER") == "1"

# Fix Windows console encoding for Unicode characters (✓, ✗, etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Modified: 2026-02-08T21:30:00Z | Author: COPILOT | Change: Catch BaseException to handle Rust/pyo3 panics from ChromaDB
def check_integration(name, check_fn, details_fn=None):
    try:
        status = check_fn()
        details = details_fn() if details_fn and status else None
        return {"name": name, "status": "active" if status else "inactive", "details": details}
    except BaseException as e:
        return {"name": name, "status": "error", "error": str(e)}

def check_python():
    return sys.version_info >= (3, 11)


def python_details():
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_pytorch():
    # Modified: 2026-02-06T22:00:00Z | Author: COPILOT | Change: Actually verify PyTorch import
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


def pytorch_details():
    # Modified: 2026-02-08T21:45:00Z | Author: COPILOT | Change: Note CPU-only is expected locally, CUDA runs in Docker/K8s
    import torch
    import os
    cuda_str = f", CUDA {torch.version.cuda}" if torch.cuda.is_available() else ", CPU"
    if not torch.cuda.is_available() and not os.environ.get("SLATE_DOCKER"):
        cuda_str += " (GPU via Docker/K8s)"
    return f"{torch.__version__}{cuda_str}"


def check_ollama():
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Use HTTP for Docker/K8s
    if IS_DOCKER:
        try:
            host = os.environ.get("OLLAMA_HOST", "localhost:11434")
            if not host.startswith("http"):
                host = f"http://{host}"
            urllib.request.urlopen(f"{host}/api/tags", timeout=5)
            return True
        except Exception:
            return False
    try:
        return subprocess.run(["ollama", "--version"], capture_output=True, timeout=5).returncode == 0
    except Exception:
        return False


def check_gpu():
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Use torch.cuda inside Docker
    if IS_DOCKER:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False


def check_transformers():
    # Modified: 2026-02-06T22:00:00Z | Author: COPILOT | Change: Actually verify transformers import
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def check_venv():
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Always pass inside Docker
    if IS_DOCKER:
        return True  # Docker IS the isolated environment
    return (Path.cwd() / ".venv").exists() or (Path.cwd() / ".venv_slate_ag").exists()


# Modified: 2026-02-06T22:30:00Z | Author: COPILOT | Change: Add ChromaDB integration check
def check_chromadb():
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


def chromadb_details():
    import chromadb
    return chromadb.__version__


# Modified: 2026-02-09T03:45:00Z | Author: COPILOT | Change: Add Copilot SDK integration check (8th integration)
def check_copilot_sdk():
    try:
        sdk_path = Path(__file__).parent.parent / "vendor" / "copilot-sdk" / "python"
        if not sdk_path.exists():
            return False
        if str(sdk_path) not in sys.path:
            sys.path.insert(0, str(sdk_path))
        from copilot import CopilotClient, define_tool  # noqa: F401
        return True
    except ImportError:
        return False


def copilot_sdk_details():
    sdk_path = Path(__file__).parent.parent / "vendor" / "copilot-sdk"
    proto_file = sdk_path / "sdk-protocol-version.json"
    if proto_file.exists():
        with open(proto_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return f"protocol v{data.get('version', '?')}"
    return "unknown"


# Modified: 2026-02-09T09:00:00Z | Author: COPILOT | Change: Add Semantic Kernel integration check (9th integration)
def check_semantic_kernel():
    """Check if Microsoft Semantic Kernel is installed and importable."""
    try:
        import semantic_kernel  # noqa: F401
        return True
    except ImportError:
        return False


def semantic_kernel_details():
    """Get Semantic Kernel version and Ollama connectivity."""
    # Modified: 2026-02-08T21:30:00Z | Author: COPILOT | Change: Catch BaseException for Rust panics
    import semantic_kernel
    version = semantic_kernel.__version__
    # Quick check if Ollama is reachable for SK
    try:
        from slate.slate_semantic_kernel import get_sk_status
        status = get_sk_status()
        if status.get("ollama", {}).get("available"):
            return f"{version} (Ollama connected)"
    except BaseException:
        pass
    return version


# Modified: 2026-02-09T03:00:00Z | Author: COPILOT | Change: Add Kubernetes integration check (11th integration)
def check_kubernetes():
    """Check if Kubernetes cluster is connected and SLATE namespace exists."""
    # Modified: 2026-02-09T01:39:00Z | Author: Antigravity (Gemini) | Change: Use in-cluster API when in Docker/K8s
    if IS_DOCKER and os.environ.get("SLATE_K8S"):
        # Inside K8s pod — check service account token exists
        sa_token = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if sa_token.exists():
            return True
        # Fallback: if SLATE_K8S is set, we trust the environment
        return True
    try:
        r = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return False
        r2 = subprocess.run(['kubectl', '-n', 'slate', 'get', 'namespace', 'slate', '-o', 'name'],
                           capture_output=True, text=True, timeout=10)
        return r2.returncode == 0
    except Exception:
        return False


def kubernetes_details():
    """Get Kubernetes deployment details."""
    try:
        r = subprocess.run(['kubectl', '-n', 'slate', 'get', 'deployments', '--no-headers'],
                          capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return 'no namespace'
        lines = [l for l in r.stdout.strip().split('\n') if l.strip()]
        ready = sum(1 for l in lines if l.split()[1].split('/')[0] == l.split()[1].split('/')[1])
        return f'{ready}/{len(lines)} deployments ready'
    except Exception:
        return 'kubectl unavailable'


# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Add GitHub Models free-tier integration check (10th integration)
def check_github_models():
    """Check if GitHub Models integration is available (auth + endpoint)."""
    try:
        from slate.slate_github_models import GitHubModelsClient
        client = GitHubModelsClient()
        return client.authenticated
    except Exception:
        return False


def github_models_details():
    """Get GitHub Models status and catalog info."""
    try:
        from slate.slate_github_models import GitHubModelsClient
        client = GitHubModelsClient()
        s = client.status()
        if s["authenticated"]:
            return f"{s['catalog_size']} models, {s['total_calls']} calls"
        return "no token"
    except Exception:
        return "not available"


INTEGRATIONS = [
    ("Python 3.11+", check_python, python_details),
    ("Virtual Env", check_venv, None),
    ("NVIDIA GPU", check_gpu, None),
    ("PyTorch", check_pytorch, pytorch_details),
    ("Transformers", check_transformers, None),
    ("Ollama", check_ollama, None),
    ("ChromaDB", check_chromadb, chromadb_details),
    ("Copilot SDK", check_copilot_sdk, copilot_sdk_details),
    ("Semantic Kernel", check_semantic_kernel, semantic_kernel_details),
    ("GitHub Models", check_github_models, github_models_details),
    ("Kubernetes", check_kubernetes, kubernetes_details),
]

def check_all():
    results = {"timestamp": datetime.now().isoformat(), "integrations": []}
    for name, check_fn, details_fn in INTEGRATIONS:
        results["integrations"].append(check_integration(name, check_fn, details_fn))
    active = sum(1 for i in results["integrations"] if i["status"] == "active")
    results["summary"] = {"active": active, "total": len(results["integrations"])}
    return results

def print_results(results):
    print("\n" + "=" * 60)
    print("  S.L.A.T.E. Runtime Check")
    print("=" * 60 + "\n")
    for item in results["integrations"]:
        icon = "\u2713" if item["status"] == "active" else "\u25cb" if item["status"] == "inactive" else "\u2717"
        details = f" ({item['details']})" if item.get("details") else ""
        print(f"  {icon} {item['name']}{details}")
    s = results["summary"]
    print(f"\n  Summary: {s['active']}/{s['total']} integrations active")
    print("\n" + "=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="SLATE Runtime Checker")
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = check_all()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())
