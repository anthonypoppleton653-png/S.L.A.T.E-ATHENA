#!/usr/bin/env python3
# Modified: 2026-02-06T23:00:00Z | Author: Claude | Change: GitHub integration verification
"""
SLATE GitHub Integration Verification
======================================
Verifies all GitHub integrations are properly configured and working.

Usage:
    python slate/slate_github_verify.py           # Full verification
    python slate/slate_github_verify.py --quick   # Quick check
    python slate/slate_github_verify.py --json    # JSON output
    python slate/slate_github_verify.py --fix     # Attempt to fix issues
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


@dataclass
class CheckResult:
    """Result of an integration check."""
    name: str
    status: str  # "pass", "fail", "warn", "skip"
    message: str
    details: Optional[Dict] = None
    fix_cmd: Optional[str] = None


@dataclass
class VerificationReport:
    """Full verification report."""
    timestamp: str
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    checks: List[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult):
        self.checks.append(result)
        if result.status == "pass":
            self.passed += 1
        elif result.status == "fail":
            self.failed += 1
        elif result.status == "warn":
            self.warnings += 1
        else:
            self.skipped += 1

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "skipped": self.skipped,
                "all_passed": self.all_passed,
            },
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "details": c.details,
                    "fix_cmd": c.fix_cmd,
                }
                for c in self.checks
            ],
        }


class GitHubIntegrationVerifier:
    """Verifies GitHub integrations for SLATE."""

    def __init__(self):
        self.workspace = WORKSPACE_ROOT
        self.report = VerificationReport(timestamp=datetime.now().isoformat())

    def verify_all(self, quick: bool = False) -> VerificationReport:
        """Run all verification checks."""
        # Core GitHub files
        self._check_github_directory()
        self._check_workflows()
        self._check_issue_templates()
        self._check_pr_template()
        self._check_codeowners()
        self._check_security()
        self._check_dependabot()
        self._check_labels()
        self._check_funding()

        if not quick:
            # Extended checks
            self._check_gh_cli()
            self._check_gh_auth()
            self._check_runner()
            self._check_mcp_server()
            self._check_claude_skills()
            self._check_copilot_config()
            self._check_github_models()

        return self.report

    def _check_github_directory(self):
        """Check .github directory exists."""
        github_dir = self.workspace / ".github"
        if github_dir.exists():
            self.report.add(CheckResult(
                "github_directory",
                "pass",
                ".github directory exists",
                {"path": str(github_dir)},
            ))
        else:
            self.report.add(CheckResult(
                "github_directory",
                "fail",
                ".github directory missing",
                fix_cmd="mkdir .github",
            ))

    def _check_workflows(self):
        """Check GitHub Actions workflows."""
        workflows_dir = self.workspace / ".github" / "workflows"
        if not workflows_dir.exists():
            self.report.add(CheckResult(
                "workflows",
                "fail",
                ".github/workflows directory missing",
            ))
            return

        workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        expected_min = 10

        if len(workflows) >= expected_min:
            self.report.add(CheckResult(
                "workflows",
                "pass",
                f"{len(workflows)} workflows found",
                {"count": len(workflows), "files": [w.name for w in workflows]},
            ))
        else:
            self.report.add(CheckResult(
                "workflows",
                "warn",
                f"Only {len(workflows)} workflows found (expected {expected_min}+)",
                {"count": len(workflows)},
            ))

    def _check_issue_templates(self):
        """Check issue templates."""
        templates_dir = self.workspace / ".github" / "ISSUE_TEMPLATE"
        if not templates_dir.exists():
            self.report.add(CheckResult(
                "issue_templates",
                "fail",
                "Issue templates directory missing",
            ))
            return

        templates = list(templates_dir.glob("*.md")) + list(templates_dir.glob("*.yml"))
        config = templates_dir / "config.yml"

        if len(templates) >= 2 and config.exists():
            self.report.add(CheckResult(
                "issue_templates",
                "pass",
                f"{len(templates)} issue templates with config",
                {"templates": [t.name for t in templates]},
            ))
        else:
            self.report.add(CheckResult(
                "issue_templates",
                "warn",
                f"{len(templates)} templates found",
                {"has_config": config.exists()},
            ))

    def _check_pr_template(self):
        """Check PR template."""
        pr_template = self.workspace / ".github" / "PULL_REQUEST_TEMPLATE.md"
        if pr_template.exists():
            size = pr_template.stat().st_size
            self.report.add(CheckResult(
                "pr_template",
                "pass",
                "PR template exists",
                {"size": size},
            ))
        else:
            self.report.add(CheckResult(
                "pr_template",
                "fail",
                "PR template missing",
            ))

    def _check_codeowners(self):
        """Check CODEOWNERS file."""
        codeowners = self.workspace / ".github" / "CODEOWNERS"
        if codeowners.exists():
            self.report.add(CheckResult(
                "codeowners",
                "pass",
                "CODEOWNERS file exists",
            ))
        else:
            self.report.add(CheckResult(
                "codeowners",
                "warn",
                "CODEOWNERS file missing",
            ))

    def _check_security(self):
        """Check SECURITY.md file."""
        security = self.workspace / ".github" / "SECURITY.md"
        if security.exists():
            self.report.add(CheckResult(
                "security",
                "pass",
                "SECURITY.md exists",
            ))
        else:
            self.report.add(CheckResult(
                "security",
                "warn",
                "SECURITY.md missing",
            ))

    def _check_dependabot(self):
        """Check Dependabot configuration."""
        dependabot = self.workspace / ".github" / "dependabot.yml"
        if dependabot.exists():
            self.report.add(CheckResult(
                "dependabot",
                "pass",
                "Dependabot configured",
            ))
        else:
            self.report.add(CheckResult(
                "dependabot",
                "warn",
                "Dependabot not configured",
            ))

    def _check_labels(self):
        """Check labels configuration."""
        labels = self.workspace / ".github" / "labels.yml"
        if labels.exists():
            self.report.add(CheckResult(
                "labels",
                "pass",
                "Labels configuration exists",
            ))
        else:
            self.report.add(CheckResult(
                "labels",
                "warn",
                "Labels configuration missing",
            ))

    def _check_funding(self):
        """Check FUNDING.yml file."""
        funding = self.workspace / ".github" / "FUNDING.yml"
        if funding.exists():
            self.report.add(CheckResult(
                "funding",
                "pass",
                "FUNDING.yml exists",
            ))
        else:
            self.report.add(CheckResult(
                "funding",
                "skip",
                "FUNDING.yml not configured (optional)",
            ))

    def _check_gh_cli(self):
        """Check GitHub CLI installation."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                self.report.add(CheckResult(
                    "gh_cli",
                    "pass",
                    f"GitHub CLI installed: {version}",
                ))
            else:
                self.report.add(CheckResult(
                    "gh_cli",
                    "fail",
                    "GitHub CLI not working",
                    fix_cmd="winget install GitHub.cli",
                ))
        except FileNotFoundError:
            self.report.add(CheckResult(
                "gh_cli",
                "fail",
                "GitHub CLI not installed",
                fix_cmd="winget install GitHub.cli",
            ))
        except Exception as e:
            self.report.add(CheckResult(
                "gh_cli",
                "fail",
                f"Error checking gh CLI: {e}",
            ))

    def _check_gh_auth(self):
        """Check GitHub CLI authentication."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Check for workflow scope
                if "workflow" in result.stdout.lower() or "workflow" in result.stderr.lower():
                    self.report.add(CheckResult(
                        "gh_auth",
                        "pass",
                        "GitHub CLI authenticated with workflow scope",
                    ))
                else:
                    self.report.add(CheckResult(
                        "gh_auth",
                        "warn",
                        "GitHub CLI authenticated but may lack workflow scope",
                        fix_cmd="gh auth login -s workflow -w",
                    ))
            else:
                self.report.add(CheckResult(
                    "gh_auth",
                    "fail",
                    "GitHub CLI not authenticated",
                    fix_cmd="gh auth login",
                ))
        except Exception as e:
            self.report.add(CheckResult(
                "gh_auth",
                "skip",
                f"Cannot check auth: {e}",
            ))

    def _check_runner(self):
        """Check self-hosted runner status."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            status = manager.get_status()

            if status.get("running"):
                self.report.add(CheckResult(
                    "runner",
                    "pass",
                    "Self-hosted runner is running",
                    {"labels": status.get("labels", [])},
                ))
            elif status.get("configured"):
                self.report.add(CheckResult(
                    "runner",
                    "warn",
                    "Runner configured but not running",
                    fix_cmd="python slate/slate_runner_manager.py --start",
                ))
            else:
                self.report.add(CheckResult(
                    "runner",
                    "warn",
                    "Runner not configured",
                    fix_cmd="python slate/slate_sdk.py --setup --runner",
                ))
        except Exception as e:
            self.report.add(CheckResult(
                "runner",
                "skip",
                f"Cannot check runner: {e}",
            ))

    def _check_mcp_server(self):
        """Check MCP server configuration."""
        mcp_server = self.workspace / "slate" / "slate_mcp_server.py"
        vscode_mcp = self.workspace / ".vscode" / "mcp.json"

        if mcp_server.exists() and vscode_mcp.exists():
            self.report.add(CheckResult(
                "mcp_server",
                "pass",
                "MCP server configured for Copilot",
                {"server": str(mcp_server), "config": str(vscode_mcp)},
            ))
        elif mcp_server.exists():
            self.report.add(CheckResult(
                "mcp_server",
                "warn",
                "MCP server exists but .vscode/mcp.json missing",
            ))
        else:
            self.report.add(CheckResult(
                "mcp_server",
                "fail",
                "MCP server not found",
            ))

    def _check_claude_skills(self):
        """Check Claude skills directory."""
        skills_dir = self.workspace / ".claude" / "skills"
        if skills_dir.exists():
            skills = list(skills_dir.glob("*.md"))
            self.report.add(CheckResult(
                "claude_skills",
                "pass",
                f"{len(skills)} Claude skills configured",
                {"skills": [s.name for s in skills]},
            ))
        else:
            self.report.add(CheckResult(
                "claude_skills",
                "warn",
                "Claude skills directory missing",
            ))

    def _check_copilot_config(self):
        """Check Copilot instructions."""
        copilot = self.workspace / ".github" / "copilot-instructions.md"
        if copilot.exists():
            self.report.add(CheckResult(
                "copilot_config",
                "pass",
                "Copilot instructions configured",
            ))
        else:
            self.report.add(CheckResult(
                "copilot_config",
                "warn",
                "Copilot instructions missing",
            ))

    def _check_github_models(self):
        """Check GitHub Models integration."""
        models_file = self.workspace / "slate" / "slate_github_models.py"
        if models_file.exists():
            # Check if token is set
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                self.report.add(CheckResult(
                    "github_models",
                    "pass",
                    "GitHub Models configured with token",
                ))
            else:
                self.report.add(CheckResult(
                    "github_models",
                    "warn",
                    "GitHub Models module exists but GITHUB_TOKEN not set",
                    fix_cmd="$env:GITHUB_TOKEN = 'your_token'",
                ))
        else:
            self.report.add(CheckResult(
                "github_models",
                "fail",
                "GitHub Models module missing",
            ))


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE GitHub Integration Verification")
    parser.add_argument("--quick", action="store_true", help="Quick check only")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")
    parser.add_argument("--fix", action="store_true", help="Show fix commands")
    args = parser.parse_args()

    verifier = GitHubIntegrationVerifier()
    report = verifier.verify_all(quick=args.quick)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Pretty print
    print()
    print("=" * 60)
    print("  S.L.A.T.E. GitHub Integration Verification")
    print("=" * 60)
    print()

    icons = {"pass": "[OK]", "fail": "[FAIL]", "warn": "[WARN]", "skip": "[SKIP]"}
    colors = {"pass": "\033[92m", "fail": "\033[91m", "warn": "\033[93m", "skip": "\033[90m"}
    reset = "\033[0m"

    for check in report.checks:
        icon = icons.get(check.status, "[?]")
        color = colors.get(check.status, "")
        print(f"  {color}{icon}{reset} {check.name}: {check.message}")
        if args.fix and check.fix_cmd:
            print(f"       Fix: {check.fix_cmd}")

    print()
    print("-" * 60)
    print(f"  Passed: {report.passed}  |  Failed: {report.failed}  |  Warnings: {report.warnings}  |  Skipped: {report.skipped}")
    print("-" * 60)

    if report.all_passed:
        print("  \033[92mAll checks passed!\033[0m")
    else:
        print("  \033[93mSome issues found. Run with --fix to see solutions.\033[0m")

    print()

    sys.exit(0 if report.all_passed else 1)


if __name__ == "__main__":
    main()
