# Specification: Custom SLATE Models

**Spec ID**: 020-custom-slate-models
**Status**: complete
**Created**: 2026-02-08
**Author**: Claude Opus 4.5
**Depends On**: gpu-manager, core-sdk

## Overview

This specification defines the custom Ollama-based AI models purpose-built for the SLATE agentic system. The custom models provide specialized capabilities optimized for different task types: code generation, fast classification, and planning/analysis.

The SLATE model architecture follows a **task-specialized model pattern** where different models handle different workloads based on their strengths:

```
Task Discovery → Classification (slate-fast) → Task Routing
                         ↓
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │slate-coder│   │slate-fast │   │slate-planner│
   │   (12B)   │   │    (3B)   │   │    (7B)    │
   │  GPU 0    │   │   GPU 1   │   │  GPU 0/1   │
   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │               │
         └───────────────┴───────────────┘
                         ↓
                 Task Execution
```

## Model Comparison

| Model | Parameters | Base Model | Primary GPU | Purpose | Speed | Context |
|-------|------------|------------|-------------|---------|-------|---------|
| **slate-coder** | 12.2B | mistral-nemo | GPU 0 | Code generation, review, architecture | Moderate | 8192 tokens |
| **slate-fast** | 3B | llama3.2:3b | GPU 1 | Classification, summarization, quick review | Fast | 4096 tokens |
| **slate-planner** | 7.2B | mistral:latest | GPU 0/1 | Planning, analysis, documentation | Balanced | 8192 tokens |

## Model Specifications

### slate-coder (12B)

The primary code generation model, built on `mistral-nemo` (12.2B parameters) for maximum code quality.

**Capabilities**:
- SLATE-specific code generation following project conventions
- Code review with security-focused analysis
- Architecture recommendations
- Refactoring suggestions
- Test generation

**Configuration**:
```
FROM mistral-nemo

PARAMETER temperature 0.3        # Low temp for consistent code output
PARAMETER top_p 0.9              # Nucleus sampling for quality
PARAMETER top_k 40               # Vocabulary diversity
PARAMETER num_predict 4096       # Long code generation support
PARAMETER repeat_penalty 1.1     # Avoid repetition
PARAMETER num_ctx 8192           # Large context window
```

**System Prompt Highlights**:
- Identity: SLATE-CODER autonomous coding agent
- Knows SLATE architecture (slate/, agents/, slate_core/ modules)
- Follows SLATE coding conventions:
  - 127.0.0.1 only bindings
  - Modified comment headers
  - Type hints required
  - Windows compatibility (pathlib, encoding='utf-8')
- Agent routing knowledge (ALPHA, BETA, GAMMA, DELTA, COPILOT)

**GPU Assignment**: GPU 0 (primary, larger VRAM allocation)

### slate-fast (3B)

The quick-response model for classification and triage tasks, built on `llama3.2:3b` for speed.

**Capabilities**:
- Task classification (implement, test, analyze, integrate, complex)
- Quick code review (LGTM or issues only)
- Summarization (max 3 bullet points)
- Priority assessment

**Configuration**:
```
FROM llama3.2

PARAMETER temperature 0.2        # Very low temp for classification
PARAMETER top_p 0.85             # Focused sampling
PARAMETER top_k 30               # Limited vocabulary for speed
PARAMETER num_predict 512        # Short outputs
PARAMETER repeat_penalty 1.1     # Avoid repetition
PARAMETER num_ctx 4096           # Moderate context
```

**System Prompt Highlights**:
- Identity: SLATE-FAST quick-response agent
- Output format: Single-word classification or bullet points
- Speed priority: Output only what is asked

**GPU Assignment**: GPU 1 (secondary, load-balanced with primary)

### slate-planner (7B)

The planning and analysis model, built on `mistral:latest` (7.2B parameters) for balanced reasoning.

**Capabilities**:
- Task decomposition (3-5 actionable steps)
- Architecture evaluation
- Priority assessment (critical/high/medium/low)
- Risk analysis
- Documentation generation

**Configuration**:
```
FROM mistral

PARAMETER temperature 0.4        # Slightly higher for creativity
PARAMETER top_p 0.9              # Quality sampling
PARAMETER top_k 40               # Vocabulary diversity
PARAMETER num_predict 2048       # Medium-length outputs
PARAMETER repeat_penalty 1.05    # Light repetition penalty
PARAMETER num_ctx 8192           # Large context for analysis
```

**System Prompt Highlights**:
- Identity: SLATE-PLANNER planning agent
- Structured output format: Assessment, Details, Recommendation, Priority
- Project state awareness (version, work areas, infrastructure)

**GPU Assignment**: GPU 0/1 (flexible, based on availability)

## Base Model Selection Rationale

| Base Model | Parameters | Why Selected |
|------------|------------|--------------|
| **mistral-nemo** | 12.2B | Best local code generation quality; trained on code-heavy datasets |
| **llama3.2:3b** | 3B | Fastest inference for classification; Meta's latest small model |
| **mistral:latest** | 7.2B | Strong reasoning, good at structured output; balanced speed/quality |

## Modelfile Locations

```
models/
├── Modelfile.slate-coder      # 12B code generation model
├── Modelfile.slate-fast       # 3B quick classification model
└── Modelfile.slate-planner    # 7B planning/analysis model
```

## Training Pipeline

The `slate/slate_model_trainer.py` module manages the complete model lifecycle:

### Build Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SLATE Model Build Pipeline                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Check Ollama Running ─────────────────────────────────────────▶│
│                                                                     │
│  2. Verify Base Model ────────────────────────────────────────────▶│
│     └── Pull if missing (ollama pull base-model)                    │
│                                                                     │
│  3. Build Custom Model ───────────────────────────────────────────▶│
│     └── ollama create model-name -f Modelfile.model-name            │
│                                                                     │
│  4. Save Build State ─────────────────────────────────────────────▶│
│     └── .slate_model_state.json                                     │
│                                                                     │
│  5. Log Build History ────────────────────────────────────────────▶│
│     └── slate_logs/models/trainer_YYYYMMDD.log                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Trainer Commands

```powershell
# Build all SLATE models
python slate/slate_model_trainer.py --build-all

# Build specific model
python slate/slate_model_trainer.py --build slate-coder

# Test all models with validation prompts
python slate/slate_model_trainer.py --test

# Benchmark model performance
python slate/slate_model_trainer.py --benchmark

# Update models with latest codebase context
python slate/slate_model_trainer.py --update-context

# Check model status
python slate/slate_model_trainer.py --status

# JSON output for automation
python slate/slate_model_trainer.py --json
```

### Model Testing

Each model is tested with a validation prompt and expected keywords:

| Model | Test Prompt | Expected Keywords |
|-------|-------------|-------------------|
| slate-coder | "Write a Python function that checks if Ollama is running on 127.0.0.1:11434" | urllib, 127.0.0.1, 11434, def |
| slate-fast | "Classify this task: Add unit tests for the runner manager module" | test |
| slate-planner | "Break down this task: Implement dual-GPU load balancing for model inference" | gpu, model, load |

### Benchmarking

The trainer benchmarks models across four task types:
- **code_gen**: Code generation capability
- **classify**: Task classification speed
- **plan**: Planning/decomposition quality
- **review**: Code review conciseness

Output includes tokens generated, tokens/second, and elapsed time.

## Model Selection for Task Types

The autonomous loop uses slate-fast for initial classification, then routes to the appropriate model:

| Task Type | Primary Model | Fallback Model |
|-----------|---------------|----------------|
| implement, code, build, fix | slate-coder | mistral-nemo |
| test, validate, verify | slate-coder | slate-planner |
| analyze, plan, research, document | slate-planner | mistral |
| classify, triage, summarize | slate-fast | llama3.2 |
| complex, multi-step | slate-planner | slate-coder |
| review | slate-coder | slate-fast |

## Performance Characteristics

### Inference Speed (Approximate)

| Model | Tokens/Second | Latency (First Token) | Memory Usage |
|-------|---------------|----------------------|--------------|
| slate-coder | 25-35 tok/s | ~500ms | ~8GB VRAM |
| slate-fast | 80-120 tok/s | ~100ms | ~2GB VRAM |
| slate-planner | 40-55 tok/s | ~300ms | ~5GB VRAM |

### GPU Load Balancing

The dual-GPU configuration (2x RTX 5070 Ti) enables concurrent inference:

```
GPU 0 (Primary):      GPU 1 (Secondary):
┌─────────────────┐   ┌─────────────────┐
│  slate-coder    │   │  slate-fast     │
│  (12B, warm)    │   │  (3B, warm)     │
├─────────────────┤   ├─────────────────┤
│  slate-planner  │   │  (overflow)     │
│  (7B, on-demand)│   │                 │
└─────────────────┘   └─────────────────┘
```

Models are pre-warmed based on priority:
1. slate-coder (priority 1, always warm on GPU 0)
2. slate-fast (priority 2, always warm on GPU 1)
3. slate-planner (priority 3, loaded on-demand)

## Context Update Mechanism

The trainer can dynamically update the slate-coder Modelfile with current project state:

```python
# Injected into SYSTEM prompt:
## Current Project State
- Core modules: 42 files in slate/
- Agent modules: 8 files in agents/
- Test files: 35 files in tests/
- Workflows: 15 files in .github/workflows/
- Pending tasks: 5
- Completed tasks: 127

### Key Modules
- action_guard.py
- integrated_autonomous_loop.py
- mcp_server.py
- ...
```

This keeps the model aware of the current codebase structure.

## State Management

Build and test state is persisted in `.slate_model_state.json`:

```json
{
  "models_built": {
    "slate-coder": {
      "built_at": "2026-02-08T06:00:00Z",
      "base": "mistral-nemo:latest",
      "build_time_s": 45.2,
      "modelfile": "Modelfile.slate-coder"
    }
  },
  "last_build": "2026-02-08T06:00:00Z",
  "last_test": "2026-02-08T06:15:00Z",
  "build_history": [...],
  "test_results": {...}
}
```

## Kubernetes Integration

When running in Kubernetes, the model trainer detects the `slate-model-trainer` CronJob:

```yaml
# K8s CronJob for scheduled model updates
apiVersion: batch/v1
kind: CronJob
metadata:
  name: slate-model-trainer
  namespace: slate
spec:
  schedule: "0 2 * * 0"  # Weekly Sunday 2am
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: trainer
            command: ["python", "slate/slate_model_trainer.py", "--update-context"]
```

## Security Considerations

1. **Local-only inference**: All models run on local GPUs, no cloud API calls
2. **Network binding**: Model trainer only connects to 127.0.0.1:11434
3. **No data exfiltration**: Training context is derived from local codebase only
4. **ActionGuard validation**: Model outputs are validated before execution

## Tech Tree Integration

```
gpu-manager ─────────────────────────▶ custom-models
                                            │
                                            ▼
                                     autonomous-loop
```

The custom-models node depends on gpu-manager for dual-GPU placement and feeds into the autonomous-loop for task execution.

## File Manifest

| File | Purpose |
|------|---------|
| `models/Modelfile.slate-coder` | 12B code generation model definition |
| `models/Modelfile.slate-fast` | 3B quick classification model definition |
| `models/Modelfile.slate-planner` | 7B planning model definition |
| `slate/slate_model_trainer.py` | Model build, test, and benchmark CLI |
| `.slate_model_state.json` | Build/test state persistence |
| `slate_logs/models/` | Trainer logs directory |

## Success Metrics

1. **Build Success**: All 3 models build without errors
2. **Test Validation**: All models pass keyword validation tests
3. **Performance**: slate-fast > 80 tok/s, slate-coder > 25 tok/s
4. **GPU Utilization**: Balanced load across both GPUs
5. **Context Freshness**: Models updated weekly with latest codebase

---

*This specification documents the SLATE custom model architecture as of version 2.4.0.*
