"""
SyncNode — typed LangGraph state.

The global run state carried through the LangGraph StateGraph. It is a TypedDict
(LangGraph merges node return values into it) with reducer annotations for the
fields that multiple parallel branches append to (so fan-in joins are
deterministic rather than last-writer-wins).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional

from typing_extensions import TypedDict


def _merge_dict(a: dict, b: dict) -> dict:
    out = dict(a or {})
    out.update(b or {})
    return out


class SyncNodeState(TypedDict, total=False):
    # Identity / input
    run_id: str
    goal: str
    failure_mode: str

    # Cognition
    normalized_intent: Optional[dict]
    knowledge_context: str
    rag_provenance: list[dict]
    plan: Optional[dict]
    plan_steps: list[dict]

    # Agent lifecycle (parallel branches append -> use reducers)
    agent_assignments: dict[str, str]
    active_agents: Annotated[list[str], operator.add]
    completed_agents: Annotated[list[str], operator.add]
    failed_agents: Annotated[list[str], operator.add]
    agent_outputs: Annotated[dict[str, Any], _merge_dict]

    # Execution evidence (branches append)
    artifacts: Annotated[list[dict], operator.add]
    tool_calls: Annotated[list[dict], operator.add]
    observations: Annotated[list[dict], operator.add]
    verifications: Annotated[list[dict], operator.add]
    errors: Annotated[list[dict], operator.add]

    # Control
    recovery_state: dict
    approval_state: dict
    execution_status: str          # running | waiting_approval | completed | failed | ...
    telemetry: dict
    audit_sequence: int
    workflow_memory_id: Optional[str]


# Terminal execution statuses.
TERMINAL_STATES = {
    "COMPLETED", "WAITING_APPROVAL", "FAILED", "CANCELLED", "PAUSED",
    "RECOVERY_EXHAUSTED",
}
