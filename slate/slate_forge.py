#!/usr/bin/env python3
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Create FORGE.md collaborative log manager
"""
SLATE FORGE.md Manager
======================
Framework for Orchestrated Research, Generation & Evolution.
Manages the shared append-only log for AI team members (Copilot, Antigravity, autonomous agents).

Usage:
    python slate/slate_forge.py --status        # Collaboration summary
    python slate/slate_forge.py --read          # Read full log
    python slate/slate_forge.py --read --section STATUS  # Filter by section
    python slate/slate_forge.py --read --filter "keyword"  # Text search
    python slate/slate_forge.py --append "entry text"  # Append new entry
    python slate/slate_forge.py --sync          # Sync across Docker/MCP
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
FORGE_PATH = WORKSPACE / 'FORGE.md'
SECTIONS = ['STATUS', 'PLAN', 'OUTPUT', 'HANDOFF', 'MAGIC']


def read_forge(section: str = None, filter_text: str = None) -> str:
    """Read FORGE.md contents, optionally filtered."""
    if not FORGE_PATH.exists():
        return '⚠️ FORGE.md not found. Create it with --append to initialize.'

    content = FORGE_PATH.read_text(encoding='utf-8')

    if section:
        # Filter to entries matching the section
        section_upper = section.upper()
        lines = content.split('\n')
        filtered = []
        in_section = False
        for line in lines:
            if f'| {section_upper}:' in line or f'| {section_upper} :' in line.upper():
                in_section = True
            elif line.startswith('### [') and in_section:
                in_section = False
            if in_section or (section_upper in line.upper() and line.startswith('### [')):
                filtered.append(line)
        if filtered:
            return '\n'.join(filtered)
        return f'No entries found for section: {section}'

    if filter_text:
        lines = content.split('\n')
        filtered = [l for l in lines if filter_text.lower() in l.lower()]
        if filtered:
            return '\n'.join(filtered)
        return f'No entries matching: {filter_text}'

    return content


def append_forge(entry: str) -> str:
    """Append a new entry to FORGE.md."""
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Auto-format entry if it doesn't have the standard format
    if not entry.startswith('['):
        entry = f'### [COPILOT] {timestamp} | {entry}'
    elif not entry.startswith('### '):
        entry = f'### {entry}'

    if not FORGE_PATH.exists():
        # Initialize FORGE.md
        header = """# S.L.A.T.E. FORGE — Collaborative AI Operations Log
# Modified: {ts} | Author: COPILOT | Change: Initialize FORGE.md

> **FORGE** = Framework for Orchestrated Research, Generation & Evolution
> Shared append-only log for AI team members (Copilot, Antigravity, autonomous agents).

---

## Protocol

1. **Format**: `[AgentName] YYYY-MM-DDTHH:MM:SSZ | Action: description`
2. **Sections**: `STATUS`, `PLAN`, `OUTPUT`, `HANDOFF`, `MAGIC`
3. **Sync**: Shared via Docker volume mount at `/app/FORGE.md` or local workspace

---

## Log

""".format(ts=timestamp)
        FORGE_PATH.write_text(header + entry + '\n\n', encoding='utf-8')
        return f'✅ FORGE.md initialized with first entry at {timestamp}'

    # Append to existing file
    with open(FORGE_PATH, 'a', encoding='utf-8') as f:
        f.write('\n' + entry + '\n')

    return f'✅ Entry appended to FORGE.md at {timestamp}'


def forge_status() -> str:
    """Get collaboration summary."""
    if not FORGE_PATH.exists():
        return '⚠️ FORGE.md not found. No collaboration history.'

    content = FORGE_PATH.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Count entries by agent
    agents = {}
    sections = {}
    entry_count = 0
    for line in lines:
        match = re.match(r'###\s*\[(\w+)\]', line)
        if match:
            agent = match.group(1)
            agents[agent] = agents.get(agent, 0) + 1
            entry_count += 1

        for sec in SECTIONS:
            if f'| {sec}:' in line.upper() or f'| {sec} :' in line.upper():
                sections[sec] = sections.get(sec, 0) + 1

    # Get last 5 entries
    entries = [l for l in lines if l.startswith('### [')]
    recent = entries[-5:] if len(entries) >= 5 else entries

    result = ['## FORGE.md Collaboration Status\n']
    result.append(f'**Total entries:** {entry_count}')
    result.append(f'**File size:** {len(content)} bytes')
    result.append(f'**Last modified:** {datetime.fromtimestamp(FORGE_PATH.stat().st_mtime).isoformat()}Z\n')

    if agents:
        result.append('### Agent Activity')
        result.append('| Agent | Entries |')
        result.append('|-------|---------|')
        for agent, count in sorted(agents.items()):
            result.append(f'| {agent} | {count} |')
        result.append('')

    if sections:
        result.append('### Section Distribution')
        result.append('| Section | Count |')
        result.append('|---------|-------|')
        for sec, count in sorted(sections.items()):
            result.append(f'| {sec} | {count} |')
        result.append('')

    if recent:
        result.append('### Recent Entries')
        for entry in recent:
            result.append(f'- {entry[4:]}')  # Strip '### '

    return '\n'.join(result)


def forge_sync() -> str:
    """Sync FORGE.md across Docker volumes and MCP."""
    if not FORGE_PATH.exists():
        return '⚠️ FORGE.md not found. Nothing to sync.'

    results = []

    # Check if Docker is available and sync
    try:
        import subprocess
        # Check if slate container is running
        check = subprocess.run(
            ['docker', 'inspect', '--format', '{{.State.Running}}', 'slate'],
            capture_output=True, text=True, timeout=10
        )
        if check.returncode == 0 and 'true' in check.stdout.lower():
            # Copy FORGE.md to Docker container
            cp = subprocess.run(
                ['docker', 'cp', str(FORGE_PATH), 'slate:/app/FORGE.md'],
                capture_output=True, text=True, timeout=30
            )
            if cp.returncode == 0:
                results.append('✅ Synced to Docker container (slate:/app/FORGE.md)')
            else:
                results.append(f'⚠️ Docker sync failed: {cp.stderr.strip()}')
        else:
            results.append('ℹ️ Docker container not running — skipping Docker sync')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results.append('ℹ️ Docker not available — skipping Docker sync')

    # Check K8s sync
    try:
        import subprocess
        check = subprocess.run(
            ['kubectl', 'get', 'ns', 'slate', '--no-headers'],
            capture_output=True, text=True, timeout=10
        )
        if check.returncode == 0:
            results.append('ℹ️ K8s namespace exists — FORGE.md syncs via ConfigMap volume mount')
        else:
            results.append('ℹ️ K8s namespace not found — skipping K8s sync')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results.append('ℹ️ kubectl not available — skipping K8s sync')

    if not results:
        results.append('ℹ️ No sync targets available (Docker/K8s offline)')

    return '\n'.join(results)


def main():
    parser = argparse.ArgumentParser(description='SLATE FORGE.md Manager')
    parser.add_argument('--status', action='store_true', help='Collaboration summary')
    parser.add_argument('--read', action='store_true', help='Read FORGE.md')
    parser.add_argument('--section', type=str, help='Filter by section (with --read)')
    parser.add_argument('--filter', type=str, help='Text search filter (with --read)')
    parser.add_argument('--append', type=str, help='Append entry to FORGE.md')
    parser.add_argument('--sync', action='store_true', help='Sync across Docker/MCP')

    args = parser.parse_args()

    if args.status:
        print(forge_status())
    elif args.read:
        print(read_forge(section=args.section, filter_text=args.filter))
    elif args.append:
        print(append_forge(args.append))
    elif args.sync:
        print(forge_sync())
    else:
        # Default: show status
        print(forge_status())


if __name__ == '__main__':
    main()
