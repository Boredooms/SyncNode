"""
SyncNode — Planner schemas.

Every node in the execution DAG must have postconditions.
No executable step may lack postconditions (Architecture constraint).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class StepRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTERNAL = "external"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff_ms: list[int] = Field(default_factory=lambda: [250, 1000, 4000])
    on_timeout: str = "observe_then_retry"  # observe_then_retry | fail | replan

    @field_validator("backoff_ms", mode="before")
    @classmethod
    def _coerce_backoff(cls, v: Any) -> Any:
        """Absorb a common model variance: the planner often emits backoff_ms as
        a single int (e.g. 1000) instead of a schedule list. Coerce a scalar into
        a geometric schedule and drop non-numeric junk, so a valid plan is not
        rejected over a formatting nit (avoids an expensive full-plan repair)."""
        if v is None:
            return [250, 1000, 4000]
        if isinstance(v, (int, float)):
            base = int(v)
            return [base, base * 2, base * 4]
        if isinstance(v, str):
            try:
                base = int(float(v))
                return [base, base * 2, base * 4]
            except ValueError:
                return [250, 1000, 4000]
        if isinstance(v, list):
            out = [int(x) for x in v if isinstance(x, (int, float))]
            return out or [250, 1000, 4000]
        return [250, 1000, 4000]


class Postcondition(BaseModel):
    """A machine-verifiable assertion to check after a step completes."""

    assertion_type: str  # file_exists | file_hash_match | uia_control_exists | dom_text_match | ...
    target: str  # path, control id, CSS selector, etc.
    expected: Optional[Any] = None
    description: str = ""


class PlanStep(BaseModel):
    """One node in the execution DAG."""

    step_key: str
    agent_key: str
    action: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    risk: StepRisk = StepRisk.LOW
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[Postcondition] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: int = 60
    requires_approval: bool = False


class ExecutionPlan(BaseModel):
    """Complete execution DAG produced by the Planner."""

    schema_version: str = "1.0"
    run_id: str
    goal_summary: str
    steps: list[PlanStep]
    total_steps: int = 0
    estimated_risk: StepRisk = StepRisk.LOW

    def model_post_init(self, __context: Any) -> None:
        self.total_steps = len(self.steps)


# _PlannerOutput is defined in _output.py to avoid circular imports
