"""
SyncNode — Run API endpoints.

POST /api/v1/runs                              — create a run
GET  /api/v1/runs/{run_id}                     — get run status
GET  /api/v1/runs/{run_id}/steps               — list run steps
GET  /api/v1/runs/{run_id}/tools               — list tool calls
GET  /api/v1/runs/{run_id}/observations        — list observations
GET  /api/v1/runs/{run_id}/verifications       — list verifications
GET  /api/v1/runs/{run_id}/recovery            — recovery events
GET  /api/v1/runs/{run_id}/audit               — audit events
GET  /api/v1/runs/{run_id}/artifacts           — artifacts
GET  /api/v1/runs/{run_id}/events              — SSE stream
POST /api/v1/runs/{run_id}/reconcile           — crash reconcile
POST /api/v1/runs/{run_id}/terminate           — terminate
POST /api/v1/runs/{run_id}/approvals/{id}/decide — approve/reject
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from syncnode_backend.config.settings import settings
from syncnode_backend.persistence.database import get_session
from syncnode_backend.persistence.models import (
    Approval, AuditEvent, Artifact, Run, RunStep, SSEEvent, ToolCall,
    Observation, VerificationResult,
)

router = APIRouter()


# ------------------------------------------------------------------ #
# Request / Response models                                             #
# ------------------------------------------------------------------ #


class CreateRunRequest(BaseModel):
    goal: str
    failure_mode: str = "none"
    workspace: Optional[str] = None


class RunResponse(BaseModel):
    run_id: str
    status: str
    goal: str
    created_at: str
    model_id: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved | rejected
    reason: Optional[str] = None


# ------------------------------------------------------------------ #
# SSE event bus (in-memory, per run)                                    #
# ------------------------------------------------------------------ #

_sse_queues: dict[str, asyncio.Queue] = {}

# Live orchestrator instances — keyed by run_id while the run is executing.
# Enables terminate_run and chat to reach the live orchestrator directly.
# Entries are removed in execute_run's finally block so no leaks occur.
_live_orchestrators: dict[str, Any] = {}


def get_sse_queue(run_id: str) -> asyncio.Queue:
    if run_id not in _sse_queues:
        _sse_queues[run_id] = asyncio.Queue()
    return _sse_queues[run_id]


async def emit_sse_event(run_id: str, event_type: str, payload: dict) -> None:
    """Emit an event to the SSE queue for a run."""
    queue = get_sse_queue(run_id)
    event = {"event_type": event_type, "run_id": run_id, "ts": time.time(), **payload}
    await queue.put(event)

    # Persist to DB
    try:
        async with get_session() as session:
            # Get next sequence
            result = await session.execute(
                select(SSEEvent).where(SSEEvent.run_id == run_id).order_by(SSEEvent.sequence.desc()).limit(1)
            )
            last = result.scalar_one_or_none()
            seq = (last.sequence + 1) if last else 1

            db_event = SSEEvent(
                run_id=run_id,
                event_type=event_type,
                sequence=seq,
                payload=event,
            )
            session.add(db_event)
    except Exception:
        pass  # SSE persistence failure should not block execution


# ------------------------------------------------------------------ #
# Endpoints                                                             #
# ------------------------------------------------------------------ #


@router.post("/runs", response_model=RunResponse)
async def create_run(request: CreateRunRequest, background_tasks: BackgroundTasks):
    """Accept a user goal and create a durable run."""
    run_id = str(uuid.uuid4())

    async with get_session() as session:
        run = Run(
            id=run_id,
            goal=request.goal,
            status="queued",
            failure_mode=request.failure_mode,
            model_id=settings.syncnode_model_id,
        )
        session.add(run)

    # Start execution in background
    background_tasks.add_task(execute_run, run_id, request.goal, request.failure_mode)

    return RunResponse(
        run_id=run_id,
        status="queued",
        goal=request.goal,
        created_at=str(time.time()),
        model_id=settings.syncnode_model_id,
    )


@router.get("/runs")
async def list_runs(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List all runs, newest first. Optionally filter by status."""
    async with get_session() as session:
        q = select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
        if status:
            q = q.where(Run.status == status)
        result = await session.execute(q)
        runs = result.scalars().all()
        return {
            "runs": [
                {
                    "run_id": r.id,
                    "status": r.status,
                    "goal": r.goal,
                    "model_id": r.model_id,
                    "created_at": r.created_at.timestamp() if r.created_at else None,
                    "completed_at": r.completed_at.timestamp() if r.completed_at else None,
                    "error_message": r.error_message,
                }
                for r in runs
            ],
            "total": len(runs),
        }


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        result = await session.get(Run, run_id)
        if not result:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "run_id": result.id,
            "status": result.status,
            "goal": result.goal,
            "model_id": result.model_id,
            "created_at": str(result.created_at),
            "completed_at": str(result.completed_at) if result.completed_at else None,
            "error_message": result.error_message,
        }


@router.get("/runs/{run_id}/steps")
async def get_run_steps(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        result = await session.execute(
            select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.step_index)
        )
        steps = result.scalars().all()
        return {"run_id": run_id, "steps": [
            {
                "step_key": s.step_key,
                "status": s.status,
                "agent": s.agent_key,
                "action": s.action,
                # Human-readable label: prefer description from output_json, fall back to action/key.
                "description": (
                    (s.output_json or {}).get("description")
                    or s.action
                    or s.step_key
                ),
                "verification": s.verification_status,
                "retries": s.retry_count,
                "started_at": str(s.started_at) if s.started_at else None,
                "completed_at": str(s.completed_at) if s.completed_at else None,
            }
            for s in steps
        ]}


@router.get("/runs/{run_id}/artifacts")
async def get_run_artifacts(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        result = await session.execute(
            select(Artifact).where(Artifact.run_id == run_id)
        )
        arts = result.scalars().all()
        # Build step_id -> step_key lookup for artifact context.
        step_keys: dict[str, str] = {}
        all_steps_r = await session.execute(
            select(RunStep).where(RunStep.run_id == run_id)
        )
        for s in all_steps_r.scalars().all():
            step_keys[s.id] = s.step_key
        return {"run_id": run_id, "artifacts": [
            {
                "artifact_id": a.id,
                "name": a.name,
                "type": a.artifact_type,
                "kind": a.artifact_type,
                "path": a.path,
                "sha256": a.sha256,
                "size_bytes": a.size_bytes,
                "verified": a.verified,
                "step_key": step_keys.get(a.metadata_json.get("producer_step_id", "") if isinstance(a.metadata_json, dict) else ""),
                "agent": (a.metadata_json or {}).get("agent") if isinstance(a.metadata_json, dict) else None,
                "created_at": str(a.created_at) if hasattr(a, "created_at") else None,
            }
            for a in arts
        ]}


@router.get("/runs/{run_id}/tools")
async def get_run_tool_calls(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        # Join ToolCall with RunStep to get the human-readable step_key.
        result = await session.execute(
            select(ToolCall, RunStep.step_key, RunStep.agent_key)
            .join(RunStep, ToolCall.step_id == RunStep.id)
            .where(ToolCall.run_id == run_id)
        )
        rows = result.all()
        return {"run_id": run_id, "tool_calls": [
            {
                "tool_key": c.tool_key,
                "step_key": step_key,
                "agent": agent_key,
                "status": c.status,
                "side_effect_type": c.side_effect_type,
                "duration_ms": c.duration_ms,
                "error_message": c.error_message,
                "inputs": c.input_json,
                "outputs": c.output_json,
            }
            for c, step_key, agent_key in rows
        ]}


@router.get("/runs/{run_id}/observations")
async def get_run_observations(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        # Join Observation with RunStep to resolve the UUID step_id -> step_key string.
        result = await session.execute(
            select(Observation, RunStep.step_key, RunStep.agent_key)
            .join(RunStep, Observation.step_id == RunStep.id)
            .where(Observation.run_id == run_id)
        )
        rows = result.all()
        return {"run_id": run_id, "observations": [
            {
                "observation_id": o.id,
                "step_key": step_key,
                "agent": agent_key,
                "observation_type": o.observation_type,
                "application": o.application,
                "window_title": o.window_title,
                "process_id": o.process_id,
                "screenshot_path": o.screenshot_path,
                "screenshot_hash": o.screenshot_hash,
                "content": (
                    (o.metadata_json or {}).get("content")
                    if isinstance(o.metadata_json, dict) else None
                ),
                "metadata": o.metadata_json,
                "captured_at": str(o.captured_at),
            }
            for o, step_key, agent_key in rows
        ]}


@router.get("/runs/{run_id}/approvals")
async def get_run_approvals(run_id: str) -> dict[str, Any]:
    """Return all approval records for a run (pending + decided)."""
    async with get_session() as session:
        result = await session.execute(
            select(Approval).where(Approval.run_id == run_id)
            .order_by(Approval.requested_at)
        )
        approvals = result.scalars().all()
        return {"run_id": run_id, "approvals": [
            {
                "approval_id": a.id,
                "run_id": a.run_id,
                "step_id": a.step_id,
                "risk_class": a.risk_class,
                "action": a.action_summary,
                "action_summary": a.action_summary,
                "risk": a.risk_class,
                "status": a.status,
                "decision": a.status if a.status != "pending" else None,
                "reason": a.decision_reason,
                "context": a.evidence_json or {},
                "created_at": a.requested_at.timestamp() if a.requested_at else None,
                "decided_at": a.decided_at.timestamp() if a.decided_at else None,
            }
            for a in approvals
        ]}


@router.get("/runs/{run_id}/verifications")
async def get_run_verifications(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        result = await session.execute(
            select(VerificationResult, RunStep.step_key, RunStep.agent_key)
            .join(RunStep, VerificationResult.step_id == RunStep.id)
            .where(VerificationResult.run_id == run_id)
        )
        rows = result.all()
        return {"run_id": run_id, "verifications": [
            {
                "verification_id": v.id,
                "step_key": step_key,
                "agent": agent_key,
                "result": v.result,
                "failure_reason": v.failure_reason,
                "assertions": v.assertions,
                "evidence": v.evidence,
            }
            for v, step_key, agent_key in rows
        ]}


@router.get("/runs/{run_id}/context")
async def get_run_context(run_id: str) -> dict[str, Any]:
    """Run context including RAG provenance (which knowledge the run used)."""
    async with get_session() as session:
        run = await session.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"run_id": run_id, "context": run.context_json or {}}


@router.get("/runs/{run_id}/audit")
async def get_run_audit(run_id: str) -> dict[str, Any]:
    async with get_session() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.run_id == run_id).order_by(AuditEvent.sequence)
        )
        events = result.scalars().all()
        return {"run_id": run_id, "events": [
            {"seq": e.sequence, "type": e.event_type,
             "hash": e.chain_hash[:8], "ts": str(e.occurred_at)}
            for e in events
        ]}


@router.get("/runs/{run_id}/events")
async def sse_stream(run_id: str):
    """Server-Sent Events stream for a run."""
    async def generate():
        queue = get_sse_queue(run_id)
        yield f"data: {json.dumps({'event_type': 'stream.connected', 'run_id': run_id})}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
                # Only close the stream on true terminal events. waiting_approval
                # is NOT terminal — the run resumes after the human decides, so
                # the stream must stay open to deliver approval.decided,
                # run.started, and run.completed/run.failed events.
                if event.get("event_type") in ("run.completed", "run.failed", "run.cancelled"):
                    break
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/runs/{run_id}/approvals/{approval_id}/decide")
async def decide_approval(
    run_id: str, approval_id: str,
    request: ApprovalDecisionRequest,
    background_tasks: BackgroundTasks,
):
    """Record a human approval decision and resume the run."""
    async with get_session() as session:
        approval = await session.get(Approval, approval_id)
        if not approval or approval.run_id != run_id:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.status != "pending":
            raise HTTPException(status_code=400, detail=f"Approval already decided: {approval.status}")

        approval.status = request.decision
        approval.decision_reason = request.reason

        run = await session.get(Run, run_id)
        if run:
            run.status = "running" if request.decision == "approved" else "failed"

    await emit_sse_event(run_id, "approval.decided", {
        "approval_id": approval_id, "decision": request.decision,
    })

    # Resume (or finalize) the run in the background after the decision.
    background_tasks.add_task(
        resume_after_approval, run_id, request.decision, request.reason
    )

    return {"approval_id": approval_id, "decision": request.decision}


@router.get("/screenshots/{observation_id}")
async def get_screenshot(observation_id: str):
    """Serve a captured screenshot image by observation id.

    Path is validated to live inside the configured workspace root so this
    endpoint can never serve arbitrary files off disk (no path traversal).
    """
    from pathlib import Path

    async with get_session() as session:
        obs = await session.get(Observation, observation_id)
        if obs is None or not obs.screenshot_path:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        try:
            shot = Path(obs.screenshot_path).resolve()
            workspace_root = Path(str(settings.syncnode_workspace_root)).resolve()
        except Exception:
            raise HTTPException(status_code=404, detail="Screenshot path invalid")

        # Fail closed: only serve files inside the workspace sandbox.
        if workspace_root not in shot.parents and shot != workspace_root:
            raise HTTPException(status_code=403, detail="Screenshot outside workspace")
        if not shot.is_file():
            raise HTTPException(status_code=404, detail="Screenshot file missing")

        return FileResponse(str(shot), media_type="image/png")


@router.post("/runs/{run_id}/terminate")
async def terminate_run(run_id: str):
    """Terminate a running run — sets DB status AND signals the live orchestrator."""
    async with get_session() as session:
        run = await session.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        run.status = "cancelled"
    # Signal the live orchestrator to stop at the next step boundary
    orch = _live_orchestrators.get(run_id)
    if orch is not None:
        orch._stop_requested = True
    await emit_sse_event(run_id, "run.cancelled", {})
    return {"run_id": run_id, "status": "cancelled"}


class InjectStepRequest(BaseModel):
    action: str                    # registered tool key, e.g. "document.create_docx"
    description: str               # human-readable label shown in the plan
    inputs: dict = {}              # pre-filled tool inputs (model will still resolve from artifacts)
    agent_key: Optional[str] = None  # override agent; auto-detected from tool if omitted


@router.post("/runs/{run_id}/inject-step")
async def inject_step(run_id: str, req: InjectStepRequest):
    """
    Inject a new step into a live run's plan.

    The step is appended to the plan and marked 'pending'. On the orchestrator's
    next wave evaluation it will be picked up and executed end-to-end through the
    normal ExecutionEngine pipeline (tool call → observation → verification).

    Works only while the run is actively executing (status == running).
    Returns 409 if the run is not live.
    """
    from syncnode_backend.tools.registry import tool_registry
    from syncnode_ai.agents.registry import agent_registry

    orch = _live_orchestrators.get(run_id)
    if orch is None or orch._plan is None:
        raise HTTPException(status_code=409, detail="Run is not currently executing")

    # Resolve the agent that owns this tool
    agent_key = req.agent_key
    if not agent_key:
        for a in agent_registry.all_enabled():
            if req.action in a.allowed_tools:
                agent_key = a.agent_id
                break
    if not agent_key:
        raise HTTPException(status_code=422, detail=f"No agent found for action '{req.action}'")

    # Validate the tool exists
    try:
        tool_registry.require(req.action)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Unknown tool: '{req.action}'")

    # Build a minimal PlanStep compatible with the planner schema
    from syncnode_ai.planner.schemas import PlanStep, Postcondition
    new_step = PlanStep(
        step_key=f"chat_injected_{uuid.uuid4().hex[:8]}",
        action=req.action,
        description=req.description,
        agent_key=agent_key,
        inputs=req.inputs or {},
        postconditions=[Postcondition(assertion_type="file_exists", target="")],
        dependencies=[],
        requires_approval=False,
    )

    # Append to the live plan and register as pending
    step_idx = len(orch._plan.steps)
    orch._plan.steps.append(new_step)
    orch._plan_step_status[step_idx] = "pending"
    orch._plan.total_steps = len(orch._plan.steps)

    # Emit SSE so frontend sees the injection immediately
    await emit_sse_event(run_id, "plan.step_injected", {
        "step_key": new_step.step_key,
        "action": req.action,
        "description": req.description,
        "injected_by": "chat",
    })
    # Also update plan in DB
    async with get_session() as session:
        run = await session.get(Run, run_id)
        if run:
            run.plan_json = orch._plan.model_dump()

    return {
        "injected": True,
        "step_key": new_step.step_key,
        "step_index": step_idx,
        "agent": agent_key,
    }


# ------------------------------------------------------------------ #
# Background execution                                                  #
# ------------------------------------------------------------------ #


async def resume_after_approval(run_id: str, decision: str, reason: Optional[str]) -> None:
async def resume_after_approval(run_id: str, decision: str, reason: Optional[str]) -> None:
    """Resume a waiting_approval run after a human decision.
    Always completes/fails the run — never leaves it stuck in 'running'.
    """
    await asyncio.sleep(0.8)
    if decision == "approved":
        # Best-effort Send click — wrapped so any exception can't block completion
        try:
            send_result = await _click_gmail_send(run_id)
            if send_result.get("sent"):
                await emit_sse_event(run_id, "tool.completed", {
                    "tool_key": "browser.click",
                    "step_key": "send_email_approved",
                    "result": {"clicked": True, "target": "Send button"},
                })
            else:
                await emit_sse_event(run_id, "run.warning", {
                    "message": f"Send not auto-clicked: {send_result.get('error', 'browser unavailable')}. Click Send manually.",
                })
        except Exception as send_exc:
            logger.warning("[APPROVAL] send click failed (non-fatal): %s", send_exc)

        # Always mark completed regardless of send result
        try:
            async with get_session() as session:
                run = await session.get(Run, run_id)
                if run:
                    run.status = "completed"
                    from datetime import datetime, timezone
                    run.completed_at = datetime.now(timezone.utc)
        except Exception as db_exc:
            logger.error("[APPROVAL] db update failed: %s", db_exc)

        await emit_sse_event(run_id, "run.completed", {
            "message": "Approved — workflow complete.",
        })
    else:
        try:
            async with get_session() as session:
                run = await session.get(Run, run_id)
                if run:
                    run.status = "failed"
                    run.error_message = f"Rejected by operator: {reason or 'no reason given'}"
        except Exception as db_exc:
            logger.error("[APPROVAL] db update failed: %s", db_exc)

        await emit_sse_event(run_id, "run.failed", {
            "error": f"Rejected: {reason or 'no reason given'}",
        })


async def _click_gmail_send(run_id: str) -> dict:
    """Click the Send button in the currently open browser compose window.

    Works with both the local compose fixture (compose.html) and real Gmail.
    The local fixture has id="send-button" with aria-label="Send".
    Returns {"sent": True} on success or {"sent": False, "error": "..."} on failure.
    """
    try:
        from syncnode_backend.browser.tools import get_page
        page = await get_page()
        if page is None:
            return {"sent": False, "error": "No active browser page"}

        current_url = page.url
        logger.info("[APPROVAL] clicking Send on page: %s", current_url[:100])

        # Try selectors in priority order — local fixture first, then real Gmail
        send_selectors = [
            # Local fixture (compose.html) — most specific, always try first
            "#send-button",
            "button[aria-label='Send']",
            "button.send-btn",
            # Real Gmail compose window Send button
            "[role='button'][data-tooltip*='Send']",
            "[role='button'][aria-label*='Send']",
            "[data-tooltip='Send ‪(Ctrl-Enter)‬']",
            "[data-tooltip='Send']",
            # Text fallback
            "button:has-text('Send')",
            ".T-I.J-J5-Ji.aoO.v7.T-I-atl.L3",
        ]

        for selector in send_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                    await btn.click(timeout=5000)
                    import asyncio as _aio
                    await _aio.sleep(1.5)
                    logger.info("[APPROVAL] Send clicked via selector=%s run_id=%s", selector, run_id)
                    return {"sent": True, "selector": selector}
            except Exception:
                continue

        return {"sent": False, "error": "Send button not found with any selector"}

    except Exception as exc:
        logger.warning("[APPROVAL] _click_gmail_send failed: %s", exc)
        return {"sent": False, "error": str(exc)}
        await emit_sse_event(run_id, "run.failed", {
            "error": f"Rejected: {reason or 'no reason given'}",
        })


async def execute_run(run_id: str, goal: str, failure_mode: str) -> None:
    """Background task: execute the full run pipeline."""
    from syncnode_backend.workflow.orchestrator import SyncNodeOrchestrator

    try:
        orch = SyncNodeOrchestrator(run_id=run_id, emit_sse=emit_sse_event)
        _live_orchestrators[run_id] = orch        # register while running
        await orch.execute(goal=goal, failure_mode=failure_mode)
    except Exception as exc:
        async with get_session() as session:
            run = await session.get(Run, run_id)
            if run:
                run.status = "failed"
                run.error_message = str(exc)
        await emit_sse_event(run_id, "run.failed", {"error": str(exc)})
    finally:
        _live_orchestrators.pop(run_id, None)     # always clean up
