---
description: Show all SLATE commands
---

# /slate-help

Show all available SLATE commands and protocols.

## Commands

| Command | Description |
|---------|-------------|
| `/slate` | Main command (status, start, stop) |
| `/slate-status` | Quick system health check |
| `/slate-workflow` | Task queue management |
| `/slate-runner` | GitHub Actions runner |
| `/slate-gpu` | GPU management |
| `/slate-k8s` | Kubernetes deployment |
| `/slate-help` | This help |

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

## MCP Tools

12 MCP tools available:
- `slate_status`, `slate_workflow`, `slate_orchestrator`
- `slate_runner`, `slate_ai`, `slate_runtime`
- `slate_hardware`, `slate_benchmark`, `slate_gpu`
- `slate_claude_code`, `slate_spec_kit`, `slate_schematic`
