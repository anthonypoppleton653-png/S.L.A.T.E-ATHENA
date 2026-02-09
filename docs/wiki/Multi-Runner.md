# Multi-Runner System
<!-- Modified: 2026-02-08T12:00:00Z | Author: CLAUDE | Change: Initial multi-runner wiki documentation -->

SLATE's multi-runner system enables parallel task execution across multiple GitHub Actions self-hosted runners, each with configurable resource profiles and GPU assignments.

## Overview

The multi-runner system distributes workloads across multiple runner instances to maximize throughput and resource utilization. Instead of a single runner processing tasks sequentially, SLATE can deploy up to 50 concurrent runners that execute workflows in parallel.

**Key Benefits:**
- Parallel workflow execution for faster CI/CD
- GPU workload distribution across multiple devices
- Resource-aware task assignment
- Automatic scaling based on hardware capacity
- Dedicated runners for different task types

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │         GitHub Actions API              │
                    │  (Workflow Dispatch & Job Assignment)   │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
           │   Runner 1  │      │   Runner 2  │      │   Runner N  │
           │  [cuda,gpu] │      │  [gpu-0]    │      │  [cpu-only] │
           └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
                  │                    │                    │
                  ▼                    ▼                    ▼
           ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
           │ GPU 0 + GPU1│      │   GPU 0     │      │   CPU Pool  │
           │ (Heavy AI)  │      │ (Light AI)  │      │ (Lint/Test) │
           └─────────────┘      └─────────────┘      └─────────────┘
                  │                    │                    │
                  └────────────────────┼────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │      Multi-Runner Coordinator       │
                    │  (slate_multi_runner.py)            │
                    │  - Task assignment                  │
                    │  - Resource tracking                │
                    │  - GPU reservation                  │
                    └─────────────────────────────────────┘
```

### Component Interactions

| Component | Purpose | Location |
|-----------|---------|----------|
| **Multi-Runner Coordinator** | Logical task distribution | `slate/slate_multi_runner.py` |
| **Real Multi-Runner Manager** | Actual runner process management | `slate/slate_real_multi_runner.py` |
| **Runner Benchmark** | Hardware capacity detection | `slate/slate_runner_benchmark.py` |
| **GitHub API** | Runner registration & workflow dispatch | GitHub Actions |

## Runner Types and Profiles

SLATE defines five runner profiles based on resource requirements:

| Profile | GPU Memory | CPU Cores | RAM | Use Cases |
|---------|------------|-----------|-----|-----------|
| **light** | 0 MB | 1 | 512 MB | Linting, formatting, simple validation |
| **standard** | 0 MB | 2 | 1 GB | Unit tests, SDK validation, security scans |
| **gpu_light** | 2 GB | 2 | 2 GB | Small model inference, embeddings |
| **gpu_heavy** | 8 GB | 4 | 8 GB | Large model inference, benchmarks |
| **gpu_max** | 14 GB | 4 | 16 GB | Full GPU tasks, multi-GPU training |

### Profile Examples

```python
# Profile resource definitions
RUNNER_PROFILES = {
    "light": {
        "examples": ["ruff check", "black --check", "mypy"],
    },
    "standard": {
        "examples": ["pytest", "bandit", "sdk-validation"],
    },
    "gpu_light": {
        "examples": ["embeddings", "small-llm", "classification"],
    },
    "gpu_heavy": {
        "examples": ["mistral-nemo", "fine-tuning", "full-benchmark"],
    },
    "gpu_max": {
        "examples": ["large-model", "multi-gpu-training"],
    },
}
```

## Configuration

### Automatic Configuration

SLATE automatically benchmarks your hardware and recommends an optimal runner configuration:

```bash
# Initialize with auto-detection
python slate/slate_multi_runner.py --init

# View recommended configuration
python slate/slate_runner_benchmark.py
```

**Example Output (Dual-GPU System):**
```
Optimal Configuration:
----------------------------------------
  Strategy: dual_gpu_scaled
  50-runner config: GPU 0/1 for inference, CPU pool for parallelism
  Total Runners: 50
  Parallel Workflows: 8

  Configuration:
    GPU 0: 1x gpu_heavy
    GPU 0: 4x gpu_light
    GPU 1: 6x gpu_light
    GPU 1: 4x standard
    CPU:  10x standard
    CPU:  25x light
```

### Manual Configuration

For custom setups, create `.slate_runners.json`:

```json
{
  "runners": [
    {
      "id": "runner-001",
      "name": "slate-primary",
      "profile": "gpu_heavy",
      "gpu_id": 0,
      "status": "idle"
    },
    {
      "id": "runner-002",
      "name": "slate-gpu-light",
      "profile": "gpu_light",
      "gpu_id": 1,
      "status": "idle"
    },
    {
      "id": "runner-003",
      "name": "slate-cpu",
      "profile": "standard",
      "gpu_id": null,
      "status": "idle"
    }
  ],
  "max_parallel_workflows": 4,
  "gpu_reservation": {
    "0": ["runner-001"],
    "1": ["runner-002"]
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CUDA_VISIBLE_DEVICES` | Restrict GPU access per runner | All GPUs |
| `SLATE_MAX_RUNNERS` | Maximum runner instances | 50 |
| `SLATE_RUNNER_TIMEOUT` | Task timeout in minutes | 30 |

## Commands

### Status and Monitoring

```bash
# Show multi-runner status
python slate/slate_multi_runner.py --status

# JSON output for automation
python slate/slate_multi_runner.py --json

# Real runner status (actual GitHub-registered runners)
python slate/slate_real_multi_runner.py --status
```

**Example Status Output:**
```
============================================================
  SLATE Multi-Runner Status
============================================================

Total Runners: 12
  Running: 3
  Idle:    8
  Error:   1
Max Parallel: 8

GPU Distribution:
  GPU 0: 3 runners
  GPU 1: 4 runners

Runners:
------------------------------------------------------------
  ID           Name                      Profile      GPU   Status
  ------------ ------------------------- ------------ ----- --------
  runner-001   slate-gpu-heavy-01        gpu_heavy    0     running
  runner-002   slate-gpu-light-02        gpu_light    0     idle
  runner-003   slate-gpu-light-03        gpu_light    1     running
  ...
============================================================
```

### Initialization and Scaling

```bash
# Initialize with optimal configuration
python slate/slate_multi_runner.py --init

# Initialize with minimal 2-runner config
python slate/slate_multi_runner.py --init --minimal

# Scale to specific runner count (max 50)
python slate/slate_multi_runner.py --scale 20
```

### Task Assignment

```bash
# Assign task to available runner
python slate/slate_multi_runner.py --assign "task-123"

# Mark runner task complete
python slate/slate_multi_runner.py --complete "runner-001"
```

### Lifecycle Management

```bash
# Start all registered runners
python slate/slate_real_multi_runner.py --start-all

# Stop all runner processes
python slate/slate_real_multi_runner.py --stop-all

# Dispatch a workflow
python slate/slate_real_multi_runner.py --dispatch "multi-runner.yml"

# View active workflow runs
python slate/slate_real_multi_runner.py --active-runs
```

### Benchmarking

```bash
# Full hardware benchmark
python slate/slate_runner_benchmark.py

# Check specific profile capacity
python slate/slate_runner_benchmark.py --profile gpu_heavy

# JSON output for automation
python slate/slate_runner_benchmark.py --json
```

## Resource Allocation

### GPU Distribution Strategy

For dual-GPU systems, SLATE distributes workloads:

```
┌──────────────────────────────────────────────────────────┐
│                    Dual-GPU Distribution                 │
├────────────────────────┬─────────────────────────────────┤
│        GPU 0           │           GPU 1                 │
├────────────────────────┼─────────────────────────────────┤
│ 1x gpu_heavy (8GB)     │ 6x gpu_light (2GB each)         │
│ 4x gpu_light (2GB each)│ 4x standard (CPU-assist)        │
│                        │                                 │
│ Total: ~16GB reserved  │ Total: ~12GB reserved           │
├────────────────────────┴─────────────────────────────────┤
│                    CPU Pool                              │
│ 10x standard (tests)  +  25x light (lint/format)         │
└──────────────────────────────────────────────────────────┘
```

### Memory-Aware Allocation

The system calculates capacity based on available resources:

```python
# Capacity calculation per profile
max_gpu_runners = gpu_free_memory // profile_gpu_requirement
max_cpu_runners = cpu_cores // profile_core_requirement
max_ram_runners = ram_free // profile_ram_requirement

# Actual capacity is minimum of all limits
actual_capacity = min(max_gpu, max_cpu, max_ram)
```

### Limiting Factor Detection

Each profile reports its limiting factor:

| Profile | Typical Limit | Reason |
|---------|--------------|--------|
| light | RAM | Many instances, low overhead |
| standard | CPU | Needs dedicated cores |
| gpu_light | GPU | VRAM consumption |
| gpu_heavy | GPU | Large VRAM footprint |
| gpu_max | GPU | Full device allocation |

## Workflow Integration

### GitHub Actions Labels

Runners register with specific labels for job targeting:

| Label | Description |
|-------|-------------|
| `self-hosted` | All SLATE runners |
| `slate` | SLATE project runners |
| `cuda` | GPU-capable runners |
| `gpu-0` | Runners assigned to GPU 0 |
| `gpu-1` | Runners assigned to GPU 1 |
| `cpu-only` | CPU-only runners |
| `gpu-2` | Multi-GPU capable |

### Parallel Workflow Example

```yaml
# .github/workflows/multi-runner.yml
name: Multi-Runner Parallel Proof

jobs:
  # Job 1: Targets primary GPU runner
  sdk-validation:
    runs-on: [self-hosted, slate, cuda]
    steps:
      - uses: actions/checkout@v6
      - run: python -c "import slate; print(f'SLATE v{slate.__version__}')"

  # Job 2: Targets GPU 0 specifically
  tests-gpu-0:
    runs-on: [self-hosted, slate, gpu-0]
    env:
      CUDA_VISIBLE_DEVICES: '0'
    steps:
      - uses: actions/checkout@v6
      - run: python -m pytest tests/ -v

  # Job 3: Targets GPU 1 specifically
  tests-gpu-1:
    runs-on: [self-hosted, slate, gpu-1]
    env:
      CUDA_VISIBLE_DEVICES: '1'
    steps:
      - uses: actions/checkout@v6
      - run: python slate/slate_benchmark.py

  # Job 4: CPU-only tasks
  lint-security:
    runs-on: [self-hosted, slate, cpu-only]
    steps:
      - uses: actions/checkout@v6
      - run: python -m ruff check slate/ agents/
```

All four jobs launch simultaneously on different runners.

## Troubleshooting

### Runner Not Picking Up Jobs

**Symptoms:**
- Jobs queued but not starting
- Runner shows as offline

**Solutions:**

```bash
# Check runner registration
python slate/slate_real_multi_runner.py --status

# Verify runner process is running
Get-Process -Name 'Runner.Listener' -ErrorAction SilentlyContinue

# Restart runners
python slate/slate_real_multi_runner.py --stop-all
python slate/slate_real_multi_runner.py --start-all
```

### GPU Memory Exhausted

**Symptoms:**
- CUDA out of memory errors
- GPU runners failing

**Solutions:**

```bash
# Check GPU utilization
nvidia-smi

# Reduce concurrent GPU runners
python slate/slate_multi_runner.py --init --minimal

# Clear GPU memory
python -c "import torch; torch.cuda.empty_cache()"
```

### Runner Registration Token Expired

**Symptoms:**
- Runner fails to connect to GitHub
- Authentication errors

**Solutions:**

```bash
# Get new registration token
python slate/slate_real_multi_runner.py

# Re-configure runner
cd actions-runner-N
./config.cmd remove
./config.cmd --url https://github.com/OWNER/REPO --token <NEW_TOKEN>
```

### Jobs Running on Wrong Runner

**Symptoms:**
- GPU jobs running on CPU runner
- Label mismatch

**Solutions:**

1. Verify runner labels in GitHub UI (Settings > Actions > Runners)
2. Check workflow `runs-on` specification
3. Update runner labels:

```bash
cd actions-runner-N
./config.cmd --labels self-hosted,slate,gpu-0
```

### Stale Configuration

**Symptoms:**
- Runner count doesn't match actual runners
- Status shows outdated information

**Solutions:**

```bash
# Re-benchmark and reinitialize
python slate/slate_runner_benchmark.py
python slate/slate_multi_runner.py --init

# Or force JSON refresh
rm .slate_runners.json
python slate/slate_multi_runner.py --init
```

## Related Documentation

- [Architecture](Architecture) - System architecture overview
- [CLI Reference](CLI-Reference) - Command-line interface documentation
- [AI Backends](AI-Backends) - AI inference configuration
- [Troubleshooting](Troubleshooting) - General troubleshooting guide
- [Configuration](Configuration) - System configuration options

## Next Steps

- Run `python slate/slate_runner_benchmark.py` to see your hardware capacity
- Initialize multi-runner with `python slate/slate_multi_runner.py --init`
- Monitor runner status with `/slate-multirunner` command
