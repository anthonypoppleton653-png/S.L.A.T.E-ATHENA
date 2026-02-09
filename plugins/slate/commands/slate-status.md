---
description: Check SLATE system status — GPU, services, runtime
---

# /slate-status

Quick system health check for SLATE.

## Instructions

Run the status check:

```bash
.venv/Scripts/python.exe slate/slate_status.py --quick
```

For JSON output:
```bash
.venv/Scripts/python.exe slate/slate_status.py --json
```

Report: GPU count, services health, K8s/Docker runtime status.
