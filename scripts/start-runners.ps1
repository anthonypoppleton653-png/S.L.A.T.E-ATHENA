# S.L.A.T.E. Docker Runner Launcher
# Modified: 2026-02-09T08:22:00-05:00 | Author: Gemini | Change: Rewrite for myoung34/github-runner image
# NOTE: All AIs modifying this file must add a dated comment like the one above.
#
# Usage:
#   Start:   .\scripts\start-runners.ps1
#   Stop:    .\scripts\start-runners.ps1 -Stop
#   Status:  .\scripts\start-runners.ps1 -Status
#
# Prerequisites:
#   - gh CLI authenticated (gh auth login)
#   - Docker Desktop with NVIDIA Container Toolkit
#   - Ollama running on host at port 11434

param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$GpuOnly,
    [switch]$CpuOnly
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ComposeFile = Join-Path $ProjectRoot "docker-compose.runners.yml"

Write-Host ""
Write-Host "============================================================"
Write-Host "  SLATE Docker Runner Manager"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================================"
Write-Host ""

# ─── Status ──────────────────────────────────────────────────────────────
if ($Status) {
    Write-Host "=== Docker Runners ==="
    docker compose -f $ComposeFile ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>&1
    Write-Host ""
    Write-Host "=== GPU Allocation ==="
    nvidia-smi --query-gpu=index, name, utilization.gpu, memory.used, memory.total --format=csv, noheader 2>&1
    Write-Host ""
    Write-Host "=== Ollama Models in VRAM ==="
    try {
        $ps = Invoke-RestMethod "http://127.0.0.1:11434/api/ps" -TimeoutSec 5
        $ps.models | ForEach-Object {
            Write-Host "  $($_.name) | $([math]::Round($_.size_vram/1GB,1))GB VRAM | ctx=$($_.context_length)"
        }
    }
    catch { Write-Host "  Ollama not responding" }
    Write-Host ""
    Write-Host "=== Native Runners ==="
    Get-Process -Name "Runner*" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  $($_.Name) PID=$($_.Id) since $($_.StartTime)"
    }
    exit 0
}

# ─── Stop ────────────────────────────────────────────────────────────────
if ($Stop) {
    Write-Host "Stopping Docker runners..."
    docker compose -f $ComposeFile down --remove-orphans 2>&1
    Write-Host "Done."
    exit 0
}

# ─── Pre-flight Checks ──────────────────────────────────────────────────

# Check Docker
$dockerOk = docker info --format "{{.ContainersRunning}}" 2>$null
if (-not $dockerOk) {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop first."
    exit 1
}
Write-Host "Docker: OK ($dockerOk containers running)"

# Check GPU
$gpuCount = (nvidia-smi --query-gpu=name --format=csv, noheader 2>$null | Measure-Object).Count
Write-Host "GPUs: $gpuCount detected"

# Check Ollama
try {
    $tags = Invoke-RestMethod "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    Write-Host "Ollama: OK ($($tags.models.Count) models available)"
}
catch {
    Write-Host "WARNING: Ollama not responding at localhost:11434"
}

# Check gh CLI auth
$ghStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: gh CLI not authenticated. Run 'gh auth login' first."
    exit 1
}
Write-Host "GitHub CLI: Authenticated"

# ─── Get PAT for runners ────────────────────────────────────────────────

# Use gh CLI token directly as the ACCESS_TOKEN
$pat = gh auth token 2>$null
if (-not $pat -or $pat.Length -lt 10) {
    Write-Host "ERROR: Could not get GitHub token. Run 'gh auth login'."
    exit 1
}
Write-Host "GitHub PAT: Ready (len=$($pat.Length))"

# Set as env var for docker-compose
$env:GH_RUNNER_PAT = $pat

# ─── Ensure Network ─────────────────────────────────────────────────────

$netExists = docker network ls --filter name=slate_network --format "{{.Name}}" 2>$null
if (-not $netExists) {
    Write-Host "Creating slate_network..."
    docker network create slate_network --subnet 172.28.0.0/16 --gateway 172.28.0.1 2>&1
}

# ─── Ensure safe output directories exist ────────────────────────────────

$safeDirs = @("docs\wiki", "docs\report", "docs\pages", "plans")
foreach ($d in $safeDirs) {
    $p = Join-Path $ProjectRoot $d
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

# ─── Pull & Start ───────────────────────────────────────────────────────

Write-Host ""
Write-Host "Pulling runner image..."
docker pull myoung34/github-runner:latest 2>&1 | Select-Object -Last 3

Write-Host ""
Write-Host "Starting runners..."

$services = @()
if (-not $CpuOnly) { $services += "slate-runner-gpu-0", "slate-runner-gpu-1" }
if (-not $GpuOnly) { $services += "slate-runner-cpu-1", "slate-runner-cpu-2" }

if ($services.Count -gt 0) {
    docker compose -f $ComposeFile up -d @services 2>&1
}
else {
    docker compose -f $ComposeFile up -d 2>&1
}

# ─── Wait & Verify ──────────────────────────────────────────────────────

Write-Host ""
Write-Host "Waiting for runner registration (15s)..."
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "=== Final Status ==="
docker compose -f $ComposeFile ps --format "table {{.Name}}\t{{.Status}}" 2>&1
Write-Host ""

# Check registered runners on GitHub
Write-Host "=== GitHub-Registered Runners ==="
gh api "repos/SynchronizedLivingArchitecture/S.L.A.T.E/actions/runners" --jq '.runners[] | "\(.name)\t\(.status)\t\(.labels | map(.name) | join(","))"' 2>&1

Write-Host ""
Write-Host "============================================================"
Write-Host "  SLATE Runners Active"
Write-Host "  GPU: $gpuCount x RTX 5070 Ti"
Write-Host "  Monitor: .\scripts\start-runners.ps1 -Status"
Write-Host "  Stop:    .\scripts\start-runners.ps1 -Stop"
Write-Host "============================================================"
