# Specification: Multi-Runner System

**Spec ID**: 016-multi-runner-system
**Status**: complete
**Created**: 2026-02-08
**Author**: Claude Opus 4.5
**Depends On**: github-runner (tech tree node)

## Overview

The Multi-Runner System provides parallel task execution across multiple GitHub Actions runners, intelligently distributing workloads based on GPU memory, CPU cores, and RAM availability. The system supports up to 50 concurrent runners across 2 GPUs, enabling massive parallelism for CI/CD, AI inference, and development workflows.

This specification defines:
- Runner profiles and resource requirements
- Benchmark-driven capacity planning
- Dynamic task assignment and load balancing
- GPU reservation and memory management
- Integration with GitHub Actions workflows

## Architecture

### System Overview

```
+===========================================================================+
|                       SLATE MULTI-RUNNER ARCHITECTURE                      |
+===========================================================================+
|                                                                            |
|   +------------------------------------------------------------------+    |
|   |                    RUNNER COORDINATOR                             |    |
|   |  (slate/slate_multi_runner.py)                                    |    |
|   |                                                                   |    |
|   |   +-----------------------+    +-------------------------+        |    |
|   |   | Task Queue Manager    |    | Runner State Manager    |        |    |
|   |   | - Priority ordering   |    | - Status tracking       |        |    |
|   |   | - Profile matching    |    | - Health monitoring     |        |    |
|   |   | - Load balancing      |    | - Error recovery        |        |    |
|   |   +-----------------------+    +-------------------------+        |    |
|   +------------------------------------------------------------------+    |
|                                    |                                       |
|                    +---------------+---------------+                       |
|                    |                               |                       |
|        +-----------v-----------+       +-----------v-----------+          |
|        |       GPU POOL 0      |       |       GPU POOL 1      |          |
|        |    RTX 5070 Ti 16GB   |       |    RTX 5070 Ti 16GB   |          |
|        +-----------------------+       +-----------------------+          |
|        | gpu_heavy (1x 8GB)    |       | gpu_light (6x 2GB)    |          |
|        | gpu_light (4x 2GB)    |       | standard  (4x 0GB)    |          |
|        +-----------------------+       +-----------------------+          |
|                    |                               |                       |
|                    +---------------+---------------+                       |
|                                    |                                       |
|        +---------------------------v---------------------------+          |
|        |                     CPU POOL                          |          |
|        |   standard (10x) + light (25x) = 35 CPU runners       |          |
|        +-------------------------------------------------------+          |
|                                                                            |
+===========================================================================+
```

### Runner Distribution

```
+==========================================================================+
|                      RUNNER DISTRIBUTION SCHEMATIC                        |
+==========================================================================+
|                                                                           |
|  GPU 0 (RTX 5070 Ti - Heavy Workloads)                                   |
|  =========================================                                |
|  |  [HEAVY]  |  [LIGHT]  [LIGHT]  [LIGHT]  [LIGHT]  |                   |
|  |   8 GB    |   2 GB     2 GB     2 GB     2 GB    |                   |
|  |  runner   |  runner   runner   runner   runner   |                   |
|  |   001     |   002      003      004      005     |   = 5 runners     |
|  =========================================                                |
|                         |                                                 |
|                         | PCIe Bus                                        |
|                         v                                                 |
|  GPU 1 (RTX 5070 Ti - Light Workloads)                                   |
|  =========================================                                |
|  | [LIGHT] [LIGHT] [LIGHT] [LIGHT] [LIGHT] [LIGHT] |                    |
|  |  2 GB    2 GB    2 GB    2 GB    2 GB    2 GB   |                    |
|  | runner  runner  runner  runner  runner  runner  |                    |
|  |  006     007     008     009     010     011    |   = 6 runners     |
|  =========================================                                |
|                         |                                                 |
|                         | Memory Bus                                      |
|                         v                                                 |
|  CPU + RAM Pool (No GPU Required)                                        |
|  =====================================================================   |
|  | STANDARD RUNNERS (CPU-bound tasks)                                |   |
|  | [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD]      |   |
|  |  012   013   014   015   016   017   018   019   020   021       |   |
|  |--------------------------------------------------------------------   |
|  | LIGHT RUNNERS (Minimal resource tasks)                            |   |
|  | [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] ... |   |
|  |  022  023  024  025  026  027  028  029  030  031  032  033 ...  |   |
|  | (up to 25 light runners)                                          |   |
|  =====================================================================   |
|                                                                           |
|  TOTAL: 5 GPU0 + 6 GPU1 + 10 Standard + 25 Light = 46-50 Runners         |
|                                                                           |
+==========================================================================+
```

## Runner Profiles

### Profile Definitions

| Profile | GPU Memory | CPU Cores | RAM | Use Cases |
|---------|------------|-----------|-----|-----------|
| **light** | 0 MB | 1 | 512 MB | Linting, formatting, simple tests |
| **standard** | 0 MB | 2 | 1 GB | Unit tests, SDK validation, security scans |
| **gpu_light** | 2 GB | 2 | 2 GB | Embeddings, small LLM inference, classification |
| **gpu_heavy** | 8 GB | 4 | 8 GB | Large model inference, fine-tuning, benchmarks |
| **gpu_max** | 14 GB | 4 | 16 GB | Maximum GPU allocation for single large tasks |

### Profile Details

```
+===========================================================================+
|                        RUNNER PROFILE SPECIFICATIONS                       |
+===========================================================================+

LIGHT RUNNER (light)
--------------------
Resources: 0 GPU | 1 CPU | 512 MB RAM
Labels:    [self-hosted, slate, light, cpu-only]
Tasks:
  - ruff check (linting)
  - black --check (formatting)
  - mypy (type checking)
  - isort --check (import sorting)
  - Simple file operations
Capacity:  Up to 25 parallel instances

STANDARD RUNNER (standard)
--------------------------
Resources: 0 GPU | 2 CPU | 1 GB RAM
Labels:    [self-hosted, slate, standard, cpu-only]
Tasks:
  - pytest (unit tests)
  - bandit (security scan)
  - SDK validation
  - Documentation builds
  - Integration tests (non-GPU)
Capacity:  Up to 10 parallel instances

GPU LIGHT RUNNER (gpu_light)
----------------------------
Resources: 2 GB GPU | 2 CPU | 2 GB RAM
Labels:    [self-hosted, slate, gpu, gpu-light, cuda]
Tasks:
  - Text embeddings generation
  - Small model inference (phi-3, llama-3B)
  - Classification tasks
  - Image preprocessing
  - Vector similarity search
Capacity:  Up to 10 parallel instances (5 per GPU)

GPU HEAVY RUNNER (gpu_heavy)
----------------------------
Resources: 8 GB GPU | 4 CPU | 8 GB RAM
Labels:    [self-hosted, slate, gpu, gpu-heavy, cuda]
Tasks:
  - mistral-nemo inference (7B)
  - Fine-tuning jobs
  - Full benchmark suite
  - Multi-model pipelines
  - RAG with large context
Capacity:  1-2 parallel instances

GPU MAX RUNNER (gpu_max)
------------------------
Resources: 14 GB GPU | 4 CPU | 16 GB RAM
Labels:    [self-hosted, slate, gpu, gpu-max, cuda, exclusive]
Tasks:
  - Large model training
  - Multi-GPU inference
  - Maximum context operations
  - Model quantization
Capacity:  1 instance (full GPU)
```

## Benchmark System

### Resource Detection

The benchmark system (`slate/slate_runner_benchmark.py`) automatically detects:

1. **GPU Resources**
   - GPU count via nvidia-smi
   - Total memory per GPU
   - Available memory per GPU
   - Current utilization percentage

2. **CPU Resources**
   - Total core count
   - Available cores for allocation

3. **Memory Resources**
   - Total system RAM
   - Available RAM for allocation

### Capacity Calculation

```
+==========================================================================+
|                       CAPACITY CALCULATION FLOW                           |
+==========================================================================+
|                                                                           |
|   INPUT: System Resources + Runner Profile                                |
|   ================================================                        |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |              GPU CAPACITY CHECK                   |                   |
|   |  gpu_capacity = free_gpu_memory / profile_gpu_mb |                   |
|   |  Per-GPU: [GPU0: N, GPU1: M, ...]                 |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |              CPU CAPACITY CHECK                   |                   |
|   |  cpu_capacity = cpu_cores / profile_cpu_cores    |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |              RAM CAPACITY CHECK                   |                   |
|   |  ram_capacity = free_ram / profile_ram_mb        |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |           LIMITING FACTOR DETECTION              |                   |
|   |  max_runners = MIN(gpu, cpu, ram)                |                   |
|   |  limiting_factor = whichever is smallest         |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   OUTPUT: RunnerCapacity { max_total, per_gpu[], limiting_factor }       |
|                                                                           |
+==========================================================================+
```

### Benchmark CLI

```bash
# Full benchmark report
python slate/slate_runner_benchmark.py

# JSON output for automation
python slate/slate_runner_benchmark.py --json

# Check specific profile capacity
python slate/slate_runner_benchmark.py --profile gpu_light
```

### Sample Benchmark Output

```
============================================================
  SLATE Multi-Runner Benchmark Report
============================================================

System Resources:
----------------------------------------
  GPUs: 2
    GPU 0: 14,208 / 16,384 MB free (12% utilized)
    GPU 1: 15,872 / 16,384 MB free (3% utilized)
  CPU Cores: 32
  RAM: 48,256 / 65,536 MB free

Runner Capacity by Profile:
----------------------------------------
  Profile              Max    Limit    Per GPU
  -------------------- ------ -------- ---------------
  Light Runner         50     cap      [999, 999]
  Standard Runner      16     cpu      [999, 999]
  GPU Light Runner     10     gpu      [7, 7]
  GPU Heavy Runner     3      gpu      [1, 1]
  GPU Max Runner       2      gpu      [1, 1]

Optimal Configuration:
----------------------------------------
  Strategy: dual_gpu_scaled
  50-runner config: GPU 0/1 for inference, CPU pool for parallelism
  Total Runners: 50
  Parallel Workflows: 8

  Configuration:
    0: 1x gpu_heavy
    0: 4x gpu_light
    1: 6x gpu_light
    1: 4x standard
    cpu: 10x standard
    cpu: 25x light

============================================================
```

## Task Assignment

### Assignment Algorithm

```
+==========================================================================+
|                        TASK ASSIGNMENT ALGORITHM                          |
+==========================================================================+
|                                                                           |
|   INCOMING TASK: { id, type, resource_requirements }                     |
|   =====================================================                   |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |          1. PROFILE MATCHING                      |                   |
|   |  Determine required profile based on task type:  |                   |
|   |  - inference_large -> gpu_heavy                   |                   |
|   |  - inference_small -> gpu_light                   |                   |
|   |  - tests           -> standard                    |                   |
|   |  - lint            -> light                       |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   +--------------------------------------------------+                   |
|   |          2. AVAILABILITY CHECK                    |                   |
|   |  Filter runners by:                               |                   |
|   |  - status == "idle"                               |                   |
|   |  - profile matches OR is more capable             |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|           +---------------+---------------+                               |
|           |                               |                               |
|           v                               v                               |
|   [Runners Available]            [No Runners Available]                  |
|           |                               |                               |
|           v                               v                               |
|   +------------------+           +------------------+                    |
|   | 3. SELECT BEST   |           | QUEUE TASK       |                    |
|   | - Prefer exact   |           | Wait for runner  |                    |
|   |   profile match  |           | to become idle   |                    |
|   | - Load balance   |           +------------------+                    |
|   |   across GPUs    |                                                   |
|   +------------------+                                                   |
|           |                                                               |
|           v                                                               |
|   +--------------------------------------------------+                   |
|   |          4. ASSIGN AND UPDATE STATE              |                   |
|   |  runner.status = "running"                        |                   |
|   |  runner.current_task = task_id                    |                   |
|   |  runner.started_at = now()                        |                   |
|   +--------------------------------------------------+                   |
|                           |                                               |
|                           v                                               |
|   OUTPUT: Assigned RunnerInstance                                        |
|                                                                           |
+==========================================================================+
```

### Load Balancing Strategy

```
+==========================================================================+
|                       LOAD BALANCING STRATEGY                             |
+==========================================================================+
|                                                                           |
|   GPU LOAD BALANCING                                                     |
|   ==================                                                      |
|                                                                           |
|   Goal: Distribute GPU tasks to minimize memory pressure                  |
|                                                                           |
|   +-------------------+          +-------------------+                   |
|   |      GPU 0        |          |      GPU 1        |                   |
|   |  Heavy Inference  |          |  Light Inference  |                   |
|   +-------------------+          +-------------------+                   |
|   | [  HEAVY 8GB  ]   |          | [LT][LT][LT][LT]  |                   |
|   | [LT][LT][LT][LT]  |          | [LT][LT][  ][  ]  |                   |
|   | Memory: 16GB      |          | Memory: 12GB used |                   |
|   +-------------------+          +-------------------+                   |
|                                                                           |
|   Assignment Priority:                                                   |
|   1. gpu_heavy tasks -> GPU 0 (dedicated heavy workload GPU)             |
|   2. gpu_light tasks -> GPU with most free memory                         |
|   3. Prefer spreading tasks across GPUs for parallelism                   |
|                                                                           |
|   CPU LOAD BALANCING                                                     |
|   ==================                                                      |
|                                                                           |
|   +---------------------------------------------------------------+     |
|   |                        CPU RUNNER POOL                         |     |
|   +---------------------------------------------------------------+     |
|   | [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD] [STD]  |     |
|   | [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT]  |     |
|   | [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT] [LT]  |     |
|   +---------------------------------------------------------------+     |
|                                                                           |
|   Assignment Priority:                                                   |
|   1. Match exact profile first (light -> light, standard -> standard)     |
|   2. Upgrade if needed (light task can run on standard runner)           |
|   3. First-idle-first-assigned for simplicity                             |
|                                                                           |
+==========================================================================+
```

## Configuration

### Configuration File (.slate_runners.json)

```json
{
  "runners": [
    {
      "id": "runner-001",
      "name": "slate-gpu-heavy-01",
      "profile": "gpu_heavy",
      "gpu_id": 0,
      "status": "idle",
      "current_task": null,
      "tasks_completed": 0
    },
    {
      "id": "runner-002",
      "name": "slate-gpu-light-02",
      "profile": "gpu_light",
      "gpu_id": 1,
      "status": "running",
      "current_task": "inference-task-123",
      "tasks_completed": 5
    }
  ],
  "max_parallel_workflows": 8,
  "gpu_reservation": {
    "0": ["runner-001"],
    "1": ["runner-002", "runner-003", "runner-004"]
  },
  "updated_at": "2026-02-08T12:00:00Z"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_parallel_workflows` | int | 8 | Maximum concurrent GitHub workflow runs |
| `task_timeout_minutes` | int | 30 | Timeout for individual tasks |
| `gpu_reservation` | dict | auto | GPU-to-runner mapping |
| `scale_max` | int | 50 | Maximum runner count |

## Coordinator CLI

### Commands

```bash
# Initialize with optimal configuration
python slate/slate_multi_runner.py --init

# Initialize with minimal configuration
python slate/slate_multi_runner.py --init --minimal

# Show current status
python slate/slate_multi_runner.py --status

# JSON output for automation
python slate/slate_multi_runner.py --json

# Assign a task
python slate/slate_multi_runner.py --assign "task-id-123"

# Complete a task
python slate/slate_multi_runner.py --complete "runner-001"

# Scale to target runner count
python slate/slate_multi_runner.py --scale 30
```

### Status Output

```
============================================================
  SLATE Multi-Runner Status
============================================================

Total Runners: 19
  Running: 3
  Idle:    15
  Error:   1
Max Parallel: 8

GPU Distribution:
  GPU 0: 1 runners
  GPU 1: 6 runners

Runners:
------------------------------------------------------------
  ID           Name                      Profile      GPU   Status
  ------------ ------------------------- ------------ ----- --------
  runner-001   slate-gpu-heavy-01        gpu_heavy    0     running
  runner-002   slate-gpu-light-02        gpu_light    1     idle
  runner-003   slate-gpu-light-03        gpu_light    1     idle
  runner-004   slate-gpu-light-04        gpu_light    1     running
  runner-005   slate-gpu-light-05        gpu_light    1     idle
  runner-006   slate-gpu-light-06        gpu_light    1     idle
  runner-007   slate-gpu-light-07        gpu_light    1     idle
  runner-008   slate-standard-08         standard     -     running
  runner-009   slate-standard-09         standard     -     idle
  runner-010   slate-standard-10         standard     -     idle
  runner-011   slate-standard-11         standard     -     idle
  runner-012   slate-light-12            light        -     idle
  runner-013   slate-light-13            light        -     idle
  ...
============================================================
```

## GitHub Actions Integration

### Workflow Integration

The Multi-Runner System integrates with GitHub Actions through:

1. **Runner Labels**: Each runner has labels matching its profile
2. **Workflow Dispatch**: Coordinator triggers workflows on specific runners
3. **Status Sync**: Runner status syncs with GitHub Actions runner status

### Workflow Configuration

```yaml
# .github/workflows/multi-runner.yml
name: Multi-Runner Task Execution

on:
  workflow_dispatch:
    inputs:
      task_id:
        description: 'Task ID to execute'
        required: true
      profile:
        description: 'Runner profile'
        required: true
        default: 'standard'
        type: choice
        options:
          - light
          - standard
          - gpu_light
          - gpu_heavy

jobs:
  execute:
    runs-on: [self-hosted, slate, "${{ inputs.profile }}"]
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Execute Task
        run: |
          python slate/slate_task_executor.py \
            --task-id "${{ inputs.task_id }}" \
            --profile "${{ inputs.profile }}"

      - name: Report Completion
        if: always()
        run: |
          python slate/slate_multi_runner.py \
            --complete "${{ runner.name }}"
```

### Runner Registration

```yaml
# Runner labels configuration
labels:
  - self-hosted
  - slate
  - ${{ runner.profile }}
  - ${{ runner.gpu_id != null && 'gpu' || 'cpu-only' }}
  - ${{ runner.gpu_id != null && 'cuda' || '' }}
```

## Resource Reservation

### GPU Memory Reservation

```
+==========================================================================+
|                       GPU MEMORY RESERVATION MAP                          |
+==========================================================================+
|                                                                           |
|   GPU 0: RTX 5070 Ti (16 GB)                                             |
|   ===================================                                     |
|   |0      4GB     8GB     12GB    16GB|                                  |
|   |[=======gpu_heavy=======]          | 8 GB reserved                    |
|   |                        [LT][LT]   | 4 GB reserved (2x gpu_light)     |
|   |                                [F]| 4 GB free                        |
|   ===================================                                     |
|                                                                           |
|   GPU 1: RTX 5070 Ti (16 GB)                                             |
|   ===================================                                     |
|   |0      4GB     8GB     12GB    16GB|                                  |
|   |[LT][LT][LT][LT][LT][LT]           | 12 GB reserved (6x gpu_light)    |
|   |                            [FREE] | 4 GB free                        |
|   ===================================                                     |
|                                                                           |
|   Legend:                                                                 |
|   [LT] = gpu_light (2 GB)                                                |
|   [F]  = Free/Available                                                  |
|                                                                           |
+==========================================================================+
```

### Reservation Protocol

1. **Static Reservation**: GPU memory is pre-allocated based on profile
2. **Exclusive Mode**: gpu_max profile gets exclusive GPU access
3. **Dynamic Adjustment**: Unused reservations can be reclaimed

## Error Handling

### Error States

| State | Cause | Recovery Action |
|-------|-------|-----------------|
| `error` | Task failure | Reset to idle after cleanup |
| `stale` | No heartbeat > 5 min | Auto-restart runner |
| `oom` | GPU out of memory | Downgrade to lighter profile |
| `timeout` | Task exceeded limit | Force kill and reset |

### Recovery Flow

```
+==========================================================================+
|                          ERROR RECOVERY FLOW                              |
+==========================================================================+
|                                                                           |
|   RUNNER ERROR DETECTED                                                  |
|   =====================                                                   |
|                |                                                          |
|                v                                                          |
|   +------------------------+                                             |
|   | Classify Error Type    |                                             |
|   +------------------------+                                             |
|                |                                                          |
|       +--------+--------+--------+                                       |
|       |        |        |        |                                       |
|       v        v        v        v                                       |
|   [timeout] [oom]   [crash]  [network]                                   |
|       |        |        |        |                                       |
|       v        v        v        v                                       |
|   +--------+ +--------+ +--------+ +--------+                            |
|   | Kill   | | Clear  | | Restart| | Retry  |                            |
|   | Task   | | GPU    | | Runner | | Connect|                            |
|   +--------+ +--------+ +--------+ +--------+                            |
|       |        |        |        |                                       |
|       +--------+--------+--------+                                       |
|                |                                                          |
|                v                                                          |
|   +------------------------+                                             |
|   | Update Runner Status   |                                             |
|   | -> "idle" or "error"   |                                             |
|   +------------------------+                                             |
|                |                                                          |
|                v                                                          |
|   +------------------------+                                             |
|   | Log Event for Metrics  |                                             |
|   +------------------------+                                             |
|                                                                           |
+==========================================================================+
```

## Monitoring

### Metrics Collected

| Metric | Type | Description |
|--------|------|-------------|
| `runners_total` | Gauge | Total configured runners |
| `runners_active` | Gauge | Currently running tasks |
| `runners_idle` | Gauge | Available for assignment |
| `runners_error` | Gauge | In error state |
| `tasks_completed_total` | Counter | Total tasks completed |
| `task_duration_seconds` | Histogram | Task execution time |
| `gpu_utilization` | Gauge | Per-GPU utilization % |
| `gpu_memory_used` | Gauge | Per-GPU memory usage |

### Dashboard Integration

The Multi-Runner status is exposed via the SLATE dashboard at `/api/runners`:

```json
{
  "total_runners": 19,
  "running": 3,
  "idle": 15,
  "error": 1,
  "max_parallel": 8,
  "gpu_distribution": {
    "GPU 0": 1,
    "GPU 1": 6
  },
  "utilization": {
    "gpu_0": 75,
    "gpu_1": 45,
    "cpu": 12
  }
}
```

## Implementation Files

| File | Purpose |
|------|---------|
| `slate/slate_multi_runner.py` | Multi-runner coordinator |
| `slate/slate_runner_benchmark.py` | Resource benchmarking |
| `.slate_runners.json` | Runner configuration state |
| `.github/workflows/multi-runner.yml` | GitHub Actions integration |

## Success Metrics

1. **Parallelism**: 19+ runners operating concurrently
2. **GPU Efficiency**: > 80% GPU utilization during workloads
3. **Assignment Speed**: < 100ms task assignment latency
4. **Error Rate**: < 1% runner error rate
5. **Recovery Time**: < 30s automatic error recovery

## Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| Auto-scaling | Dynamic runner count based on queue depth | Medium |
| Cross-node | Distributed runners across multiple machines | Low |
| Preemption | Higher priority tasks can preempt lower | Medium |
| Affinity | Prefer same runner for related tasks | Low |
| Warm pools | Pre-warmed GPU memory for fast startup | High |

---

## Specification Lock

```
+---------------------------------------------------------------+
|              MULTI-RUNNER SYSTEM SPECIFICATION LOCK            |
+---------------------------------------------------------------+
|                                                               |
|  Version: 1.0.0                                               |
|  Status: LOCKED                                               |
|  Date: 2026-02-08                                             |
|                                                               |
|  The following are immutable:                                 |
|  - Runner profile resource requirements                       |
|  - Benchmark calculation formulas                             |
|  - Assignment algorithm logic                                 |
|  - Configuration file schema                                  |
|                                                               |
|  Additive improvements only. No breaking changes.             |
|                                                               |
+---------------------------------------------------------------+
```
