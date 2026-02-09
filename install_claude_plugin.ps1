# SLATE Claude Code Plugin Installer (PowerShell)
# Registers SLATE marketplace with Claude Code - plugins load dynamically

param(
    [switch]$Uninstall,
    [switch]$Validate,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "SLATE Claude Code Plugin" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# Check Python venv
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python venv not found at $PythonExe" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Build arguments
$PyArgs = @()
if ($Uninstall) { $PyArgs += "--uninstall" }
if ($Validate) { $PyArgs += "--validate" }
if ($Dev) { $PyArgs += "--dev" }

# Run installer
& $PythonExe (Join-Path $ScriptDir "install_claude_plugin.py") @PyArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Plugin ready! Commands are namespaced as /slate:<command>" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "  /slate:help     - Show all SLATE commands"
Write-Host "  /slate:status   - Check system status"
Write-Host "  /slate:start    - Start SLATE services"
Write-Host ""
Write-Host "For GitHub distribution:" -ForegroundColor Yellow
Write-Host "  /plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E"
Write-Host "  /plugin install slate@slate"
