# Specification: Kubernetes Infrastructure
<!-- Auto-generated from specs/018-kubernetes-infrastructure/spec.md -->
<!-- Generated: 2026-02-09T09:07:03.007079+00:00 -->

| Property | Value |
|----------|-------|
| **Spec Id** | 018-kubernetes-infrastructure |
| **Status** | complete |
| **Created** | 2026-02-08 |
| **Author** | Claude Opus 4.5 |
| **Depends On** | core-sdk, docker-infra, dashboard |

## Contents

- [Overview](#overview)
- [Tech Tree Reference](#tech-tree-reference)
- [System Architecture](#system-architecture)
  - [High-Level Overview](#high-level-overview)
  - [Deployment Summary](#deployment-summary)
- [Namespace and RBAC](#namespace-and-rbac)
  - [Namespace Configuration](#namespace-configuration)
  - [Service Accounts](#service-accounts)
  - [RBAC Role Hierarchy](#rbac-role-hierarchy)
- [Service Mesh and Networking](#service-mesh-and-networking)
  - [Service Architecture](#service-architecture)
  - [Services Summary](#services-summary)
  - [Network Policies](#network-policies)
- [Ingress and Access](#ingress-and-access)
  - [Ingress Configuration](#ingress-configuration)
  - [Port Forwarding Access](#port-forwarding-access)
- [GPU Scheduling and Resources](#gpu-scheduling-and-resources)
  - [NVIDIA Device Plugin](#nvidia-device-plugin)
  - [Resource Quotas](#resource-quotas)
  - [LimitRange Defaults](#limitrange-defaults)
  - [Priority Classes](#priority-classes)
- [Persistent Storage](#persistent-storage)
  - [PersistentVolumeClaims](#persistentvolumeclaims)
  - [Storage Summary](#storage-summary)
- [Auto-Scaling and High Availability](#auto-scaling-and-high-availability)
  - [Horizontal Pod Autoscalers](#horizontal-pod-autoscalers)
  - [PodDisruptionBudgets](#poddisruptionbudgets)
  - [Topology Spread](#topology-spread)
- [ML Pipeline and CronJobs](#ml-pipeline-and-cronjobs)
  - [CronJob Schedule](#cronjob-schedule)
  - [CronJob Details](#cronjob-details)
  - [Model Preload Job](#model-preload-job)
  - [Custom Model Definitions](#custom-model-definitions)
- [Helm Chart Integration](#helm-chart-integration)
  - [Chart Structure](#chart-structure)
  - [Deployment Methods](#deployment-methods)
  - [Kustomization Base](#kustomization-base)
- [K8s Entrypoints](#k8s-entrypoints)
  - [Service Entrypoint Module](#service-entrypoint-module)
  - [K8s Integration Module](#k8s-integration-module)
- [Configuration Management](#configuration-management)
  - [ConfigMaps](#configmaps)
  - [Secrets](#secrets)
- [Monitoring and Observability](#monitoring-and-observability)
  - [Metrics Endpoints](#metrics-endpoints)
  - [Health Probes](#health-probes)
- [Security Context](#security-context)
  - [Pod Security Standards](#pod-security-standards)
- [File Reference](#file-reference)
  - [K8s Manifests](#k8s-manifests)
  - [Python Modules](#python-modules)
- [Quick Reference](#quick-reference)
  - [Deployment Commands](#deployment-commands)
  - [Troubleshooting](#troubleshooting)
- [Success Criteria](#success-criteria)

---

## Overview

This specification documents the **Kubernetes Infrastructure** for SLATE deployment. SLATE runs as a complete containerized local cloud in Kubernetes, providing isolated microservices with full integration, GPU scheduling, network isolation, and automated ML training pipelines.

The K8s infrastructure enables:
- **Local Cloud Experience**: Run the entire SLATE system on local hardware with cloud-grade orchestration
- **GPU Scheduling**: Dual-GPU workload distribution via NVIDIA device plugin
- **Network Isolation**: Zero-trust networking with policy-enforced service communication
- **Auto-Scaling**: Horizontal Pod Autoscaling based on CPU/memory utilization
- **ML Pipeline Automation**: CronJobs for model training, codebase indexing, and health monitoring
- **High Availability**: PodDisruptionBudgets and topology spread for resilience

## Tech Tree Reference

```yaml
id: k8s-infra
name: Kubernetes Infrastructure
status: complete
phase: 2
description: "Kubernetes manifests for SLATE deployment - namespace, RBAC, deployments, network policies, dashboard service discovery"
paths:
  - k8s/
  - slate/k8s_entrypoints.py
  - slate/k8s_integration.py
```

## System Architecture

### High-Level Overview

```
+=====================================================================+
|                    SLATE KUBERNETES ARCHITECTURE                     |
+=====================================================================+

  +-------------------------------------------------------------------+
  |                    INGRESS (slate.local)                          |
  |   nginx-ingress-controller with WebSocket support                 |
  +-----------------------------------+-------------------------------+
                                      |
                                      v
  +-------------------------------------------------------------------+
  |                       SLATE NAMESPACE                              |
  |                                                                    |
  |  +-----------------------+    +-----------------------+            |
  |  |   SLATE DASHBOARD     |    |    AGENT ROUTER       |            |
  |  |   (HPA 2-6 replicas)  |    |    (2 replicas)       |            |
  |  |   Port: 8080          |    |    Port: 8081         |            |
  |  +-----------+-----------+    +-----------+-----------+            |
  |              |                            |                        |
  |              +-------------+--------------+                        |
  |                            |                                       |
  |              +-------------v--------------+                        |
  |              |                            |                        |
  |  +-----------v-----------+  +-------------v-----------+            |
  |  |  AUTONOMOUS LOOP      |  |   WORKFLOW MANAGER      |            |
  |  |  (1 replica + GPU)    |  |   (1 replica)           |            |
  |  |  Port: 8082           |  |   Port: 8084            |            |
  |  +-----------+-----------+  +-------------+-----------+            |
  |              |                            |                        |
  |              +-------------+--------------+                        |
  |                            |                                       |
  |  +-------------------------v--------------------------+            |
  |  |              COPILOT BRIDGE                        |            |
  |  |              (1 replica)                           |            |
  |  |              Port: 8083                            |            |
  |  +----------------------------------------------------+            |
  |                                                                    |
  |  +-------------------+  +-------------------+  +----------------+  |
  |  |    OLLAMA         |  |    CHROMADB       |  | GITHUB RUNNER  |  |
  |  |    (GPU)          |  |    (Vector DB)    |  | (GPU, ARC)     |  |
  |  |    Port: 11434    |  |    Port: 8000     |  | N/A            |  |
  |  +-------------------+  +-------------------+  +----------------+  |
  |                                                                    |
  +-------------------------------------------------------------------+
```

### Deployment Summary

| Component | Deployment | Replicas | Port | GPU | HPA |
|-----------|------------|----------|------|-----|-----|
| Dashboard | slate-dashboard | 2 (HPA: 2-6) | 8080 | No | Yes |
| Agent Router | slate-agent-router | 2 | 8081, 9090 | No | No |
| Autonomous Loop | slate-autonomous-loop | 1 | 8082 | Optional | No |
| Copilot Bridge | slate-copilot-bridge | 1 | 8083 | No | No |
| Workflow Manager | slate-workflow-manager | 1 | 8084 | No | No |
| Ollama | ollama | 1 | 11434 | Yes | No |
| ChromaDB | chromadb | 1 (HPA: 1-3) | 8000 | No | Yes |

**Total: 7 Deployments, 9+ Pods**

## Namespace and RBAC

### Namespace Configuration

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: slate
  labels:
    app.kubernetes.io/name: slate
    app.kubernetes.io/part-of: slate-system
    # Pod Security Standards
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Service Accounts

```
+========================================+
|          SERVICE ACCOUNTS              |
+========================================+

  +------------------+     +------------------+     +------------------+
  |   slate-core     |     |   slate-agent    |     |   slate-runner   |
  |                  |     |                  |     |                  |
  | Used by:         |     | Used by:         |     | Used by:         |
  | - Dashboard      |     | - Ollama         |     | - GitHub Runner  |
  | - Agent Router   |     | - ChromaDB       |     |                  |
  | - Autonomous     |     | - ML Jobs        |     | Permissions:     |
  | - Workflow Mgr   |     |                  |     | - pods/log       |
  |                  |     | Permissions:     |     | - configmaps     |
  | Permissions:     |     | - pods (read)    |     | - secrets (read) |
  | - pods (read)    |     | - services       |     | - batch/jobs     |
  | - configmaps     |     | - configmaps     |     |                  |
  | - services       |     | - deployments    |     |                  |
  | - deployments    |     |                  |     |                  |
  | - batch/jobs     |     |                  |     |                  |
  | - events         |     |                  |     |                  |
  +------------------+     +------------------+     +------------------+
```

### RBAC Role Hierarchy

```
+=====================================================================+
|                         RBAC STRUCTURE                               |
+=====================================================================+

                    +---------------------------+
                    |    ClusterRole:           |
                    |    slate-deny-all         |
                    |    (Empty - no cluster    |
                    |     permissions)          |
                    +---------------------------+

  +------------------------+              +------------------------+
  |    Role:               |              |    Role:               |
  |    slate-core-role     |              |    slate-agent-role    |
  |                        |              |                        |
  | Resources:             |              | Resources:             |
  | - pods/log/status (R)  |              | - pods (R)             |
  | - configmaps (RWC)     |              | - services (R)         |
  | - secrets (R)          |              | - configmaps (R)       |
  | - services (R)         |              | - deployments (R)      |
  | - deployments (R)      |              |                        |
  | - batch/jobs (RWC)     |              |                        |
  | - events (R)           |              |                        |
  +------------------------+              +------------------------+
          |                                        |
          v                                        v
  +------------------------+              +------------------------+
  | RoleBinding:           |              | RoleBinding:           |
  | slate-core-binding     |              | slate-agent-binding    |
  |                        |              |                        |
  | SA: slate-core         |              | SA: slate-agent        |
  +------------------------+              +------------------------+
```

**Key Principles:**
- **Least Privilege**: Each service account has only the permissions it needs
- **No Cluster Admin**: SLATE agents NEVER have cluster-wide access
- **Read-Only for Agents**: Agent role is strictly read-only
- **No Secret Creation**: Secrets are managed externally (sealed-secrets/external-secrets)

## Service Mesh and Networking

### Service Architecture

```
+=====================================================================+
|                    SERVICE MESH TOPOLOGY                             |
+=====================================================================+

                         +-------------------+
                         |   slate-ingress   |
                         |   (nginx)         |
                         +---------+---------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+------------------+     +------------------+     +------------------+
| slate-dashboard  |     | slate-agent-     |     | slate-autonomous |
| -svc             |     | router-svc       |     | -svc             |
| Port: 8080       |     | Port: 8081/9090  |     | Port: 8082       |
+--------+---------+     +--------+---------+     +--------+---------+
         |                         |                         |
         +------------+------------+------------+------------+
                      |                         |
                      v                         v
         +-------------------+       +-------------------+
         | ollama-svc        |       | chromadb-svc      |
         | Port: 11434       |       | Port: 8000        |
         | ClusterIP         |       | ClusterIP         |
         +-------------------+       +-------------------+
```

### Services Summary

| Service | Type | Port(s) | Selector |
|---------|------|---------|----------|
| slate-dashboard-svc | ClusterIP | 8080 | app.kubernetes.io/component: dashboard |
| slate-agent-router-svc | ClusterIP | 8081, 9090 | app.kubernetes.io/component: agent-router |
| slate-autonomous-svc | ClusterIP | 8082 | app.kubernetes.io/component: autonomous-loop |
| slate-copilot-bridge-svc | ClusterIP | 8083 | app.kubernetes.io/component: copilot-bridge |
| slate-workflow-svc | ClusterIP | 8084 | app.kubernetes.io/component: workflow-manager |
| ollama-svc | ClusterIP | 11434 | app.kubernetes.io/component: ollama |
| chromadb-svc | ClusterIP | 8000 | app.kubernetes.io/name: chromadb |
| slate-metrics-svc | ClusterIP | 9090 | app.kubernetes.io/component: agent-router |

### Network Policies

```
+=====================================================================+
|                    NETWORK POLICY STRUCTURE                          |
+=====================================================================+

  +-------------------------------------------------------------------+
  |                   default-deny-all                                 |
  |   All ingress/egress DENIED by default for all pods               |
  +-------------------------------------------------------------------+

           |                    |                    |
           v                    v                    v

  +------------------+  +------------------+  +------------------+
  | allow-intra-     |  | allow-dashboard- |  | allow-github-    |
  | slate            |  | ingress          |  | egress           |
  |                  |  |                  |  |                  |
  | Allows:          |  | Allows:          |  | Allows:          |
  | - Pod-to-pod     |  | - NodePort/      |  | - HTTPS to       |
  |   within slate   |  |   port-forward   |  |   GitHub API     |
  |   namespace      |  |   on :8080       |  |   CIDRs only     |
  | - DNS to         |  |                  |  | - DNS to         |
  |   kube-system    |  |                  |  |   kube-system    |
  +------------------+  +------------------+  +------------------+

  +------------------+  +------------------+  +------------------+
  | allow-ollama-    |  | allow-chromadb-  |  | allow-ingress-   |
  | from-slate       |  | from-slate       |  | to-services      |
  |                  |  |                  |  |                  |
  | Allows:          |  | Allows:          |  | Allows:          |
  | - Ingress from   |  | - Ingress from   |  | - From nginx-    |
  |   slate-system   |  |   slate-system   |  |   ingress ns     |
  |   pods on :11434 |  |   pods on :8000  |  |   to all SLATE   |
  | - NO external    |  | - NO external    |  |   service ports  |
  |   egress         |  |   egress         |  |                  |
  +------------------+  +------------------+  +------------------+
```

**Security Principles:**
- **Default Deny**: All traffic blocked unless explicitly allowed
- **Namespace Isolation**: Only slate namespace pods can communicate
- **No External Egress**: Ollama/ChromaDB cannot reach the internet
- **GitHub API Only**: Core services can only reach GitHub API CIDRs (for CI/CD)
- **DNS Scoped**: DNS queries only to kube-system CoreDNS

## Ingress and Access

### Ingress Configuration

```
+=====================================================================+
|                       INGRESS ROUTING                                |
+=====================================================================+

  Host: slate.local
  IngressClass: nginx

  +----------------------------+-------------------------------------+
  | Path                       | Backend                             |
  +----------------------------+-------------------------------------+
  | /                          | slate-dashboard-svc:8080            |
  | /ws                        | slate-dashboard-svc:8080 (WebSocket)|
  | /api/k8s                   | slate-dashboard-svc:8080            |
  | /api/agents                | slate-agent-router-svc:8081         |
  | /api/autonomous            | slate-autonomous-svc:8082           |
  | /api/bridge                | slate-copilot-bridge-svc:8083       |
  | /api/workflow              | slate-workflow-svc:8084             |
  | /metrics                   | slate-metrics-svc:9090              |
  +----------------------------+-------------------------------------+

  Annotations:
  - ssl-redirect: false (local only)
  - proxy-body-size: 50m
  - proxy-read/send-timeout: 3600 (for WebSocket)
  - limit-connections: 20
  - limit-rps: 50
```

### Port Forwarding Access

```bash
# Dashboard Access (Primary)
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
# Open: http://localhost:8080

# Ollama Direct Access
kubectl port-forward -n slate svc/ollama-svc 11434:11434

# ChromaDB Direct Access
kubectl port-forward -n slate svc/chromadb-svc 8000:8000

# Agent Router (for debugging)
kubectl port-forward -n slate svc/slate-agent-router-svc 8081:8081
```

## GPU Scheduling and Resources

### NVIDIA Device Plugin

```
+=====================================================================+
|                    GPU INFRASTRUCTURE                                |
+=====================================================================+

  +-------------------------------------------------------------------+
  |                   NVIDIA Device Plugin DaemonSet                   |
  |   Namespace: kube-system                                          |
  |   Image: nvcr.io/nvidia/k8s-device-plugin:v0.16.2                 |
  +-------------------------------------------------------------------+
         |
         v
  +-------------------------------------------------------------------+
  |                        GPU NODE                                    |
  |   Capacity: nvidia.com/gpu: 2                                     |
  |   Architecture: Blackwell (RTX 5070 Ti)                           |
  +-------------------------------------------------------------------+
         |
         +---------------------------+---------------------------+
         |                           |                           |
         v                           v                           v
  +---------------+         +---------------+         +---------------+
  |    GPU 0      |         |    GPU 1      |         |   Reserved    |
  |               |         |               |         |               |
  | Ollama        |         | Autonomous    |         | (spillover)   |
  | (Primary)     |         | Loop          |         |               |
  |               |         |               |         |               |
  | 16GB VRAM     |         | 16GB VRAM     |         |               |
  +---------------+         +---------------+         +---------------+
```

### Resource Quotas

```yaml
# GPU Resource Quota for slate namespace
requests.nvidia.com/gpu: "2"
limits.nvidia.com/gpu: "2"
requests.cpu: "16"
limits.cpu: "32"
requests.memory: "48Gi"
limits.memory: "96Gi"
pods: "20"
```

### LimitRange Defaults

```yaml
# Default container resources
default:
  cpu: 500m
  memory: 1Gi
defaultRequest:
  cpu: 100m
  memory: 256Mi
max:
  cpu: "8"
  memory: 32Gi
min:
  cpu: 50m
  memory: 64Mi
```

### Priority Classes

| Priority Class | Value | Description |
|----------------|-------|-------------|
| slate-gpu-priority | 1000 | GPU workloads (Ollama, training, autonomous) |
| slate-standard-priority | 500 | Standard workloads (router, workflow, bridge) |

## Persistent Storage

### PersistentVolumeClaims

```
+=====================================================================+
|                    PERSISTENT STORAGE                                |
+=====================================================================+

  +-------------------+     +-------------------+     +-------------------+
  | slate-workspace   |     | slate-data-pvc    |     | ollama-data-pvc   |
  | -pvc              |     |                   |     |                   |
  |                   |     | Storage: 5Gi      |     | Storage: 20Gi     |
  | Storage: 10Gi     |     | Access: RWO       |     | Access: RWO       |
  | Access: RWO       |     |                   |     |                   |
  |                   |     | Used by:          |     | Used by:          |
  | Used by:          |     | - Agent Router    |     | - Ollama          |
  | - Dashboard       |     | - Autonomous      |     |   (/root/.ollama) |
  | - Agent Router    |     | - Workflow Mgr    |     |                   |
  | - Autonomous      |     |                   |     |                   |
  | - Workflow Mgr    |     |                   |     |                   |
  | - Copilot Bridge  |     |                   |     |                   |
  +-------------------+     +-------------------+     +-------------------+

  +-------------------+     +-------------------+
  | chroma-data-pvc   |     | slate-memory-pvc  |
  |                   |     |                   |
  | Storage: 5Gi      |     | Storage: 2Gi      |
  | Access: RWO       |     | Access: RWO       |
  |                   |     |                   |
  | Used by:          |     | Used by:          |
  | - ChromaDB        |     | - Autonomous Loop |
  |   (/chroma/chroma)|     |   (state memory)  |
  +-------------------+     +-------------------+
```

### Storage Summary

| PVC | Size | Access | Purpose |
|-----|------|--------|---------|
| slate-workspace-pvc | 10Gi | RWO | SLATE codebase and workspace |
| slate-data-pvc | 5Gi | RWO | ChromaDB index, task data |
| ollama-data-pvc | 20Gi | RWO | Ollama models and cache |
| chroma-data-pvc | 5Gi | RWO | ChromaDB persistent store |
| slate-memory-pvc | 2Gi | RWO | Autonomous loop state |

## Auto-Scaling and High Availability

### Horizontal Pod Autoscalers

```
+=====================================================================+
|                    AUTO-SCALING CONFIGURATION                        |
+=====================================================================+

  +-------------------------------------------------------------------+
  |                    slate-dashboard-hpa                             |
  +-------------------------------------------------------------------+
  | Target: slate-dashboard                                           |
  | Min: 2  |  Max: 6                                                 |
  | Metrics:                                                          |
  |   - CPU: 70% utilization                                          |
  |   - Memory: 80% utilization                                       |
  | Behavior:                                                         |
  |   - Scale Up: +2 pods per 60s (stabilize 60s)                     |
  |   - Scale Down: -1 pod per 120s (stabilize 300s)                  |
  +-------------------------------------------------------------------+

  +-------------------------------------------------------------------+
  |                    slate-core-hpa                                  |
  +-------------------------------------------------------------------+
  | Target: slate-core                                                |
  | Min: 2  |  Max: 10                                                |
  | Metrics:                                                          |
  |   - CPU: 70% utilization                                          |
  |   - Memory: 80% utilization                                       |
  +-------------------------------------------------------------------+

  +-------------------------------------------------------------------+
  |                    chromadb-hpa                                    |
  +-------------------------------------------------------------------+
  | Target: chromadb                                                  |
  | Min: 1  |  Max: 3                                                 |
  | Metrics:                                                          |
  |   - CPU: 75% utilization                                          |
  |   - Memory: 80% utilization                                       |
  +-------------------------------------------------------------------+
```

### PodDisruptionBudgets

```yaml
# Dashboard PDB
minAvailable: 1
selector: app.kubernetes.io/name: slate-dashboard

# Core PDB
minAvailable: 1
selector: app.kubernetes.io/component: core

# Ollama PDB
minAvailable: 1
selector: app.kubernetes.io/component: ollama
```

### Topology Spread

Dashboard pods use topology spread constraints to distribute across nodes:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: slate-dashboard
```

## ML Pipeline and CronJobs

### CronJob Schedule

```
+=====================================================================+
|                    ML PIPELINE CRONJOBS                              |
+=====================================================================+

  SCHEDULE OVERVIEW (UTC)
  ========================

  00:00  01:00  02:00  03:00  04:00  05:00  06:00  ...  every 4h
    |      |      |      |      |      |      |         |
    v      |      v      v      |      |      v         v
  +-----+  |  +-----+ +-----+   |      |  +-----+   +-------+
  |NIGHT|  |  |INDEX| |TRAIN|   |      |  |BENCH|   |CLEANUP|
  |HLTH |  |  |     | |     |   |      |  |     |   |       |
  +-----+  |  +-----+ +-----+   |      |  +-----+   +-------+
           |                    |      |
           |                    |      v
           |                    |  (Weekly: Sunday)
           |                    |  +----------+
           |                    |  |AI TRAIN  |
           |                    |  +----------+
           |                    |
           v
  (Every 4 hours)
  +---------------+
  |WORKFLOW       |
  |CLEANUP        |
  +---------------+
```

### CronJob Details

| CronJob | Schedule | Purpose | Deadline |
|---------|----------|---------|----------|
| slate-nightly-health | 0 0 * * * | Full system health check | 10m |
| slate-codebase-indexer | 0 2 * * * | ChromaDB codebase indexing | 2h |
| slate-model-trainer | 0 3 * * 0 | Weekly model retraining | 2h |
| slate-inference-benchmarks | 0 6 * * 0 | GPU inference benchmarks | 1h |
| slate-workflow-cleanup | 0 */4 * * * | Stale task cleanup | 5m |

### Model Preload Job

A one-time Job runs after Ollama starts to preload SLATE custom models:

```
+-------------------------------------------------------------------+
|                    slate-model-preload (Job)                       |
+-------------------------------------------------------------------+
| TTL: 3600s (auto-cleanup after 1h)                                |
| Backoff: 3 retries                                                |
|                                                                   |
| Init Container: wait-for-ollama                                   |
|   - Polls http://ollama-svc:11434/api/tags                        |
|   - Timeout: 5 minutes                                            |
|                                                                   |
| Main Container: model-preloader                                   |
|   - Checks existing models                                        |
|   - Pulls: slate-coder, slate-fast, slate-planner                 |
+-------------------------------------------------------------------+
```

### Custom Model Definitions

```yaml
# Modelfile.slate-coder (12B, mistral-nemo base)
FROM mistral-nemo
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
SYSTEM "You are SLATE-Coder..."

# Modelfile.slate-fast (3B, llama3.2 base)
FROM llama3.2
PARAMETER temperature 0.2
PARAMETER top_p 0.8
PARAMETER num_ctx 4096
SYSTEM "You are SLATE-Fast..."

# Modelfile.slate-planner (7B, mistral base)
FROM mistral
PARAMETER temperature 0.4
PARAMETER top_p 0.85
PARAMETER num_ctx 8192
SYSTEM "You are SLATE-Planner..."
```

## Helm Chart Integration

### Chart Structure

```
helm/
+-- Chart.yaml               # Main chart metadata
+-- values.yaml              # Default configuration
+-- slate/                   # Subchart (deprecated)
+-- templates/
    +-- _helpers.tpl         # Template helpers
    +-- core.yaml            # Core deployment
    +-- dashboard.yaml       # Dashboard deployment
    +-- ollama.yaml          # Ollama deployment
    +-- chromadb.yaml        # ChromaDB deployment
    +-- agentic-system.yaml  # Agent deployments
    +-- ml-pipeline.yaml     # ML CronJobs
    +-- runners.yaml         # GitHub runners
    +-- rbac-security.yaml   # RBAC and security
    +-- monitoring.yaml      # Prometheus ServiceMonitors
```

### Deployment Methods

```bash
# Kustomize (Recommended for local)
kubectl apply -k k8s/

# Environment-specific overlays
kubectl apply -k k8s/overlays/local/    # Minikube/kind
kubectl apply -k k8s/overlays/dev/      # Development
kubectl apply -k k8s/overlays/staging/  # Staging
kubectl apply -k k8s/overlays/prod/     # Production

# Helm
helm install slate ./helm -n slate --create-namespace
helm upgrade slate ./helm -n slate -f custom-values.yaml

# Optional CRD-dependent resources (apply after CRD installation)
kubectl apply -f k8s/runners-arc.yaml        # Actions Runner Controller
kubectl apply -f k8s/monitoring-crds.yaml    # Prometheus Operator
```

### Kustomization Base

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: slate

resources:
  - namespace.yaml
  - rbac.yaml
  - network-policy.yaml
  - storage.yaml
  - secrets.yaml
  - slate-instructions.yaml
  - instruction-controller.yaml
  - deployments.yaml
  - slate-dashboard.yaml
  - hpa-monitoring.yaml
  - pdb.yaml
  - agentic-system.yaml
  - ml-pipeline.yaml
  - runners.yaml
  - ingress-gpu.yaml

labels:
  - pairs:
      app.kubernetes.io/managed-by: slate
      app.kubernetes.io/version: "2.4.0"
      slate.io/security-policy: restricted
      slate.io/network-policy: deny-all-default
    includeSelectors: false
```

## K8s Entrypoints

### Service Entrypoint Module

The `slate/k8s_entrypoints.py` module provides container entrypoints for each SLATE service:

```python
# Usage in K8s deployment
command: ["python", "slate/k8s_entrypoints.py", "--service", "<name>"]

# Available services:
# - core:           SLATE status API (8080)
# - agent-router:   Task classification and routing (8081, 9090)
# - autonomous:     Task discovery and execution loop (8082)
# - workflow:       Task lifecycle management (8084)
# - dashboard:      FastAPI dashboard server (8080)
```

### K8s Integration Module

The `slate/k8s_integration.py` module provides:

- **Service Discovery**: Automatic K8s DNS-based service URLs
- **Health Monitoring**: Concurrent health checks for all services
- **Cluster Introspection**: kubectl-based deployment/pod/cronjob status
- **GPU Detection**: NVIDIA device plugin and GPU node detection
- **ConfigMap Reading**: Mounted volume ConfigMap access

```python
from slate.k8s_integration import get_k8s_integration

k8s = get_k8s_integration()

# Check if running in K8s
if k8s.is_k8s_environment():
    # Get all service health
    health = await k8s.check_all_services()

    # Get cluster status via kubectl
    cluster = k8s.get_cluster_status()

    # Read adaptive instructions from ConfigMap
    instructions = k8s.get_instruction_state()
```

## Configuration Management

### ConfigMaps

| ConfigMap | Purpose | Keys |
|-----------|---------|------|
| slate-dashboard-config | Dashboard environment | OLLAMA_HOST, CHROMADB_HOST, feature flags |
| slate-dashboard-entrypoint | Dashboard startup script | start-dashboard.py |
| slate-agent-config | Agent routing rules | agent-routing.yaml, models.yaml |
| slate-instructions | Adaptive agent instructions | active-state.yaml, copilot-rules.yaml |
| slate-model-files | Ollama Modelfile definitions | Modelfile.slate-* |
| slate-tech-tree | Tech tree state | tech_tree.json |

### Secrets

| Secret | Purpose | Keys |
|--------|---------|------|
| slate-github-secret | GitHub API access | token |
| slate-github-credentials | GitHub workflow dispatch | GITHUB_TOKEN |

## Monitoring and Observability

### Metrics Endpoints

```
+=====================================================================+
|                    PROMETHEUS METRICS                                |
+=====================================================================+

  Scrape Targets:
  +-------------------------------------------------------------------+
  | Service                  | Port | Path     | Labels              |
  +-------------------------------------------------------------------+
  | slate-dashboard          | 8080 | /metrics | component=dashboard |
  | slate-agent-router       | 9090 | /metrics | component=router    |
  | slate-metrics-svc        | 9090 | /metrics | (aggregated)        |
  +-------------------------------------------------------------------+

  Annotations (on pods):
    prometheus.io/scrape: "true"
    prometheus.io/port: "<port>"
    prometheus.io/path: "/metrics"
```

### Health Probes

All deployments include standardized health probes:

```yaml
# Startup Probe (for slow-starting containers)
startupProbe:
  httpGet:
    path: /health
    port: <port>
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30

# Liveness Probe
livenessProbe:
  httpGet:
    path: /health
    port: <port>
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10

# Readiness Probe
readinessProbe:
  httpGet:
    path: /health
    port: <port>
  initialDelaySeconds: 5
  periodSeconds: 10
  successThreshold: 1
```

## Security Context

### Pod Security Standards

All SLATE pods enforce the following security context:

```yaml
# Pod-level
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

# Container-level
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false  # Required for state files
  capabilities:
    drop:
      - ALL
```

**Exceptions:**
- Ollama: `runAsNonRoot: false` (requires root for model storage)
- ChromaDB: `runAsNonRoot: false` (image runs as root)

## File Reference

### K8s Manifests

| File | Purpose |
|------|---------|
| `k8s/namespace.yaml` | SLATE namespace with PSS labels |
| `k8s/rbac.yaml` | ServiceAccounts, Roles, RoleBindings |
| `k8s/network-policy.yaml` | NetworkPolicies for isolation |
| `k8s/storage.yaml` | PersistentVolumeClaims |
| `k8s/secrets.yaml` | Secret definitions |
| `k8s/deployments.yaml` | Core, Ollama, ChromaDB deployments |
| `k8s/slate-dashboard.yaml` | Full dashboard deployment + HPA + PDB |
| `k8s/agentic-system.yaml` | Agent router, autonomous, bridge, workflow |
| `k8s/ml-pipeline.yaml` | CronJobs and model ConfigMaps |
| `k8s/runners.yaml` | GitHub Actions runner RBAC |
| `k8s/runners-arc.yaml` | Actions Runner Controller CRDs |
| `k8s/ingress-gpu.yaml` | Ingress, GPU plugin, quotas, priority |
| `k8s/hpa-monitoring.yaml` | HPA definitions, metrics service |
| `k8s/pdb.yaml` | PodDisruptionBudgets |
| `k8s/kustomization.yaml` | Kustomize base configuration |

### Python Modules

| File | Purpose |
|------|---------|
| `slate/k8s_entrypoints.py` | Container entrypoints for SLATE services |
| `slate/k8s_integration.py` | K8s service discovery and cluster introspection |

## Quick Reference

### Deployment Commands

```bash
# Deploy to local K8s
kubectl apply -k k8s/

# Check deployment status
kubectl get all -n slate

# Watch pods
kubectl get pods -n slate -w

# Check logs
kubectl logs -n slate deployment/slate-dashboard

# Port forward dashboard
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080

# Scale deployment
kubectl scale -n slate deployment/slate-dashboard --replicas=3

# Restart deployment
kubectl rollout restart -n slate deployment/slate-dashboard

# Check rollout status
kubectl rollout status -n slate deployment/slate-dashboard
```

### Troubleshooting

```bash
# Check events
kubectl get events -n slate --sort-by='.lastTimestamp'

# Describe failing pod
kubectl describe pod -n slate <pod-name>

# Check network policies
kubectl get networkpolicy -n slate

# Check PVCs
kubectl get pvc -n slate

# Check HPA status
kubectl get hpa -n slate

# Check resource usage
kubectl top pods -n slate
```

## Success Criteria

1. **All 7 deployments running**: slate-dashboard, slate-agent-router, slate-autonomous-loop, slate-copilot-bridge, slate-workflow-manager, ollama, chromadb
2. **Network isolation enforced**: Only allowed traffic flows between pods
3. **GPU scheduling operational**: Ollama and autonomous loop can request GPUs
4. **Auto-scaling functional**: Dashboard scales between 2-6 replicas
5. **CronJobs executing**: Nightly health, indexing, training jobs complete
6. **Health probes passing**: All deployments report healthy
7. **PVCs bound**: All storage claims provisioned
8. **Ingress routing**: All paths route to correct services

---

**Theme Lock Declaration:**

```
+===============================================================+
|          K8S INFRASTRUCTURE SPECIFICATION LOCK                 |
+===============================================================+
|                                                               |
|  Version: 2.4.0                                               |
|  Status: LOCKED                                               |
|  Date: 2026-02-08                                             |
|                                                               |
|  The following are immutable:                                 |
|  - Namespace name (slate)                                     |
|  - Service account names                                      |
|  - Network policy deny-all default                            |
|  - Service port assignments                                   |
|  - Security context requirements                              |
|                                                               |
|  Additive improvements only. No breaking changes.             |
|                                                               |
+===============================================================+
```

---
*Source: [specs/018-kubernetes-infrastructure/spec.md](../../../specs/018-kubernetes-infrastructure/spec.md)*
