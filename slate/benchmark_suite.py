#!/usr/bin/env python3
# Modified: 2026-02-09T15:26:00-05:00 | Author: Gemini (Antigravity)
# Change: Create comprehensive benchmark suite (T-025-005, T-025-006, T-025-007)
# NOTE: All AIs modifying this file must add a dated comment.
"""
SLATE Benchmark Suite
=====================

Comprehensive hardware profiling for Spec 025 onboarding:
  - T-025-005: GPU inference, VRAM, thermal, CPU, storage, memory, network
  - T-025-006: Performance Profile Card (ASCII, HTML, JSON)
  - T-025-007: Thermal Policy System (aggressive/balanced/quiet/endurance)

Usage:
    python -m slate.benchmark_suite               # Full benchmark
    python -m slate.benchmark_suite --quick        # Fast subset (~15s)
    python -m slate.benchmark_suite --card         # Show profile card
    python -m slate.benchmark_suite --json         # JSON output
    python -m slate.benchmark_suite --thermal      # Show thermal policy
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─── Constants ──────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
RESULTS_DIR = WORKSPACE / ".slate_analytics"
RESULTS_FILE = RESULTS_DIR / "benchmark_results.json"
THERMAL_CONFIG = WORKSPACE / ".slate_config" / "thermal.yaml"


# ─── Enums ──────────────────────────────────────────────────────────────

class BenchmarkCategory(Enum):
    GPU_INFERENCE = "gpu_inference"
    GPU_VRAM = "gpu_vram"
    GPU_THERMAL = "gpu_thermal"
    GPU_COMPUTE = "gpu_compute"
    CPU_SINGLE = "cpu_single"
    CPU_MULTI = "cpu_multi"
    MEMORY_BANDWIDTH = "memory_bandwidth"
    STORAGE_IOPS = "storage_iops"
    STORAGE_SEQ = "storage_sequential"
    NETWORK_LATENCY = "network_latency"


class ThermalPolicy(Enum):
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    QUIET = "quiet"
    ENDURANCE = "endurance"


class ScoreTier(Enum):
    WORKSTATION = "Workstation"
    PROFESSIONAL = "Professional"
    STANDARD = "Standard"
    BASIC = "Basic"
    MINIMAL = "Minimal"


# ─── Data Classes ───────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    category: str
    name: str
    score: float = 0.0          # 0-100 normalized score
    value: float = 0.0          # Raw metric
    unit: str = ""
    available: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_sec: float = 0.0


@dataclass
class ProfileCard:
    """System performance profile card."""
    timestamp: str = ""
    hostname: str = ""
    overall_score: float = 0.0
    tier: str = ""
    results: List[Dict] = field(default_factory=list)
    gpu_name: str = "N/A"
    gpu_vram_mb: int = 0
    cpu_cores: int = 0
    ram_gb: float = 0.0
    recommended_thermal: str = "balanced"
    recommended_models: List[str] = field(default_factory=list)


@dataclass
class ThermalConfig:
    """Thermal policy configuration."""
    policy: str = "balanced"
    gpu_power_limit_pct: int = 100
    max_temp_c: int = 85
    throttle_temp_c: int = 80
    fan_curve: str = "auto"
    description: str = ""


# ─── GPU Benchmarks ────────────────────────────────────────────────────

def benchmark_gpu_inference() -> BenchmarkResult:
    """Benchmark Ollama inference throughput (tok/s)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.GPU_INFERENCE.value,
        name="Ollama Inference Throughput"
    )
    try:
        # Check Ollama availability
        check = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        if check.returncode != 0:
            result.available = False
            result.error = "Ollama not running"
            return result

        models = [l.split()[0] for l in check.stdout.strip().splitlines()[1:]
                   if l.strip() and not l.startswith("NAME")]

        if not models:
            result.available = False
            result.error = "No models available"
            return result

        # Pick a small model for benchmarking
        test_model = None
        preferred = ["qwen2.5:0.5b", "qwen2.5:1.5b", "phi3:mini", "llama3.2:1b", "gemma2:2b"]
        for pref in preferred:
            if any(pref in m for m in models):
                test_model = next(m for m in models if pref in m)
                break
        if not test_model:
            test_model = models[0]

        # Run inference benchmark
        prompt = "Write a brief summary of the benefits of local AI inference in exactly three sentences."
        start = time.perf_counter()
        resp = subprocess.run(
            ["ollama", "run", test_model, prompt],
            capture_output=True, text=True, timeout=120
        )
        elapsed = time.perf_counter() - start

        if resp.returncode != 0:
            result.available = False
            result.error = f"Inference failed: {resp.stderr[:200]}"
            return result

        output = resp.stdout.strip()
        # Rough token count: ~4 chars per token
        approx_tokens = max(len(output) // 4, 1)
        tok_per_sec = approx_tokens / elapsed if elapsed > 0 else 0

        result.value = round(tok_per_sec, 1)
        result.unit = "tok/s"
        result.duration_sec = round(elapsed, 2)
        result.details = {
            "model": test_model,
            "prompt_length": len(prompt),
            "output_length": len(output),
            "approx_tokens": approx_tokens,
        }

        # Score: 0-100 based on tok/s (100 = 100+ tok/s)
        result.score = min(100, round(tok_per_sec))

    except FileNotFoundError:
        result.available = False
        result.error = "Ollama not installed"
    except subprocess.TimeoutExpired:
        result.available = False
        result.error = "Inference timed out (>120s)"
    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


def benchmark_gpu_vram() -> BenchmarkResult:
    """Profile GPU VRAM capacity and bandwidth."""
    result = BenchmarkResult(
        category=BenchmarkCategory.GPU_VRAM.value,
        name="GPU VRAM Profile"
    )
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,memory.used,temperature.gpu,power.draw,power.limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if smi.returncode != 0:
            result.available = False
            result.error = "nvidia-smi failed"
            return result

        gpus = []
        for line in smi.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append({
                    "name": parts[0],
                    "total_mb": int(float(parts[1])),
                    "free_mb": int(float(parts[2])),
                    "used_mb": int(float(parts[3])),
                    "temp_c": int(float(parts[4])) if parts[4].strip() != "[N/A]" else None,
                    "power_w": float(parts[5]) if parts[5].strip() != "[N/A]" else None,
                    "power_limit_w": float(parts[6]) if parts[6].strip() != "[N/A]" else None,
                })

        if not gpus:
            result.available = False
            result.error = "No GPU data"
            return result

        total_vram = sum(g["total_mb"] for g in gpus)
        result.value = total_vram
        result.unit = "MB VRAM"
        result.details = {"gpus": gpus, "gpu_count": len(gpus)}

        # Score: 0-100 based on total VRAM (100 = 24GB+)
        result.score = min(100, round(total_vram / 245.76))  # 24576 MB = 100

    except FileNotFoundError:
        result.available = False
        result.error = "nvidia-smi not found"
    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


def benchmark_gpu_thermal() -> BenchmarkResult:
    """Profile GPU thermal behavior under load (5-second stress test)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.GPU_THERMAL.value,
        name="GPU Thermal Profile"
    )
    try:
        # Get idle temperature
        idle_temp = _get_gpu_temp()
        if idle_temp is None:
            result.available = False
            result.error = "Cannot read GPU temperature"
            return result

        # Stress test: run GPU compute for 5 seconds
        try:
            import torch
            if not torch.cuda.is_available():
                result.available = False
                result.error = "CUDA not available"
                return result

            device = torch.device("cuda")
            temps = [idle_temp]
            start = time.perf_counter()

            while time.perf_counter() - start < 5.0:
                a = torch.randn(3000, 3000, device=device)
                b = torch.randn(3000, 3000, device=device)
                _ = torch.matmul(a, b)
                torch.cuda.synchronize()
                t = _get_gpu_temp()
                if t is not None:
                    temps.append(t)
                del a, b

            elapsed = time.perf_counter() - start
        except ImportError:
            # No torch — use nvidia-smi query only
            result.details = {"idle_temp_c": idle_temp, "note": "PyTorch not available for stress test"}
            result.value = idle_temp
            result.unit = "°C idle"
            result.score = max(0, 100 - idle_temp)
            return result

        peak_temp = max(temps)
        delta = peak_temp - idle_temp

        result.value = peak_temp
        result.unit = "°C peak"
        result.duration_sec = round(elapsed, 2)
        result.details = {
            "idle_temp_c": idle_temp,
            "peak_temp_c": peak_temp,
            "delta_c": delta,
            "samples": len(temps),
            "thermal_headroom_c": max(0, 90 - peak_temp),
        }

        # Score: 100 = cool (peak < 60°C), 0 = hot (peak > 95°C)
        result.score = max(0, min(100, round((95 - peak_temp) * 2.86)))

    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


def _get_gpu_temp() -> Optional[int]:
    """Read current GPU temperature from nvidia-smi."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            return int(r.stdout.strip().splitlines()[0].strip())
    except Exception:
        pass
    return None


# ─── CPU Benchmarks ────────────────────────────────────────────────────

def benchmark_cpu_single() -> BenchmarkResult:
    """Single-threaded CPU benchmark (math-intensive)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.CPU_SINGLE.value,
        name="CPU Single-Thread"
    )
    start = time.perf_counter()
    total = 0.0
    ops = 200_000
    for i in range(1, ops + 1):
        total += math.sqrt(i) * math.log(i + 1) * math.sin(i)
    elapsed = time.perf_counter() - start

    ops_per_sec = ops / elapsed
    result.value = round(ops_per_sec, 0)
    result.unit = "ops/s"
    result.duration_sec = round(elapsed, 3)
    result.details = {"ops": ops, "elapsed_sec": round(elapsed, 4)}

    # Score: 100 = 500K ops/s, 0 = 50K ops/s
    result.score = max(0, min(100, round((ops_per_sec - 50000) / 4500)))
    return result


def benchmark_cpu_multi() -> BenchmarkResult:
    """Multi-threaded CPU benchmark."""
    result = BenchmarkResult(
        category=BenchmarkCategory.CPU_MULTI.value,
        name="CPU Multi-Thread"
    )
    cores = os.cpu_count() or 2
    ops_per_thread = 100_000

    def _work():
        total = 0.0
        for i in range(1, ops_per_thread + 1):
            total += math.sqrt(i) * math.log(i + 1)
        return total

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=cores) as pool:
        futures = [pool.submit(_work) for _ in range(cores)]
        for f in as_completed(futures):
            f.result()
    elapsed = time.perf_counter() - start

    total_ops = cores * ops_per_thread
    ops_per_sec = total_ops / elapsed
    result.value = round(ops_per_sec, 0)
    result.unit = "ops/s"
    result.duration_sec = round(elapsed, 3)
    result.details = {
        "cores": cores,
        "ops_per_thread": ops_per_thread,
        "total_ops": total_ops,
        "speedup_vs_single": round(cores * 0.75, 1),  # Estimated
    }

    # Score: 100 = 4M ops/s, 0 = 200K ops/s
    result.score = max(0, min(100, round((ops_per_sec - 200000) / 38000)))
    return result


# ─── Memory Benchmark ──────────────────────────────────────────────────

def benchmark_memory_bandwidth() -> BenchmarkResult:
    """Memory bandwidth test (sequential read/write throughput)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.MEMORY_BANDWIDTH.value,
        name="Memory Bandwidth"
    )
    block_size = 64 * 1024 * 1024  # 64 MB blocks
    iterations = 5

    # Write benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        data = bytearray(block_size)
        for i in range(0, block_size, 4096):
            data[i] = 0xFF
    write_elapsed = time.perf_counter() - start

    # Read benchmark
    data = bytearray(block_size)
    start = time.perf_counter()
    total = 0
    for _ in range(iterations):
        for i in range(0, block_size, 4096):
            total += data[i]
    read_elapsed = time.perf_counter() - start

    total_mb = (block_size * iterations) / (1024 * 1024)
    write_mbps = total_mb / write_elapsed if write_elapsed > 0 else 0
    read_mbps = total_mb / read_elapsed if read_elapsed > 0 else 0
    combined = (write_mbps + read_mbps) / 2

    result.value = round(combined, 0)
    result.unit = "MB/s"
    result.duration_sec = round(write_elapsed + read_elapsed, 3)
    result.details = {
        "write_mbps": round(write_mbps, 0),
        "read_mbps": round(read_mbps, 0),
        "block_size_mb": block_size // (1024 * 1024),
        "iterations": iterations,
    }

    # Score: 100 = 10GB/s+, 0 = 500MB/s
    result.score = max(0, min(100, round((combined - 500) / 95)))

    del data
    return result


# ─── Storage Benchmarks ────────────────────────────────────────────────

def benchmark_storage_iops() -> BenchmarkResult:
    """Storage random I/O benchmark (small file ops)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.STORAGE_IOPS.value,
        name="Storage IOPS"
    )
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            files_count = 200
            data = os.urandom(4096)  # 4KB random blocks

            # Write IOPS
            start = time.perf_counter()
            for i in range(files_count):
                p = Path(tmpdir) / f"iops_{i}.bin"
                p.write_bytes(data)
            write_elapsed = time.perf_counter() - start

            # Read IOPS
            start = time.perf_counter()
            for i in range(files_count):
                p = Path(tmpdir) / f"iops_{i}.bin"
                _ = p.read_bytes()
            read_elapsed = time.perf_counter() - start

        write_iops = files_count / write_elapsed if write_elapsed > 0 else 0
        read_iops = files_count / read_elapsed if read_elapsed > 0 else 0
        combined = (write_iops + read_iops) / 2

        result.value = round(combined, 0)
        result.unit = "IOPS"
        result.duration_sec = round(write_elapsed + read_elapsed, 3)
        result.details = {
            "write_iops": round(write_iops, 0),
            "read_iops": round(read_iops, 0),
            "block_size": "4KB",
            "files": files_count,
        }

        # Score: 100 = 10K IOPS (Python I/O), 0 = 200 IOPS
        result.score = max(0, min(100, round((combined - 200) / 98)))

    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


def benchmark_storage_sequential() -> BenchmarkResult:
    """Storage sequential read/write benchmark."""
    result = BenchmarkResult(
        category=BenchmarkCategory.STORAGE_SEQ.value,
        name="Storage Sequential I/O"
    )
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            testfile = Path(tmpdir) / "seq_benchmark.bin"
            block = os.urandom(1024 * 1024)  # 1 MB
            rounds = 20  # 20 MB total

            # Sequential write
            start = time.perf_counter()
            with open(testfile, "wb") as f:
                for _ in range(rounds):
                    f.write(block)
                f.flush()
                os.fsync(f.fileno())
            write_elapsed = time.perf_counter() - start

            # Sequential read
            start = time.perf_counter()
            with open(testfile, "rb") as f:
                while f.read(1024 * 1024):
                    pass
            read_elapsed = time.perf_counter() - start

        write_mbps = rounds / write_elapsed if write_elapsed > 0 else 0
        read_mbps = rounds / read_elapsed if read_elapsed > 0 else 0

        result.value = round((write_mbps + read_mbps) / 2, 0)
        result.unit = "MB/s"
        result.duration_sec = round(write_elapsed + read_elapsed, 3)
        result.details = {
            "write_mbps": round(write_mbps, 0),
            "read_mbps": round(read_mbps, 0),
            "total_mb": rounds,
        }

        # Score: 100 = 3GB/s, 0 = 100MB/s
        result.score = max(0, min(100, round((result.value - 100) / 29)))

    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


# ─── Network Benchmark ─────────────────────────────────────────────────

def benchmark_network_latency() -> BenchmarkResult:
    """Network latency test (DNS + HTTP to common endpoints)."""
    result = BenchmarkResult(
        category=BenchmarkCategory.NETWORK_LATENCY.value,
        name="Network Latency"
    )
    try:
        import urllib.request

        endpoints = [
            ("GitHub API", "https://api.github.com"),
            ("Ollama Hub", "https://ollama.com"),
        ]

        latencies = []
        details = {}
        for name, url in endpoints:
            try:
                start = time.perf_counter()
                req = urllib.request.Request(url, method="HEAD")
                urllib.request.urlopen(req, timeout=10)
                ms = (time.perf_counter() - start) * 1000
                latencies.append(ms)
                details[name] = round(ms, 1)
            except Exception:
                details[name] = None

        if not latencies:
            result.available = False
            result.error = "All endpoints unreachable"
            return result

        avg = sum(latencies) / len(latencies)
        result.value = round(avg, 1)
        result.unit = "ms avg"
        result.details = {"endpoints": details}

        # Score: 100 = <50ms, 0 = >2000ms
        result.score = max(0, min(100, round(100 - (avg - 50) / 19.5)))

    except Exception as e:
        result.available = False
        result.error = str(e)

    return result


# ─── Benchmark Runner ──────────────────────────────────────────────────

# Modified: 2026-02-09T20:30:00Z | Author: COPILOT | Change: Add quiet parameter to suppress stdout progress when --json is used
def run_full_suite(quick: bool = False, quiet: bool = False) -> List[BenchmarkResult]:
    """Run the full benchmark suite.

    Args:
        quick: Skip thermal and inference benchmarks for faster results.
        quiet: Suppress progress output to stdout (for --json piping).
    """
    _out = (lambda *a, **kw: print(*a, file=sys.stderr, **kw)) if quiet else print
    benchmarks = [
        ("GPU Inference", benchmark_gpu_inference),
        ("GPU VRAM", benchmark_gpu_vram),
        ("GPU Thermal", benchmark_gpu_thermal),
        ("CPU Single", benchmark_cpu_single),
        ("CPU Multi", benchmark_cpu_multi),
        ("Memory", benchmark_memory_bandwidth),
        ("Storage IOPS", benchmark_storage_iops),
        ("Storage Sequential", benchmark_storage_sequential),
        ("Network", benchmark_network_latency),
    ]

    if quick:
        # Skip thermal (takes 5s) and inference (takes ~30s)
        benchmarks = [b for b in benchmarks
                      if b[0] not in ("GPU Inference", "GPU Thermal")]

    results = []
    total = len(benchmarks)
    for i, (label, func) in enumerate(benchmarks, 1):
        _out(f"  [{i}/{total}] {label}...", end=" ", flush=True)
        try:
            r = func()
            status = f"✓ {r.value} {r.unit}" if r.available else f"✗ {r.error or 'N/A'}"
            _out(status)
            results.append(r)
        except Exception as e:
            _out(f"✗ Error: {e}")
            results.append(BenchmarkResult(
                category=label.lower().replace(" ", "_"),
                name=label, available=False, error=str(e)
            ))

    return results


# ─── Scoring & Profile Card (T-025-006) ────────────────────────────────

def compute_overall_score(results: List[BenchmarkResult]) -> Tuple[float, ScoreTier]:
    """Compute weighted overall score from benchmark results."""
    weights = {
        BenchmarkCategory.GPU_INFERENCE.value: 0.25,
        BenchmarkCategory.GPU_VRAM.value: 0.15,
        BenchmarkCategory.GPU_THERMAL.value: 0.10,
        BenchmarkCategory.CPU_SINGLE.value: 0.10,
        BenchmarkCategory.CPU_MULTI.value: 0.10,
        BenchmarkCategory.MEMORY_BANDWIDTH.value: 0.08,
        BenchmarkCategory.STORAGE_IOPS.value: 0.07,
        BenchmarkCategory.STORAGE_SEQ.value: 0.07,
        BenchmarkCategory.NETWORK_LATENCY.value: 0.08,
    }

    weighted_sum = 0.0
    weight_total = 0.0
    for r in results:
        w = weights.get(r.category, 0.05)
        if r.available:
            weighted_sum += r.score * w
            weight_total += w

    score = round(weighted_sum / weight_total, 1) if weight_total > 0 else 0.0

    if score >= 85:
        tier = ScoreTier.WORKSTATION
    elif score >= 65:
        tier = ScoreTier.PROFESSIONAL
    elif score >= 45:
        tier = ScoreTier.STANDARD
    elif score >= 25:
        tier = ScoreTier.BASIC
    else:
        tier = ScoreTier.MINIMAL

    return score, tier


def _recommend_models(vram_mb: int) -> List[str]:
    """Recommend Ollama models based on available VRAM."""
    models = []
    if vram_mb >= 80000:
        models.extend(["llama3.1:70b", "qwen2.5:72b", "deepseek-r1:70b"])
    if vram_mb >= 40000:
        models.extend(["llama3.1:70b-q4", "qwen2.5:32b", "deepseek-r1:32b"])
    if vram_mb >= 16000:
        models.extend(["llama3.1:8b", "qwen2.5:14b", "deepseek-r1:14b", "gemma2:9b"])
    if vram_mb >= 8000:
        models.extend(["llama3.2:3b", "qwen2.5:7b", "phi3:medium", "gemma2:2b"])
    if vram_mb >= 4000:
        models.extend(["qwen2.5:1.5b", "phi3:mini", "llama3.2:1b"])
    if not models:
        models.append("qwen2.5:0.5b (CPU mode)")
    return models[:6]


def generate_profile_card(results: List[BenchmarkResult]) -> ProfileCard:
    """Generate a performance profile card from benchmark results."""
    import platform

    score, tier = compute_overall_score(results)

    # Extract hardware details
    vram_result = next((r for r in results if r.category == BenchmarkCategory.GPU_VRAM.value), None)
    gpu_name = "N/A"
    gpu_vram = 0
    if vram_result and vram_result.available:
        gpus = vram_result.details.get("gpus", [])
        if gpus:
            gpu_name = gpus[0]["name"]
            gpu_vram = sum(g["total_mb"] for g in gpus)

    card = ProfileCard(
        timestamp=datetime.now().isoformat(),
        hostname=platform.node(),
        overall_score=score,
        tier=tier.value,
        results=[asdict(r) for r in results],
        gpu_name=gpu_name,
        gpu_vram_mb=gpu_vram,
        cpu_cores=os.cpu_count() or 0,
        ram_gb=_get_ram_gb(),
        recommended_thermal=recommend_thermal_policy(results).policy,
        recommended_models=_recommend_models(gpu_vram),
    )
    return card


def _get_ram_gb() -> float:
    """Get total system RAM in GB."""
    try:
        import platform
        if platform.system() == "Windows":
            # Use PowerShell (wmic is deprecated)
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                return round(int(r.stdout.strip()) / (1024**3), 1)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return round(int(line.split()[1]) / (1024**2), 1)
    except Exception:
        pass
    return 0.0


# ─── ASCII Profile Card ────────────────────────────────────────────────

def render_ascii_card(card: ProfileCard) -> str:
    """Render a beautiful ASCII profile card for the terminal."""
    BAR_WIDTH = 20

    def bar(score: float, width: int = BAR_WIDTH) -> str:
        filled = round(score / 100 * width)
        return "█" * filled + "░" * (width - filled)

    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║                 S.L.A.T.E. PERFORMANCE CARD                 ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Host:   {card.hostname:<25} Score: {card.overall_score:>5.1f}/100  ║")
    lines.append(f"║  Tier:   {card.tier:<25} {'⬛' * min(5, int(card.overall_score / 20) + 1):>10}       ║")
    lines.append(f"║  GPU:    {card.gpu_name:<40} {card.gpu_vram_mb:>5} MB  ║")
    lines.append(f"║  CPU:    {card.cpu_cores:>2} cores   RAM: {card.ram_gb:>5.1f} GB                       ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")

    for r in card.results:
        if not r.get("available", True):
            label = f"  {r['name']:<22}"
            lines.append(f"║{label} {'N/A':>36} ║")
            continue
        label = f"  {r['name']:<22}"
        s = r.get("score", 0)
        v = r.get("value", 0)
        u = r.get("unit", "")
        b = bar(s, 16)
        val_str = f"{v:>8.0f} {u:<6}"
        lines.append(f"║{label} {b} {s:>3.0f} {val_str} ║")

    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Thermal Policy: {card.recommended_thermal:<42}║")
    lines.append(f"║  Recommended Models:                                        ║")
    for m in card.recommended_models[:4]:
        lines.append(f"║    • {m:<55}║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def render_html_card(card: ProfileCard) -> str:
    """Render an HTML dashboard widget for the profile card."""
    rows = ""
    for r in card.results:
        if not r.get("available", True):
            rows += f'<tr><td>{r["name"]}</td><td colspan="3" class="na">N/A</td></tr>\n'
            continue
        s = r.get("score", 0)
        v = r.get("value", 0)
        u = r.get("unit", "")
        color = "#4CAF50" if s >= 70 else "#FF9800" if s >= 40 else "#F44336"
        rows += f'''<tr>
  <td>{r["name"]}</td>
  <td><div class="bar" style="width: {s}%; background: {color};"></div></td>
  <td>{s:.0f}</td>
  <td>{v:.0f} {u}</td>
</tr>\n'''

    models_list = "".join(f"<li>{m}</li>" for m in card.recommended_models[:4])

    return f"""<!-- SLATE Performance Profile Card — Auto-generated -->
<!-- Modified: {card.timestamp} | Author: Gemini (Antigravity) -->
<div class="slate-profile-card" style="background: var(--sl-surface-variant, #161616); border: 1px solid rgba(184,115,51,0.3); border-radius: 12px; padding: 24px; font-family: var(--font-mono, monospace); color: #E0E0E0;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <div>
      <div style="font-size: 0.7rem; color: #B85A3C; letter-spacing: 0.15em;">PERFORMANCE CARD</div>
      <div style="font-size: 1.4rem; font-weight: 700;">{card.overall_score:.1f} <span style="font-size: 0.8rem; color: #888;">/100</span></div>
    </div>
    <div style="background: rgba(184,115,51,0.15); padding: 6px 14px; border-radius: 8px; border: 1px solid #B85A3C; font-size: 0.8rem; color: #B85A3C; font-weight: 600;">{card.tier}</div>
  </div>
  <div style="font-size: 0.75rem; color: #888; margin-bottom: 12px;">{card.gpu_name} • {card.gpu_vram_mb} MB VRAM • {card.cpu_cores} cores • {card.ram_gb} GB RAM</div>
  <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">
    <style>.bar {{ height: 8px; border-radius: 4px; min-width: 4px; }} .na {{ color: #555; }}</style>
    {rows}
  </table>
  <div style="margin-top: 16px; font-size: 0.75rem; color: #888;">
    <div style="color: #B85A3C; margin-bottom: 4px;">Thermal: {card.recommended_thermal} • Recommended Models:</div>
    <ul style="margin: 0; padding-left: 16px;">{models_list}</ul>
  </div>
</div>"""


# ─── Thermal Policy (T-025-007) ────────────────────────────────────────

THERMAL_POLICIES = {
    ThermalPolicy.AGGRESSIVE: ThermalConfig(
        policy="aggressive",
        gpu_power_limit_pct=100,
        max_temp_c=95,
        throttle_temp_c=90,
        fan_curve="max",
        description="Maximum performance, no power limits. For short bursts or well-cooled systems."
    ),
    ThermalPolicy.BALANCED: ThermalConfig(
        policy="balanced",
        gpu_power_limit_pct=85,
        max_temp_c=85,
        throttle_temp_c=80,
        fan_curve="auto",
        description="Good performance with thermal protection. Default for most systems."
    ),
    ThermalPolicy.QUIET: ThermalConfig(
        policy="quiet",
        gpu_power_limit_pct=70,
        max_temp_c=78,
        throttle_temp_c=72,
        fan_curve="quiet",
        description="Reduced noise with lower power. For shared workspaces."
    ),
    ThermalPolicy.ENDURANCE: ThermalConfig(
        policy="endurance",
        gpu_power_limit_pct=60,
        max_temp_c=72,
        throttle_temp_c=65,
        fan_curve="silent",
        description="Maximum longevity, minimum noise. For 24/7 unattended operation."
    ),
}


def recommend_thermal_policy(results: List[BenchmarkResult]) -> ThermalConfig:
    """Auto-select thermal policy based on benchmark results."""
    thermal = next((r for r in results if r.category == BenchmarkCategory.GPU_THERMAL.value), None)

    if thermal and thermal.available:
        peak = thermal.details.get("peak_temp_c", 75)
        headroom = thermal.details.get("thermal_headroom_c", 15)

        if headroom >= 25:
            return THERMAL_POLICIES[ThermalPolicy.AGGRESSIVE]
        elif headroom >= 15:
            return THERMAL_POLICIES[ThermalPolicy.BALANCED]
        elif headroom >= 5:
            return THERMAL_POLICIES[ThermalPolicy.QUIET]
        else:
            return THERMAL_POLICIES[ThermalPolicy.ENDURANCE]

    # No thermal data — default to balanced
    return THERMAL_POLICIES[ThermalPolicy.BALANCED]


def save_thermal_config(config: ThermalConfig) -> Path:
    """Write thermal policy to .slate_config/thermal.yaml."""
    THERMAL_CONFIG.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# SLATE Thermal Policy Configuration
# Modified: {datetime.now().isoformat()} | Gemini (Antigravity)
# Auto-selected based on benchmark results
# NOTE: All AIs modifying this file must add a dated comment.
# ────────────────────────────────────────

policy: {config.policy}
description: "{config.description}"

gpu:
  power_limit_pct: {config.gpu_power_limit_pct}
  max_temp_c: {config.max_temp_c}
  throttle_temp_c: {config.throttle_temp_c}
  fan_curve: {config.fan_curve}

# Override per GPU (optional)
# gpu_overrides:
#   "NVIDIA GeForce RTX 4090":
#     power_limit_pct: 90
#     max_temp_c: 88
"""
    THERMAL_CONFIG.write_text(content, encoding="utf-8")
    return THERMAL_CONFIG


# ─── Save / Load ───────────────────────────────────────────────────────

def save_results(card: ProfileCard) -> Path:
    """Save profile card to .slate_analytics/benchmark_results.json."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(
        json.dumps(asdict(card), indent=2, default=str),
        encoding="utf-8"
    )
    return RESULTS_FILE


def load_results() -> Optional[ProfileCard]:
    """Load previous benchmark results."""
    if not RESULTS_FILE.exists():
        return None
    try:
        data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        return ProfileCard(**{k: v for k, v in data.items()
                             if k in ProfileCard.__dataclass_fields__})
    except Exception:
        return None


# ─── CLI ────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for SLATE Benchmark Suite."""
    parser = argparse.ArgumentParser(
        description="SLATE Benchmark Suite (Spec 025)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python -m slate.benchmark_suite --quick --card\n"
               "  python -m slate.benchmark_suite --json\n"
               "  python -m slate.benchmark_suite --thermal\n"
    )
    parser.add_argument("--quick", action="store_true", help="Quick mode (skip inference & thermal)")
    parser.add_argument("--card", action="store_true", help="Show ASCII profile card")
    parser.add_argument("--html", action="store_true", help="Output HTML profile card")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--thermal", action="store_true", help="Show recommended thermal policy")
    parser.add_argument("--save", action="store_true", help="Save results to .slate_analytics/")
    parser.add_argument("--previous", action="store_true", help="Show previous results")
    args = parser.parse_args()

    if args.previous:
        prev = load_results()
        if prev:
            if args.json:
                print(json.dumps(asdict(prev), indent=2, default=str))
            else:
                print(render_ascii_card(prev))
        else:
            print("No previous benchmark results found.")
        return 0

    # When --json is requested, redirect progress to stderr so stdout is clean JSON
    _out = (lambda *a, **kw: print(*a, file=sys.stderr, **kw)) if args.json else print
    _out()
    _out("  ⚙ SLATE Benchmark Suite")
    _out("  " + "─" * 50)

    results = run_full_suite(quick=args.quick, quiet=args.json)
    card = generate_profile_card(results)

    if args.json:
        print(json.dumps(asdict(card), indent=2, default=str))
    elif args.html:
        print(render_html_card(card))
    elif args.card or True:  # Always show card
        print()
        print(render_ascii_card(card))

    if args.thermal:
        policy = recommend_thermal_policy(results)
        print(f"\n  Recommended Thermal Policy: {policy.policy.upper()}")
        print(f"  {policy.description}")
        print(f"  GPU Power: {policy.gpu_power_limit_pct}% | Max: {policy.max_temp_c}°C | Fan: {policy.fan_curve}")

    if args.save:
        path = save_results(card)
        thermal_path = save_thermal_config(recommend_thermal_policy(results))
        print(f"\n  ✓ Results saved to {path}")
        print(f"  ✓ Thermal config saved to {thermal_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
