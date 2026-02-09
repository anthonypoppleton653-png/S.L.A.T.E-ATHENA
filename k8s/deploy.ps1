# SLATE Kubernetes Deployment Script
# Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5
# Usage: .\k8s\deploy.ps1 [-Environment local|dev|staging|prod] [-SkipPrereqs]

param(
    [ValidateSet("local", "dev", "staging", "prod")]
    [string]$Environment = "local",
    [switch]$SkipPrereqs,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SLATE_NS = "slate"

Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                    S.L.A.T.E. Kubernetes Deployment                          ║
║         Synchronized Living Architecture for Transformation and Evolution    ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Namespace:   $SLATE_NS" -ForegroundColor Yellow
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Prerequisites Check
# ─────────────────────────────────────────────────────────────────────────────
function Test-Prerequisites {
    Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Cyan

    # kubectl
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl not found. Please install kubectl first."
        exit 1
    }
    Write-Host "  ✓ kubectl found" -ForegroundColor Green

    # Cluster connectivity
    $cluster = kubectl config current-context 2>$null
    if (-not $cluster) {
        Write-Error "No Kubernetes cluster configured. Run 'kubectl config use-context <context>'"
        exit 1
    }
    Write-Host "  ✓ Connected to cluster: $cluster" -ForegroundColor Green

    # Check for GPU nodes (optional warning)
    $gpuNodes = kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}' 2>$null
    if ($gpuNodes -match '\d') {
        Write-Host "  ✓ GPU nodes detected" -ForegroundColor Green
    } else {
        Write-Host "  ! No GPU nodes detected (Ollama will run in CPU mode)" -ForegroundColor Yellow
    }

    # Metrics server (for HPA)
    $metrics = kubectl get deployment metrics-server -n kube-system 2>$null
    if (-not $metrics) {
        Write-Host "  ! Metrics server not found (HPA won't work)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ Metrics server available" -ForegroundColor Green
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Namespace Creation
# ─────────────────────────────────────────────────────────────────────────────
function New-SlateNamespace {
    Write-Host "[2/6] Creating namespace..." -ForegroundColor Cyan

    $existing = kubectl get namespace $SLATE_NS 2>$null
    if ($existing) {
        Write-Host "  ✓ Namespace '$SLATE_NS' already exists" -ForegroundColor Green
    } else {
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would create namespace '$SLATE_NS'" -ForegroundColor Magenta
        } else {
            kubectl create namespace $SLATE_NS
            Write-Host "  ✓ Created namespace '$SLATE_NS'" -ForegroundColor Green
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Secret Setup
# ─────────────────────────────────────────────────────────────────────────────
function Set-Secrets {
    Write-Host "[3/6] Configuring secrets..." -ForegroundColor Cyan

    # Check for GitHub token
    $ghToken = $env:GITHUB_TOKEN
    if (-not $ghToken) {
        $ghToken = $env:GH_TOKEN
    }

    if ($ghToken) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would create GitHub secret" -ForegroundColor Magenta
        } else {
            kubectl create secret generic slate-github-secret `
                --namespace $SLATE_NS `
                --from-literal=token=$ghToken `
                --dry-run=client -o yaml | kubectl apply -f -
            Write-Host "  ✓ GitHub secret configured" -ForegroundColor Green
        }
    } else {
        Write-Host "  ! No GITHUB_TOKEN found - some features will be limited" -ForegroundColor Yellow
        Write-Host "    Set GITHUB_TOKEN environment variable for full functionality" -ForegroundColor Gray
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Deploy SLATE
# ─────────────────────────────────────────────────────────────────────────────
function Deploy-Slate {
    Write-Host "[4/6] Deploying SLATE resources..." -ForegroundColor Cyan

    $kustomizePath = "k8s"
    if ($Environment -ne "local") {
        $kustomizePath = "k8s/overlays/$Environment"
    }

    if (-not (Test-Path $kustomizePath)) {
        Write-Error "Kustomize path not found: $kustomizePath"
        exit 1
    }

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would apply: kubectl apply -k $kustomizePath" -ForegroundColor Magenta
        kubectl apply -k $kustomizePath --dry-run=client
    } else {
        kubectl apply -k $kustomizePath
        Write-Host "  ✓ SLATE resources deployed" -ForegroundColor Green
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Wait for Pods
# ─────────────────────────────────────────────────────────────────────────────
function Wait-ForPods {
    Write-Host "[5/6] Waiting for pods to be ready..." -ForegroundColor Cyan

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would wait for pods" -ForegroundColor Magenta
        return
    }

    # Wait for key deployments
    $deployments = @("slate-dashboard", "ollama")

    foreach ($dep in $deployments) {
        Write-Host "  Waiting for $dep..." -NoNewline
        $timeout = 300  # 5 minutes
        $ready = kubectl rollout status deployment/$dep -n $SLATE_NS --timeout="${timeout}s" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
        } else {
            Write-Host " (timeout)" -ForegroundColor Yellow
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Display Status
# ─────────────────────────────────────────────────────────────────────────────
function Show-Status {
    Write-Host "[6/6] Deployment complete!" -ForegroundColor Cyan
    Write-Host ""

    if ($DryRun) {
        Write-Host "[DRY RUN] No changes made" -ForegroundColor Magenta
        return
    }

    # Pod status
    Write-Host "Pod Status:" -ForegroundColor Yellow
    kubectl get pods -n $SLATE_NS -o wide
    Write-Host ""

    # Services
    Write-Host "Services:" -ForegroundColor Yellow
    kubectl get svc -n $SLATE_NS
    Write-Host ""

    # Access instructions
    Write-Host @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                           Access Instructions                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Dashboard (port-forward):
  kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
  Open: http://localhost:8080

Dashboard (ingress - requires DNS/hosts entry):
  Add to /etc/hosts: <cluster-ip> slate.local
  Open: http://slate.local

Check K8s Integration:
  curl http://localhost:8080/api/k8s/status

View Logs:
  kubectl logs -n slate -l app.kubernetes.io/component=dashboard -f

"@ -ForegroundColor Cyan
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
try {
    if (-not $SkipPrereqs) {
        Test-Prerequisites
    }
    New-SlateNamespace
    Set-Secrets
    Deploy-Slate
    Wait-ForPods
    Show-Status

    Write-Host "SLATE is now running in your local Kubernetes cloud!" -ForegroundColor Green
}
catch {
    Write-Host "Deployment failed: $_" -ForegroundColor Red
    exit 1
}
