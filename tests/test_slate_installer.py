# test_slate_installer.py

import pytest
from slate.slate_installer import detect_python, detect_git, detect_ollama, detect_docker, detect_vscode_extension, _run, _is_windows, _print_step, _print_header

def test_detect_python():
    python_info = detect_python()
    assert "installed" in python_info
    assert "version" in python_info
    assert "executable" in python_info
    assert "meets_requirement" in python_info
    assert "platform" in python_info

def test_detect_git():
    git_info = detect_git()
    assert "installed" in git_info
    assert "version" in git_info
    assert "path" in git_info

def test_detect_ollama():
    ollama_info = detect_ollama()
    assert "installed" in ollama_info
    assert "version" in ollama_info
    assert "path" in ollama_info

def test_detect_docker():
    docker_info = detect_docker()
    assert "installed" in docker_info
    assert "version" in docker_info
    assert "path" in docker_info

def test_detect_vscode_extension():
    extension_info = detect_vscode_extension()
    assert "installed" in extension_info
    assert "version" in extension_info
    assert "id" in extension_info

def test__run():
    # Test with a simple command like 'echo'
    result = _run(["echo", "Hello, World!"])
    assert result.returncode == 0
    assert "Hello, World!" in result.stdout

def test__is_windows():
    assert _is_windows() == (os.name == "nt")

def test__print_step(capsys):
    _print_step("✓", "This is a test step")
    captured = capsys.readouterr()
    assert "  ✓ This is a test step" in captured.out

def test__print_header(capsys):
    _print_header("Test Header")
    captured = capsys.readouterr()
    assert "  ─" * 60 in captured.out
    assert "  Test Header" in captured.out
    assert "  ─" * 60 in captured.out