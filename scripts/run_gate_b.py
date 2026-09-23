#!/usr/bin/env python3
"""
SyncNode — Gate B smoke test runner.

Tests the local Gemma capability without the full backend.
"""

import subprocess
import sys
from pathlib import Path

AI_ML_SRC = Path(__file__).parents[1] / "ai_ml" / "src"
BACKEND_SRC = Path(__file__).parents[1] / "backend" / "src"
TEST_PATH = Path(__file__).parents[1] / "ai_ml" / "tests" / "model" / "test_local_gemma_capabilities.py"

import os
env = os.environ.copy()
env["PYTHONPATH"] = f"{AI_ML_SRC};{BACKEND_SRC};{env.get('PYTHONPATH', '')}"

cmd = [
    sys.executable, "-m", "pytest",
    str(TEST_PATH),
    "-v", "-s", "--tb=short",
    "--asyncio-mode=auto",
]

print("=" * 60)
print("GATE B: Local Gemma Capability Test")
print("=" * 60)
result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
