"""
SyncNode — Execution Engine (deterministic).

Takes a VALIDATED tool proposal and drives one tool through its full lifecycle
with a persisted state machine and resource locks. It is deliberately dumb about
cognition: it does NOT interpret natural language, select tools, invent
arguments, override policy, or decide verification outcomes — those belong to
the intent/planner/registry/policy/verifier subsystems.

State machine:

    PROPOSED → VALIDATED → AUTHORIZED → LOCKED → PRECONDITION_CHECK
    → EXECUTING → OBSERVING → VERIFYING → (PASSED | FAILED | AMBIGUOUS)

Failure routes (decided by the caller/recovery engine, not here):
    RECOVERING / REPLANNING / WAITING_APPROVAL / FAILED
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from syncnode_backend.runtime.locks import ResourceLockManager, lease_group
from syncnode_backend.tools.registry import ToolDefinition, ToolRegistry

logger = logging.getLogger(__name__)


class ExecState(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    AUTHORIZED = "AUTHORIZED"
    LOCKED = "LOCKED"
    PRECONDITION_CHECK = "PRECONDITION_CHECK"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class ToolProposal:
    """A concrete, already-validated intent to run one tool."""

    tool_key: str
    inputs: dict[str, Any]
    agent_key: str
    agent_allowed_tools: list[str]
    step_key: str
    postconditions: list[dict] = field(default_factory=list)
    step_id: str = ""


@dataclass
class ExecutionResult:
    state: ExecState
    tool_key: str
    step_key: str
    tool_output: Optional[dict] = None
    verification: Optional[Any] = None  # VerificationReport
    error: Optional[str] = None
    error_class: Optional[str] = None
    transitions: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


# Callback signatures (injected so the engine stays decoupled).
PreconditionFn = Callable[[ToolDefinition, ToolProposal], Awaitable[Optional[str]]]
ObserveFn = Callable[[ToolProposal, Optional[dict]], Awaitable[float]]
VerifyFn = Callable[[ToolProposal, Optional[dict], float], Awaitable[Any]]
EmitFn = Callable[[str, dict], Awaitable[None]]


class ExecutionEngine:
    """Drives one validated tool proposal through the execution lifecycle."""

    def __init__(
        self,
        registry: ToolRegistry,
        locks: ResourceLockManager,
        *,
        emit: Optional[EmitFn] = None,
        precondition: Optional[PreconditionFn] = None,
        observe: Optional[ObserveFn] = None,
        verify: Optional[VerifyFn] = None,
    ) -> None:
        self._registry = registry
        self._locks = locks
        self._emit = emit
        self._precondition = precondition
        self._observe = observe
        self._verify = verify

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        if self._emit:
            try:
                await self._emit(event_type, payload)
            except Exception as exc:  # noqa: BLE001 - telemetry must not break execution
                logger.debug("emit failed: %s", exc)

    def _resource_locks_for(self, defn: ToolDefinition) -> list[str]:
        locks = list(defn.resource_locks)
        # Derive an application lock if the tool drives an app and declared none.
        if not locks and defn.supported_applications:
            for app in defn.supported_applications:
                locks.append(f"app:{app}")
        return locks

    async def run(self, proposal: ToolProposal) -> ExecutionResult:
        from syncnode_backend.errors.exceptions import (
            ToolError, ToolNotFoundError, ToolPermissionError, ToolUnavailableError,
        )

        t0 = time.monotonic()
        transitions: list[str] = [ExecState.PROPOSED.value]
        result = ExecutionResult(
            state=ExecState.PROPOSED, tool_key=proposal.tool_key,
            step_key=proposal.step_key, transitions=transitions,
        )

        def _transition(state: ExecState) -> None:
            result.state = state
            transitions.append(state.value)

        # ---- VALIDATED (lookup + availability + strict args) ----
        try:
            defn = self._registry.require(proposal.tool_key)
            await self._registry.check_available(proposal.tool_key)
            norm_inputs = self._registry.validate_call(
                proposal.tool_key, proposal.inputs, proposal.agent_allowed_tools
            )
        except ToolNotFoundError as exc:
            return self._fail(result, "TOOL_NOT_FOUND", str(exc), t0)
        except ToolUnavailableError as exc:
            return self._fail(result, "APP_NOT_RUNNING", str(exc), t0)
        except ToolPermissionError as exc:
            return self._fail(result, "POLICY_DENIED", str(exc), t0)
        except ToolError as exc:
            return self._fail(result, "INVALID_TOOL_ARGUMENTS", str(exc), t0)
        _transition(ExecState.VALIDATED)

        # ---- AUTHORIZED (agent access already checked in validate_call) ----
        _transition(ExecState.AUTHORIZED)
        await self._emit_event("tool.authorized", {
            "tool": proposal.tool_key, "agent": proposal.agent_key,
            "step_key": proposal.step_key, "risk": defn.risk_class,
        })

        resources = self._resource_locks_for(defn)
        try:
            async with lease_group(self._locks, resources, owner=proposal.agent_key):
                _transition(ExecState.LOCKED)

                # ---- PRECONDITION_CHECK ----
                _transition(ExecState.PRECONDITION_CHECK)
                if self._precondition is not None:
                    problem = await self._precondition(defn, proposal)
                    if problem:
                        return self._fail(result, "PRECONDITION_FAILED", problem, t0)

                # ---- EXECUTING ----
                _transition(ExecState.EXECUTING)
                await self._emit_event("tool.started", {
                    "tool": proposal.tool_key, "agent": proposal.agent_key,
                    "step_key": proposal.step_key,
                })
                try:
                    tool_output = await defn.handler(**norm_inputs)  # type: ignore[misc]
                except Exception as exc:  # noqa: BLE001 - real tool failure
                    return self._fail(result, "TOOL_EXECUTION_ERROR", str(exc), t0)
                result.tool_output = tool_output if isinstance(tool_output, dict) else {"result": tool_output}
                await self._emit_event("tool.completed", {
                    "tool": proposal.tool_key, "step_key": proposal.step_key,
                })

                # ---- OBSERVING ----
                _transition(ExecState.OBSERVING)
                obs_ts = time.time()
                if self._observe is not None:
                    obs_ts = await self._observe(proposal, result.tool_output)
                await self._emit_event("observation.captured", {
                    "step_key": proposal.step_key, "ts": obs_ts,
                })

                # ---- VERIFYING ----
                _transition(ExecState.VERIFYING)
                if self._verify is not None and proposal.postconditions:
                    report = await self._verify(proposal, result.tool_output, obs_ts)
                    result.verification = report
                    outcome = getattr(report, "result", "PASS")
                    if outcome == "PASS":
                        _transition(ExecState.PASSED)
                    elif outcome in ("STALE", "UNAVAILABLE"):
                        _transition(ExecState.AMBIGUOUS)
                        result.error_class = outcome
                        result.error = getattr(report, "failure_reason", outcome)
                    else:
                        _transition(ExecState.FAILED)
                        result.error_class = "VERIFICATION_FAILED"
                        result.error = getattr(report, "failure_reason", "verification failed")
                else:
                    # No postconditions to check — treat as passed at the engine
                    # level (the planner is expected to attach postconditions;
                    # missing ones are enforced upstream).
                    _transition(ExecState.PASSED)
        except Exception as exc:  # lock timeout or unexpected
            from syncnode_backend.errors.exceptions import LockTimeoutError
            cls = "LOCK_TIMEOUT" if isinstance(exc, LockTimeoutError) else "UNKNOWN"
            return self._fail(result, cls, str(exc), t0)

        result.duration_ms = (time.monotonic() - t0) * 1000
        return result

    def _fail(self, result: ExecutionResult, error_class: str, error: str, t0: float) -> ExecutionResult:
        result.state = ExecState.FAILED
        result.transitions.append(ExecState.FAILED.value)
        result.error_class = error_class
        result.error = error
        result.duration_ms = (time.monotonic() - t0) * 1000
        logger.warning("Execution failed — tool=%s class=%s: %s",
                       result.tool_key, error_class, error)
        return result
