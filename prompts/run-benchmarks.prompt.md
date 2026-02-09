---
name: run-benchmarks
agent: 'agent'
description: 'Execute comprehensive GPU and inference benchmarks for SLATE'
tags: [benchmark, gpu, performance, inference]
model: 'slate-coder'
# Modified: 2026-02-09T02:47:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from sonnet→slate-coder (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# Run SLATE Benchmarks

Execute comprehensive benchmarks to measure system performance.

## Quick Benchmark

Run a quick system benchmark:

```powershell
python slate/slate_benchmark.py
```

## Detailed Benchmarks

### GPU Memory and Compute

```powershell
python slate/slate_hardware_optimizer.py --benchmark
```

### Inference Performance

Test Ollama model inference speeds:

```powershell
python slate/ml_orchestrator.py --benchmarks
```

Expected output for RTX 5070 Ti (Blackwell):
- slate-coder (12B): ~91 tokens/sec
- slate-fast (3B): ~308 tokens/sec
- slate-planner (7B): ~154 tokens/sec

### SLATE Custom Model Test

```powershell
python slate/slate_model_trainer.py --benchmark
```

## Benchmark Results Format

Results should include:

| Metric | Value | Target |
|--------|-------|--------|
| GPU Memory Available | XX GB | 16 GB |
| CUDA Compute | XX.X | 12.0+ |
| Inference Speed | XX tok/s | 100+ tok/s |
| Index Build Time | XX sec | <60 sec |
| ChromaDB Query | XX ms | <100 ms |

## Performance Optimization

If benchmarks are below targets:

1. **Low inference speed**: Check GPU utilization, model placement
   ```powershell
   python slate/slate_gpu_manager.py --status
   ```

2. **High memory usage**: Review model loading strategy
   ```powershell
   python slate/slate_gpu_manager.py --preload
   ```

3. **Slow queries**: Rebuild vector index
   ```powershell
   python slate/slate_chromadb.py --reset && python slate/slate_chromadb.py --index
   ```
