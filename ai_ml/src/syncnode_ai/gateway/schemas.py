"""
SyncNode Model Gateway — domain schemas.

These are the canonical typed contracts for all model/inference
operations. Only the OllamaAdapter may translate these to
Ollama-specific HTTP payloads.
"""

from __future__ import annotations

import base64
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Literal, Optional, Union

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Provider / scope                                                      #
# ------------------------------------------------------------------ #


class ProviderScope(str, Enum):
    LOCAL_LOOPBACK = "LOCAL_LOOPBACK"
    # Future: LOCAL_UNIX_SOCKET = "LOCAL_UNIX_SOCKET"


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ProviderHealth(BaseModel):
    provider: str
    scope: ProviderScope
    status: ProviderStatus
    model_id: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None


# ------------------------------------------------------------------ #
# Model capabilities                                                    #
# ------------------------------------------------------------------ #


class ModelCapabilities(BaseModel):
    completion: bool = True
    vision: bool = False
    audio: bool = False
    tools: bool = False
    thinking: bool = False
    streaming: bool = True
    structured_output: bool = True  # via format=json
    context_window: int = 8192
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None


class ModelProfile(BaseModel):
    """Runtime profile of a discovered local model."""

    provider: str
    model_id: str
    display_name: str
    capabilities: ModelCapabilities
    digest: Optional[str] = None
    size_bytes: Optional[int] = None
    priority: int = 100
    enabled: bool = True

    @property
    def is_local(self) -> bool:
        return True  # All profiles in Phase 1 are local


# ------------------------------------------------------------------ #
# Request / response                                                    #
# ------------------------------------------------------------------ #


class ImageInput(BaseModel):
    """An image to include in a multimodal inference request."""

    source: Literal["path", "base64", "url"] = "path"
    value: str  # file path, base64 string, or URL (local only)
    mime_type: str = "image/png"

    def to_base64(self) -> str:
        """Return base64-encoded image bytes regardless of source."""
        if self.source == "base64":
            return self.value
        if self.source == "path":
            return base64.b64encode(Path(self.value).read_bytes()).decode()
        raise ValueError(f"Cannot convert source={self.source!r} to base64 directly")


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    images: list[ImageInput] = Field(default_factory=list)


class ToolSchema(BaseModel):
    """JSON-schema definition of a tool callable by the model."""

    name: str
    description: str
    parameters: dict[str, Any]


class ModelRequest(BaseModel):
    """Normalized request sent to the Model Gateway."""

    model_id: str
    messages: list[Message]
    # Structured output — if set, gateway enforces JSON schema validation
    output_schema: Optional[dict[str, Any]] = None
    # Tool definitions available to the model
    tools: list[ToolSchema] = Field(default_factory=list)
    # Streaming mode
    stream: bool = False
    # Thinking/reasoning (if supported)
    thinking: bool = False
    # Token budget
    max_tokens: Optional[int] = None
    temperature: float = 0.0
    top_p: Optional[float] = None
    # Local runtime controls (translated to Ollama options / keep_alive by the
    # adapter). None => let the adapter fall back to its configured default.
    num_ctx: Optional[int] = None
    num_gpu: Optional[int] = None
    keep_alive: Optional[str] = None
    # Caller metadata for telemetry
    caller: str = "unknown"
    run_id: Optional[str] = None
    step_id: Optional[str] = None


class ModelResponse(BaseModel):
    """Normalized response from the Model Gateway."""

    model_id: str
    content: str
    # If structured output was requested, parsed_output contains validated object
    parsed_output: Optional[dict[str, Any]] = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    thinking_content: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"


class ModelStreamEvent(BaseModel):
    """One chunk in a streaming model response."""

    event_type: Literal["delta", "tool_call", "done", "error"]
    delta: Optional[str] = None
    tool_call: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    done: bool = False
    # Aggregated stats sent with the final "done" event
    input_tokens: int = 0
    output_tokens: int = 0
