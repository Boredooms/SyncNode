"""
Tool Registry hardening + anti-hallucination tests (Phase B, Gate 49/50).

These are pure-unit tests — no model, no Ollama, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from syncnode_backend.errors.exceptions import (  # noqa: E402
    ToolError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolUnavailableError,
)
from syncnode_backend.tools.registry import ToolDefinition, ToolRegistry  # noqa: E402


async def _handler(path: str, content: str, title: str = "") -> dict:
    return {"path": path, "content": content, "title": title}


def _registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolDefinition(
        key="document.create_docx",
        name="Create DOCX",
        version=1,
        description="Create a docx",
        input_schema={"path": "str", "content": "str", "title": "str?"},
        output_schema={"path": "str"},
        capabilities=["document_creation"],
        risk_class="medium",
        side_effect_type="IDEMPOTENT_LOCAL",
        idempotency="idempotent",
        verification_strategy="always",
        handler=_handler,
        arg_aliases={"filename": "path", "workspace": "", "text": "content"},
        allowed_agents=["document"],
    ))
    return reg


ALLOWED = ["document.create_docx"]


def test_unknown_tool_rejected():
    reg = _registry()
    with pytest.raises(ToolNotFoundError):
        reg.validate_call("computer.open_file", {"path": "x"}, ALLOWED)


def test_unknown_argument_rejected():
    reg = _registry()
    with pytest.raises(ToolError):
        reg.validate_call("document.create_docx",
                          {"path": "a.docx", "content": "hi", "length": 5}, ALLOWED)


def test_known_alias_accepted():
    reg = _registry()
    norm = reg.validate_call("document.create_docx",
                             {"filename": "a.docx", "content": "hi"}, ALLOWED)
    assert norm["path"] == "a.docx"
    assert "filename" not in norm


def test_contextual_alias_dropped():
    reg = _registry()
    norm = reg.validate_call("document.create_docx",
                             {"path": "a.docx", "content": "hi", "workspace": "demo"}, ALLOWED)
    assert "workspace" not in norm


def test_undeclared_alias_still_rejected():
    reg = _registry()
    # "app_name" is not a declared alias for this tool -> fail closed.
    with pytest.raises(ToolError):
        reg.validate_call("document.create_docx",
                          {"path": "a.docx", "content": "hi", "app_name": "word"}, ALLOWED)


def test_missing_required_rejected():
    reg = _registry()
    with pytest.raises(ToolError):
        reg.validate_call("document.create_docx", {"path": "a.docx"}, ALLOWED)


def test_agent_without_permission_rejected():
    reg = _registry()
    with pytest.raises(ToolPermissionError):
        reg.validate_call("document.create_docx",
                          {"path": "a.docx", "content": "hi"}, agent_allowed_tools=[])


def test_alias_does_not_overwrite_canonical():
    reg = _registry()
    norm = reg.validate_call("document.create_docx",
                             {"path": "real.docx", "filename": "ghost.docx", "content": "hi"},
                             ALLOWED)
    assert norm["path"] == "real.docx"


@pytest.mark.asyncio
async def test_unavailable_tool_fails_closed():
    reg = _registry()

    async def _never() -> bool:
        return False

    reg.get("document.create_docx").availability_probe = _never
    with pytest.raises(ToolUnavailableError):
        await reg.check_available("document.create_docx")


def test_decorative_args_dropped_only_when_opted_in():
    reg = ToolRegistry()

    async def gen(topic: str, content: str = "") -> dict:
        return {"content": content, "topic": topic}

    reg.register(ToolDefinition(
        key="writer.generate_paragraph", name="Writer", version=1, description="gen",
        input_schema={"topic": "str"}, output_schema={"content": "str"},
        capabilities=["paragraph_writing"], risk_class="low",
        side_effect_type="READ_ONLY", idempotency="idempotent",
        verification_strategy="never", handler=gen,
        drop_decorative_args=True,
    ))
    # style/tone are decorative and dropped for this opted-in tool.
    norm = reg.validate_call("writer.generate_paragraph",
                             {"topic": "trees", "style": "formal", "tone": "warm"},
                             ["writer.generate_paragraph"])
    assert "style" not in norm and "tone" not in norm
    assert norm["topic"] == "trees"


def test_decorative_args_still_rejected_when_not_opted_in():
    reg = _registry()  # document.create_docx does NOT opt in
    # "length" is decorative but this tool is strict -> reject (fail closed).
    with pytest.raises(ToolError):
        reg.validate_call("document.create_docx",
                          {"path": "a.docx", "content": "hi", "length": 5}, ALLOWED)


def test_scoped_schemas_only_for_agent():
    reg = _registry()
    scoped = reg.schemas_for_agent(ALLOWED)
    assert len(scoped) == 1 and scoped[0]["tool"] == "document.create_docx"
    assert reg.schemas_for_agent([]) == []
