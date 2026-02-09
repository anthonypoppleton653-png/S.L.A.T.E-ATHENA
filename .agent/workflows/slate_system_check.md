---
description: Run SLATE system checks and docker diagnostics
---
# SLATE System Check

Standardized workflow for running SLATE diagnostics via Docker/K8s.

// turbo-all

## 1. K8s Pod Health
```powershell
kubectl get pods -n slate -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount"
```

## 2. K8s Resource Usage
```powershell
kubectl top pods -n slate
```

## 3. Docker Compose Status
```powershell
docker compose ps
```

## 4. SLATE Workflow Status (via K8s)
```powershell
kubectl exec -n slate deployment/slate-core -- python slate/slate_workflow_manager.py --status
```

## 5. SLATE Runtime Check (via K8s)
```powershell
kubectl exec -n slate deployment/slate-core -- python slate/slate_runtime.py --check-all
```

## 6. Docker Compose Config Validation
```powershell
docker compose config --quiet && echo "VALID" || echo "INVALID"
```
```powershell
docker compose -f docker-compose.dev.yml config --quiet && echo "VALID" || echo "INVALID"
```
```powershell
docker compose -f docker-compose.prod.yml config --quiet && echo "VALID" || echo "INVALID"
```
