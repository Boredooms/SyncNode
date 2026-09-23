"""
SyncNode — Local Markdown Knowledge Base.

Knowledge is a set of local, editable Markdown files under ``knowledge/`` with
YAML front matter. The backend parses, versions (by content hash), and serves
them. These files later power the Electron Markdown editor; for now they are a
backend-only, RAG-feeding, provenance-tracked knowledge source.

SAFETY TIERS (critical). Knowledge files are DATA, not a control plane. A file's
``trust`` metadata classifies it:

    authoritative_policy  — may express approval/security policy (only files
                            under knowledge/policies/ can claim this)
    reference             — factual reference (applications, tools)
    workflow              — how-to workflow guidance
    untrusted             — external/imported content; never influences policy

Retrieval NEVER lets a ``reference``/``workflow``/``untrusted`` document mutate
policy: policy is read only from ``authoritative_policy`` files in the policy
directory. Content that tries to say "ignore approvals" from a non-policy file is
treated as untrusted data and cannot change control flow.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TrustTier(str, Enum):
    AUTHORITATIVE_POLICY = "authoritative_policy"
    REFERENCE = "reference"
    WORKFLOW = "workflow"
    UNTRUSTED = "untrusted"


# Which directory a doc must live in to be allowed to claim a tier.
_POLICY_DIR = "policies"


@dataclass
class KnowledgeDoc:
    id: str
    type: str                 # application | workflow | policy | tool | organization | rule
    path: str                 # relative to knowledge root
    title: str
    trust: TrustTier
    version: int
    status: str               # active | draft | deprecated
    tags: list[str]
    body: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "path": self.path, "title": self.title,
            "trust": self.trust.value, "version": self.version, "status": self.status,
            "tags": self.tags, "content_hash": self.content_hash,
        }


_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Minimal YAML-front-matter parser (no external yaml dependency needed).

    Supports scalars and simple ``- item`` lists. Anything more complex is
    ignored rather than misparsed.
    """
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    meta: dict[str, Any] = {}
    current_list_key: Optional[str] = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*-\s+", line) and current_list_key:
            meta[current_list_key].append(line.strip()[1:].strip())
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                meta[key] = []
                current_list_key = key
            else:
                meta[key] = _coerce(val)
                current_list_key = None
    return meta, body


def _coerce(val: str) -> Any:
    v = val.strip().strip('"').strip("'")
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if v.isdigit():
        return int(v)
    return v


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class KnowledgeService:
    """Loads and serves local Markdown knowledge with safety-tier enforcement."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._docs: dict[str, KnowledgeDoc] = {}

    @property
    def root(self) -> Path:
        return self._root

    # ---------------------------------------------------------------- #
    # Loading                                                            #
    # ---------------------------------------------------------------- #

    def load_all(self) -> int:
        """(Re)load all *.md files under the knowledge root."""
        self._docs.clear()
        if not self._root.exists():
            logger.warning("Knowledge root does not exist: %s", self._root)
            return 0
        for md in sorted(self._root.rglob("*.md")):
            try:
                doc = self._load_file(md)
                if doc.id in self._docs:
                    logger.warning("Duplicate knowledge id %r (%s)", doc.id, md)
                self._docs[doc.id] = doc
            except Exception as exc:  # noqa: BLE001 - skip unparsable files
                logger.error("Failed to load knowledge file %s: %s", md, exc)
        logger.info("Knowledge loaded — %d documents", len(self._docs))
        return len(self._docs)

    def _load_file(self, md: Path) -> KnowledgeDoc:
        text = md.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(text)
        rel = md.relative_to(self._root).as_posix()
        doc_id = str(meta.get("id") or md.stem)
        claimed_trust = str(meta.get("trust", "")).strip().lower()
        trust = self._resolve_trust(claimed_trust, rel)
        return KnowledgeDoc(
            id=doc_id,
            type=str(meta.get("type", "reference")),
            path=rel,
            title=str(meta.get("title", doc_id)),
            trust=trust,
            version=int(meta.get("version", 1)),
            status=str(meta.get("status", "active")),
            tags=list(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else [],
            body=body.strip(),
            content_hash=_content_hash(text),
            metadata=meta,
        )

    @staticmethod
    def _resolve_trust(claimed: str, rel_path: str) -> TrustTier:
        """Enforce safety tiers: only files under policies/ may be authoritative.

        A non-policy file claiming ``authoritative_policy`` is downgraded to
        ``reference`` (it cannot become a control-plane instruction).
        """
        in_policy_dir = rel_path.split("/", 1)[0] == _POLICY_DIR
        if claimed == TrustTier.AUTHORITATIVE_POLICY.value:
            if in_policy_dir:
                return TrustTier.AUTHORITATIVE_POLICY
            logger.warning(
                "Downgrading %s: claims authoritative_policy but is not under %s/",
                rel_path, _POLICY_DIR,
            )
            return TrustTier.REFERENCE
        for t in TrustTier:
            if claimed == t.value:
                return t
        # Default: policy dir => authoritative, else reference.
        return TrustTier.AUTHORITATIVE_POLICY if in_policy_dir else TrustTier.REFERENCE

    # ---------------------------------------------------------------- #
    # Query                                                              #
    # ---------------------------------------------------------------- #

    def all(self) -> list[KnowledgeDoc]:
        return list(self._docs.values())

    def get(self, doc_id: str) -> Optional[KnowledgeDoc]:
        return self._docs.get(doc_id)

    def by_type(self, doc_type: str) -> list[KnowledgeDoc]:
        return [d for d in self._docs.values() if d.type == doc_type]

    def authoritative_policies(self) -> list[KnowledgeDoc]:
        return [d for d in self._docs.values()
                if d.trust == TrustTier.AUTHORITATIVE_POLICY and d.status == "active"]

    def search(self, query: str, *, tags: Optional[list[str]] = None,
               limit: int = 5) -> list[tuple[KnowledgeDoc, float]]:
        """Lightweight lexical relevance search (no embeddings dependency).

        Scores by tag match + term overlap in title/body/tags. Good enough for
        conditional RAG in the golden workflow; can be swapped for ChromaDB
        embeddings without changing the interface.
        """
        terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        wanted_tags = set(t.lower() for t in (tags or []))
        scored: list[tuple[KnowledgeDoc, float]] = []
        for d in self._docs.values():
            if d.status != "active":
                continue
            hay = (d.title + " " + " ".join(d.tags) + " " + d.body).lower()
            score = 0.0
            for term in terms:
                score += hay.count(term) * 1.0
                if term in d.tags:
                    score += 3.0
            if wanted_tags & set(x.lower() for x in d.tags):
                score += 5.0
            if score > 0:
                scored.append((d, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    # ---------------------------------------------------------------- #
    # Mutation (backend API; later the Electron editor)                  #
    # ---------------------------------------------------------------- #

    def write(self, rel_path: str, text: str) -> KnowledgeDoc:
        """Create or update a knowledge file. Path is jailed to the knowledge root."""
        from syncnode_backend.errors.exceptions import KnowledgeError
        target = (self._root / rel_path).resolve()
        try:
            target.relative_to(self._root.resolve())
        except ValueError:
            raise KnowledgeError(f"Knowledge path escapes root: {rel_path!r}")
        if target.suffix != ".md":
            raise KnowledgeError("Knowledge files must be .md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        doc = self._load_file(target)
        self._docs[doc.id] = doc
        return doc

    def delete(self, doc_id: str) -> bool:
        doc = self._docs.get(doc_id)
        if not doc:
            return False
        (self._root / doc.path).unlink(missing_ok=True)
        del self._docs[doc_id]
        return True
