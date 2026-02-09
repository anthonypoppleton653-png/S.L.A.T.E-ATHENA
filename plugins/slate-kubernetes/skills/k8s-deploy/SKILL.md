---
name: k8s-deploy
description: Deploy SLATE to local Kubernetes cluster. Use when deploying SLATE to Docker Desktop K8s, minikube, k3s, or Rancher Desktop.
---

# Kubernetes Deploy Skill

Deploy SLATE to a local Kubernetes cluster with GPU support.

## Prerequisites

Before deploying, ensure:
1. A local K8s cluster is running (Docker Desktop K8s, minikube, or k3s)
2. kubectl is installed and configured
3. SLATE Docker images are built (optional - can pull from registry)

## Instructions

When the user wants to deploy SLATE to Kubernetes, follow these steps:

### 1. Detect the K8s Provider

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --detect --json
```

Report which provider is detected (Docker Desktop, minikube, k3s).

### 2. Check if Images Need Building

If using local images:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --build
```

### 3. Deploy SLATE

Using Kustomize (default):
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --deploy --method kustomize
```

Using Helm:
```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --deploy --method helm
```

### 4. Verify Deployment

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --status
```

## Services Deployed

| Service | Port | Description |
|---------|------|-------------|
| slate-dashboard-svc | 8080 | SLATE Dashboard UI |
| ollama-svc | 11434 | Ollama LLM inference |
| chromadb-svc | 8000 | ChromaDB vector store |

## Port Forwarding

To access the dashboard locally:
```powershell
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
```

## GPU Support

SLATE automatically detects NVIDIA GPUs and configures:
- nvidia.com/gpu resource requests
- CUDA_VISIBLE_DEVICES environment
- GPU node affinity

## Examples

User: "Deploy SLATE to Kubernetes"
-> Detect provider, deploy with kustomize, verify status

User: "Deploy SLATE to minikube with Helm"
-> Use --method helm for Helm deployment

User: "Build and deploy SLATE locally"
-> Build images first, then deploy
