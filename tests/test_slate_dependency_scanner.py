# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix API names — scan_all() not scan(), create_link() not link()
# test_slate_dependency_scanner.py

import pytest
from pathlib import Path
from slate.slate_dependency_scanner import DependencyScanner

@pytest.fixture
def scanner(tmp_path):
    return DependencyScanner(workspace=tmp_path)

def test_scan_all_returns_report(scanner):
    """scan_all() returns a ScanReport with results for each dependency type."""
    report = scanner.scan_all()
    assert hasattr(report, "results")
    assert "python" in report.results
    assert "cuda" in report.results
    assert "ollama" in report.results

def test_scanner_workspace(scanner, tmp_path):
    """Scanner uses the provided workspace path."""
    assert scanner.workspace == tmp_path

def test_create_link(scanner, tmp_path):
    """create_link() creates symlink from source to target."""
    source = tmp_path / "source_dir"
    source.mkdir()
    target = tmp_path / "linked_dir"

    result = scanner.create_link(source, target)
    assert result is True
    assert target.exists()