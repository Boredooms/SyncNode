"""
SyncNode — Intent schemas.

Every model-generated intent must conform to these schemas
before entering the planning stage.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class GoalType(str, Enum):
    CREATE_DOCUMENT = "CREATE_DOCUMENT"
    MODIFY_DOCUMENT = "MODIFY_DOCUMENT"
    READ_DOCUMENT = "READ_DOCUMENT"
    OPEN_APPLICATION = "OPEN_APPLICATION"
    BROWSER_NAVIGATION = "BROWSER_NAVIGATION"
    EMAIL_DRAFT = "EMAIL_DRAFT"
    SEARCH_FILES = "SEARCH_FILES"
    EXECUTE_WORKFLOW = "EXECUTE_WORKFLOW"
    COMPOSITE = "COMPOSITE"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequirement(str, Enum):
    NONE = "none"
    PRE_EXECUTION = "pre_execution"
    POST_PLAN = "post_plan"
    BEFORE_EXTERNAL_SEND = "before_external_send"


class EntityRef(BaseModel):
    """A named entity extracted from the user goal."""

    entity_type: str  # document | application | email | person | path | url
    value: str
    resolved: Optional[str] = None  # Resolved to actual path/address if possible


class Constraint(BaseModel):
    constraint_type: str
    description: str
    is_hard: bool = True  # Hard = must be respected; soft = best-effort


class StructuredIntent(BaseModel):
    """
    Schema-validated intent produced by the Intent Engine.

    The planner uses this object to construct the execution DAG.
    Invalid intent must not proceed to planning.
    """

    schema_version: str = "1.0"
    goal_type: GoalType
    goal_summary: str = Field(..., description="One-sentence summary of what the user wants.")
    tasks: list[str] = Field(..., description="Ordered list of high-level task names.")
    entities: list[EntityRef] = Field(default_factory=list)
    workspace: Optional[str] = None
    applications: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    recipient: Optional[str] = None
    subject_hint: Optional[str] = None   # email subject extracted by enricher
    body_hint: Optional[str] = None      # email body extracted by enricher
    save_filename: Optional[str] = None  # desired output filename (e.g. "tree.docx")
    attachment_filename: Optional[str] = None  # file to attach
    constraints: list[Constraint] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    approval_required: ApprovalRequirement = ApprovalRequirement.NONE
    requires_human_stop: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
