#!/usr/bin/env python3
"""
SLATE Warmup — GPU Model Preloading & System Initialization
=============================================================
# Modified: 2026-02-07T08:00:00Z | Author: COPILOT | Change: Initial warmup system

Initializes the SLATE agentic system by:
1. Configuring Ollama for dual-GPU with persistent model keep-alive
2. Preloading SLATE models onto both GPUs
3. Building/refreshing the codebase embedding index
4. Verifying inference readiness on all models

This ensures that both GPUs are hot and ready for autonomous task execution
instead of cold-starting models on every inference request.

Usage:
    python slate/slate_warmup.py                    # Full warmup
    python slate/slate_warmup.py --preload-only     # Just load models
    python slate/slate_warmup.py --index-only       # Just build embeddings
    python slate/slate_warmup.py --status           # Check warmup state
    python slate/slate_warmup.py --json             # JSON status
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Modified: 2026-02-07T08:00:00Z | Author: COPILOT | Change: workspace setup
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OLLAMA_BASE = "http://127.0.0.1:11434"
STATE_FILE = WORKSPACE_ROOT / ".slate_warmup_state.json"
LOG_DIR = WORKSPACE_ROOT / "slate_logs" / "warmup"

# Models to preload with their keep-alive durations
PRELOAD_MODELS = [
    {"name": "slate-coder:latest", "gpu": 0, "keep_alive": "24h", "priority": 1},
    {"name": "slate-fast:latest", "gpu": 1, "keep_alive": "24h", "priority": 1},
    {"name": "slate-planner:latest", "gpu": 0, "keep_alive": "12h", "priority": 2},
    {"name": "nomic-embed-text:latest", "gpu": 1, "keep_alive": "24h", "priority": 1},
]

# Ollama environment configuration for dual-GPU persistence
OLLAMA_ENV_CONFIG = {
    "CUDA_VISIBLE_DEVICES": "0,1",
    "OLLAMA_HOST": "127.0.0.1:11434",
    "OLLAMA_NUM_PARALLEL": "4",
    "OLLAMA_MAX_LOADED_MODELS": "6",
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KEEP_ALIVE": "24h",
}

# Embedding index refresh interval (seconds)
INDEX_REFRESH_INTERVAL = 6 * 3600  # 6 hours


class SlateWarmup:
    """Handles SLATE system initialization and GPU warmup."""

    # Modified: 2026-02-07T08:00:00Z | Author: COPILOT | Change: warmup system core
    def __init__(self):
        self.workspace = WORKSPACE_ROOT
        self.state = self._load_state()
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "last_warmup": None,
            "last_preload": None,
            "last_index": None,
            "models_loaded": [],
            "warmup_count": 0,
            "preload_failures": [],
            "index_stats": {},
        }

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2, default=str), encoding="utf-8")

    def _log(self, msg: str, level: str = "INFO"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"[{ts}] [WARMUP] [{level}] {msg}"
        print(line)
        log_file = LOG_DIR / f"warmup_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _ollama_request(self, path: str, data: dict | None = None,
                        timeout: int = 120) -> dict:
        """Make request to Ollama API."""
        url = f"{OLLAMA_BASE}{path}"
        if data:
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=body,
                                        headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))

    # ------------------------------------------------------------------
    # Ollama Configuration
    # ------------------------------------------------------------------

    def configure_ollama_env(self) -> dict:
        """Set Ollama environment variables for dual-GPU persistence."""
        actions = []

        # Set env vars in current process
        for key, value in OLLAMA_ENV_CONFIG.items():
            os.environ[key] = value
            actions.append(f"Set {key}={value}")

        # Write .ollama_env for runner hooks
        env_file = self.workspace / ".ollama_env"
        env_lines = [
            f"# SLATE Ollama Configuration — Auto-generated",
            f"# Modified: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} | Author: COPILOT",
            "",
        ]
        for key, value in OLLAMA_ENV_CONFIG.items():
            env_lines.append(f"{key}={value}")
        env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        actions.append(f"Wrote {env_file.name}")

        self._log(f"Configured Ollama: {len(actions)} settings applied")
        return {"success": True, "actions": actions}

    # ------------------------------------------------------------------
    # Model Preloading
    # ------------------------------------------------------------------

    def preload_models(self) -> dict:
        """Preload SLATE models onto GPUs with persistent keep-alive."""
        self._log("Starting model preload...")
        results = {}
        loaded = []
        failures = []

        # Check available models
        try:
            available = {m.get("name") for m in self._ollama_request("/api/tags", timeout=5).get("models", [])}
        except Exception as e:
            return {"success": False, "error": f"Cannot reach Ollama: {e}"}

        # Sort by priority (load most important first)
        sorted_models = sorted(PRELOAD_MODELS, key=lambda m: m["priority"])

        for model_spec in sorted_models:
            model_name = model_spec["name"]
            keep_alive = model_spec["keep_alive"]

            if model_name not in available:
                self._log(f"  SKIP {model_name} — not available", "WARN")
                failures.append({"model": model_name, "error": "not available"})
                continue

            try:
                self._log(f"  Loading {model_name} (keep_alive={keep_alive})...")
                start = time.time()

                if "embed" in model_name:
                    # Embedding model — use embed API
                    self._ollama_request("/api/embed", {
                        "model": model_name,
                        "input": "SLATE warmup initialization",
                        "keep_alive": keep_alive,
                    }, timeout=60)
                else:
                    # Generation model — use generate API with keep_alive
                    self._ollama_request("/api/generate", {
                        "model": model_name,
                        "prompt": "Ready.",
                        "stream": False,
                        "keep_alive": keep_alive,
                        "options": {"num_predict": 1},
                    }, timeout=120)

                elapsed = round(time.time() - start, 1)
                self._log(f"  Loaded {model_name} in {elapsed}s")
                results[model_name] = {"success": True, "elapsed_s": elapsed}
                loaded.append(model_name)

            except Exception as e:
                self._log(f"  FAIL {model_name}: {e}", "ERROR")
                results[model_name] = {"success": False, "error": str(e)[:100]}
                failures.append({"model": model_name, "error": str(e)[:100]})

        # Verify GPU usage
        gpu_status = self._get_gpu_usage()

        # Update state
        self.state["last_preload"] = datetime.now(timezone.utc).isoformat()
        self.state["models_loaded"] = loaded
        self.state["preload_failures"] = failures
        self._save_state()

        self._log(f"Preload complete: {len(loaded)}/{len(sorted_models)} models loaded")

        return {
            "success": len(loaded) > 0,
            "loaded": len(loaded),
            "total": len(sorted_models),
            "models": results,
            "gpu_status": gpu_status,
        }

    def _get_gpu_usage(self) -> list[dict]:
        """Get current GPU memory usage."""
        try:
            r = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            gpus = []
            for line in r.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append({
                        "gpu": int(parts[0]),
                        "used_mb": int(parts[1]),
                        "total_mb": int(parts[2]),
                        "util_pct": int(parts[3]),
                    })
            return gpus
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Codebase Embedding Index
    # ------------------------------------------------------------------

    def build_embeddings(self, force: bool = False) -> dict:
        """Build or refresh codebase embedding index."""
        # Check if index is fresh enough
        if not force and self.state.get("last_index"):
            try:
                last = datetime.fromisoformat(self.state["last_index"].replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - last).total_seconds()
                if age < INDEX_REFRESH_INTERVAL:
                    self._log(f"Embedding index is fresh ({age/3600:.1f}h old), skipping")
                    return {"status": "fresh", "age_hours": round(age / 3600, 1)}
            except Exception:
                pass

        self._log("Building codebase embedding index...")
        try:
            from slate.ml_orchestrator import MLOrchestrator
            ml = MLOrchestrator()
            result = ml.index_codebase()
            self.state["last_index"] = datetime.now(timezone.utc).isoformat()
            self.state["index_stats"] = {
                "files": result.get("total_files", 0),
                "chunks": result.get("total_chunks", 0),
            }
            self._save_state()
            self._log(f"Index built: {result.get('total_files', 0)} files, {result.get('total_chunks', 0)} chunks")
            return {"status": "built", **result}
        except Exception as e:
            self._log(f"Index build failed: {e}", "ERROR")
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------
    # Full Warmup
    # ------------------------------------------------------------------

    def warmup(self, skip_index: bool = False) -> dict:
        """Run full SLATE warmup sequence."""
        self._log("=" * 50)
        self._log("SLATE System Warmup Starting")
        self._log("=" * 50)
        start = time.time()

        results = {}

        # Step 1: Configure Ollama
        self._log("\n--- Step 1: Configure Ollama ---")
        results["configure"] = self.configure_ollama_env()

        # Step 2: Ensure SLATE models exist
        self._log("\n--- Step 2: Ensure SLATE Models ---")
        try:
            from slate.ml_orchestrator import MLOrchestrator
            ml = MLOrchestrator()
            results["models"] = ml.ensure_slate_models()
            self._log(f"Models: {results['models'].get('status', 'unknown')}")
        except Exception as e:
            results["models"] = {"status": "error", "error": str(e)}
            self._log(f"Model check failed: {e}", "ERROR")

        # Step 3: Preload models onto GPUs
        self._log("\n--- Step 3: Preload Models ---")
        results["preload"] = self.preload_models()

        # Step 4: Build embedding index
        if not skip_index:
            self._log("\n--- Step 4: Build Embedding Index ---")
            results["index"] = self.build_embeddings()
        else:
            results["index"] = {"status": "skipped"}

        # Step 5: Verify readiness
        self._log("\n--- Step 5: Verify Readiness ---")
        results["verify"] = self._verify_readiness()

        elapsed = round(time.time() - start, 1)

        # Update state
        self.state["last_warmup"] = datetime.now(timezone.utc).isoformat()
        self.state["warmup_count"] += 1
        self._save_state()

        self._log(f"\nWarmup complete in {elapsed}s")
        self._log(f"  Models loaded: {results['preload'].get('loaded', 0)}")
        self._log(f"  GPUs active: {len([g for g in results['preload'].get('gpu_status', []) if g.get('used_mb', 0) > 100])}")
        self._log(f"  Ready: {results['verify'].get('ready', False)}")
        self._log("=" * 50)

        results["elapsed_s"] = elapsed
        return results

    def _verify_readiness(self) -> dict:
        """Verify the system is ready for autonomous work."""
        checks = {}

        # Check loaded models
        try:
            loaded = self._ollama_request("/api/ps", timeout=5).get("models", [])
            checks["models_in_vram"] = len(loaded)
            checks["model_names"] = [m.get("name", "?") for m in loaded]
        except Exception:
            checks["models_in_vram"] = 0
            checks["model_names"] = []

        # Check GPU usage
        gpus = self._get_gpu_usage()
        checks["gpus_active"] = len([g for g in gpus if g.get("used_mb", 0) > 100])
        checks["gpu_details"] = gpus

        # Quick inference test
        try:
            start = time.time()
            self._ollama_request("/api/generate", {
                "model": "slate-fast:latest",
                "prompt": "ping",
                "stream": False,
                "keep_alive": "24h",
                "options": {"num_predict": 5},
            }, timeout=30)
            checks["inference_latency_ms"] = round((time.time() - start) * 1000)
            checks["inference_ok"] = True
        except Exception as e:
            checks["inference_ok"] = False
            checks["inference_error"] = str(e)[:80]

        checks["ready"] = (
            checks.get("models_in_vram", 0) >= 2
            and checks.get("gpus_active", 0) >= 1
            and checks.get("inference_ok", False)
        )

        return checks

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get warmup status."""
        # Current loaded models
        loaded = []
        try:
            loaded = self._ollama_request("/api/ps", timeout=5).get("models", [])
        except Exception:
            pass

        return {
            "last_warmup": self.state.get("last_warmup"),
            "last_preload": self.state.get("last_preload"),
            "last_index": self.state.get("last_index"),
            "warmup_count": self.state.get("warmup_count", 0),
            "models_loaded": [m.get("name", "?") for m in loaded],
            "models_loaded_count": len(loaded),
            "gpu_status": self._get_gpu_usage(),
            "index_stats": self.state.get("index_stats", {}),
            "preload_failures": self.state.get("preload_failures", []),
        }

    def print_status(self):
        """Print human-readable warmup status."""
        s = self.get_status()
        print("=" * 60)
        print("  SLATE Warmup Status")
        print("=" * 60)
        print(f"\n  Last Warmup:  {s.get('last_warmup', 'Never')}")
        print(f"  Warmup Count: {s.get('warmup_count', 0)}")
        print(f"  Last Preload: {s.get('last_preload', 'Never')}")
        print(f"  Last Index:   {s.get('last_index', 'Never')}")

        print(f"\n  Models in VRAM ({s['models_loaded_count']}):")
        if s["models_loaded"]:
            for m in s["models_loaded"]:
                print(f"    - {m}")
        else:
            print("    (none — models need preloading)")

        print(f"\n  GPU Status:")
        for g in s.get("gpu_status", []):
            pct = g["used_mb"] / max(g["total_mb"], 1) * 100
            print(f"    GPU {g['gpu']}: {g['used_mb']} / {g['total_mb']} MB ({pct:.0f}%), util {g['util_pct']}%")

        idx = s.get("index_stats", {})
        if idx:
            print(f"\n  Embedding Index: {idx.get('files', 0)} files, {idx.get('chunks', 0)} chunks")
        else:
            print(f"\n  Embedding Index: Not built")

        if s.get("preload_failures"):
            print(f"\n  Preload Failures:")
            for f in s["preload_failures"]:
                print(f"    x {f['model']}: {f['error']}")

        print("\n" + "=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SLATE System Warmup")
    parser.add_argument("--preload-only", action="store_true", help="Only preload models")
    parser.add_argument("--index-only", action="store_true", help="Only build embeddings")
    parser.add_argument("--status", action="store_true", help="Show warmup status")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if fresh")
    args = parser.parse_args()

    warmup = SlateWarmup()

    if args.status:
        if args.json:
            print(json.dumps(warmup.get_status(), indent=2, default=str))
        else:
            warmup.print_status()
    elif args.preload_only:
        warmup.configure_ollama_env()
        result = warmup.preload_models()
        print(json.dumps(result, indent=2, default=str) if args.json
              else f"Loaded {result['loaded']}/{result['total']} models")
    elif args.index_only:
        result = warmup.build_embeddings(force=args.force)
        print(json.dumps(result, indent=2, default=str) if args.json
              else f"Index: {result.get('status', 'unknown')}")
    else:
        result = warmup.warmup()
        if args.json:
            print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
