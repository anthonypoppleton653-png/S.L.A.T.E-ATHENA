#!/usr/bin/env python3
# Modified: 2026-02-09T03:10:00Z | Author: Claude Opus 4.5 | Change: Add SLATE_PLUGIN_ROOT env var support
"""
SLATE MCP Server Launcher

This launcher detects its own location and starts the MCP server with correct paths.
Works for both local development and marketplace installations.

Path resolution priority:
1. SLATE_PLUGIN_ROOT environment variable (set by Claude Code plugin system)
2. __file__ detection (fallback for direct invocation)
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Detect workspace root - prefer env var if set by Claude Code
    plugin_root = os.environ.get("SLATE_PLUGIN_ROOT")

    if plugin_root:
        workspace_root = Path(plugin_root)
        slate_dir = workspace_root / "slate"
    else:
        # Fallback: detect from this file's location
        launcher_path = Path(__file__).resolve()
        slate_dir = launcher_path.parent  # slate/
        workspace_root = slate_dir.parent  # project root

    # Find the MCP server
    mcp_server = slate_dir / "mcp_server.py"

    if not mcp_server.exists():
        print(f"ERROR: MCP server not found at {mcp_server}", file=sys.stderr)
        sys.exit(1)

    # Find Python interpreter
    # Priority: 1. SLATE_PYTHON env var, 2. .venv in workspace, 3. System python
    python_exe = os.environ.get("SLATE_PYTHON")

    if not python_exe:
        venv_python = workspace_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)
        else:
            # Try Linux/Mac venv path
            venv_python = workspace_root / ".venv" / "bin" / "python"
            if venv_python.exists():
                python_exe = str(venv_python)
            else:
                python_exe = sys.executable

    # Set up environment
    env = os.environ.copy()
    env["SLATE_WORKSPACE"] = str(workspace_root)
    env["PYTHONPATH"] = str(workspace_root)
    env.setdefault("SLATE_BEHAVIOR", "operator")
    env.setdefault("SLATE_ACTIONGUARD", "enabled")

    # Run the MCP server
    args = [python_exe, str(mcp_server)] + sys.argv[1:]

    try:
        result = subprocess.run(args, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"ERROR: Python not found at {python_exe}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
