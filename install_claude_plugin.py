#!/usr/bin/env python3
# Modified: 2026-02-09T03:00:00Z | Author: Claude Opus 4.5 | Change: Simplify for local development (no install needed)
"""
SLATE Claude Code Plugin Manager

For LOCAL DEVELOPMENT: No installation needed! The plugin auto-loads when
you're in the SLATE workspace because .claude-plugin/plugin.json exists.

For EXTERNAL USERS installing from GitHub:
    /plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E
    /plugin install slate@slate-marketplace

Usage:
    python install_claude_plugin.py              # Show local dev instructions
    python install_claude_plugin.py --validate   # Validate plugin structure
    python install_claude_plugin.py --global     # Install to global settings (optional)
    python install_claude_plugin.py --uninstall  # Remove from global settings
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
    """Register SLATE marketplace in Claude Code settings (merges, doesn't overwrite)."""
    settings_file = claude_dir / "settings.json"
    settings = {}

    # Read existing settings - preserve all other configuration
    if settings_file.exists():
        try:
            with open(settings_file, encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    settings = json.loads(content)
                    print(f"Loaded existing settings ({len(settings)} keys)")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse existing settings.json: {e}")
            print("Creating new settings file...")
        except Exception as e:
            print(f"Warning: Error reading settings.json: {e}")

    # Add marketplace to extraKnownMarketplaces
    if "extraKnownMarketplaces" not in settings:
        settings["extraKnownMarketplaces"] = {}

    workspace_str = str(workspace).replace("\\", "/")

    # GitHub marketplace for distribution (matches VS Code plugin manager)
    settings["extraKnownMarketplaces"]["slate-marketplace"] = {
        "source": {
            "source": "github",
            "repo": "SynchronizedLivingArchitecture/S.L.A.T.E"
        }
    }

    # Enable the plugin
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}

    settings["enabledPlugins"]["slate@slate-marketplace"] = True

    # Write updated settings
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"\nMarketplace 'slate-marketplace' registered")
    print("Plugin 'slate@slate-marketplace' enabled")

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
        settings["extraKnownMarketplaces"].pop("slate-marketplace", None)

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
        description="SLATE Claude Code Plugin Manager"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the plugin structure"
    )
    parser.add_argument(
        "--global",
        dest="install_global",
        action="store_true",
        help="Install to global Claude settings (optional, for external access)"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove from global Claude settings"
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

    if args.uninstall:
        if not uninstall_marketplace(workspace, claude_dir):
            sys.exit(1)
        print("\nGlobal marketplace registration removed.")
        sys.exit(0)

    if args.install_global:
        if not install_marketplace(workspace, claude_dir):
            sys.exit(1)
        print("\n" + "=" * 40)
        print("Global Installation Complete!")
        print("=" * 40)
        sys.exit(0)

    # Default: Show local development info
    print("\n" + "=" * 40)
    print("LOCAL DEVELOPMENT MODE")
    print("=" * 40)
    print("\nNo installation needed for local development!")
    print("The plugin auto-loads because .claude-plugin/plugin.json exists.")
    print("\nJust run Claude Code in this workspace:")
    print(f"  cd {workspace}")
    print("  claude")
    print("\nAvailable commands:")
    print("  /slate:status     - Check system status")
    print("  /slate:help       - Show all commands")
    print("  /slate-workflow   - Manage task queue")
    print("\nFor external users (installing from GitHub):")
    print("  /plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E")
    print("  /plugin install slate@slate-marketplace")


if __name__ == "__main__":
    main()
