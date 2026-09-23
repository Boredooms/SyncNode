"""
SyncNode — SQLAlchemy async ORM models.

This is the canonical Phase-1 persistence schema.
Matches the logical data model in idea.md §4.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Use JSONB for PostgreSQL, JSON for SQLite
JSONTYPE = JSON


class Base(AsyncAttrs, DeclarativeBase):
    pass


# ------------------------------------------------------------------ #
# Organization / User / Session                                         #
# ------------------------------------------------------------------ #


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_org_status"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="operator")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    organization: Mapped[Organization] = relationship(back_populates="users")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'operator', 'reviewer', 'viewer')", name="ck_user_role"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_user_status"),
        UniqueConstraint("organization_id", "email", name="uq_user_org_email"),
        Index("idx_users_org", "organization_id"),
    )


# ------------------------------------------------------------------ #
# Model Profiles                                                        #
# ------------------------------------------------------------------ #


class ModelProfile(Base):
    __tablename__ = "model_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONTYPE, nullable=False, default=dict)
    context_window: Mapped[Optional[int]] = mapped_column(Integer)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_thinking: Mapped[bool] = mapped_column(Boolean, default=False)
    parameter_size: Mapped[Optional[str]] = mapped_column(String(50))
    quantization: Mapped[Optional[str]] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    config: Mapped[dict] = mapped_column(JSONTYPE, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("provider", "model_id", name="uq_model_provider_id"),
    )


# ------------------------------------------------------------------ #
# Agent Definitions                                                     #
# ------------------------------------------------------------------ #


class AgentDefinition(Base):
    __tablename__ = "agent_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    capabilities: Mapped[list] = mapped_column(JSONTYPE, nullable=False, default=list)
    allowed_tools: Mapped[list] = mapped_column(JSONTYPE, nullable=False, default=list)
    model_requirements: Mapped[dict] = mapped_column(JSONTYPE, default=dict)
    risk_class: Mapped[str] = mapped_column(String(20), default="normal")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint(
            "risk_class IN ('normal', 'sensitive', 'external', 'destructive')",
            name="ck_agent_risk",
        ),
    )


# ------------------------------------------------------------------ #
# Tool Definitions                                                      #
# ------------------------------------------------------------------ #


class ToolDefinition(Base):
    __tablename__ = "tool_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    input_schema: Mapped[dict] = mapped_column(JSONTYPE, nullable=False, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSONTYPE, nullable=False, default=dict)
    capabilities: Mapped[list] = mapped_column(JSONTYPE, nullable=False, default=list)
    risk_class: Mapped[str] = mapped_column(String(30), nullable=False)
    side_effect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    idempotency: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ------------------------------------------------------------------ #
# Runs                                                                  #
# ------------------------------------------------------------------ #


class Run(Base):
    """Top-level durable run record. Created on POST /api/v1/runs."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    intent_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    plan_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    context_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    model_id: Mapped[Optional[str]] = mapped_column(String(200))
    failure_mode: Mapped[str] = mapped_column(String(50), default="none")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    evidence_dir: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[Optional[User]] = relationship(back_populates="runs")
    steps: Mapped[list["RunStep"]] = relationship("RunStep", back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship("AuditEvent", back_populates="run", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="run", cascade="all, delete-orphan")
    sse_events: Mapped[list["SSEEvent"]] = relationship("SSEEvent", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','waiting_approval','completed','failed','cancelled')",
            name="ck_run_status",
        ),
        Index("idx_run_status", "status"),
        Index("idx_run_created", "created_at"),
    )


class RunStep(Base):
    """One step in a run's task graph."""

    __tablename__ = "run_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_key: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    input_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    output_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    verification_status: Mapped[Optional[str]] = mapped_column(String(20))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[Run] = relationship(back_populates="steps")
    tool_calls: Mapped[list["ToolCall"]] = relationship("ToolCall", back_populates="step", cascade="all, delete-orphan")
    observations: Mapped[list["Observation"]] = relationship("Observation", back_populates="step", cascade="all, delete-orphan")
    verifications: Mapped[list["VerificationResult"]] = relationship("VerificationResult", back_populates="step", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','running','completed','failed','skipped','waiting_approval')",
            name="ck_step_status",
        ),
        Index("idx_step_run", "run_id"),
    )


# ------------------------------------------------------------------ #
# Tool Calls                                                            #
# ------------------------------------------------------------------ #


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    step_id: Mapped[str] = mapped_column(ForeignKey("run_steps.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tool_key: Mapped[str] = mapped_column(String(100), nullable=False)
    input_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    output_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    side_effect_type: Mapped[Optional[str]] = mapped_column(String(50))
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(200))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    invoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    step: Mapped[RunStep] = relationship(back_populates="tool_calls")


# ------------------------------------------------------------------ #
# Observations                                                          #
# ------------------------------------------------------------------ #


class Observation(Base):
    """Real-world state snapshot captured after an action."""

    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    step_id: Mapped[str] = mapped_column(ForeignKey("run_steps.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    application: Mapped[Optional[str]] = mapped_column(String(255))
    window_title: Mapped[Optional[str]] = mapped_column(Text)
    process_id: Mapped[Optional[int]] = mapped_column(Integer)
    screenshot_path: Mapped[Optional[str]] = mapped_column(Text)
    screenshot_hash: Mapped[Optional[str]] = mapped_column(String(64))
    uia_snapshot: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    dom_snapshot: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    filesystem_refs: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    step: Mapped[RunStep] = relationship(back_populates="observations")


# ------------------------------------------------------------------ #
# Verification Results                                                  #
# ------------------------------------------------------------------ #


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    step_id: Mapped[str] = mapped_column(ForeignKey("run_steps.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observation_id: Mapped[Optional[str]] = mapped_column(String(36))
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # PASS | FAIL | STALE | UNAVAILABLE
    assertions: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    step: Mapped[RunStep] = relationship(back_populates="verifications")


# ------------------------------------------------------------------ #
# Artifacts                                                             #
# ------------------------------------------------------------------ #


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(String(64))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[Run] = relationship(back_populates="artifacts")


# ------------------------------------------------------------------ #
# Approvals                                                             #
# ------------------------------------------------------------------ #


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    risk_class: Mapped[str] = mapped_column(String(50), nullable=False)
    action_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSONTYPE)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    decided_by: Mapped[Optional[str]] = mapped_column(String(36))
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    run: Mapped[Run] = relationship(back_populates="approvals")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired')",
            name="ck_approval_status",
        ),
    )


# ------------------------------------------------------------------ #
# Audit Events                                                          #
# ------------------------------------------------------------------ #


class AuditEvent(Base):
    """Tamper-evident audit record. SHA-256 chain links each event to previous."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("runs.id"))
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONTYPE, nullable=False, default=dict)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[Optional[Run]] = relationship(back_populates="audit_events")

    __table_args__ = (
        Index("idx_audit_run", "run_id"),
        Index("idx_audit_sequence", "sequence"),
    )


# ------------------------------------------------------------------ #
# SSE Events (persisted for replay)                                     #
# ------------------------------------------------------------------ #


class KnowledgeDocument(Base):
    """Version/hash tracking for a local Markdown knowledge file.

    The Markdown file on disk is the source of truth; this table tracks
    version history, content hashes, and trust tier for audit and reindexing.
    """

    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    doc_id: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    trust: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")
    tags: Mapped[list] = mapped_column(JSONTYPE, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("idx_knowledge_doc_id", "doc_id"),
        Index("idx_knowledge_hash", "content_hash"),
    )


class WorkflowMemory(Base):
    """A recorded workflow trajectory + outcome for safe learning."""

    __tablename__ = "workflow_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[Optional[str]] = mapped_column(String(36))
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    goal_summary: Mapped[str] = mapped_column(Text, default="")
    tool_sequence: Mapped[list] = mapped_column(JSONTYPE, default=list)
    trajectory: Mapped[list] = mapped_column(JSONTYPE, default=list)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    total_reward: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    failure_class: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("idx_wfmem_task", "task_type"),
        Index("idx_wfmem_success", "success"),
    )


class CandidateStrategy(Base):
    """A learned candidate workflow improvement awaiting human review.

    Lifecycle: CANDIDATE -> EVALUATING -> APPROVED -> ACTIVE -> DEPRECATED.
    NEVER auto-promoted; promotion is an explicit human decision.
    """

    __tablename__ = "candidate_strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_tool_sequence: Mapped[list] = mapped_column(JSONTYPE, default=list)
    rationale: Mapped[str] = mapped_column(Text, default="")
    source_run_id: Mapped[Optional[str]] = mapped_column(String(36))
    lifecycle: Mapped[str] = mapped_column(String(20), default="CANDIDATE")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36))
    review_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint(
            "lifecycle IN ('CANDIDATE','EVALUATING','APPROVED','ACTIVE','DEPRECATED','REJECTED')",
            name="ck_candidate_lifecycle",
        ),
        Index("idx_candidate_task", "task_type"),
    )


class SSEEvent(Base):
    __tablename__ = "sse_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONTYPE, nullable=False, default=dict)
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[Run] = relationship(back_populates="sse_events")

    __table_args__ = (
        Index("idx_sse_run_seq", "run_id", "sequence"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────────────────────────────────────

class ChatSession(Base):
    """A persistent conversational chat session with the local AI."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(Text, default="New Chat")
    # Optional binding to a specific run — set when chat is opened from a run panel
    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)          # rolling context summary
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_chat_session_updated", "updated_at"),)


class ChatMessage(Base):
    """A single message in a chat session (user or assistant)."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)   # user | assistant | tool
    content: Mapped[str] = mapped_column(Text, default="")
    tool_calls: Mapped[Optional[list]] = mapped_column(JSONTYPE)    # tools the model called
    tool_results: Mapped[Optional[list]] = mapped_column(JSONTYPE)  # results returned
    seq: Mapped[int] = mapped_column(Integer, default=0)            # ordering within session
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (Index("idx_chat_msg_session_seq", "session_id", "seq"),)
