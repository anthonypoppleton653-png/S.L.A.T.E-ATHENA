# Modified: 2026-02-09T19:45:00Z | Author: COPILOT | Change: CUDA Toolkit install script for TRELLIS.2
# SLATE CUDA Toolkit 12.4 Installer
# This script self-elevates and installs the CUDA Toolkit needed for o-voxel compilation

param(
    [switch]$Silent,
    [switch]$ExtractOnly
)

# Self-elevate if not admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting admin privileges..."
    $scriptPath = $MyInvocation.MyCommand.Definition
    $args = @("-ExecutionPolicy", "Bypass", "-File", $scriptPath)
    if ($Silent) { $args += "-Silent" }
    if ($ExtractOnly) { $args += "-ExtractOnly" }
    Start-Process powershell -ArgumentList $args -Verb RunAs -Wait
    exit
}

Write-Host "=" * 60
Write-Host "  SLATE CUDA Toolkit 12.4.1 Installer"
Write-Host "=" * 60
Write-Host ""

$installer = "$env:TEMP\cuda_12.4.1_installer.exe"
$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"

# Check if already installed
if (Test-Path "$cudaPath\bin\nvcc.exe") {
    Write-Host "[OK] CUDA 12.4 already installed at $cudaPath"
    & "$cudaPath\bin\nvcc.exe" --version
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 0
}

# Check installer exists
if (-not (Test-Path $installer)) {
    Write-Host "[ERROR] Installer not found at: $installer"
    Write-Host "Run this first to download:"
    Write-Host '  winget install --id Nvidia.CUDA --version 12.4'
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

$size = [math]::Round((Get-Item $installer).Length / 1GB, 2)
Write-Host "Installer: $installer ($size GB)"
Write-Host ""

if ($ExtractOnly) {
    $extractDir = "$env:TEMP\cuda_12.4.1_extracted"
    Write-Host "Extracting to $extractDir ..."
    & $installer -extract="$extractDir"
    if (Test-Path $extractDir) {
        Write-Host "[OK] Extracted successfully"
        Get-ChildItem $extractDir | Select-Object Name
    } else {
        Write-Host "[FAIL] Extraction failed"
    }
} else {
    Write-Host "Installing CUDA Toolkit 12.4.1 (silent mode)..."
    Write-Host "This will take several minutes..."
    Write-Host ""
    
    # Silent install - toolkit components only (no driver update)
    & $installer -s cuda_12.4 cudnn nvcc_12.4 cuobjdump_12.4 cupti_12.4 cuxxfilt_12.4 nvdisasm_12.4 nvprune_12.4 nvtx_12.4 sanitizer_12.4 cufft_12.4 cublas_12.4 curand_12.4 cusolver_12.4 cusparse_12.4 npp_12.4 nvjpeg_12.4 nvrtc_12.4 thrust_12.4 visual_studio_integration_12.4
    
    $exitCode = $LASTEXITCODE
    Write-Host ""
    
    if (Test-Path "$cudaPath\bin\nvcc.exe") {
        Write-Host "[OK] CUDA 12.4 installed successfully!"
        & "$cudaPath\bin\nvcc.exe" --version
        
        # Set environment variables
        [System.Environment]::SetEnvironmentVariable("CUDA_HOME", $cudaPath, "User")
        [System.Environment]::SetEnvironmentVariable("CUDA_PATH", $cudaPath, "User")
        $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*CUDA*v12.4*") {
            [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$cudaPath\bin", "User")
            Write-Host "[OK] Added CUDA to user PATH"
        }
        Write-Host "[OK] Set CUDA_HOME=$cudaPath"
        Write-Host ""
        Write-Host "IMPORTANT: Restart VS Code terminal to pick up new env vars!"
    } else {
        Write-Host "[FAIL] Installation failed (exit code: $exitCode)"
        Write-Host "Try running the installer manually:"
        Write-Host "  $installer"
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
