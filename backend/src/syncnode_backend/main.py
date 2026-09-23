"""
SyncNode — FastAPI main application.

Defines the app with lifespan startup/shutdown, health endpoints,
and API v1 router registration.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from syncnode_backend.config.logging_setup import configure_logging
from syncnode_backend.config.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    configure_logging(level=settings.syncnode_log_level, fmt=settings.syncnode_log_format)
    logger.info(f"SyncNode backend starting — model={settings.syncnode_model_id}")

    # Initialize database
    from syncnode_backend.persistence.database import init_database
    await init_database()
    logger.info("Database initialized")

    # Ensure workspace dirs exist
    settings.syncnode_workspace_root.mkdir(parents=True, exist_ok=True)
    settings.syncnode_demo_workspace.mkdir(parents=True, exist_ok=True)

    # Register all tools
    from syncnode_backend.tools.registry import tool_registry
    from syncnode_backend.documents.tools import register_document_tools
    from syncnode_backend.computer.tools import register_computer_tools
    from syncnode_backend.browser.tools import register_browser_tools
    from syncnode_backend.office.tools import register_office_tools
    from syncnode_backend.system.tools import register_system_tools
    register_document_tools(tool_registry)
    register_computer_tools(tool_registry)
    register_browser_tools(tool_registry)
    register_office_tools(tool_registry)
    register_system_tools(tool_registry)
    logger.info(f"Tool registry initialized — {len(tool_registry.all_enabled())} tools")

    yield

    # Shutdown
    logger.info("SyncNode backend shutting down")
    from syncnode_backend.browser.tools import close_browser
    try:
        await close_browser()
    except Exception:
        pass
    from syncnode_backend.persistence.database import close_database
    await close_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SyncNode Backend",
        description="Sovereign local multi-agent AI workbench backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    from syncnode_backend.api.v1 import (
        runs, health, events, knowledge, tools, learning, chat,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(runs.router, prefix="/api/v1", tags=["runs"])
    app.include_router(events.router, prefix="/api/v1", tags=["events"])
    app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
    app.include_router(tools.router, prefix="/api/v1", tags=["tools"])
    app.include_router(learning.router, prefix="/api/v1", tags=["learning"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

    @app.exception_handler(Exception)
    async def generic_handler(request, exc):
        logger.error(f"Unhandled exception — error={str(exc)} path={str(request.url)}")
        return JSONResponse(status_code=500, content={"error": str(exc), "type": type(exc).__name__})

    return app


app = create_app()