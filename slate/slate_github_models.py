#!/usr/bin/env python3
# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Initial GitHub Models free-tier integration
"""
SLATE GitHub Models Integration
=================================
Free AI model access through GitHub Models (models.inference.ai.azure.com).

Provides:
- Chat completions via OpenAI-compatible API (GPT-4o, Llama, Mistral, Phi, etc.)
- Automatic GitHub PAT authentication from git credential manager
- Built-in rate limiting for free-tier compliance
- Semantic Kernel connector factory for SLATE pipeline
- Fallback chain: GitHub Models → Ollama (local)

Free-tier rate limits (as of 2025):
  Low-rate models  : 15 RPM,  150 RPD,  8k  input tokens,  4k  output tokens
  High-rate models : 15 RPM,  150 RPD,  8k  input tokens,  4k  output tokens
  Embedding models : 15 RPM,  150 RPD,  64k input tokens

See: https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models#rate-limits

Usage:
    python slate/slate_github_models.py --status          # Check available models & auth
    python slate/slate_github_models.py --list-models     # List all available models
    python slate/slate_github_models.py --chat "prompt"   # Chat with default model
    python slate/slate_github_models.py --chat "prompt" --model gpt-4o  # Chat with specific model
    python slate/slate_github_models.py --benchmark       # Run throughput benchmark
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: workspace setup
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.github_models")

# ── Constants ────────────────────────────────────────────────────────────

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
STATE_FILE = WORKSPACE_ROOT / ".slate_github_models.json"

# Model catalog — GitHub Models free tier
# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Initial model catalog
GITHUB_MODELS_CATALOG = {
    # ── OpenAI ──
    "gpt-4o": {
        "provider": "OpenAI",
        "tier": "low",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["reasoning", "analysis", "code"],
    },
    "gpt-4o-mini": {
        "provider": "OpenAI",
        "tier": "high",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["fast", "classification", "summary"],
    },
    # ── Meta Llama ──
    "Meta-Llama-3.1-405B-Instruct": {
        "provider": "Meta",
        "tier": "low",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["reasoning", "code", "analysis"],
    },
    "Meta-Llama-3.1-70B-Instruct": {
        "provider": "Meta",
        "tier": "low",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["reasoning", "code"],
    },
    "Meta-Llama-3.1-8B-Instruct": {
        "provider": "Meta",
        "tier": "high",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["fast", "classification"],
    },
    # ── Mistral ──
    "Mistral-large-2411": {
        "provider": "Mistral AI",
        "tier": "low",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["reasoning", "code", "multilingual"],
    },
    "Mistral-small": {
        "provider": "Mistral AI",
        "tier": "high",
        "context_window": 32000,
        "max_output": 4096,
        "best_for": ["fast", "classification"],
    },
    # ── Microsoft Phi ──
    "Phi-4": {
        "provider": "Microsoft",
        "tier": "high",
        "context_window": 16384,
        "max_output": 4096,
        "best_for": ["reasoning", "code", "math"],
    },
    "Phi-3.5-mini-instruct": {
        "provider": "Microsoft",
        "tier": "high",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["fast", "efficient"],
    },
    # ── Cohere ──
    "Cohere-command-r-plus-08-2024": {
        "provider": "Cohere",
        "tier": "low",
        "context_window": 128000,
        "max_output": 4096,
        "best_for": ["rag", "search", "enterprise"],
    },
    # ── DeepSeek ──
    "DeepSeek-R1": {
        "provider": "DeepSeek",
        "tier": "low",
        "context_window": 64000,
        "max_output": 8192,
        "best_for": ["reasoning", "code", "math"],
    },
}

# Rate limit tracking — free tier
# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Rate limits from GH docs
RATE_LIMITS = {
    "low": {"rpm": 15, "rpd": 150, "input_tokens": 8000, "output_tokens": 4096},
    "high": {"rpm": 15, "rpd": 150, "input_tokens": 8000, "output_tokens": 4096},
    "embedding": {"rpm": 15, "rpd": 150, "input_tokens": 64000},
}

# SLATE role → GitHub Models mapping (supplements Ollama models)
SLATE_ROLE_MAP = {
    "code": "gpt-4o",
    "fast": "gpt-4o-mini",
    "planner": "Mistral-large-2411",
    "analysis": "gpt-4o",
    "reasoning": "DeepSeek-R1",
    "summary": "gpt-4o-mini",
    "general": "gpt-4o-mini",
}


# ── Data Classes ─────────────────────────────────────────────────────────

@dataclass
class RateTracker:
    """Tracks API call rate for free-tier compliance."""
    minute_calls: List[float] = field(default_factory=list)
    day_calls: List[float] = field(default_factory=list)

    def can_call(self, tier: str = "low") -> bool:
        """Check if a call is allowed under rate limits."""
        now = time.time()
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["low"])

        # Prune old entries
        self.minute_calls = [t for t in self.minute_calls if now - t < 60]
        self.day_calls = [t for t in self.day_calls if now - t < 86400]

        if len(self.minute_calls) >= limits["rpm"]:
            return False
        if len(self.day_calls) >= limits["rpd"]:
            return False
        return True

    def record_call(self) -> None:
        """Record a call timestamp."""
        now = time.time()
        self.minute_calls.append(now)
        self.day_calls.append(now)

    def remaining(self, tier: str = "low") -> Dict[str, int]:
        """Get remaining calls."""
        now = time.time()
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["low"])
        self.minute_calls = [t for t in self.minute_calls if now - t < 60]
        self.day_calls = [t for t in self.day_calls if now - t < 86400]
        return {
            "rpm_remaining": max(0, limits["rpm"] - len(self.minute_calls)),
            "rpd_remaining": max(0, limits["rpd"] - len(self.day_calls)),
        }


@dataclass
class ChatResponse:
    """Response from a GitHub Models chat completion."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.content)


# ── GitHub Token ─────────────────────────────────────────────────────────

def get_github_token() -> str:
    """
    Get GitHub token from git credential manager.
    Same method used by RunnerAPI and other SLATE modules.
    """
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return ""


# ── GitHub Models Client ─────────────────────────────────────────────────

class GitHubModelsClient:
    """
    Client for GitHub Models free-tier AI inference.

    Uses the OpenAI Python SDK pointed at the GitHub Models endpoint
    with a GitHub PAT for authentication. Includes rate limiting,
    SLATE role mapping, and Ollama fallback.
    """

    # Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Initial client implementation

    def __init__(self, token: Optional[str] = None, default_model: str = "gpt-4o-mini"):
        self.token = token or get_github_token()
        self.default_model = default_model
        self.endpoint = GITHUB_MODELS_ENDPOINT
        self._client: Optional[Any] = None
        self._async_client: Optional[Any] = None
        self._rate_tracker = RateTracker()
        self._call_history: List[Dict[str, Any]] = []
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load persisted state."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "last_call": None,
            "models_used": {},
        }

    def _save_state(self) -> None:
        """Persist state to disk."""
        try:
            STATE_FILE.write_text(
                json.dumps(self._state, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

    @property
    def authenticated(self) -> bool:
        """Check if we have a valid token."""
        return bool(self.token)

    def get_sync_client(self) -> Any:
        """Get or create synchronous OpenAI client for GitHub Models."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self.endpoint,
                api_key=self.token,
            )
        return self._client

    def get_async_client(self) -> Any:
        """Get or create async OpenAI client for GitHub Models."""
        if self._async_client is None:
            from openai import AsyncOpenAI
            self._async_client = AsyncOpenAI(
                base_url=self.endpoint,
                api_key=self.token,
            )
        return self._async_client

    def resolve_model(self, role: str = "") -> str:
        """Resolve a SLATE role to a GitHub Models model name."""
        if role and role in SLATE_ROLE_MAP:
            return SLATE_ROLE_MAP[role]
        return self.default_model

    def get_model_tier(self, model: str) -> str:
        """Get the rate-limit tier for a model."""
        info = GITHUB_MODELS_CATALOG.get(model, {})
        return info.get("tier", "low")

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: str = "",
        role: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """
        Send a chat completion request to GitHub Models.

        Args:
            prompt: User message
            model: Model name (overrides role)
            system: System prompt
            role: SLATE role (code, fast, planner, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            ChatResponse with content or error
        """
        model = model or self.resolve_model(role)
        tier = self.get_model_tier(model)

        # Rate limit check
        if not self._rate_tracker.can_call(tier):
            remaining = self._rate_tracker.remaining(tier)
            return ChatResponse(
                content="",
                model=model,
                error=f"Rate limit exceeded. Remaining: {remaining}",
            )

        # Build messages
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Enforce max token limits from free tier
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["low"])
        max_tokens = min(max_tokens, limits.get("output_tokens", 4096))

        t0 = time.time()
        try:
            client = self.get_sync_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency = (time.time() - t0) * 1000

            self._rate_tracker.record_call()

            content = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            # Update state
            self._state["total_calls"] += 1
            self._state["total_input_tokens"] += usage.get("prompt_tokens", 0)
            self._state["total_output_tokens"] += usage.get("completion_tokens", 0)
            self._state["last_call"] = datetime.now(timezone.utc).isoformat()
            self._state.setdefault("models_used", {})
            self._state["models_used"][model] = (
                self._state["models_used"].get(model, 0) + 1
            )
            self._save_state()

            return ChatResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.time() - t0) * 1000
            error_msg = str(e)
            # Classify common errors
            if "401" in error_msg or "Unauthorized" in error_msg:
                error_msg = "Authentication failed — GitHub PAT may be invalid or missing 'models:read' scope"
            elif "429" in error_msg or "rate" in error_msg.lower():
                error_msg = f"Rate limited by GitHub Models — free tier: {limits['rpm']} RPM / {limits['rpd']} RPD"
            elif "404" in error_msg:
                error_msg = f"Model '{model}' not found on GitHub Models"

            return ChatResponse(
                content="",
                model=model,
                error=error_msg,
                latency_ms=latency,
            )

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Return the catalog of known GitHub Models."""
        models = []
        for name, info in GITHUB_MODELS_CATALOG.items():
            models.append({
                "name": name,
                "provider": info["provider"],
                "tier": info["tier"],
                "context_window": info.get("context_window", 0),
                "best_for": info.get("best_for", []),
            })
        return models

    def status(self) -> Dict[str, Any]:
        """Get full status of GitHub Models integration."""
        remaining = self._rate_tracker.remaining("low")
        return {
            "authenticated": self.authenticated,
            "endpoint": self.endpoint,
            "default_model": self.default_model,
            "catalog_size": len(GITHUB_MODELS_CATALOG),
            "rate_limits": remaining,
            "total_calls": self._state.get("total_calls", 0),
            "total_input_tokens": self._state.get("total_input_tokens", 0),
            "total_output_tokens": self._state.get("total_output_tokens", 0),
            "last_call": self._state.get("last_call"),
            "models_used": self._state.get("models_used", {}),
        }


# ── Semantic Kernel Integration ──────────────────────────────────────────

def create_github_models_sk_service(
    role: str = "general",
    token: Optional[str] = None,
) -> Any:
    """
    Create a Semantic Kernel OpenAIChatCompletion service backed by GitHub Models.

    This can be added to a Semantic Kernel instance alongside the Ollama service
    to provide cloud-augmented inference for tasks that benefit from larger models.

    Args:
        role: SLATE role (code, fast, planner, analysis, reasoning, general)
        token: GitHub PAT (auto-detected if not provided)

    Returns:
        OpenAIChatCompletion service configured for GitHub Models
    """
    # Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: SK connector for GitHub Models
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    from openai import AsyncOpenAI

    _token = token or get_github_token()
    if not _token:
        raise RuntimeError("No GitHub token available for GitHub Models")

    model = SLATE_ROLE_MAP.get(role, "gpt-4o-mini")

    async_client = AsyncOpenAI(
        base_url=GITHUB_MODELS_ENDPOINT,
        api_key=_token,
    )

    service = OpenAIChatCompletion(
        ai_model_id=model,
        async_client=async_client,
        service_id=f"github_models_{role}",
    )

    return service


# ── Ollama Fallback ──────────────────────────────────────────────────────

class GitHubModelsWithFallback:
    """
    GitHub Models client with automatic Ollama fallback.

    Tries GitHub Models first. If rate-limited, auth fails, or unavailable,
    falls back to local Ollama inference transparently.
    """

    # Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Fallback chain implementation

    OLLAMA_FALLBACK_MAP = {
        "code": "slate-coder:latest",
        "fast": "slate-fast:latest",
        "planner": "slate-planner:latest",
        "analysis": "mistral-nemo:latest",
        "reasoning": "mistral-nemo:latest",
        "summary": "slate-fast:latest",
        "general": "mistral-nemo:latest",
    }

    def __init__(self, token: Optional[str] = None):
        self.github_client = GitHubModelsClient(token=token)
        self._ollama_available: Optional[bool] = None

    def _check_ollama(self) -> bool:
        """Check if Ollama is running."""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            self._ollama_available = result.returncode == 0
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def _ollama_generate(self, model: str, prompt: str, system: str = "") -> str:
        """Generate with Ollama as fallback."""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            result = subprocess.run(
                ["ollama", "run", model, full_prompt],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return f"[Ollama error: {result.stderr.strip()}]"
        except subprocess.TimeoutExpired:
            return "[Ollama timeout]"
        except Exception as e:
            return f"[Ollama error: {e}]"

    def chat(
        self,
        prompt: str,
        role: str = "general",
        model: Optional[str] = None,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """
        Chat with automatic fallback.

        1. Try GitHub Models (free tier)
        2. Fall back to Ollama (local) if GitHub Models fails
        """
        # Try GitHub Models first
        if self.github_client.authenticated:
            response = self.github_client.chat(
                prompt=prompt,
                model=model,
                role=role,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response.ok:
                return response
            logger.info(
                f"GitHub Models failed ({response.error}), falling back to Ollama"
            )

        # Fallback to Ollama
        if self._check_ollama():
            ollama_model = self.OLLAMA_FALLBACK_MAP.get(
                role, "mistral-nemo:latest"
            )
            t0 = time.time()
            content = self._ollama_generate(ollama_model, prompt, system)
            latency = (time.time() - t0) * 1000
            return ChatResponse(
                content=content,
                model=f"ollama/{ollama_model}",
                latency_ms=latency,
            )

        return ChatResponse(
            content="",
            model=model or "none",
            error="Both GitHub Models and Ollama unavailable",
        )


# ── CLI ──────────────────────────────────────────────────────────────────

def print_status(client: GitHubModelsClient) -> None:
    """Print formatted status."""
    s = client.status()
    print("=" * 60)
    print("  SLATE GitHub Models Integration")
    print("=" * 60)
    auth_icon = "✓" if s["authenticated"] else "✗"
    print(f"  Auth:           {auth_icon} {'Token found' if s['authenticated'] else 'No token'}")
    print(f"  Endpoint:       {s['endpoint']}")
    print(f"  Default Model:  {s['default_model']}")
    print(f"  Catalog Size:   {s['catalog_size']} models")
    print(f"  RPM Remaining:  {s['rate_limits']['rpm_remaining']}")
    print(f"  RPD Remaining:  {s['rate_limits']['rpd_remaining']}")
    print(f"  Total Calls:    {s['total_calls']}")
    print(f"  Input Tokens:   {s['total_input_tokens']:,}")
    print(f"  Output Tokens:  {s['total_output_tokens']:,}")
    if s["last_call"]:
        print(f"  Last Call:      {s['last_call']}")
    if s["models_used"]:
        print("  Models Used:")
        for m, c in s["models_used"].items():
            print(f"    {m}: {c}")
    print("=" * 60)


def print_models() -> None:
    """Print available model catalog."""
    print(f"{'Model':<40} {'Provider':<15} {'Tier':<6} {'Context':<10} {'Best For'}")
    print("-" * 100)
    for name, info in sorted(GITHUB_MODELS_CATALOG.items()):
        best_for = ", ".join(info.get("best_for", []))
        ctx = f"{info.get('context_window', 0):,}"
        print(f"{name:<40} {info['provider']:<15} {info['tier']:<6} {ctx:<10} {best_for}")


def run_benchmark(client: GitHubModelsClient) -> None:
    """Run a simple throughput benchmark."""
    print("Running GitHub Models benchmark...")
    print("-" * 60)

    test_models = ["gpt-4o-mini", "gpt-4o"]
    test_prompt = "Explain what CUDA compute capability 12.0 (Blackwell) means in 2 sentences."

    for model in test_models:
        if model not in GITHUB_MODELS_CATALOG:
            continue
        print(f"\n  Model: {model}")
        response = client.chat(
            prompt=test_prompt,
            model=model,
            max_tokens=256,
        )
        if response.ok:
            tokens = response.usage.get("total_tokens", 0)
            out_tokens = response.usage.get("completion_tokens", 0)
            tps = (out_tokens / (response.latency_ms / 1000)) if response.latency_ms > 0 else 0
            print(f"    Status:   ✓ OK")
            print(f"    Latency:  {response.latency_ms:.0f}ms")
            print(f"    Tokens:   {tokens} total ({out_tokens} output)")
            print(f"    Speed:    {tps:.1f} tok/s")
            print(f"    Response: {response.content[:120]}...")
        else:
            print(f"    Status:   ✗ {response.error}")
        time.sleep(1)  # Respect rate limits between calls

    print("\n" + "-" * 60)
    print("Benchmark complete.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SLATE GitHub Models Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--chat", type=str, help="Chat with a model")
    parser.add_argument("--model", type=str, default=None, help="Model name for --chat")
    parser.add_argument("--role", type=str, default="general", help="SLATE role (code, fast, planner, etc.)")
    parser.add_argument("--system", type=str, default="", help="System prompt for --chat")
    parser.add_argument("--benchmark", action="store_true", help="Run throughput benchmark")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--fallback", action="store_true", help="Use fallback client (GitHub → Ollama)")

    args = parser.parse_args()

    if args.status:
        client = GitHubModelsClient()
        if args.json:
            print(json.dumps(client.status(), indent=2, default=str))
        else:
            print_status(client)
        return

    if args.list_models:
        if args.json:
            print(json.dumps(
                [{"name": k, **v} for k, v in GITHUB_MODELS_CATALOG.items()],
                indent=2,
            ))
        else:
            print_models()
        return

    if args.chat:
        if args.fallback:
            fb_client = GitHubModelsWithFallback()
            response = fb_client.chat(
                prompt=args.chat,
                role=args.role,
                model=args.model,
                system=args.system,
            )
        else:
            client = GitHubModelsClient()
            response = client.chat(
                prompt=args.chat,
                model=args.model,
                role=args.role,
                system=args.system,
            )
        if args.json:
            print(json.dumps({
                "content": response.content,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
                "latency_ms": response.latency_ms,
                "error": response.error,
            }, indent=2))
        else:
            if response.ok:
                print(f"\n[{response.model}] ({response.latency_ms:.0f}ms)\n")
                print(response.content)
                if response.usage:
                    print(f"\n--- {response.usage.get('total_tokens', 0)} tokens ---")
            else:
                print(f"Error: {response.error}")
        return

    if args.benchmark:
        client = GitHubModelsClient()
        run_benchmark(client)
        return

    # Default: show status
    client = GitHubModelsClient()
    print_status(client)


if __name__ == "__main__":
    main()
