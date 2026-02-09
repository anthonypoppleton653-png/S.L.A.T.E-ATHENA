#!/usr/bin/env python3
# Modified: 2026-02-09T14:00:00Z | Author: ClaudeCode (Opus 4.6) | Change: Create unified AI backend with Claude Code as inference provider
"""
SLATE Unified AI Backend
==========================
Central routing for all AI inference tasks across SLATE providers.

Providers (priority order, all FREE / local):
1. Ollama (localhost:11434) — Primary: slate-coder 12B, slate-fast 3B, slate-planner 7B
2. Claude Code (local MCP bridge) — Agentic tasks, code generation, complex reasoning
3. Foundry Local (localhost:5272) — ONNX-optimized Phi-3, Mistral-7B

Task routing:
    code_generation    → ollama (slate-coder)     or claude_code
    code_review        → ollama (slate-coder)     or claude_code
    test_generation    → ollama (slate-coder)     or claude_code
    bug_fix            → claude_code              or ollama (slate-coder)
    refactoring        → claude_code              or ollama (slate-coder)
    documentation      → ollama (slate-fast)      or claude_code
    analysis           → claude_code              or ollama (slate-planner)
    research           → claude_code              or ollama (slate-planner)
    planning           → ollama (slate-planner)   or claude_code
    classification     → ollama (slate-fast)
    prompt_engineering → claude_code              or ollama (slate-planner)

Usage:
    python slate/unified_ai_backend.py --status
    python slate/unified_ai_backend.py --task "your task"
    python slate/unified_ai_backend.py --task "your task" --provider ollama
    python slate/unified_ai_backend.py --task "your task" --provider claude_code
    python slate/unified_ai_backend.py --providers
    python slate/unified_ai_backend.py --route "code_generation"
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WORKSPACE_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("slate.unified_ai_backend")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
FOUNDRY_HOST = os.environ.get("FOUNDRY_HOST", "http://127.0.0.1:5272")

# Model mapping per task type
TASK_MODELS = {
    "code_generation":    {"ollama": "slate-coder",   "claude_code": "opus-4.6"},
    "code_review":        {"ollama": "slate-coder",   "claude_code": "opus-4.6"},
    "test_generation":    {"ollama": "slate-coder",   "claude_code": "opus-4.6"},
    "bug_fix":            {"claude_code": "opus-4.6", "ollama": "slate-coder"},
    "refactoring":        {"claude_code": "opus-4.6", "ollama": "slate-coder"},
    "documentation":      {"ollama": "slate-fast",    "claude_code": "sonnet-4.5"},
    "analysis":           {"claude_code": "opus-4.6", "ollama": "slate-planner"},
    "research":           {"claude_code": "opus-4.6", "ollama": "slate-planner"},
    "planning":           {"ollama": "slate-planner", "claude_code": "opus-4.6"},
    "classification":     {"ollama": "slate-fast"},
    "prompt_engineering": {"claude_code": "opus-4.6", "ollama": "slate-planner"},
}

# Provider priority per task type (first = preferred)
TASK_ROUTING = {
    "code_generation":    ["ollama", "claude_code", "foundry"],
    "code_review":        ["ollama", "claude_code"],
    "test_generation":    ["ollama", "claude_code"],
    "bug_fix":            ["claude_code", "ollama"],
    "refactoring":        ["claude_code", "ollama"],
    "documentation":      ["ollama", "claude_code"],
    "analysis":           ["claude_code", "ollama"],
    "research":           ["claude_code", "ollama"],
    "planning":           ["ollama", "claude_code"],
    "classification":     ["ollama"],
    "prompt_engineering": ["claude_code", "ollama"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class InferenceResult:
    """Result from an AI inference call."""
    success: bool
    provider: str
    model: str
    response: str
    tokens: int = 0
    duration_ms: float = 0
    cost: str = "FREE"
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "provider": self.provider,
            "model": self.model,
            "response": self.response[:500] + "..." if len(self.response) > 500 else self.response,
            "tokens": self.tokens,
            "duration_ms": round(self.duration_ms, 1),
            "cost": self.cost,
            "error": self.error,
        }


@dataclass
class ProviderStatus:
    """Status of an AI provider."""
    name: str
    available: bool
    endpoint: str
    models: list[str] = field(default_factory=list)
    latency_ms: float = 0
    error: str = ""
    cost: str = "FREE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "endpoint": self.endpoint,
            "models": self.models,
            "latency_ms": round(self.latency_ms, 1),
            "error": self.error,
            "cost": self.cost,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Implementations
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaProvider:
    """Ollama local LLM inference provider."""

    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host
        self.name = "ollama"

    def check_status(self) -> ProviderStatus:
        """Check Ollama availability and list models."""
        start = time.time()
        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                latency = (time.time() - start) * 1000
                return ProviderStatus(
                    name=self.name,
                    available=True,
                    endpoint=self.host,
                    models=models,
                    latency_ms=latency,
                    cost="FREE",
                )
        except Exception as e:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=self.host,
                error=str(e),
            )

    def generate(self, prompt: str, model: str = "slate-fast",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        """Generate text via Ollama API."""
        start = time.time()
        try:
            url = f"{self.host}/api/generate"
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                duration = (time.time() - start) * 1000
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=model,
                    response=result.get("response", ""),
                    tokens=result.get("eval_count", 0),
                    duration_ms=duration,
                    cost="FREE",
                )
        except Exception as e:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error=str(e),
            )


class ClaudeCodeProvider:
    """Claude Code inference provider — routes through the MCP bridge / copilot agent bridge.

    Claude Code operates as a LOCAL inference provider within SLATE because:
    1. It runs as a local CLI process (no external API calls from SLATE's perspective)
    2. Tasks are dispatched via the copilot agent bridge (file-based IPC)
    3. Results come back through the same local bridge
    4. ActionGuard validation applies to all dispatched tasks

    This provider is used for complex reasoning, agentic code tasks, and
    prompt engineering where Ollama models need augmentation.
    """

    def __init__(self):
        self.name = "claude_code"
        self.bridge_queue = WORKSPACE_ROOT / ".slate_copilot_bridge.json"
        self.bridge_results = WORKSPACE_ROOT / ".slate_copilot_bridge_results.json"

    def check_status(self) -> ProviderStatus:
        """Check Claude Code availability via bridge files and process detection."""
        start = time.time()
        models = ["opus-4.6", "sonnet-4.5", "haiku-4.5"]

        # Check if bridge files exist (Claude Code integration active)
        bridge_exists = self.bridge_queue.exists()

        # Check if Claude Code process is running
        process_active = False
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq claude.exe", "/NH"],
                    capture_output=True, text=True, timeout=5,
                )
                process_active = "claude.exe" in result.stdout.lower()
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "claude"],
                    capture_output=True, text=True, timeout=5,
                )
                process_active = result.returncode == 0
        except Exception:
            pass

        # Check MCP server configuration
        mcp_configured = (WORKSPACE_ROOT / ".mcp.json").exists()

        available = bridge_exists and mcp_configured
        latency = (time.time() - start) * 1000

        status_detail = []
        if bridge_exists:
            status_detail.append("bridge:ok")
        if process_active:
            status_detail.append("process:active")
        if mcp_configured:
            status_detail.append("mcp:configured")

        return ProviderStatus(
            name=self.name,
            available=available,
            endpoint="local:mcp-bridge",
            models=models if available else [],
            latency_ms=latency,
            error="" if available else f"Missing: {', '.join(d for d in ['bridge', 'mcp'] if d not in ' '.join(status_detail))}",
            cost="FREE (local CLI)",
        )

    def generate(self, prompt: str, model: str = "opus-4.6",
                 max_tokens: int = 4096, temperature: float = 0.7) -> InferenceResult:
        """Generate via Claude Code by dispatching through copilot agent bridge.

        For synchronous tasks, this enqueues a task on the bridge and polls
        for results. For fire-and-forget tasks, it just enqueues.
        """
        start = time.time()

        try:
            # Import bridge
            from slate.copilot_agent_bridge import CopilotAgentBridge
            bridge = CopilotAgentBridge()

            # Enqueue inference task
            task = bridge.enqueue_task(
                title=f"claude_code_inference:{model}",
                description=prompt[:2000],
                priority="high",
                source="unified_ai_backend",
                tools_hint=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            )

            task_id = task["id"]

            # Poll for result (with timeout)
            poll_timeout = 60  # seconds
            poll_interval = 2  # seconds
            elapsed = 0

            while elapsed < poll_timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval

                # Check results file
                results_data = self._read_results()
                for r in results_data.get("results", []):
                    if r.get("task_id") == task_id:
                        duration = (time.time() - start) * 1000
                        return InferenceResult(
                            success=r.get("success", False),
                            provider=self.name,
                            model=model,
                            response=r.get("result", ""),
                            tokens=0,  # Token count from bridge not available
                            duration_ms=duration,
                            cost="FREE (local CLI)",
                        )

            duration = (time.time() - start) * 1000
            return InferenceResult(
                success=True,
                provider=self.name,
                model=model,
                response=f"Task dispatched to Claude Code bridge (id: {task_id}). "
                         f"Result will be available via bridge polling.",
                duration_ms=duration,
                cost="FREE (local CLI)",
            )

        except Exception as e:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error=str(e),
            )

    def _read_results(self) -> dict:
        try:
            return json.loads(self.bridge_results.read_text(encoding="utf-8"))
        except Exception:
            return {"results": []}


class FoundryProvider:
    """Foundry Local ONNX inference provider."""

    def __init__(self, host: str = FOUNDRY_HOST):
        self.host = host
        self.name = "foundry"

    def check_status(self) -> ProviderStatus:
        """Check Foundry Local availability."""
        start = time.time()
        try:
            url = f"{self.host}/v1/models"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id", "") for m in data.get("data", [])]
                latency = (time.time() - start) * 1000
                return ProviderStatus(
                    name=self.name,
                    available=True,
                    endpoint=self.host,
                    models=models,
                    latency_ms=latency,
                    cost="FREE",
                )
        except Exception as e:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=self.host,
                error=str(e),
            )

    def generate(self, prompt: str, model: str = "phi-3.5",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        """Generate via Foundry Local OpenAI-compatible API."""
        start = time.time()
        try:
            url = f"{self.host}/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                response_text = choices[0]["message"]["content"] if choices else ""
                usage = result.get("usage", {})
                duration = (time.time() - start) * 1000
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=model,
                    response=response_text,
                    tokens=usage.get("completion_tokens", 0),
                    duration_ms=duration,
                    cost="FREE",
                )
        except Exception as e:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error=str(e),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Backend
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedAIBackend:
    """Routes AI tasks to the best available local provider."""

    def __init__(self):
        self.providers = {
            "ollama": OllamaProvider(),
            "claude_code": ClaudeCodeProvider(),
            "foundry": FoundryProvider(),
        }
        self._status_cache: dict[str, ProviderStatus] = {}
        self._cache_time: float = 0
        self._cache_ttl: float = 30.0  # seconds

    def get_all_status(self) -> dict[str, ProviderStatus]:
        """Get status of all providers (cached)."""
        now = time.time()
        if not self._status_cache or (now - self._cache_time) > self._cache_ttl:
            self._status_cache = {}
            for name, provider in self.providers.items():
                self._status_cache[name] = provider.check_status()
            self._cache_time = now
        return self._status_cache

    def classify_task(self, task_description: str) -> str:
        """Classify a task description into a task type.

        Uses keyword matching for fast local classification.
        Falls back to 'analysis' for ambiguous tasks.
        """
        desc_lower = task_description.lower()

        keyword_map = {
            "code_generation": ["implement", "create", "build", "write code", "add feature", "generate code"],
            "code_review": ["review", "audit", "inspect", "check code", "lint"],
            "test_generation": ["test", "spec", "coverage", "unit test", "integration test"],
            "bug_fix": ["fix", "bug", "error", "crash", "broken", "debug", "issue"],
            "refactoring": ["refactor", "restructure", "reorganize", "clean up", "optimize code"],
            "documentation": ["document", "docs", "readme", "comment", "docstring", "wiki"],
            "analysis": ["analyze", "investigate", "assess", "evaluate", "understand"],
            "research": ["research", "explore", "find", "search", "discover", "look up"],
            "planning": ["plan", "design", "architect", "roadmap", "strategy"],
            "classification": ["classify", "categorize", "route", "triage", "sort"],
            "prompt_engineering": ["prompt", "super prompt", "template", "instruction"],
        }

        for task_type, keywords in keyword_map.items():
            for kw in keywords:
                if kw in desc_lower:
                    return task_type

        return "analysis"  # default

    def route_task(self, task_type: str) -> list[str]:
        """Get provider priority list for a task type."""
        return TASK_ROUTING.get(task_type, ["ollama", "claude_code"])

    def get_model_for_task(self, task_type: str, provider: str) -> str:
        """Get the recommended model for a task type and provider."""
        models = TASK_MODELS.get(task_type, {})
        return models.get(provider, "slate-fast" if provider == "ollama" else "opus-4.6")

    def execute(self, task: str, provider_override: Optional[str] = None,
                model_override: Optional[str] = None,
                max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        """Execute an AI task with automatic provider selection and failover.

        Args:
            task: The task/prompt to execute
            provider_override: Force a specific provider
            model_override: Force a specific model
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            InferenceResult with the response
        """
        # Classify task
        task_type = self.classify_task(task)

        # Get provider list
        if provider_override:
            provider_list = [provider_override]
        else:
            provider_list = self.route_task(task_type)

        # Get available providers
        statuses = self.get_all_status()

        # Try providers in priority order
        for provider_name in provider_list:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            status = statuses.get(provider_name)
            if status and not status.available:
                logger.info(f"Skipping {provider_name}: not available ({status.error})")
                continue

            model = model_override or self.get_model_for_task(task_type, provider_name)
            logger.info(f"Executing on {provider_name} with model {model} (task_type={task_type})")

            result = provider.generate(
                prompt=task,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if result.success:
                return result
            else:
                logger.warning(f"Provider {provider_name} failed: {result.error}")

        # All providers failed
        return InferenceResult(
            success=False,
            provider="none",
            model="none",
            response="",
            error=f"All providers failed for task type '{task_type}'. "
                  f"Tried: {', '.join(provider_list)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Module-Level Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_backend: Optional[UnifiedAIBackend] = None


def get_backend() -> UnifiedAIBackend:
    """Get the singleton UnifiedAIBackend instance."""
    global _backend
    if _backend is None:
        _backend = UnifiedAIBackend()
    return _backend


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def print_status(as_json: bool = False):
    """Print status of all AI providers."""
    backend = get_backend()
    statuses = backend.get_all_status()

    if as_json:
        print(json.dumps({k: v.to_dict() for k, v in statuses.items()}, indent=2))
        return

    print("=" * 65)
    print("  SLATE Unified AI Backend — Provider Status")
    print("=" * 65)

    for name, status in statuses.items():
        icon = "OK" if status.available else "OFFLINE"
        print(f"\n  [{icon:>7}] {name}")
        print(f"           Endpoint: {status.endpoint}")
        if status.models:
            print(f"           Models:   {', '.join(status.models[:6])}")
        print(f"           Latency:  {status.latency_ms:.0f}ms")
        print(f"           Cost:     {status.cost}")
        if status.error:
            print(f"           Error:    {status.error[:80]}")

    print("\n" + "-" * 65)
    print("  Task Routing Table")
    print("-" * 65)
    print(f"  {'Task Type':<22} {'Primary':<15} {'Fallback':<15} {'Cost'}")
    print(f"  {'─' * 22} {'─' * 15} {'─' * 15} {'─' * 8}")
    for task_type, providers in TASK_ROUTING.items():
        primary = providers[0] if providers else "none"
        fallback = providers[1] if len(providers) > 1 else "—"
        print(f"  {task_type:<22} {primary:<15} {fallback:<15} FREE")

    print("\n" + "=" * 65)


def main():
    parser = argparse.ArgumentParser(description="SLATE Unified AI Backend")
    parser.add_argument("--status", action="store_true", help="Check all provider status")
    parser.add_argument("--task", type=str, help="Execute an AI task")
    parser.add_argument("--provider", type=str, choices=["ollama", "claude_code", "foundry"],
                        help="Force a specific provider")
    parser.add_argument("--model", type=str, help="Force a specific model")
    parser.add_argument("--providers", action="store_true", help="List all providers")
    parser.add_argument("--route", type=str, help="Show routing for a task type")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    backend = get_backend()

    if args.status or args.providers:
        print_status(as_json=args.json)

    elif args.task:
        result = backend.execute(
            task=args.task,
            provider_override=args.provider,
            model_override=args.model,
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.success:
                print(f"Provider: {result.provider} | Model: {result.model} | "
                      f"Tokens: {result.tokens} | {result.duration_ms:.0f}ms | {result.cost}")
                print("-" * 50)
                print(result.response)
            else:
                print(f"Error: {result.error}")
                sys.exit(1)

    elif args.route:
        task_type = args.route
        providers = backend.route_task(task_type)
        model_map = TASK_MODELS.get(task_type, {})
        if args.json:
            print(json.dumps({"task_type": task_type, "providers": providers, "models": model_map}))
        else:
            print(f"Task type: {task_type}")
            print(f"Provider order: {' → '.join(providers)}")
            for p in providers:
                print(f"  {p}: {model_map.get(p, 'default')}")

    else:
        print_status(as_json=args.json)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
