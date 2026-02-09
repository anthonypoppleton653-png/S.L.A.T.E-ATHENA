---
description: Deploy SLATE to local Kubernetes cluster
---

# /slate-kubernetes:k8s-deploy

Deploy SLATE to a local Kubernetes cluster.

## Usage

```
/slate-kubernetes:k8s-deploy [--method kustomize|helm] [--build]
```

## Options

| Option | Description |
|--------|-------------|
| `--method kustomize` | Use Kustomize overlays (default) |
| `--method helm` | Use Helm chart |
| `--build` | Build Docker images before deploy |

## Instructions

1. First detect the K8s provider:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --detect
```

2. Optionally build images:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --build
```

3. Deploy:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --deploy --method kustomize
```

4. Verify:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --status
```

## Post-Deploy

Access the dashboard:
```powershell
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
```

Then open: http://127.0.0.1:8080

## Examples

```
/slate-kubernetes:k8s-deploy                    # Deploy with Kustomize
/slate-kubernetes:k8s-deploy --method helm      # Deploy with Helm
/slate-kubernetes:k8s-deploy --build            # Build and deploy
```
