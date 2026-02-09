# SLATE Plugin Mode Toggle
# Switches between local development and marketplace modes
# Usage: .\toggle_plugin_mode.ps1 [marketplace|local]

param(
    [Parameter(Position=0)]
    [ValidateSet("marketplace", "local", "status")]
    [string]$Mode = "status"
)

$PluginDir = ".claude-plugin"
$DisabledDir = ".claude-plugin.disabled"

function Get-CurrentMode {
    if (Test-Path $PluginDir) {
        return "local"
    } elseif (Test-Path $DisabledDir) {
        return "marketplace"
    } else {
        return "none"
    }
}

$CurrentMode = Get-CurrentMode

switch ($Mode) {
    "status" {
        Write-Host "SLATE Plugin Mode Status" -ForegroundColor Cyan
        Write-Host "========================" -ForegroundColor Cyan
        Write-Host ""
        if ($CurrentMode -eq "local") {
            Write-Host "Current Mode: LOCAL (auto-loads from .claude-plugin/)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Plugin auto-loads at PROJECT scope when in this workspace."
            Write-Host ""
            Write-Host "To switch to marketplace mode:"
            Write-Host "  .\toggle_plugin_mode.ps1 marketplace" -ForegroundColor Green
        } elseif ($CurrentMode -eq "marketplace") {
            Write-Host "Current Mode: MARKETPLACE (from GitHub)" -ForegroundColor Green
            Write-Host ""
            Write-Host "Plugin loads from GitHub marketplace at USER scope."
            Write-Host ""
            Write-Host "To switch back to local mode:"
            Write-Host "  .\toggle_plugin_mode.ps1 local" -ForegroundColor Yellow
        } else {
            Write-Host "Current Mode: NONE (plugin directory missing)" -ForegroundColor Red
        }
    }
    "marketplace" {
        if ($CurrentMode -eq "marketplace") {
            Write-Host "Already in marketplace mode." -ForegroundColor Green
            exit 0
        }
        if (Test-Path $PluginDir) {
            Rename-Item $PluginDir $DisabledDir
            Write-Host "Switched to MARKETPLACE mode" -ForegroundColor Green
            Write-Host ""
            Write-Host "The .claude-plugin/ directory has been disabled (renamed to .claude-plugin.disabled/)"
            Write-Host ""
            Write-Host "Now enable the marketplace plugin in Claude Code:"
            Write-Host "  /plugin enable slate@slate-marketplace" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Or restart Claude Code to use the marketplace version."
        } else {
            Write-Host "Error: .claude-plugin/ not found" -ForegroundColor Red
            exit 1
        }
    }
    "local" {
        if ($CurrentMode -eq "local") {
            Write-Host "Already in local mode." -ForegroundColor Yellow
            exit 0
        }
        if (Test-Path $DisabledDir) {
            Rename-Item $DisabledDir $PluginDir
            Write-Host "Switched to LOCAL mode" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "The .claude-plugin/ directory has been restored."
            Write-Host ""
            Write-Host "The plugin will auto-load at project scope."
            Write-Host "Restart Claude Code to apply."
        } else {
            Write-Host "Error: .claude-plugin.disabled/ not found" -ForegroundColor Red
            exit 1
        }
    }
}
