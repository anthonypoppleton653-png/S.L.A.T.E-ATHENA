---
description: Main SLATE Kubernetes command - deploy, manage, and monitor SLATE on K8s
---

# /slate-kubernetes:k8s

Manage SLATE on Kubernetes (Docker Desktop, minikube, k3s, Rancher Desktop).

## Usage

```
/slate-kubernetes:k8s [action] [options]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | Show deployment status (default) |
| `deploy` | Deploy SLATE to K8s |
| `teardown` | Remove SLATE from K8s |
| `logs` | View pod logs |
| `detect` | Detect K8s provider |
| `build` | Build local Docker images |

## Options

| Option | Description |
|--------|-------------|
| `--method helm` | Use Helm instead of Kustomize |
| `--follow` | Follow logs in real-time |
| `--json` | Output as JSON |

## Instructions

Parse the user's request and run the appropriate command:

**Status Check:**
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --status
```

**Deploy:**
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --deploy
```

**Teardown:**
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --teardown
```

**Logs:**
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --logs
```

**Detect Provider:**
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --detect
```

## Examples

```
/slate-kubernetes:k8s status        # Check deployment
/slate-kubernetes:k8s deploy        # Deploy with Kustomize
/slate-kubernetes:k8s deploy helm   # Deploy with Helm
/slate-kubernetes:k8s teardown      # Remove from K8s
/slate-kubernetes:k8s logs          # View logs
```
