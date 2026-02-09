---
name: slate-gpu
description: Manage dual-GPU load balancing for Ollama LLMs. Use for GPU status, configuration, or preloading models.
---

# /slate-gpu

Manage dual-GPU load balancing for Ollama LLMs (2x RTX 5070 Ti).

## Usage
/slate-gpu [status | configure | preload]

## Description

This skill manages dual-GPU configuration for SLATE including:
- GPU status and utilization monitoring
- Model placement across GPUs
- Load balancing configuration
- Model preloading for warm starts

## Instructions

When the user invokes this skill, run the appropriate GPU command:

**Check GPU status:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_gpu; print(slate_gpu('status'))"
```

**Configure dual-GPU:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_gpu; print(slate_gpu('configure'))"
```

**Preload models:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_gpu; print(slate_gpu('preload'))"
```

## Examples

User: "/slate-gpu"
→ Show GPU status and model placement

User: "/slate-gpu configure"
→ Set up dual-GPU environment variables

User: "Check GPU utilization"
→ Invoke this skill with status action
