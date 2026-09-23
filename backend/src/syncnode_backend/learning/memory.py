"""
SyncNode — Workflow Memory + Safe Learning.

Knowledge = how the world works (Markdown KB).
Workflow memory = what happened previously (trajectories + outcomes).

This module:
  - records a completed run's trajectory + deterministic reward,
  - ranks previously successful trajectories for a task type (strategy hints),
  - generates CANDIDATE strategies from failures,
  - enforces a human-reviewed promotion lifecycle.

SAFETY: nothing here mutates production policy, tool permissions, security
rules, or system prompts. Candidate strategies are inert until an explicit human
decision promotes them. A single run never changes control behaviour.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import select

from syncnode_backend.learning.reward import step_reward, trajectory_reward
from syncnode_backend.persistence.database import get_session
from syncnode_backend.persistence.models import CandidateStrategy, WorkflowMemory

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryStep:
    step_key: str
    action: str
    verification: Optional[str] = None
    retries: int = 0
    recovered: bool = False
    policy_violation: bool = False
    unsafe_side_effect: bool = False
    reward: float = 0.0
    observation: dict[str, Any] = field(default_factory=dict)


class WorkflowMemoryService:
    """Records trajectories and produces safe, human-gated learning."""

    async def record_run(
        self,
        *,
        run_id: str,
        task_type: str,
        goal_summary: str,
        steps: list[TrajectoryStep],
        success: bool,
        duration_ms: Optional[int] = None,
        failure_class: Optional[str] = None,
    ) -> dict[str, Any]:
        for s in steps:
            s.reward = step_reward(
                verification=s.verification, retries=s.retries, recovered=s.recovered,
                policy_violation=s.policy_violation, unsafe_side_effect=s.unsafe_side_effect,
            )
        total = trajectory_reward([s.reward for s in steps])
        tool_sequence = [s.action for s in steps if s.action]
        trajectory = [
            {"step": s.step_key, "action": s.action, "verification": s.verification,
             "retries": s.retries, "recovered": s.recovered, "reward": s.reward}
            for s in steps
        ]

        async with get_session() as session:
            session.add(WorkflowMemory(
                run_id=run_id, task_type=task_type, goal_summary=goal_summary,
                tool_sequence=tool_sequence, trajectory=trajectory, success=success,
                total_reward=total, duration_ms=duration_ms, failure_class=failure_class,
            ))

        logger.info("Workflow memory recorded — task=%s success=%s reward=%.2f",
                    task_type, success, total)

        # On failure, generate a CANDIDATE strategy for human review (never auto-applied).
        if not success and failure_class:
            await self._propose_candidate(run_id, task_type, goal_summary, tool_sequence, failure_class)

        return {"task_type": task_type, "success": success, "total_reward": total,
                "tool_sequence": tool_sequence}

    async def best_strategies(self, task_type: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return previously successful trajectories for a task type, best first.

        These are HINTS the planner may consider. They never bypass the tool
        registry, policy, verification, or recovery.
        """
        async with get_session() as session:
            result = await session.execute(
                select(WorkflowMemory)
                .where(WorkflowMemory.task_type == task_type, WorkflowMemory.success == True)  # noqa: E712
                .order_by(WorkflowMemory.total_reward.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                {"tool_sequence": r.tool_sequence, "total_reward": r.total_reward,
                 "run_id": r.run_id, "goal_summary": r.goal_summary}
                for r in rows
            ]

    async def _propose_candidate(
        self, run_id: str, task_type: str, goal_summary: str,
        tool_sequence: list[str], failure_class: str,
    ) -> None:
        # Map a failure class to a reusable, human-readable improvement idea.
        hints = {
            "TOOL_NOT_FOUND": "Constrain the plan to registered tools; the planner "
                              "should only emit actions present in the tool registry.",
            "INVALID_TOOL_ARGUMENTS": "Use the tool's declared argument names; only "
                                      "declared aliases are normalized.",
            "APP_NOT_RUNNING": "Resolve and launch the application (via App Paths) and "
                               "verify it is running before acting on it.",
            "TARGET_NOT_FOUND": "Re-observe the environment to resolve the target before acting.",
            "VERIFICATION_FAILED": "Ensure the step's postconditions match the artifact "
                                   "the tool actually produced.",
            "LOCK_TIMEOUT": "Serialize steps that contend for the same application/desktop lock.",
        }
        rationale = hints.get(failure_class, f"Investigate failure class {failure_class}.")
        async with get_session() as session:
            session.add(CandidateStrategy(
                task_type=task_type,
                summary=f"Improve handling of {failure_class} for '{goal_summary[:60]}'",
                proposed_tool_sequence=tool_sequence,
                rationale=rationale,
                source_run_id=run_id,
                lifecycle="CANDIDATE",
            ))
        logger.info("Candidate strategy proposed (CANDIDATE, awaiting review) — task=%s class=%s",
                    task_type, failure_class)

    # ---- Human-reviewed promotion lifecycle (never automatic) ----

    async def list_candidates(self, lifecycle: Optional[str] = None) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = select(CandidateStrategy).order_by(CandidateStrategy.created_at.desc())
            if lifecycle:
                stmt = stmt.where(CandidateStrategy.lifecycle == lifecycle)
            rows = (await session.execute(stmt)).scalars().all()
            return [self._candidate_dict(r) for r in rows]

    async def review_candidate(
        self, candidate_id: str, *, decision: str, reviewer: str, reason: str = "",
    ) -> dict[str, Any]:
        """Explicit human decision. decision ∈ {approve, reject, activate, deprecate}.

        Promotion to ACTIVE requires an explicit 'activate' after 'approve'.
        """
        from syncnode_backend.errors.exceptions import SyncNodeError
        transitions = {
            "approve": ("CANDIDATE", "APPROVED"),
            "reject": (None, "REJECTED"),
            "activate": ("APPROVED", "ACTIVE"),
            "deprecate": (None, "DEPRECATED"),
        }
        if decision not in transitions:
            raise SyncNodeError(f"Unknown review decision: {decision!r}")
        required_from, new_state = transitions[decision]
        async with get_session() as session:
            cand = await session.get(CandidateStrategy, candidate_id)
            if not cand:
                raise SyncNodeError("Candidate not found")
            if required_from and cand.lifecycle != required_from:
                raise SyncNodeError(
                    f"Cannot {decision}: candidate is {cand.lifecycle}, expected {required_from}"
                )
            cand.lifecycle = new_state
            cand.reviewed_by = reviewer
            cand.review_reason = reason
            return self._candidate_dict(cand)

    @staticmethod
    def _candidate_dict(r: CandidateStrategy) -> dict[str, Any]:
        return {
            "id": r.id,
            "candidate_id": r.id,           # matches frontend expectation
            "task_type": r.task_type,
            "summary": r.summary,
            "description": r.summary,       # frontend reads 'description'
            "rationale": r.rationale,
            "proposed_tool_sequence": r.proposed_tool_sequence,
            "lifecycle": r.lifecycle,
            "source_run_id": r.source_run_id,
            "reviewed_by": r.reviewed_by,
            "review_reason": r.review_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }


workflow_memory = WorkflowMemoryService()
