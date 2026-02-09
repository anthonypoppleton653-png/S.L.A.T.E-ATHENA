# Kubernetes Deployment
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Create comprehensive K8s deployment guide -->

SLATE runs as a **containerized local cloud** using Kubernetes. This guide covers deploying, managing, and troubleshooting SLATE in a Kubernetes environment.

## Overview: Local Cloud Concept

SLATE transforms your local hardware into a fully-featured AI operations center. Instead of running services directly on the host, Kubernetes provides:

| Benefit | Description |
|---------|-------------|
| **Isolation** | Each service runs in its own container with defined resource limits |
| **Self-Healing** | Failed pods are automatically restarted |
| **Scaling** | Horizontal Pod Autoscalers adjust replicas based on load |
| **Networking** | Services discover each other via DNS (e.g., `ollama-svc:11434`) |
| **Security** | Network policies, RBAC, and pod security contexts enforce least-privilege |

The entire SLATE ecosystem deploys as microservices in the `slate` namespace.

---

## Prerequisites

<table>
<tr>
<th>Required</th>
<th>Recommended</th>
</tr>
<tr>
<td>
<ul>
<li><strong>kubectl</strong> - <a href="https://kubernetes.io/docs/tasks/tools/">Install Guide</a></li>
<li><strong>Kubernetes cluster</strong> (any of):
  <ul>
  <li>Docker Desktop K8s</li>
  <li>minikube</li>
  <li>kind</li>
  <li>k3s</li>
  </ul>
</li>
<li><strong>4GB+ RAM</strong> available for K8s</li>
</ul>
</td>
<td>
<ul>
<li><strong>Helm 3</strong> - For templated deployments</li>
<li><strong>NVIDIA GPU</strong> with device plugin</li>
<li><strong>metrics-server</strong> - For HPA auto-scaling</li>
<li><strong>Ingress controller</strong> - For external access</li>
</ul>
</td>
</tr>
</table>

### Verify Prerequisites

```bash
# Check kubectl
kubectl version --client

# Check cluster connectivity
kubectl cluster-info

# Check available nodes
kubectl get nodes

# Check for GPU support (optional)
kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}'
```

---

## Quick Deploy

### Option 1: PowerShell Script (Recommended for Windows)

```powershell
# Deploy to local K8s
.\k8s\deploy.ps1 -Environment local

# Check status
.\k8s\status.ps1

# Dry-run to preview changes
.\k8s\deploy.ps1 -Environment local -DryRun
```

### Option 2: Kustomize

```bash
# Deploy base configuration
kubectl apply -k k8s/

# Or deploy local overlay (for minikube/kind/Docker Desktop)
kubectl kustomize k8s/overlays/local/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -

# Check deployment status
kubectl get pods -n slate -w
```

### Option 3: Helm

```bash
# Install with Helm
helm install slate ./helm -n slate --create-namespace

# Upgrade existing installation
helm upgrade slate ./helm -n slate -f custom-values.yaml

# View generated manifests (dry-run)
helm template slate ./helm -n slate
```

---

## Architecture

SLATE deploys 7 core deployments plus supporting infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Ingress (slate.local)                                │
│                              nginx-ingress-controller                           │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────────────┐
│  SLATE Dashboard│         │  Agent Router   │         │   Autonomous Loop       │
│   (HPA 2-6)     │         │   (2 replicas)  │         │    (1 pod + GPU)        │
│   Port: 8080    │         │   Port: 8081    │         │    Port: 8082           │
└────────┬────────┘         └────────┬────────┘         └───────────┬─────────────┘
         │                           │                               │
         └───────────────────────────┼───────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────────┐
         │                           │                               │
         ▼                           ▼                               ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────────────┐
│     Ollama      │         │    ChromaDB     │         │   Copilot Bridge        │
│   (GPU Node)    │         │  (Vector Store) │         │    Port: 8083           │
│  Port: 11434    │         │   Port: 8000    │         └─────────────────────────┘
└─────────────────┘         └─────────────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │                               │
                     ▼                               ▼
          ┌─────────────────┐             ┌─────────────────────────┐
          │Workflow Manager │             │   GitHub Runner         │
          │  Port: 8084     │             │   (Optional ARC)        │
          └─────────────────┘             └─────────────────────────┘
```

### Deployments

| Deployment | Replicas | Purpose | Port |
|------------|----------|---------|------|
| `slate-dashboard` | 2-6 (HPA) | Full FastAPI UI with WebSocket | 8080 |
| `slate-agent-router` | 2 | Task classification and routing | 8081 |
| `slate-autonomous-loop` | 1 | Self-healing task execution brain | 8082 |
| `slate-copilot-bridge` | 1 | VS Code extension integration | 8083 |
| `slate-workflow-manager` | 1 | Task lifecycle management | 8084 |
| `ollama` | 1 | Local LLM inference (GPU) | 11434 |
| `chromadb` | 1 | Vector store for RAG memory | 8000 |

---

## Services and Ports

| Service | K8s Service Name | Port | Protocol | Purpose |
|---------|------------------|------|----------|---------|
| Dashboard | `slate-dashboard-svc` | 8080 | HTTP/WS | UI, REST API, WebSocket |
| Ollama | `ollama-svc` | 11434 | HTTP | LLM inference API |
| ChromaDB | `chromadb-svc` | 8000 | HTTP | Vector database API |
| Agent Router | `slate-agent-router-svc` | 8081 | HTTP | Task routing API |
| Autonomous Loop | `slate-autonomous-svc` | 8082 | HTTP | Loop status API |
| Copilot Bridge | `slate-copilot-bridge-svc` | 8083 | HTTP | VS Code bridge API |
| Workflow | `slate-workflow-svc` | 8084 | HTTP | Workflow management |
| Metrics | `slate-metrics-svc` | 9090 | HTTP | Prometheus scrape target |

### Service Discovery

Within the cluster, services communicate using Kubernetes DNS:

```python
# In K8s, services are reachable by name
OLLAMA_HOST = "ollama-svc:11434"     # Not localhost!
CHROMADB_HOST = "chromadb-svc:8000"
```

---

## Kustomize Overlays

SLATE uses Kustomize for environment-specific configurations:

```
k8s/
├── kustomization.yaml        # Base configuration
├── namespace.yaml
├── rbac.yaml
├── storage.yaml
├── deployments.yaml
├── slate-dashboard.yaml
├── agentic-system.yaml
├── ml-pipeline.yaml
└── overlays/
    ├── local/                # minikube/kind/Docker Desktop
    │   ├── kustomization.yaml
    │   └── local-storage.yaml
    ├── dev/                  # Development cluster
    │   └── kustomization.yaml
    ├── staging/              # Staging environment
    │   └── kustomization.yaml
    └── prod/                 # Production deployment
        └── kustomization.yaml
```

### Applying Overlays

```bash
# Local development (Docker Desktop/minikube)
kubectl kustomize k8s/overlays/local/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -

# Development environment
kubectl apply -k k8s/overlays/dev/

# Production (with GPU and scaling)
kubectl apply -k k8s/overlays/prod/
```

### Local Overlay Features

The `local` overlay:
- Uses `slate:local` image (locally built, never pulled)
- Replaces PVCs with hostPath volumes
- Removes GPU nodeSelector (for clusters without GPU labels)
- Sets `imagePullPolicy: Never` for local images

---

## Helm Chart

The Helm chart provides templated deployment with customizable values.

### Installation

```bash
# Install with defaults
helm install slate ./helm -n slate --create-namespace

# Install with custom values
helm install slate ./helm -n slate --create-namespace -f my-values.yaml

# View values schema
helm show values ./helm
```

### Key Values

```yaml
# helm/values.yaml (excerpt)

# Dashboard configuration
dashboard:
  replicas: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 6
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi

# Ollama LLM
ollama:
  enabled: true
  resources:
    limits:
      nvidia.com/gpu: "1"   # Request GPU
  persistence:
    size: 20Gi

# ChromaDB vector store
chromadb:
  enabled: true
  persistence:
    size: 5Gi

# GPU configuration
gpu:
  enabled: true
  nodeSelector:
    nvidia.com/gpu.present: "true"

# Agentic AI system
agenticSystem:
  enabled: true
  agents:
    ALPHA:
      role: Coding
      gpu: true
      model: slate-coder
    BETA:
      role: Testing
      gpu: true
      model: slate-fast
```

### Common Customizations

```bash
# CPU-only deployment (no GPU)
helm install slate ./helm -n slate --set gpu.enabled=false

# Single replica (minimal resources)
helm install slate ./helm -n slate \
  --set dashboard.replicas=1 \
  --set dashboard.autoscaling.enabled=false

# Custom storage class
helm install slate ./helm -n slate \
  --set storage.workspace.storageClass=fast-ssd
```

---

## Port Forwarding for Local Access

Since services use ClusterIP (internal only), use port-forwarding for local access:

```bash
# Dashboard (most common)
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080

# Ollama (for direct API access)
kubectl port-forward -n slate svc/ollama-svc 11434:11434

# ChromaDB
kubectl port-forward -n slate svc/chromadb-svc 8000:8000

# All services at once (background)
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080 &
kubectl port-forward -n slate svc/ollama-svc 11434:11434 &
kubectl port-forward -n slate svc/chromadb-svc 8000:8000 &
```

### Using Python Helper

```bash
# SLATE provides a helper for port forwarding
python slate/slate_k8s_deploy.py --port-forward
```

### Accessing After Port-Forward

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8080 |
| Dashboard API | http://localhost:8080/api/status |
| K8s Status | http://localhost:8080/api/k8s/status |
| Ollama | http://localhost:11434/api/tags |
| ChromaDB | http://localhost:8000/api/v2/heartbeat |

---

## CronJobs and Scheduled Tasks

SLATE uses CronJobs for automated maintenance:

| CronJob | Schedule | Purpose |
|---------|----------|---------|
| `slate-model-trainer` | Weekly Sun 3am | Rebuild custom Ollama models |
| `slate-codebase-indexer` | Daily 2am | Re-index codebase to ChromaDB |
| `slate-inference-benchmarks` | Weekly Sun 6am | Run GPU inference benchmarks |
| `slate-nightly-health` | Daily midnight | Full system health check |
| `slate-workflow-cleanup` | Every 4 hours | Clean stale/abandoned tasks |
| `slate-instruction-sync` | Hourly | Sync agent instructions |

### Managing CronJobs

```bash
# List all CronJobs
kubectl get cronjobs -n slate

# View CronJob schedule
kubectl describe cronjob slate-codebase-indexer -n slate

# Trigger manual run
kubectl create job --from=cronjob/slate-codebase-indexer manual-index -n slate

# View job history
kubectl get jobs -n slate --sort-by=.metadata.creationTimestamp

# View job logs
kubectl logs -n slate job/manual-index
```

### One-Time Jobs

The `slate-model-preload` Job runs once after Ollama starts to pull required models:

```bash
# Check model preload status
kubectl get job slate-model-preload -n slate

# View preload logs
kubectl logs -n slate job/slate-model-preload
```

---

## Persistent Storage (PVCs)

SLATE uses PersistentVolumeClaims for data that must survive pod restarts:

| PVC | Size | Purpose |
|-----|------|---------|
| `slate-workspace-pvc` | 10Gi | SLATE workspace (code, configs) |
| `slate-data-pvc` | 5Gi | Index data, caches |
| `slate-memory-pvc` | 2Gi | Autonomous loop state |
| `ollama-data-pvc` | 20Gi | Ollama models (~7GB per model) |
| `chroma-data-pvc` | 5Gi | ChromaDB vector embeddings |

### Checking Storage

```bash
# View PVCs
kubectl get pvc -n slate

# Check storage usage
kubectl exec -n slate deploy/ollama -- df -h /root/.ollama

# Expand PVC (if StorageClass supports it)
kubectl patch pvc ollama-data-pvc -n slate -p '{"spec":{"resources":{"requests":{"storage":"40Gi"}}}}'
```

### Local Storage (hostPath)

For local development, the `local` overlay uses hostPath volumes:

```yaml
# k8s/overlays/local/local-storage.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: slate-workspace-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /path/to/S.L.A.T.E  # Your local workspace
```

---

## RBAC and Security

SLATE follows the principle of least privilege:

### Service Accounts

| ServiceAccount | Purpose | Permissions |
|----------------|---------|-------------|
| `slate-core` | Dashboard, workflow manager | ConfigMaps R/W, Pods R, Secrets R |
| `slate-agent` | Agents, ChromaDB, Ollama | ConfigMaps R, Pods R (read-only) |
| `slate-runner` | GitHub Actions runner | Jobs create, ConfigMaps R/W |

### Roles

```yaml
# slate-core-role: Can manage state, not secrets
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]  # Read only, no create/update

# slate-agent-role: Read-only access
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
```

### Pod Security

All SLATE pods run with restricted security contexts:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

containerSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false  # SLATE needs writable /tmp
  capabilities:
    drop:
      - ALL
```

### Network Policies

NetworkPolicies restrict pod-to-pod communication:

```yaml
# Dashboard can only reach:
# - Ollama (port 11434)
# - ChromaDB (port 8000)
# - DNS (port 53)
# - GitHub API (port 443)
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n slate

# View pod events
kubectl describe pod -n slate <pod-name>

# Common issues:
# - ImagePullBackOff: Image not found or registry auth
# - Pending: Insufficient resources or PVC not bound
# - CrashLoopBackOff: Application crashing
```

### ImagePullBackOff

```bash
# For local images, build first
docker build -t slate:local .

# Verify image exists
docker images | grep slate

# For minikube, load image into cluster
minikube image load slate:local

# For kind
kind load docker-image slate:local
```

### PVC Pending

```bash
# Check PVC status
kubectl get pvc -n slate

# View PV availability
kubectl get pv

# For local clusters, apply local-storage overlay
kubectl apply -f k8s/overlays/local/local-storage.yaml
```

### Service Not Reachable

```bash
# Check service exists
kubectl get svc -n slate

# Test from within cluster
kubectl run -n slate debug --rm -it --image=busybox -- wget -qO- http://ollama-svc:11434/api/tags

# Check endpoints
kubectl get endpoints -n slate
```

### Ollama Out of Memory

```bash
# Check GPU memory
kubectl exec -n slate deploy/ollama -- nvidia-smi

# Use smaller models
kubectl exec -n slate deploy/ollama -- ollama pull phi:latest

# Increase memory limit in values.yaml
ollama:
  resources:
    limits:
      memory: 24Gi
```

### Logs

```bash
# Dashboard logs
kubectl logs -n slate -l app.kubernetes.io/component=dashboard -f

# Ollama logs
kubectl logs -n slate deploy/ollama -f

# All SLATE logs
kubectl logs -n slate -l app.kubernetes.io/part-of=slate-system -f --max-log-requests=10

# Previous container logs (after crash)
kubectl logs -n slate deploy/slate-dashboard --previous
```

### Reset Deployment

```bash
# Delete and recreate namespace
kubectl delete namespace slate
kubectl apply -k k8s/

# Or just restart deployments
kubectl rollout restart deployment -n slate --all
```

---

## Related Pages

- [Architecture](Architecture) - System design and components
- [Getting Started](Getting-Started) - Initial setup guide
- [AI Backends](AI-Backends) - Ollama and Foundry Local configuration
- [Troubleshooting](Troubleshooting) - General troubleshooting guide
- [CLI Reference](CLI-Reference) - Command-line tools
- [Configuration](Configuration) - Environment variables and settings

---

## Quick Reference

```bash
# Deploy
.\k8s\deploy.ps1 -Environment local           # Windows
kubectl apply -k k8s/                          # Base
kubectl apply -k k8s/overlays/local/           # Local overlay

# Status
kubectl get pods -n slate
kubectl get svc -n slate
kubectl top pods -n slate

# Access
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080

# Logs
kubectl logs -n slate deploy/slate-dashboard -f

# Cleanup
kubectl delete namespace slate
```
