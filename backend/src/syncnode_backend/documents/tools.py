"""
SyncNode — Document tools.

Implements:
  document.create_docx
  document.inspect_docx
  document.read_docx
  filesystem.write
  filesystem.find
  filesystem.hash
  writer.generate_paragraph

All paths are canonicalized and workspace-sandboxed before any operation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _get_workspace_root() -> Path:
    from syncnode_backend.config.settings import settings
    return settings.syncnode_workspace_root.resolve()


def _safe_path(raw_path: str, workspace_root: Optional[Path] = None) -> Path:
    """
    Canonicalize and validate a path is inside the workspace root.

    Raises WorkspacePathError for traversal attempts.
    """
    root = workspace_root or _get_workspace_root()
    p = Path(raw_path)
    if p.is_absolute():
        resolved = p.resolve()
    else:
        resolved = (root / p).resolve()
        
    try:
        resolved.relative_to(root)
    except ValueError:
        from syncnode_backend.errors.exceptions import WorkspacePathError
        raise WorkspacePathError(
            f"Path {resolved!r} is outside workspace root {root!r}. "
            "Model-generated paths outside the workspace are not allowed."
        )
    return resolved


def _sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ #
# Filesystem tools                                                      #
# ------------------------------------------------------------------ #


async def tool_filesystem_find(
    pattern: str,
    workspace: Optional[str] = None,
) -> dict[str, Any]:
    """Find files matching a glob pattern inside the workspace."""
    root = _safe_path(workspace, _get_workspace_root()) if workspace else _get_workspace_root()
    if not root.exists():
        return {"found": [], "count": 0}
    found = [str(p) for p in root.rglob(pattern) if p.is_file()]
    return {"found": found, "count": len(found)}


async def tool_filesystem_hash(path: str) -> dict[str, Any]:
    """Return SHA-256 hash of a file."""
    p = _safe_path(path)
    if not p.exists():
        return {"error": f"File not found: {path}", "exists": False}
    digest = _sha256_file(p)
    return {
        "path": str(p),
        "sha256": digest,
        "size_bytes": p.stat().st_size,
        "exists": True,
    }


async def tool_filesystem_write(
    path: str,
    content: str,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Write text content to a file inside the workspace."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    digest = _sha256_file(p)
    return {
        "path": str(p),
        "sha256": digest,
        "size_bytes": p.stat().st_size,
        "written": True,
    }


# ------------------------------------------------------------------ #
# Document tools                                                        #
# ------------------------------------------------------------------ #

async def _generate_paragraph_via_model(topic: str) -> str:
    """Generate an original paragraph for `topic` using the local model gateway.

    The writer agent's job is to actually write, so when no content is supplied
    we ask the local model. Uses the FAST_SIMPLE inference profile. Local-only.
    """
    from syncnode_backend.config.settings import settings
    from syncnode_ai.gateway.gateway import ModelGateway
    from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
    from syncnode_ai.gateway.schemas import Message, ModelRequest
    from syncnode_ai.routing import TaskClass, profile_registry

    adapter = OllamaAdapter(
        base_url=settings.ollama_base_url,
        timeout=float(settings.syncnode_model_timeout),
        default_num_ctx=settings.syncnode_num_ctx,
        default_num_gpu=settings.syncnode_gpu_layers,
        default_keep_alive=settings.syncnode_keep_alive,
    )
    gateway = ModelGateway(adapter=adapter, model_id=settings.syncnode_model_id)
    from syncnode_backend.runtime.scheduler import scheduler
    try:
        profile = profile_registry.get(TaskClass.FAST_SIMPLE)
        request = ModelRequest(
            model_id=gateway.model_id,
            messages=[
                Message(
                    role="system",
                    content=(
                        "You are the SyncNode Writer Agent. Write a single, original, "
                        "professional paragraph. Return only the paragraph text — no "
                        "preamble, no markdown, no headings."
                    ),
                ),
                Message(role="user", content=f"Write a short paragraph about: {topic}"),
            ],
            caller="writer.generate_paragraph",
        ).model_copy(update=profile.request_overrides())
        async with scheduler.model_slot("writer"):
            response = await gateway.generate(request)
        return (response.content or "").strip()
    finally:
        await gateway.close()


async def tool_writer_generate_paragraph(topic: str = "", content: str = "") -> dict[str, Any]:
    """
    Writer tool. If `content` is supplied it is used verbatim; otherwise the
    writer generates an original paragraph for `topic` via the local model.

    The result is persisted to a scratch file in the workspace so the
    verification engine can confirm real, non-empty content on disk (rather than
    trusting a model claim).
    """
    text = (content or "").strip()
    if not text and topic.strip():
        text = await _generate_paragraph_via_model(topic.strip())
        logger.info(f"Writer generated paragraph for topic={topic[:40]!r} chars={len(text)}")
    else:
        logger.info(f"Writer using supplied content chars={len(text)}")

    # Persist for real verification.
    safe_target = _safe_path("generated_paragraph.txt")
    safe_target.parent.mkdir(parents=True, exist_ok=True)
    safe_target.write_text(text, encoding="utf-8")

    return {
        "content": text,
        "topic": topic,
        "path": "generated_paragraph.txt",
        "written": True,
    }



async def tool_document_create_docx(
    path: str,
    content: str = "",
    title: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a DOCX file with the given content.

    If `content` is empty, the document agent generates a paragraph via the local
    model (topic derived from the title or filename), so a plan that omits an
    explicit writer step still produces a real, non-empty document.

    Args:
        path: Target file path (must be inside workspace).
        content: Text content to write as a paragraph (auto-generated if empty).
        title: Optional document title (added as heading).

    Returns:
        path, sha256, size_bytes, paragraph_count
    """
    from docx import Document as DocxDocument
    from docx.shared import Pt

    text = (content or "").strip()
    if not text:
        topic = (title or Path(path).stem.replace("_", " ")).strip() or "the SyncNode workbench"
        text = await _generate_paragraph_via_model(topic)
        logger.info("create_docx auto-generated content chars=%d topic=%r", len(text), topic)

    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    doc = DocxDocument()

    if title:
        heading = doc.add_heading(title, level=1)
        heading.runs[0].font.size = Pt(16)

    # Add the paragraph content
    paragraph = doc.add_paragraph(text)

    doc.save(str(p))

    digest = _sha256_file(p)
    size = p.stat().st_size

    logger.info(f"DOCX created — path={str(p)} sha256={digest[:8]}")
    return {
        "path": str(p),
        "sha256": digest,
        "size_bytes": size,
        "paragraph_count": len(doc.paragraphs),
        "title": title,
        "created": True,
    }


async def tool_document_inspect_docx(path: str) -> dict[str, Any]:
    """
    Inspect a DOCX file and return structural metadata.

    Does NOT trust the file was created by SyncNode.
    Reads and verifies the actual DOCX structure.
    """
    from docx import Document as DocxDocument

    p = _safe_path(path)
    if not p.exists():
        return {"exists": False, "path": str(p), "error": "File not found"}

    doc = DocxDocument(str(p))

    paragraphs = []
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            paragraphs.append({
                "index": i,
                "style": para.style.name if para.style else None,
                "text": para.text[:200],  # Truncate for safety
                "word_count": len(para.text.split()),
            })

    digest = _sha256_file(p)
    size = p.stat().st_size

    return {
        "exists": True,
        "path": str(p),
        "sha256": digest,
        "size_bytes": size,
        "paragraph_count": len(paragraphs),
        "total_paragraphs": len(doc.paragraphs),
        "paragraphs": paragraphs,
        "section_count": len(doc.sections),
        "has_content": len(paragraphs) > 0,
    }


async def tool_document_read_docx(path: str) -> dict[str, Any]:
    """Read the full text content of a DOCX file."""
    from docx import Document as DocxDocument

    p = _safe_path(path)
    if not p.exists():
        return {"exists": False, "text": ""}

    doc = DocxDocument(str(p))
    full_text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    return {
        "exists": True,
        "path": str(p),
        "text": full_text,
        "word_count": len(full_text.split()),
    }


def register_document_tools(registry) -> None:
    """Register all document and filesystem tools in the given registry."""
    from syncnode_backend.tools.registry import ToolDefinition

    tools = [
        ToolDefinition(
            key="filesystem.find",
            name="Filesystem Find",
            version=1,
            description="Find files matching a pattern in the workspace",
            input_schema={"pattern": "str", "workspace": "Optional[str]"},
            output_schema={"found": "list[str]", "count": "int"},
            capabilities=["filesystem"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_filesystem_find,
        ),
        ToolDefinition(
            key="filesystem.hash",
            name="Filesystem Hash",
            version=1,
            description="SHA-256 hash a file",
            input_schema={"path": "str"},
            output_schema={"sha256": "str", "exists": "bool"},
            capabilities=["filesystem"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_filesystem_hash,
        ),
        ToolDefinition(
            key="filesystem.write",
            name="Filesystem Write",
            version=1,
            description="Write text content to a workspace file",
            input_schema={"path": "str", "content": "str"},
            output_schema={"path": "str", "sha256": "str"},
            capabilities=["filesystem"],
            risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL",
            idempotency="idempotent",
            verification_strategy="always",
            handler=tool_filesystem_write,
        ),
        ToolDefinition(
            key="document.create_docx",
            name="Create DOCX",
            version=1,
            description="Create a DOCX document with text content",
            input_schema={"path": "str", "content": "str", "title": "Optional[str]"},
            output_schema={"path": "str", "sha256": "str", "paragraph_count": "int"},
            capabilities=["document_creation"],
            risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL",
            idempotency="idempotent",
            verification_strategy="always",
            handler=tool_document_create_docx,
            arg_aliases={
                # Common model synonyms for the target path.
                "filename": "path",
                "file_name": "path",
                "file": "path",
                "document_name": "path",
                "output_path": "path",
                # Contextual hints the handler does not take (paths are already
                # workspace-relative and sandboxed by _safe_path).
                "workspace": "",
                "directory": "",
                "text": "content",
                "body": "content",
                "heading": "title",
            },
        ),
        ToolDefinition(
            key="document.inspect_docx",
            name="Inspect DOCX",
            version=1,
            description="Inspect DOCX structure and content",
            input_schema={"path": "str"},
            output_schema={"exists": "bool", "paragraph_count": "int", "paragraphs": "list"},
            capabilities=["document_inspection"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_document_inspect_docx,
            arg_aliases={"filename": "path", "file_name": "path", "file": "path",
                         "document_name": "path", "workspace": "", "directory": ""},
        ),
        ToolDefinition(
            key="document.read_docx",
            name="Read DOCX",
            version=1,
            description="Read full text from a DOCX file",
            input_schema={"path": "str"},
            output_schema={"text": "str", "word_count": "int"},
            capabilities=["document_inspection"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_document_read_docx,
            arg_aliases={"filename": "path", "file_name": "path", "file": "path",
                         "document_name": "path", "workspace": "", "directory": ""},
        ),
        ToolDefinition(
            key="writer.generate_paragraph",
            name="Generate Paragraph",
            version=1,
            description="Generate a paragraph of text",
            input_schema={"topic": "str", "content": "str"},
            output_schema={"content": "str", "generated": "bool"},
            capabilities=["paragraph_writing"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_writer_generate_paragraph,
            arg_aliases={"subject": "topic", "prompt": "topic", "text": "content",
                         "body": "content", "paragraph": "content"},
            drop_decorative_args=True,
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Document and filesystem tools registered — count={len(tools)}")