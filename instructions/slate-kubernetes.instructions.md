---
name: slate-kubernetes
description: 'Best practices for SLATE Kubernetes manifests and Helm charts'
applyTo: 'k8s/**/*.yaml, helm/**/*.yaml, helm/**/*.tpl'
tags: [kubernetes, helm, infrastructure, slate]
---

# SLATE Kubernetes Standards

These instructions apply to all Kubernetes manifests and Helm charts in SLATE.

## Namespace

All SLATE resources deploy to the `slate` namespace:

```yaml
metadata:
  namespace: slate
```

## Labels (Required)

All resources must include standard labels:

```yaml
metadata:
  labels:
    app.kubernetes.io/name: slate-dashboard
    app.kubernetes.io/component: dashboard
    app.kubernetes.io/part-of: slate
    app.kubernetes.io/managed-by: kustomize  # or helm
```

## Resource Limits

All containers must specify resource limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

For GPU workloads:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1  # Request GPU
```

## Security Context

All pods should run with security best practices:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

## Network Binding

**NEVER use 0.0.0.0** in containers — use 127.0.0.1 or let K8s handle networking:

```yaml
# CORRECT
env:
  - name: HOST
    value: "0.0.0.0"  # OK in K8s - ClusterIP handles exposure

# Container command should bind to all interfaces for K8s Service discovery
command: ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

Note: In K8s, binding to 0.0.0.0 inside a pod is safe because NetworkPolicy controls access.

## Service Ports

Standard SLATE service ports:

| Service | Port | Purpose |
|---------|------|---------|
| Dashboard | 8080 | FastAPI dashboard |
| Agent Router | 8081 | Task classification |
| Autonomous Loop | 8082 | Autonomous execution |
| Copilot Bridge | 8083 | VS Code extension bridge |
| Workflow Manager | 8084 | Task lifecycle |
| Instruction API | 8085 | Adaptive instructions |
| Metrics | 9090 | Prometheus scrape |
| Ollama | 11434 | LLM inference |
| ChromaDB | 8000 | Vector store |

## Health Checks

All deployments must include health probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

## ConfigMaps for Instructions

The adaptive instruction layer uses ConfigMaps:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: slate-instructions
  namespace: slate
data:
  active-state.yaml: |
    mode: NORMAL
    agentAvailability: full
  instruction-block.md: |
    # SLATE Operating Instructions
    ...
```

## Kustomize Overlays

Use overlays for environment-specific configuration:

```
k8s/
├── base/                    # Base manifests
├── overlays/
│   ├── local/              # Minikube/kind
│   ├── dev/                # Development cluster
│   └── prod/               # Production cluster
└── kustomization.yaml
```

## GPU Node Affinity

For GPU workloads, use node affinity:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: nvidia.com/gpu.present
              operator: In
              values:
                - "true"
```

## Secrets Management

Never hardcode secrets. Use Kubernetes Secrets:

```yaml
env:
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: slate-secrets
        key: github-token
```
