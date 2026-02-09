#!/usr/bin/env python3
"""
SLATE Claude Agent SDK Integration

Provides SLATE-specific tools, hooks, and subagents for the Claude Agent SDK.
Based on https://platform.claude.com/docs/en/agent-sdk/overview

Usage:
    from slate.claude_agent_sdk_integration import (
        create_slate_tools,
        create_slate_hooks,
        get_slate_agent_options,
        SLATE_SUBAGENTS
    )
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate.action_guard import ActionGuard


# ============================================================================
# SLATE Custom Tools (SDK MCP Servers)
# ============================================================================

def tool(name: str, description: str, input_schema: Dict[str, Any]):
    """Decorator for defining custom tools as SDK MCP server functions."""
    def decorator(func: Callable):
        func._tool_name = name
        func._tool_description = description
        func._tool_input_schema = input_schema
        return func
    return decorator


@tool(
    "slate_status",
    "Check SLATE system status including GPU, services, and runtime health",
    {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["quick", "full", "json"],
                "description": "Output format: quick (summary), full (detailed), json (machine-readable)"
            }
        }
    }
)
async def slate_status_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check SLATE system status."""
    format_type = args.get("format", "quick")

    try:
        from slate.slate_status import SlateStatus
        status = SlateStatus()

        if format_type == "json":
            result = status.to_json()
        elif format_type == "full":
            result = status.full_report()
        else:
            result = status.quick_report()

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error checking status: {e}"}]}


@tool(
    "slate_workflow",
    "Manage SLATE task workflow queue - view, cleanup, or enforce rules",
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "cleanup", "enforce"],
                "description": "Action: status (view queue), cleanup (fix stale tasks), enforce (check rules)"
            }
        }
    }
)
async def slate_workflow_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Manage SLATE workflow queue."""
    action = args.get("action", "status")

    try:
        from slate.slate_workflow_manager import WorkflowManager
        manager = WorkflowManager()

        if action == "cleanup":
            result = manager.cleanup()
        elif action == "enforce":
            result = manager.enforce_rules()
        else:
            result = manager.status_report()

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error with workflow: {e}"}]}


@tool(
    "slate_gpu",
    "Manage dual-GPU load balancing for Ollama LLMs",
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "configure", "preload"],
                "description": "Action: status (GPU info), configure (setup dual-GPU), preload (warm models)"
            }
        }
    }
)
async def slate_gpu_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Manage SLATE GPU configuration."""
    action = args.get("action", "status")

    try:
        from slate.slate_gpu_manager import GPUManager
        manager = GPUManager()

        if action == "configure":
            result = manager.configure()
        elif action == "preload":
            result = manager.preload_models()
        else:
            result = manager.status()

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error with GPU: {e}"}]}


@tool(
    "slate_orchestrator",
    "Control SLATE orchestrator - start, stop, or check service status",
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "stop", "status"],
                "description": "Action to perform on the orchestrator"
            }
        },
        "required": ["action"]
    }
)
async def slate_orchestrator_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Control SLATE orchestrator."""
    action = args.get("action", "status")

    try:
        from slate.slate_orchestrator import Orchestrator
        orch = Orchestrator()

        if action == "start":
            result = orch.start()
        elif action == "stop":
            result = orch.stop()
        else:
            result = orch.status()

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error with orchestrator: {e}"}]}


@tool(
    "slate_ai",
    "Execute AI tasks using SLATE's unified backend (routes to free local LLMs)",
    {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The AI task to execute"
            },
            "check_status": {
                "type": "boolean",
                "description": "If true, check backend status instead of executing task"
            }
        }
    }
)
async def slate_ai_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute AI tasks via SLATE backend."""
    task = args.get("task", "")
    check_status = args.get("check_status", False)

    try:
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()

        if check_status:
            result = backend.status()
        else:
            result = await backend.execute(task)

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error with AI backend: {e}"}]}


@tool(
    "slate_k8s",
    "Deploy and manage SLATE on Kubernetes",
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "deploy", "teardown", "logs"],
                "description": "K8s action to perform"
            },
            "service": {
                "type": "string",
                "description": "Specific service to target (optional)"
            }
        }
    }
)
async def slate_k8s_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Manage SLATE K8s deployment."""
    action = args.get("action", "status")
    service = args.get("service")

    try:
        from slate.slate_k8s_deploy import K8sDeployer
        deployer = K8sDeployer()

        if action == "deploy":
            result = deployer.deploy()
        elif action == "teardown":
            result = deployer.teardown()
        elif action == "logs" and service:
            result = deployer.get_logs(service)
        else:
            result = deployer.status()

        return {"content": [{"type": "text", "text": result}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error with K8s: {e}"}]}


# All SLATE tools
SLATE_TOOLS = [
    slate_status_tool,
    slate_workflow_tool,
    slate_gpu_tool,
    slate_orchestrator_tool,
    slate_ai_tool,
    slate_k8s_tool,
]


def create_slate_tools():
    """
    Create SLATE tools as an SDK MCP server.

    Usage with Claude Agent SDK:
        from claude_agent_sdk import create_sdk_mcp_server, ClaudeAgentOptions
        from slate.claude_agent_sdk_integration import create_slate_tools, SLATE_TOOLS

        slate_server = create_sdk_mcp_server(
            name="slate",
            version="5.1.0",
            tools=SLATE_TOOLS
        )

        options = ClaudeAgentOptions(
            mcp_servers={"slate": slate_server},
            allowed_tools=["mcp__slate__*"]
        )
    """
    return SLATE_TOOLS


# ============================================================================
# SLATE Hooks (ActionGuard Integration)
# ============================================================================

class SlateHooks:
    """SLATE hooks for Claude Agent SDK integration."""

    def __init__(self):
        self.action_guard = ActionGuard()
        self.audit_log = WORKSPACE_ROOT / ".slate_audit" / "claude_agent.log"
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

    async def pre_tool_use_bash(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate Bash commands through ActionGuard before execution.

        Returns:
            Empty dict to allow, or hookSpecificOutput with deny to block.
        """
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name != "Bash":
            return {}

        command = tool_input.get("command", "")

        # Validate through ActionGuard
        result = self.action_guard.validate_command(command)

        if not result.allowed:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"ActionGuard blocked: {result.reason}",
                }
            }

        return {}

    async def pre_tool_use_write(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate file write operations through ActionGuard.
        """
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name not in ["Write", "Edit"]:
            return {}

        file_path = tool_input.get("file_path", "")

        # Validate through ActionGuard
        result = self.action_guard.validate_file_path(file_path)

        if not result.allowed:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"ActionGuard blocked: {result.reason}",
                }
            }

        return {}

    async def post_tool_use_audit(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log tool executions for audit trail.
        """
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_use_id": tool_use_id,
            "tool_name": tool_name,
            "tool_input_summary": str(tool_input)[:200],
        }

        try:
            with open(self.audit_log, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Non-critical, don't fail

        return {}

    async def user_prompt_scan(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scan user prompts for PII/credentials.
        """
        prompt = input_data.get("prompt", "")

        # Check for credential patterns in prompt
        pii_patterns = [
            r'api[_-]?key\s*[:=]\s*[\'"]?[\w-]+',
            r'password\s*[:=]\s*[\'"]?[\w-]+',
            r'secret\s*[:=]\s*[\'"]?[\w-]+',
            r'token\s*[:=]\s*[\'"]?[\w-]+',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style keys
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        ]

        import re
        for pattern in pii_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": "Potential credential/secret detected in prompt. Continue?",
                    }
                }

        return {}


def create_slate_hooks():
    """
    Create SLATE hooks for Claude Agent SDK.

    Usage:
        from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
        from slate.claude_agent_sdk_integration import create_slate_hooks

        hooks = create_slate_hooks()

        options = ClaudeAgentOptions(
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[hooks.pre_tool_use_bash]),
                    HookMatcher(matcher="Write|Edit", hooks=[hooks.pre_tool_use_write]),
                ],
                "PostToolUse": [
                    HookMatcher(matcher=".*", hooks=[hooks.post_tool_use_audit]),
                ],
                "UserPromptSubmit": [
                    HookMatcher(matcher=".*", hooks=[hooks.user_prompt_scan]),
                ],
            }
        )
    """
    return SlateHooks()


# ============================================================================
# SLATE Subagents
# ============================================================================

SLATE_SUBAGENTS = {
    "slate-operator": {
        "description": "SLATE system operator for infrastructure management, deployments, and service health.",
        "prompt": """You are the SLATE Operator agent. Your role is to:
1. Monitor and manage SLATE infrastructure
2. Deploy and maintain K8s/Docker services
3. Handle GPU configuration and model placement
4. Execute DIAGNOSE -> ACT -> VERIFY pattern

Always use SLATE MCP tools (slate_status, slate_workflow, slate_gpu, etc.) for operations.
Report results clearly with service status and any issues found.""",
        "tools": [
            "mcp__slate__slate_status",
            "mcp__slate__slate_workflow",
            "mcp__slate__slate_orchestrator",
            "mcp__slate__slate_gpu",
            "mcp__slate__slate_k8s",
            "Bash",
            "Read",
            "Glob",
        ],
    },

    "slate-code-reviewer": {
        "description": "Expert code reviewer for SLATE codebase quality and security reviews.",
        "prompt": """You are the SLATE Code Reviewer. Your role is to:
1. Analyze code quality and suggest improvements
2. Check for security vulnerabilities (OWASP Top 10)
3. Verify ActionGuard patterns are not bypassed
4. Ensure PII protection is maintained

Focus on the slate/ and slate_core/ directories. Use Grep to find patterns.""",
        "tools": ["Read", "Glob", "Grep"],
    },

    "slate-test-runner": {
        "description": "Test execution agent for running SLATE test suites.",
        "prompt": """You are the SLATE Test Runner. Your role is to:
1. Run pytest tests in the tests/ directory
2. Analyze test failures and suggest fixes
3. Check test coverage for slate/ modules
4. Report test results clearly

Use pytest with -v flag for verbose output.""",
        "tools": ["Bash", "Read", "Glob"],
    },

    "slate-docs-generator": {
        "description": "Documentation generator for SLATE codebase.",
        "prompt": """You are the SLATE Documentation Generator. Your role is to:
1. Analyze code and generate documentation
2. Update CLAUDE.md with new features
3. Create API reference for MCP tools
4. Maintain specs/ documentation

Only update documentation files, never modify code.""",
        "tools": ["Read", "Write", "Glob", "Grep"],
    },
}


# ============================================================================
# SLATE Agent Options Builder
# ============================================================================

def get_slate_agent_options(
    mode: str = "operator",
    allowed_tools: Optional[List[str]] = None,
    extra_mcp_servers: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get Claude Agent SDK options configured for SLATE.

    Args:
        mode: Operation mode - "operator" (full access), "readonly" (no writes), "minimal" (status only)
        allowed_tools: Override default tool list
        extra_mcp_servers: Additional MCP servers to include

    Returns:
        Dict suitable for ClaudeAgentOptions

    Usage:
        from claude_agent_sdk import query, ClaudeAgentOptions
        from slate.claude_agent_sdk_integration import get_slate_agent_options

        options = ClaudeAgentOptions(**get_slate_agent_options(mode="operator"))

        async for message in query(prompt="Check SLATE status", options=options):
            print(message)
    """
    hooks = create_slate_hooks()

    # Default tools by mode
    default_tools = {
        "operator": [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
            "WebSearch", "WebFetch", "Task", "TodoWrite",
            "mcp__slate__*",
        ],
        "readonly": [
            "Read", "Glob", "Grep",
            "mcp__slate__slate_status",
            "mcp__slate__slate_workflow",
        ],
        "minimal": [
            "mcp__slate__slate_status",
        ],
    }

    tools = allowed_tools or default_tools.get(mode, default_tools["operator"])

    # Build MCP servers config
    mcp_servers = {
        "slate": {
            "command": str(WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"),
            "args": [str(WORKSPACE_ROOT / "slate" / "mcp_server.py")],
            "env": {
                "SLATE_WORKSPACE": str(WORKSPACE_ROOT),
                "PYTHONPATH": str(WORKSPACE_ROOT),
                "SLATE_BEHAVIOR": "operator",
                "SLATE_ACTIONGUARD": "enabled",
            }
        }
    }

    if extra_mcp_servers:
        mcp_servers.update(extra_mcp_servers)

    # Build hooks config
    hooks_config = {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [hooks.pre_tool_use_bash]},
            {"matcher": "Write|Edit", "hooks": [hooks.pre_tool_use_write]},
        ],
        "PostToolUse": [
            {"matcher": "Bash|Write|Edit", "hooks": [hooks.post_tool_use_audit]},
        ],
    }

    if mode == "operator":
        hooks_config["UserPromptSubmit"] = [
            {"matcher": ".*", "hooks": [hooks.user_prompt_scan]},
        ]

    return {
        "allowed_tools": tools,
        "permission_mode": "bypassPermissions" if mode == "operator" else "default",
        "mcp_servers": mcp_servers,
        "hooks": hooks_config,
        "agents": SLATE_SUBAGENTS,
        "cwd": str(WORKSPACE_ROOT),
        "system_prompt": f"""You are operating in SLATE mode: {mode}

SLATE (Synchronized Living Architecture for Transformation and Evolution) is an AI-powered development system with:
- Dual RTX 5070 Ti GPUs for local LLM inference
- K8s-first container runtime
- ActionGuard security validation
- GitHub Actions workflow integration

Follow the DIAGNOSE -> ACT -> VERIFY pattern for all operations.
Use SLATE MCP tools (slate_*) for system management.
""",
    }


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI interface for testing SLATE Agent SDK integration."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Claude Agent SDK Integration")
    parser.add_argument("--list-tools", action="store_true", help="List available SLATE tools")
    parser.add_argument("--list-agents", action="store_true", help="List available SLATE subagents")
    parser.add_argument("--show-options", action="store_true", help="Show agent options for a mode")
    parser.add_argument("--mode", default="operator", help="Mode: operator, readonly, minimal")
    parser.add_argument("--test", action="store_true", help="Run integration test")

    args = parser.parse_args()

    if args.list_tools:
        print("SLATE Custom Tools:")
        print("=" * 50)
        for tool_func in SLATE_TOOLS:
            print(f"  {tool_func._tool_name}")
            print(f"    {tool_func._tool_description}")
            print()

    elif args.list_agents:
        print("SLATE Subagents:")
        print("=" * 50)
        for name, config in SLATE_SUBAGENTS.items():
            print(f"  {name}")
            print(f"    {config['description']}")
            print(f"    Tools: {', '.join(config['tools'][:3])}...")
            print()

    elif args.show_options:
        options = get_slate_agent_options(mode=args.mode)
        print(f"SLATE Agent Options (mode={args.mode}):")
        print("=" * 50)
        print(json.dumps({
            "allowed_tools": options["allowed_tools"],
            "permission_mode": options["permission_mode"],
            "mcp_servers": list(options["mcp_servers"].keys()),
            "agents": list(options["agents"].keys()),
        }, indent=2))

    elif args.test:
        print("Testing SLATE Agent SDK Integration...")
        print("=" * 50)

        # Test ActionGuard hook
        hooks = create_slate_hooks()

        # Test allowed command
        result = await hooks.pre_tool_use_bash(
            {"tool_name": "Bash", "tool_input": {"command": "python --version"}},
            "test-1",
            {}
        )
        print(f"Test 'python --version': {'ALLOWED' if not result else 'BLOCKED'}")

        # Test blocked command
        result = await hooks.pre_tool_use_bash(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},
            "test-2",
            {}
        )
        print(f"Test 'rm -rf /': {'BLOCKED' if result else 'ALLOWED (ERROR!)'}")

        print("\nIntegration test complete.")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
