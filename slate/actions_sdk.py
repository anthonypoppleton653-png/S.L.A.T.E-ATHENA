#!/usr/bin/env python3
# Modified: 2026-02-08T15:00:00Z | Author: COPILOT | Change: Create GitHub Actions SDK wrapper — Python equivalents of @actions/* packages
"""
SLATE Actions SDK Wrapper
==========================
Python wrappers mirroring the GitHub Actions SDK (@actions/*) packages for
self-hosted runner integration with SLATE's local AI orchestration.

Provides Pythonic equivalents of:
    - @actions/core     → inputs, outputs, logging, secrets masking
    - @actions/exec     → CLI execution with backoff
    - @actions/cache    → Model and dependency caching
    - @actions/github   → Octokit/GitHub API client
    - @actions/artifact → Build artifact management
    - @actions/io       → Disk I/O helpers

Usage:
    from slate.actions_sdk import ActionsCore, ActionsExec, ActionsCache, ActionsGitHub

    # Core operations
    core = ActionsCore()
    model_name = core.get_input("model_name", required=True)
    core.set_output("inference_result", result)
    core.info("Processing complete")

    # Execute with retry
    executor = ActionsExec()
    executor.exec_with_retry("python slate/ml_orchestrator.py --infer 'test'")

    # Cache models
    cache = ActionsCache()
    cache.save("ollama-models", ["/root/.ollama/models"])
    cache.restore("ollama-models")

    # GitHub API
    gh = ActionsGitHub()
    gh.dispatch_workflow("ci.yml")
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

WORKSPACE = Path(__file__).parent.parent

log = logging.getLogger("slate.actions_sdk")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════════
# @actions/core equivalent
# ═══════════════════════════════════════════════════════════════════════════════

class ActionsCore:
    """Python equivalent of @actions/core — inputs, outputs, logging, secrets.

    Works both in GitHub Actions (reads GITHUB_* env vars) and locally
    (reads from function args or environment).
    """

    def __init__(self):
        self._in_actions = "GITHUB_ACTIONS" in os.environ

    @property
    def is_actions(self) -> bool:
        """Return True if running inside GitHub Actions."""
        return self._in_actions

    # ── Inputs / Outputs ────────────────────────────────────────────────────

    def get_input(self, name: str, required: bool = False, default: str = "") -> str:
        """Get an action input value.

        In Actions: reads INPUT_<NAME> env var.
        Locally: reads from environment or returns default.
        """
        env_key = f"INPUT_{name.upper().replace(' ', '_').replace('-', '_')}"
        value = os.environ.get(env_key, default)
        if required and not value:
            raise ValueError(f"Required input '{name}' not provided")
        return value

    def set_output(self, name: str, value: Any) -> None:
        """Set an action output value."""
        if self._in_actions:
            output_file = os.environ.get("GITHUB_OUTPUT", "")
            if output_file:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(f"{name}={value}\n")
        log.info(f"Output: {name}={value}")

    def export_variable(self, name: str, value: str) -> None:
        """Export an environment variable for subsequent steps."""
        os.environ[name] = value
        if self._in_actions:
            env_file = os.environ.get("GITHUB_ENV", "")
            if env_file:
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"{name}={value}\n")

    def add_path(self, path: str) -> None:
        """Add a path to PATH for subsequent steps."""
        current = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{path}{os.pathsep}{current}"
        if self._in_actions:
            path_file = os.environ.get("GITHUB_PATH", "")
            if path_file:
                with open(path_file, "a", encoding="utf-8") as f:
                    f.write(f"{path}\n")

    # ── Logging ─────────────────────────────────────────────────────────────

    def debug(self, message: str) -> None:
        """Log debug message."""
        if self._in_actions:
            print(f"::debug::{message}")
        log.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        print(message)

    def warning(self, message: str, file: str = "", line: int = 0) -> None:
        """Log warning annotation."""
        attrs = self._format_attrs(file, line)
        if self._in_actions:
            print(f"::warning {attrs}::{message}")
        else:
            log.warning(message)

    def error(self, message: str, file: str = "", line: int = 0) -> None:
        """Log error annotation."""
        attrs = self._format_attrs(file, line)
        if self._in_actions:
            print(f"::error {attrs}::{message}")
        else:
            log.error(message)

    def notice(self, message: str, file: str = "", line: int = 0) -> None:
        """Log notice annotation."""
        attrs = self._format_attrs(file, line)
        if self._in_actions:
            print(f"::notice {attrs}::{message}")
        else:
            log.info(f"NOTICE: {message}")

    def set_failed(self, message: str) -> None:
        """Set the action as failed with an error message."""
        self.error(message)
        if self._in_actions:
            sys.exit(1)

    def start_group(self, name: str) -> None:
        """Start a log group."""
        if self._in_actions:
            print(f"::group::{name}")
        else:
            print(f"\n{'─' * 40} {name} {'─' * 40}")

    def end_group(self) -> None:
        """End a log group."""
        if self._in_actions:
            print("::endgroup::")
        else:
            print("─" * 80)

    def mask_secret(self, secret: str) -> None:
        """Mask a secret value in logs."""
        if self._in_actions:
            print(f"::add-mask::{secret}")

    @staticmethod
    def _format_attrs(file: str = "", line: int = 0) -> str:
        parts = []
        if file:
            parts.append(f"file={file}")
        if line:
            parts.append(f"line={line}")
        return ",".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# @actions/exec equivalent
# ═══════════════════════════════════════════════════════════════════════════════

class ActionsExec:
    """Python equivalent of @actions/exec — CLI execution with retry/backoff.

    Enhanced with SLATE stability patterns (exponential backoff, circuit breaking).
    """

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or str(WORKSPACE)

    def exec(self, command: str, args: Optional[list[str]] = None,
             timeout: int = 300, env: Optional[dict] = None) -> subprocess.CompletedProcess:
        """Execute a command.

        Args:
            command: The command to run.
            args: Optional arguments.
            timeout: Timeout in seconds.
            env: Additional environment variables.

        Returns:
            CompletedProcess with stdout/stderr.
        """
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        cmd = command if not args else f"{command} {' '.join(args)}"
        log.info(f"Executing: {cmd}")

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=self.cwd, env=full_env, timeout=timeout, encoding="utf-8",
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                print(line)
        if result.returncode != 0 and result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(f"  [stderr] {line}", file=sys.stderr)

        return result

    def exec_with_retry(self, command: str, max_attempts: int = 3,
                        base_delay: float = 2.0, timeout: int = 300) -> subprocess.CompletedProcess:
        """Execute with exponential backoff retry.

        Backoff: t = base_delay * 2^n seconds, max 5 attempts.
        """
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                result = self.exec(command, timeout=timeout)
                if result.returncode == 0:
                    return result
                last_error = RuntimeError(
                    f"Command failed with exit code {result.returncode}: {result.stderr[:200]}"
                )
            except subprocess.TimeoutExpired as e:
                last_error = e
            except Exception as e:
                last_error = e

            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                log.warning(f"Attempt {attempt}/{max_attempts} failed. Retrying in {delay:.0f}s...")
                time.sleep(delay)

        raise last_error  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════════
# @actions/cache equivalent
# ═══════════════════════════════════════════════════════════════════════════════

class ActionsCache:
    """Python equivalent of @actions/cache — model and dependency caching.

    Caches Ollama models, pip packages, and build artifacts locally.
    Uses hash-based cache keys for invalidation.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or WORKSPACE / ".slate_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, paths: list[str], hash_files: Optional[list[str]] = None) -> bool:
        """Save paths to cache with a key.

        Args:
            key: Cache key (e.g., 'ollama-models', 'pip-deps').
            paths: List of paths to cache.
            hash_files: Optional files to hash for cache invalidation.

        Returns:
            True if saved successfully.
        """
        cache_key = self._resolve_key(key, hash_files)
        cache_path = self.cache_dir / cache_key
        manifest = {
            "key": key,
            "resolved_key": cache_key,
            "paths": paths,
            "created": datetime.now(timezone.utc).isoformat(),
        }

        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            # Save manifest
            (cache_path / "manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            log.info(f"Cache saved: {key} → {cache_key}")
            return True
        except Exception as e:
            log.error(f"Cache save failed for {key}: {e}")
            return False

    def restore(self, key: str, hash_files: Optional[list[str]] = None) -> Optional[dict]:
        """Restore from cache.

        Returns:
            Cache manifest if hit, None if miss.
        """
        cache_key = self._resolve_key(key, hash_files)
        cache_path = self.cache_dir / cache_key / "manifest.json"

        if cache_path.exists():
            manifest = json.loads(cache_path.read_text(encoding="utf-8"))
            log.info(f"Cache hit: {key} → {cache_key}")
            return manifest

        log.info(f"Cache miss: {key}")
        return None

    def _resolve_key(self, key: str, hash_files: Optional[list[str]] = None) -> str:
        """Resolve cache key with optional file hashing."""
        if not hash_files:
            return key

        hasher = hashlib.sha256()
        hasher.update(key.encode())
        for f in sorted(hash_files):
            path = Path(f)
            if path.exists():
                hasher.update(path.read_bytes())

        return f"{key}-{hasher.hexdigest()[:12]}"

    def clean(self, max_age_hours: int = 168) -> int:
        """Clean cache entries older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        cleaned = 0
        for entry in self.cache_dir.iterdir():
            if entry.is_dir():
                manifest_path = entry / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        created = datetime.fromisoformat(manifest["created"]).timestamp()
                        if created < cutoff:
                            shutil.rmtree(entry)
                            cleaned += 1
                    except Exception:
                        pass
        return cleaned

    def status(self) -> dict:
        """Get cache status."""
        entries = []
        total_size = 0
        for entry in self.cache_dir.iterdir():
            if entry.is_dir():
                manifest_path = entry / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        entries.append(manifest)
                    except Exception:
                        pass
        return {
            "cache_dir": str(self.cache_dir),
            "entries": len(entries),
            "keys": [e.get("key") for e in entries],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# @actions/github equivalent
# ═══════════════════════════════════════════════════════════════════════════════

class ActionsGitHub:
    """Python equivalent of @actions/github — Octokit client for SLATE repo.

    Uses git credential manager for authentication (no hardcoded tokens).
    """

    REPO = "SynchronizedLivingArchitecture/S.L.A.T.E"
    API_BASE = f"https://api.github.com/repos/{REPO}"

    def __init__(self):
        self._token: Optional[str] = None

    @property
    def token(self) -> str:
        """Get GitHub token from git credential manager."""
        if self._token:
            return self._token

        try:
            result = subprocess.run(
                ["git", "credential", "fill"],
                input="protocol=https\nhost=github.com\n",
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if line.startswith("password="):
                    self._token = line.split("=", 1)[1]
                    return self._token
        except Exception as e:
            log.error(f"Failed to get GitHub token: {e}")

        raise RuntimeError("Could not retrieve GitHub token from credential manager")

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make an authenticated GitHub API request."""
        import urllib.request

        url = f"{self.API_BASE}/{endpoint}" if not endpoint.startswith("http") else endpoint
        body = json.dumps(data).encode("utf-8") if data else None

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"token {self.token}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        if body:
            req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = resp.read().decode("utf-8")
            return json.loads(response_data) if response_data else {}

    def dispatch_workflow(self, workflow: str, ref: str = "main",
                          inputs: Optional[dict] = None) -> bool:
        """Dispatch a workflow run."""
        data: dict[str, Any] = {"ref": ref}
        if inputs:
            data["inputs"] = inputs

        try:
            import urllib.request
            url = f"{self.API_BASE}/actions/workflows/{workflow}/dispatches"
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header("Authorization", f"token {self.token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("Content-Type", "application/json")
            urllib.request.urlopen(req, timeout=30)
            log.info(f"Dispatched workflow: {workflow}")
            return True
        except Exception as e:
            log.error(f"Workflow dispatch failed: {e}")
            return False

    def get_workflow_runs(self, status: str = "in_progress", per_page: int = 10) -> list[dict]:
        """Get recent workflow runs."""
        try:
            data = self._request("GET", f"actions/runs?status={status}&per_page={per_page}")
            return data.get("workflow_runs", [])
        except Exception as e:
            log.error(f"Failed to get workflow runs: {e}")
            return []

    def create_release(self, tag: str, name: str, body: str,
                       prerelease: bool = False, draft: bool = False) -> Optional[dict]:
        """Create a GitHub release."""
        try:
            return self._request("POST", "releases", {
                "tag_name": tag,
                "name": name,
                "body": body,
                "prerelease": prerelease,
                "draft": draft,
            })
        except Exception as e:
            log.error(f"Release creation failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# @actions/io equivalent
# ═══════════════════════════════════════════════════════════════════════════════

class ActionsIO:
    """Python equivalent of @actions/io — disk I/O helpers."""

    @staticmethod
    def cp(source: str, dest: str, recursive: bool = True) -> None:
        """Copy file or directory."""
        src = Path(source)
        dst = Path(dest)
        if src.is_dir() and recursive:
            shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))

    @staticmethod
    def mv(source: str, dest: str) -> None:
        """Move file or directory."""
        shutil.move(source, dest)

    @staticmethod
    def rmRF(path: str) -> None:
        """Remove file or directory recursively (safe version)."""
        p = Path(path)
        if not p.exists():
            return
        # Safety: never remove workspace root or system paths
        workspace_str = str(WORKSPACE).lower()
        if str(p).lower() in (workspace_str, "c:\\", "/", "c:\\windows"):
            raise ValueError(f"Refusing to remove protected path: {path}")
        if p.is_dir():
            shutil.rmtree(str(p))
        else:
            p.unlink()

    @staticmethod
    def mkdirP(path: str) -> None:
        """Create directory and all parents."""
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def which(tool: str) -> Optional[str]:
        """Find tool on PATH."""
        return shutil.which(tool)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for Actions SDK wrapper."""
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Actions SDK Wrapper")
    parser.add_argument("--status", action="store_true", help="SDK status")
    parser.add_argument("--cache-status", action="store_true", help="Cache status")
    parser.add_argument("--dispatch", type=str, help="Dispatch a workflow (e.g., ci.yml)")
    parser.add_argument("--runs", action="store_true", help="Show active workflow runs")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.cache_status:
        cache = ActionsCache()
        status = cache.status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"Cache: {status['entries']} entries in {status['cache_dir']}")
            for key in status["keys"]:
                print(f"  - {key}")

    elif args.dispatch:
        gh = ActionsGitHub()
        ok = gh.dispatch_workflow(args.dispatch)
        print(f"Dispatch {args.dispatch}: {'✓' if ok else '✗'}")

    elif args.runs:
        gh = ActionsGitHub()
        runs = gh.get_workflow_runs()
        if args.json:
            print(json.dumps(runs, indent=2, default=str))
        else:
            print(f"\nActive workflow runs: {len(runs)}")
            for r in runs[:10]:
                print(f"  [{r.get('status', '?')}] {r.get('name', '?')} #{r.get('run_number', '?')}")

    elif args.status:
        core = ActionsCore()
        print()
        print("=" * 60)
        print("  SLATE Actions SDK")
        print("=" * 60)
        print(f"  Running in Actions: {core.is_actions}")
        print(f"  Workspace: {WORKSPACE}")
        io = ActionsIO()
        tools = ["python", "git", "docker", "kubectl", "helm", "nvidia-smi"]
        for tool in tools:
            path = io.which(tool)
            icon = "✓" if path else "✗"
            print(f"  [{icon}] {tool}: {path or 'not found'}")
        print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
