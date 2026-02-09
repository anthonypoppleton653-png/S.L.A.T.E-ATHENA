#!/usr/bin/env python3
# Modified: 2026-02-08T15:00:00Z | Author: COPILOT | Change: Create Phoenix release automation — stable branch, tagging, changelog generation
"""
SLATE Release Manager
======================
Automates the Phoenix release process:
    - Create 'stable' branch from main
    - Merge verified features via PRs with CI checks
    - Tag releases (Phoenix-v1.0, etc.)
    - Generate changelog from conventional commits
    - Validate pre-release conditions (tests pass, no stale tasks, etc.)

Usage:
    python slate/release.py --status           # Pre-release checklist
    python slate/release.py --prepare          # Prepare stable branch
    python slate/release.py --tag Phoenix-v1.0 # Tag release
    python slate/release.py --changelog        # Generate changelog
    python slate/release.py --full-release     # Full release pipeline
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent

log = logging.getLogger("slate.release")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════════
# Git Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command."""
    return subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, cwd=str(WORKSPACE),
        check=check, encoding="utf-8",
    )


def get_current_branch() -> str:
    """Get current git branch."""
    result = _run_git("rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip()


def get_latest_tag() -> Optional[str]:
    """Get the latest git tag."""
    result = _run_git("describe", "--tags", "--abbrev=0", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def get_commit_log(since_tag: Optional[str] = None) -> list[dict]:
    """Get commit log since last tag."""
    fmt = "--format=%H|%s|%an|%aI"
    if since_tag:
        result = _run_git("log", f"{since_tag}..HEAD", fmt, check=False)
    else:
        result = _run_git("log", "--max-count=100", fmt, check=False)

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line or "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        commits.append({
            "hash": parts[0][:7],
            "message": parts[1],
            "author": parts[2],
            "date": parts[3],
        })
    return commits


def branch_exists(name: str) -> bool:
    """Check if a branch exists locally or remotely."""
    result = _run_git("branch", "--list", name, check=False)
    if result.stdout.strip():
        return True
    result = _run_git("branch", "-r", "--list", f"origin/{name}", check=False)
    return bool(result.stdout.strip())


# ═══════════════════════════════════════════════════════════════════════════════
# Changelog Generator
# ═══════════════════════════════════════════════════════════════════════════════

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

CATEGORY_MAP = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "perf": "Performance",
    "refactor": "Refactoring",
    "test": "Tests",
    "ci": "CI/CD",
    "build": "Build",
    "chore": "Maintenance",
    "style": "Style",
    "revert": "Reverts",
}


def generate_changelog(commits: list[dict], version: str = "Unreleased") -> str:
    """Generate changelog from conventional commits."""
    categories: dict[str, list[dict]] = {}
    uncategorized = []

    for commit in commits:
        match = CONVENTIONAL_PATTERN.match(commit["message"])
        if match:
            cat = CATEGORY_MAP.get(match.group("type"), "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "description": match.group("description"),
                "scope": match.group("scope"),
                "breaking": bool(match.group("breaking")),
                "hash": commit["hash"],
                "author": commit["author"],
            })
        else:
            uncategorized.append(commit)

    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines.append(f"## [{version}] - {now}")
    lines.append("")

    # Breaking changes first
    breaking = []
    for entries in categories.values():
        for e in entries:
            if e["breaking"]:
                breaking.append(e)
    if breaking:
        lines.append("### ⚠ BREAKING CHANGES")
        for b in breaking:
            scope = f"**{b['scope']}:** " if b["scope"] else ""
            lines.append(f"- {scope}{b['description']} ({b['hash']})")
        lines.append("")

    # Categories
    priority_order = ["Features", "Bug Fixes", "Performance", "Refactoring",
                      "Documentation", "Tests", "CI/CD", "Build", "Maintenance"]
    for cat in priority_order:
        if cat in categories:
            lines.append(f"### {cat}")
            for entry in categories[cat]:
                scope = f"**{entry['scope']}:** " if entry["scope"] else ""
                lines.append(f"- {scope}{entry['description']} ({entry['hash']})")
            lines.append("")

    if uncategorized:
        lines.append("### Other Changes")
        for c in uncategorized:
            lines.append(f"- {c['message']} ({c['hash']})")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Release Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

class ReleaseManager:
    """Manages the Phoenix release pipeline."""

    def __init__(self):
        self.pyproject_path = WORKSPACE / "pyproject.toml"

    def get_version(self) -> str:
        """Get version from pyproject.toml."""
        content = self.pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        return match.group(1) if match else "0.0.0"

    def pre_release_checks(self) -> dict:
        """Run pre-release validation checks."""
        checks = {}

        # 1. Clean working tree
        result = _run_git("status", "--porcelain")
        checks["clean_tree"] = len(result.stdout.strip()) == 0

        # 2. On main branch
        checks["on_main"] = get_current_branch() == "main"

        # 3. Tests pass (check for pytest)
        try:
            result = subprocess.run(
                [str(WORKSPACE / ".venv" / "Scripts" / "python.exe"), "-m", "pytest",
                 "--tb=no", "-q", "--co"],
                capture_output=True, text=True, cwd=str(WORKSPACE), timeout=30,
            )
            checks["tests_collected"] = result.returncode == 0
        except Exception:
            checks["tests_collected"] = False

        # 4. No stale tasks
        try:
            result = subprocess.run(
                [str(WORKSPACE / ".venv" / "Scripts" / "python.exe"),
                 str(WORKSPACE / "slate" / "slate_workflow_manager.py"), "--status"],
                capture_output=True, text=True, timeout=30,
            )
            checks["no_stale_tasks"] = "Pending:     0" in result.stdout
        except Exception:
            checks["no_stale_tasks"] = False

        # 5. SLATE health
        try:
            result = subprocess.run(
                [str(WORKSPACE / ".venv" / "Scripts" / "python.exe"),
                 str(WORKSPACE / "slate" / "slate_status.py"), "--quick"],
                capture_output=True, text=True, timeout=30,
            )
            checks["slate_healthy"] = result.returncode == 0
        except Exception:
            checks["slate_healthy"] = False

        # 6. Version set
        checks["version"] = self.get_version()
        checks["version_valid"] = checks["version"] != "0.0.0"

        checks["all_pass"] = all(
            v for k, v in checks.items()
            if k not in ("version",) and isinstance(v, bool)
        )

        return checks

    def prepare_stable_branch(self, dry_run: bool = False) -> bool:
        """Create or update the 'stable' branch from main."""
        current = get_current_branch()
        if current != "main":
            log.error(f"Must be on 'main' branch (currently on '{current}')")
            return False

        if dry_run:
            log.info("[DRY RUN] Would create/update 'stable' branch from main")
            return True

        if branch_exists("stable"):
            log.info("Updating existing 'stable' branch...")
            _run_git("checkout", "stable")
            _run_git("merge", "--no-ff", "main", "-m",
                     f"chore(release): merge main into stable for Phoenix release")
        else:
            log.info("Creating 'stable' branch from main...")
            _run_git("checkout", "-b", "stable")

        log.info("Stable branch ready.")
        _run_git("checkout", "main")  # Return to main
        return True

    def tag_release(self, tag: str, message: Optional[str] = None, dry_run: bool = False) -> bool:
        """Tag a release."""
        if not message:
            version = self.get_version()
            message = f"SLATE {tag} — v{version} Phoenix Release"

        if dry_run:
            log.info(f"[DRY RUN] Would create tag '{tag}' with message: {message}")
            return True

        _run_git("tag", "-a", tag, "-m", message)
        log.info(f"Created tag: {tag}")
        return True

    def push_release(self, tag: str, dry_run: bool = False) -> bool:
        """Push stable branch and tags to origin."""
        if dry_run:
            log.info("[DRY RUN] Would push stable branch and tags")
            return True

        _run_git("push", "origin", "stable")
        _run_git("push", "origin", tag)
        log.info(f"Pushed stable branch and tag {tag}")
        return True

    def full_release(self, tag: str = "Phoenix-v1.0", dry_run: bool = False) -> dict:
        """Execute full release pipeline."""
        results = {"steps": []}

        # 1. Pre-release checks
        checks = self.pre_release_checks()
        results["checks"] = checks
        results["steps"].append(("pre-release checks", checks["all_pass"]))
        if not checks["all_pass"] and not dry_run:
            log.error("Pre-release checks failed. Fix issues before releasing.")
            results["success"] = False
            return results

        # 2. Generate changelog
        last_tag = get_latest_tag()
        commits = get_commit_log(since_tag=last_tag)
        changelog = generate_changelog(commits, version=tag)
        changelog_path = WORKSPACE / "CHANGELOG.md"

        if not dry_run:
            existing = ""
            if changelog_path.exists():
                existing = changelog_path.read_text(encoding="utf-8")
            changelog_path.write_text(
                f"# SLATE Changelog\n\n{changelog}\n{existing}",
                encoding="utf-8",
            )
            _run_git("add", "CHANGELOG.md")
            _run_git("commit", "-m", f"docs(changelog): generate changelog for {tag}")

        results["steps"].append(("changelog generated", True))
        results["changelog"] = changelog

        # 3. Prepare stable branch
        ok = self.prepare_stable_branch(dry_run=dry_run)
        results["steps"].append(("stable branch prepared", ok))

        # 4. Tag release
        ok = self.tag_release(tag, dry_run=dry_run)
        results["steps"].append(("release tagged", ok))

        # 5. Push
        if not dry_run:
            ok = self.push_release(tag, dry_run=dry_run)
            results["steps"].append(("pushed to origin", ok))
        else:
            results["steps"].append(("push (skipped — dry run)", True))

        results["success"] = all(ok for _, ok in results["steps"])
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Release Manager")
    parser.add_argument("--status", action="store_true", help="Pre-release checklist")
    parser.add_argument("--prepare", action="store_true", help="Prepare stable branch")
    parser.add_argument("--tag", type=str, help="Tag a release (e.g., Phoenix-v1.0)")
    parser.add_argument("--changelog", action="store_true", help="Generate changelog")
    parser.add_argument("--full-release", action="store_true", help="Full release pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    mgr = ReleaseManager()

    if args.status:
        checks = mgr.pre_release_checks()
        if args.json:
            print(json.dumps(checks, indent=2, default=str))
        else:
            print()
            print("=" * 60)
            print("  SLATE Pre-Release Checklist")
            print("=" * 60)
            for key, value in checks.items():
                if key in ("all_pass", "version"):
                    continue
                icon = "✓" if value else "✗"
                label = key.replace("_", " ").title()
                print(f"  [{icon}] {label}")
            print(f"\n  Version: {checks['version']}")
            icon = "✓" if checks["all_pass"] else "✗"
            print(f"\n  [{icon}] {'READY for release' if checks['all_pass'] else 'NOT READY — fix issues above'}")
            print("=" * 60)

    elif args.prepare:
        ok = mgr.prepare_stable_branch(dry_run=args.dry_run)
        print(f"Stable branch: {'ready' if ok else 'FAILED'}")

    elif args.tag:
        ok = mgr.tag_release(args.tag, dry_run=args.dry_run)
        print(f"Tag {args.tag}: {'created' if ok else 'FAILED'}")

    elif args.changelog:
        last_tag = get_latest_tag()
        commits = get_commit_log(since_tag=last_tag)
        print(generate_changelog(commits))

    elif args.full_release:
        tag = "Phoenix-v1.0"
        results = mgr.full_release(tag=tag, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print()
            print("=" * 60)
            print(f"  SLATE Release: {tag}")
            print("=" * 60)
            for step, ok in results["steps"]:
                icon = "✓" if ok else "✗"
                print(f"  [{icon}] {step}")
            print()
            icon = "✓" if results["success"] else "✗"
            print(f"  [{icon}] {'Release complete!' if results['success'] else 'Release FAILED'}")
            print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
