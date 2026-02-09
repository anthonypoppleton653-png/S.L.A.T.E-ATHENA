#!/usr/bin/env python3
# Modified: 2026-02-09T04:45:00Z | Author: Claude | Change: Unified vendor SDK integration status and testing
"""
SLATE Vendor Integration Status
================================
Unified status and testing for all vendor SDK integrations.

Vendors Tracked:
    - openai-agents-python: Agent/Tool/Guardrail abstractions
    - semantic-kernel: LLM orchestration and skills
    - autogen: Multi-agent conversation framework
    - copilot-sdk: GitHub Copilot tool definitions
    - spec-kit: Specification-driven development workflow

Usage:
    python slate/vendor_integration.py                  # Full status
    python slate/vendor_integration.py --test           # Run integration tests
    python slate/vendor_integration.py --json           # JSON output
"""

import json
import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WORKSPACE_ROOT))


def check_openai_agents() -> dict[str, Any]:
    """Check openai-agents-python SDK integration."""
    try:
        from slate.vendor_agents_sdk import (
            SDK_AVAILABLE,
            Agent,
            function_tool,
            InputGuardrail,
            Runner,
        )
        return {
            "name": "openai-agents-python",
            "available": SDK_AVAILABLE,
            "path": str(WORKSPACE_ROOT / "vendor" / "openai-agents-python"),
            "types": {
                "Agent": Agent is not None,
                "function_tool": function_tool is not None,
                "InputGuardrail": InputGuardrail is not None,
                "Runner": Runner is not None,
            },
            "integration_file": "slate/vendor_agents_sdk.py",
        }
    except ImportError as e:
        return {
            "name": "openai-agents-python",
            "available": False,
            "error": str(e),
        }


def check_autogen() -> dict[str, Any]:
    """Check Microsoft AutoGen SDK integration."""
    try:
        from slate.vendor_autogen_sdk import (
            SDK_AVAILABLE,
            Agent,
            BaseAgent,
            AgentRuntime,
            ClosureAgent,
        )
        return {
            "name": "autogen",
            "available": SDK_AVAILABLE,
            "path": str(WORKSPACE_ROOT / "vendor" / "autogen"),
            "types": {
                "Agent": Agent is not None,
                "BaseAgent": BaseAgent is not None,
                "AgentRuntime": AgentRuntime is not None,
                "ClosureAgent": ClosureAgent is not None,
            },
            "integration_file": "slate/vendor_autogen_sdk.py",
        }
    except ImportError as e:
        return {
            "name": "autogen",
            "available": False,
            "error": str(e),
        }


def check_semantic_kernel() -> dict[str, Any]:
    """Check Microsoft Semantic Kernel integration."""
    try:
        from slate.slate_semantic_kernel import (
            _check_sk_available,
            _check_ollama_available,
        )
        sk_ok, sk_version = _check_sk_available()
        ollama_ok = _check_ollama_available()
        return {
            "name": "semantic-kernel",
            "available": sk_ok,
            "version": sk_version,
            "path": str(WORKSPACE_ROOT / "vendor" / "semantic-kernel"),
            "ollama_connected": ollama_ok,
            "integration_file": "slate/slate_semantic_kernel.py",
        }
    except ImportError as e:
        return {
            "name": "semantic-kernel",
            "available": False,
            "error": str(e),
        }


def check_copilot_sdk() -> dict[str, Any]:
    """Check GitHub Copilot SDK integration."""
    sdk_path = WORKSPACE_ROOT / "vendor" / "copilot-sdk" / "python"
    if str(sdk_path) not in sys.path:
        sys.path.insert(0, str(sdk_path))

    try:
        from copilot import define_tool
        from copilot.types import Tool, ToolResult
        return {
            "name": "copilot-sdk",
            "available": True,
            "path": str(sdk_path),
            "types": {
                "define_tool": define_tool is not None,
                "Tool": Tool is not None,
                "ToolResult": ToolResult is not None,
            },
            "integration_files": [
                "slate/copilot_sdk_tools.py",
                "slate/copilot_sdk_session.py",
            ],
        }
    except ImportError as e:
        return {
            "name": "copilot-sdk",
            "available": False,
            "error": str(e),
        }


def check_spec_kit() -> dict[str, Any]:
    """Check Spec-Kit workflow integration."""
    spec_kit_path = WORKSPACE_ROOT / "vendor" / "spec-kit"
    specs_dir = WORKSPACE_ROOT / "specs"

    # Spec-kit is a workflow toolkit, not a Python library
    # Check for presence and SLATE integration
    spec_count = len(list(specs_dir.glob("*/spec.md"))) if specs_dir.exists() else 0

    return {
        "name": "spec-kit",
        "available": spec_kit_path.exists(),
        "path": str(spec_kit_path),
        "type": "workflow-toolkit",
        "specs_directory": str(specs_dir),
        "spec_count": spec_count,
        "integration_file": "slate/slate_spec_kit.py",
    }


def get_full_status() -> dict[str, Any]:
    """Get complete vendor integration status."""
    vendors = [
        check_openai_agents(),
        check_autogen(),
        check_semantic_kernel(),
        check_copilot_sdk(),
        check_spec_kit(),
    ]

    available_count = sum(1 for v in vendors if v.get("available", False))

    return {
        "summary": {
            "total": len(vendors),
            "available": available_count,
            "unavailable": len(vendors) - available_count,
        },
        "vendors": vendors,
    }


def run_integration_tests() -> dict[str, Any]:
    """Run basic integration tests for all vendors."""
    results = []

    # Test openai-agents-python
    try:
        from slate.vendor_agents_sdk import SDK_AVAILABLE, Agent
        if SDK_AVAILABLE and Agent:
            results.append({"name": "openai-agents", "test": "import", "passed": True})
        else:
            results.append({"name": "openai-agents", "test": "import", "passed": False})
    except Exception as e:
        results.append({"name": "openai-agents", "test": "import", "passed": False, "error": str(e)})

    # Test autogen
    try:
        from slate.vendor_autogen_sdk import SDK_AVAILABLE, Agent
        if SDK_AVAILABLE and Agent:
            results.append({"name": "autogen", "test": "import", "passed": True})
        else:
            results.append({"name": "autogen", "test": "import", "passed": False})
    except Exception as e:
        results.append({"name": "autogen", "test": "import", "passed": False, "error": str(e)})

    # Test semantic-kernel
    try:
        import semantic_kernel
        results.append({"name": "semantic-kernel", "test": "import", "passed": True, "version": semantic_kernel.__version__})
    except Exception as e:
        results.append({"name": "semantic-kernel", "test": "import", "passed": False, "error": str(e)})

    # Test copilot-sdk
    try:
        sdk_path = WORKSPACE_ROOT / "vendor" / "copilot-sdk" / "python"
        sys.path.insert(0, str(sdk_path))
        from copilot import define_tool
        results.append({"name": "copilot-sdk", "test": "import", "passed": True})
    except Exception as e:
        results.append({"name": "copilot-sdk", "test": "import", "passed": False, "error": str(e)})

    # Test spec-kit (check files exist)
    try:
        spec_kit_path = WORKSPACE_ROOT / "vendor" / "spec-kit"
        readme = spec_kit_path / "README.md"
        results.append({"name": "spec-kit", "test": "exists", "passed": readme.exists()})
    except Exception as e:
        results.append({"name": "spec-kit", "test": "exists", "passed": False, "error": str(e)})

    passed = sum(1 for r in results if r.get("passed", False))
    return {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "tests": results,
    }


def print_status(status: dict[str, Any]) -> None:
    """Print formatted status output."""
    print("=" * 60)
    print("  SLATE Vendor Integration Status")
    print("=" * 60)
    print()

    summary = status["summary"]
    print(f"  Total: {summary['total']} | Available: {summary['available']} | Unavailable: {summary['unavailable']}")
    print()

    for vendor in status["vendors"]:
        name = vendor["name"]
        available = vendor.get("available", False)
        icon = "[OK]" if available else "[--]"
        print(f"  {icon} {name}")

        if available:
            if "version" in vendor:
                print(f"      Version: {vendor['version']}")
            if "types" in vendor:
                loaded = sum(1 for v in vendor["types"].values() if v)
                total = len(vendor["types"])
                print(f"      Types: {loaded}/{total} loaded")
            if "spec_count" in vendor:
                print(f"      Specs: {vendor['spec_count']} found")
        else:
            if "error" in vendor:
                print(f"      Error: {vendor['error']}")

        print()

    print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Vendor Integration Status")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--test", action="store_true", help="Run integration tests")
    args = parser.parse_args()

    if args.test:
        results = run_integration_tests()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("Integration Tests:")
            for test in results["tests"]:
                status = "PASS" if test["passed"] else "FAIL"
                print(f"  [{status}] {test['name']}: {test['test']}")
            print(f"\nSummary: {results['summary']['passed']}/{results['summary']['total']} passed")
    else:
        status = get_full_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print_status(status)


if __name__ == "__main__":
    main()
