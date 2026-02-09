#!/usr/bin/env python3
# Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Create standalone update system for SLATE installations
"""
SLATE Updater — Upstream Update System
========================================
Pulls updates from the upstream SLATE repository, handles merge conflicts,
re-validates the ecosystem, updates Docker images, and syncs K8s configs.

Designed for end users who cloned/forked the SLATE repo and want to stay
current with the upstream mainline.

Update Pipeline:
    1. PRE-FLIGHT   — Validate git state; check for uncommitted changes
    2. FETCH        — Fetch upstream remote (adds if missing)
    3. MERGE        — Merge upstream/main with conflict detection
    4. DEPS         — Update pip deps, SLATE SDK, VS Code extension
    5. DOCKER       — Rebuild Docker images if Dockerfile changed
    6. K8S          — Re-apply K8s manifests if k8s/ changed
    7. VALIDATE     — Full ecosystem validation
    8. REPORT       — Summary of changes applied

Channels:
    stable  — Tagged releases only (default for --channel stable)
    main    — Latest main branch (default)
    beta    — Pre-release / beta branch

Usage:
    python slate/slate_updater.py --check                 # Check for available updates
    python slate/slate_updater.py --update                 # Full update from upstream/main
    python slate/slate_updater.py --update --channel stable # Update to latest release tag
    python slate/slate_updater.py --update --no-docker      # Skip Docker rebuild
    python slate/slate_updater.py --update --no-k8s         # Skip K8s re-apply
    python slate/slate_updater.py --update --dry-run        # Show what would change
    python slate/slate_updater.py --status                  # Current version info
    python slate/slate_updater.py --json                    # JSON output
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Initial updater module

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
UPSTREAM_URL = "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git"
UPSTREAM_REMOTE = "upstream"
UPDATE_STATE_FILE = WORKSPACE_ROOT / ".slate_update_state.json"


def _run(cmd: list[str], cwd: str | None = None,
         timeout: int = 120, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command safely."""
    try:
        return subprocess.run(
            cmd,
            cwd=cwd or str(WORKSPACE_ROOT),
            capture_output=capture,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 1, "", "timeout")
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 1, "", f"not found: {cmd[0]}")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def _cmd_exists(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    import shutil
    return shutil.which(cmd) is not None


def _get_python() -> Path:
    """Get the Python executable path."""
    venv_py = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return venv_py
    venv_py_unix = WORKSPACE_ROOT / ".venv" / "bin" / "python"
    if venv_py_unix.exists():
        return venv_py_unix
    return Path(sys.executable)


def _get_pip() -> Path:
    """Get the pip executable path."""
    venv_pip = WORKSPACE_ROOT / ".venv" / "Scripts" / "pip.exe"
    if venv_pip.exists():
        return venv_pip
    venv_pip_unix = WORKSPACE_ROOT / ".venv" / "bin" / "pip"
    if venv_pip_unix.exists():
        return venv_pip_unix
    return Path(sys.executable).parent / "pip"


class SlateUpdater:
    """
    Manages upstream updates for SLATE installations.

    Handles fetching from upstream, merging changes, updating
    dependencies, rebuilding Docker images, and re-applying K8s configs.
    """

    def __init__(self, workspace: Path | None = None):
        # Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Updater init
        self.workspace = workspace or WORKSPACE_ROOT
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.steps_done: list[str] = []
        self.changes: list[str] = []

    # ── Logging ───────────────────────────────────────────────────────

    def _log(self, icon: str, msg: str):
        print(f"  {icon} {msg}")

    def _header(self, title: str):
        print(f"\n  ── {title} {'─' * max(1, 50 - len(title))}")

    # ── Git Helpers ───────────────────────────────────────────────────

    def _git(self, *args: str, timeout: int = 120) -> subprocess.CompletedProcess:
        """Run a git command in the workspace."""
        return _run(["git"] + list(args), cwd=str(self.workspace), timeout=timeout)

    def _get_current_version(self) -> str:
        """Get current SLATE version from pyproject.toml."""
        pyproject = self.workspace / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        return "unknown"

    def _get_current_branch(self) -> str:
        """Get current git branch name."""
        result = self._git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else "unknown"

    def _get_current_commit(self) -> str:
        """Get current git commit hash (short)."""
        result = self._git("rev-parse", "--short", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else "unknown"

    def _has_uncommitted_changes(self) -> bool:
        """Check for uncommitted changes in the working tree."""
        result = self._git("status", "--porcelain")
        return bool(result.stdout.strip()) if result.returncode == 0 else False

    def _ensure_upstream_remote(self) -> bool:
        """Ensure the 'upstream' remote exists, add it if missing."""
        result = self._git("remote", "get-url", UPSTREAM_REMOTE)
        if result.returncode == 0:
            return True

        # Add upstream remote
        result = self._git("remote", "add", UPSTREAM_REMOTE, UPSTREAM_URL)
        if result.returncode == 0:
            self._log("✓", f"Added upstream remote: {UPSTREAM_URL}")
            return True
        else:
            self._log("✗", f"Failed to add upstream remote: {result.stderr.strip()}")
            return False

    def _get_upstream_version(self) -> str:
        """Get version from upstream pyproject.toml (after fetch)."""
        result = self._git("show", f"{UPSTREAM_REMOTE}/main:pyproject.toml")
        if result.returncode == 0:
            match = re.search(r'version\s*=\s*"([^"]+)"', result.stdout)
            if match:
                return match.group(1)
        return "unknown"

    def _get_latest_release_tag(self) -> str | None:
        """Get the latest release tag from upstream."""
        result = self._git("tag", "--sort=-v:refname", "-l", "v*")
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
        return None

    def _get_changed_files_since(self, ref: str) -> list[str]:
        """Get list of files changed between HEAD and a ref."""
        result = self._git("diff", "--name-only", f"HEAD..{ref}")
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f]
        return []

    # ── Status ────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Get current installation status and version info."""
        # Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Status reporting
        version = self._get_current_version()
        branch = self._get_current_branch()
        commit = self._get_current_commit()
        has_changes = self._has_uncommitted_changes()

        # Check if upstream remote exists
        upstream_exists = self._git("remote", "get-url", UPSTREAM_REMOTE).returncode == 0

        # Load last update state
        last_update = None
        if UPDATE_STATE_FILE.exists():
            try:
                state = json.loads(UPDATE_STATE_FILE.read_text(encoding="utf-8"))
                last_update = state.get("last_update")
            except Exception:
                pass

        return {
            "version": version,
            "branch": branch,
            "commit": commit,
            "has_uncommitted_changes": has_changes,
            "upstream_remote": upstream_exists,
            "upstream_url": UPSTREAM_URL,
            "last_update": last_update,
            "workspace": str(self.workspace),
        }

    # ── Check ─────────────────────────────────────────────────────────

    def check(self) -> dict:
        """Check if updates are available from upstream."""
        # Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Update check logic
        print()
        print("═" * 64)
        print("  S.L.A.T.E. Update Check")
        print("═" * 64)

        current_version = self._get_current_version()
        current_commit = self._get_current_commit()
        self._log("ℹ", f"Current: v{current_version} ({current_commit})")

        # Ensure upstream remote
        if not self._ensure_upstream_remote():
            self._log("✗", "Cannot check for updates without upstream remote")
            return {"updates_available": False, "error": "no upstream remote"}

        # Fetch upstream
        self._header("Fetching Upstream")
        result = self._git("fetch", UPSTREAM_REMOTE, "--tags", timeout=60)
        if result.returncode != 0:
            self._log("✗", f"Fetch failed: {result.stderr.strip()[:200]}")
            return {"updates_available": False, "error": "fetch failed"}
        self._log("✓", "Fetched upstream")

        # Compare commits
        upstream_version = self._get_upstream_version()
        result = self._git("rev-list", "--count", f"HEAD..{UPSTREAM_REMOTE}/main")
        commits_behind = int(result.stdout.strip()) if result.returncode == 0 else 0

        result = self._git("rev-list", "--count", f"{UPSTREAM_REMOTE}/main..HEAD")
        commits_ahead = int(result.stdout.strip()) if result.returncode == 0 else 0

        # Check latest release tag
        latest_tag = self._get_latest_release_tag()

        # Changed files preview
        changed_files = []
        if commits_behind > 0:
            changed_files = self._get_changed_files_since(f"{UPSTREAM_REMOTE}/main")

        update_available = commits_behind > 0

        self._header("Update Status")
        if update_available:
            self._log("⬆", f"Updates available: {commits_behind} commits behind upstream")
            self._log("ℹ", f"Upstream version: v{upstream_version}")
            if latest_tag:
                self._log("ℹ", f"Latest release: {latest_tag}")
            if changed_files:
                categories = self._categorize_changes(changed_files)
                for cat, files in categories.items():
                    self._log("  ", f"  {cat}: {len(files)} file(s)")
        else:
            self._log("✓", "Already up to date!")

        if commits_ahead > 0:
            self._log("ℹ", f"Your fork is {commits_ahead} commit(s) ahead of upstream")

        print()

        return {
            "updates_available": update_available,
            "current_version": current_version,
            "upstream_version": upstream_version,
            "commits_behind": commits_behind,
            "commits_ahead": commits_ahead,
            "latest_tag": latest_tag,
            "changed_files": changed_files[:50],  # Cap at 50
            "has_uncommitted_changes": self._has_uncommitted_changes(),
        }

    def _categorize_changes(self, files: list[str]) -> dict[str, list[str]]:
        """Categorize changed files by area."""
        categories: dict[str, list[str]] = {}
        mappings = {
            "Core SDK": lambda f: f.startswith("slate/"),
            "Docker": lambda f: f.startswith("Dockerfile") or "docker-compose" in f,
            "Kubernetes": lambda f: f.startswith("k8s/") or f.startswith("helm/"),
            "Workflows": lambda f: f.startswith(".github/workflows/"),
            "Instructions": lambda f: "AGENTS.md" in f or "copilot-instructions" in f or "CLAUDE.md" in f,
            "Extensions": lambda f: f.startswith("plugins/"),
            "Tests": lambda f: f.startswith("tests/"),
            "Documentation": lambda f: f.startswith("docs/") or f.endswith(".md"),
            "Other": lambda f: True,
        }
        for f in files:
            placed = False
            for cat, check in mappings.items():
                if cat != "Other" and check(f):
                    categories.setdefault(cat, []).append(f)
                    placed = True
                    break
            if not placed:
                categories.setdefault("Other", []).append(f)
        return categories

    # ── Update ────────────────────────────────────────────────────────

    def update(self, channel: str = "main", rebuild_docker: bool = True,
               reapply_k8s: bool = True, dry_run: bool = False) -> dict:
        """
        Full update pipeline from upstream.

        Args:
            channel: Update channel — 'main', 'stable', or 'beta'
            rebuild_docker: Whether to rebuild Docker images if Dockerfile changed
            reapply_k8s: Whether to re-apply K8s manifests if k8s/ changed
            dry_run: If True, only show what would change without applying
        """
        # Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Full update pipeline
        print()
        print("═" * 64)
        print(f"  S.L.A.T.E. Update — Channel: {channel}")
        print("═" * 64)

        start_time = time.time()
        pre_version = self._get_current_version()
        pre_commit = self._get_current_commit()

        # ── Step 1: Pre-flight ────────────────────────────────────────
        self._header("Pre-flight Checks")
        if not (self.workspace / ".git").exists():
            self._log("✗", "Not a git repository")
            self.errors.append("Not a git repository")
            return self._report(start_time, pre_version, pre_commit)

        if not self._ensure_upstream_remote():
            self.errors.append("Cannot add upstream remote")
            return self._report(start_time, pre_version, pre_commit)

        has_changes = self._has_uncommitted_changes()
        if has_changes:
            self._log("⚠", "Uncommitted changes detected — will stash before merge")

        self._log("✓", "Pre-flight OK")
        self.steps_done.append("preflight")

        # ── Step 2: Fetch ─────────────────────────────────────────────
        self._header("Fetching Upstream")
        result = self._git("fetch", UPSTREAM_REMOTE, "--tags", timeout=60)
        if result.returncode != 0:
            self._log("✗", f"Fetch failed: {result.stderr.strip()[:200]}")
            self.errors.append("Upstream fetch failed")
            return self._report(start_time, pre_version, pre_commit)
        self._log("✓", "Fetched upstream + tags")
        self.steps_done.append("fetch")

        # Determine merge target
        if channel == "stable":
            tag = self._get_latest_release_tag()
            if tag:
                merge_ref = tag
                self._log("ℹ", f"Stable channel: merging tag {tag}")
            else:
                merge_ref = f"{UPSTREAM_REMOTE}/main"
                self._log("⚠", "No release tags found — falling back to main")
        elif channel == "beta":
            # Check if beta branch exists
            result = self._git("rev-parse", "--verify", f"{UPSTREAM_REMOTE}/beta")
            if result.returncode == 0:
                merge_ref = f"{UPSTREAM_REMOTE}/beta"
            else:
                merge_ref = f"{UPSTREAM_REMOTE}/main"
                self._log("⚠", "No beta branch — falling back to main")
        else:
            merge_ref = f"{UPSTREAM_REMOTE}/main"

        # Check what will change
        changed_files = self._get_changed_files_since(merge_ref)
        if not changed_files:
            self._log("✓", "Already up to date — nothing to merge")
            return self._report(start_time, pre_version, pre_commit)

        categories = self._categorize_changes(changed_files)
        self._log("ℹ", f"{len(changed_files)} file(s) will be updated:")
        for cat, files in categories.items():
            self._log("  ", f"  {cat}: {len(files)}")

        if dry_run:
            self._log("ℹ", "Dry run — no changes applied")
            return {
                "dry_run": True,
                "would_update": len(changed_files),
                "changed_files": changed_files,
                "categories": {k: len(v) for k, v in categories.items()},
                "merge_ref": merge_ref,
            }

        # ── Step 3: Stash & Merge ────────────────────────────────────
        self._header("Merging Updates")
        if has_changes:
            self._git("stash", "push", "-m", "slate-updater: pre-update stash")
            self._log("ℹ", "Stashed local changes")

        result = self._git("merge", merge_ref, "--no-edit", timeout=120)
        if result.returncode != 0:
            # Check for merge conflicts
            status = self._git("status", "--porcelain")
            conflicts = [l for l in status.stdout.split("\n") if l.startswith("UU ")]
            if conflicts:
                self._log("⚠", f"Merge conflicts in {len(conflicts)} file(s):")
                for c in conflicts[:10]:
                    self._log("  ", f"  {c[3:]}")
                self._log("ℹ", "Aborting merge — resolve manually with:")
                self._log("  ", "  git merge --abort  # to undo")
                self._log("  ", "  git mergetool      # to resolve")
                self._git("merge", "--abort")
                if has_changes:
                    self._git("stash", "pop")
                self.errors.append(f"Merge conflicts in {len(conflicts)} files")
                return self._report(start_time, pre_version, pre_commit)
            else:
                self._log("✗", f"Merge failed: {result.stderr.strip()[:200]}")
                if has_changes:
                    self._git("stash", "pop")
                self.errors.append("Merge failed")
                return self._report(start_time, pre_version, pre_commit)

        self._log("✓", f"Merged {merge_ref}")
        self.steps_done.append("merge")

        # Pop stash after successful merge
        if has_changes:
            pop_result = self._git("stash", "pop")
            if pop_result.returncode != 0:
                self._log("⚠", "Stash pop had conflicts — check your local changes")
                self.warnings.append("Stash pop conflicts — check local changes")
            else:
                self._log("✓", "Restored local changes")

        # ── Step 4: Update Dependencies ──────────────────────────────
        deps_changed = any(f in changed_files for f in
                           ["requirements.txt", "pyproject.toml", "setup.cfg", "setup.py"])
        if deps_changed:
            self._header("Updating Dependencies")
            pip = _get_pip()
            req_file = self.workspace / "requirements.txt"
            if req_file.exists() and pip.exists():
                result = _run(
                    [str(pip), "install", "-r", str(req_file), "--upgrade", "--quiet"],
                    cwd=str(self.workspace), timeout=600,
                )
                if result.returncode == 0:
                    self._log("✓", "pip dependencies updated")
                else:
                    self._log("⚠", "Some dependency updates failed")
                    self.warnings.append("Partial dependency update failure")

            # Re-install SLATE SDK in dev mode
            if (self.workspace / "pyproject.toml").exists():
                result = _run(
                    [str(pip), "install", "-e", str(self.workspace), "--quiet"],
                    cwd=str(self.workspace), timeout=120,
                )
                if result.returncode == 0:
                    self._log("✓", "SLATE SDK updated")

            self.steps_done.append("deps")
        else:
            self._log("ℹ", "No dependency changes — skipping")

        # ── Step 5: Update VS Code Extension ─────────────────────────
        ext_changed = any(f.startswith("plugins/slate-copilot/") for f in changed_files)
        if ext_changed:
            self._header("Rebuilding VS Code Extension")
            ext_dir = self.workspace / "plugins" / "slate-copilot"
            if ext_dir.exists() and _cmd_exists("npm"):
                _run(["npm", "install"], cwd=str(ext_dir), timeout=120)
                compile_result = _run(["npm", "run", "compile"],
                                      cwd=str(ext_dir), timeout=60)
                if compile_result.returncode == 0:
                    self._log("✓", "Extension compiled")
                    # Package and install if vsce available
                    if _cmd_exists("vsce"):
                        _run(["vsce", "package", "--no-dependencies"],
                             cwd=str(ext_dir), timeout=60)
                        vsix_files = list(ext_dir.glob("*.vsix"))
                        if vsix_files:
                            _run(["code", "--install-extension", str(vsix_files[-1])],
                                 timeout=60)
                            self._log("✓", "Extension installed in VS Code")
                    self.steps_done.append("extension")
                else:
                    self._log("⚠", "Extension compile failed")
                    self.warnings.append("Extension build failed — run manually")
            else:
                self._log("ℹ", "npm not available — skip extension build")

        # ── Step 6: Docker Rebuild ───────────────────────────────────
        docker_changed = any(
            f.startswith("Dockerfile") or "docker-compose" in f
            for f in changed_files
        )
        if docker_changed and rebuild_docker:
            self._header("Docker Image Rebuild")
            if _cmd_exists("docker"):
                result = _run(
                    ["docker", "compose", "build", "--no-cache"],
                    cwd=str(self.workspace), timeout=600,
                )
                if result.returncode == 0:
                    self._log("✓", "Docker images rebuilt")
                    self.steps_done.append("docker")
                else:
                    self._log("⚠", "Docker build failed — run manually")
                    self.warnings.append("Docker build failed")
            else:
                self._log("ℹ", "Docker not installed — skipping")
        elif docker_changed:
            self._log("ℹ", "Docker files changed but --no-docker flag set")

        # ── Step 7: Kubernetes Re-apply ──────────────────────────────
        k8s_changed = any(
            f.startswith("k8s/") or f.startswith("helm/")
            for f in changed_files
        )
        if k8s_changed and reapply_k8s:
            self._header("Kubernetes Manifests")
            if _cmd_exists("kubectl"):
                # Check if cluster is accessible
                result = _run(["kubectl", "cluster-info"], timeout=10)
                if result.returncode == 0:
                    # Re-apply kustomize overlay
                    kustomize_dir = self.workspace / "k8s" / "overlays" / "local"
                    if kustomize_dir.exists():
                        result = _run(
                            ["kubectl", "apply", "-k", str(kustomize_dir)],
                            timeout=120,
                        )
                    else:
                        result = _run(
                            ["kubectl", "apply", "-k", str(self.workspace / "k8s")],
                            timeout=120,
                        )

                    if result.returncode == 0:
                        self._log("✓", "K8s manifests applied")
                        self.steps_done.append("k8s")
                    else:
                        self._log("⚠", "K8s apply failed — run manually")
                        self.warnings.append("K8s apply failed")
                else:
                    self._log("ℹ", "K8s cluster not accessible — skipping")
            else:
                self._log("ℹ", "kubectl not installed — skipping")
        elif k8s_changed:
            self._log("ℹ", "K8s files changed but --no-k8s flag set")

        # ── Step 8: Validate ─────────────────────────────────────────
        self._header("Validation")
        python = _get_python()
        if python.exists():
            result = _run(
                [str(python), "slate/slate_status.py", "--quick"],
                cwd=str(self.workspace), timeout=30,
            )
            if result.returncode == 0:
                self._log("✓", "System health check passed")
                self.steps_done.append("validate")
            else:
                self._log("⚠", "Health check had warnings")
                self.warnings.append("Health check warnings")

        # ── Step 9: Update instruction templates ─────────────────────
        instructions_changed = any(
            "copilot-instructions" in f or "CLAUDE.md" in f or "AGENTS.md" in f
            for f in changed_files
        )
        if instructions_changed:
            self._log("ℹ", "Instruction files updated — review changes in:")
            self._log("  ", "  .github/copilot-instructions.md")
            self._log("  ", "  CLAUDE.md")
            self._log("  ", "  AGENTS.md")
            self.changes.append("Instruction files updated")

        # Save update state
        self._save_state(pre_version, pre_commit, merge_ref, changed_files)

        return self._report(start_time, pre_version, pre_commit)

    def _save_state(self, pre_version: str, pre_commit: str,
                    merge_ref: str, changed_files: list[str]):
        """Save update state for tracking."""
        state = {
            "last_update": datetime.now(timezone.utc).isoformat(),
            "pre_version": pre_version,
            "post_version": self._get_current_version(),
            "pre_commit": pre_commit,
            "post_commit": self._get_current_commit(),
            "merge_ref": merge_ref,
            "files_updated": len(changed_files),
            "steps_completed": self.steps_done,
        }
        try:
            UPDATE_STATE_FILE.write_text(
                json.dumps(state, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _report(self, start_time: float, pre_version: str,
                pre_commit: str) -> dict:
        """Generate final update report."""
        elapsed = time.time() - start_time
        post_version = self._get_current_version()
        post_commit = self._get_current_commit()

        success = len(self.errors) == 0

        print()
        print("═" * 64)
        if success:
            print(f"  ✓ S.L.A.T.E. Update Complete ({elapsed:.1f}s)")
        else:
            print(f"  ✗ S.L.A.T.E. Update Failed ({elapsed:.1f}s)")
        print(f"  Version: v{pre_version} → v{post_version}")
        print(f"  Commit:  {pre_commit} → {post_commit}")
        if self.steps_done:
            print(f"  Steps:   {', '.join(self.steps_done)}")
        if self.warnings:
            print(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings:
                print(f"    ⚠ {w}")
        if self.errors:
            print(f"  Errors: {len(self.errors)}")
            for e in self.errors:
                print(f"    ✗ {e}")
        print("═" * 64)
        print()

        return {
            "success": success,
            "elapsed_seconds": round(elapsed, 1),
            "pre_version": pre_version,
            "post_version": post_version,
            "pre_commit": pre_commit,
            "post_commit": post_commit,
            "steps_done": self.steps_done,
            "changes": self.changes,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for SLATE updater."""
    # Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: CLI for updater
    parser = argparse.ArgumentParser(
        description="S.L.A.T.E. Upstream Update System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python slate/slate_updater.py --check                   # Check for updates
  python slate/slate_updater.py --update                   # Full update from upstream/main
  python slate/slate_updater.py --update --channel stable  # Update to latest release
  python slate/slate_updater.py --update --dry-run         # Preview changes
  python slate/slate_updater.py --update --no-docker       # Skip Docker rebuild
  python slate/slate_updater.py --status                   # Current version info
        """,
    )
    parser.add_argument("--check", action="store_true",
                        help="Check for available updates")
    parser.add_argument("--update", action="store_true",
                        help="Pull and apply updates from upstream")
    parser.add_argument("--status", action="store_true",
                        help="Show current version and update info")
    parser.add_argument("--channel", choices=["main", "stable", "beta"],
                        default="main", help="Update channel (default: main)")
    parser.add_argument("--no-docker", action="store_true", dest="no_docker",
                        help="Skip Docker image rebuild")
    parser.add_argument("--no-k8s", action="store_true", dest="no_k8s",
                        help="Skip Kubernetes re-apply")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="Show what would change without applying")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()
    updater = SlateUpdater()

    if args.status:
        result = updater.status()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print()
            print("═" * 64)
            print("  S.L.A.T.E. Installation Status")
            print("═" * 64)
            print(f"  Version:    v{result['version']}")
            print(f"  Branch:     {result['branch']}")
            print(f"  Commit:     {result['commit']}")
            print(f"  Upstream:   {'configured' if result['upstream_remote'] else 'not set'}")
            print(f"  Local edits: {'yes' if result['has_uncommitted_changes'] else 'clean'}")
            if result['last_update']:
                print(f"  Last update: {result['last_update']}")
            print("═" * 64)
            print()
        return 0

    if args.check:
        result = updater.check()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        return 0

    if args.update:
        result = updater.update(
            channel=args.channel,
            rebuild_docker=not args.no_docker,
            reapply_k8s=not args.no_k8s,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("success", False) else 1

    # Default: show status + check hint
    result = updater.status()
    print()
    print("═" * 64)
    print("  S.L.A.T.E. Updater")
    print("═" * 64)
    print(f"  Version: v{result['version']} ({result['branch']}@{result['commit']})")
    print()
    print("  Commands:")
    print("    --check     Check for available updates")
    print("    --update    Pull and apply updates from upstream")
    print("    --status    Show detailed version info")
    print("═" * 64)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
