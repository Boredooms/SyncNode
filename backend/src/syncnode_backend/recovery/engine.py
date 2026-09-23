"""
SyncNode — Recovery Engine.

Deterministic, policy-aware, bounded recovery. Given a classified failure, it
decides the next recovery tier:

    RETRY          — transient; try again (bounded, with backoff)
    REOBSERVE      — stale/ambiguous observation; refresh then retry
    FALLBACK       — try an alternative tool/approach
    REPLAN         — the plan is wrong; ask the planner to revise
    ESCALATE       — hand to a human (approval/notification)
    ABORT          — unrecoverable / policy-denied

A circuit breaker stops repeated failures of the same (step, error_class) from
looping forever. Nothing here bypasses policy, verification, or the approval
boundary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorClass(str, Enum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_TOOL_ARGUMENTS = "INVALID_TOOL_ARGUMENTS"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_AMBIGUOUS = "TARGET_AMBIGUOUS"
    APP_NOT_RUNNING = "APP_NOT_RUNNING"
    APP_CRASH = "APP_CRASH"
    TIMEOUT = "TIMEOUT"
    STALE_OBSERVATION = "STALE_OBSERVATION"
    ARTIFACT_MISSING = "ARTIFACT_MISSING"
    ARTIFACT_CORRUPTED = "ARTIFACT_CORRUPTED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    USER_INTERFERENCE = "USER_INTERFERENCE"
    LOCK_TIMEOUT = "LOCK_TIMEOUT"
    MODEL_ERROR = "MODEL_ERROR"
    RAG_ERROR = "RAG_ERROR"
    UNKNOWN = "UNKNOWN"


class RecoveryTier(str, Enum):
    RETRY = "RETRY"
    REOBSERVE = "REOBSERVE"
    FALLBACK = "FALLBACK"
    REPLAN = "REPLAN"
    ESCALATE = "ESCALATE"
    ABORT = "ABORT"


# Deterministic default mapping from error class to recovery tier.
_DEFAULT_TIER: dict[ErrorClass, RecoveryTier] = {
    ErrorClass.TOOL_NOT_FOUND: RecoveryTier.REPLAN,
    ErrorClass.INVALID_TOOL_ARGUMENTS: RecoveryTier.REPLAN,
    ErrorClass.TARGET_NOT_FOUND: RecoveryTier.REOBSERVE,
    ErrorClass.TARGET_AMBIGUOUS: RecoveryTier.REOBSERVE,
    ErrorClass.APP_NOT_RUNNING: RecoveryTier.FALLBACK,
    ErrorClass.APP_CRASH: RecoveryTier.FALLBACK,
    ErrorClass.TIMEOUT: RecoveryTier.RETRY,
    ErrorClass.STALE_OBSERVATION: RecoveryTier.REOBSERVE,
    ErrorClass.ARTIFACT_MISSING: RecoveryTier.RETRY,
    ErrorClass.ARTIFACT_CORRUPTED: RecoveryTier.REPLAN,
    ErrorClass.VERIFICATION_FAILED: RecoveryTier.RETRY,
    ErrorClass.POLICY_DENIED: RecoveryTier.ABORT,
    ErrorClass.APPROVAL_REQUIRED: RecoveryTier.ESCALATE,
    ErrorClass.USER_INTERFERENCE: RecoveryTier.REOBSERVE,
    ErrorClass.LOCK_TIMEOUT: RecoveryTier.RETRY,
    ErrorClass.MODEL_ERROR: RecoveryTier.RETRY,
    ErrorClass.RAG_ERROR: RecoveryTier.RETRY,
    ErrorClass.UNKNOWN: RecoveryTier.ESCALATE,
}

# Backoff schedule (ms) by attempt index.
_BACKOFF_MS = [250, 1000, 4000]


@dataclass
class RecoveryDecision:
    tier: RecoveryTier
    error_class: ErrorClass
    attempt: int
    backoff_ms: int
    reason: str
    circuit_open: bool = False


@dataclass
class _BreakerState:
    failures: int = 0


class RecoveryEngine:
    """Bounded, deterministic recovery with a per-(step,error) circuit breaker."""

    def __init__(self, *, max_attempts: int = 3, breaker_threshold: int = 3) -> None:
        self._max_attempts = max_attempts
        self._breaker_threshold = breaker_threshold
        self._breakers: dict[str, _BreakerState] = {}

    @staticmethod
    def classify(error_class: str) -> ErrorClass:
        try:
            return ErrorClass(error_class)
        except ValueError:
            return ErrorClass.UNKNOWN

    def _breaker_key(self, step_key: str, error_class: ErrorClass) -> str:
        return f"{step_key}::{error_class.value}"

    def decide(self, *, step_key: str, error_class: str, attempt: int) -> RecoveryDecision:
        """Decide the recovery tier for a failure. `attempt` is 1-based."""
        ec = self.classify(error_class)
        tier = _DEFAULT_TIER.get(ec, RecoveryTier.ESCALATE)

        key = self._breaker_key(step_key, ec)
        state = self._breakers.setdefault(key, _BreakerState())
        state.failures += 1
        circuit_open = state.failures >= self._breaker_threshold

        # Non-retryable classes never retry regardless of attempt.
        non_retryable = {RecoveryTier.ABORT, RecoveryTier.ESCALATE, RecoveryTier.REPLAN}

        if circuit_open and tier not in {RecoveryTier.ABORT}:
            # Too many repeats of the same failure — stop looping.
            logger.warning("Circuit breaker OPEN for %s (failures=%d) -> ESCALATE", key, state.failures)
            return RecoveryDecision(
                tier=RecoveryTier.ESCALATE, error_class=ec, attempt=attempt,
                backoff_ms=0, reason=f"circuit breaker open after {state.failures} failures",
                circuit_open=True,
            )

        if tier == RecoveryTier.RETRY and attempt >= self._max_attempts:
            return RecoveryDecision(
                tier=RecoveryTier.ESCALATE, error_class=ec, attempt=attempt,
                backoff_ms=0, reason=f"max attempts ({self._max_attempts}) exhausted",
            )

        backoff = 0
        if tier in (RecoveryTier.RETRY, RecoveryTier.REOBSERVE) and tier not in non_retryable:
            backoff = _BACKOFF_MS[min(attempt - 1, len(_BACKOFF_MS) - 1)]

        return RecoveryDecision(
            tier=tier, error_class=ec, attempt=attempt, backoff_ms=backoff,
            reason=f"{ec.value} -> {tier.value}",
        )

    def reset(self, step_key: str) -> None:
        """Clear breaker state for a step once it finally succeeds."""
        for k in list(self._breakers.keys()):
            if k.startswith(f"{step_key}::"):
                del self._breakers[k]


recovery_engine = RecoveryEngine()
