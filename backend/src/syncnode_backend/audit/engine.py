"""
SyncNode — Audit Engine.

Tamper-evident audit chain using SHA-256 hash chaining.

Every audit event is linked to the previous via chain_hash:
  chain_hash = SHA256(prev_chain_hash || canonical_payload)

Verification:
  Walk the chain: any mutation breaks the chain.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Required audit event types
AUDIT_EVENT_TYPES = {
    "run.created",
    "intent.completed",
    "rag.query",
    "rag.retrieval.completed",
    "plan.created",
    "plan.validated",
    "plan.wave_dispatched",
    "policy.preflight",
    "tool.authorized",
    "agent.spawned",
    "tool.invoked",
    "tool.completed",
    "observation.captured",
    "verification.started",
    "verification.passed",
    "verification.failed",
    "recovery.triggered",
    "approval.requested",
    "approval.decided",
    "security.boundary_hit",
    "run.completed",
    "run.failed",
    "run.waiting_approval",
    "run.cancelled",
    "workflow.memory_recorded",
    "tool.started",
    "tool.completed",
}


def _canonical_json(payload: dict) -> bytes:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _chain_hash(prev_chain_hash: str, payload_hash: str) -> str:
    combined = (prev_chain_hash + payload_hash).encode()
    return hashlib.sha256(combined).hexdigest()


class AuditEngine:
    """
    Persists tamper-evident audit events.

    In-memory sequence tracking for single-run; persisted via DB session.
    """

    def __init__(self) -> None:
        self._sequence: int = 0
        self._last_chain_hash: str = "0" * 64  # Genesis hash

    async def record(
        self,
        event_type: str,
        payload: dict[str, Any],
        run_id: Optional[str] = None,
        step_id: Optional[str] = None,
        db_session=None,
    ) -> dict[str, Any]:
        """
        Record an audit event.

        Args:
            event_type: One of AUDIT_EVENT_TYPES.
            payload: Event data (must be JSON-serializable).
            run_id: Optional run correlation ID.
            step_id: Optional step correlation ID.
            db_session: Optional DB session for persistence.

        Returns:
            The audit record dict.
        """
        if event_type not in AUDIT_EVENT_TYPES:
            logger.warning(f"Non-standard audit event type — event_type={event_type}")

        self._sequence += 1
        seq = self._sequence

        # Enrich payload with metadata
        full_payload = {
            "event_type": event_type,
            "run_id": run_id,
            "step_id": step_id,
            "sequence": seq,
            "occurred_at": time.time(),
            **payload,
        }

        payload_hash = _hash_payload(full_payload)
        ch = _chain_hash(self._last_chain_hash, payload_hash)
        self._last_chain_hash = ch

        record = {
            "event_type": event_type,
            "payload": full_payload,
            "payload_hash": payload_hash,
            "chain_hash": ch,
            "sequence": seq,
            "run_id": run_id,
            "step_id": step_id,
        }

        logger.debug(f"Audit event recorded — event_type={event_type} seq={seq} chain={ch[:8]}")

        # Persist to the database. Use the caller's session when provided,
        # otherwise open our own — audit events MUST be durable (a run's
        # tamper-evident chain is worthless if it is never written).
        await self._persist(
            event_type, full_payload, payload_hash, ch, seq, run_id, step_id, db_session
        )

        return record

    @staticmethod
    async def _persist(
        event_type: str,
        full_payload: dict,
        payload_hash: str,
        chain_hash: str,
        seq: int,
        run_id: Optional[str],
        step_id: Optional[str],
        db_session,
    ) -> None:
        from syncnode_backend.persistence.models import AuditEvent

        def _make() -> "AuditEvent":
            return AuditEvent(
                run_id=run_id,
                step_id=step_id,
                event_type=event_type,
                payload=full_payload,
                payload_hash=payload_hash,
                chain_hash=chain_hash,
                sequence=seq,
            )

        try:
            if db_session is not None:
                db_session.add(_make())
                await db_session.flush()
            else:
                from syncnode_backend.persistence.database import get_session
                async with get_session() as session:
                    session.add(_make())
        except Exception as exc:  # noqa: BLE001 - audit persistence best-effort
            logger.error(f"Failed to persist audit event — error={str(exc)}")

    @staticmethod
    def verify_chain(events: list[dict]) -> dict[str, Any]:
        """
        Verify the integrity of an audit chain.

        Args:
            events: List of audit event records (ordered by sequence).

        Returns:
            {"valid": bool, "broken_at_sequence": Optional[int], "checked": int}
        """
        prev_chain = "0" * 64
        for event in sorted(events, key=lambda e: e["sequence"]):
            expected_payload_hash = _hash_payload(event["payload"])
            if expected_payload_hash != event["payload_hash"]:
                return {
                    "valid": False,
                    "broken_at_sequence": event["sequence"],
                    "reason": "payload_hash_mismatch",
                    "checked": event["sequence"],
                }
            expected_chain = _chain_hash(prev_chain, event["payload_hash"])
            if expected_chain != event["chain_hash"]:
                return {
                    "valid": False,
                    "broken_at_sequence": event["sequence"],
                    "reason": "chain_hash_mismatch",
                    "checked": event["sequence"],
                }
            prev_chain = event["chain_hash"]

        return {"valid": True, "broken_at_sequence": None, "checked": len(events)}


# Module-level singleton
audit_engine = AuditEngine()