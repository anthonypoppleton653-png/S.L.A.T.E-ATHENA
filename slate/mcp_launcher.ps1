# SLATE MCP Server Launcher for Windows
# Modified: 2026-02-09T03:30:00Z | Author: Claude Opus 4.5 | Change: PowerShell launcher for reliable Python detection

$ErrorActionPreference = "Stop"

# Detect script location (works for both local and cached plugin)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginRoot = Split-Path -Parent $ScriptDir

# Check for SLATE_PLUGIN_ROOT env var (set by Claude Code)
if ($env:SLATE_PLUGIN_ROOT) {
    $PluginRoot = $env:SLATE_PLUGIN_ROOT
}

$McpServer = Join-Path $PluginRoot "slate\mcp_server.py"

# Find Python - try multiple locations
$PythonCandidates = @(
    (Join-Path $PluginRoot ".venv\Scripts\python.exe"),
    (Join-Path $PluginRoot "venv\Scripts\python.exe"),
    "py.exe",
    "python.exe",
    "python3.exe"
)

$Python = $null
foreach ($candidate in $PythonCandidates) {
    if (Test-Path $candidate -ErrorAction SilentlyContinue) {
        $Python = $candidate
        break
    }
    # Also check if it's in PATH
    $inPath = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($inPath) {
        $Python = $inPath.Source
        break
    }
}

if (-not $Python) {
    Write-Error "ERROR: Python not found. Tried: $($PythonCandidates -join ', ')"
    exit 1
}

if (-not (Test-Path $McpServer)) {
    Write-Error "ERROR: MCP server not found at $McpServer"
    exit 1
}

# Set environment
$env:SLATE_WORKSPACE = $PluginRoot
$env:PYTHONPATH = $PluginRoot
if (-not $env:SLATE_BEHAVIOR) { $env:SLATE_BEHAVIOR = "operator" }
if (-not $env:SLATE_ACTIONGUARD) { $env:SLATE_ACTIONGUARD = "enabled" }

# Run MCP server
& $Python $McpServer $args
exit $LASTEXITCODE
