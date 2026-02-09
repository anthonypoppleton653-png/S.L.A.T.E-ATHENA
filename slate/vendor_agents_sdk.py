#!/usr/bin/env python3
# Modified: 2026-02-10T12:30:00Z | Author: COPILOT | Change: Add handoff function import alongside Handoff class
"""
Vendor OpenAI Agents SDK Import Helper
========================================
Imports Agent, function_tool, InputGuardrail, OutputGuardrail, Runner, Handoff,
handoff (factory function) from the vendored openai-agents-python fork at
vendor/openai-agents-python/src.

Problem:
    SLATE's `agents/` directory shadows the pip-installed `agents` package.
    Direct `import agents` always resolves to SLATE's `agents/__init__.py`.

Solution:
    sys.path swap — temporarily insert vendor path, clear SLATE's agents from
    sys.modules, import SDK classes, then restore everything.

Usage:
    from slate.vendor_agents_sdk import (
        Agent, function_tool, FunctionTool,
        InputGuardrail, OutputGuardrail,
        Runner, Handoff, handoff as handoff_factory,
        SDK_AVAILABLE,
    )

Note:
    This does NOT require openai>=2.9.0. It only imports the type/schema
    infrastructure — not the OpenAI client bits. The vendor SDK is used for
    its Agent/Tool/Guardrail abstractions, not for API calls.
"""

import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
VENDOR_SDK_SRC = WORKSPACE_ROOT / "vendor" / "openai-agents-python" / "src"

# Sentinel values for when SDK isn't available
SDK_AVAILABLE = False

# These will be populated by _import_sdk()
Agent: Any = None
function_tool: Any = None
FunctionTool: Any = None
InputGuardrail: Any = None
OutputGuardrail: Any = None
Runner: Any = None
Handoff: Any = None
handoff: Any = None  # Factory function: handoff(agent) -> Handoff
RunConfig: Any = None


def _import_sdk() -> bool:
    """
    Import openai-agents-python SDK classes using sys.path swap technique.

    Returns True if successful, False otherwise.
    """
    global Agent, function_tool, FunctionTool
    global InputGuardrail, OutputGuardrail
    global Runner, Handoff, handoff, RunConfig
    global SDK_AVAILABLE

    if not VENDOR_SDK_SRC.exists():
        return False

    vendor_src = str(VENDOR_SDK_SRC)

    # Save state
    original_path = sys.path[:]
    stashed_modules = {}

    # Stash any existing 'agents' module (SLATE's agents/ directory)
    for key in list(sys.modules.keys()):
        if key == 'agents' or key.startswith('agents.'):
            stashed_modules[key] = sys.modules.pop(key)

    try:
        # Insert vendor path at front
        sys.path.insert(0, vendor_src)

        # Import SDK classes
        from agents import Agent as _Agent
        from agents import function_tool as _function_tool
        from agents.tool import FunctionTool as _FunctionTool
        from agents import InputGuardrail as _InputGuardrail
        from agents import OutputGuardrail as _OutputGuardrail
        from agents import Runner as _Runner
        from agents import Handoff as _Handoff

        # Import handoff factory function
        from agents.handoffs import handoff as _handoff_factory

        # Try RunConfig (may not exist in all versions)
        try:
            from agents import RunConfig as _RunConfig
        except ImportError:
            _RunConfig = None

        # Assign to module-level globals
        Agent = _Agent
        function_tool = _function_tool
        FunctionTool = _FunctionTool
        InputGuardrail = _InputGuardrail
        OutputGuardrail = _OutputGuardrail
        Runner = _Runner
        Handoff = _Handoff
        handoff = _handoff_factory
        RunConfig = _RunConfig

        SDK_AVAILABLE = True
        return True

    except Exception as e:
        # Import failed — SDK may have incompatible dependencies
        import traceback
        print(f"[SLATE] vendor_agents_sdk: import failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

    finally:
        # Remove any vendor 'agents' modules we loaded
        for key in list(sys.modules.keys()):
            if key == 'agents' or key.startswith('agents.'):
                sys.modules.pop(key, None)

        # Restore original SLATE agents modules
        sys.modules.update(stashed_modules)

        # Restore original sys.path
        sys.path[:] = original_path


# Run import at module load
_import_sdk()


def get_sdk_info() -> dict:
    """Return SDK import status for diagnostics."""
    return {
        "available": SDK_AVAILABLE,
        "vendor_path": str(VENDOR_SDK_SRC),
        "vendor_exists": VENDOR_SDK_SRC.exists(),
        "classes": {
            "Agent": Agent is not None,
            "function_tool": function_tool is not None,
            "FunctionTool": FunctionTool is not None,
            "InputGuardrail": InputGuardrail is not None,
            "OutputGuardrail": OutputGuardrail is not None,
            "Runner": Runner is not None,
            "Handoff": Handoff is not None,
            "RunConfig": RunConfig is not None,
        },
    }


if __name__ == "__main__":
    import json
    info = get_sdk_info()
    print(json.dumps(info, indent=2))
    if SDK_AVAILABLE:
        print(f"\nAgent class: {Agent}")
        print(f"function_tool: {function_tool}")
        print(f"FunctionTool: {FunctionTool}")
    else:
        print("\nSDK NOT available — check vendor/openai-agents-python/src exists")
