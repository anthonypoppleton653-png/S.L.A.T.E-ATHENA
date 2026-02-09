# SLATE Plugin for Claude Code

**S.L.A.T.E.** — Synchronized Living Architecture for Transformation and Evolution

The unified SLATE plugin for Claude Code with:
- **SLATE Operator Behavior** — Permission bypass with ActionGuard security
- **MCP Tools** — 12 tools for system management
- **Slash Commands** — Quick access to all SLATE operations
- **K8s/Docker Runtime** — Container-first execution
- **10 Operational Protocols** — Structured task execution

## Installation

The plugin is automatically enabled when working in a SLATE workspace.

### Manual Installation

Add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "slate-marketplace": {
      "source": "."
    }
  },
  "enabledPlugins": {
    "slate@slate-marketplace": true
  }
}
```

## Behavior Profile

This plugin runs with **SLATE Operator Behavior**:

| Setting | Value |
|---------|-------|
| Profile | `slate-operator` |
| Permission Mode | `bypassWithActionGuard` |
| Security | ActionGuard (Python-side) |
| Runtime | K8s > Docker |

### Permission Bypass

All tool calls are pre-approved:
- `Bash(*)` — Validated by ActionGuard
- `Read(*)`, `Write(*)`, `Edit(*)` — File operations
- `mcp__slate__*(*)` — All SLATE MCP tools

### Security

Despite bypass mode, security is maintained through:
1. **ActionGuard** — Blocks `rm -rf`, `0.0.0.0`, `eval()`
2. **PreToolUse Hooks** — Validate before execution
3. **Container Isolation** — Commands run in K8s/Docker

## Commands

| Command | Description |
|---------|-------------|
| `/slate` | Main command (status, start, stop) |
| `/slate-status` | Quick system health check |
| `/slate-workflow` | Task queue management |
| `/slate-runner` | GitHub Actions runner |
| `/slate-gpu` | GPU management |
| `/slate-k8s` | Kubernetes deployment |
| `/slate-help` | Show all commands |

## MCP Tools

| Tool | Description |
|------|-------------|
| `slate_status` | System health check |
| `slate_workflow` | Task queue management |
| `slate_orchestrator` | Service lifecycle |
| `slate_runner` | Runner management |
| `slate_ai` | AI task execution |
| `slate_runtime` | Runtime integrations |
| `slate_hardware` | GPU detection |
| `slate_benchmark` | Performance benchmarks |
| `slate_gpu` | Dual-GPU management |
| `slate_claude_code` | Claude Code validation |
| `slate_spec_kit` | Spec processing |
| `slate_schematic` | System diagrams |

## Protocols

| Protocol | Description |
|----------|-------------|
| P001-INIT | System initialization |
| P002-EXECUTE | DIAGNOSE → ACT → VERIFY |
| P003-WORKFLOW | Task management |
| P004-GPU | Dual-GPU load balancing |
| P005-SECURITY | ActionGuard validation |
| P006-RECOVERY | Error recovery |
| P007-CODE | File operations |
| P008-GIT | Git with safety |
| P009-K8S | Kubernetes |
| P010-AUTONOMOUS | Background tasks |

## License

EOSL-1.0
