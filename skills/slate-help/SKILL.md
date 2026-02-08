---
name: slate-help
description: Show all available SLATE commands. Use when user asks for help with SLATE or available commands.
---

# /slate-help

Display help for all SLATE slash commands.

## Instructions

Show this help information:

## SLATE Commands

<!-- Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s commands to help skill -->

| Command | Description |
|---------|-------------|
| `/slate-sdk:slate-orchestrator [start\|stop\|status]` | Manage SLATE orchestrator |
| `/slate-sdk:slate-status [--quick\|--json]` | Check system and service status |
| `/slate-sdk:slate-workflow [--status\|--cleanup]` | Manage task workflow queue |
| `/slate-sdk:slate-runner [--status\|--setup]` | Manage GitHub Actions runner |
| `/slate-sdk:slate-k8s [--status\|--deploy\|--health\|--teardown]` | Kubernetes cluster management |
| `/slate-sdk:slate-help` | Show this help |

## Quick Examples

```bash
/slate-sdk:slate-orchestrator start   # Start all SLATE services
/slate-sdk:slate-orchestrator stop    # Stop all services
/slate-sdk:slate-status --quick       # Check GPU, services, environment
/slate-sdk:slate-workflow --status    # View task queue health
/slate-sdk:slate-runner --status      # Check GitHub runner status
```

Note: Commands are namespaced with `slate-sdk:` prefix to avoid conflicts with other plugins.

## MCP Tools

The SLATE MCP server also provides these tools:
- `slate_status` - Check all services and GPU status
- `slate_workflow` - Manage task queue
- `slate_orchestrator` - Start/stop services
- `slate_runner` - Manage GitHub runner
- `slate_ai` - Execute AI tasks via local LLMs
- `slate_kubernetes` - K8s cluster status, deploy, health, teardown
