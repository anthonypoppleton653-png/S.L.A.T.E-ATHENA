# Specification: Claude Agent SDK Integration

**Spec ID**: 017-claude-agent-sdk
**Status**: complete
**Created**: 2026-02-08
**Author**: Claude Opus 4.5
**Depends On**: 007-slate-design-system, 011-schematic-diagram-sdk

## Overview

This specification defines the **Claude Agent SDK Integration** for SLATE, providing a comprehensive framework for programmatic interaction with Claude Code through the Agent SDK. The integration enables session management, tool registration, MCP protocol support, hook-based security through ActionGuard, and permission bypass with enterprise-grade security guarantees.

SLATE's Claude Agent SDK integration follows the principle of **secure by default, permissive by configuration** - all operations pass through ActionGuard validation before execution, enabling permission bypass without sacrificing security.

## Architecture

### High-Level System Architecture

```
+============================================================================+
|                         CLAUDE AGENT SDK INTEGRATION                        |
+============================================================================+
|                                                                             |
|  +-----------------+     +------------------+     +--------------------+    |
|  |  Claude Code    |     |  SLATE Hooks     |     |   SLATE Tools      |    |
|  |  (Host Agent)   |<--->|  (ActionGuard)   |<--->|   (MCP Server)     |    |
|  +-----------------+     +------------------+     +--------------------+    |
|          |                       |                        |                 |
|          v                       v                        v                 |
|  +-----------------+     +------------------+     +--------------------+    |
|  |  Session        |     |  PreToolUse      |     |  slate_status      |    |
|  |  Management     |     |  PostToolUse     |     |  slate_workflow    |    |
|  |                 |     |  UserPrompt      |     |  slate_gpu         |    |
|  +-----------------+     +------------------+     |  slate_orchestrator|    |
|          |                       |               |  slate_ai          |    |
|          v                       v               |  slate_k8s         |    |
|  +-----------------+     +------------------+     +--------------------+    |
|  |  Agent Options  |     |  Audit Trail     |                              |
|  |  Builder        |     |  (.slate_audit)  |                              |
|  +-----------------+     +------------------+                              |
|                                                                             |
+============================================================================+
```

### Component Relationships

```
                           SLATE WORKSPACE
                                 |
         +----------------------+----------------------+
         |                      |                      |
         v                      v                      v
   .claude/settings.json   .mcp.json        slate/claude_agent_sdk_integration.py
         |                      |                      |
         v                      v                      v
   +------------+         +------------+         +------------+
   | Behavior   |         | MCP Server |         | SDK Tools  |
   | Profile    |         | Config     |         | & Hooks    |
   +------------+         +------------+         +------------+
         |                      |                      |
         +----------------------+----------------------+
                                |
                                v
                    +------------------------+
                    |   ActionGuard          |
                    |   Security Layer       |
                    +------------------------+
                                |
                    +-----------+-----------+
                    |           |           |
                    v           v           v
              Bash Cmds    File Ops    K8s Manifests
```

## Core Components

### 1. Tool Registration System

SLATE tools are registered using a decorator-based system that provides metadata for the MCP protocol.

```python
def tool(name: str, description: str, input_schema: Dict[str, Any]):
    """Decorator for defining custom tools as SDK MCP server functions."""
    def decorator(func: Callable):
        func._tool_name = name
        func._tool_description = description
        func._tool_input_schema = input_schema
        return func
    return decorator
```

#### Registered SLATE Tools

| Tool | Description | Input Schema |
|------|-------------|--------------|
| `slate_status` | Check SLATE system status including GPU, services, and runtime health | `format: quick\|full\|json` |
| `slate_workflow` | Manage SLATE task workflow queue - view, cleanup, or enforce rules | `action: status\|cleanup\|enforce` |
| `slate_gpu` | Manage dual-GPU load balancing for Ollama LLMs | `action: status\|configure\|preload` |
| `slate_orchestrator` | Control SLATE orchestrator - start, stop, or check service status | `action: start\|stop\|status` |
| `slate_ai` | Execute AI tasks using SLATE's unified backend (routes to free local LLMs) | `task: string, check_status: boolean` |
| `slate_k8s` | Deploy and manage SLATE on Kubernetes | `action: status\|deploy\|teardown\|logs, service?: string` |

### 2. Hook System (ActionGuard Integration)

The hook system provides security validation at multiple points in the agent execution lifecycle.

```
                      HOOK LIFECYCLE
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    PreToolUse       PostToolUse      UserPromptSubmit
          |                |                |
          v                v                v
    +----------+     +-----------+    +------------+
    | Validate |     | Audit Log |    | PII Scan   |
    | Command  |     | Entry     |    | Detection  |
    +----------+     +-----------+    +------------+
          |                |                |
          v                v                v
    ActionGuard      .slate_audit/    Credential
    Decision         claude_agent.log  Warning
```

#### PreToolUse Hooks

**Bash Command Validation:**
```python
async def pre_tool_use_bash(
    self,
    input_data: Dict[str, Any],
    tool_use_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate Bash commands through ActionGuard before execution."""
    command = tool_input.get("command", "")
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
```

**File Write Validation:**
```python
async def pre_tool_use_write(
    self,
    input_data: Dict[str, Any],
    tool_use_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate file write operations through ActionGuard."""
    file_path = tool_input.get("file_path", "")
    result = self.action_guard.validate_file_path(file_path)
    # Returns deny if blocked, empty dict if allowed
```

#### PostToolUse Hooks

**Audit Trail Logging:**
```python
async def post_tool_use_audit(
    self,
    input_data: Dict[str, Any],
    tool_use_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Log tool executions for audit trail."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_use_id": tool_use_id,
        "tool_name": tool_name,
        "tool_input_summary": str(tool_input)[:200],
    }
    # Writes to .slate_audit/claude_agent.log
```

#### UserPromptSubmit Hooks

**PII/Credential Scanning:**
```python
async def user_prompt_scan(
    self,
    input_data: Dict[str, Any],
    tool_use_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Scan user prompts for PII/credentials."""
    pii_patterns = [
        r'api[_-]?key\s*[:=]\s*[\'"]?[\w-]+',
        r'password\s*[:=]\s*[\'"]?[\w-]+',
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style keys
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
    ]
    # Returns "ask" decision if credential detected
```

### 3. Subagent System

SLATE provides specialized subagents for different operational domains.

```
                    SLATE SUBAGENT HIERARCHY
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
+---------------+   +---------------+   +---------------+
| slate-operator|   | slate-code-   |   | slate-test-   |
|               |   | reviewer      |   | runner        |
| Infrastructure|   | Security Audit|   | Test Suite    |
| K8s/Docker    |   | Code Quality  |   | Coverage      |
+---------------+   +---------------+   +---------------+
        |                   |                   |
        v                   v                   v
   MCP Tools:          Read-Only:           Bash/Read:
   slate_*             Read, Glob, Grep     pytest
   Bash, Read, Glob
```

#### Subagent Definitions

| Agent | Purpose | Allowed Tools |
|-------|---------|---------------|
| `slate-operator` | Infrastructure management, deployments, service health | `mcp__slate__*`, `Bash`, `Read`, `Glob` |
| `slate-code-reviewer` | Code quality and security reviews | `Read`, `Glob`, `Grep` |
| `slate-test-runner` | Test execution and coverage analysis | `Bash`, `Read`, `Glob` |
| `slate-docs-generator` | Documentation generation and updates | `Read`, `Write`, `Glob`, `Grep` |

### 4. Agent Options Builder

The `get_slate_agent_options()` function provides a complete configuration builder for Claude Agent SDK sessions.

```python
def get_slate_agent_options(
    mode: str = "operator",           # operator | readonly | minimal
    allowed_tools: Optional[List[str]] = None,
    extra_mcp_servers: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get Claude Agent SDK options configured for SLATE."""
```

#### Operation Modes

| Mode | Permission Level | Tools Available |
|------|------------------|-----------------|
| `operator` | Full access with ActionGuard | All tools + MCP slate_* |
| `readonly` | Read-only operations | `Read`, `Glob`, `Grep`, `slate_status`, `slate_workflow` |
| `minimal` | Status only | `slate_status` |

#### Options Structure

```python
{
    "allowed_tools": [...],
    "permission_mode": "bypassPermissions" | "default",
    "mcp_servers": {
        "slate": {
            "command": ".venv/Scripts/python.exe",
            "args": ["slate/mcp_server.py"],
            "env": {
                "SLATE_WORKSPACE": "...",
                "SLATE_BEHAVIOR": "operator",
                "SLATE_ACTIONGUARD": "enabled"
            }
        }
    },
    "hooks": {
        "PreToolUse": [...],
        "PostToolUse": [...],
        "UserPromptSubmit": [...]
    },
    "agents": {...},  # Subagent definitions
    "cwd": "...",
    "system_prompt": "..."
}
```

## Session Management

### Session Lifecycle

```
                    SESSION LIFECYCLE
                          |
    +---------------------+---------------------+
    |                     |                     |
    v                     v                     v
+--------+          +---------+          +---------+
| CREATE |    -->   | ACTIVE  |    -->   | CLOSE   |
|        |          |         |          |         |
| Options|          | Execute |          | Audit   |
| Hooks  |          | Tools   |          | Cleanup |
| MCP    |          | Subagent|          |         |
+--------+          +---------+          +---------+
```

### Programmatic Session Creation

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from slate.claude_agent_sdk_integration import get_slate_agent_options

# Create options for SLATE operator mode
options = ClaudeAgentOptions(**get_slate_agent_options(mode="operator"))

# Execute queries
async for message in query(prompt="Check SLATE status", options=options):
    print(message)
```

### Hook Registration

```python
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
```

## MCP Server Integration

### Server Configuration

The SLATE MCP server is configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "slate": {
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": ["slate/mcp_server.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "SLATE_BEHAVIOR": "operator",
        "SLATE_ACTIONGUARD": "enabled"
      }
    }
  }
}
```

### Tool Naming Convention

MCP tools follow the pattern: `mcp__<server>__<tool_name>`

```
mcp__slate__slate_status       # Status check
mcp__slate__slate_workflow     # Workflow management
mcp__slate__slate_gpu          # GPU management
mcp__slate__slate_orchestrator # Service control
mcp__slate__slate_ai           # AI task execution
mcp__slate__slate_k8s          # K8s deployment
```

### Server Protocol Flow

```
Claude Code                    MCP Server                    SLATE Backend
    |                              |                              |
    |  tools/list                  |                              |
    |----------------------------->|                              |
    |                              |                              |
    |  {tools: [...]}              |                              |
    |<-----------------------------|                              |
    |                              |                              |
    |  tools/call: slate_status    |                              |
    |----------------------------->|                              |
    |                              |  SlateStatus()               |
    |                              |----------------------------->|
    |                              |                              |
    |                              |  {gpu: ..., services: ...}   |
    |                              |<-----------------------------|
    |                              |                              |
    |  {content: [{type: "text"}]} |                              |
    |<-----------------------------|                              |
```

## Permission Bypass with Security

### Security Model

```
+===========================================================================+
|                    PERMISSION BYPASS SECURITY MODEL                        |
+===========================================================================+
|                                                                            |
|  USER REQUEST                                                              |
|       |                                                                    |
|       v                                                                    |
|  +--------------------+     +--------------------+                         |
|  | Claude Code Agent  |---->| PreToolUse Hook    |                         |
|  +--------------------+     +--------------------+                         |
|                                    |                                       |
|                                    v                                       |
|                             +-------------+                                |
|                             | ActionGuard |                                |
|                             +-------------+                                |
|                                    |                                       |
|                    +---------------+---------------+                       |
|                    |               |               |                       |
|                    v               v               v                       |
|              +----------+   +----------+   +-----------+                   |
|              | ALLOWED  |   | BLOCKED  |   | ASK USER  |                   |
|              +----------+   +----------+   +-----------+                   |
|                    |               |               |                       |
|                    v               |               v                       |
|              +----------+          |        +----------+                   |
|              | EXECUTE  |          |        | PROMPT   |                   |
|              +----------+          |        +----------+                   |
|                    |               |               |                       |
|                    v               v               v                       |
|              +----------------------------------------+                    |
|              |            AUDIT LOG                   |                    |
|              +----------------------------------------+                    |
|                                                                            |
+===========================================================================+
```

### ActionGuard Rules

| Category | Blocked Patterns | Reason |
|----------|------------------|--------|
| Code Injection | `eval(`, `exec(os`, `__import__(` | Prevent arbitrary code execution |
| Destructive | `rm -rf /`, `subprocess.call.*shell=True` | Prevent system damage |
| Network Binding | `0.0.0.0` | Force localhost-only binding |
| External APIs | `api.openai.com`, `api.anthropic.com` | Enforce local-first policy |
| K8s Privilege | `privileged: true`, `hostNetwork: true` | Prevent container escape |

### Settings Configuration

The `.claude/settings.json` enables permission bypass with ActionGuard:

```json
{
  "behavior": {
    "profile": "slate-operator",
    "description": "SLATE System Operator with permission bypass and ActionGuard security"
  },
  "permissions": {
    "mode": "bypassWithActionGuard",
    "actionGuardEnabled": true,
    "confirmDestructive": false,
    "confirmExternal": false,
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "mcp__slate__*(*)"
    ]
  }
}
```

## Vendor SDK Integration

### OpenAI Agents SDK Integration

SLATE integrates with the vendored `openai-agents-python` SDK for proper Agent, InputGuardrail, and Handoff definitions.

```python
from slate.vendor_agents_sdk import (
    Agent as SDKAgent,
    function_tool as sdk_function_tool,
    InputGuardrail as SDKInputGuardrail,
    Handoff as SDKHandoff,
    handoff as sdk_handoff,
    SDK_AVAILABLE as AGENTS_SDK_AVAILABLE,
)
```

#### ActionGuardInputGuardrail

```python
class ActionGuardInputGuardrail:
    """InputGuardrail that wraps SLATE's ActionGuard for the openai-agents SDK."""

    def __init__(self):
        self.action_guard = ActionGuard()

    async def check(self, input_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """Validate input through ActionGuard."""
        text = json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)
        result = self.action_guard.validate_command(text)
        if not result.allowed:
            return {"blocked": True, "reason": f"ActionGuard: {result.reason}"}
        return {}
```

#### SDK Agent Creation

```python
def get_sdk_agents() -> Dict[str, Any]:
    """Create proper Agent objects from the vendor openai-agents-python SDK."""
    guardrail = _create_sdk_action_guard_guardrail()

    operator_agent = SDKAgent(
        name="slate_operator",
        instructions="...",
        handoffs=[
            sdk_handoff(docs_agent),
            sdk_handoff(test_agent),
            sdk_handoff(reviewer_agent),
        ],
        input_guardrails=[guardrail] if guardrail else [],
    )
    return {"slate-operator": operator_agent, ...}
```

### AutoGen SDK Integration

SLATE also integrates with Microsoft AutoGen for multi-agent conversations:

```python
from slate.vendor_autogen_sdk import (
    Agent as AutoGenAgent,
    BaseAgent as AutoGenBaseAgent,
    AgentRuntime as AutoGenRuntime,
    ClosureAgent as AutoGenClosureAgent,
    MessageContext as AutoGenMessageContext,
    SDK_AVAILABLE as AUTOGEN_SDK_AVAILABLE,
)
```

## CLI Interface

### Available Commands

```bash
# List available SLATE tools
python slate/claude_agent_sdk_integration.py --list-tools

# List available subagents
python slate/claude_agent_sdk_integration.py --list-agents

# Show agent options for a mode
python slate/claude_agent_sdk_integration.py --show-options --mode operator

# Run integration test
python slate/claude_agent_sdk_integration.py --test
```

### Example Output

```
SLATE Custom Tools:
==================================================
  slate_status
    Check SLATE system status including GPU, services, and runtime health

  slate_workflow
    Manage SLATE task workflow queue - view, cleanup, or enforce rules

  slate_gpu
    Manage dual-GPU load balancing for Ollama LLMs

  slate_orchestrator
    Control SLATE orchestrator - start, stop, or check service status

  slate_ai
    Execute AI tasks using SLATE's unified backend (routes to free local LLMs)

  slate_k8s
    Deploy and manage SLATE on Kubernetes
```

## Implementation Files

### Core Files

| File | Purpose |
|------|---------|
| `slate/claude_agent_sdk_integration.py` | Main SDK integration module |
| `slate/action_guard.py` | Security validation layer |
| `slate/mcp_server.py` | MCP protocol server implementation |
| `.claude/settings.json` | Claude Code configuration |
| `.claude/settings.local.json` | Permission override settings |
| `.mcp.json` | MCP server configuration |

### Behavior Files

| File | Purpose |
|------|---------|
| `.claude/behaviors/slate-operator.md` | Operator behavior profile |
| `.claude/behaviors/slate-protocols.md` | Protocol definitions (P001-P010) |
| `.claude/hooks.json` | Hook configuration |

### Audit Files

| File | Purpose |
|------|---------|
| `.slate_audit/claude_agent.log` | Tool execution audit trail |
| `.slate_audit/actionguard.log` | ActionGuard decision log |

## Data Flow Diagram

```
                        COMPLETE DATA FLOW
                              |
+-----------------------------+-----------------------------+
|                             |                             |
v                             v                             v
USER PROMPT              MCP TOOL CALL                 SUBAGENT CALL
    |                         |                             |
    v                         v                             v
UserPromptSubmit         PreToolUse                   PreToolUse
Hook (PII Scan)          Hook (ActionGuard)           Hook (ActionGuard)
    |                         |                             |
    |     +-------------------+                             |
    |     |                                                 |
    v     v                                                 v
+---------------+                                   +---------------+
| Claude Code   |                                   | Subagent      |
| Session       |                                   | Execution     |
+---------------+                                   +---------------+
    |     |                                                 |
    |     +-------------------+                             |
    |                         |                             |
    v                         v                             v
PostToolUse              PostToolUse                  PostToolUse
Hook (Audit)             Hook (Audit)                 Hook (Audit)
    |                         |                             |
    +-------------------------+-----------------------------+
                              |
                              v
                    +-------------------+
                    | .slate_audit/     |
                    | claude_agent.log  |
                    +-------------------+
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Hook Latency | < 10ms | Time from hook trigger to decision |
| ActionGuard Accuracy | 100% | No blocked patterns executed |
| Tool Registration | 6 tools | All SLATE tools registered |
| Subagent Coverage | 4 agents | All domains covered |
| Audit Completeness | 100% | All tool executions logged |

## Security Considerations

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Command injection | ActionGuard pattern matching |
| Credential exposure | PII scanner in UserPromptSubmit |
| Network escape | 0.0.0.0 binding blocked |
| Privilege escalation | K8s security patterns |
| Unauthorized API calls | Domain blocklist |

### Audit Requirements

1. All tool executions logged with timestamp, tool_use_id, and input summary
2. ActionGuard decisions logged with pattern matched and decision reason
3. PII scan detections logged with redacted pattern
4. Session lifecycle events (create, close) logged

## Theme Lock Declaration

```
+---------------------------------------------------------------+
|            CLAUDE AGENT SDK SPECIFICATION LOCK                 |
+---------------------------------------------------------------+
|                                                               |
|  Version: 1.0.0                                               |
|  Status: LOCKED                                               |
|  Date: 2026-02-08                                             |
|                                                               |
|  The following are immutable:                                 |
|  - Hook event names (PreToolUse, PostToolUse, UserPrompt)     |
|  - ActionGuard blocked patterns                               |
|  - Tool input schema structures                               |
|  - Permission mode values                                     |
|  - Audit log format                                           |
|                                                               |
|  Additive improvements only. No breaking changes.             |
|                                                               |
+---------------------------------------------------------------+
```

## References

- **Claude Agent SDK Documentation**: https://docs.anthropic.com/claude-code/sdk
- **MCP Protocol Specification**: https://modelcontextprotocol.io/
- **SLATE ActionGuard**: `slate/action_guard.py`
- **SLATE MCP Server**: `slate/mcp_server.py`
- **OpenAI Agents SDK**: `vendor/openai-agents-python/`
- **Microsoft AutoGen**: `vendor/autogen/`
