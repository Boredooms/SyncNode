"""
SyncNode — Ollama Provider Adapter.

This is the ONLY module permitted to speak the Ollama HTTP protocol.
All other code uses the ModelGateway domain interface.

Invariant MG-01: All requests must resolve to loopback.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator, Optional

import httpx

from syncnode_ai.gateway.schemas import (
    ImageInput,
    Message,
    ModelCapabilities,
    ModelProfile,
    ModelRequest,
    ModelResponse,
    ModelStreamEvent,
    ProviderHealth,
    ProviderScope,
    ProviderStatus,
)


class OllamaAdapter:
    """
    Adapts the SyncNode ModelGateway domain interface to the Ollama HTTP API.

    Speaks:
    - GET  /api/tags        — model discovery
    - POST /api/chat        — chat completion (text, vision, tools, structured)
    - POST /api/show        — model detail
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 300.0,
        *,
        default_num_ctx: int = 8192,
        default_num_gpu: Optional[int] = 99,
        default_keep_alive: str = "30m",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        # Runtime defaults applied when a ModelRequest does not override them.
        # These are the measured-optimal values for the target GPU; see
        # docs/INFERENCE_OPTIMIZATION.md.
        self._default_num_ctx = default_num_ctx
        self._default_num_gpu = default_num_gpu
        self._default_keep_alive = default_keep_alive
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(connect=10.0, read=timeout, write=30.0, pool=10.0),
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=8),
        )

    # ---------------------------------------------------------------- #
    # Model discovery                                                    #
    # ---------------------------------------------------------------- #

    async def list_models(self) -> list[ModelProfile]:
        """Fetch all locally available models from /api/tags."""
        response = await self._client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        profiles = []
        for m in data.get("models", []):
            caps_list: list[str] = m.get("capabilities", [])
            detail = m.get("details", {})
            profiles.append(
                ModelProfile(
                    provider="ollama",
                    model_id=m["name"],
                    display_name=m["name"],
                    capabilities=ModelCapabilities(
                        completion="completion" in caps_list,
                        vision="vision" in caps_list,
                        audio="audio" in caps_list,
                        tools="tools" in caps_list,
                        thinking="thinking" in caps_list,
                        streaming=True,
                        structured_output=True,
                        context_window=detail.get("context_length", 8192),
                        parameter_size=detail.get("parameter_size"),
                        quantization=detail.get("quantization_level"),
                    ),
                    digest=m.get("digest"),
                    size_bytes=m.get("size"),
                )
            )
        return profiles

    async def get_model_profile(self, model_id: str) -> Optional[ModelProfile]:
        """Return the profile for a specific model_id, or None if not found."""
        profiles = await self.list_models()
        for p in profiles:
            if p.model_id == model_id:
                return p
        return None

    # ---------------------------------------------------------------- #
    # Health check                                                       #
    # ---------------------------------------------------------------- #

    async def health(self, model_id: str) -> ProviderHealth:
        """Quick health probe — list models and verify the target is present."""
        start = time.monotonic()
        try:
            profile = await self.get_model_profile(model_id)
            latency_ms = (time.monotonic() - start) * 1000
            if profile is None:
                return ProviderHealth(
                    provider="ollama",
                    scope=ProviderScope.LOCAL_LOOPBACK,
                    status=ProviderStatus.UNAVAILABLE,
                    model_id=model_id,
                    latency_ms=latency_ms,
                    error=f"Model {model_id!r} not found in Ollama",
                )
            return ProviderHealth(
                provider="ollama",
                scope=ProviderScope.LOCAL_LOOPBACK,
                status=ProviderStatus.HEALTHY,
                model_id=model_id,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return ProviderHealth(
                provider="ollama",
                scope=ProviderScope.LOCAL_LOOPBACK,
                status=ProviderStatus.UNAVAILABLE,
                model_id=model_id,
                latency_ms=latency_ms,
                error=str(exc),
            )

    # ---------------------------------------------------------------- #
    # Chat completion                                                    #
    # ---------------------------------------------------------------- #

    def _build_ollama_messages(self, messages: list[Message]) -> list[dict]:
        """Convert domain Message list to Ollama's message format."""
        result = []
        for msg in messages:
            item: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.images:
                item["images"] = [img.to_base64() for img in msg.images]
            result.append(item)
        return result

    def _build_tools_payload(self, tools: list) -> list[dict]:
        """Convert ToolSchema list to Ollama tool format."""
        result = []
        for t in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            })
        return result

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Non-streaming chat completion."""
        payload = self._build_payload(request, stream=False)
        start = time.monotonic()
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.monotonic() - start) * 1000
        return self._parse_response(data, request, latency_ms)

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        """Streaming chat completion — yields ModelStreamEvent chunks."""
        payload = self._build_payload(request, stream=True)
        async with self._client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if chunk.get("done"):
                    yield ModelStreamEvent(
                        event_type="done",
                        done=True,
                        input_tokens=chunk.get("prompt_eval_count", 0),
                        output_tokens=chunk.get("eval_count", 0),
                    )
                    return

                msg = chunk.get("message", {})
                delta = msg.get("content", "")
                tool_calls = msg.get("tool_calls")

                if tool_calls:
                    for tc in tool_calls:
                        yield ModelStreamEvent(
                            event_type="tool_call",
                            tool_call=tc,
                        )
                elif delta:
                    yield ModelStreamEvent(
                        event_type="delta",
                        delta=delta,
                    )

    # ---------------------------------------------------------------- #
    # Internal helpers                                                   #
    # ---------------------------------------------------------------- #

    def _build_payload(self, request: ModelRequest, stream: bool) -> dict:
        # Resolve runtime controls: request override → adapter default.
        num_ctx = request.num_ctx if request.num_ctx is not None else self._default_num_ctx
        num_gpu = request.num_gpu if request.num_gpu is not None else self._default_num_gpu
        keep_alive = (
            request.keep_alive if request.keep_alive is not None else self._default_keep_alive
        )

        options: dict[str, Any] = {
            "temperature": request.temperature,
            # Bounded context keeps the model GPU-resident and load time low.
            "num_ctx": num_ctx,
        }
        # num_gpu controls layer offload. Emit it explicitly so Ollama does not
        # fall back to its conservative auto-estimate (measured ~3.8x slower).
        if num_gpu is not None:
            options["num_gpu"] = num_gpu
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        payload: dict[str, Any] = {
            "model": request.model_id,
            "messages": self._build_ollama_messages(request.messages),
            "stream": stream,
            "options": options,
            # Keep the model warm between workflow steps to avoid cold reloads.
            "keep_alive": keep_alive,
        }

        # Tool calling
        if request.tools:
            payload["tools"] = self._build_tools_payload(request.tools)

        # Thinking mode (Gemma 4 supports this)
        if request.thinking:
            payload["think"] = True

        # JSON format
        if request.output_schema is not None:
            payload["format"] = "json"

        return payload

    def _parse_response(
        self, data: dict, request: ModelRequest, latency_ms: float
    ) -> ModelResponse:
        msg = data.get("message", {})
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        thinking = msg.get("thinking", None)

        # Attempt JSON parse if structured output was requested
        parsed: Optional[dict] = None
        if request.output_schema is not None and content:
            import re
            clean_content = content.strip()
            match = re.search(r'(\{.*\}|\[.*\])', clean_content, re.DOTALL)
            if match:
                clean_content = match.group(1)

            try:
                parsed = json.loads(clean_content)
            except json.JSONDecodeError:
                # Caller handles repair
                pass

        return ModelResponse(
            model_id=request.model_id,
            content=content,
            parsed_output=parsed,
            tool_calls=tool_calls or [],
            thinking_content=thinking,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=latency_ms,
            finish_reason=data.get("done_reason", "stop"),
        )

    async def close(self) -> None:
        await self._client.aclose()
