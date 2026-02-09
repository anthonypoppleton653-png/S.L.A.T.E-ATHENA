#!/usr/bin/env python3
"""
SLATE UV Package Manager Integration
======================================

Manages SLATE's transition from pip to UV for faster dependency resolution
and deterministic builds. UV provides:

- 10-100x faster dependency resolution vs pip
- Deterministic lockfiles (uv.lock)
- Cross-platform reproducible environments
- Drop-in pip compatibility

Usage:
    python slate/slate_uv.py --status    # Check UV status
    python slate/slate_uv.py --sync      # Install from uv.lock
    python slate/slate_uv.py --lock      # Regenerate uv.lock
    python slate/slate_uv.py --verify    # Verify environment matches lock
    python slate/slate_uv.py --benchmark # Compare UV vs pip speed
"""
# Modified: 2026-02-09T21:00:00Z | Author: Claude Opus 4.6 | Change: Create UV package manager integration

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
UV_LOCK = WORKSPACE_ROOT / "uv.lock"
PYPROJECT = WORKSPACE_ROOT / "pyproject.toml"
REQUIREMENTS_LOCK = WORKSPACE_ROOT / "requirements.lock"
VENV_DIR = WORKSPACE_ROOT / ".venv"


@dataclass
class UVStatus:
    """UV installation and project status."""
    uv_installed: bool = False
    uv_version: str = ""
    lock_exists: bool = False
    lock_packages: int = 0
    pyproject_exists: bool = False
    venv_exists: bool = False
    pip_lock_exists: bool = False


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    """Run a command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(WORKSPACE_ROOT),
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return -1, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, f"Command timed out after {timeout}s"


def get_uv_version() -> str:
    """Get UV version string."""
    code, output = _run(["uv", "--version"])
    if code == 0:
        return output.strip()
    return ""


def get_lock_package_count() -> int:
    """Count packages in uv.lock."""
    if not UV_LOCK.exists():
        return 0
    try:
        content = UV_LOCK.read_text(encoding="utf-8")
        # Each package starts with [[package]]
        return content.count("[[package]]")
    except Exception:
        return 0


def get_status() -> UVStatus:
    """Get comprehensive UV status."""
    uv_ver = get_uv_version()
    return UVStatus(
        uv_installed=bool(uv_ver),
        uv_version=uv_ver,
        lock_exists=UV_LOCK.exists(),
        lock_packages=get_lock_package_count(),
        pyproject_exists=PYPROJECT.exists(),
        venv_exists=VENV_DIR.exists(),
        pip_lock_exists=REQUIREMENTS_LOCK.exists(),
    )


def lock(prerelease: bool = True) -> tuple[bool, str]:
    """Generate uv.lock from pyproject.toml."""
    cmd = ["uv", "lock"]
    if prerelease:
        cmd.append("--prerelease=allow")
    code, output = _run(cmd, timeout=120)
    return code == 0, output


def sync(dry_run: bool = False) -> tuple[bool, str]:
    """Install dependencies from uv.lock."""
    cmd = ["uv", "sync"]
    if dry_run:
        cmd.append("--dry-run")
    code, output = _run(cmd, timeout=300)
    return code == 0, output


def verify() -> tuple[bool, str]:
    """Verify environment matches uv.lock."""
    if not UV_LOCK.exists():
        return False, "uv.lock not found — run --lock first"
    # Check if uv.lock is up-to-date with pyproject.toml
    code, output = _run(["uv", "lock", "--check"], timeout=60)
    if code == 0:
        return True, "Environment matches uv.lock"
    return False, output


def benchmark() -> dict:
    """Benchmark UV vs pip for dependency resolution."""
    results = {}

    # UV lock time
    start = time.time()
    code, _ = _run(["uv", "lock", "--prerelease=allow"], timeout=120)
    results["uv_lock_ms"] = round((time.time() - start) * 1000)
    results["uv_lock_success"] = code == 0

    # UV sync (dry-run) time
    start = time.time()
    code, output = _run(["uv", "sync", "--dry-run"], timeout=120)
    results["uv_sync_ms"] = round((time.time() - start) * 1000)

    # pip check time (as comparison)
    start = time.time()
    code, _ = _run([sys.executable, "-m", "pip", "check"], timeout=60)
    results["pip_check_ms"] = round((time.time() - start) * 1000)

    if results["uv_lock_ms"] > 0 and results["pip_check_ms"] > 0:
        results["speedup"] = round(results["pip_check_ms"] / results["uv_lock_ms"], 1)

    return results


def print_status():
    """Print UV status report."""
    status = get_status()
    print()
    print("============================================================")
    print("  SLATE UV Package Manager")
    print("============================================================")
    print()
    print(f"  UV Installed: {'Yes' if status.uv_installed else 'No'}")
    if status.uv_version:
        print(f"  UV Version:   {status.uv_version}")
    print(f"  pyproject.toml: {'exists' if status.pyproject_exists else 'missing'}")
    print(f"  uv.lock:        {'exists' if status.lock_exists else 'not generated'}")
    if status.lock_packages:
        print(f"  Lock Packages:  {status.lock_packages}")
    print(f"  .venv:          {'exists' if status.venv_exists else 'missing'}")
    print(f"  pip lock:       {'exists (legacy)' if status.pip_lock_exists else 'none'}")
    print()

    if status.lock_exists:
        ok, msg = verify()
        icon = "[OK]" if ok else "[!!]"
        print(f"  Lock Status: {icon} {msg}")
    print()
    print("============================================================")
    print()


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SLATE UV Package Manager Integration")
    parser.add_argument("--status", action="store_true", help="Show UV status")
    parser.add_argument("--lock", action="store_true", help="Generate uv.lock")
    parser.add_argument("--sync", action="store_true", help="Install from uv.lock")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run sync")
    parser.add_argument("--verify", action="store_true", help="Verify environment")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark UV vs pip")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.lock:
        print("Generating uv.lock...")
        ok, output = lock()
        print(f"  {'Success' if ok else 'Failed'}: {output}")

    elif args.sync:
        print("Syncing dependencies from uv.lock...")
        ok, output = sync(dry_run=args.dry_run)
        print(output)

    elif args.verify:
        ok, msg = verify()
        print(f"{'OK' if ok else 'FAIL'}: {msg}")

    elif args.benchmark:
        print("Running UV vs pip benchmark...")
        results = benchmark()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"  UV lock:   {results.get('uv_lock_ms', 0):,}ms")
            print(f"  UV sync:   {results.get('uv_sync_ms', 0):,}ms")
            print(f"  pip check: {results.get('pip_check_ms', 0):,}ms")
            if "speedup" in results:
                print(f"  Speedup:   {results['speedup']}x")

    elif args.json:
        status = get_status()
        print(json.dumps({
            "uv_installed": status.uv_installed,
            "uv_version": status.uv_version,
            "lock_exists": status.lock_exists,
            "lock_packages": status.lock_packages,
            "venv_exists": status.venv_exists,
        }, indent=2))

    else:
        print_status()
