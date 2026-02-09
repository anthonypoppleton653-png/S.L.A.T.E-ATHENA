---
description: Remove SLATE from Kubernetes cluster
---

# /slate-kubernetes:k8s-teardown

Remove SLATE deployment from Kubernetes.

## Usage

```
/slate-kubernetes:k8s-teardown [--method kustomize|helm]
```

## Options

| Option | Description |
|--------|-------------|
| `--method kustomize` | Remove Kustomize resources (default) |
| `--method helm` | Uninstall Helm release |

## Instructions

Run the teardown:

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --teardown
```

For Helm:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --teardown --method helm
```

## What Gets Removed

- All SLATE Deployments
- All SLATE Services
- ConfigMaps and Secrets
- SLATE Namespace (if empty)

## What Is Retained

- PersistentVolumes (Retain policy)
- Docker images (local cache)

To fully clean storage:
```powershell
kubectl delete pv -l app.kubernetes.io/part-of=slate-system
```

## Verification

```powershell
kubectl get all -n slate
```

## Examples

```
/slate-kubernetes:k8s-teardown              # Remove with Kustomize
/slate-kubernetes:k8s-teardown --method helm # Uninstall Helm chart
```
