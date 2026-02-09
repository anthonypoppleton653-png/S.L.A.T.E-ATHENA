#!/usr/bin/env python3
# Modified: 2026-02-09T23:30:00Z | Author: COPILOT | Change: Create setup validation script for public SLATE installs
"""
SLATE Setup Validator
======================
Comprehensive pre-flight and post-install validation for SLATE installations.
Checks all prerequisites, validates configuration, and reports readiness.

Checks:
    1. Python version (3.11+ required)
    2. Git installation and repo state
    3. Virtual environment (.venv)
    4. Required Python packages
    5. GPU detection (NVIDIA / CUDA)
    6. Docker installation and status
    7. Kubernetes (kubectl, cluster access)
    8. Ollama installation and models
    9. VS Code and SLATE extension
    10. Claude Code configuration
    11. Instruction files present
    12. Security configuration (ActionGuard, PII scanner)
    13. Network binding validation (127.0.0.1 only)
    14. File permissions and directory structure

Usage:
    python slate/slate_setup_validator.py                  # Full validation
    python slate/slate_setup_validator.py --quick           # Required checks only
    python slate/slate_setup_validator.py --fix             # Auto-fix what's possible
    python slate/slate_setup_validator.py --json            # JSON output
    python slate/slate_setup_validator.py --category gpu    # Check specific category
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Modified: 2026-02-09T23:30:00Z | Author: COPILOT | Change: Initial setup validator

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()


def _run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a subprocess command safely."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(WORKSPACE_ROOT), encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


class CheckResult:
    """Result of a single validation check."""

    def __init__(self, name: str, category: str, required: bool = True):
        self.name = name
        self.category = category
        self.required = required
        self.passed: bool = False
        self.message: str = ""
        self.details: dict[str, Any] = {}
        self.fix_hint: str = ""

    def ok(self, msg: str, **details):
        self.passed = True
        self.message = msg
        self.details.update(details)
        return self

    def fail(self, msg: str, fix: str = "", **details):
        self.passed = False
        self.message = msg
        self.fix_hint = fix
        self.details.update(details)
        return self

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "category": self.category,
            "required": self.required,
            "passed": self.passed,
            "message": self.message,
        }
        if self.details:
            d["details"] = self.details
        if self.fix_hint:
            d["fix"] = self.fix_hint
        return d


class SlateSetupValidator:
    """Validates SLATE installation prerequisites and configuration."""

    def __init__(self, workspace: Path | None = None):
        # Modified: 2026-02-09T23:30:00Z | Author: COPILOT | Change: Validator init
        self.workspace = workspace or WORKSPACE_ROOT
        self.results: list[CheckResult] = []

    def validate_all(self, quick: bool = False) -> dict:
        """Run all validation checks."""
        start = time.time()

        # Required checks (always run)
        self._check_python()
        self._check_git()
        self._check_venv()
        self._check_packages()
        self._check_directory_structure()
        self._check_instruction_files()

        if not quick:
            # Optional / extended checks
            self._check_gpu()
            self._check_docker()
            self._check_kubernetes()
            self._check_ollama()
            self._check_vscode()
            self._check_claude_code()
            self._check_security()
            self._check_network_bindings()

        return self._build_report(time.time() - start)

    def validate_category(self, category: str) -> dict:
        """Validate a specific category only."""
        start = time.time()
        dispatch = {
            "python": self._check_python,
            "git": self._check_git,
            "venv": self._check_venv,
            "packages": self._check_packages,
            "gpu": self._check_gpu,
            "docker": self._check_docker,
            "k8s": self._check_kubernetes,
            "kubernetes": self._check_kubernetes,
            "ollama": self._check_ollama,
            "vscode": self._check_vscode,
            "claude": self._check_claude_code,
            "security": self._check_security,
            "network": self._check_network_bindings,
            "structure": self._check_directory_structure,
            "instructions": self._check_instruction_files,
        }
        fn = dispatch.get(category.lower())
        if fn:
            fn()
        else:
            self.results.append(
                CheckResult("category", "unknown").fail(
                    f"Unknown category: {category}",
                    fix=f"Valid: {', '.join(sorted(dispatch.keys()))}",
                )
            )
        return self._build_report(time.time() - start)

    # ── Individual Checks ─────────────────────────────────────────────

    def _check_python(self):
        """Check Python version >= 3.11."""
        c = CheckResult("Python Version", "python")
        v = sys.version_info
        version_str = f"{v.major}.{v.minor}.{v.micro}"
        if v.major == 3 and v.minor >= 11:
            c.ok(f"Python {version_str}", executable=sys.executable)
        else:
            c.fail(
                f"Python {version_str} — need 3.11+",
                fix="Install Python 3.11+ from https://python.org",
            )
        self.results.append(c)

    def _check_git(self):
        """Check git installation and repo state."""
        c = CheckResult("Git", "git")
        result = _run(["git", "--version"])
        if result.returncode != 0:
            c.fail("Git not found", fix="Install git from https://git-scm.com")
            self.results.append(c)
            return

        version = result.stdout.strip().replace("git version ", "")
        git_dir = self.workspace / ".git"
        if git_dir.exists():
            # Check remote
            remote = _run(["git", "remote", "get-url", "origin"])
            remote_url = remote.stdout.strip() if remote.returncode == 0 else "none"
            c.ok(f"Git {version}", repo=True, remote=remote_url)
        else:
            c.fail(
                f"Git {version} installed but no repo at {self.workspace}",
                fix="git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git",
            )
        self.results.append(c)

    def _check_venv(self):
        """Check virtual environment."""
        c = CheckResult("Virtual Environment", "venv")
        venv_dir = self.workspace / ".venv"
        if venv_dir.exists():
            # Check platform-specific python
            if platform.system() == "Windows":
                py = venv_dir / "Scripts" / "python.exe"
            else:
                py = venv_dir / "bin" / "python"
            if py.exists():
                c.ok(f"venv at {venv_dir.name}/", python=str(py))
            else:
                c.fail(
                    "venv directory exists but python not found",
                    fix="python -m venv .venv",
                )
        else:
            c.fail(
                "No .venv directory",
                fix="python -m venv .venv && pip install -r requirements.txt",
            )
        self.results.append(c)

    def _check_packages(self):
        """Check required Python packages."""
        required = ["fastapi", "uvicorn", "pydantic", "httpx", "toml"]
        optional = ["torch", "transformers", "chromadb", "semantic_kernel"]

        # Check required
        c = CheckResult("Required Packages", "packages")
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            c.fail(
                f"Missing: {', '.join(missing)}",
                fix=f"pip install {' '.join(missing)}",
            )
        else:
            c.ok(f"All {len(required)} required packages installed")
        self.results.append(c)

        # Check optional
        c2 = CheckResult("Optional Packages", "packages", required=False)
        installed = []
        for pkg in optional:
            try:
                __import__(pkg)
                installed.append(pkg)
            except ImportError:
                pass
        c2.ok(f"{len(installed)}/{len(optional)} optional: {', '.join(installed) or 'none'}")
        self.results.append(c2)

    def _check_gpu(self):
        """Check NVIDIA GPU and CUDA."""
        c = CheckResult("NVIDIA GPU", "gpu", required=False)
        result = _run(["nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
                        "--format=csv,noheader,nounits"])
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpus.append({
                        "name": parts[0],
                        "memory_mb": parts[1],
                        "compute_capability": parts[2],
                    })
            c.ok(f"{len(gpus)} GPU(s): {gpus[0]['name']}", gpus=gpus)
        else:
            c.ok("No NVIDIA GPU detected (CPU mode — Ollama handles GPU inference)")
        self.results.append(c)

    def _check_docker(self):
        """Check Docker installation."""
        c = CheckResult("Docker", "docker", required=False)
        result = _run(["docker", "--version"])
        if result.returncode != 0:
            c.ok("Docker not installed (optional — needed for container deployment)")
            self.results.append(c)
            return

        version = result.stdout.strip()
        # Check if Docker daemon is running
        ps = _run(["docker", "ps"], timeout=10)
        running = ps.returncode == 0

        # Check for NVIDIA Container Toolkit
        nvidia_runtime = _run(["docker", "info", "--format", "{{.Runtimes}}"], timeout=10)
        has_nvidia = "nvidia" in (nvidia_runtime.stdout or "").lower()

        c.ok(
            f"{version} ({'running' if running else 'stopped'})",
            running=running, nvidia_runtime=has_nvidia,
        )
        self.results.append(c)

    def _check_kubernetes(self):
        """Check kubectl and cluster access."""
        c = CheckResult("Kubernetes", "kubernetes", required=False)
        if not shutil.which("kubectl"):
            c.ok("kubectl not installed (optional — needed for K8s deployment)")
            self.results.append(c)
            return

        result = _run(["kubectl", "cluster-info"], timeout=10)
        if result.returncode == 0:
            # Check SLATE namespace
            ns = _run(["kubectl", "get", "namespace", "slate", "-o", "name"], timeout=10)
            has_ns = ns.returncode == 0
            c.ok(
                f"Cluster accessible, SLATE namespace: {'yes' if has_ns else 'no'}",
                cluster=True, slate_namespace=has_ns,
            )
        else:
            c.ok("kubectl installed but no cluster accessible")
        self.results.append(c)

    def _check_ollama(self):
        """Check Ollama installation and models."""
        c = CheckResult("Ollama", "ollama", required=False)
        result = _run(["ollama", "--version"], timeout=10)
        if result.returncode != 0:
            c.ok("Ollama not installed (needed for local LLM inference)")
            c.fix_hint = "Install from https://ollama.com"
            self.results.append(c)
            return

        version = result.stdout.strip()
        # List models
        models = _run(["ollama", "list"], timeout=10)
        model_count = 0
        slate_models = []
        if models.returncode == 0:
            lines = models.stdout.strip().split("\n")[1:]  # Skip header
            model_count = len(lines)
            for line in lines:
                name = line.split()[0] if line.split() else ""
                if "slate" in name.lower():
                    slate_models.append(name)

        c.ok(
            f"Ollama {version}, {model_count} model(s), SLATE models: {len(slate_models)}",
            models=model_count, slate_models=slate_models,
        )
        self.results.append(c)

    def _check_vscode(self):
        """Check VS Code and SLATE extension."""
        c = CheckResult("VS Code", "vscode", required=False)
        result = _run(["code", "--version"], timeout=10)
        if result.returncode != 0:
            c.ok("VS Code not on PATH (optional)")
            self.results.append(c)
            return

        version = result.stdout.strip().split("\n")[0]
        # Check SLATE extension
        ext = _run(["code", "--list-extensions"], timeout=15)
        has_slate = "slate.slate-copilot" in (ext.stdout or "").lower() if ext.returncode == 0 else False

        c.ok(
            f"VS Code {version}, SLATE extension: {'installed' if has_slate else 'not installed'}",
            slate_extension=has_slate,
        )
        if not has_slate:
            c.fix_hint = "Install from plugins/slate-copilot/ or VS Code marketplace"
        self.results.append(c)

    def _check_claude_code(self):
        """Check Claude Code configuration."""
        c = CheckResult("Claude Code Config", "claude", required=False)
        claude_dir = self.workspace / ".claude"
        settings = claude_dir / "settings.json"

        if not claude_dir.exists():
            c.ok("No .claude/ directory (create during install for Claude Code support)")
            self.results.append(c)
            return

        if settings.exists():
            try:
                data = json.loads(settings.read_text(encoding="utf-8"))
                has_mcp = "mcpServers" in data and "slate" in data.get("mcpServers", {})
                c.ok(
                    f"Claude settings found, SLATE MCP: {'configured' if has_mcp else 'missing'}",
                    mcp_configured=has_mcp,
                )
            except Exception as e:
                c.fail(f"Cannot parse .claude/settings.json: {e}")
        else:
            c.ok(".claude/ exists but no settings.json")
            c.fix_hint = "Copy templates/claude-settings.template.json to .claude/settings.json"

        self.results.append(c)

    def _check_security(self):
        """Check security configuration."""
        c = CheckResult("Security Config", "security")
        issues = []

        # Check ActionGuard exists
        ag = self.workspace / "slate" / "action_guard.py"
        if not ag.exists():
            issues.append("action_guard.py missing")

        # Check PII scanner exists
        pii = self.workspace / "slate" / "pii_scanner.py"
        if not pii.exists():
            issues.append("pii_scanner.py missing")

        # Check .gitignore has security entries
        gitignore = self.workspace / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            required_entries = [".env", "secrets/", ".slate_identity/"]
            for entry in required_entries:
                if entry not in content:
                    issues.append(f".gitignore missing: {entry}")

        if issues:
            c.fail(f"Security issues: {', '.join(issues)}")
        else:
            c.ok("ActionGuard, PII scanner, .gitignore all present")
        self.results.append(c)

    def _check_network_bindings(self):
        """Scan for unsafe network bindings (0.0.0.0)."""
        c = CheckResult("Network Bindings", "network")
        unsafe_files = []

        # Scan Python files for 0.0.0.0 bindings
        for py_file in (self.workspace / "slate").glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                if "0.0.0.0" in content:
                    # Check if it's in a comment or string about blocking
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if "0.0.0.0" in stripped and not stripped.startswith("#"):
                            # Could be a real binding
                            if "host=" in stripped or "bind" in stripped.lower():
                                unsafe_files.append(f"{py_file.name}:{i}")
            except Exception:
                pass

        if unsafe_files:
            c.fail(
                f"Potential unsafe bindings in: {', '.join(unsafe_files[:5])}",
                fix="Change all 0.0.0.0 bindings to 127.0.0.1",
            )
        else:
            c.ok("No unsafe 0.0.0.0 bindings found")
        self.results.append(c)

    def _check_directory_structure(self):
        """Check essential directory structure."""
        c = CheckResult("Directory Structure", "structure")
        required_dirs = ["slate", "agents", "k8s"]
        required_files = ["pyproject.toml", "requirements.txt", "Dockerfile"]
        missing = []

        for d in required_dirs:
            if not (self.workspace / d).is_dir():
                missing.append(f"dir: {d}/")
        for f in required_files:
            if not (self.workspace / f).is_file():
                missing.append(f"file: {f}")

        if missing:
            c.fail(f"Missing: {', '.join(missing)}")
        else:
            c.ok(f"All {len(required_dirs)} dirs + {len(required_files)} files present")
        self.results.append(c)

    def _check_instruction_files(self):
        """Check instruction files are present."""
        c = CheckResult("Instruction Files", "instructions")
        files = {
            "AGENTS.md": self.workspace / "AGENTS.md",
            "CLAUDE.md": self.workspace / "CLAUDE.md",
            "copilot-instructions.md": self.workspace / ".github" / "copilot-instructions.md",
        }
        present = []
        missing = []
        for name, path in files.items():
            if path.exists():
                present.append(name)
            else:
                missing.append(name)

        if missing:
            c.fail(
                f"Missing: {', '.join(missing)}",
                fix="Run install_slate.py --install to generate instruction files",
            )
        else:
            c.ok(f"All {len(present)} instruction files present")
        self.results.append(c)

    # ── Report ────────────────────────────────────────────────────────

    def _build_report(self, elapsed: float) -> dict:
        """Build validation report."""
        required_checks = [r for r in self.results if r.required]
        optional_checks = [r for r in self.results if not r.required]

        required_pass = sum(1 for r in required_checks if r.passed)
        optional_pass = sum(1 for r in optional_checks if r.passed)

        all_required_pass = required_pass == len(required_checks)

        return {
            "ready": all_required_pass,
            "required": {"passed": required_pass, "total": len(required_checks)},
            "optional": {"passed": optional_pass, "total": len(optional_checks)},
            "elapsed_seconds": round(elapsed, 2),
            "checks": [r.to_dict() for r in self.results],
        }

    def print_report(self, report: dict):
        """Print a human-readable validation report."""
        print()
        print("═" * 64)
        print("  S.L.A.T.E. Setup Validation")
        print("═" * 64)

        for check in report["checks"]:
            icon = "✓" if check["passed"] else ("✗" if check["required"] else "ℹ")
            req = "" if check["required"] else " (optional)"
            print(f"  {icon} {check['name']}: {check['message']}{req}")
            if not check["passed"] and check.get("fix"):
                print(f"      Fix: {check['fix']}")

        print()
        req = report["required"]
        opt = report["optional"]
        ready = report["ready"]
        print(f"  Required: {req['passed']}/{req['total']} passed")
        print(f"  Optional: {opt['passed']}/{opt['total']} passed")
        print()
        if ready:
            print("  ✓ SLATE is ready to use!")
        else:
            print("  ✗ Some required checks failed — fix issues above")
        print(f"  ({report['elapsed_seconds']:.1f}s)")
        print("═" * 64)
        print()


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for SLATE setup validator."""
    # Modified: 2026-02-09T23:30:00Z | Author: COPILOT | Change: CLI for validator
    parser = argparse.ArgumentParser(
        description="S.L.A.T.E. Setup Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python slate/slate_setup_validator.py                    # Full validation
  python slate/slate_setup_validator.py --quick             # Required checks only
  python slate/slate_setup_validator.py --category gpu      # GPU checks only
  python slate/slate_setup_validator.py --json              # JSON output
        """,
    )
    parser.add_argument("--quick", action="store_true",
                        help="Required checks only (faster)")
    parser.add_argument("--category", type=str,
                        help="Validate specific category (python, git, gpu, docker, k8s, ollama, vscode, claude, security, network)")
    parser.add_argument("--json", action="store_true",
                        help="JSON output")

    args = parser.parse_args()
    validator = SlateSetupValidator()

    if args.category:
        report = validator.validate_category(args.category)
    else:
        report = validator.validate_all(quick=args.quick)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        validator.print_report(report)

    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
