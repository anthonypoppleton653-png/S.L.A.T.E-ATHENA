---
name: k8s-teardown
description: Remove SLATE from Kubernetes cluster. Use when uninstalling or cleaning up SLATE K8s deployment.
---

# Kubernetes Teardown Skill

Remove SLATE from a Kubernetes cluster.

## Instructions

When the user wants to remove SLATE from Kubernetes:

### Using Kustomize (default)

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --teardown --method kustomize
```

### Using Helm

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --teardown --method helm
```

## What Gets Removed

- All SLATE Deployments
- All SLATE Services
- All SLATE ConfigMaps
- All SLATE Secrets
- SLATE Namespace (if empty)

## What Gets Retained

- **PersistentVolumes** (Retain policy by default)
- **Docker images** (cached locally)

To fully clean up storage:
```powershell
kubectl delete pv -l app.kubernetes.io/part-of=slate-system
```

## Verification

After teardown, verify with:
```powershell
kubectl get all -n slate
```

Should return: `No resources found in slate namespace.`

## Examples

User: "Remove SLATE from Kubernetes"
-> Run teardown with default method

User: "Uninstall SLATE Helm chart"
-> Use --method helm for Helm uninstall

User: "Clean up K8s deployment"
-> Run teardown and optionally remove PVs
