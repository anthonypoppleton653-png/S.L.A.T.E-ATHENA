---
description: Kubernetes deployment management
---

# /slate-k8s

Deploy and manage SLATE on Kubernetes.

## Usage

```
/slate-k8s [action]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | Deployment status (default) |
| `deploy` | Deploy to K8s |
| `teardown` | Remove from K8s |
| `logs` | View pod logs |
| `detect` | Detect K8s provider |

## Instructions

**Status:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --status
```

**Deploy:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --deploy
```

**Teardown:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --teardown
```

**Logs:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --logs
```

**Detect:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --detect --json
```
