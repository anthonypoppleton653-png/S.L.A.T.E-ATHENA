#!/usr/bin/env python3
# Modified: 2026-02-10T18:00:00Z | Author: COPILOT | Change: Add Gemini CLI, Copilot CLI providers, cross-verification pipeline, GPU-first routing
"""
SLATE Unified AI Backend
==========================
Central routing for all AI inference tasks across SLATE providers.

Providers (priority order, all FREE / local):
1. Ollama (localhost:11434) — GPU Primary: slate-coder 12B, slate-fast 3B, slate-planner 7B
2. Claude Code CLI (E:\\.tools\\npm-global\\claude.cmd) — Complex reasoning, code gen
3. Gemini CLI (E:\\.tools\\npm-global\\gemini.cmd) — Analysis, verification, review
4. Copilot CLI (gh copilot) — Code suggestions, explanations
5. Foundry Local (localhost:5272) — ONNX-optimized Phi-3, Mistral-7B

Cross-verification pipeline:
    Work produced by one provider is verified by another.
    Primary generates code/analysis → Verifier reviews/confirms/flags discrepancies.

Task routing:
    code_generation    → ollama (slate-coder)     | verify: gemini
    code_review        → gemini                   | verify: ollama
    test_generation    → ollama (slate-coder)     | verify: gemini
    bug_fix            → claude_code              | verify: gemini
    refactoring        → claude_code              | verify: gemini
    documentation      → ollama (slate-fast)      | verify: copilot
    analysis           → gemini                   | verify: ollama
    research           → gemini                   | verify: ollama
    planning           → ollama (slate-planner)   | verify: gemini
    classification     → ollama (slate-fast)
    prompt_engineering → claude_code              | verify: gemini
    verification       → gemini                   | (meta-verify)

Usage:
    python slate/unified_ai_backend.py --status
    python slate/unified_ai_backend.py --task "your task"
    python slate/unified_ai_backend.py --task "your task" --provider gemini
    python slate/unified_ai_backend.py --task "your task" --provider copilot
    python slate/unified_ai_backend.py --verify "code to verify" --verifier gemini
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
LMSTUDIO_HOST = os.environ.get("LMSTUDIO_HOST", "http://127.0.0.1:1234")
TRELLIS_HOST = os.environ.get("TRELLIS_HOST", "http://127.0.0.1:8086")

# CLI tool paths — everything on E:\ drive
TOOLS_DIR = Path(os.environ.get("SLATE_TOOLS_DIR", str(WORKSPACE_ROOT / ".tools" / "npm-global")))
CLAUDE_CMD = str(TOOLS_DIR / ("claude.cmd" if sys.platform == "win32" else "claude"))
GEMINI_CMD = str(TOOLS_DIR / ("gemini.cmd" if sys.platform == "win32" else "gemini"))
GH_CMD = os.environ.get("GH_PATH", "gh")  # gh is in system PATH

# Model mapping per task type (6 providers)
TASK_MODELS = {
    "code_generation":    {"ollama": "slate-coder",   "claude_code": "opus-4.6",  "gemini": "gemini-2.5-pro", "copilot": "gpt-4o", "lmstudio": "auto"},
    "code_review":        {"gemini": "gemini-2.5-pro", "claude_code": "opus-4.6", "ollama": "slate-coder", "lmstudio": "auto"},
    "test_generation":    {"ollama": "slate-coder",   "claude_code": "opus-4.6",  "gemini": "gemini-2.5-pro", "lmstudio": "auto"},
    "bug_fix":            {"claude_code": "opus-4.6", "ollama": "slate-coder",    "gemini": "gemini-2.5-pro", "lmstudio": "auto"},
    "refactoring":        {"claude_code": "opus-4.6", "ollama": "slate-coder",    "gemini": "gemini-2.5-pro", "lmstudio": "auto"},
    "documentation":      {"ollama": "slate-fast",    "gemini": "gemini-2.5-flash", "copilot": "gpt-4o", "lmstudio": "auto"},
    "analysis":           {"gemini": "gemini-2.5-pro", "claude_code": "opus-4.6", "ollama": "slate-planner", "lmstudio": "auto"},
    "research":           {"gemini": "gemini-2.5-pro", "claude_code": "opus-4.6", "ollama": "slate-planner", "lmstudio": "auto"},
    "planning":           {"ollama": "slate-planner", "claude_code": "opus-4.6",  "gemini": "gemini-2.5-pro", "lmstudio": "auto"},
    "classification":     {"ollama": "slate-fast", "lmstudio": "auto"},
    "prompt_engineering": {"claude_code": "opus-4.6", "ollama": "slate-planner",  "gemini": "gemini-2.5-pro", "lmstudio": "auto"},
    "verification":       {"gemini": "gemini-2.5-pro", "copilot": "gpt-4o",      "ollama": "slate-planner", "lmstudio": "auto"},
}

# Provider priority per task type (first = preferred, lmstudio = failover for GPU tasks)
TASK_ROUTING = {
    "code_generation":    ["ollama", "claude_code", "gemini", "lmstudio", "foundry"],
    "code_review":        ["gemini", "claude_code", "ollama", "lmstudio"],
    "test_generation":    ["ollama", "claude_code", "gemini", "lmstudio"],
    "bug_fix":            ["claude_code", "ollama", "gemini", "lmstudio"],
    "refactoring":        ["claude_code", "ollama", "gemini", "lmstudio"],
    "documentation":      ["ollama", "gemini", "copilot", "lmstudio"],
    "analysis":           ["gemini", "claude_code", "ollama", "lmstudio"],
    "research":           ["gemini", "claude_code", "ollama", "lmstudio"],
    "planning":           ["ollama", "claude_code", "gemini", "lmstudio"],
    "classification":     ["ollama", "lmstudio"],
    "prompt_engineering": ["claude_code", "ollama", "gemini", "lmstudio"],
    "verification":       ["gemini", "copilot", "ollama", "lmstudio"],
    "3d_generation":      ["trellis2"],
    "avatar_generation":  ["trellis2"],
    "asset_generation":   ["trellis2"],
}

# Cross-verification mapping: task_type → which provider verifies the work
VERIFICATION_ROUTING = {
    "code_generation":    "gemini",
    "code_review":        "ollama",
    "test_generation":    "gemini",
    "bug_fix":            "gemini",
    "refactoring":        "gemini",
    "documentation":      "copilot",
    "analysis":           "ollama",
    "research":           "ollama",
    "planning":           "gemini",
    "prompt_engineering": "gemini",
    "verification":       "ollama",  # meta-verify
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
        # Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Add num_gpu 999 to force all layers to GPU VRAM
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
                    "num_gpu": 999,
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


# Modified: 2026-02-09T22:00:00Z | Author: COPILOT | Change: Add LMStudioProvider — 6th provider, OpenAI-compatible API, speculative decoding, JIT model loading, MCP tools
class LMStudioProvider:
    """LM Studio local LLM inference provider.

    LM Studio (https://lmstudio.ai) is a local-first LLM inference platform with:
    - OpenAI-compatible API at /v1/chat/completions, /v1/models, /v1/embeddings
    - Anthropic-compatible API at /v1/messages
    - Native REST API at /api/v0/ and /api/v1/ with rich stats (tok/s, TTFT)
    - GGUF model support (same format as Ollama, llama.cpp backend)
    - Speculative decoding for 2-3x faster inference
    - JIT (Just-In-Time) model loading — auto-loads on demand, unloads after TTL
    - Structured output via JSON schema constrained generation
    - Continuous batching for parallel requests
    - MCP tool integration via /v1/responses and /api/v1/chat
    - Multi-model serving with named identifiers
    - CUDA GPU acceleration on Windows/Linux, Metal/MLX on macOS

    Default port: 1234  |  Env var: LMSTUDIO_HOST
    CLI: lms (model management, server control, runtime selection)

    SDKs:
    - Python: pip install lmstudio (sync/async, agents, embeddings, tools, plugins)
    - TypeScript: @lmstudio/sdk (npm, Node.js + browser)

    Integration with SLATE:
    - Serves as failover for Ollama (same GGUF models, different runtime)
    - Unique advantages: speculative decoding, JIT loading, structured output
    - Model value 'auto' means use whatever model is currently loaded in LM Studio
    - No Docker/K8s support (host-level only, not containerizable)
    """

    def __init__(self, host: str = LMSTUDIO_HOST):
        self.host = host
        self.name = "lmstudio"

    def check_status(self) -> ProviderStatus:
        """Check LM Studio server availability and list loaded/available models."""
        start = time.time()
        try:
            # Use OpenAI-compatible /v1/models endpoint
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

    def get_native_status(self) -> dict:
        """Get extended model info from LM Studio native API (/api/v0/models).

        Returns richer metadata than OpenAI-compat: architecture, quantization,
        max context length, load state, file size.
        """
        try:
            url = f"{self.host}/api/v0/models"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {}

    def generate(self, prompt: str, model: str = "auto",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        """Generate via LM Studio OpenAI-compatible /v1/chat/completions API.

        When model='auto', uses whatever model is currently loaded in LM Studio.
        LM Studio's JIT loading will auto-load the first available model if none loaded.
        """
        start = time.time()
        try:
            url = f"{self.host}/v1/chat/completions"
            payload_dict = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }
            # Only set model if not 'auto' — omitting lets LM Studio pick the loaded model
            if model and model != "auto":
                payload_dict["model"] = model

            payload = json.dumps(payload_dict).encode("utf-8")
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                response_text = choices[0]["message"]["content"] if choices else ""
                usage = result.get("usage", {})
                actual_model = result.get("model", model)
                duration = (time.time() - start) * 1000
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=actual_model,
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

    def generate_native(self, prompt: str, model: str = "auto",
                        max_tokens: int = 2048, temperature: float = 0.7,
                        context_length: int = 8000) -> InferenceResult:
        """Generate via LM Studio native /api/v1/chat endpoint.

        Provides richer response with stats (tok/s, TTFT), MCP tool integration,
        and reasoning tokens. Use this for tasks requiring extended context or
        tool-augmented generation.
        """
        start = time.time()
        try:
            url = f"{self.host}/api/v1/chat"
            payload_dict = {
                "input": prompt,
                "context_length": context_length,
                "temperature": temperature,
            }
            if model and model != "auto":
                payload_dict["model"] = model

            payload = json.dumps(payload_dict).encode("utf-8")
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                # Native API returns output as array of typed blocks
                output_blocks = result.get("output", [])
                response_parts = []
                for block in output_blocks:
                    if block.get("type") == "message":
                        response_parts.append(block.get("content", ""))
                response_text = "\n".join(response_parts)

                stats = result.get("stats", {})
                actual_model = result.get("model_instance_id", model)
                duration = (time.time() - start) * 1000
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=actual_model,
                    response=response_text,
                    tokens=stats.get("total_output_tokens", 0),
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

    def embed(self, text: str, model: str = "auto") -> list[float]:
        """Generate embeddings via LM Studio /v1/embeddings endpoint.

        Requires an embedding model to be loaded in LM Studio
        (e.g., nomic-embed-text, bge-small, etc.)
        """
        try:
            url = f"{self.host}/v1/embeddings"
            payload_dict = {
                "input": text,
            }
            if model and model != "auto":
                payload_dict["model"] = model

            payload = json.dumps(payload_dict).encode("utf-8")
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                data = result.get("data", [])
                if data:
                    return data[0].get("embedding", [])
                return []
        except Exception:
            return []


# Modified: 2026-02-10T18:00:00Z | Author: COPILOT | Change: Add GeminiCliProvider for Gemini CLI inference
class GeminiCliProvider:
    """Gemini CLI inference provider — wraps the local Gemini CLI for analysis and verification.

    Gemini CLI is installed on E:\\ drive at .tools/npm-global/gemini.cmd.
    It provides strong analytical capabilities ideal for:
    - Code review and verification (cross-checking Ollama/Claude output)
    - Research and analysis tasks
    - Documentation quality assessment
    - Multi-step reasoning

    All execution is LOCAL — Gemini CLI manages its own auth and inference.
    """

    def __init__(self, cmd_path: str = GEMINI_CMD):
        self.name = "gemini"
        self.cmd_path = cmd_path

    def check_status(self) -> ProviderStatus:
        """Check Gemini CLI availability."""
        start = time.time()
        try:
            result = subprocess.run(
                [self.cmd_path, "--version"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace",
            )
            latency = (time.time() - start) * 1000

            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0] if result.stdout.strip() else "unknown"
                return ProviderStatus(
                    name=self.name,
                    available=True,
                    endpoint=f"cli:{self.cmd_path}",
                    models=["gemini-2.5-pro", "gemini-2.5-flash"],
                    latency_ms=latency,
                    cost="FREE (Google AI)",
                )
            else:
                return ProviderStatus(
                    name=self.name,
                    available=False,
                    endpoint=f"cli:{self.cmd_path}",
                    error=f"CLI exited with code {result.returncode}: {result.stderr.strip()[:100]}",
                )
        except FileNotFoundError:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=f"cli:{self.cmd_path}",
                error=f"Gemini CLI not found at {self.cmd_path}",
            )
        except Exception as e:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=f"cli:{self.cmd_path}",
                error=str(e)[:100],
            )

    def generate(self, prompt: str, model: str = "gemini-2.5-pro",
                 max_tokens: int = 4096, temperature: float = 0.7) -> InferenceResult:
        """Generate text via Gemini CLI subprocess.

        Uses `gemini -p "prompt"` for non-interactive single-shot inference.
        """
        start = time.time()
        try:
            # Build command: gemini -p "prompt" for single-shot mode
            cmd = [self.cmd_path, "-p", prompt[:8000]]  # Limit prompt size for CLI

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 min timeout for complex tasks
                encoding="utf-8",
                errors="replace",
                cwd=str(WORKSPACE_ROOT),
                env={**os.environ, "TERM": "dumb", "NO_COLOR": "1"},
            )

            duration = (time.time() - start) * 1000
            response_text = result.stdout.strip()

            if result.returncode == 0 and response_text:
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=model,
                    response=response_text,
                    tokens=len(response_text.split()),  # Approximate
                    duration_ms=duration,
                    cost="FREE (Google AI)",
                )
            else:
                error_msg = result.stderr.strip()[:200] if result.stderr else f"Exit code {result.returncode}"
                return InferenceResult(
                    success=False,
                    provider=self.name,
                    model=model,
                    response=response_text,
                    error=error_msg,
                    duration_ms=duration,
                )

        except subprocess.TimeoutExpired:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error="Gemini CLI timed out after 180s",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error=str(e),
            )


# Modified: 2026-02-10T18:00:00Z | Author: COPILOT | Change: Add CopilotCliProvider for gh copilot CLI inference
class CopilotCliProvider:
    """GitHub Copilot CLI inference provider — wraps `gh copilot` for code suggestions.

    Uses the `gh copilot suggest` and `gh copilot explain` commands for:
    - Code suggestions and completions
    - Code explanations
    - Shell command generation
    - Documentation assistance

    All execution is LOCAL through the gh CLI extension.
    """

    def __init__(self, gh_path: str = GH_CMD):
        self.name = "copilot"
        self.gh_path = gh_path

    def check_status(self) -> ProviderStatus:
        """Check gh copilot availability."""
        start = time.time()
        try:
            result = subprocess.run(
                [self.gh_path, "copilot", "--version"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace",
            )
            latency = (time.time() - start) * 1000

            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0] if result.stdout.strip() else "unknown"
                return ProviderStatus(
                    name=self.name,
                    available=True,
                    endpoint=f"cli:{self.gh_path} copilot",
                    models=["gpt-4o"],
                    latency_ms=latency,
                    cost="FREE (GitHub Copilot)",
                )
            else:
                return ProviderStatus(
                    name=self.name,
                    available=False,
                    endpoint=f"cli:{self.gh_path} copilot",
                    error=f"gh copilot exited {result.returncode}: {result.stderr.strip()[:100]}",
                )
        except FileNotFoundError:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=f"cli:{self.gh_path}",
                error=f"gh CLI not found at {self.gh_path}",
            )
        except Exception as e:
            return ProviderStatus(
                name=self.name,
                available=False,
                endpoint=f"cli:{self.gh_path}",
                error=str(e)[:100],
            )

    def generate(self, prompt: str, model: str = "gpt-4o",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        """Generate via gh copilot explain for code-related tasks.

        Uses `gh copilot explain` for explanations/analysis.
        Falls back to direct prompt piping if explain doesn't work well.
        """
        start = time.time()
        try:
            # Use 'explain' mode for code-related prompts
            cmd = [self.gh_path, "copilot", "explain", prompt[:4000]]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
                cwd=str(WORKSPACE_ROOT),
                env={**os.environ, "GH_PROMPT": "disable"},
            )

            duration = (time.time() - start) * 1000
            response_text = result.stdout.strip()

            if result.returncode == 0 and response_text:
                return InferenceResult(
                    success=True,
                    provider=self.name,
                    model=model,
                    response=response_text,
                    tokens=len(response_text.split()),
                    duration_ms=duration,
                    cost="FREE (GitHub Copilot)",
                )
            else:
                error_msg = result.stderr.strip()[:200] if result.stderr else f"Exit code {result.returncode}"
                return InferenceResult(
                    success=False,
                    provider=self.name,
                    model=model,
                    response=response_text,
                    error=error_msg,
                    duration_ms=duration,
                )

        except subprocess.TimeoutExpired:
            return InferenceResult(
                success=False,
                provider=self.name,
                model=model,
                response="",
                error="gh copilot timed out after 120s",
                duration_ms=(time.time() - start) * 1000,
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
            "gemini": GeminiCliProvider(),
            "copilot": CopilotCliProvider(),
            "foundry": FoundryProvider(),
            "lmstudio": LMStudioProvider(),
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
            "verification": ["verify", "cross-check", "validate output", "double-check", "confirm correctness"],
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
        defaults = {
            "ollama": "slate-fast",
            "claude_code": "opus-4.6",
            "gemini": "gemini-2.5-pro",
            "copilot": "gpt-4o",
            "foundry": "phi-3.5",
            "lmstudio": "auto",
        }
        return models.get(provider, defaults.get(provider, "slate-fast"))

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

    # Modified: 2026-02-10T18:00:00Z | Author: COPILOT | Change: Add cross-verification pipeline
    def verify(self, content: str, task_type: str = "verification",
               verifier_override: Optional[str] = None,
               original_provider: str = "") -> InferenceResult:
        """Cross-verify content produced by one AI provider using another.

        The verification pipeline:
        1. Receives content (code/analysis/docs) from a primary provider
        2. Routes to a different provider for independent review
        3. Returns verification result with pass/fail assessment

        Args:
            content: The content to verify (code, analysis, etc.)
            task_type: The original task type (used to route to correct verifier)
            verifier_override: Force a specific verifier provider
            original_provider: Which provider produced the content (logged for audit)

        Returns:
            InferenceResult with verification assessment
        """
        # Select verifier
        if verifier_override:
            verifier_name = verifier_override
        else:
            verifier_name = VERIFICATION_ROUTING.get(task_type, "gemini")

        # Don't verify with the same provider that generated
        if verifier_name == original_provider:
            # Cycle to next available verifier
            fallback_order = ["gemini", "ollama", "copilot", "claude_code"]
            for fb in fallback_order:
                if fb != original_provider and fb in self.providers:
                    verifier_name = fb
                    break

        # Build verification prompt
        verify_prompt = (
            f"VERIFICATION REQUEST\n"
            f"{'=' * 40}\n"
            f"Original task type: {task_type}\n"
            f"Original provider: {original_provider or 'unknown'}\n\n"
            f"Please review the following output for:\n"
            f"1. Correctness — Are there logical errors, bugs, or inaccuracies?\n"
            f"2. Completeness — Does it fully address the task?\n"
            f"3. Quality — Is it well-structured and following best practices?\n"
            f"4. Security — Any security concerns (exposed secrets, unsafe patterns)?\n\n"
            f"CONTENT TO VERIFY:\n"
            f"{'─' * 40}\n"
            f"{content[:6000]}\n"
            f"{'─' * 40}\n\n"
            f"Respond with:\n"
            f"- VERDICT: PASS or FAIL\n"
            f"- CONFIDENCE: HIGH/MEDIUM/LOW\n"
            f"- ISSUES: List any problems found (or 'None')\n"
            f"- SUGGESTIONS: Improvements if any\n"
        )

        logger.info(f"Cross-verifying with {verifier_name} (original: {original_provider})")
        return self.execute(
            task=verify_prompt,
            provider_override=verifier_name,
            max_tokens=2048,
            temperature=0.3,  # Low temperature for objective verification
        )

    def execute_with_verification(self, task: str,
                                   provider_override: Optional[str] = None,
                                   verify: bool = True) -> dict[str, Any]:
        """Execute a task and optionally cross-verify the result.

        Returns a dict with both the primary result and verification result.
        """
        # Step 1: Execute primary task
        primary_result = self.execute(task=task, provider_override=provider_override)

        output = {
            "primary": primary_result.to_dict(),
            "verified": False,
            "verification": None,
        }

        if not primary_result.success or not verify:
            return output

        # Step 2: Cross-verify
        task_type = self.classify_task(task)
        verification = self.verify(
            content=primary_result.response,
            task_type=task_type,
            original_provider=primary_result.provider,
        )

        output["verified"] = True
        output["verification"] = verification.to_dict()
        return output


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

    print("=" * 75)
    print("  SLATE Unified AI Backend — Provider Status (6 providers)")
    print("=" * 75)

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

    available_count = sum(1 for s in statuses.values() if s.available)
    print(f"\n  Providers: {available_count}/{len(statuses)} online")

    print("\n" + "-" * 75)
    print("  Task Routing Table")
    print("-" * 75)
    print(f"  {'Task Type':<22} {'Primary':<15} {'Fallback':<15} {'Verifier':<12} {'Cost'}")
    print(f"  {'─' * 22} {'─' * 15} {'─' * 15} {'─' * 12} {'─' * 8}")
    for task_type, providers in TASK_ROUTING.items():
        primary = providers[0] if providers else "none"
        fallback = providers[1] if len(providers) > 1 else "—"
        verifier = VERIFICATION_ROUTING.get(task_type, "—")
        print(f"  {task_type:<22} {primary:<15} {fallback:<15} {verifier:<12} FREE")

    print("\n" + "=" * 75)


def main():
    parser = argparse.ArgumentParser(description="SLATE Unified AI Backend — 6 providers, cross-verification")
    parser.add_argument("--status", action="store_true", help="Check all provider status")
    parser.add_argument("--task", type=str, help="Execute an AI task")
    parser.add_argument("--provider", type=str,
                        choices=["ollama", "claude_code", "gemini", "copilot", "foundry", "lmstudio"],
                        help="Force a specific provider")
    parser.add_argument("--model", type=str, help="Force a specific model")
    parser.add_argument("--verify", type=str, help="Cross-verify content with a verifier")
    parser.add_argument("--verifier", type=str,
                        choices=["ollama", "claude_code", "gemini", "copilot", "lmstudio"],
                        help="Force a specific verifier for --verify")
    parser.add_argument("--with-verification", action="store_true",
                        help="Execute task AND cross-verify the result")
    parser.add_argument("--providers", action="store_true", help="List all providers")
    parser.add_argument("--route", type=str, help="Show routing for a task type")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    backend = get_backend()

    if args.status or args.providers:
        print_status(as_json=args.json)

    elif args.verify:
        # Cross-verification mode
        result = backend.verify(
            content=args.verify,
            verifier_override=args.verifier,
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.success:
                print(f"Verifier: {result.provider} | Model: {result.model} | "
                      f"{result.duration_ms:.0f}ms | {result.cost}")
                print("-" * 50)
                print(result.response)
            else:
                print(f"Verification error: {result.error}")
                sys.exit(1)

    elif args.task:
        if args.with_verification:
            # Execute + verify
            output = backend.execute_with_verification(
                task=args.task,
                provider_override=args.provider,
                verify=True,
            )
            if args.json:
                print(json.dumps(output, indent=2))
            else:
                primary = output["primary"]
                print(f"Primary: {primary['provider']} | Model: {primary['model']} | "
                      f"Tokens: {primary['tokens']} | {primary['duration_ms']:.0f}ms")
                print("-" * 50)
                print(primary["response"][:2000])
                if output["verified"] and output["verification"]:
                    v = output["verification"]
                    print(f"\n{'=' * 50}")
                    print(f"VERIFICATION by {v['provider']} | Model: {v['model']} | "
                          f"{v['duration_ms']:.0f}ms")
                    print("-" * 50)
                    print(v["response"][:1000])
        else:
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
        verifier = VERIFICATION_ROUTING.get(task_type, "none")
        if args.json:
            print(json.dumps({
                "task_type": task_type,
                "providers": providers,
                "models": model_map,
                "verifier": verifier,
            }))
        else:
            print(f"Task type: {task_type}")
            print(f"Provider order: {' → '.join(providers)}")
            print(f"Verifier: {verifier}")
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
