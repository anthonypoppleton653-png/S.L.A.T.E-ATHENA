#!/usr/bin/env python3
"""Test slate import to find blocking issue."""
import sys
sys.path.insert(0, '.')

print("Step 1: Testing basic imports...")
import os
import json
import logging
print("Step 1: OK")

# Test each slate submodule individually
submodules = [
    'torch_config',
    'message_broker', 
    'rag_memory',
    'gpu_scheduler',
    'slate_agent_v2',
    'file_lock',
    'slate_orchestrator',
    'llm_cache',
    'shared_knowledge',
    'proactive_tasks',
    'dual_gpu_training',
]

for mod in submodules:
    print(f"Testing slate.{mod}...", flush=True)
    try:
        __import__(f'slate.{mod}')
        print(f"  {mod}: OK")
    except Exception as e:
        print(f"  {mod}: FAIL - {e}")

print("All tests complete!")

