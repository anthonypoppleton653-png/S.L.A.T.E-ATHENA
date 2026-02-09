# Modified: 2026-02-09T07:52:00Z | Author: COPILOT | Change: Create prompt index generator
"""Generate prompts/index.json manifest for programmatic prompt discovery."""
import os
import json
import re
import datetime

prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prompts')
manifest = {
    'version': '1.0.0',
    'generated': datetime.datetime.utcnow().isoformat() + 'Z',
    'count': 0,
    'prompts': []
}

for fname in sorted(os.listdir(prompts_dir)):
    if not fname.endswith('.prompt.md'):
        continue

    fpath = os.path.join(prompts_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse YAML frontmatter
    fm_match = re.search(r'---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        continue

    fm = fm_match.group(1)
    entry = {'file': fname}

    for line in fm.split('\n'):
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key == 'tags':
                val = [t.strip().strip("'\"") for t in val.strip('[]').split(',')]
            entry[key] = val

    manifest['prompts'].append(entry)

manifest['count'] = len(manifest['prompts'])

out_path = os.path.join(prompts_dir, 'index.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(json.dumps(manifest, indent=2))
print(f'\nWrote {out_path}')
