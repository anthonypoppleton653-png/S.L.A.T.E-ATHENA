# Claude Code Integration
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Initial creation of Claude Code integration documentation -->

SLATE provides deep integration with Claude Code through MCP servers, slash commands, hooks, and the Claude Agent SDK. This page documents all integration points and provides practical examples.

## Overview

SLATE integrates with Claude Code at multiple levels:

| Integration Layer | Purpose | Key Files |
|-------------------|---------|-----------|
| **MCP Server** | Exposes SLATE tools to Claude Code | `slate/mcp_server.py`, `.mcp.json` |
| **Slash Commands** | Quick access to SLATE operations | `.claude/commands/*.md` |
| **Plugin System** | Package commands, skills, hooks together | `.claude-plugin/plugin.json` |
| **Hooks** | ActionGuard security validation | `.claude/hooks.json` |
| **Agent SDK** | Programmatic automation | `slate/claude_agent_sdk_integration.py` |
| **Behavior Profile** | Permission bypass with security | `.claude/behaviors/slate-operator.md` |

```
Claude Code ─────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ /slate      │  │ MCP Tools   │  │ Hooks       │  │ Agent SDK   │  │
│  │ Commands    │  │ slate_*     │  │ ActionGuard │  │ Subagents   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │                │         │
│         └────────────────┴────────────────┴────────────────┘         │
│                                   │                                   │
│                          ┌────────▼────────┐                         │
│                          │  SLATE Engine   │                         │
│                          │  (Python)       │                         │
│                          └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────────-┘
```

---

## MCP Server Setup

### Configuration

SLATE's MCP server is configured in `.mcp.json`:

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
      },
      "description": "SLATE MCP Server - AI orchestration, workflow management, GPU, K8s deployment"
    }
  }
}
```

### Starting the MCP Server

The MCP server starts automatically when Claude Code loads the SLATE workspace. To manually test:

```powershell
# Test MCP server
.\.venv\Scripts\python.exe slate/mcp_server.py
```

### Verifying MCP Connection

```powershell
# Validate MCP configuration
.\.venv\Scripts\python.exe slate/claude_code_manager.py --test-mcp slate
```

---

## Available MCP Tools

SLATE provides 12 MCP tools accessible as `mcp__slate__<tool_name>`:

### System Management

| Tool | Description | Actions |
|------|-------------|---------|
| `slate_status` | Check all services and GPU status | `quick`, `json`, `full` |
| `slate_orchestrator` | Start/stop SLATE services | `start`, `stop`, `status` |
| `slate_runtime` | Check runtime integrations | `text`, `json` |

### Workflow & Tasks

| Tool | Description | Actions |
|------|-------------|---------|
| `slate_workflow` | Manage task workflow queue | `status`, `cleanup`, `enforce` |
| `slate_runner` | Manage GitHub Actions runner | `status`, `setup`, `dispatch` |

### AI & GPU

| Tool | Description | Actions |
|------|-------------|---------|
| `slate_ai` | Execute AI tasks via local LLMs | task execution, status check |
| `slate_gpu` | Manage dual-GPU load balancing | `status`, `configure`, `preload` |
| `slate_hardware` | Detect and optimize GPU hardware | `detect`, `optimize`, `install-pytorch` |
| `slate_benchmark` | Run performance benchmarks | (no args) |

### Development Tools

| Tool | Description | Actions |
|------|-------------|---------|
| `slate_claude_code` | Validate Claude Code configuration | `validate`, `report`, `status`, `agent-options` |
| `slate_spec_kit` | Process specs and generate wiki | `status`, `process-all`, `wiki`, `analyze` |
| `slate_schematic` | Generate system diagrams | `from-system`, `from-tech-tree`, `components` |

### Tool Input Schemas

Each tool has a defined input schema. Example for `slate_status`:

```json
{
  "type": "object",
  "properties": {
    "format": {
      "type": "string",
      "enum": ["quick", "json", "full"],
      "description": "Output format",
      "default": "quick"
    }
  }
}
```

### Using MCP Tools in Conversation

```
User: Check SLATE status
Claude: [Uses mcp__slate__slate_status with format="quick"]

User: Clean up stale tasks
Claude: [Uses mcp__slate__slate_workflow with action="cleanup"]

User: Configure GPUs for Ollama
Claude: [Uses mcp__slate__slate_gpu with action="configure"]
```

---

## Slash Commands

SLATE provides slash commands for quick operations:

### Core Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/slate` | Manage orchestrator | `/slate [start\|stop\|status\|restart\|runner\|costs]` |
| `/slate-status` | Check system status | `/slate-status [--quick\|--json\|--full]` |
| `/slate-workflow` | Manage task queue | `/slate-workflow [--status\|--cleanup\|--enforce]` |
| `/slate-runner` | Manage GitHub runner | `/slate-runner [--status\|--setup\|--dispatch]` |
| `/slate-gpu` | Manage GPU configuration | `/slate-gpu [status\|configure\|preload\|balance]` |
| `/slate-help` | Show all commands | `/slate-help` |

### Development Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/slate-claude` | Validate Claude Code | `/slate-claude [validate\|report\|status]` |
| `/slate-spec-kit` | Process specifications | `/slate-spec-kit [--status\|--process-all\|--wiki\|--analyze]` |
| `/slate-schematic` | Generate diagrams | `/slate-schematic [from-system\|from-tech-tree\|components]` |
| `/slate-discussions` | Manage GitHub Discussions | `/slate-discussions [--status\|--unanswered\|--sync-tasks]` |
| `/slate-multirunner` | Multi-runner system | `/slate-multirunner [--status\|--add\|--remove]` |
| `/slate-diagnose` | Diagnose issues | `/slate-diagnose` |

### Spec-Kit Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/speckit:specify` | Create specification | `/speckit:specify <topic>` |
| `/speckit:plan` | Generate implementation plan | `/speckit:plan <spec>` |
| `/speckit:tasks` | Generate tasks from spec | `/speckit:tasks <spec>` |
| `/speckit:implement` | Implement a spec | `/speckit:implement <spec>` |
| `/speckit:constitution` | Show constitution | `/speckit:constitution` |
| `/speckit:clarify` | Clarify spec questions | `/speckit:clarify <spec>` |
| `/speckit:analyze` | Analyze spec | `/speckit:analyze <spec>` |
| `/speckit:checklist` | Show spec checklist | `/speckit:checklist <spec>` |

### Command Examples

```bash
# Start SLATE services
/slate start

# Check system status (quick view)
/slate-status

# Clean up stale tasks in workflow queue
/slate-workflow --cleanup

# Check GitHub runner configuration
/slate-runner --status

# Validate Claude Code integration
/slate-claude validate

# Generate system architecture diagram
/slate-schematic from-system
```

---

## Plugin System

SLATE is packaged as a Claude Code plugin that bundles commands, skills, hooks, and MCP servers.

### Plugin Structure

```
.claude-plugin/
├── plugin.json         # Plugin manifest
└── marketplace.json    # Distribution catalog

.claude/
├── commands/           # Slash commands
├── hooks.json          # ActionGuard hooks
├── settings.json       # Configuration
├── settings.local.json # Permission overrides
└── behaviors/          # Behavior profiles
    ├── slate-operator.md
    └── slate-protocols.md

skills/                 # Agent skills (skills/*/SKILL.md)
.mcp.json              # MCP server configuration
```

### Plugin Manifest (`plugin.json`)

```json
{
  "name": "slate",
  "version": "5.3.0",
  "description": "S.L.A.T.E. - AI agent orchestration with GPU support",
  "author": {
    "name": "SynchronizedLivingArchitecture",
    "url": "https://github.com/SynchronizedLivingArchitecture"
  },
  "repository": "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E",
  "license": "EOSL-1.0",
  "keywords": ["slate", "ai", "agents", "kubernetes", "gpu", "llm", "ollama", "mcp"],
  "commands": "./.claude/commands/",
  "skills": "./skills/",
  "hooks": "./.claude/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

### Plugin Scopes

| Plugin Type | Scope | How It Loads |
|-------------|-------|--------------|
| Local (`.claude-plugin/` exists) | Project | Auto-loads when `cd` into workspace |
| Marketplace (`/plugin install`) | User | Must explicitly enable |

**Important**: Do not mix scopes. If you have a local `.claude-plugin/` directory, don't also enable it as a marketplace plugin.

### Installation Methods

**Local (Recommended for Development)**:
```bash
# Plugin auto-loads when working in SLATE workspace
cd /path/to/S.L.A.T.E
claude  # Plugin loads at project scope
```

**From GitHub Marketplace**:
```bash
# Add marketplace (one-time)
/plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E

# Install
/plugin install slate@slate-marketplace
```

**Development Mode**:
```bash
claude --plugin-dir /path/to/S.L.A.T.E
```

---

## CLAUDE.md Configuration

SLATE's `CLAUDE.md` file provides comprehensive instructions for Claude Code. Key sections:

### Active Technologies
```markdown
- Python 3.11+ (backend)
- FastAPI (dashboard on port 8080)
- Ollama (local LLM on port 11434)
- Foundry Local (ONNX inference on port 5272)
- ChromaDB (vector store for RAG)
```

### MCP Tools Reference
Lists all available MCP tools with descriptions.

### Security Architecture
Documents ActionGuard, SDK Source Guard, and PII Scanner.

### Code Style
Defines conventions for Python, imports, and task files.

### Quick Reference
Common commands for system management.

---

## Hook Integration with ActionGuard

SLATE uses hooks to validate actions through ActionGuard before execution.

### Hook Configuration (`.claude/hooks.json`)

```json
{
  "$schema": "https://claude.ai/schemas/hooks.json",
  "description": "SLATE ActionGuard-integrated hooks for Claude Code",
  "version": "1.0.1",

  "hooks": {
    "PreToolUse": [
      {
        "name": "slate-actionguard-bash",
        "description": "Validate Bash commands through SLATE ActionGuard",
        "matcher": {
          "tool": "Bash"
        },
        "command": "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe ${CLAUDE_PLUGIN_ROOT}/slate/action_guard.py --validate-bash \"$TOOL_INPUT_command\"",
        "timeout": 5000,
        "onError": "allow",
        "onBlock": {
          "action": "deny",
          "message": "ActionGuard blocked this command."
        }
      },
      {
        "name": "slate-actionguard-write",
        "description": "Validate file writes through SLATE ActionGuard",
        "matcher": {
          "tool": "Write"
        },
        "command": "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe ${CLAUDE_PLUGIN_ROOT}/slate/action_guard.py --validate-file \"$TOOL_INPUT_file_path\" --op write",
        "timeout": 3000,
        "onError": "allow"
      }
    ],

    "PostToolUse": [
      {
        "name": "slate-audit-log",
        "description": "Log tool executions for SLATE audit trail",
        "matcher": {
          "tool": ["Bash", "Write", "Edit"]
        },
        "command": "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe ${CLAUDE_PLUGIN_ROOT}/slate/claude_code_manager.py --log-tool \"$TOOL_NAME\" \"$TOOL_USE_ID\"",
        "timeout": 2000,
        "onError": "ignore",
        "background": true
      }
    ],

    "UserPromptSubmit": [
      {
        "name": "slate-prompt-scan",
        "description": "Scan user prompts for security issues",
        "command": "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe ${CLAUDE_PLUGIN_ROOT}/slate/action_guard.py --scan-prompt",
        "timeout": 3000,
        "onError": "allow"
      }
    ],

    "Stop": [
      {
        "name": "slate-session-cleanup",
        "description": "Clean up SLATE session state on stop",
        "command": "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe ${CLAUDE_PLUGIN_ROOT}/slate/copilot_agent_bridge.py --cleanup",
        "timeout": 5000,
        "onError": "ignore"
      }
    ]
  }
}
```

### Hook Events

| Event | When Triggered | SLATE Usage |
|-------|----------------|-------------|
| `PreToolUse` | Before tool execution | Validate Bash commands, file paths |
| `PostToolUse` | After tool execution | Audit logging |
| `UserPromptSubmit` | User sends message | PII/credential scanning |
| `Stop` | Session ends | Cleanup session state |

### ActionGuard Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Destructive command |
| `0.0.0.0` bindings | Network exposure |
| `eval()`, `exec()` | Code injection risk |
| External API calls | Cloud cost prevention |
| Credential patterns | PII protection |

---

## Permission Modes

SLATE supports multiple permission modes configured in `.claude/settings.json`:

### SLATE Operator Mode (Default)

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
      "Edit(*)",
      "Glob(*)",
      "Grep(*)",
      "WebFetch(*)",
      "WebSearch(*)",
      "Task(*)",
      "TodoWrite(*)",
      "mcp__slate__*(*)"
    ]
  }
}
```

### Permission Modes Explained

| Mode | Description | Use Case |
|------|-------------|----------|
| `bypassWithActionGuard` | Skip prompts, ActionGuard validates | Full SLATE operation |
| `acceptEdits` | Auto-accept file edits | Development mode |
| `default` | Prompt for sensitive operations | External users |

### Why Permission Bypass is Safe

1. **ActionGuard validates all commands** before execution (Python-side)
2. **SDK Source Guard** ensures trusted package publishers
3. **PII Scanner** blocks credential exposure
4. **Container isolation** runs commands in K8s/Docker, not host
5. **K8s RBAC** provides minimal service account permissions

---

## Agent SDK Programmatic Usage

For automation and scripting, use the Claude Agent SDK integration.

### Getting Agent Options

```python
from slate.claude_code_manager import get_manager

manager = get_manager()

# Get recommended SDK options
options = manager.get_agent_options(
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    permission_mode="acceptEdits",
    model="claude-sonnet-4-5-20250929"
)

print(options["allowed_tools"])
print(options["mcp_servers"])
```

### Using SLATE Hooks Programmatically

```python
from slate.claude_code_manager import get_manager

manager = get_manager()

# Execute hooks before tool use
result = manager.execute_hooks(
    event="PreToolUse",
    tool_name="Bash",
    tool_input={"command": "python script.py"},
    session_id="my-session"
)

if result.permission_decision == "deny":
    print(f"Blocked: {result.reason}")
else:
    print("Allowed")
```

### Full Agent SDK Integration

```python
from slate.claude_agent_sdk_integration import (
    create_slate_tools,
    create_slate_hooks,
    get_slate_agent_options,
    SLATE_SUBAGENTS,
)

# Get full agent configuration
options = get_slate_agent_options(mode="operator")

print(f"Tools: {options['allowed_tools']}")
print(f"MCP Servers: {list(options['mcp_servers'].keys())}")
print(f"Subagents: {list(options['agents'].keys())}")

# Create hooks instance
hooks = create_slate_hooks()

# Available subagents
for name, config in SLATE_SUBAGENTS.items():
    print(f"{name}: {config['description']}")
```

### SLATE Subagents

| Subagent | Description | Tools |
|----------|-------------|-------|
| `slate-operator` | Infrastructure management | `slate_*`, Bash, Read, Glob |
| `slate-code-reviewer` | Code quality and security | Read, Glob, Grep |
| `slate-test-runner` | Test execution | Bash, Read, Glob |
| `slate-docs-generator` | Documentation generation | Read, Write, Glob, Grep |

### Operation Modes

```python
# Full operator access
options = get_slate_agent_options(mode="operator")
# Tools: All, Permission: bypassPermissions

# Read-only access
options = get_slate_agent_options(mode="readonly")
# Tools: Read, Glob, Grep, slate_status, slate_workflow

# Minimal access
options = get_slate_agent_options(mode="minimal")
# Tools: slate_status only
```

---

## Code Examples

### Example 1: Check System Status

```python
# Using MCP tool directly
result = await slate_status_tool({"format": "quick"})
print(result["content"][0]["text"])
```

### Example 2: Validate Commands with ActionGuard

```python
from slate.action_guard import get_guard

guard = get_guard()

# Safe command
result = guard.validate_command("python --version")
print(f"Allowed: {result.allowed}")  # True

# Blocked command
result = guard.validate_command("rm -rf /")
print(f"Allowed: {result.allowed}")  # False
print(f"Reason: {result.reason}")
```

### Example 3: Manage Workflow Queue

```python
from slate.slate_workflow_manager import WorkflowManager

manager = WorkflowManager()

# Get status
print(manager.status_report())

# Cleanup stale tasks
print(manager.cleanup())

# Enforce rules
print(manager.enforce_rules())
```

### Example 4: Session Management

```python
from slate.claude_code_manager import get_manager

manager = get_manager()

# Create session
session_id = manager.create_session()

# Record tool use
manager.record_tool_use(
    session_id=session_id,
    tool_name="Bash",
    tool_input={"command": "pytest"},
    tool_output="All tests passed"
)

# Get session data
session = manager.get_session(session_id)
print(f"Tool uses: {len(session['tool_uses'])}")
```

### Example 5: Validation Report

```python
from slate.claude_code_manager import get_manager

manager = get_manager()

# Run all validation checks
results = manager.validate()

for r in results:
    status = "PASS" if r.valid else "FAIL"
    print(f"[{status}] {r.component}: {r.message}")

# Generate full report
print(manager.generate_report())
```

---

## Troubleshooting

### MCP Server Not Starting

**Symptoms**: Tools not available, "MCP server not found" errors

**Solutions**:
1. Check Python venv exists: `.\.venv\Scripts\python.exe --version`
2. Verify MCP script exists: `Test-Path slate/mcp_server.py`
3. Check MCP package: `pip show mcp`
4. Test manually: `.\.venv\Scripts\python.exe slate/mcp_server.py`

### ActionGuard Blocking Valid Commands

**Symptoms**: Commands blocked unexpectedly

**Solutions**:
1. Check blocked patterns in `slate/action_guard.py`
2. Review hook output for specific reason
3. Add exception if appropriate (with security review)

### Plugin Not Loading

**Symptoms**: Commands not available, plugin not recognized

**Solutions**:
1. Verify `.claude-plugin/plugin.json` exists
2. Check for JSON syntax errors
3. Restart Claude Code
4. Check scope conflicts (local vs marketplace)

### Permission Denied

**Symptoms**: Operations failing with permission errors

**Solutions**:
1. Check `.claude/settings.local.json` for permission rules
2. Verify `SLATE_ACTIONGUARD=enabled` environment variable
3. Review behavior profile in `.claude/behaviors/`

### Hooks Not Executing

**Symptoms**: Hooks not triggering, no audit logs

**Solutions**:
1. Verify `.claude/hooks.json` syntax
2. Check hook timeout settings
3. Test hook commands manually
4. Check hook `onError` behavior

### Validation Failing

**Symptoms**: Validation checks failing

**Solutions**:
```powershell
# Run validation with details
.\.venv\Scripts\python.exe slate/claude_code_manager.py --validate

# Generate full report
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report
```

---

## Related Documentation

- [Architecture](Architecture) - System design and components
- [CLI Reference](CLI-Reference) - Command-line tools
- [Configuration](Configuration) - Settings and customization
- [AI Backends](AI-Backends) - Ollama and Foundry Local setup
- [Troubleshooting](Troubleshooting) - Common issues and solutions
- [API Reference](API-Reference) - Programmatic API documentation

---

## Quick Reference

```powershell
# Validate Claude Code configuration
.\.venv\Scripts\python.exe slate/claude_code_manager.py --validate

# Generate full validation report
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report

# Show Agent SDK options
.\.venv\Scripts\python.exe slate/claude_code_manager.py --agent-options

# Test MCP server
.\.venv\Scripts\python.exe slate/claude_code_manager.py --test-mcp slate

# Check integration status
.\.venv\Scripts\python.exe slate/claude_code_manager.py --status
```
