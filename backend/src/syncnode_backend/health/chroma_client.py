"""
Shared ChromaDB client singleton.

Every part of the backend that needs a ChromaDB PersistentClient must import
`get_chroma_client()` from here instead of constructing its own instance.

ChromaDB 0.6+ raises "An instance of Chroma already exists … with different
settings" if two calls to PersistentClient() use different Settings objects
for the same persist_dir.  A single module-level singleton with a fixed
Settings object eliminates that conflict entirely.
"""

from __future__ import annotations

import threading
from typing import Optional

_client = None
_lock = threading.Lock()


def get_chroma_client():
    """Return the process-wide ChromaDB PersistentClient, creating it on first call."""
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:          # double-checked locking
            return _client
        from syncnode_backend.config.settings import settings
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        return _client


def reset_chroma_client() -> None:
    """Reset the singleton (test use only)."""
    global _client
    with _lock:
        _client = None
