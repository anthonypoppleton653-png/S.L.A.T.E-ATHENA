---
name: k8s-logs
description: View logs from SLATE Kubernetes pods. Use when debugging, monitoring, or troubleshooting SLATE on K8s.
---

# Kubernetes Logs Skill

View and follow logs from SLATE pods running on Kubernetes.

## Instructions

### View Recent Logs

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --logs --lines 100
```

### Follow Logs in Real-Time

```powershell
.\.venv\Scripts\python.exe slate/slate_k8s.py --logs --follow
```

### Direct kubectl Commands

View specific pod logs:
```powershell
kubectl logs -n slate -l app=slate-dashboard --tail=100
kubectl logs -n slate -l app=ollama --tail=100
kubectl logs -n slate -l app=chromadb --tail=100
```

Follow all SLATE logs:
```powershell
kubectl logs -n slate -l app.kubernetes.io/part-of=slate-system --all-containers -f
```

## Log Aggregation

For structured log analysis, SLATE pods output JSON logs when `LOG_FORMAT=json` is set.

Parse with jq:
```powershell
kubectl logs -n slate -l app=slate-dashboard --tail=100 | jq -r '.timestamp + " " + .level + " " + .message'
```

## Examples

User: "Show SLATE K8s logs"
-> Display last 50 log lines from all SLATE pods

User: "Follow the Kubernetes logs"
-> Stream logs in real-time

User: "Debug the dashboard pod"
-> Show logs specifically from slate-dashboard
