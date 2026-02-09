#!/usr/bin/env python3
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Create prompt runner for SLATE super prompts
"""
SLATE Prompt Runner
===================
Manages and executes SLATE super prompts via Ollama.

Usage:
    python slate/slate_prompt_runner.py --list                # List all prompts
    python slate/slate_prompt_runner.py --get "name"          # Get prompt details
    python slate/slate_prompt_runner.py --run "name"          # Run prompt via Ollama
    python slate/slate_prompt_runner.py --run "name" --model "model"  # Run with specific model
    python slate/slate_prompt_runner.py --validate            # Validate all prompts
    python slate/slate_prompt_runner.py --index               # Regenerate prompt index
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
PROMPTS_DIR = WORKSPACE / 'prompts'
INDEX_PATH = PROMPTS_DIR / 'index.json'
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')


def load_index() -> dict:
    """Load the prompt index."""
    if not INDEX_PATH.exists():
        return {'version': '1.0.0', 'prompts': []}
    return json.loads(INDEX_PATH.read_text(encoding='utf-8'))


def list_prompts() -> str:
    """List all available prompts."""
    index = load_index()
    prompts = index.get('prompts', [])

    if not prompts:
        return '⚠️ No prompts found. Run --index to regenerate.'

    result = ['## SLATE Prompt Index\n']
    result.append(f'**Total prompts:** {len(prompts)}')
    result.append(f'**Version:** {index.get("version", "unknown")}\n')
    result.append('| # | Name | Model | Tags | Description |')
    result.append('|---|------|-------|------|-------------|')

    for i, p in enumerate(prompts, 1):
        name = p.get('name', 'unknown')
        model = p.get('model', 'default')
        tags = ', '.join(p.get('tags', [])[:3])
        desc = p.get('description', '')[:60]
        result.append(f'| {i} | {name} | {model} | {tags} | {desc} |')

    return '\n'.join(result)


def get_prompt(name: str) -> str:
    """Get full details of a specific prompt."""
    index = load_index()
    prompts = index.get('prompts', [])

    # Find by name (case-insensitive)
    for p in prompts:
        if p.get('name', '').lower() == name.lower():
            result = [f'## Prompt: {p["name"]}\n']
            result.append(f'**Model:** {p.get("model", "default")}')
            result.append(f'**Tags:** {", ".join(p.get("tags", []))}')
            result.append(f'**Description:** {p.get("description", "N/A")}\n')

            # Read the actual prompt file
            file_path = PROMPTS_DIR / p.get('file', f'{name}.md')
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                result.append(f'### Prompt Content ({len(content)} chars)\n')
                if len(content) > 2000:
                    result.append(content[:2000] + '\n\n...[truncated]...')
                else:
                    result.append(content)
            else:
                result.append(f'⚠️ Prompt file not found: {file_path.name}')

            return '\n'.join(result)

    return f'⚠️ Prompt not found: {name}\nAvailable: {", ".join(p.get("name", "?") for p in prompts)}'


def run_prompt(name: str, model_override: str = None) -> str:
    """Execute a prompt via Ollama."""
    index = load_index()
    prompts = index.get('prompts', [])

    # Find prompt
    prompt_entry = None
    for p in prompts:
        if p.get('name', '').lower() == name.lower():
            prompt_entry = p
            break

    if not prompt_entry:
        return f'⚠️ Prompt not found: {name}'

    model = model_override or prompt_entry.get('model', 'slate-fast')

    # Read prompt file
    file_path = PROMPTS_DIR / prompt_entry.get('file', f'{name}.md')
    if not file_path.exists():
        return f'⚠️ Prompt file not found: {file_path.name}'

    prompt_text = file_path.read_text(encoding='utf-8')

    # Execute via Ollama
    try:
        import urllib.request
        url = f'{OLLAMA_HOST}/api/generate'
        payload = json.dumps({
            'model': model,
            'prompt': prompt_text,
            'stream': False,
            'options': {
                'num_predict': 2048,
                'temperature': 0.7
            }
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            response_text = result.get('response', '')
            eval_count = result.get('eval_count', 0)
            eval_duration = result.get('eval_duration', 0)
            tokens_per_sec = (eval_count / (eval_duration / 1e9)) if eval_duration > 0 else 0

            output = [f'## Prompt Execution: {name}\n']
            output.append(f'**Model:** {model}')
            output.append(f'**Tokens:** {eval_count}')
            output.append(f'**Speed:** {tokens_per_sec:.1f} tok/s\n')
            output.append('### Response\n')
            output.append(response_text)
            return '\n'.join(output)

    except urllib.error.URLError as e:
        return f'⚠️ Ollama connection failed: {e}\nIs Ollama running at {OLLAMA_HOST}?'
    except Exception as e:
        return f'⚠️ Prompt execution failed: {e}'


def validate_prompts() -> str:
    """Validate all prompts — check files exist, models available."""
    index = load_index()
    prompts = index.get('prompts', [])

    if not prompts:
        return '⚠️ No prompts in index. Run --index to regenerate.'

    result = ['## Prompt Validation Report\n']
    valid = 0
    issues = []

    # Check Ollama models
    available_models = set()
    try:
        import urllib.request
        url = f'{OLLAMA_HOST}/api/tags'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for m in data.get('models', []):
                name_parts = m.get('name', '').split(':')
                available_models.add(name_parts[0])
    except Exception:
        result.append('⚠️ Cannot connect to Ollama — model validation skipped\n')

    for p in prompts:
        name = p.get('name', 'unknown')
        file_name = p.get('file', f'{name}.md')
        file_path = PROMPTS_DIR / file_name
        model = p.get('model', 'default')

        entry_issues = []

        # Check file exists
        if not file_path.exists():
            entry_issues.append(f'File missing: {file_name}')

        # Check model available
        if available_models and model not in available_models:
            entry_issues.append(f'Model not found: {model}')

        # Check required fields
        if not p.get('description'):
            entry_issues.append('Missing description')
        if not p.get('tags'):
            entry_issues.append('Missing tags')

        if entry_issues:
            issues.append(f'**{name}**: {"; ".join(entry_issues)}')
        else:
            valid += 1

    result.append(f'**Valid:** {valid}/{len(prompts)}')
    if issues:
        result.append(f'**Issues:** {len(issues)}\n')
        for issue in issues:
            result.append(f'- {issue}')
    else:
        result.append('\n✅ All prompts valid!')

    return '\n'.join(result)


def regenerate_index() -> str:
    """Regenerate the prompt index from prompt files."""
    if not PROMPTS_DIR.exists():
        return '⚠️ Prompts directory not found.'

    # Find all markdown files in prompts/
    prompt_files = sorted(PROMPTS_DIR.glob('*.md'))
    if not prompt_files:
        return '⚠️ No prompt files found in prompts/'

    prompts = []
    for pf in prompt_files:
        content = pf.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Extract metadata from first few lines
        name = pf.stem
        description = ''
        model = 'slate-fast'
        tags = []

        for line in lines[:20]:
            if line.startswith('# '):
                name = line[2:].strip()
            elif 'model:' in line.lower():
                model = line.split(':', 1)[1].strip().strip('`')
            elif 'description:' in line.lower():
                description = line.split(':', 1)[1].strip()
            elif 'tags:' in line.lower():
                tag_str = line.split(':', 1)[1].strip()
                tags = [t.strip() for t in tag_str.split(',')]

        if not description:
            # Use first non-header, non-empty line as description
            for line in lines:
                if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('-'):
                    description = line.strip()[:100]
                    break

        prompts.append({
            'name': name,
            'file': pf.name,
            'model': model,
            'description': description,
            'tags': tags or ['general'],
            'chars': len(content)
        })

    index = {
        'version': '1.0.0',
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'count': len(prompts),
        'prompts': prompts
    }

    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding='utf-8')
    return f'✅ Regenerated prompt index: {len(prompts)} prompts in {INDEX_PATH.name}'


def main():
    parser = argparse.ArgumentParser(description='SLATE Prompt Runner')
    parser.add_argument('--list', action='store_true', help='List all prompts')
    parser.add_argument('--get', type=str, help='Get prompt details by name')
    parser.add_argument('--run', type=str, help='Run prompt via Ollama')
    parser.add_argument('--model', type=str, help='Override model (with --run)')
    parser.add_argument('--validate', action='store_true', help='Validate all prompts')
    parser.add_argument('--index', action='store_true', help='Regenerate index')

    args = parser.parse_args()

    if args.list:
        print(list_prompts())
    elif args.get:
        print(get_prompt(args.get))
    elif args.run:
        print(run_prompt(args.run, model_override=args.model))
    elif args.validate:
        print(validate_prompts())
    elif args.index:
        print(regenerate_index())
    else:
        print(list_prompts())


if __name__ == '__main__':
    main()
