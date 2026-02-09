#!/usr/bin/env python3
# Modified: 2026-02-09T04:00:00Z | Author: Claude Opus 4.5 | Change: Fork sync and analysis system
"""
SLATE Fork Sync System
=======================

Manages forked dependencies, syncs with upstream, and analyzes
changes that could benefit SLATE integrations.

Forked Repositories:
- openai/openai-agents-python  -> Multi-agent workflows
- microsoft/semantic-kernel    -> LLM orchestration
- microsoft/autogen           -> Agentic AI framework
- microsoft/onnxruntime       -> ML inference
- nvidia/TensorRT-LLM         -> LLM optimization
- nvidia/NeMo-Agent-Toolkit   -> Agent framework
- nvidia/Megatron-LM          -> Large model training
- nvidia/nvidia-container-toolkit -> GPU containers

Usage:
    python slate/slate_fork_sync.py --status      # Check fork status
    python slate/slate_fork_sync.py --sync-all    # Sync all forks with upstream
    python slate/slate_fork_sync.py --analyze     # Analyze upstream changes
    python slate/slate_fork_sync.py --recommend   # AI recommendations for integrations
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# K8s-aware Ollama URL
def _normalize_url(host: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"http://{host}"

OLLAMA_URL = _normalize_url(os.environ.get("OLLAMA_HOST", "127.0.0.1:11434"))


@dataclass
class ForkInfo:
    """Information about a forked repository."""
    name: str
    upstream: str  # e.g., "openai/openai-agents-python"
    fork: str      # e.g., "SynchronizedLivingArchitecture/openai-agents-python"
    purpose: str   # What SLATE uses this for
    submodule_path: Optional[str] = None  # Path in vendor/ if cloned
    integration_files: List[str] = None  # SLATE files that integrate with this

    def __post_init__(self):
        if self.integration_files is None:
            self.integration_files = []


# Registry of all forked dependencies
FORK_REGISTRY: List[ForkInfo] = [
    ForkInfo(
        name="openai-agents-python",
        upstream="openai/openai-agents-python",
        fork="SynchronizedLivingArchitecture/openai-agents-python",
        purpose="Multi-agent workflow orchestration patterns",
        submodule_path="vendor/openai-agents-python",
        integration_files=["slate/slate_unified_autonomous.py", "slate/guided_workflow.py"]
    ),
    ForkInfo(
        name="semantic-kernel",
        upstream="microsoft/semantic-kernel",
        fork="SynchronizedLivingArchitecture/semantic-kernel",
        purpose="LLM orchestration, skills, and memory",
        submodule_path="vendor/semantic-kernel",
        integration_files=["slate/slate_semantic_kernel.py"]
    ),
    ForkInfo(
        name="autogen",
        upstream="microsoft/autogen",
        fork="SynchronizedLivingArchitecture/autogen",
        purpose="Multi-agent conversations and code execution",
        submodule_path="vendor/autogen",
        integration_files=["slate/slate_unified_autonomous.py"]
    ),
    ForkInfo(
        name="onnxruntime",
        upstream="microsoft/onnxruntime",
        fork="SynchronizedLivingArchitecture/onnxruntime",
        purpose="Cross-platform ML inference optimization",
        integration_files=["slate/foundry_local.py"]
    ),
    ForkInfo(
        name="TensorRT-LLM",
        upstream="nvidia/TensorRT-LLM",
        fork="SynchronizedLivingArchitecture/TensorRT-LLM",
        purpose="High-performance LLM inference on NVIDIA GPUs",
        integration_files=["slate/slate_gpu_manager.py"]
    ),
    ForkInfo(
        name="NeMo-Agent-Toolkit",
        upstream="nvidia/NeMo-Agent-Toolkit",
        fork="SynchronizedLivingArchitecture/NeMo-Agent-Toolkit",
        purpose="Agent team optimization and orchestration",
        integration_files=["slate/slate_unified_autonomous.py"]
    ),
    ForkInfo(
        name="Megatron-LM",
        upstream="nvidia/Megatron-LM",
        fork="SynchronizedLivingArchitecture/Megatron-LM",
        purpose="Large model training at scale",
        integration_files=["slate/slate_model_trainer.py"]
    ),
    ForkInfo(
        name="nvidia-container-toolkit",
        upstream="nvidia/nvidia-container-toolkit",
        fork="SynchronizedLivingArchitecture/nvidia-container-toolkit",
        purpose="GPU container runtime for K8s/Docker",
        integration_files=["k8s/", "Dockerfile"]
    ),
    ForkInfo(
        name="copilot-sdk",
        upstream="github/copilot-sdk",
        fork="SynchronizedLivingArchitecture/copilot-sdk",
        purpose="GitHub Copilot integration and tools",
        submodule_path="vendor/copilot-sdk",
        integration_files=["slate/copilot_sdk_tools.py", "plugins/slate-copilot/"]
    ),
    ForkInfo(
        name="pytorch",
        upstream="pytorch/pytorch",
        fork="SynchronizedLivingArchitecture/pytorch",
        purpose="Deep learning framework",
        integration_files=["slate/slate_gpu_manager.py"]
    ),
    ForkInfo(
        name="transformers",
        upstream="huggingface/transformers",
        fork="SynchronizedLivingArchitecture/transformers",
        purpose="Model loading and inference",
        integration_files=["slate/foundry_local.py"]
    ),
    ForkInfo(
        name="ollama",
        upstream="ollama/ollama",
        fork="SynchronizedLivingArchitecture/ollama",
        purpose="Local LLM inference server",
        integration_files=["slate/foundry_local.py", "slate/unified_ai_backend.py"]
    ),
    ForkInfo(
        name="chroma",
        upstream="chroma-core/chroma",
        fork="SynchronizedLivingArchitecture/chroma",
        purpose="Vector database for RAG",
        integration_files=["slate/slate_chromadb.py"]
    ),
    ForkInfo(
        name="anthropic-sdk-python",
        upstream="anthropic/anthropic-sdk-python",
        fork="SynchronizedLivingArchitecture/anthropic-sdk-python",
        purpose="Claude API integration",
        integration_files=["slate/claude_agent_sdk_integration.py"]
    ),
    ForkInfo(
        name="claude-code",
        upstream="anthropic/claude-code",
        fork="SynchronizedLivingArchitecture/claude-code",
        purpose="Claude Code CLI reference",
        integration_files=["slate/claude_code_manager.py", ".claude/"]
    ),
    ForkInfo(
        name="spec-kit",
        upstream="speckit/spec-kit",
        fork="SynchronizedLivingArchitecture/spec-kit",
        purpose="Specification-driven development",
        submodule_path="vendor/spec-kit",
        integration_files=["slate/slate_spec_kit.py", "specs/"]
    ),
    # === Microsoft 3D / AI Infrastructure (Phase 3) ===
    ForkInfo(
        name="TRELLIS.2",
        upstream="microsoft/TRELLIS.2",
        fork="SynchronizedLivingArchitecture/TRELLIS.2",
        purpose="Image-to-3D asset generation for SLATE avatar system",
        integration_files=["slate/slate_trellis.py", "k8s/trellis2-generator.yaml", "specs/024-trellis-3d-integration/"]
    ),
    ForkInfo(
        name="graphrag",
        upstream="microsoft/graphrag",
        fork="SynchronizedLivingArchitecture/graphrag",
        purpose="Knowledge graph RAG to augment ChromaDB vector search",
        integration_files=["slate/slate_chromadb.py", "slate/slate_graphrag.py"]
    ),
    ForkInfo(
        name="Olive",
        upstream="microsoft/Olive",
        fork="SynchronizedLivingArchitecture/Olive",
        purpose="Hardware-aware model quantization/optimization for dual RTX 5070 Ti",
        integration_files=["slate/slate_model_trainer.py", "models/"]
    ),
    ForkInfo(
        name="agent-framework",
        upstream="microsoft/agent-framework",
        fork="SynchronizedLivingArchitecture/agent-framework",
        purpose="Unified successor to semantic-kernel + autogen for multi-agent orchestration",
        integration_files=["slate/slate_unified_autonomous.py", "slate/vendor_autogen_sdk.py"]
    ),
    ForkInfo(
        name="presidio",
        upstream="microsoft/presidio",
        fork="SynchronizedLivingArchitecture/presidio",
        purpose="NLP-powered PII detection upgrade for SLATE scanner",
        integration_files=["slate/pii_scanner.py"]
    ),
    ForkInfo(
        name="playwright-mcp",
        upstream="microsoft/playwright-mcp",
        fork="SynchronizedLivingArchitecture/playwright-mcp",
        purpose="Browser automation via MCP for testing/validation",
        integration_files=["slate/mcp_server.py", ".mcp.json"]
    ),
    ForkInfo(
        name="LLMLingua",
        upstream="microsoft/LLMLingua",
        fork="SynchronizedLivingArchitecture/LLMLingua",
        purpose="20x prompt compression for 16GB VRAM constraint",
        integration_files=["slate/unified_ai_backend.py", "slate/foundry_local.py"]
    ),
    ForkInfo(
        name="markitdown",
        upstream="microsoft/markitdown",
        fork="SynchronizedLivingArchitecture/markitdown",
        purpose="Document-to-Markdown for RAG ingestion pipeline",
        integration_files=["slate/slate_chromadb.py", "slate/slate_spec_kit.py"]
    ),
]


def get_gh_cli() -> str:
    """Find GitHub CLI executable."""
    gh_path = WORKSPACE_ROOT / ".tools" / "gh.exe"
    return str(gh_path) if gh_path.exists() else "gh"


def run_gh_command(args: List[str], timeout: int = 30) -> Dict[str, Any]:
    """Run a GitHub CLI command and return result."""
    gh = get_gh_cli()
    try:
        result = subprocess.run(
            [gh] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE_ROOT)
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_fork_status(fork: ForkInfo) -> Dict[str, Any]:
    """Check the status of a single fork."""
    result = run_gh_command([
        "repo", "view", fork.fork,
        "--json", "name,updatedAt,defaultBranchRef"
    ])

    if not result["success"]:
        return {"name": fork.name, "status": "error", "error": result.get("error", result.get("stderr"))}

    try:
        data = json.loads(result["stdout"])

        # Check if submodule exists locally
        local_exists = False
        if fork.submodule_path:
            local_path = WORKSPACE_ROOT / fork.submodule_path
            local_exists = local_path.exists() and (local_path / ".git").exists()

        return {
            "name": fork.name,
            "status": "ok",
            "fork": fork.fork,
            "upstream": fork.upstream,
            "purpose": fork.purpose,
            "updated_at": data.get("updatedAt"),
            "default_branch": data.get("defaultBranchRef", {}).get("name", "main"),
            "local_submodule": local_exists,
            "integration_files": fork.integration_files
        }
    except json.JSONDecodeError:
        return {"name": fork.name, "status": "parse_error", "raw": result["stdout"]}


def check_upstream_commits(fork: ForkInfo, limit: int = 5) -> Dict[str, Any]:
    """Check for new commits in upstream that aren't in fork."""
    result = run_gh_command([
        "api", f"repos/{fork.upstream}/commits",
        "--jq", f".[:{limit}] | .[] | {{sha: .sha[:7], message: .commit.message | split(\"\\n\")[0], date: .commit.author.date}}"
    ], timeout=15)

    if not result["success"]:
        return {"name": fork.name, "status": "error", "commits": []}

    commits = []
    for line in result["stdout"].strip().split("\n"):
        if line:
            try:
                commits.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return {
        "name": fork.name,
        "upstream": fork.upstream,
        "recent_commits": commits
    }


def sync_fork_with_upstream(fork: ForkInfo) -> Dict[str, Any]:
    """Sync a fork with its upstream repository."""
    result = run_gh_command([
        "repo", "sync", fork.fork,
        "--source", fork.upstream,
        "--force"
    ], timeout=60)

    return {
        "name": fork.name,
        "synced": result["success"],
        "message": result.get("stdout", "") or result.get("stderr", "")
    }


def update_submodule(fork: ForkInfo) -> Dict[str, Any]:
    """Update a local submodule to latest."""
    if not fork.submodule_path:
        return {"name": fork.name, "status": "no_submodule"}

    submodule_path = WORKSPACE_ROOT / fork.submodule_path
    if not submodule_path.exists():
        return {"name": fork.name, "status": "not_cloned"}

    try:
        result = subprocess.run(
            ["git", "submodule", "update", "--remote", fork.submodule_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(WORKSPACE_ROOT)
        )
        return {
            "name": fork.name,
            "status": "updated" if result.returncode == 0 else "error",
            "output": result.stdout or result.stderr
        }
    except Exception as e:
        return {"name": fork.name, "status": "error", "error": str(e)}


async def analyze_integration_opportunities() -> Dict[str, Any]:
    """Use AI to analyze what features from forks could benefit SLATE."""
    try:
        import httpx

        # Gather fork info
        fork_summary = []
        for fork in FORK_REGISTRY[:5]:  # Limit to top 5 for prompt size
            status = check_fork_status(fork)
            if status.get("status") == "ok":
                commits = check_upstream_commits(fork, limit=3)
                fork_summary.append({
                    "name": fork.name,
                    "purpose": fork.purpose,
                    "recent_changes": [c.get("message", "") for c in commits.get("recent_commits", [])]
                })

        prompt = f"""Analyze these forked dependencies for SLATE (AI development platform):

{json.dumps(fork_summary, indent=2)}

SLATE integrates: Ollama, Semantic Kernel, GitHub Actions, K8s, dual RTX 5070 Ti GPUs.

Identify 3-5 specific features or patterns from these forks that could improve SLATE's:
1. Multi-agent orchestration
2. GPU utilization
3. Local AI inference
4. Workflow automation

Be specific about which fork and what feature."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "mistral-nemo",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 500}
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "analysis": data.get("response", ""),
                    "forks_analyzed": [f["name"] for f in fork_summary]
                }
    except Exception as e:
        pass

    return {
        "success": False,
        "error": "AI analysis unavailable",
        "forks_analyzed": []
    }


def get_all_fork_status() -> Dict[str, Any]:
    """Get status of all registered forks."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_forks": len(FORK_REGISTRY),
        "forks": []
    }

    for fork in FORK_REGISTRY:
        status = check_fork_status(fork)
        results["forks"].append(status)

    # Summary
    ok_count = sum(1 for f in results["forks"] if f.get("status") == "ok")
    results["summary"] = {
        "accessible": ok_count,
        "errors": len(FORK_REGISTRY) - ok_count,
        "with_submodules": sum(1 for f in results["forks"] if f.get("local_submodule"))
    }

    return results


def sync_all_forks() -> Dict[str, Any]:
    """Sync all forks with upstream."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "synced": [],
        "failed": []
    }

    for fork in FORK_REGISTRY:
        print(f"Syncing {fork.name}...", end=" ", flush=True)
        result = sync_fork_with_upstream(fork)

        if result.get("synced"):
            print("OK")
            results["synced"].append(fork.name)
        else:
            print("FAILED")
            results["failed"].append({"name": fork.name, "error": result.get("message", "")})

    return results


def main():
    parser = argparse.ArgumentParser(description="SLATE Fork Sync System")
    parser.add_argument("--status", action="store_true", help="Check status of all forks")
    parser.add_argument("--sync-all", action="store_true", help="Sync all forks with upstream")
    parser.add_argument("--sync", type=str, help="Sync specific fork by name")
    parser.add_argument("--analyze", action="store_true", help="Analyze integration opportunities")
    parser.add_argument("--list", action="store_true", help="List all registered forks")
    parser.add_argument("--upstream", type=str, help="Check upstream commits for a fork")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        print("\nSLATE Forked Dependencies")
        print("=" * 60)
        for fork in FORK_REGISTRY:
            submodule = "[submodule]" if fork.submodule_path else ""
            print(f"\n  {fork.name} {submodule}")
            print(f"    Upstream: {fork.upstream}")
            print(f"    Purpose:  {fork.purpose}")
            if fork.integration_files:
                print(f"    Integrates: {', '.join(fork.integration_files[:3])}")

    elif args.status:
        print("\nChecking fork status...")
        results = get_all_fork_status()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"  SLATE Fork Status ({results['summary']['accessible']}/{results['total_forks']} accessible)")
            print(f"{'='*60}")

            for fork in results["forks"]:
                status = fork.get("status", "unknown")
                icon = "[OK]" if status == "ok" else "[ERR]"
                submodule = " (local)" if fork.get("local_submodule") else ""
                print(f"\n  {icon} {fork['name']}{submodule}")
                if status == "ok":
                    print(f"      Purpose: {fork.get('purpose', 'N/A')}")

    elif args.sync_all:
        print("\nSyncing all forks with upstream...")
        results = sync_all_forks()
        print(f"\nSynced: {len(results['synced'])}, Failed: {len(results['failed'])}")

    elif args.sync:
        fork = next((f for f in FORK_REGISTRY if f.name == args.sync), None)
        if fork:
            print(f"Syncing {fork.name}...")
            result = sync_fork_with_upstream(fork)
            print(f"Result: {'OK' if result.get('synced') else 'FAILED'}")
        else:
            print(f"Fork '{args.sync}' not found")

    elif args.upstream:
        fork = next((f for f in FORK_REGISTRY if f.name == args.upstream), None)
        if fork:
            print(f"\nRecent upstream commits for {fork.name}:")
            result = check_upstream_commits(fork, limit=10)
            for commit in result.get("recent_commits", []):
                print(f"  {commit.get('sha', '?')} - {commit.get('message', 'No message')}")
        else:
            print(f"Fork '{args.upstream}' not found")

    elif args.analyze:
        import asyncio
        print("\nAnalyzing integration opportunities...")
        result = asyncio.run(analyze_integration_opportunities())
        if result.get("success"):
            print("\n" + result.get("analysis", "No analysis available"))
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
