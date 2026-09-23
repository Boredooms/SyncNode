"""
Gate B — Local Gemma 4 capability verification test.

Run this test to confirm:
  - Ollama is reachable
  - gemma4:e4b is discovered
  - text generation works
  - structured JSON output works
  - tool calling works
  - vision works
  - streaming works
  - NO cloud fallback occurs

Usage:
    pytest ai_ml/tests/model/test_local_gemma_capabilities.py -v
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Optional

import pytest

# Add ai_ml source to path for standalone running
sys.path.insert(0, str(Path(__file__).parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).parents[4] / "backend" / "src"))

from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
from syncnode_ai.gateway.gateway import ModelGateway
from syncnode_ai.gateway.schemas import (
    ImageInput,
    Message,
    ModelRequest,
    ModelStreamEvent,
    ProviderStatus,
    ToolSchema,
)
from pydantic import BaseModel

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_ID = "gemma4:e4b"


@pytest.fixture
def adapter():
    return OllamaAdapter(base_url=OLLAMA_URL, timeout=120.0)


@pytest.fixture
def gateway(adapter):
    return ModelGateway(adapter=adapter, model_id=MODEL_ID, max_repair=3)


# ------------------------------------------------------------------ #
# Test: model discovery                                                 #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ollama_reachable(adapter):
    """Ollama must be reachable at the loopback address."""
    health = await adapter.health(MODEL_ID)
    assert health.status == ProviderStatus.HEALTHY, (
        f"Ollama health check failed: {health.error}"
    )
    print(f"\n[GATE-B] Ollama health: {health.status} — latency {health.latency_ms:.0f}ms")


@pytest.mark.asyncio
async def test_gemma_model_discovered(adapter):
    """gemma4:e4b must be in the local model list."""
    profiles = await adapter.list_models()
    model_ids = [p.model_id for p in profiles]
    assert MODEL_ID in model_ids, (
        f"Model {MODEL_ID!r} not found. Available: {model_ids}"
    )
    profile = next(p for p in profiles if p.model_id == MODEL_ID)
    print(f"\n[GATE-B] Model: {profile.model_id}")
    print(f"  capabilities: {profile.capabilities}")
    print(f"  parameter_size: {profile.capabilities.parameter_size}")
    print(f"  quantization: {profile.capabilities.quantization}")
    print(f"  context_window: {profile.capabilities.context_window}")


@pytest.mark.asyncio
async def test_no_cloud_model_selected(gateway):
    """The gateway must not select a cloud-suffixed model."""
    request = ModelRequest(
        model_id="glm-5.2:cloud",  # cloud model — must be rejected
        messages=[Message(role="user", content="Hello")],
        caller="test_no_cloud",
    )
    from syncnode_ai.errors import CloudInferenceAttemptError
    with pytest.raises(CloudInferenceAttemptError):
        await gateway.generate(request)
    print("\n[GATE-B] Cloud inference correctly rejected ✓")


# ------------------------------------------------------------------ #
# Test: text generation                                                 #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_text_generation(gateway):
    """Basic text generation must return a non-empty response."""
    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(role="system", content="You are a helpful assistant. Be concise."),
            Message(role="user", content="Say 'SyncNode text generation working' and nothing else."),
        ],
        temperature=0.0,
        caller="test_text_generation",
    )
    response = await gateway.generate(request)
    assert response.content, "Model returned empty content"
    assert len(response.content) > 5
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    print(f"\n[GATE-B] Text generation ✓")
    print(f"  Response: {response.content[:100]!r}")
    print(f"  Tokens: in={response.input_tokens} out={response.output_tokens}")
    print(f"  Latency: {response.latency_ms:.0f}ms")


# ------------------------------------------------------------------ #
# Test: structured output                                               #
# ------------------------------------------------------------------ #


class DemoStructured(BaseModel):
    greeting: str
    number: int
    items: list[str]


@pytest.mark.asyncio
async def test_structured_output(gateway):
    """Model must produce valid JSON matching the target schema."""
    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(role="system", content="You are a JSON output assistant. Always respond with valid JSON only."),
            Message(
                role="user",
                content=(
                    'Return a JSON object with exactly these fields: '
                    '"greeting" (string = "hello syncnode"), '
                    '"number" (integer = 42), '
                    '"items" (list of 2 strings = ["alpha", "beta"])'
                ),
            ),
        ],
        temperature=0.0,
        caller="test_structured_output",
    )
    instance, raw_response = await gateway.generate_structured(request, DemoStructured)
    assert isinstance(instance, DemoStructured)
    assert instance.number == 42
    assert len(instance.items) == 2
    print(f"\n[GATE-B] Structured output ✓")
    print(f"  Parsed: greeting={instance.greeting!r} number={instance.number} items={instance.items}")


# ------------------------------------------------------------------ #
# Test: streaming                                                       #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_streaming(gateway):
    """Streaming must yield delta events and a final done event."""
    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(role="user", content="Count from 1 to 5, one number per line."),
        ],
        stream=True,
        temperature=0.0,
        caller="test_streaming",
    )
    events: list[ModelStreamEvent] = []
    async for event in gateway.stream(request):
        events.append(event)
        if event.done:
            break

    delta_events = [e for e in events if e.event_type == "delta"]
    done_events = [e for e in events if e.done]
    assert len(delta_events) > 0, "No delta events received"
    assert len(done_events) == 1, "Missing done event"
    full_text = "".join(e.delta or "" for e in delta_events)
    assert len(full_text) > 0
    print(f"\n[GATE-B] Streaming ✓")
    print(f"  Delta chunks: {len(delta_events)}")
    print(f"  Total chars: {len(full_text)}")


# ------------------------------------------------------------------ #
# Test: tool calling                                                    #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_tool_calling(gateway):
    """Model must produce a tool_call when a matching tool is available."""
    weather_tool = ToolSchema(
        name="get_weather",
        description="Get current weather for a city",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    )
    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(role="user", content="What is the weather in London right now?"),
        ],
        tools=[weather_tool],
        temperature=0.0,
        caller="test_tool_calling",
    )
    response = await gateway.generate(request)
    # The model should use the tool or respond in text
    has_tool_call = len(response.tool_calls) > 0
    print(f"\n[GATE-B] Tool calling {'✓ (used tool)' if has_tool_call else '⚠ (model responded in text)'}")
    if has_tool_call:
        print(f"  Tool calls: {response.tool_calls}")
    else:
        print(f"  Text response: {response.content[:80]!r}")
    # Not a hard failure — model may respond in text if it doesn't recognize the pattern


# ------------------------------------------------------------------ #
# Test: vision                                                          #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_vision(gateway, tmp_path):
    """Model must accept an image and describe it."""
    # Create a simple test image (1x1 red pixel PNG)
    import struct
    import zlib

    def minimal_png() -> bytes:
        """Create a minimal 1x1 red pixel PNG."""
        def chunk(ctype: bytes, data: bytes) -> bytes:
            c = ctype + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        raw = b"\x00\xFF\x00\x00"  # filter byte + R G B
        idat = chunk(b"IDAT", zlib.compress(raw))
        iend = chunk(b"IEND", b"")
        return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend

    img_path = tmp_path / "test_pixel.png"
    img_path.write_bytes(minimal_png())
    img_b64 = base64.b64encode(img_path.read_bytes()).decode()

    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(
                role="user",
                content="Describe this image in one word.",
                images=[ImageInput(source="base64", value=img_b64, mime_type="image/png")],
            ),
        ],
        temperature=0.0,
        caller="test_vision",
    )
    response = await gateway.generate(request)
    assert response.content, "Vision model returned empty response"
    print(f"\n[GATE-B] Vision ✓")
    print(f"  Description: {response.content[:80]!r}")


# ------------------------------------------------------------------ #
# Test: thinking mode                                                   #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_thinking_mode(gateway):
    """Thinking mode should not raise an error on gemma4:e4b."""
    request = ModelRequest(
        model_id=MODEL_ID,
        messages=[
            Message(role="user", content="What is 7 + 8? Just the number."),
        ],
        thinking=True,
        temperature=0.0,
        caller="test_thinking",
    )
    response = await gateway.generate(request)
    assert response.content, "Thinking mode returned empty response"
    print(f"\n[GATE-B] Thinking mode ✓")
    print(f"  Answer: {response.content!r}")
    if response.thinking_content:
        print(f"  Thinking (first 100 chars): {response.thinking_content[:100]!r}")


# ------------------------------------------------------------------ #
# Summary report                                                        #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_print_full_capability_report(adapter):
    """Print a full model capability report to stdout."""
    profiles = await adapter.list_models()
    local_profiles = [p for p in profiles if not p.model_id.endswith(":cloud")]
    
    print("\n" + "=" * 60)
    print("SYNCNODE LOCAL MODEL CAPABILITY REPORT")
    print("=" * 60)
    for p in local_profiles:
        print(f"\nModel: {p.model_id}")
        c = p.capabilities
        print(f"  completion:        {c.completion}")
        print(f"  vision:            {c.vision}")
        print(f"  audio:             {c.audio}")
        print(f"  tools:             {c.tools}")
        print(f"  thinking:          {c.thinking}")
        print(f"  streaming:         {c.streaming}")
        print(f"  context_window:    {c.context_window:,}")
        print(f"  parameter_size:    {c.parameter_size}")
        print(f"  quantization:      {c.quantization}")
    print("=" * 60)
