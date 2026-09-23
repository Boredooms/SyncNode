"""Recovery engine tests (Phase H): classification, tiers, bounds, circuit breaker."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from syncnode_backend.recovery.engine import (  # noqa: E402
    ErrorClass, RecoveryEngine, RecoveryTier,
)


def test_classify_known_and_unknown():
    eng = RecoveryEngine()
    assert eng.classify("LOCK_TIMEOUT") == ErrorClass.LOCK_TIMEOUT
    assert eng.classify("nonsense") == ErrorClass.UNKNOWN


def test_policy_denied_aborts():
    eng = RecoveryEngine()
    d = eng.decide(step_key="s1", error_class="POLICY_DENIED", attempt=1)
    assert d.tier == RecoveryTier.ABORT


def test_tool_not_found_replans():
    eng = RecoveryEngine()
    d = eng.decide(step_key="s1", error_class="TOOL_NOT_FOUND", attempt=1)
    assert d.tier == RecoveryTier.REPLAN


def test_stale_observation_reobserves_with_backoff():
    eng = RecoveryEngine()
    d = eng.decide(step_key="s1", error_class="STALE_OBSERVATION", attempt=1)
    assert d.tier == RecoveryTier.REOBSERVE
    assert d.backoff_ms > 0


def test_retry_then_escalate_when_exhausted():
    eng = RecoveryEngine(max_attempts=3, breaker_threshold=99)
    d1 = eng.decide(step_key="s1", error_class="TIMEOUT", attempt=1)
    assert d1.tier == RecoveryTier.RETRY
    d3 = eng.decide(step_key="s1", error_class="TIMEOUT", attempt=3)
    assert d3.tier == RecoveryTier.ESCALATE  # attempt >= max


def test_circuit_breaker_opens():
    eng = RecoveryEngine(max_attempts=99, breaker_threshold=3)
    eng.decide(step_key="s2", error_class="TIMEOUT", attempt=1)
    eng.decide(step_key="s2", error_class="TIMEOUT", attempt=2)
    d = eng.decide(step_key="s2", error_class="TIMEOUT", attempt=3)
    assert d.circuit_open is True
    assert d.tier == RecoveryTier.ESCALATE


def test_breaker_reset_on_success():
    eng = RecoveryEngine(max_attempts=99, breaker_threshold=2)
    eng.decide(step_key="s3", error_class="TIMEOUT", attempt=1)
    eng.reset("s3")
    d = eng.decide(step_key="s3", error_class="TIMEOUT", attempt=1)
    assert d.circuit_open is False


def test_approval_required_escalates():
    eng = RecoveryEngine()
    d = eng.decide(step_key="s1", error_class="APPROVAL_REQUIRED", attempt=1)
    assert d.tier == RecoveryTier.ESCALATE
