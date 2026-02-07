# /slate-multirunner

Manage SLATE multi-runner system for parallel task execution.

## Usage
/slate-multirunner [--status | --init | --benchmark]

## Instructions

Based on the argument provided (default: --status):

**For status check (default):**
```bash
./.venv/Scripts/python.exe slate/slate_multi_runner.py
```

**For initialization:**
```bash
./.venv/Scripts/python.exe slate/slate_multi_runner.py --init
```

**For benchmark:**
```bash
./.venv/Scripts/python.exe slate/slate_runner_benchmark.py
```

Report findings including:
1. Total runners configured
2. Running/idle/error counts
3. GPU distribution
4. Per-runner status

## Multi-Runner Architecture

SLATE supports up to 19 parallel runners distributed across resources:

| Profile | GPU | Count | Use Case |
|---------|-----|-------|----------|
| gpu_heavy | 0 | 1 | Large model inference |
| gpu_light | 1 | 6 | Small inference tasks |
| standard | CPU | 4 | Tests, validation |
| light | CPU | 8 | Lint, format checks |

## Resource Requirements

| Profile | GPU Memory | CPU Cores | RAM |
|---------|------------|-----------|-----|
| light | 0 | 1 | 512MB |
| standard | 0 | 2 | 1GB |
| gpu_light | 2GB | 2 | 2GB |
| gpu_heavy | 8GB | 4 | 8GB |

ARGUMENTS: --status
