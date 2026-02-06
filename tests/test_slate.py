#!/usr/bin/env python3
"""Tests for slate package."""

import pytest
import sys

def test_import_slate():
    import slate
    assert slate.__version__ == "2.4.0"

def test_version_format():
    import slate
    parts = slate.__version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)

def test_slate_status_import():
    from slate import slate_status
    assert hasattr(slate_status, 'get_status')

def test_slate_benchmark_import():
    from slate import slate_benchmark
    assert hasattr(slate_benchmark, 'run_benchmarks')

def test_slate_hardware_optimizer_import():
    from slate import slate_hardware_optimizer
    assert hasattr(slate_hardware_optimizer, 'detect_gpus')

def test_slate_runtime_import():
    from slate import slate_runtime
    assert hasattr(slate_runtime, 'check_all')

def test_slate_terminal_monitor_import():
    from slate import slate_terminal_monitor
    assert hasattr(slate_terminal_monitor, 'is_blocked')

def test_blocked_commands():
    from slate.slate_terminal_monitor import is_blocked
    assert is_blocked("curl.exe https://example.com")[0] == True
    assert is_blocked("Start-Sleep -Seconds 10")[0] == True
    assert is_blocked("python --version")[0] == False
