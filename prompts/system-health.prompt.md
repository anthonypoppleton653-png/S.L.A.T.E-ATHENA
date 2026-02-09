---
name: system-health
agent: 'agent'
description: 'Check SLATE system health including GPU, services, Kubernetes, and workflow status'
tags: [health, diagnostics, status]
model: 'slate-fast'
# Modified: 2026-02-09T02:47:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from sonnet→slate-fast (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# System Health Check

Check the complete health status of the SLATE system.

## Instructions

Run the following checks in order:

1. **System Status** - Quick health check of all components
   ```powershell
   python slate/slate_status.py --quick
   ```

2. **Runtime Integrations** - Verify all 7 integrations are active
   ```powershell
   python slate/slate_runtime.py --check-all
   ```

3. **Workflow Queue** - Check for stale or blocked tasks
   ```powershell
   python slate/slate_workflow_manager.py --status
   ```

4. **Kubernetes Status** (if deployed)
   ```powershell
   python slate/slate_k8s_deploy.py --status
   ```

## Expected Output

Report results in a structured format:

| Component | Status | Details |
|-----------|--------|---------|
| Python | OK/WARN/ERROR | Version, venv path |
| GPU | OK/WARN/ERROR | Count, memory, architecture |
| Services | OK/WARN/ERROR | Dashboard, Ollama, etc. |
| Kubernetes | OK/WARN/N/A | Pod count, health |
| Workflow | OK/WARN/ERROR | Task counts, stale tasks |

## Troubleshooting

If issues are found:
- **GPU not detected**: Check NVIDIA drivers, run `nvidia-smi`
- **Ollama offline**: Start with `ollama serve`
- **Stale tasks**: Run `python slate/slate_workflow_manager.py --cleanup`
- **K8s unhealthy**: Check pods with `kubectl get pods -n slate`
