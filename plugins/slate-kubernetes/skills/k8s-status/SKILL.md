---
name: k8s-status
description: Check SLATE Kubernetes deployment status. Use when checking pod health, service status, or K8s cluster info.
---

# Kubernetes Status Skill

Check the status of SLATE running on Kubernetes.

## Instructions

When the user wants to check Kubernetes status, run:

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --status
```

For JSON output (automation/parsing):
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --detect --json
```

## Status Information

The status command shows:

1. **Provider Info**
   - K8s provider (Docker Desktop, minikube, k3s)
   - Current context
   - kubectl version
   - Helm availability
   - GPU detection

2. **Pod Status**
   - All SLATE pods in the `slate` namespace
   - Pod phase (Running, Pending, Failed)
   - Ready status
   - Restart count

3. **Services**
   - All SLATE services
   - ClusterIP and ports
   - Endpoints

4. **Storage**
   - PersistentVolumeClaims
   - Bound/Pending status
   - Storage class

5. **Resource Usage**
   - CPU and memory per pod
   - GPU allocation

## Health Check API

For programmatic health checks:

```python
from slate.k8s_integration import get_k8s_integration

k8s = get_k8s_integration()
status = await k8s.get_full_status()
```

## Examples

User: "What's the K8s status?"
-> Run status check and report all pods/services

User: "Are the SLATE pods healthy?"
-> Check pod status and report any issues

User: "Check Kubernetes cluster info"
-> Detect provider and show cluster configuration
