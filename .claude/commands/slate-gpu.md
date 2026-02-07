# /slate-gpu

Manage dual-GPU configuration for SLATE's Ollama LLM backend.

## Usage
/slate-gpu [status | configure | preload | balance]

## Instructions

Based on the argument provided (default: status), execute the appropriate command:

**Status (default):**
```powershell
.\.venv\Scripts\python.exe slate/slate_gpu_manager.py --status
```

**Configure dual-GPU:**
```powershell
.\.venv\Scripts\python.exe slate/slate_gpu_manager.py --configure
```

**Preload models to GPUs:**
```powershell
.\.venv\Scripts\python.exe slate/slate_gpu_manager.py --preload
```

**JSON output:**
```powershell
.\.venv\Scripts\python.exe slate/slate_gpu_manager.py --json
```

## GPU Layout
- GPU 0 (Primary): slate-coder, slate-planner, mistral-nemo — heavy inference
- GPU 1 (Secondary): slate-fast, nomic-embed-text, llama3.2 — quick tasks

Report the results showing:
1. Per-GPU memory usage and temperature
2. Loaded models and their VRAM consumption
3. Any balancing recommendations
4. Configuration changes made
