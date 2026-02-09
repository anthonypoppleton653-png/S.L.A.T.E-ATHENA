---
description: Manage dual-GPU load balancing
---

# /slate-gpu

Manage SLATE dual-GPU load balancing for Ollama LLMs.

## Usage

```
/slate-gpu [action]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | GPU and model placement (default) |
| `configure` | Set up dual-GPU environment |
| `preload` | Warm models on GPUs |

## Instructions

**Status:**
```bash
.venv/Scripts/python.exe slate/slate_gpu_manager.py --status
```

**Configure:**
```bash
.venv/Scripts/python.exe slate/slate_gpu_manager.py --configure
```

**Preload:**
```bash
.venv/Scripts/python.exe slate/slate_gpu_manager.py --preload
```
