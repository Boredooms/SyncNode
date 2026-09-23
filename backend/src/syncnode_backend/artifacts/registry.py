"""
SyncNode — Run-scoped Artifact Registry.

Every run gets an isolated workspace: workspace/runs/<run_id>/{word,excel,
powerpoint,email}. Artifacts produced during the run are registered with typed
metadata and referenced by a stable ``artifact://run/<run_id>/<artifact_id>``
reference — never by a raw model-generated path.

This guarantees:
  - no stale artifact reuse (a fresh run directory per run),
  - deterministic artifact identity (id + run_id + sha256 + producer step),
  - typed references flow between steps instead of literal strings.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_ARTIFACT_REF_RE = re.compile(r"^artifact://run/([^/]+)/(.+)$")


@dataclass
class ArtifactRecord:
    artifact_id: str
    run_id: str
    kind: str                 # word | excel | powerpoint | email | other
    path: str                 # absolute canonical path
    mime_type: str
    producer_step: str
    created_at: float
    sha256: Optional[str] = None
    verified: bool = False
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ref(self) -> str:
        return f"artifact://run/{self.run_id}/{self.artifact_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id, "run_id": self.run_id, "kind": self.kind,
            "ref": self.ref, "path": self.path, "mime_type": self.mime_type,
            "producer_step": self.producer_step, "created_at": self.created_at,
            "sha256": self.sha256, "verified": self.verified, "status": self.status,
        }


_MIME = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".png": "image/png",
}


def _sha256(p: Path) -> Optional[str]:
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class RunArtifactRegistry:
    """Per-run artifact namespace + typed registry."""

    def __init__(self, run_id: str, runs_root: Path) -> None:
        self.run_id = run_id
        self.run_dir = (runs_root / "runs" / run_id).resolve()
        self._artifacts: dict[str, ArtifactRecord] = {}
        self._started_at = time.time()

    # ---- clean-run setup ----

    def initialize(self) -> None:
        """Create the run-scoped workspace and assert it is clean."""
        for sub in ("word", "excel", "powerpoint", "email"):
            (self.run_dir / sub).mkdir(parents=True, exist_ok=True)
        # Assert no pre-existing generated office artifacts (fresh run).
        existing = [
            p for p in self.run_dir.rglob("*")
            if p.is_file() and p.suffix in (".docx", ".xlsx", ".pptx")
        ]
        if existing:
            from syncnode_backend.errors.exceptions import SyncNodeError
            raise SyncNodeError(
                f"Run directory {self.run_dir} is not clean: {existing}"
            )
        logger.info("Run workspace initialized (clean) — %s", self.run_dir)

    def subdir(self, kind: str) -> Path:
        d = self.run_dir / kind
        d.mkdir(parents=True, exist_ok=True)
        return d

    def new_path(self, kind: str, filename: str) -> Path:
        """A run-scoped path for a new artifact of a given kind."""
        return self.subdir(kind) / filename

    # ---- registration ----

    def register(self, *, kind: str, path: str, producer_step: str,
                 metadata: Optional[dict] = None) -> ArtifactRecord:
        p = Path(path).resolve()
        # Must live inside this run's directory (no stale/global paths).
        try:
            p.relative_to(self.run_dir)
        except ValueError:
            from syncnode_backend.errors.exceptions import SyncNodeError
            raise SyncNodeError(
                f"Artifact path {p} is outside run directory {self.run_dir}"
            )
        artifact_id = f"{kind}_{uuid.uuid4().hex[:8]}"
        rec = ArtifactRecord(
            artifact_id=artifact_id, run_id=self.run_id, kind=kind,
            path=str(p), mime_type=_MIME.get(p.suffix, "application/octet-stream"),
            producer_step=producer_step, created_at=time.time(),
            sha256=_sha256(p), metadata=metadata or {},
        )
        # Reject a file that predates this run (stale artifact protection).
        if rec.created_at and p.exists():
            mtime = p.stat().st_mtime
            if mtime < self._started_at - 5:
                from syncnode_backend.errors.exceptions import SyncNodeError
                raise SyncNodeError(
                    f"Artifact {p} was not created during this run (stale)."
                )
        self._artifacts[artifact_id] = rec
        logger.info("Artifact registered — %s kind=%s sha=%s",
                    rec.ref, kind, (rec.sha256 or "")[:8])
        return rec

    def mark_verified(self, artifact_id: str, verified: bool = True) -> None:
        if artifact_id in self._artifacts:
            self._artifacts[artifact_id].verified = verified
            self._artifacts[artifact_id].status = "verified" if verified else "unverified"

    # ---- lookup / resolution ----

    def get(self, artifact_id: str) -> Optional[ArtifactRecord]:
        return self._artifacts.get(artifact_id)

    def by_kind(self, kind: str) -> list[ArtifactRecord]:
        return [a for a in self._artifacts.values() if a.kind == kind]

    def latest(self, kind: str) -> Optional[ArtifactRecord]:
        items = sorted(self.by_kind(kind), key=lambda a: a.created_at)
        return items[-1] if items else None

    def all(self) -> list[ArtifactRecord]:
        return list(self._artifacts.values())

    def resolve_ref(self, ref: str) -> Optional[ArtifactRecord]:
        """Resolve an artifact:// reference to a record (this run only)."""
        m = _ARTIFACT_REF_RE.match(ref or "")
        if not m:
            return None
        run_id, artifact_id = m.group(1), m.group(2)
        if run_id != self.run_id:
            return None
        return self._artifacts.get(artifact_id)

    def resolve_path(self, value: str) -> Optional[str]:
        """If value is an artifact ref, return its canonical path; else None."""
        rec = self.resolve_ref(value)
        return rec.path if rec else None
