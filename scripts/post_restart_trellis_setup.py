# Modified: 2026-02-09T20:15:00Z | Author: COPILOT | Change: Post-restart CUDA + o-voxel setup script
# SLATE TRELLIS.2 Post-Restart Setup
# Run this after restarting Windows to complete CUDA Toolkit + o-voxel installation
#
# Usage: .\.venv\Scripts\python.exe scripts\post_restart_trellis_setup.py

import subprocess
import sys
import os
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
VENV_PYTHON = WORKSPACE / ".venv" / "Scripts" / "python.exe"
VENV_PIP = WORKSPACE / ".venv" / "Scripts" / "pip.exe"
O_VOXEL_DIR = WORKSPACE / "models" / "trellis2" / "o-voxel"
CUDA_PATHS = [
    Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"),
    Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6"),
    Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5"),
]

def check_mark(ok):
    return "\u2713" if ok else "\u2717"

def main():
    print("=" * 60)
    print("  SLATE TRELLIS.2 Post-Restart Setup")
    print("=" * 60)
    print()

    # Step 1: Find CUDA Toolkit
    print("Step 1: Checking CUDA Toolkit...")
    cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    if cuda_home and Path(cuda_home).exists():
        print(f"  {check_mark(True)} CUDA_HOME set: {cuda_home}")
    else:
        # Search common paths
        cuda_home = None
        for p in CUDA_PATHS:
            if (p / "bin" / "nvcc.exe").exists():
                cuda_home = str(p)
                break
        if not cuda_home:
            # Search broadly
            cuda_base = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
            if cuda_base.exists():
                versions = sorted(cuda_base.iterdir(), reverse=True)
                for v in versions:
                    if (v / "bin" / "nvcc.exe").exists():
                        cuda_home = str(v)
                        break

        if cuda_home:
            print(f"  {check_mark(True)} Found CUDA at: {cuda_home}")
            os.environ["CUDA_HOME"] = cuda_home
            os.environ["CUDA_PATH"] = cuda_home
            print(f"  Set CUDA_HOME={cuda_home}")
        else:
            print(f"  {check_mark(False)} CUDA Toolkit not found!")
            print("  Please run the CUDA installer again:")
            print(f'    Start-Process "{os.environ["TEMP"]}\\cuda_12.4.1_installer.exe"')
            print("  Then restart and run this script again.")
            sys.exit(1)

    # Verify nvcc works
    nvcc = Path(cuda_home) / "bin" / "nvcc.exe"
    if nvcc.exists():
        result = subprocess.run([str(nvcc), "--version"], capture_output=True, text=True)
        version_line = [l for l in result.stdout.splitlines() if "release" in l.lower()]
        if version_line:
            print(f"  {check_mark(True)} nvcc: {version_line[0].strip()}")
        else:
            print(f"  {check_mark(True)} nvcc found at {nvcc}")
    else:
        print(f"  {check_mark(False)} nvcc.exe not found at {nvcc}")
        sys.exit(1)

    print()

    # Step 2: Build o-voxel
    print("Step 2: Building o-voxel...")
    if not O_VOXEL_DIR.exists():
        print(f"  {check_mark(False)} o-voxel directory not found at {O_VOXEL_DIR}")
        print("  Run: git submodule update --init --recursive")
        sys.exit(1)

    if not (O_VOXEL_DIR / "setup.py").exists():
        print(f"  {check_mark(False)} setup.py not found in {O_VOXEL_DIR}")
        sys.exit(1)

    print(f"  Building from {O_VOXEL_DIR}...")
    print("  This compiles CUDA kernels — may take 2-5 minutes...")
    print()

    env = os.environ.copy()
    env["CUDA_HOME"] = cuda_home
    env["CUDA_PATH"] = cuda_home

    proc = subprocess.run(
        [str(VENV_PIP), "install", "-e", str(O_VOXEL_DIR)],
        env=env,
        timeout=600,
    )

    if proc.returncode == 0:
        print()
        print(f"  {check_mark(True)} o-voxel installed successfully!")
    else:
        print()
        print(f"  {check_mark(False)} o-voxel build failed (exit code {proc.returncode})")
        print("  Check the error output above.")
        print("  Common fixes:")
        print("    - Ensure Visual Studio Build Tools are installed")
        print("    - Ensure CUDA_HOME is set correctly")
        print("    - Try: $env:CUDA_HOME = '" + cuda_home + "'")
        sys.exit(1)

    print()

    # Step 3: Verify TRELLIS is ready
    print("Step 3: Verifying TRELLIS.2 status...")
    proc = subprocess.run(
        [str(VENV_PYTHON), str(WORKSPACE / "slate" / "slate_trellis.py"), "--status"],
        env=env,
    )
    print()

    # Step 4: Quick import test
    print("Step 4: Quick import test...")
    test_proc = subprocess.run(
        [str(VENV_PYTHON), "-c", "import o_voxel; print('o_voxel OK:', o_voxel.__file__)"],
        capture_output=True, text=True, env=env,
    )
    if test_proc.returncode == 0:
        print(f"  {check_mark(True)} {test_proc.stdout.strip()}")
    else:
        print(f"  {check_mark(False)} o_voxel import failed: {test_proc.stderr.strip()[:200]}")

    print()
    print("=" * 60)
    print("  Setup complete! Start the dashboard with:")
    print(f"  {VENV_PYTHON} agents/slate_dashboard_server.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
