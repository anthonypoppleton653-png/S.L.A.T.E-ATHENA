# Specification: Dual-GPU Manager
<!-- Auto-generated from specs/019-dual-gpu-manager/spec.md -->
<!-- Generated: 2026-02-09T09:07:03.026446+00:00 -->

| Property | Value |
|----------|-------|
| **Spec Id** | 019-dual-gpu-manager |
| **Status** | complete |
| **Created** | 2026-02-08 |
| **Author** | Claude Opus 4.5 |
| **Depends On** | 012-watchmaker-3d-dashboard (GPU Workbench visualization) |

## Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [GPU-to-Model Assignment](#gpu-to-model-assignment)
  - [Model Placement Strategy](#model-placement-strategy)
- [Load Balancing Algorithm](#load-balancing-algorithm)
  - [Memory-Aware Scheduling](#memory-aware-scheduling)
  - [GPU Utilization Balancing](#gpu-utilization-balancing)
- [Warmup System](#warmup-system)
  - [Warmup Sequence](#warmup-sequence)
  - [Keep-Alive Configuration](#keep-alive-configuration)
  - [Warmup State Persistence](#warmup-state-persistence)
- [Memory Management](#memory-management)
  - [VRAM Allocation Strategy](#vram-allocation-strategy)
  - [Eviction Policy](#eviction-policy)
- [CUDA Configuration](#cuda-configuration)
  - [Environment Variables](#environment-variables)
  - [Pre-Job Hook Integration](#pre-job-hook-integration)
- [Ollama Integration](#ollama-integration)
  - [API Endpoints Used](#api-endpoints-used)
  - [Model Loading Flow](#model-loading-flow)
- [CLI Commands](#cli-commands)
  - [GPU Manager](#gpu-manager)
  - [Warmup System](#warmup-system)
- [Integration Points](#integration-points)
  - [Dashboard Integration](#dashboard-integration)
  - [Kubernetes Integration](#kubernetes-integration)
  - [MCP Tool Integration](#mcp-tool-integration)
- [Monitoring & Metrics](#monitoring-metrics)
  - [nvidia-smi Query Fields](#nvidia-smi-query-fields)
  - [Health Checks](#health-checks)
- [File Paths](#file-paths)
- [Success Criteria](#success-criteria)
- [References](#references)

---

## Overview

The Dual-GPU Manager provides load-balanced GPU management for SLATE's AI inference workloads. Running on 2x NVIDIA RTX 5070 Ti GPUs, this system intelligently distributes Ollama model placement, manages VRAM allocation, and maintains hot models through a persistent warmup system.

The system ensures that:
- Heavy inference workloads run on dedicated GPU 0
- Quick tasks and embeddings run on GPU 1
- Models remain loaded in VRAM with configurable keep-alive durations
- Automatic load balancing prevents GPU oversubscription
- System warmup initializes both GPUs for instant inference

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SLATE DUAL-GPU ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
        │  GPU Manager │     │   Warmup     │     │   Ollama     │
        │              │────▶│   System     │────▶│   Server     │
        │slate_gpu_    │     │slate_warmup  │     │  :11434      │
        │manager.py    │     │.py           │     │              │
        └──────┬───────┘     └──────────────┘     └───────┬──────┘
               │                                          │
               │         GPU LOAD DISTRIBUTION            │
               │                                          │
    ┌──────────┴──────────────────────────────────────────┴──────────┐
    │                                                                 │
    │  ┌────────────────────────┐    ┌────────────────────────┐     │
    │  │        GPU 0           │    │        GPU 1           │     │
    │  │   HEAVY INFERENCE      │    │    QUICK TASKS         │     │
    │  │                        │    │                        │     │
    │  │  ┌─────────────────┐   │    │  ┌─────────────────┐   │     │
    │  │  │ slate-coder     │   │    │  │ slate-fast      │   │     │
    │  │  │ (12B params)    │   │    │  │ (3B params)     │   │     │
    │  │  │ keep_alive: 24h │   │    │  │ keep_alive: 24h │   │     │
    │  │  └─────────────────┘   │    │  └─────────────────┘   │     │
    │  │  ┌─────────────────┐   │    │  ┌─────────────────┐   │     │
    │  │  │ slate-planner   │   │    │  │ nomic-embed-text│   │     │
    │  │  │ (7B params)     │   │    │  │ (embeddings)    │   │     │
    │  │  │ keep_alive: 12h │   │    │  │ keep_alive: 24h │   │     │
    │  │  └─────────────────┘   │    │  └─────────────────┘   │     │
    │  │  ┌─────────────────┐   │    │  ┌─────────────────┐   │     │
    │  │  │ mistral-nemo    │   │    │  │ llama3.2:3b     │   │     │
    │  │  │ mistral         │   │    │  │ phi:latest      │   │     │
    │  │  └─────────────────┘   │    │  │ llama2:latest   │   │     │
    │  │                        │    │  └─────────────────┘   │     │
    │  │  Memory: 14GB max      │    │  Memory: 14GB max      │     │
    │  │  Role: heavy_inference │    │  Role: quick_tasks     │     │
    │  └────────────────────────┘    └────────────────────────┘     │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
```

## GPU-to-Model Assignment

The system uses a static model assignment strategy optimized for SLATE's workload patterns:

| GPU | Role | Models | Max VRAM | Use Case |
|-----|------|--------|----------|----------|
| 0 | Heavy Inference | slate-coder, slate-planner, mistral-nemo, mistral | 14 GB | Code generation, planning, complex reasoning |
| 1 | Quick Tasks | slate-fast, nomic-embed-text, llama3.2:3b, phi, llama2 | 14 GB | Fast responses, embeddings, simple tasks |

### Model Placement Strategy

```
MODEL PLACEMENT DECISION TREE
══════════════════════════════════════════════════════════════════════

                    ┌─────────────────┐
                    │ New Model Load  │
                    │    Request      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Check Model     │
                    │ Assignment Map  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐           ┌────────▼────────┐
     │ Model in GPU_0  │           │ Model in GPU_1  │
     │ Assignment List │           │ Assignment List │
     └────────┬────────┘           └────────┬────────┘
              │                             │
     ┌────────▼────────┐           ┌────────▼────────┐
     │ Check GPU_0     │           │ Check GPU_1     │
     │ Memory Status   │           │ Memory Status   │
     └────────┬────────┘           └────────┬────────┘
              │                             │
       ┌──────┴──────┐               ┌──────┴──────┐
       │             │               │             │
  ┌────▼────┐  ┌─────▼─────┐    ┌────▼────┐  ┌─────▼─────┐
  │ Fits in │  │ Evict LRU │    │ Fits in │  │ Evict LRU │
  │ VRAM    │  │ Model     │    │ VRAM    │  │ Model     │
  └────┬────┘  └─────┬─────┘    └────┬────┘  └─────┬─────┘
       │             │               │             │
       └──────┬──────┘               └──────┬──────┘
              │                             │
       ┌──────▼──────┐               ┌──────▼──────┐
       │ Load Model  │               │ Load Model  │
       │ to GPU 0    │               │ to GPU 1    │
       └─────────────┘               └─────────────┘
```

## Load Balancing Algorithm

### Memory-Aware Scheduling

```
LOAD BALANCING ALGORITHM
══════════════════════════════════════════════════════════════════════

1. QUERY: Inference request for model M arrives

2. CHECK LOADED:
   IF M is already loaded in VRAM:
     → Route to loaded instance (hot path)
     → Update keep_alive timer
     → RETURN

3. FIND TARGET GPU:
   assigned_gpu = GPU_MODEL_MAP[M]

   IF assigned_gpu.free_memory >= M.size:
     → Load M to assigned_gpu
   ELSE:
     → Evict least-recently-used model from assigned_gpu
     → Load M to assigned_gpu

4. EXECUTE:
   → Run inference on target GPU
   → Update utilization metrics
   → Set keep_alive timer

5. METRICS:
   → Log GPU utilization
   → Log memory usage
   → Log inference latency
```

### GPU Utilization Balancing

```
GPU UTILIZATION OVER TIME
══════════════════════════════════════════════════════════════════════

GPU 0 (Heavy Inference):
   0%  ├────────────────────────────────────────────────────────┤ 100%
       │████████████████████████████████████░░░░░░░░░░░░░░░░░░░░│ 72%
       │ Code generation ████████████████████                   │
       │ Planning        ████████████                           │
       │ Complex tasks   ████                                   │

GPU 1 (Quick Tasks):
   0%  ├────────────────────────────────────────────────────────┤ 100%
       │██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ 35%
       │ Embeddings     ████████                                │
       │ Fast responses ██████                                  │
       │ Simple tasks   ████                                    │

SCHEDULER TARGET:
   Keep GPU 0 utilization < 85% (headroom for burst)
   Keep GPU 1 utilization < 60% (fast response latency)
```

## Warmup System

The warmup system (`slate_warmup.py`) ensures models are pre-loaded in VRAM before inference requests arrive.

### Warmup Sequence

```
WARMUP SEQUENCE DIAGRAM
══════════════════════════════════════════════════════════════════════

    START
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Configure Ollama Environment                                │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│   CUDA_VISIBLE_DEVICES = "0,1"                                      │
│   OLLAMA_HOST = "127.0.0.1:11434"                                   │
│   OLLAMA_NUM_PARALLEL = 4                                           │
│   OLLAMA_MAX_LOADED_MODELS = 6                                      │
│   OLLAMA_FLASH_ATTENTION = 1                                        │
│   OLLAMA_KEEP_ALIVE = "24h"                                         │
│                                                                     │
│   → Write .ollama_env for runner hooks                              │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Ensure SLATE Models Exist                                   │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│   ┌─────────────────┐    ┌─────────────────┐                       │
│   │ slate-coder     │    │ slate-fast      │                       │
│   │ (from mistral)  │    │ (from phi)      │                       │
│   └─────────────────┘    └─────────────────┘                       │
│   ┌─────────────────┐    ┌─────────────────┐                       │
│   │ slate-planner   │    │ nomic-embed-text│                       │
│   │ (from llama)    │    │ (embedding)     │                       │
│   └─────────────────┘    └─────────────────┘                       │
│                                                                     │
│   → Check availability via /api/tags                                │
│   → Create modelfiles if missing                                    │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Preload Models with Keep-Alive                              │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│   Priority 1 (Critical):                                            │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │ slate-coder:latest  │ GPU 0 │ keep_alive: 24h │ ◉ LOAD  │     │
│   │ slate-fast:latest   │ GPU 1 │ keep_alive: 24h │ ◉ LOAD  │     │
│   │ nomic-embed-text    │ GPU 1 │ keep_alive: 24h │ ◉ LOAD  │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│   Priority 2 (Secondary):                                           │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │ slate-planner:latest│ GPU 0 │ keep_alive: 12h │ ◎ LOAD  │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│   → Send minimal inference to trigger VRAM load                     │
│   → Set keep_alive for persistent retention                         │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Build Embedding Index (Optional)                            │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│   IF index age > 6 hours:                                           │
│     → Index codebase files                                          │
│     → Generate embeddings via nomic-embed-text                      │
│     → Store in ChromaDB                                             │
│   ELSE:                                                             │
│     → Skip (index is fresh)                                         │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Verify Readiness                                            │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│   Checks:                                                           │
│   ├─ models_in_vram >= 2    ✓                                      │
│   ├─ gpus_active >= 1       ✓                                      │
│   └─ inference_test OK      ✓                                      │
│                                                                     │
│   → Run test inference on slate-fast                                │
│   → Measure latency (should be < 500ms for warm model)              │
│   → Update warmup state file                                        │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
    READY
```

### Keep-Alive Configuration

| Model | Priority | Keep-Alive | Purpose |
|-------|----------|------------|---------|
| slate-coder | 1 | 24h | Always hot for code generation |
| slate-fast | 1 | 24h | Always hot for quick responses |
| nomic-embed-text | 1 | 24h | Always hot for RAG queries |
| slate-planner | 2 | 12h | Hot during working hours |

### Warmup State Persistence

```json
{
  "last_warmup": "2026-02-08T10:00:00Z",
  "last_preload": "2026-02-08T10:00:00Z",
  "last_index": "2026-02-08T06:00:00Z",
  "warmup_count": 42,
  "models_loaded": [
    "slate-coder:latest",
    "slate-fast:latest",
    "nomic-embed-text:latest",
    "slate-planner:latest"
  ],
  "preload_failures": [],
  "index_stats": {
    "files": 287,
    "chunks": 1543
  }
}
```

## Memory Management

### VRAM Allocation Strategy

```
VRAM ALLOCATION PER GPU (16 GB Total Each)
══════════════════════════════════════════════════════════════════════

GPU 0 - Heavy Inference (16 GB):
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│  │                                                               │ │
│  │  slate-coder (12B)                                   ~8 GB    │ │
│  │  ████████████████████████████████████████████████████         │ │
│  │                                                               │ │
│  │  slate-planner (7B)                                  ~5 GB    │ │
│  │  ██████████████████████████████████                           │ │
│  │                                                               │ │
│  │  Reserved headroom                                   ~1 GB    │ │
│  │  ░░░░░░░░                                                     │ │
│  │                                                               │ │
│  │  System/CUDA overhead                                ~2 GB    │ │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓                                                 │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Max Loaded: 14 GB (88% of 16 GB)                                   │
└─────────────────────────────────────────────────────────────────────┘

GPU 1 - Quick Tasks (16 GB):
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│  │                                                               │ │
│  │  slate-fast (3B)                                     ~2 GB    │ │
│  │  ████████████████                                             │ │
│  │                                                               │ │
│  │  nomic-embed-text                                    ~0.5 GB  │ │
│  │  ████                                                         │ │
│  │                                                               │ │
│  │  llama3.2:3b                                         ~2 GB    │ │
│  │  ████████████████                                             │ │
│  │                                                               │ │
│  │  phi:latest                                          ~2 GB    │ │
│  │  ████████████████                                             │ │
│  │                                                               │ │
│  │  Available for additional models                     ~7.5 GB  │ │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░       │ │
│  │                                                               │ │
│  │  System/CUDA overhead                                ~2 GB    │ │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓                                                 │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Max Loaded: 14 GB (88% of 16 GB)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Eviction Policy

When VRAM is exhausted, the system uses Least Recently Used (LRU) eviction:

```
EVICTION DECISION FLOW
══════════════════════════════════════════════════════════════════════

    Load Request for Model M
           │
           ▼
    ┌──────────────────┐
    │ Target GPU has   │──── YES ───▶ Load M (hot path)
    │ sufficient VRAM? │
    └──────────────────┘
           │ NO
           ▼
    ┌──────────────────┐
    │ Get models on    │
    │ target GPU       │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Sort by:         │
    │ 1. Priority      │
    │ 2. Last access   │
    │ 3. Keep-alive    │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Evict lowest     │
    │ priority model   │
    │ with expired     │
    │ keep-alive       │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Free VRAM        │
    │ sufficient?      │
    └──────────────────┘
       │         │
      YES       NO
       │         │
       ▼         ▼
    Load M    Evict next
              LRU model
```

## CUDA Configuration

### Environment Variables

```bash
# Core GPU visibility
CUDA_VISIBLE_DEVICES=0,1

# Ollama server configuration
OLLAMA_HOST=127.0.0.1:11434

# Parallel inference (allows concurrent requests)
OLLAMA_NUM_PARALLEL=4

# Maximum models in VRAM across all GPUs
OLLAMA_MAX_LOADED_MODELS=6

# Enable flash attention for memory efficiency
OLLAMA_FLASH_ATTENTION=1

# Default model retention time
OLLAMA_KEEP_ALIVE=24h
```

### Pre-Job Hook Integration

The GPU manager integrates with GitHub Actions runner hooks:

```powershell
# actions-runner/hooks/pre-job.ps1 (auto-configured)

# SLATE Dual-GPU Ollama configuration
$env:CUDA_VISIBLE_DEVICES = "0,1"
$env:OLLAMA_NUM_PARALLEL = "4"
$env:OLLAMA_MAX_LOADED_MODELS = "6"
$env:OLLAMA_FLASH_ATTENTION = "1"
```

## Ollama Integration

### API Endpoints Used

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `GET /api/tags` | List available models | Check model availability |
| `GET /api/ps` | List loaded models | Monitor VRAM usage |
| `POST /api/generate` | Run inference | Load model + generate |
| `POST /api/embed` | Generate embeddings | Load embedding model + embed |

### Model Loading Flow

```
OLLAMA MODEL LOADING
══════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────────────────┐
                    │           GPU Manager Request               │
                    │                                             │
                    │   POST /api/generate                        │
                    │   {                                         │
                    │     "model": "slate-coder:latest",          │
                    │     "prompt": "Ready.",                     │
                    │     "stream": false,                        │
                    │     "keep_alive": "24h",                    │
                    │     "options": {"num_predict": 1}           │
                    │   }                                         │
                    └─────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │              Ollama Server                   │
                    │                                             │
                    │   1. Check if model in VRAM                 │
                    │   2. If not, load from disk to VRAM         │
                    │   3. Execute inference                      │
                    │   4. Set keep_alive timer                   │
                    │   5. Return response                        │
                    └─────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │            Model State in VRAM              │
                    │                                             │
                    │   ┌─────────────────────────────────────┐  │
                    │   │ slate-coder:latest                  │  │
                    │   │ ─────────────────────────────────── │  │
                    │   │ VRAM: 8.2 GB                        │  │
                    │   │ Expires: 2026-02-09T10:00:00Z       │  │
                    │   │ GPU: auto-assigned by Ollama        │  │
                    │   └─────────────────────────────────────┘  │
                    └─────────────────────────────────────────────┘
```

## CLI Commands

### GPU Manager

```powershell
# View GPU status with model assignments
python slate/slate_gpu_manager.py --status

# Configure Ollama for dual-GPU operation
python slate/slate_gpu_manager.py --configure

# Preload key models to both GPUs
python slate/slate_gpu_manager.py --preload

# Get JSON output for automation
python slate/slate_gpu_manager.py --json
```

### Warmup System

```powershell
# Full system warmup (configure + preload + index + verify)
python slate/slate_warmup.py

# Preload models only (skip indexing)
python slate/slate_warmup.py --preload-only

# Build embedding index only
python slate/slate_warmup.py --index-only

# View warmup status
python slate/slate_warmup.py --status

# JSON output for automation
python slate/slate_warmup.py --json

# Force rebuild even if fresh
python slate/slate_warmup.py --force
```

## Integration Points

### Dashboard Integration

The GPU Workbench in the Watchmaker dashboard (spec 012) visualizes GPU status:

```
┌────────────────────────────┐  ┌────────────────────────────┐
│  GPU 0: RTX 5070 Ti        │  │  GPU 1: RTX 5070 Ti        │
│  ════════════════════════  │  │  ════════════════════════  │
│                            │  │                            │
│  ⟳ Compute: ▓▓▓▓▓▓░░ 75%  │  │  ⟳ Compute: ▓▓▓░░░░░ 38%  │
│  ◐ Memory:  ▓▓▓▓░░░░ 50%  │  │  ◐ Memory:  ▓▓░░░░░░ 25%  │
│  ◉ Power:   ▓▓▓▓▓░░░ 62%  │  │  ◉ Power:   ▓▓▓░░░░░ 40%  │
│                            │  │                            │
│  Active Tasks:             │  │  Active Tasks:             │
│  ├─ mistral-nemo (7B)      │  │  ├─ llama3.2 (3B)          │
│  └─ embedding gen          │  │  └─ (idle)                 │
│                            │  │                            │
│  Temp: 58 C  CUDA 12.8     │  │  Temp: 42 C  CUDA 12.8     │
└────────────────────────────┘  └────────────────────────────┘
```

### Kubernetes Integration

When running in K8s, the GPU manager detects Ollama pods and integrates with cluster resources:

```yaml
# k8s/slate-ollama.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: slate
  labels:
    app.kubernetes.io/component: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        resources:
          limits:
            nvidia.com/gpu: 2
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0,1"
        - name: OLLAMA_NUM_PARALLEL
          value: "4"
        - name: OLLAMA_MAX_LOADED_MODELS
          value: "6"
```

### MCP Tool Integration

The `/slate-gpu` command exposes GPU management via MCP:

```json
{
  "tool": "slate_gpu",
  "description": "Manage dual-GPU load balancing",
  "operations": ["status", "configure", "preload", "balance"]
}
```

## Monitoring & Metrics

### nvidia-smi Query Fields

```
Query: nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits

Output per GPU:
- index: GPU index (0 or 1)
- name: GPU model name (NVIDIA GeForce RTX 5070 Ti)
- memory.used: VRAM in use (MB)
- memory.free: Available VRAM (MB)
- memory.total: Total VRAM (MB)
- utilization.gpu: Compute utilization (%)
- temperature.gpu: GPU temperature (Celsius)
```

### Health Checks

| Check | Threshold | Action |
|-------|-----------|--------|
| VRAM usage | > 90% | Alert, consider eviction |
| GPU temp | > 80C | Throttle workload |
| Utilization | > 95% sustained | Queue requests |
| Models loaded | < 2 | Trigger warmup |

## File Paths

| File | Purpose |
|------|---------|
| `slate/slate_gpu_manager.py` | GPU management and load balancing |
| `slate/slate_warmup.py` | System warmup and model preloading |
| `.ollama_env` | Ollama environment configuration |
| `.slate_warmup_state.json` | Warmup state persistence |
| `slate_logs/warmup/warmup_*.log` | Warmup operation logs |

## Success Criteria

1. **Model Availability**: Priority 1 models always loaded in VRAM
2. **Inference Latency**: Warm model inference < 500ms first token
3. **GPU Utilization**: Balanced load across both GPUs
4. **Memory Efficiency**: No OOM errors under normal workload
5. **Warmup Time**: Full system warmup < 2 minutes
6. **Keep-Alive**: Models retained for configured duration

---

## References

- CLAUDE.md: Dual-GPU configuration and commands
- Spec 012: Watchmaker 3D Dashboard (GPU Workbench visualization)
- Ollama API documentation: https://github.com/ollama/ollama/blob/main/docs/api.md

---
*Source: [specs/019-dual-gpu-manager/spec.md](../../../specs/019-dual-gpu-manager/spec.md)*
