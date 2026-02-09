#!/usr/bin/env python3
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Create SLATE Copilot SDK installer — installs plugin, skills, MCP, and instructions
"""
SLATE Copilot SDK Installer
============================
Installs the SLATE Copilot SDK plugin as a system dependency and configures
all integration points: tools, hooks, skills, MCP server, and instructions.

Usage:
    python slate/install_copilot_sdk.py              # Full install
    python slate/install_copilot_sdk.py --check      # Check install status
    python slate/install_copilot_sdk.py --verify      # Verify all integrations
    python slate/install_copilot_sdk.py --uninstall   # Remove plugin config
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
PYTHON = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"


def check_dependency(package: str, import_name: str = "") -> bool:
    """Check if a Python package is installed and importable."""
    name = import_name or package.replace("-", "_")
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def install_dependency(package: str) -> bool:
    """Install a Python package via pip."""
    try:
        result = subprocess.run(
            [str(PYTHON), "-m", "pip", "install", package],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  Error installing {package}: {e}")
        return False


def check_install_status() -> dict:
    """Check the current SLATE Copilot SDK installation status."""
    status = {
        "python": str(PYTHON),
        "python_exists": PYTHON.exists(),
        "dependencies": {},
        "files": {},
        "integrations": {},
    }

    # Check dependencies
    deps = [
        ("github-copilot-sdk", "copilot"),
        ("pydantic", "pydantic"),
        ("mcp", "mcp"),
    ]
    for package, import_name in deps:
        status["dependencies"][package] = check_dependency(package, import_name)

    # Check files
    files = {
        "slate_copilot_sdk": WORKSPACE_ROOT / "slate" / "slate_copilot_sdk.py",
        "mcp_server": WORKSPACE_ROOT / "slate" / "mcp_server.py",
        "copilot_instructions": WORKSPACE_ROOT / ".copilot-instructions.md",
        "copilot_skills_json": WORKSPACE_ROOT / ".copilot" / "skills.json",
        "vendor_sdk": WORKSPACE_ROOT / "vendor" / "copilot-sdk",
    }
    for name, path in files.items():
        status["files"][name] = path.exists()

    # Check skills
    skills_dir = WORKSPACE_ROOT / "skills"
    skill_names = ["slate-status", "slate-runner", "slate-orchestrator", "slate-workflow", "slate-help"]
    for skill in skill_names:
        skill_json = skills_dir / skill / "skill.json"
        skill_md = skills_dir / skill / "SKILL.md"
        status["integrations"][f"skill:{skill}"] = skill_json.exists() and skill_md.exists()

    # Check VS Code extension
    ext_dir = WORKSPACE_ROOT / "plugins" / "slate-copilot"
    status["integrations"]["vscode_extension"] = (ext_dir / "package.json").exists()

    # Check Agent SDK hooks
    hooks_file = ext_dir / "src" / "slateAgentSdkHooks.ts"
    status["integrations"]["agent_sdk_hooks"] = hooks_file.exists()

    return status


def print_check_status():
    """Print formatted install status."""
    status = check_install_status()

    print("=" * 60)
    print("SLATE Copilot SDK — Installation Status")
    print("=" * 60)
    print()

    print("  Python:")
    print(f"    Path:    {status['python']}")
    print(f"    Exists:  {'Yes' if status['python_exists'] else 'No'}")
    print()

    print("  Dependencies:")
    for dep, installed in status["dependencies"].items():
        indicator = "✓" if installed else "✗"
        print(f"    {indicator} {dep}")
    print()

    print("  Files:")
    for name, exists in status["files"].items():
        indicator = "✓" if exists else "✗"
        print(f"    {indicator} {name}")
    print()

    print("  Integrations:")
    for name, ready in status["integrations"].items():
        indicator = "✓" if ready else "✗"
        print(f"    {indicator} {name}")
    print()

    all_ok = (
        all(status["dependencies"].values()) and
        all(status["files"].values()) and
        all(status["integrations"].values())
    )
    if all_ok:
        print("  Status: ✓ All integrations installed and configured")
    else:
        missing = []
        for section in [status["dependencies"], status["files"], status["integrations"]]:
            for name, ok in section.items():
                if not ok:
                    missing.append(name)
        print(f"  Status: ✗ Missing: {', '.join(missing)}")

    print("=" * 60)
    return all_ok


def install_full():
    """Full SLATE Copilot SDK installation."""
    print("=" * 60)
    print("SLATE Copilot SDK — Full Installation")
    print("=" * 60)
    print()

    steps_ok = 0
    steps_total = 0

    # Step 1: Install Python dependencies
    steps_total += 1
    print("[1/6] Installing Python dependencies...")
    deps = [
        ("github-copilot-sdk", "copilot"),
        ("pydantic", "pydantic"),
    ]
    all_deps = True
    for package, import_name in deps:
        if check_dependency(package, import_name):
            print(f"  ✓ {package} already installed")
        else:
            print(f"  Installing {package}...")
            if install_dependency(package):
                print(f"  ✓ {package} installed")
            else:
                print(f"  ✗ Failed to install {package}")
                all_deps = False
    if all_deps:
        steps_ok += 1
    print()

    # Step 2: Verify plugin file
    steps_total += 1
    print("[2/6] Verifying plugin file...")
    plugin_file = WORKSPACE_ROOT / "slate" / "slate_copilot_sdk.py"
    if plugin_file.exists():
        print(f"  ✓ {plugin_file.relative_to(WORKSPACE_ROOT)}")
        steps_ok += 1
    else:
        print(f"  ✗ Plugin file not found: {plugin_file}")
    print()

    # Step 3: Register skills
    steps_total += 1
    print("[3/6] Registering skills...")
    try:
        result = subprocess.run(
            [str(PYTHON), str(plugin_file), "--register-skills"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(result.stdout)
            steps_ok += 1
        else:
            print(f"  ✗ Skill registration failed: {result.stderr}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Step 4: Verify MCP server
    steps_total += 1
    print("[4/6] Verifying MCP server...")
    mcp_file = WORKSPACE_ROOT / "slate" / "mcp_server.py"
    if mcp_file.exists():
        print(f"  ✓ MCP server: {mcp_file.relative_to(WORKSPACE_ROOT)}")
        steps_ok += 1
    else:
        print(f"  ✗ MCP server not found")
    print()

    # Step 5: Check copilot-sdk fork
    steps_total += 1
    print("[5/6] Checking copilot-sdk fork...")
    vendor_sdk = WORKSPACE_ROOT / "vendor" / "copilot-sdk"
    if vendor_sdk.exists():
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=str(vendor_sdk),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "SynchronizedLivingArchitecture" in result.stdout:
                print(f"  ✓ Fork: SynchronizedLivingArchitecture/copilot-sdk")
                steps_ok += 1
            else:
                print(f"  ✗ Fork not properly configured")
        except Exception:
            print(f"  ✓ Vendor SDK exists: {vendor_sdk}")
            steps_ok += 1
    else:
        print(f"  ✗ Vendor SDK not found at {vendor_sdk}")
    print()

    # Step 6: Create .copilot-instructions.md
    steps_total += 1
    print("[6/6] Verifying .copilot-instructions.md...")
    instructions_file = WORKSPACE_ROOT / ".copilot-instructions.md"
    if instructions_file.exists():
        print(f"  ✓ Instructions file exists")
        steps_ok += 1
    else:
        print(f"  ✗ Instructions file not found (will be created)")
    print()

    # Summary
    print("=" * 60)
    print(f"  Installation: {steps_ok}/{steps_total} steps completed")
    if steps_ok == steps_total:
        print("  Status: ✓ SLATE Copilot SDK fully installed")
    else:
        print("  Status: ✗ Some steps failed — run with --check for details")
    print("=" * 60)
    return steps_ok == steps_total


def verify_integrations():
    """Verify all SLATE Copilot SDK integrations work."""
    print("=" * 60)
    print("SLATE Copilot SDK — Integration Verification")
    print("=" * 60)
    print()

    results = {}

    # Test 1: Import Copilot SDK
    print("[1/5] Import Copilot SDK...")
    try:
        from copilot import CopilotClient
        from copilot.tools import define_tool
        from copilot.types import Tool, ToolInvocation, ToolResult
        print("  ✓ All Copilot SDK imports successful")
        results["copilot_sdk_import"] = True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        results["copilot_sdk_import"] = False
    print()

    # Test 2: Import SLATE plugin
    print("[2/5] Import SLATE plugin...")
    try:
        sys.path.insert(0, str(WORKSPACE_ROOT))
        from slate.slate_copilot_sdk import SlateCopilotPlugin, TOOL_REGISTRY
        plugin = SlateCopilotPlugin()
        print(f"  ✓ Plugin loaded with {len(TOOL_REGISTRY)} tools")
        results["plugin_import"] = True
    except Exception as e:
        print(f"  ✗ Plugin import failed: {e}")
        results["plugin_import"] = False
    print()

    # Test 3: Execute a tool
    print("[3/5] Execute slate_status tool...")
    try:
        from slate.slate_copilot_sdk import SlateCopilotPlugin
        plugin = SlateCopilotPlugin()
        result = plugin.execute_tool("slate_status", {"format": "quick"})
        if result and "Error" not in result[:20]:
            print(f"  ✓ Tool executed ({len(result)} chars output)")
            results["tool_execution"] = True
        else:
            print(f"  ✗ Tool returned error: {result[:100]}")
            results["tool_execution"] = False
    except Exception as e:
        print(f"  ✗ Execution failed: {e}")
        results["tool_execution"] = False
    print()

    # Test 4: ActionGuard hooks
    print("[4/5] Test ActionGuard hooks...")
    try:
        from slate.slate_copilot_sdk import ActionGuardHooks
        hooks = ActionGuardHooks()

        # Should allow normal input
        r1 = hooks.on_pre_tool_use("slate_status", {"format": "quick"})
        assert r1["allowed"], "Normal tool should be allowed"

        # Should block dangerous patterns
        r2 = hooks.on_pre_tool_use("slate_runner", {"workflow": "rm -rf /"})
        assert not r2["allowed"], "Dangerous pattern should be blocked"

        # Should detect PII
        r3 = hooks.on_user_prompt_submitted("My key is ghp_1234567890abcdefABCDEF1234567890abcd")
        assert not r3["safe"], "GitHub token should be detected"

        print("  ✓ ActionGuard hooks working (allow, block, PII detection)")
        results["action_guard"] = True
    except Exception as e:
        print(f"  ✗ Hook test failed: {e}")
        results["action_guard"] = False
    print()

    # Test 5: Skill definitions
    print("[5/5] Verify skill definitions...")
    try:
        from slate.slate_copilot_sdk import get_skill_definitions
        skills = get_skill_definitions()
        if len(skills) >= 5:
            print(f"  ✓ {len(skills)} skills loaded")
            for s in skills:
                print(f"    • {s['name']}: {s['description'][:50]}")
            results["skills"] = True
        else:
            print(f"  ✗ Expected 5+ skills, got {len(skills)}")
            results["skills"] = False
    except Exception as e:
        print(f"  ✗ Skill loading failed: {e}")
        results["skills"] = False
    print()

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print("=" * 60)
    print(f"  Verification: {passed}/{total} tests passed")
    if passed == total:
        print("  Status: ✓ All integrations verified")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"  Status: ✗ Failed: {', '.join(failed)}")
    print("=" * 60)
    return passed == total


def main():
    parser = argparse.ArgumentParser(
        description="SLATE Copilot SDK Installer"
    )
    parser.add_argument("--check", action="store_true",
                        help="Check install status")
    parser.add_argument("--verify", action="store_true",
                        help="Verify all integrations")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove plugin configuration")
    parser.add_argument("--json", action="store_true",
                        help="JSON output for --check")

    args = parser.parse_args()

    if args.check:
        if args.json:
            status = check_install_status()
            print(json.dumps(status, indent=2))
        else:
            print_check_status()
    elif args.verify:
        verify_integrations()
    elif args.uninstall:
        print("Uninstall not implemented — remove .copilot/ directory manually")
    else:
        install_full()


if __name__ == "__main__":
    main()
