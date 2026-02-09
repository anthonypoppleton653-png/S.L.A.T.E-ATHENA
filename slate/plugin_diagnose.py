#!/usr/bin/env python3
# Modified: 2026-02-09T03:35:00Z | Author: Claude Opus 4.5 | Change: Plugin diagnostic tool
"""
SLATE Plugin Diagnostic Tool

Diagnoses plugin installation issues and reports status.
Can be run from any location - automatically detects plugin root.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def find_plugin_root() -> Path:
    """Find the plugin root directory."""
    # Check environment variable first
    if os.environ.get("SLATE_PLUGIN_ROOT"):
        return Path(os.environ["SLATE_PLUGIN_ROOT"])

    # Detect from this file's location
    return Path(__file__).resolve().parent.parent


def check_python() -> dict:
    """Check Python environment."""
    root = find_plugin_root()
    venv_python = root / ".venv" / "Scripts" / "python.exe"

    result = {
        "name": "Python Environment",
        "status": "FAIL",
        "details": []
    }

    result["details"].append(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    result["details"].append(f"Executable: {sys.executable}")

    if venv_python.exists():
        result["details"].append(f"Venv Python: {venv_python} [EXISTS]")
        result["status"] = "OK"
    else:
        result["details"].append(f"Venv Python: {venv_python} [NOT FOUND]")
        # Check if we're running from venv anyway
        if ".venv" in sys.executable or "venv" in sys.executable:
            result["status"] = "OK"
            result["details"].append("Running from virtual environment")

    return result


def check_plugin_structure() -> dict:
    """Check plugin directory structure."""
    root = find_plugin_root()

    result = {
        "name": "Plugin Structure",
        "status": "OK",
        "details": []
    }

    required_files = [
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        ".mcp.json",
        ".claude/hooks.json",
        ".claude/settings.json",
        "slate/mcp_server.py",
        "slate/mcp_launcher.py",
        "slate/mcp_launcher.ps1",
    ]

    missing = []
    for file in required_files:
        path = root / file
        if path.exists():
            result["details"].append(f"[OK] {file}")
        else:
            result["details"].append(f"[MISSING] {file}")
            missing.append(file)

    if missing:
        result["status"] = "FAIL"
        result["details"].append(f"Missing {len(missing)} required files")

    return result


def check_commands() -> dict:
    """Check slash commands."""
    root = find_plugin_root()
    commands_dir = root / ".claude" / "commands"

    result = {
        "name": "Slash Commands",
        "status": "OK",
        "details": []
    }

    if not commands_dir.exists():
        result["status"] = "FAIL"
        result["details"].append(f"Commands directory not found: {commands_dir}")
        return result

    commands = list(commands_dir.glob("*.md"))
    result["details"].append(f"Found {len(commands)} commands")

    slate_commands = [c for c in commands if c.stem.startswith("slate")]
    result["details"].append(f"SLATE commands: {len(slate_commands)}")

    for cmd in slate_commands[:5]:  # Show first 5
        result["details"].append(f"  - /{cmd.stem}")

    if len(slate_commands) > 5:
        result["details"].append(f"  ... and {len(slate_commands) - 5} more")

    return result


def check_skills() -> dict:
    """Check skills."""
    root = find_plugin_root()
    skills_dir = root / "skills"

    result = {
        "name": "Skills",
        "status": "OK",
        "details": []
    }

    if not skills_dir.exists():
        result["status"] = "FAIL"
        result["details"].append(f"Skills directory not found: {skills_dir}")
        return result

    skills = list(skills_dir.glob("*/SKILL.md"))
    result["details"].append(f"Found {len(skills)} skills")

    for skill in skills[:5]:
        result["details"].append(f"  - {skill.parent.name}")

    if len(skills) > 5:
        result["details"].append(f"  ... and {len(skills) - 5} more")

    return result


def check_mcp_config() -> dict:
    """Check MCP configuration."""
    root = find_plugin_root()
    mcp_json = root / ".mcp.json"

    result = {
        "name": "MCP Configuration",
        "status": "OK",
        "details": []
    }

    if not mcp_json.exists():
        result["status"] = "FAIL"
        result["details"].append(".mcp.json not found")
        return result

    try:
        with open(mcp_json) as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})
        result["details"].append(f"Configured servers: {len(servers)}")

        for name, server in servers.items():
            cmd = server.get("command", "unknown")
            result["details"].append(f"  - {name}: {cmd}")

            # Check for variable usage
            args = server.get("args", [])
            for arg in args:
                if "${CLAUDE_PLUGIN_ROOT}" in str(arg):
                    result["details"].append(f"    Uses ${{CLAUDE_PLUGIN_ROOT}} variable")
                    break
    except json.JSONDecodeError as e:
        result["status"] = "FAIL"
        result["details"].append(f"Invalid JSON: {e}")

    return result


def check_hooks() -> dict:
    """Check hooks configuration."""
    root = find_plugin_root()
    hooks_json = root / ".claude" / "hooks.json"

    result = {
        "name": "Hooks Configuration",
        "status": "OK",
        "details": []
    }

    if not hooks_json.exists():
        result["status"] = "WARN"
        result["details"].append("hooks.json not found (optional)")
        return result

    try:
        with open(hooks_json) as f:
            config = json.load(f)

        hooks = config.get("hooks", {})
        total_hooks = sum(len(v) for v in hooks.values() if isinstance(v, list))
        result["details"].append(f"Total hooks: {total_hooks}")

        for event, hook_list in hooks.items():
            if isinstance(hook_list, list):
                result["details"].append(f"  - {event}: {len(hook_list)} hooks")
    except json.JSONDecodeError as e:
        result["status"] = "FAIL"
        result["details"].append(f"Invalid JSON: {e}")

    return result


def check_mcp_server() -> dict:
    """Check if MCP server can start."""
    root = find_plugin_root()
    mcp_server = root / "slate" / "mcp_server.py"

    result = {
        "name": "MCP Server",
        "status": "OK",
        "details": []
    }

    if not mcp_server.exists():
        result["status"] = "FAIL"
        result["details"].append("mcp_server.py not found")
        return result

    # Try to import the module
    try:
        sys.path.insert(0, str(root))
        import slate.mcp_server
        result["details"].append("Module imports successfully")
    except ImportError as e:
        result["status"] = "FAIL"
        result["details"].append(f"Import error: {e}")
    except Exception as e:
        result["status"] = "WARN"
        result["details"].append(f"Warning: {e}")

    return result


def run_diagnostics():
    """Run all diagnostic checks."""
    root = find_plugin_root()

    print("=" * 60)
    print("  SLATE Plugin Diagnostics")
    print("=" * 60)
    print(f"\nPlugin Root: {root}")
    print(f"Environment: SLATE_PLUGIN_ROOT = {os.environ.get('SLATE_PLUGIN_ROOT', 'not set')}")
    print()

    checks = [
        check_python(),
        check_plugin_structure(),
        check_commands(),
        check_skills(),
        check_mcp_config(),
        check_hooks(),
        check_mcp_server(),
    ]

    passed = 0
    failed = 0
    warnings = 0

    for check in checks:
        status = check["status"]
        name = check["name"]

        if status == "OK":
            icon = "[OK]"
            passed += 1
        elif status == "WARN":
            icon = "[WARN]"
            warnings += 1
        else:
            icon = "[FAIL]"
            failed += 1

        print(f"{icon} {name}")
        for detail in check["details"]:
            print(f"    {detail}")
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 60)

    if failed > 0:
        print("\nTo fix issues:")
        print("  1. Ensure you're in the SLATE workspace")
        print("  2. Run: python install_claude_plugin.py --validate")
        print("  3. Check that .venv exists with required packages")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(run_diagnostics())
