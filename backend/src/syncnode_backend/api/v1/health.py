"""
SyncNode — Health endpoints.

GET /health          — basic liveness
GET /health/ready    — full readiness (all subsystems)
GET /health/model    — Ollama / model status
GET /health/database — database connectivity
GET /health/rag      — ChromaDB / RAG status
GET /health/computer — Windows UIA availability
GET /health/browser  — Playwright browser status
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from syncnode_backend.config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_liveness() -> dict[str, Any]:
    return {"status": "ok", "service": "syncnode-backend", "ts": time.time()}


@router.get("/health/ready")
async def health_readiness() -> JSONResponse:
    checks: dict[str, Any] = {}
    all_ok = True

    # Database
    try:
        from syncnode_backend.persistence.database import get_engine
        from sqlalchemy import text
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "error", "error": str(exc)}
        all_ok = False

    # Model / Ollama
    try:
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        health = await adapter.health(settings.syncnode_model_id)
        await adapter.close()
        checks["model"] = {
            "status": health.status.value,
            "model_id": health.model_id,
            "latency_ms": health.latency_ms,
        }
        if health.status.value != "healthy":
            all_ok = False
    except Exception as exc:
        checks["model"] = {"status": "error", "error": str(exc)}
        all_ok = False

    # RAG
    try:
        from syncnode_backend.config.settings import settings as s
        import chromadb
        client = chromadb.PersistentClient(path=s.chroma_persist_dir)
        cols = client.list_collections()
        checks["rag"] = {"status": "ok", "collections": len(cols)}
    except Exception as exc:
        checks["rag"] = {"status": "error", "error": str(exc)}
        # RAG not critical for basic readiness

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"ready": all_ok, "checks": checks, "ts": time.time()},
    )


@router.get("/health/model")
async def health_model() -> dict[str, Any]:
    try:
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        profiles = await adapter.list_models()
        health = await adapter.health(settings.syncnode_model_id)
        await adapter.close()

        local_profiles = [p for p in profiles if not p.model_id.endswith(":cloud")]
        target = next((p for p in local_profiles if p.model_id == settings.syncnode_model_id), None)

        return {
            "status": health.status.value,
            "model_id": settings.syncnode_model_id,
            "latency_ms": health.latency_ms,
            "error": health.error,
            "target_profile": target.model_dump() if target else None,
            "local_models_available": len(local_profiles),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health/database")
async def health_database() -> dict[str, Any]:
    try:
        from syncnode_backend.persistence.database import get_engine
        from sqlalchemy import text
        engine = get_engine()
        t0 = time.monotonic()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.monotonic() - t0) * 1000
        return {"status": "ok", "latency_ms": latency_ms, "url": settings.database_url.split("?")[0]}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health/rag")
async def health_rag() -> dict[str, Any]:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        cols = client.list_collections()
        return {
            "status": "ok",
            "persist_dir": settings.chroma_persist_dir,
            "collections": [c.name for c in cols],
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health/computer")
async def health_computer() -> dict[str, Any]:
    try:
        import uiautomation as auto
        root = auto.GetRootControl()
        return {"status": "ok", "uia_root": root.Name or "Desktop"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health/browser")
async def health_browser() -> dict[str, Any]:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("about:blank")
            await browser.close()
        return {"status": "ok", "browser_type": settings.syncnode_browser_type}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
