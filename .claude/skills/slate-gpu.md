# SLATE GPU Skill

Monitor and manage GPU resources for AI workloads.

## Hardware

- **GPUs**: 2x NVIDIA RTX 5070 Ti
- **Architecture**: Blackwell
- **VRAM**: 16GB each (32GB total)
- **CUDA**: Available

## Commands

### Quick GPU Check
```powershell
nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv
```

### Detailed GPU Info
```powershell
nvidia-smi
```

### GPU via SLATE
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status
```

### PyTorch CUDA Check
```powershell
.\.venv\Scripts\python.exe -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Devices: {torch.cuda.device_count()}')"
```

## MCP Tool

Use `slate_gpu_info` to get detailed GPU information programmatically.

## Dashboard

GPU status is shown at http://127.0.0.1:8080 in the GPU Status panel.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CUDA_VISIBLE_DEVICES` | Control which GPUs are visible |
| `SLATE_GPU_COUNT` | Number of GPUs detected |
| `SLATE_GPU_0` | Name of GPU 0 |
| `SLATE_GPU_1` | Name of GPU 1 |

## Multi-GPU Usage

Both GPUs are available for SLATE workloads:
- GPU 0: Primary for AI inference
- GPU 1: Secondary for parallel tasks

Set `CUDA_VISIBLE_DEVICES=0,1` to use both (default).
