# SLATE Kubernetes Plugin

Deploy, manage, and monitor SLATE on local Kubernetes clusters (Docker Desktop, minikube, k3s, Rancher Desktop).

## Installation

Install directly from GitHub:

```bash
claude /plugin install https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E#plugins/slate-kubernetes
```

Or clone and install locally:

```bash
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
claude --plugin-dir ./S.L.A.T.E/plugins/slate-kubernetes
```

## Requirements

- **kubectl** - Kubernetes CLI (required)
- **helm** - Helm package manager (optional, for Helm deployments)
- **docker** - Docker runtime (optional, for building images)

### Supported K8s Providers

| Provider | GPU Support | Notes |
|----------|-------------|-------|
| Docker Desktop | Yes | Enable K8s in settings |
| minikube | Yes | Use `--driver docker --gpus all` |
| k3s / k3d | Yes | Lightweight, good for dev |
| Rancher Desktop | Yes | Alternative to Docker Desktop |

## Commands

After installation, the following commands are available:

| Command | Description |
|---------|-------------|
| `/slate-kubernetes:k8s` | Main K8s management command |
| `/slate-kubernetes:k8s-deploy` | Deploy SLATE to K8s |
| `/slate-kubernetes:k8s-status` | Check deployment status |
| `/slate-kubernetes:k8s-teardown` | Remove SLATE from K8s |

## Quick Start

1. **Ensure K8s is running:**
   ```bash
   kubectl cluster-info
   ```

2. **Deploy SLATE:**
   ```
   /slate-kubernetes:k8s-deploy
   ```

3. **Check status:**
   ```
   /slate-kubernetes:k8s-status
   ```

4. **Access Dashboard:**
   ```bash
   kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
   ```
   Open: http://127.0.0.1:8080

## Deployment Methods

### Kustomize (Default)

Uses Kubernetes-native Kustomize for deployment:

```
/slate-kubernetes:k8s-deploy --method kustomize
```

Manifests are in `k8s/` directory with overlays for different environments:
- `k8s/overlays/local/` - Local development
- `k8s/overlays/dev/` - Development cluster
- `k8s/overlays/staging/` - Staging environment
- `k8s/overlays/prod/` - Production

### Helm

Uses Helm chart for deployment:

```
/slate-kubernetes:k8s-deploy --method helm
```

Chart is in `helm/slate/` directory.

## Services Deployed

| Service | Port | Description |
|---------|------|-------------|
| slate-dashboard-svc | 8080 | SLATE Dashboard UI |
| ollama-svc | 11434 | Ollama LLM inference |
| chromadb-svc | 8000 | ChromaDB vector store |
| slate-agent-router-svc | 8081 | Agent routing service |
| slate-workflow-svc | 8084 | Workflow manager |

## GPU Support

SLATE automatically detects NVIDIA GPUs and configures:

- `nvidia.com/gpu` resource requests
- `CUDA_VISIBLE_DEVICES` environment
- GPU node affinity
- NVIDIA device plugin integration

For dual-GPU systems, SLATE distributes LLM inference across GPUs.

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod -n slate -l app=slate-dashboard
kubectl logs -n slate -l app=slate-dashboard
```

### Image pull errors

Build images locally:
```bash
python slate/slate_k8s.py --build
```

### GPU not detected

Ensure NVIDIA device plugin is installed:
```bash
kubectl get pods -n kube-system | grep nvidia
```

## Teardown

Remove SLATE from K8s:

```
/slate-kubernetes:k8s-teardown
```

Note: PersistentVolumes are retained by default. To fully clean up:
```bash
kubectl delete pv -l app.kubernetes.io/part-of=slate-system
```

## License

EOSL-1.0 - See [LICENSE](../../LICENSE) for details.

## Repository

https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E
