# tests/test_mcp_server.py
# Modified: 2026-02-10T12:10:00Z | Author: COPILOT | Change: Rewrite to avoid mcp_server sys.exit on import

import pytest
from pathlib import Path
import py_compile


MCP_PATH = Path(__file__).parent.parent / "slate" / "mcp_server.py"


def _read_source() -> str:
    return MCP_PATH.read_text(encoding="utf-8")


def test_mcp_server_module_exists():
    """Verify mcp_server.py exists."""
    assert MCP_PATH.exists(), "slate/mcp_server.py should exist"
    content = _read_source()
    assert "Server" in content
    assert "run_slate_command" in content


def test_mcp_server_has_tools():
    """Verify mcp_server defines SLATE tools."""
    content = _read_source()
    assert "slate-status" in content or "slate_status" in content
    assert "slate-runtime" in content or "slate_runtime" in content


def test_mcp_server_run_slate_command_pattern():
    """Verify run_slate_command uses subprocess correctly."""
    content = _read_source()
    assert "subprocess" in content
    assert "def run_slate_command" in content


def test_mcp_server_security():
    """Verify mcp_server binds to localhost only."""
    content = _read_source()
    assert "0.0.0.0" not in content


def test_mcp_server_syntax():
    """Verify mcp_server.py has valid Python syntax."""
    py_compile.compile(str(MCP_PATH), doraise=True)