"""
SyncNode — Model Management API.

GET  /api/v1/models          — list all locally available Ollama models
GET  /api/v1/models/active   — get the currently active model
POST /api/v1/models/active   — switch the active model (hot-swap, no restart)
GET  /api/v1/models/{id}     — get profile for a specific model
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response schemas ────────────────────────────────────────────────────────

class ModelCapabilitiesOut(BaseModel):
    completion: bool = True
    vision: bool = False
    audio: bool = False
    tools: bool = False
    thinking: bool = False
    streaming: bool = True
    structured_output: bool = True
    context_window: int = 4096
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None


class ModelProfileOut(BaseModel):
    model_id: str
    display_name: str
    provider: str
    capabilities: ModelCapabilitiesOut
    size_bytes: Optional[int] = None
    digest: Optional[str] = None
    is_active: bool = False


class SetActiveModelRequest(BaseModel):
    model_id: str


class SetActiveModelResponse(BaseModel):
    model_id: str
    previous_model_id: str
    restarted: bool = False
    message: str


# ── Runtime model registry (in-process, no restart required) ────────────────
# The active model can be hot-swapped: the orchestrator reads settings at run
# creation time, so any run created after the swap uses the new model.

_active_model_override: Optional[str] = None   # None = use settings default


def get_active_model_id() -> str:
    """Return the currently active model ID (override or settings default)."""
    from syncnode_backend.config.settings import settings
    return _active_model_override or settings.syncnode_model_id


def set_active_model_id(model_id: str) -> str:
    """Hot-swap the active model. Returns the previous model ID."""
    global _active_model_override
    previous = get_active_model_id()
    _active_model_override = model_id
    logger.info("[MODELS] active model changed %r → %r", previous, model_id)
    return previous


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/models", response_model=list[ModelProfileOut])
async def list_models():
    """List all locally available Ollama models with their capabilities."""
    try:
        from syncnode_backend.config.settings import settings
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        profiles = await adapter.list_models()
        await adapter.close()

        active = get_active_model_id()
        return [
            ModelProfileOut(
                model_id=p.model_id,
                display_name=p.display_name,
                provider=p.provider,
                capabilities=ModelCapabilitiesOut(
                    completion=p.capabilities.completion,
                    vision=p.capabilities.vision,
                    audio=p.capabilities.audio,
                    tools=p.capabilities.tools,
                    thinking=p.capabilities.thinking,
                    streaming=p.capabilities.streaming,
                    structured_output=p.capabilities.structured_output,
                    context_window=p.capabilities.context_window,
                    parameter_size=p.capabilities.parameter_size,
                    quantization=p.capabilities.quantization,
                ),
                size_bytes=p.size_bytes,
                digest=p.digest,
                is_active=(p.model_id == active),
            )
            for p in profiles
        ]
    except Exception as exc:
        logger.error("list_models failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Failed to list Ollama models: {exc}")


@router.get("/models/active", response_model=ModelProfileOut)
async def get_active_model():
    """Return the currently active model profile."""
    active = get_active_model_id()
    try:
        from syncnode_backend.config.settings import settings
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        profile = await adapter.get_model_profile(active)
        await adapter.close()
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Active model {active!r} not found in Ollama")
        return ModelProfileOut(
            model_id=profile.model_id,
            display_name=profile.display_name,
            provider=profile.provider,
            capabilities=ModelCapabilitiesOut(
                completion=profile.capabilities.completion,
                vision=profile.capabilities.vision,
                audio=profile.capabilities.audio,
                tools=profile.capabilities.tools,
                thinking=profile.capabilities.thinking,
                streaming=profile.capabilities.streaming,
                structured_output=profile.capabilities.structured_output,
                context_window=profile.capabilities.context_window,
                parameter_size=profile.capabilities.parameter_size,
                quantization=profile.capabilities.quantization,
            ),
            size_bytes=profile.size_bytes,
            digest=profile.digest,
            is_active=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/models/active", response_model=SetActiveModelResponse)
async def set_active_model(req: SetActiveModelRequest):
    """
    Hot-swap the active model.

    The new model must be available in the local Ollama instance.
    Runs created AFTER this call will use the new model.
    No backend restart required.
    """
    from syncnode_backend.config.settings import settings
    from syncnode_ai.gateway.ollama_adapter import OllamaAdapter

    # Verify the requested model actually exists
    try:
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        profile = await adapter.get_model_profile(req.model_id)
        await adapter.close()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Ollama: {exc}")

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model {req.model_id!r} is not available in local Ollama. "
                   f"Run: ollama pull {req.model_id}"
        )

    previous = set_active_model_id(req.model_id)
    return SetActiveModelResponse(
        model_id=req.model_id,
        previous_model_id=previous,
        restarted=False,
        message=f"Active model switched from {previous!r} to {req.model_id!r}. "
                f"New runs will use {req.model_id!r}.",
    )


@router.get("/models/{model_id:path}", response_model=ModelProfileOut)
async def get_model(model_id: str):
    """Return the profile for a specific model by ID."""
    from syncnode_backend.config.settings import settings
    from syncnode_ai.gateway.ollama_adapter import OllamaAdapter

    try:
        adapter = OllamaAdapter(base_url=settings.ollama_base_url, timeout=10.0)
        profile = await adapter.get_model_profile(model_id)
        await adapter.close()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if profile is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id!r} not found in Ollama")

    active = get_active_model_id()
    return ModelProfileOut(
        model_id=profile.model_id,
        display_name=profile.display_name,
        provider=profile.provider,
        capabilities=ModelCapabilitiesOut(
            completion=profile.capabilities.completion,
            vision=profile.capabilities.vision,
            audio=profile.capabilities.audio,
            tools=profile.capabilities.tools,
            thinking=profile.capabilities.thinking,
            streaming=profile.capabilities.streaming,
            structured_output=profile.capabilities.structured_output,
            context_window=profile.capabilities.context_window,
            parameter_size=profile.capabilities.parameter_size,
            quantization=profile.capabilities.quantization,
        ),
        size_bytes=profile.size_bytes,
        digest=profile.digest,
        is_active=(profile.model_id == active),
    )
