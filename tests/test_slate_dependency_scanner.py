# test_slate_dependency_scanner.py

import pytest
from pathlib import Path
from slate.slate_dependency_scanner import DependencyScanner, DependencyResult, DependencyLocation

@pytest.fixture
def scanner():
    return DependencyScanner()

def test_scan_no_deps(scanner):
    results = scanner.scan()
    assert all(not r.found for r in results.values())

def test_scan_with_fake_dep(scanner, tmp_path):
    fake_dep_path = tmp_path / "fake_dep"
    fake_dep_path.mkdir()
    results = scanner.scan([str(fake_dep_path)])
    assert results["fake_dep"].found
    assert len(results["fake_dep"].locations) == 1

def test_link(scanner, tmp_path):
    fake_dep_path = tmp_path / "fake_dep"
    fake_dep_path.mkdir()
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()

    results = scanner.scan([str(fake_dep_path)])
    assert results["fake_dep"].found
    assert len(results["fake_dep"].locations) == 1

    scanner.link(results, str(workspace_path))
    assert (workspace_path / "fake_dep").is_symlink()