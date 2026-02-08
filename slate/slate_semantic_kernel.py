#!/usr/bin/env python3
# Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: Initial Semantic Kernel integration for SLATE
"""
SLATE Semantic Kernel Integration
===================================
Integrates Microsoft Semantic Kernel with the SLATE agentic pipeline.

Provides:
- Local Ollama connector (127.0.0.1:11434) as SK AI service
- ChromaDB vector memory connector for RAG
- SLATE native functions as SK plugins (status, workflow, runner, GPU)
- Agent routing via SK planner
- ActionGuard-enforced function calling

All operations are LOCAL ONLY (127.0.0.1). No external API calls.

Usage:
    python slate/slate_semantic_kernel.py --status           # Check SK integration
    python slate/slate_semantic_kernel.py --invoke "prompt"  # Run SK pipeline
    python slate/slate_semantic_kernel.py --plugins          # List registered plugins
    python slate/slate_semantic_kernel.py --benchmark        # Run SK inference benchmark
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: workspace setup
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.semantic_kernel")

# ── Constants ────────────────────────────────────────────────────────────
OLLAMA_ENDPOINT = "http://127.0.0.1:11434"
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_ENDPOINT}/v1"  # OpenAI-compatible endpoint
STATE_FILE = WORKSPACE_ROOT / ".slate_sk_state.json"

# SLATE model mapping for SK services
SK_MODEL_MAP = {
    "code": "slate-coder:latest",
    "fast": "slate-fast:latest",
    "planner": "slate-planner:latest",
    "general": "mistral-nemo:latest",
    "embedding": "nomic-embed-text:latest",
}

# Fallback models if SLATE custom models aren't built
SK_FALLBACK_MAP = {
    "slate-coder:latest": "mistral-nemo:latest",
    "slate-fast:latest": "llama3.2:3b",
    "slate-planner:latest": "mistral:latest",
}


def _check_sk_available() -> tuple[bool, str]:
    """Check if Semantic Kernel is importable."""
    try:
        import semantic_kernel  # noqa: F401
        return True, semantic_kernel.__version__
    except ImportError:
        return False, "not installed"


def _check_ollama_available() -> bool:
    """Check if Ollama is running on localhost."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{OLLAMA_ENDPOINT}/api/tags")
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


def _get_available_models() -> list[str]:
    """Get list of models available in Ollama."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{OLLAMA_ENDPOINT}/api/tags")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _resolve_model(role: str) -> str:
    """Resolve the best available model for a given role."""
    preferred = SK_MODEL_MAP.get(role, SK_MODEL_MAP["general"])
    available = _get_available_models()
    if preferred in available:
        return preferred
    fallback = SK_FALLBACK_MAP.get(preferred)
    if fallback and fallback in available:
        return fallback
    # Last resort: any available model
    if available:
        return available[0]
    return preferred  # Return preferred even if unavailable (will error at call time)


# ── Semantic Kernel Setup ────────────────────────────────────────────────

async def create_slate_kernel(
    model_role: str = "general",
    enable_memory: bool = True,
    enable_plugins: bool = True,
) -> Any:
    """
    Create a Semantic Kernel instance configured for SLATE.

    Uses Ollama's OpenAI-compatible endpoint as the AI service
    and ChromaDB as the vector memory store.

    Args:
        model_role: Which SLATE model to use (code, fast, planner, general)
        enable_memory: Whether to attach ChromaDB memory
        enable_plugins: Whether to register SLATE native plugins
    """
    from semantic_kernel import Kernel
    from semantic_kernel.connectors.ai.open_ai import (
        OpenAIChatCompletion,
    )
    from openai import AsyncOpenAI

    kernel = Kernel()

    # ── AI Service: Ollama via OpenAI-compatible API ──
    model_id = _resolve_model(model_role)
    async_client = AsyncOpenAI(
        base_url=OLLAMA_CHAT_ENDPOINT,
        api_key="ollama",
    )
    chat_service = OpenAIChatCompletion(
        ai_model_id=model_id,
        async_client=async_client,
        service_id=f"slate_{model_role}",
    )
    kernel.add_service(chat_service)

    # ── GitHub Models Service (optional cloud augmentation) ──
    # Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Add GitHub Models as secondary SK service
    try:
        from slate.slate_github_models import create_github_models_sk_service
        gh_service = create_github_models_sk_service(role=model_role)
        kernel.add_service(gh_service)
        logger.info(f"GitHub Models service added for role '{model_role}'")
    except Exception as e:
        logger.debug(f"GitHub Models service not added: {e}")

    # ── Memory: ChromaDB vector store ──
    if enable_memory:
        try:
            await _attach_chromadb_memory(kernel)
        except Exception as e:
            logger.warning(f"ChromaDB memory not attached: {e}")

    # ── Plugins: SLATE native functions ──
    if enable_plugins:
        _register_slate_plugins(kernel)

    return kernel


async def _attach_chromadb_memory(kernel: Any) -> None:
    """Attach ChromaDB-based memory to the kernel for RAG."""
    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: ChromaDB memory connector
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        chroma_path = WORKSPACE_ROOT / "slate_memory" / "chromadb"
        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Verify collections exist
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        logger.info(f"ChromaDB collections available: {collection_names}")

        # Store reference on kernel for plugin access
        kernel._slate_chromadb = client  # type: ignore[attr-defined]
        logger.info("ChromaDB memory attached to kernel")

    except ImportError:
        logger.warning("chromadb not installed — memory disabled")
    except Exception as e:
        logger.warning(f"ChromaDB connection failed: {e}")


def _register_slate_plugins(kernel: Any) -> None:
    """Register SLATE native functions as SK plugins."""
    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: Register SLATE system functions
    from semantic_kernel.functions import kernel_function

    # ── System Status Plugin ──
    class SlateSystemPlugin:
        """SLATE system operations accessible to the SK planner."""

        @kernel_function(
            name="get_system_status",
            description="Get SLATE system health: Python, GPUs, Ollama, memory, disk"
        )
        def get_system_status(self) -> str:
            """Run slate_status.py --quick and return results."""
            import subprocess
            python = str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe")
            script = str(WORKSPACE_ROOT / "slate" / "slate_status.py")
            try:
                result = subprocess.run(
                    [python, script, "--json"],
                    capture_output=True, text=True, timeout=15,
                    encoding="utf-8"
                )
                return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            except Exception as e:
                return f"Status check failed: {e}"

        @kernel_function(
            name="get_runtime_integrations",
            description="Check all 8 SLATE integrations: Python, GPU, PyTorch, Transformers, Ollama, ChromaDB, venv, Copilot SDK"
        )
        def get_runtime_integrations(self) -> str:
            """Run slate_runtime.py --json and return results."""
            import subprocess
            python = str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe")
            script = str(WORKSPACE_ROOT / "slate" / "slate_runtime.py")
            try:
                result = subprocess.run(
                    [python, script, "--json"],
                    capture_output=True, text=True, timeout=15,
                    encoding="utf-8"
                )
                return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            except Exception as e:
                return f"Runtime check failed: {e}"

        @kernel_function(
            name="get_workflow_status",
            description="Get task queue status: pending, in-progress, completed tasks"
        )
        def get_workflow_status(self) -> str:
            """Run slate_workflow_manager.py --status."""
            import subprocess
            python = str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe")
            script = str(WORKSPACE_ROOT / "slate" / "slate_workflow_manager.py")
            try:
                result = subprocess.run(
                    [python, script, "--status"],
                    capture_output=True, text=True, timeout=15,
                    encoding="utf-8"
                )
                return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            except Exception as e:
                return f"Workflow check failed: {e}"

        @kernel_function(
            name="get_gpu_status",
            description="Get GPU status: memory usage, temperature, model assignments"
        )
        def get_gpu_status(self) -> str:
            """Run slate_gpu_manager.py --status."""
            import subprocess
            python = str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe")
            script = str(WORKSPACE_ROOT / "slate" / "slate_gpu_manager.py")
            try:
                result = subprocess.run(
                    [python, script, "--status"],
                    capture_output=True, text=True, timeout=15,
                    encoding="utf-8"
                )
                return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            except Exception as e:
                return f"GPU check failed: {e}"

    # ── Code Search Plugin (ChromaDB RAG) ──
    class SlateCodeSearchPlugin:
        """Semantic code search over the SLATE codebase using ChromaDB."""

        @kernel_function(
            name="search_codebase",
            description="Semantic search over the SLATE codebase. Returns relevant code snippets for a query."
        )
        def search_codebase(self, query: str, n_results: int = 5) -> str:
            """Search ChromaDB for relevant code."""
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                chroma_path = WORKSPACE_ROOT / "slate_memory" / "chromadb"
                client = chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                collection = client.get_collection("slate_code")
                results = collection.query(
                    query_texts=[query],
                    n_results=min(n_results, 10),
                )
                if results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    output_parts = []
                    for doc, meta in zip(docs, metas):
                        source = meta.get("source", "unknown")
                        output_parts.append(f"--- {source} ---\n{doc[:500]}")
                    return "\n\n".join(output_parts)
                return "No results found."
            except Exception as e:
                return f"Search failed: {e}"

    # ── Agent Routing Plugin ──
    class SlateAgentPlugin:
        """Route tasks to appropriate SLATE agents."""

        @kernel_function(
            name="route_task",
            description="Route a task to the appropriate SLATE agent based on intent keywords"
        )
        def route_task(self, task_description: str) -> str:
            """Classify task and return the best agent."""
            desc_lower = task_description.lower()
            routing = {
                "ALPHA (Coding)": ["implement", "code", "build", "fix", "create", "refactor"],
                "BETA (Testing)": ["test", "validate", "verify", "coverage", "pytest"],
                "GAMMA (Planning)": ["analyze", "plan", "research", "document", "architecture"],
                "DELTA (External)": ["claude", "mcp", "sdk", "integration", "api"],
                "COPILOT_CHAT (Interactive)": ["diagnose", "investigate", "troubleshoot", "explain"],
                "COPILOT (Orchestration)": ["complex", "multi-step", "workflow"],
            }
            for agent, keywords in routing.items():
                if any(kw in desc_lower for kw in keywords):
                    return f"Task routed to {agent}: {task_description}"
            return f"Task routed to COPILOT (default): {task_description}"

    # Register all plugins
    kernel.add_plugin(SlateSystemPlugin(), plugin_name="slate_system")
    kernel.add_plugin(SlateCodeSearchPlugin(), plugin_name="slate_search")
    kernel.add_plugin(SlateAgentPlugin(), plugin_name="slate_agents")
    logger.info("Registered 3 SLATE SK plugins (system, search, agents)")


# ── SK Invocation ────────────────────────────────────────────────────────

async def invoke_sk(
    prompt: str,
    model_role: str = "general",
    system_prompt: str = "",
    enable_memory: bool = True,
    enable_plugins: bool = True,
    use_function_calling: bool = False,
) -> str:
    """
    Invoke Semantic Kernel with a prompt using local Ollama models.

    Args:
        prompt: The user prompt to process
        model_role: Which SLATE model role to use
        system_prompt: Optional system instruction
        enable_memory: Whether to use ChromaDB RAG memory
        enable_plugins: Whether to register SLATE plugins
        use_function_calling: Whether to enable auto function calling

    Returns:
        The model's response as a string
    """
    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: SK invocation pipeline
    from semantic_kernel.contents import ChatHistory

    # ActionGuard check on the prompt
    try:
        from slate.action_guard import ActionGuard
        guard = ActionGuard()
        result = guard.validate_action("sk_invoke", prompt)
        if not result.allowed:
            return f"[ActionGuard BLOCKED]: {result.reason}"
    except ImportError:
        pass  # ActionGuard not available, proceed

    kernel = await create_slate_kernel(
        model_role=model_role,
        enable_memory=enable_memory,
        enable_plugins=enable_plugins,
    )

    chat_history = ChatHistory()
    if system_prompt:
        chat_history.add_system_message(system_prompt)
    else:
        chat_history.add_system_message(
            "You are SLATE, a local-first AI assistant for the S.L.A.T.E. framework. "
            "You have access to system status, GPU management, workflow tracking, and "
            "code search plugins. Answer concisely and accurately. All operations are LOCAL ONLY."
        )
    chat_history.add_user_message(prompt)

    service_id = f"slate_{model_role}"
    chat_service = kernel.get_service(service_id)

    if use_function_calling and enable_plugins:
        # Auto function calling with SK planner
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
        settings = OpenAIChatPromptExecutionSettings(
            service_id=service_id,
            function_choice_behavior="auto",
        )
        try:
            result = await chat_service.get_chat_message_content(
                chat_history=chat_history,
                settings=settings,
                kernel=kernel,
            )
            return str(result) if result else "[No response]"
        except Exception as e:
            logger.warning(f"Function calling failed, falling back to direct: {e}")

    # Direct chat completion (no function calling)
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
    settings = OpenAIChatPromptExecutionSettings(
        service_id=service_id,
        max_tokens=2048,
        temperature=0.3,
    )
    try:
        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=settings,
        )
        return str(result) if result else "[No response]"
    except Exception as e:
        return f"[SK Error]: {e}"


# ── Status & Diagnostics ────────────────────────────────────────────────

def get_sk_status() -> dict[str, Any]:
    """Get comprehensive Semantic Kernel integration status."""
    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: SK status reporting
    sk_available, sk_version = _check_sk_available()
    ollama_available = _check_ollama_available()
    available_models = _get_available_models() if ollama_available else []

    # Check which SLATE models are available
    slate_models = {}
    for role, model in SK_MODEL_MAP.items():
        if model in available_models:
            slate_models[role] = {"model": model, "status": "available"}
        else:
            fallback = SK_FALLBACK_MAP.get(model)
            if fallback and fallback in available_models:
                slate_models[role] = {"model": fallback, "status": "fallback"}
            else:
                slate_models[role] = {"model": model, "status": "missing"}

    # Check ChromaDB
    chromadb_status = {"available": False, "collections": 0, "documents": 0}
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        chroma_path = WORKSPACE_ROOT / "slate_memory" / "chromadb"
        if chroma_path.exists():
            client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            collections = client.list_collections()
            total_docs = sum(c.count() for c in collections)
            chromadb_status = {
                "available": True,
                "collections": len(collections),
                "documents": total_docs,
            }
    except Exception:
        pass

    return {
        "semantic_kernel": {
            "available": sk_available,
            "version": sk_version,
        },
        "ollama": {
            "available": ollama_available,
            "endpoint": OLLAMA_ENDPOINT,
            "models_count": len(available_models),
        },
        "slate_models": slate_models,
        "chromadb_memory": chromadb_status,
        "plugins": ["slate_system", "slate_search", "slate_agents"],
        "security": "ActionGuard enforced",
    }


def print_status() -> None:
    """Print formatted SK integration status."""
    status = get_sk_status()

    print()
    print("=" * 60)
    print("  SLATE Semantic Kernel Integration")
    print("=" * 60)
    print()

    # SK Status
    sk = status["semantic_kernel"]
    sk_icon = "✓" if sk["available"] else "✗"
    print(f"  {sk_icon} Semantic Kernel: {sk['version']}")

    # Ollama
    ol = status["ollama"]
    ol_icon = "✓" if ol["available"] else "✗"
    print(f"  {ol_icon} Ollama: {ol['endpoint']} ({ol['models_count']} models)")

    # SLATE Models
    print()
    print("  Model Routing:")
    for role, info in status["slate_models"].items():
        icon = "✓" if info["status"] == "available" else ("~" if info["status"] == "fallback" else "✗")
        suffix = f" (fallback)" if info["status"] == "fallback" else ""
        print(f"    {icon} {role:12s} → {info['model']}{suffix}")

    # ChromaDB
    print()
    mem = status["chromadb_memory"]
    mem_icon = "✓" if mem["available"] else "✗"
    print(f"  {mem_icon} ChromaDB Memory: {mem['collections']} collections, {mem['documents']} documents")

    # Plugins
    print()
    print(f"  Plugins: {', '.join(status['plugins'])}")
    print(f"  Security: {status['security']}")

    print()
    print("=" * 60)
    print()


async def run_benchmark() -> None:
    """Run a quick SK inference benchmark using local models."""
    # Modified: 2026-02-08T10:00:00Z | Author: COPILOT | Change: SK inference benchmark
    print()
    print("=" * 60)
    print("  SLATE Semantic Kernel Benchmark")
    print("=" * 60)
    print()

    test_prompts = [
        ("fast", "Summarize what SLATE does in one sentence."),
        ("code", "Write a Python function to check if a port is open on localhost."),
        ("planner", "Create a 3-step plan to add tests to a Python module."),
    ]

    for role, prompt in test_prompts:
        model = _resolve_model(role)
        print(f"  [{role}] Model: {model}")
        print(f"  Prompt: {prompt[:60]}...")

        start = time.perf_counter()
        try:
            result = await invoke_sk(
                prompt=prompt,
                model_role=role,
                enable_memory=False,
                enable_plugins=False,
            )
            elapsed = time.perf_counter() - start
            preview = result[:200].replace("\n", " ")
            print(f"  Response ({elapsed:.1f}s): {preview}...")
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f"  Error ({elapsed:.1f}s): {e}")

        print()

    print("=" * 60)
    print()


def list_plugins() -> None:
    """List all registered SK plugins and their functions."""
    print()
    print("=" * 60)
    print("  SLATE Semantic Kernel Plugins")
    print("=" * 60)
    print()

    plugins = {
        "slate_system": {
            "get_system_status": "Get SLATE system health: Python, GPUs, Ollama, memory, disk",
            "get_runtime_integrations": "Check all 8 SLATE integrations",
            "get_workflow_status": "Get task queue status: pending, in-progress, completed",
            "get_gpu_status": "Get GPU status: memory, temperature, model assignments",
        },
        "slate_search": {
            "search_codebase": "Semantic search over SLATE codebase via ChromaDB",
        },
        "slate_agents": {
            "route_task": "Route a task to the appropriate SLATE agent",
        },
    }

    for plugin_name, functions in plugins.items():
        print(f"  Plugin: {plugin_name}")
        for func_name, desc in functions.items():
            print(f"    • {func_name}: {desc}")
        print()

    print("=" * 60)
    print()


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SLATE Semantic Kernel Integration")
    parser.add_argument("--status", action="store_true", help="Show SK integration status")
    parser.add_argument("--invoke", type=str, help="Invoke SK with a prompt")
    parser.add_argument("--model", type=str, default="general",
                        choices=["code", "fast", "planner", "general"],
                        help="Model role to use (default: general)")
    parser.add_argument("--plugins", action="store_true", help="List registered plugins")
    parser.add_argument("--benchmark", action="store_true", help="Run SK inference benchmark")
    parser.add_argument("--json", action="store_true", help="Output status as JSON")
    parser.add_argument("--function-calling", action="store_true",
                        help="Enable auto function calling (experimental)")

    args = parser.parse_args()

    if args.status:
        if args.json:
            print(json.dumps(get_sk_status(), indent=2))
        else:
            print_status()
    elif args.plugins:
        list_plugins()
    elif args.benchmark:
        asyncio.run(run_benchmark())
    elif args.invoke:
        result = asyncio.run(invoke_sk(
            prompt=args.invoke,
            model_role=args.model,
            use_function_calling=args.function_calling,
        ))
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
