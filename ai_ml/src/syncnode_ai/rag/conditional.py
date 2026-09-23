"""
SyncNode — Conditional RAG.

RAG does not run on every call. This module decides *whether* a task needs
retrieved knowledge, and if so retrieves relevant local knowledge with
provenance (document id, path, trust tier, content hash, score).

Retrieval is backed by the backend KnowledgeService (local Markdown). The
pipeline is:

    goal / intent
      -> knowledge requirement detection (task classification)
      -> retrieve (lexical, provenance-tracked)
      -> assemble compact context

Design notes:
- The retriever is passed in (dependency injection) so ai_ml does not import
  backend internals directly; the orchestrator supplies the backend's
  KnowledgeService-backed retriever.
- Provenance is always recorded so a run can prove which knowledge it used.
- Retrieved reference/workflow knowledge is CONTEXT, never control: it cannot
  change policy (policy is read only from authoritative policy docs).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    trust: str
    path: str
    content_hash: str
    score: float
    text: str


@dataclass
class RagResult:
    required: bool
    reason: str
    query: str
    tags: list[str] = field(default_factory=list)
    chunks: list[RetrievedChunk] = field(default_factory=list)

    def provenance(self) -> list[dict[str, Any]]:
        return [
            {"doc_id": c.doc_id, "path": c.path, "trust": c.trust,
             "content_hash": c.content_hash, "score": round(c.score, 2)}
            for c in self.chunks
        ]

    def context_text(self, max_chars: int = 1500) -> str:
        """Assemble a compact, provenance-labeled knowledge context block."""
        if not self.chunks:
            return ""
        parts = ["Relevant local knowledge (reference only; policy is authoritative):"]
        budget = max_chars
        for c in self.chunks:
            snippet = c.text.strip()
            if len(snippet) > 400:
                snippet = snippet[:400] + "…"
            block = f"\n[{c.doc_id} · {c.trust}]\n{snippet}"
            if len(block) > budget:
                break
            parts.append(block)
            budget -= len(block)
        return "\n".join(parts)


# A retriever takes (query, tags, limit) and returns a list of dicts with keys:
# doc_id, title, trust, path, content_hash, score, text.
Retriever = Callable[[str, Optional[list[str]], int], list[dict[str, Any]]]


# Keyword → tag hints used both to detect the knowledge requirement and to bias
# retrieval toward the right knowledge area.
_TAG_HINTS: dict[str, list[str]] = {
    "email": ["email", "approval", "browser"],
    "draft": ["email", "approval"],
    "send": ["approval", "email"],
    "word": ["word", "document", "docx"],
    "document": ["document", "word", "docx"],
    "docx": ["document", "word", "docx"],
    "report": ["document", "word"],
    "excel": ["excel", "spreadsheet", "xlsx"],
    "spreadsheet": ["excel", "spreadsheet", "xlsx"],
    "workbook": ["excel", "spreadsheet", "xlsx"],
    "powerpoint": ["powerpoint", "presentation", "pptx"],
    "presentation": ["powerpoint", "presentation", "pptx"],
    "slide": ["powerpoint", "presentation", "pptx"],
    "save": ["workspace", "filesystem"],
    "workspace": ["workspace", "filesystem"],
    "approval": ["approval"],
    "attach": ["email", "approval"],
}

# Trivial tasks that do not need knowledge retrieval.
_TRIVIAL_RE = re.compile(
    r"^\s*(say|write one|write a single|echo|repeat|hello|hi)\b", re.IGNORECASE
)


def detect_knowledge_requirement(goal: str) -> tuple[bool, str, list[str]]:
    """Return (required, reason, tag_hints) for a goal string."""
    text = goal.lower()
    if _TRIVIAL_RE.match(goal) and len(goal) < 60:
        return False, "trivial task; no knowledge required", []

    tags: list[str] = []
    matched: list[str] = []
    for kw, kw_tags in _TAG_HINTS.items():
        if re.search(rf"\b{re.escape(kw)}\b", text):
            matched.append(kw)
            for t in kw_tags:
                if t not in tags:
                    tags.append(t)

    # Any application/document/external action requires knowledge.
    if tags:
        return True, f"task references: {', '.join(sorted(set(matched)))}", tags
    # Longer, non-trivial goals default to retrieving general policy.
    if len(goal) > 60:
        return True, "non-trivial task; retrieve general policy", ["workspace", "approval"]
    return False, "no knowledge signals detected", []


class ConditionalRAG:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    def retrieve_for_goal(self, goal: str, *, limit: int = 5) -> RagResult:
        required, reason, tags = detect_knowledge_requirement(goal)
        if not required:
            return RagResult(required=False, reason=reason, query=goal, tags=tags)
        raw = self._retriever(goal, tags, limit)
        chunks = [
            RetrievedChunk(
                doc_id=r["doc_id"], title=r.get("title", r["doc_id"]),
                trust=r.get("trust", "reference"), path=r.get("path", ""),
                content_hash=r.get("content_hash", ""), score=float(r.get("score", 0.0)),
                text=r.get("text", ""),
            )
            for r in raw
        ]
        return RagResult(required=True, reason=reason, query=goal, tags=tags, chunks=chunks)
