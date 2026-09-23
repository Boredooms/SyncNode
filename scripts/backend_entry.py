#!/usr/bin/env python3
"""
SyncNode Backend — PyInstaller entry point.

This file is the __main__ of the bundled executable.
It sets PYTHONPATH-equivalent sys.path entries and launches uvicorn.
"""
import os
import sys
from pathlib import Path

# When running from PyInstaller bundle, _MEIPASS is the temp extract dir
BUNDLE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

# Ensure the app working dir has a writable data/ folder
APP_DIR = Path(os.environ.get("SYNCNODE_APP_DIR", Path.home() / ".syncnode"))
APP_DIR.mkdir(parents=True, exist_ok=True)

# Point database and rag index at the user's app data dir (writable)
os.environ.setdefault("DATABASE_URL",     f"sqlite+aiosqlite:///{APP_DIR / 'syncnode.db'}")
os.environ.setdefault("CHROMA_PERSIST_DIR", str(APP_DIR / "rag_index"))
os.environ.setdefault("SYNCNODE_WORKSPACE_ROOT", str(APP_DIR / "workspace"))
os.environ.setdefault("SYNCNODE_DEMO_WORKSPACE", str(APP_DIR / "workspace" / "demo"))
os.environ.setdefault("SYNCNODE_KNOWLEDGE_ROOT", str(BUNDLE / "knowledge"))

# Ollama GPU stability
os.environ.setdefault("CUDA_VISIBLE_DEVICES",     "0")
os.environ.setdefault("OLLAMA_IGPU_ENABLE",        "0")
os.environ.setdefault("OLLAMA_LOAD_TIMEOUT",       "300s")
os.environ.setdefault("OLLAMA_MAX_LOADED_MODELS",  "1")

# Load .env from bundle if present
env_file = BUNDLE / ".env.default"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Launch backend
import uvicorn
uvicorn.run(
    "syncnode_backend.main:app",
    host=os.environ.get("SYNCNODE_API_HOST", "127.0.0.1"),
    port=int(os.environ.get("SYNCNODE_API_PORT", "8000")),
    log_level=os.environ.get("SYNCNODE_LOG_LEVEL", "info").lower(),
    access_log=True,
)
