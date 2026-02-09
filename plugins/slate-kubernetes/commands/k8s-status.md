---
description: Check SLATE Kubernetes deployment status
---

# /slate-kubernetes:k8s-status

Check the status of SLATE running on Kubernetes.

## Usage

```
/slate-kubernetes:k8s-status [--json]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON for automation |

## Instructions

Run the status command:

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --status
```

For JSON output:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --detect --json
```

## Status Output

The command shows:
- K8s provider (Docker Desktop, minikube, k3s)
- All SLATE pods and their status
- Services and endpoints
- PersistentVolumeClaims
- Resource usage (CPU/memory)
- GPU allocation

## Health Check

For programmatic health checking:
```powershell
.\.venv\Scripts\python.exe slate/k8s_integration.py --health --json
```

## Examples

```
/slate-kubernetes:k8s-status        # Full status report
/slate-kubernetes:k8s-status --json # Machine-readable output
```
