#!/usr/bin/env python3
"""
SyncNode — Backend server startup script.

Sets all required environment variables (CUDA, Ollama GPU timeout, Python paths)
before launching uvicorn so the backend starts correctly on Windows with RTX GPU.

Usage:
    python scripts/start_server.py [--port 8000] [--reload] [--log-level info]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _load_dotenv(env_file: Path) -> dict:
    """Load .env file into a dict without requiring python-dotenv at import time."""
    result = {}
    if not env_file.exists():
        return result
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Start SyncNode backend")
    parser.add_argument("--host",      default="127.0.0.1")
    parser.add_argument("--port",      type=int, default=8000)
    parser.add_argument("--reload",    action="store_true", default=False)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    # ── Build environment ─────────────────────────────────────────────────────
    env = os.environ.copy()

    # Load .env file values first (project-level overrides)
    dotenv_path = ROOT / ".env"
    dotenv_vals = _load_dotenv(dotenv_path)
    env.update(dotenv_vals)

    # ── Ollama / CUDA stability fixes ─────────────────────────────────────────
    # These fix the "llama-server GPU discovery watchdog timed out" error on
    # Windows single-GPU systems (RTX 2050 + Intel iGPU coexisting).
    #
    # 1. Force CUDA device 0 — prevents multi-GPU probe loop
    env.setdefault("CUDA_VISIBLE_DEVICES", "0")
    # 2. Disable Intel iGPU Vulkan probing — we only want CUDA
    env.setdefault("OLLAMA_IGPU_ENABLE",   "0")
    # 3. Longer load timeout — gives llama-server more time to init CUDA on cold start
    env.setdefault("OLLAMA_LOAD_TIMEOUT",  "300s")
    # 4. Limit to 1 concurrent model load — prevents parallel CUDA init deadlock
    env.setdefault("OLLAMA_MAX_LOADED_MODELS", "1")
    # 5. Keep model warm between workflow steps (avoids 11-19s cold reload per step)
    env.setdefault("OLLAMA_KEEP_ALIVE", "30m")

    # ── Python paths ──────────────────────────────────────────────────────────
    backend_src = ROOT / "backend" / "src"
    ai_ml_src   = ROOT / "ai_ml"   / "src"

    existing_pp = env.get("PYTHONPATH", "")
    new_pp = os.pathsep.join(
        str(p) for p in [backend_src, ai_ml_src]
        if str(p) not in existing_pp
    )
    env["PYTHONPATH"] = f"{new_pp}{os.pathsep}{existing_pp}" if existing_pp else new_pp

    # ── uvicorn command ───────────────────────────────────────────────────────
    cmd = [
        sys.executable, "-m", "uvicorn",
        "syncnode_backend.main:app",
        "--host",      args.host,
        "--port",      str(args.port),
        "--log-level", args.log_level,
    ]
    if args.reload:
        cmd += ["--reload",
                "--reload-dir", str(ROOT / "backend" / "src"),
                "--reload-dir", str(ROOT / "ai_ml"   / "src")]

    print(f"▶  SyncNode backend → http://{args.host}:{args.port}")
    print(f"   CUDA_VISIBLE_DEVICES = {env['CUDA_VISIBLE_DEVICES']}")
    print(f"   OLLAMA_IGPU_ENABLE   = {env['OLLAMA_IGPU_ENABLE']}")
    print(f"   OLLAMA_LOAD_TIMEOUT  = {env['OLLAMA_LOAD_TIMEOUT']}")
    print(f"   PYTHONPATH           = {env['PYTHONPATH'][:80]}…")

    subprocess.run(cmd, env=env, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    main()
