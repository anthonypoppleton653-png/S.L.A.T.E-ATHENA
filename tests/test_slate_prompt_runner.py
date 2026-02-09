# test_slate_prompt_runner.py

import json
import pytest
from pathlib import Path
from slate.slate_prompt_runner import load_index, list_prompts, get_prompt, run_prompt, INDEX_PATH

@pytest.fixture
def mock_index():
    return {
        'version': '1.0.0',
        'prompts': [
            {'name': 'test_prompt', 'model': 'default', 'tags': ['tag1', 'tag2'], 'description': 'Test prompt description'},
            {'name': 'another_prompt', 'model': 'slate-fast'}
        ]
    }

def test_load_index(mock_index, monkeypatch, tmp_path):
    # Modified: 2026-02-10T14:00:00Z | Author: COPILOT | Change: Use tmp_path file instead of monkeypatching read-only WindowsPath attributes
    idx_file = tmp_path / "index.json"
    idx_file.write_text(json.dumps(mock_index), encoding="utf-8")
    monkeypatch.setattr("slate.slate_prompt_runner.INDEX_PATH", idx_file)

    assert load_index() == mock_index

def test_list_prompts(mock_index, monkeypatch):
    def mock_load_index():
        return mock_index

    monkeypatch.setattr('slate.slate_prompt_runner.load_index', mock_load_index)

    result = list_prompts()
    assert '## SLATE Prompt Index' in result
    assert 'test_prompt' in result
    assert 'another_prompt' in result

def test_get_prompt(mock_index, monkeypatch):
    def mock_load_index():
        return mock_index

    monkeypatch.setattr('slate.slate_prompt_runner.load_index', mock_load_index)

    result = get_prompt('test_prompt')
    assert '## Prompt: test_prompt' in result
    assert '**Model:** default' in result
    assert '**Tags:** tag1, tag2' in result
    assert '**Description:** Test prompt description' in result

def test_run_prompt(mock_index, monkeypatch):
    def mock_load_index():
        return mock_index

    monkeypatch.setattr('slate.slate_prompt_runner.load_index', mock_load_index)

    result = run_prompt('test_prompt')
    assert '⚠️ Prompt file not found: test_prompt.md' in result