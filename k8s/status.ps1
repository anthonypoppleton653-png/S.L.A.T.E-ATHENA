# SLATE Kubernetes Status Check
# Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5
# Usage: .\k8s\status.ps1

$SLATE_NS = "slate"

Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                       S.L.A.T.E. Kubernetes Status                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Cluster info
Write-Host "Cluster: $(kubectl config current-context)" -ForegroundColor Yellow
Write-Host ""

# Namespace check
$ns = kubectl get namespace $SLATE_NS 2>$null
if (-not $ns) {
    Write-Host "SLATE namespace not found. Run: .\k8s\deploy.ps1" -ForegroundColor Red
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Pod Health
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Pod Health ===" -ForegroundColor Cyan
kubectl get pods -n $SLATE_NS -o wide
Write-Host ""

# Count by status
$pods = kubectl get pods -n $SLATE_NS -o jsonpath='{.items[*].status.phase}' 2>$null
$running = ($pods -split ' ' | Where-Object { $_ -eq 'Running' }).Count
$pending = ($pods -split ' ' | Where-Object { $_ -eq 'Pending' }).Count
$failed = ($pods -split ' ' | Where-Object { $_ -eq 'Failed' }).Count

Write-Host "Summary: $running Running, $pending Pending, $failed Failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } elseif ($pending -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Services
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Services ===" -ForegroundColor Cyan
kubectl get svc -n $SLATE_NS
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Ingress
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Ingress ===" -ForegroundColor Cyan
kubectl get ingress -n $SLATE_NS
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# HPAs
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Autoscaling ===" -ForegroundColor Cyan
kubectl get hpa -n $SLATE_NS
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# PVCs
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Storage ===" -ForegroundColor Cyan
kubectl get pvc -n $SLATE_NS
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# GPU Resources
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== GPU Resources ===" -ForegroundColor Cyan
$gpuPods = kubectl get pods -n $SLATE_NS -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.limits.nvidia\.com/gpu}{"\n"}{end}' 2>$null
if ($gpuPods) {
    $gpuPods | Where-Object { $_ -match '\d' }
} else {
    Write-Host "No GPU pods found"
}
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard Health Check
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Dashboard Health ===" -ForegroundColor Cyan
try {
    # Quick port-forward check
    $dashboardPod = kubectl get pods -n $SLATE_NS -l app.kubernetes.io/component=dashboard -o jsonpath='{.items[0].metadata.name}' 2>$null
    if ($dashboardPod) {
        Write-Host "Dashboard Pod: $dashboardPod" -ForegroundColor Green

        # Check readiness
        $ready = kubectl get pod $dashboardPod -n $SLATE_NS -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
        if ($ready -eq "True") {
            Write-Host "Status: Ready" -ForegroundColor Green
        } else {
            Write-Host "Status: Not Ready" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No dashboard pods found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not check dashboard: $_" -ForegroundColor Yellow
}
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Recent Events
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "=== Recent Events (last 5) ===" -ForegroundColor Cyan
kubectl get events -n $SLATE_NS --sort-by='.lastTimestamp' | Select-Object -Last 5
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Quick Commands
# ─────────────────────────────────────────────────────────────────────────────
Write-Host @"
=== Quick Commands ===
Dashboard:     kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
Logs:          kubectl logs -n slate -l app.kubernetes.io/component=dashboard -f
Ollama logs:   kubectl logs -n slate -l app.kubernetes.io/name=ollama -f
Shell:         kubectl exec -it -n slate deploy/slate-dashboard -- /bin/bash
Restart:       kubectl rollout restart -n slate deploy/slate-dashboard

"@ -ForegroundColor Gray
