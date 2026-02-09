#!/usr/bin/env python3
"""
SLATE Claude Code Plugin Installer

This script registers the SLATE plugin marketplace with Claude Code.
Plugins are loaded dynamically without restart.

Usage:
    python install_claude_plugin.py              # Install/update
    python install_claude_plugin.py --uninstall  # Remove
    python install_claude_plugin.py --validate   # Validate structure
    python install_claude_plugin.py --dev        # Load for development (no install)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def get_claude_dir() -> Path:
    """Get the Claude Code configuration directory."""
    if sys.platform == "win32":
        claude_dir = Path(os.environ.get("USERPROFILE", "")) / ".claude"
    else:
        claude_dir = Path.home() / ".claude"
    return claude_dir


def get_workspace_root() -> Path:
    """Get the SLATE workspace root."""
    return Path(__file__).parent.resolve()


def validate_plugin_structure(workspace: Path) -> bool:
    """Validate that the plugin structure is correct."""
    required_files = [
        workspace / ".claude-plugin" / "plugin.json",
        workspace / ".claude-plugin" / "marketplace.json",
        workspace / ".mcp.json",
    ]

    for req_file in required_files:
        if not req_file.exists():
            print(f"ERROR: Missing required file: {req_file}")
            return False

    # Validate plugin.json
    try:
        with open(workspace / ".claude-plugin" / "plugin.json") as fp:
            plugin_data = json.load(fp)
            if "name" not in plugin_data:
                print("ERROR: plugin.json missing 'name' field")
                return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in plugin.json: {e}")
        return False

    # Validate marketplace.json
    try:
        with open(workspace / ".claude-plugin" / "marketplace.json") as fp:
            marketplace_data = json.load(fp)
            if "plugins" not in marketplace_data:
                print("ERROR: marketplace.json missing 'plugins' array")
                return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in marketplace.json: {e}")
        return False

    # Check for skills
    skills_dir = workspace / "skills"
    if skills_dir.exists():
        skill_count = len(list(skills_dir.glob("*/SKILL.md")))
        print(f"Found {skill_count} skills in skills/")

    # Check for commands
    commands_dir = workspace / ".claude" / "commands"
    if commands_dir.exists():
        command_count = len(list(commands_dir.glob("*.md")))
        print(f"Found {command_count} commands in .claude/commands/")

    return True


def install_marketplace(workspace: Path, claude_dir: Path) -> bool:
    """Register SLATE marketplace in Claude Code settings."""
    settings_file = claude_dir / "settings.json"
    settings = {}

    if settings_file.exists():
        try:
            with open(settings_file) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            pass

    # Add marketplace to extraKnownMarketplaces
    if "extraKnownMarketplaces" not in settings:
        settings["extraKnownMarketplaces"] = {}

    workspace_str = str(workspace).replace("\\", "/")

    # Local marketplace for development
    settings["extraKnownMarketplaces"]["slate-local"] = {
        "source": workspace_str
    }

    # GitHub marketplace for distribution
    settings["extraKnownMarketplaces"]["slate"] = {
        "source": {
            "source": "github",
            "repo": "SynchronizedLivingArchitecture/S.L.A.T.E"
        }
    }

    # Enable the local plugin
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}

    settings["enabledPlugins"]["slate@slate-local"] = True

    # Write updated settings
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"\nMarketplace 'slate-local' registered at: {workspace_str}")
    print("Plugin 'slate@slate-local' enabled")

    return True


def uninstall_marketplace(workspace: Path, claude_dir: Path) -> bool:
    """Remove SLATE marketplace from Claude Code settings."""
    settings_file = claude_dir / "settings.json"

    if not settings_file.exists():
        print("No settings file found")
        return True

    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print("Invalid settings.json")
        return False

    # Remove from extraKnownMarketplaces
    if "extraKnownMarketplaces" in settings:
        settings["extraKnownMarketplaces"].pop("slate-local", None)
        settings["extraKnownMarketplaces"].pop("slate", None)

    # Remove from enabledPlugins
    if "enabledPlugins" in settings:
        keys_to_remove = [k for k in settings["enabledPlugins"] if k.startswith("slate@")]
        for k in keys_to_remove:
            del settings["enabledPlugins"][k]

    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    print("SLATE marketplace removed from Claude Code settings")
    return True


def dev_load(workspace: Path) -> None:
    """Print command to load plugin for development (no install needed)."""
    workspace_str = str(workspace).replace("\\", "/")
    print("\nTo load SLATE plugin for development (no restart needed):")
    print(f"  claude --plugin-dir \"{workspace_str}\"")
    print("\nOr in an existing session, the plugin is auto-loaded from the workspace.")


def main():
    parser = argparse.ArgumentParser(
        description="Install SLATE plugin for Claude Code"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall the plugin marketplace"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate the plugin structure"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Show development loading command (no install)"
    )
    args = parser.parse_args()

    workspace = get_workspace_root()
    claude_dir = get_claude_dir()

    print("SLATE Claude Code Plugin")
    print("=" * 40)
    print(f"Workspace: {workspace}")
    print(f"Claude Config: {claude_dir}")
    print()

    # Validate plugin structure
    if not validate_plugin_structure(workspace):
        print("\nPlugin validation failed!")
        sys.exit(1)

    print("\nPlugin structure validated successfully!")

    if args.validate:
        sys.exit(0)

    if args.dev:
        dev_load(workspace)
        sys.exit(0)

    if args.uninstall:
        if not uninstall_marketplace(workspace, claude_dir):
            sys.exit(1)
    else:
        if not install_marketplace(workspace, claude_dir):
            sys.exit(1)

    print("\n" + "=" * 40)
    print("Plugin Installation Complete!")
    print("=" * 40)
    print("\nUsage:")
    print("  /slate:status     - Check system status")
    print("  /slate:start      - Start SLATE services")
    print("  /slate:help       - Show all commands")
    print("\nNote: Plugin loads automatically in this workspace.")
    print("For other directories, add the marketplace:")
    print("  /plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E")


if __name__ == "__main__":
    main()
