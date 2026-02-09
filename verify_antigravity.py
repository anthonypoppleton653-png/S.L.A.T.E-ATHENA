# Modified: 2026-02-09T02:10:00Z | Author: COPILOT | Change: Add timestamp comment for SLATE compliance
import sys
from pathlib import Path

# Add workspace root
WORKSPACE_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(WORKSPACE_ROOT))

def check():
    print("Verifying Antigravity Integration...")
    
    # 1. Agent Registration
    try:
        # Windows DLL Fix
        import os
        site_packages = Path(sys.executable).parent.parent / "Lib" / "site-packages"
        torch_lib = site_packages / "torch" / "lib"
        if torch_lib.exists():
            os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ["PATH"]
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(torch_lib))

        from slate.instruction_loader import get_instruction_loader
        loader = get_instruction_loader()
        prompt = loader.get_agent_prompt("ANTIGRAVITY")
        if "Google AI Ultra" in prompt:
            print("[PASS] Agent 'ANTIGRAVITY' registered in instruction_loader.")
        else:
            print("[FAIL] Agent 'ANTIGRAVITY' prompt mismatch.")
    except Exception as e:
        print(f"[FAIL] Check Agent Registration: {e}")

    # 2. Plugin Existence
    plugin_path = WORKSPACE_ROOT / "plugins" / "slate-antigravity" / "plugin.json"
    if plugin_path.exists():
        print("[PASS] Plugin 'slate-antigravity' exists.")
    else:
        print("[FAIL] Plugin 'slate-antigravity' missing.")

    # 3. Environment (GPU)
    try:
        import torch
        if torch.cuda.is_available():
            print(f"[PASS] GPU Available: {torch.cuda.get_device_name(0)}")
        else:
            print("[FAIL] GPU not available in torch.")
    except ImportError:
        print("[FAIL] torch not installed.")
    
    # 4. MCP Config
    mcp_path = WORKSPACE_ROOT / ".mcp.json"
    if ".venv_slate_ag" in mcp_path.read_text():
        print("[PASS] .mcp.json uses .venv_slate_ag.")
    else:
        print("[FAIL] .mcp.json does not use isolated venv.")

if __name__ == "__main__":
    check()
