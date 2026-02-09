# tests/test_dependency_resolver.py

import pytest
from slate.dependency_resolver import (
    HEAVY_PACKAGES,
    SYSTEM_TOOLS,
    _detect_gpu_compute_capability,
    _min_cuda_for_gpu,
)

def test_heavy_packages():
    assert "torch" in HEAVY_PACKAGES
    assert "onnxruntime-gpu" in HEAVY_PACKAGES

def test_system_tools():
    assert "ollama" in SYSTEM_TOOLS
    assert "docker" in SYSTEM_TOOLS
    assert SYSTEM_TOOLS["ollama"]["check_cmd"] == ["ollama", "--version"]
    assert SYSTEM_TOOLS["ollama"]["type"] == "binary"

def test_gpu_compute_capability_detection():
    # Mock subprocess to simulate different GPU compute capabilities
    import subprocess

    def mock_run(args, **kwargs):
        if args[0] == "nvidia-smi" and args[1:] == ["--query-gpu=compute_cap", "--format=csv,noheader"]:
            return subprocess.CompletedProcess(
                args,
                returncode=0,
                stdout="7.5\n6.1\n".strip()
            )
        else:
            raise Exception("Unexpected command")

    subprocess.run = mock_run

    assert _detect_gpu_compute_capability() == 7.5
    assert _min_cuda_for_gpu(7.5) == "10.0"

def test_min_cuda_for_gpu():
    assert _min_cuda_for_gpu(8.9) == "11.8"
    assert _min_cuda_for_gpu(6.1) == "8.0"
    assert _min_cuda_for_gpu(5.0) is None