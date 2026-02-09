---
name: deploy-kubernetes
agent: 'agent'
description: 'Deploy SLATE to Kubernetes cluster using Kustomize overlays or Helm'
tags: [kubernetes, deployment, infrastructure]
model: 'sonnet'
---

# Deploy SLATE to Kubernetes

Deploy the complete SLATE system to a Kubernetes cluster.

## Prerequisites

Before deployment, verify:
- `kubectl` is configured with cluster access
- NVIDIA GPU operator installed (for GPU nodes)
- Sufficient cluster resources (8GB RAM, 4 CPUs minimum)

## Deployment Options

### Option 1: Kustomize (Recommended)

```powershell
# Local/development deployment
python slate/slate_k8s_deploy.py --deploy-kustomize local

# Production deployment
python slate/slate_k8s_deploy.py --deploy-kustomize prod
```

### Option 2: Direct Apply

```powershell
# Apply all base manifests
kubectl apply -k k8s/overlays/local/
```

### Option 3: Helm

```powershell
helm install slate ./helm -n slate --create-namespace -f helm/values.yaml
```

## Post-Deployment Verification

1. **Check pod status**
   ```powershell
   kubectl get pods -n slate
   ```

2. **Health check**
   ```powershell
   python slate/slate_k8s_deploy.py --health
   ```

3. **Port forward dashboard**
   ```powershell
   kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
   ```

4. **Access dashboard**
   Open http://localhost:8080 in browser

## Expected Services

After successful deployment:

| Service | Port | Purpose |
|---------|------|---------|
| slate-dashboard-svc | 8080 | Main dashboard |
| slate-copilot-bridge-svc | 8083 | VS Code extension |
| ollama-svc | 11434 | LLM inference |
| chromadb-svc | 8000 | Vector store |

## Troubleshooting

- **Pods stuck in Pending**: Check node resources, GPU availability
- **ImagePullBackOff**: Verify image registry access
- **CrashLoopBackOff**: Check logs with `kubectl logs -n slate <pod>`
