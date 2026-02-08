#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# CELL: slate_benchmark [python]
# Author: COPILOT | Created: 2026-02-06T00:30:00Z | Modified: 2026-02-06T00:30:00Z
# Purpose: System benchmark for SLATE
# ═══════════════════════════════════════════════════════════════════════════════
"""
SLATE Benchmark
===============
Run system benchmarks to check performance.

Usage:
    python slate/slate_benchmark.py
    python slate/slate_benchmark.py --json
"""

import argparse
import json
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def benchmark_cpu_single():
    """Single-threaded CPU benchmark."""
    start = time.perf_counter()
    total = 0.0
    for i in range(1, 100001):
        total += i ** 0.5
    elapsed = time.perf_counter() - start
    return {"name": "cpu_single", "ops": 100000, "time_sec": round(elapsed, 4), "ops_per_sec": round(100000/elapsed, 0)}


def benchmark_memory():
    # Modified: 2026-02-07T19:20:00Z | Author: COPILOT | Change: Clarify CPU memory benchmark
    """CPU memory allocation benchmark."""
    start = time.perf_counter()
    data = []
    for _ in range(1000):
        data.append(bytearray(10000))
    elapsed = time.perf_counter() - start
    del data
    return {"name": "memory_alloc", "ops": 1000, "time_sec": round(elapsed, 4), "mb_allocated": 10}


def _get_slate_task_activity() -> dict:
    # Modified: 2026-02-07T19:40:00Z | Author: COPILOT | Change: Detect active SLATE tasks for benchmark scheduling
    """Return SLATE task activity for adaptive benchmark scheduling."""
    workspace = Path(__file__).parent.parent
    task_file = workspace / "current_tasks.json"
    if not task_file.exists():
        return {"in_progress": 0, "pending": 0, "total": 0}

    try:
        data = json.loads(task_file.read_text(encoding="utf-8"))
        tasks = data.get("tasks", [])
        in_progress = sum(1 for t in tasks if t.get("status") == "in-progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        return {"in_progress": in_progress, "pending": pending, "total": len(tasks)}
    except Exception:
        return {"in_progress": 0, "pending": 0, "total": 0}


def _get_gpu_utilization() -> int | None:
    # Modified: 2026-02-07T19:40:00Z | Author: COPILOT | Change: Read GPU utilization for adaptive benchmarking
    """Return GPU utilization percentage via nvidia-smi if available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            util_vals = [int(v.strip()) for v in result.stdout.splitlines() if v.strip().isdigit()]
            return max(util_vals) if util_vals else None
    except Exception:
        pass
    return None


def benchmark_gpu_memory(target_mb: int | None = None):
    # Modified: 2026-02-07T19:40:00Z | Author: COPILOT | Change: Make GPU memory target adaptive to SLATE scheduling
    """GPU memory allocation benchmark (AI memory target on GPU).

    Adaptive behavior: targets a fraction of currently free GPU memory, scaled
    by current GPU utilization and SLATE task activity to avoid overlap.
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return {"name": "gpu_memory", "available": False}

        device = torch.device("cuda")
        free_bytes, total_bytes = torch.cuda.mem_get_info(0)
        free_mb = int(free_bytes / (1024 * 1024))
        total_mb = int(total_bytes / (1024 * 1024))

        adaptive_used = target_mb is None
        task_activity = _get_slate_task_activity()
        gpu_util = _get_gpu_utilization()

        # Scheduling-aware policy
        busy = (task_activity.get("in_progress", 0) > 0) or ((gpu_util or 0) >= 60)
        very_busy = (task_activity.get("in_progress", 0) >= 2) or ((gpu_util or 0) >= 80)

        if free_mb < 256 or very_busy:
            return {
                "name": "gpu_memory",
                "available": False,
                "reason": "GPU busy or low free memory",
                "free_mb": free_mb,
                "total_mb": total_mb,
                "gpu_utilization_pct": gpu_util,
                "in_progress_tasks": task_activity.get("in_progress", 0),
            }

        # Adaptive target: scale down if busy, otherwise use 25% of free VRAM
        if adaptive_used:
            scale = 0.10 if busy else 0.25
            min_mb = 128 if busy else 256
            max_mb = 512 if busy else 2048
            target_mb = max(min_mb, min(int(free_mb * scale), max_mb))

        torch.cuda.synchronize()
        start = time.perf_counter()

        # Allocate target_mb on GPU using float32 (4 bytes each)
        num_floats = (target_mb * 1024 * 1024) // 4
        buf = torch.empty(num_floats, dtype=torch.float32, device=device)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        # Touch buffer to ensure allocation is realized
        _ = buf.sum().item()
        del buf
        torch.cuda.synchronize()

        return {
            "name": "gpu_memory",
            "available": True,
            "device": torch.cuda.get_device_name(0),
            "target_mb": target_mb,
            "free_mb": free_mb,
            "total_mb": total_mb,
            "strategy": "adaptive" if adaptive_used else "fixed",
            "policy": "busy" if busy else "normal",
            "gpu_utilization_pct": gpu_util,
            "in_progress_tasks": task_activity.get("in_progress", 0),
            "time_sec": round(elapsed, 4),
        }
    except ImportError:
        return {"name": "gpu_memory", "available": False, "reason": "PyTorch not installed"}
    except Exception as e:
        return {"name": "gpu_memory", "available": False, "error": str(e)}


def benchmark_disk():
    """Disk I/O benchmark."""
    import tempfile
    from pathlib import Path

    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        testfile = Path(tmpdir) / "benchmark.bin"
        data = b"x" * (1024 * 1024)  # 1 MB
        for _ in range(10):
            testfile.write_bytes(data)
            _ = testfile.read_bytes()
    elapsed = time.perf_counter() - start
    return {"name": "disk_io", "ops": 20, "time_sec": round(elapsed, 4), "mb_transferred": 20}


def benchmark_gpu():
    """GPU benchmark (if available)."""
    try:
        import torch
        if not torch.cuda.is_available():
            return {"name": "gpu", "available": False}

        device = torch.device("cuda")
        torch.cuda.synchronize()
        start = time.perf_counter()

        a = torch.randn(2000, 2000, device=device)
        b = torch.randn(2000, 2000, device=device)
        for _ in range(10):
            _ = torch.matmul(a, b)

        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        return {
            "name": "gpu_matmul",
            "available": True,
            "device": torch.cuda.get_device_name(0),
            "ops": 10,
            "time_sec": round(elapsed, 4),
            "gflops": round((10 * 2 * 2000**3) / elapsed / 1e9, 2)
        }
    except ImportError:
        return {"name": "gpu", "available": False, "reason": "PyTorch not installed"}
    except Exception as e:
        return {"name": "gpu", "available": False, "error": str(e)}


# Modified: 2026-02-09T05:00:00Z | Author: COPILOT | Change: Add K8s cluster benchmark
def benchmark_kubernetes():
    """Benchmark Kubernetes cluster — pod readiness latency and deployment health."""
    try:
        import subprocess as _sp
        import time as _time

        # Check kubectl availability
        r = _sp.run(["kubectl", "version", "--client"],
                    capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return {"name": "kubernetes", "available": False, "reason": "kubectl not found"}

        # Measure deployment query latency
        start = _time.perf_counter()
        r = _sp.run(["kubectl", "get", "deployments", "-n", "slate", "-o", "json"],
                    capture_output=True, text=True, timeout=15)
        query_time = _time.perf_counter() - start

        if r.returncode != 0:
            return {"name": "kubernetes", "available": False, "reason": "cluster unreachable"}

        deploys = json.loads(r.stdout).get("items", [])
        total = len(deploys)
        ready = sum(1 for d in deploys
                    if d.get("status", {}).get("readyReplicas", 0) == d.get("spec", {}).get("replicas", 1))

        # Measure pod query latency
        start2 = _time.perf_counter()
        r2 = _sp.run(["kubectl", "get", "pods", "-n", "slate", "--no-headers"],
                     capture_output=True, text=True, timeout=15)
        pod_query_time = _time.perf_counter() - start2
        pod_count = len([l for l in r2.stdout.strip().splitlines() if l.strip()]) if r2.returncode == 0 else 0

        return {
            "name": "kubernetes",
            "available": True,
            "deployments_total": total,
            "deployments_ready": ready,
            "pods": pod_count,
            "deploy_query_sec": round(query_time, 4),
            "pod_query_sec": round(pod_query_time, 4),
        }
    except FileNotFoundError:
        return {"name": "kubernetes", "available": False, "reason": "kubectl not installed"}
    except Exception as e:
        return {"name": "kubernetes", "available": False, "error": str(e)}


def run_benchmarks():
    """Run all benchmarks."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "benchmarks": []
    }

    print("Running benchmarks...")

    # Modified: 2026-02-09T05:00:00Z | Author: COPILOT | Change: Add K8s benchmark step
    print("  [1/6] CPU single-threaded...")
    results["benchmarks"].append(benchmark_cpu_single())

    print("  [2/6] Memory allocation (CPU)...")
    results["benchmarks"].append(benchmark_memory())

    print("  [3/6] Memory allocation (GPU target)...")
    results["benchmarks"].append(benchmark_gpu_memory())

    print("  [4/6] Disk I/O...")
    results["benchmarks"].append(benchmark_disk())

    print("  [5/6] GPU compute...")
    results["benchmarks"].append(benchmark_gpu())

    print("  [6/6] Kubernetes cluster...")
    results["benchmarks"].append(benchmark_kubernetes())

    return results


def print_results(results: dict):
    """Print benchmark results."""
    print()
    print("=" * 50)
    print("  S.L.A.T.E. Benchmark Results")
    print("=" * 50)
    print()

    for b in results["benchmarks"]:
        name = b["name"]
        if name == "cpu_single":
            print(f"  CPU:    {b['ops_per_sec']:,.0f} ops/sec ({b['time_sec']}s)")
        elif name == "memory_alloc":
            print(f"  Memory: {b['mb_allocated']} MB in {b['time_sec']}s")
        elif name == "gpu_memory" and b.get("available"):
            strategy = b.get("strategy", "adaptive")
            policy = b.get("policy", "normal")
            free_mb = b.get("free_mb")
            total_mb = b.get("total_mb")
            util = b.get("gpu_utilization_pct")
            tasks = b.get("in_progress_tasks")
            mem_note = f" ({free_mb}/{total_mb} MB free)" if free_mb and total_mb else ""
            util_note = f", util {util}%" if util is not None else ""
            task_note = f", tasks {tasks}" if tasks is not None else ""
            print(f"  GPU Mem: {b['target_mb']} MB on {b['device']} in {b['time_sec']}s [{strategy}/{policy}]{mem_note}{util_note}{task_note}")
        elif name == "gpu_memory" and not b.get("available"):
            reason = b.get("reason")
            util = b.get("gpu_utilization_pct")
            tasks = b.get("in_progress_tasks")
            extra = []
            if util is not None:
                extra.append(f"util {util}%")
            if tasks is not None:
                extra.append(f"tasks {tasks}")
            suffix = f" ({reason}; {', '.join(extra)})" if reason and extra else f" ({reason})" if reason else ""
            print(f"  GPU Mem: Not available{suffix}")
        elif name == "disk_io":
            print(f"  Disk:   {b['mb_transferred']} MB in {b['time_sec']}s")
        elif name == "gpu_matmul" and b.get("available"):
            print(f"  GPU:    {b['gflops']} GFLOPS on {b['device']}")
        elif name == "gpu" and not b.get("available"):
            print("  GPU:    Not available")
        # Modified: 2026-02-09T05:00:00Z | Author: COPILOT | Change: Add K8s benchmark rendering
        elif name == "kubernetes" and b.get("available"):
            print(f"  K8s:    {b['deployments_ready']}/{b['deployments_total']} deploys, {b['pods']} pods (query {b['deploy_query_sec']}s)")
        elif name == "kubernetes" and not b.get("available"):
            reason = b.get("reason", b.get("error", "unavailable"))
            print(f"  K8s:    Not available ({reason})")

    print()
    print("=" * 50)
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SLATE Benchmark")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = run_benchmarks()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
