---
name: slate-status
description: Check SLATE services and system status. Use when checking GPU, services, or environment health.
---

# /slate-status

Check the status of all SLATE services and system components.

## Usage
/slate-status [--quick | --json | --full]

## Description
<!-- Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s status to skill description -->
This skill provides comprehensive system status for the SLATE development environment including:
- GPU detection and configuration
- Service health (Dashboard, Ollama, Foundry Local)
- GitHub Actions runner status
- Workflow queue health
- Python environment validation
- Kubernetes cluster status (pods, deployments, services)
- Docker container state

## Instructions

When the user invokes this skill, run the SLATE status command:

```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --quick
```

For JSON output (automation):
```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --json
```

Report the results in a clear, formatted summary showing:
1. Service status (running/stopped)
2. GPU availability and configuration
3. Any warnings or issues detected
4. Recommendations for fixes if issues found

## Examples

User: "/slate-status"
→ Run quick status check and report all services

User: "/slate-status --json"
→ Output machine-readable JSON for pipeline integration

User: "What's the status of SLATE?"
→ Invoke this skill automatically

User: "Check K8s pods"
→ Run `python slate/slate_k8s_deploy.py --status` and report pod health
