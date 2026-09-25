"""
SyncNode — Agentic Chat API.

POST /api/v1/chat/sessions                    — create session
GET  /api/v1/chat/sessions                    — list sessions
GET  /api/v1/chat/sessions/{id}               — get session + messages
DELETE /api/v1/chat/sessions/{id}             — delete session
POST /api/v1/chat/sessions/{id}/stream        — send message, stream SSE response
POST /api/v1/chat/sessions/{id}/clear         — clear history
GET  /api/v1/chat/sessions/{id}/run-context   — get serialised run context for session

Per-turn pipeline:
  1. Load conversation history
  2. If run_id attached → load run memory: goal, steps, artifacts, workspace files, trajectory
  3. If history > CONTEXT_TURN_LIMIT → summarize old turns with gemma3:1b (CPU, unloads immediately)
  4. Build system prompt with full workflow context + available tools
  5. Stream gemma4:e4b response token-by-token
  6. Agentic loop: if model proposes tool call → execute → feed result back → re-stream (up to 5 rounds)
  7. If run_id present and model produces a step-modification request → inject into the live workflow
  8. Store assistant message, persist
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from syncnode_backend.config.settings import settings
from syncnode_backend.persistence.database import get_session
from syncnode_backend.persistence.models import ChatSession, ChatMessage
from syncnode_backend.runtime.scheduler import scheduler

logger = logging.getLogger(__name__)

router = APIRouter()

CONTEXT_TURN_LIMIT = 12   # above this → summarize older turns
SUMMARY_KEEP_TURNS  = 4   # keep most-recent N turns after summarizing


# ─────────────────────────────────────────────────────────────────────────────
# Workflow context builder
# Serialises everything the model needs to know about the current run:
#   - goal + status
#   - plan steps with their status
#   - produced artifacts (name, path, verified, sha256)
#   - workspace files in the run directory
#   - recent trajectory steps (tool → result pairs)
#   - workflow memory from past similar runs
# ─────────────────────────────────────────────────────────────────────────────

async def _build_run_context(run_id: str) -> str:
    """Return a compact, token-budgeted string summarising the run for the model.

    Hard limits to avoid blowing the num_ctx window:
      - Steps:     max 20, each line capped at 120 chars  → ~2400 chars
      - Artifacts: max 10, each line capped at 100 chars  → ~1000 chars
      - Workspace: max 8  files                           →  ~400 chars
      - Memory:    max 2  entries, 80 chars each          →  ~200 chars
    Total budget: ~4000 chars ≈ ~1000 tokens — safe alongside a system prompt.
    """
    from syncnode_backend.persistence.models import (
        Run, RunStep, Artifact as ArtifactModel,
    )
    lines: list[str] = []

    try:
        async with get_session() as db:
            run = await db.get(Run, run_id)
            if not run:
                return ""

            lines.append(f"[ACTIVE RUN: {run_id[:12]}…]")
            lines.append(f"Goal: {run.goal[:200]}")
            lines.append(f"Status: {run.status}")

            # ── Steps (capped at 20) ─────────────────────────────────────────
            result = await db.execute(
                select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.step_index)
            )
            steps = result.scalars().all()
            if steps:
                lines.append("\nPlan Steps:")
                for s in steps[:20]:
                    icon = "✓" if s.status == "completed" else ("✗" if s.status == "failed" else "○")
                    entry = f"  {icon} [{s.status}] {s.step_key} → {s.action or '—'}"
                    lines.append(entry[:120])
                if len(steps) > 20:
                    lines.append(f"  … and {len(steps) - 20} more steps")

            # ── Artifacts (capped at 10) ──────────────────────────────────────
            result2 = await db.execute(
                select(ArtifactModel).where(ArtifactModel.run_id == run_id)
            )
            artifacts = result2.scalars().all()
            if artifacts:
                lines.append("\nProduced Artifacts (use these exact paths to open/edit files):")
                for a in artifacts[:10]:
                    v = "✓" if a.verified else "?"
                    # Show full path so Chat AI can reference it directly
                    full_path = a.path or "—"
                    entry = f"  {v} {a.name} ({a.artifact_type}) → {full_path}"
                    lines.append(entry[:200])
                if len(artifacts) > 10:
                    lines.append(f"  … and {len(artifacts) - 10} more")

            # ── Workspace files (capped at 8) ─────────────────────────────────
            try:
                run_dir = Path(settings.syncnode_demo_workspace) / "runs" / run_id
                if not run_dir.exists():
                    run_dir = Path(settings.syncnode_workspace_root) / "runs" / run_id
                if run_dir.exists():
                    doc_files = [
                        f for f in run_dir.rglob("*")
                        if f.is_file() and f.suffix in
                           (".docx", ".xlsx", ".pptx", ".txt", ".md", ".pdf", ".png")
                    ]
                    if doc_files:
                        lines.append("\nWorkspace Files:")
                        for f in doc_files[:8]:
                            size_kb = f.stat().st_size // 1024
                            rel = str(f.relative_to(run_dir))
                            lines.append(f"  📄 {rel} ({size_kb}KB)"[:90])
            except Exception:
                pass

    except Exception as exc:
        logger.warning("[CHAT] run context load failed: %s", exc)
        return ""

    # ── Workflow memory (capped at 2 entries) ─────────────────────────────────
    try:
        from syncnode_backend.learning.memory import workflow_memory
        memories = await workflow_memory.best_strategies("general", limit=2)
        if memories:
            lines.append("\nWorkflow Memory (similar past runs):")
            for m in memories[:2]:
                seq = (getattr(m, "tool_sequence", None) or [])[:4]
                summary = getattr(m, "goal_summary", "—")[:80]
                lines.append(f"  • {summary} → [{', '.join(seq)}]")
    except Exception:
        pass

    result_str = "\n".join(lines)
    # Hard cap: if somehow still too long, truncate with notice
    if len(result_str) > 6000:
        result_str = result_str[:5950] + "\n  … [context truncated]"
    return result_str


# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """\
You are SyncNode, an agentic AI assistant running entirely locally on the user's machine.
You have FULL ACCESS to the local Windows PC and all its files.

CAPABILITIES:
- Read, write, search, and delete files ANYWHERE on the PC (system.fs_read/write/list/search/delete)
- Run any PowerShell or CMD command (system.shell)
- List and manage running processes (system.process_list / system.process_kill)
- Read/write clipboard (system.clipboard_get / system.clipboard_set)
- Read environment variables (system.env_get)
- Read Windows registry (system.registry_get)
- Create Word, Excel, PowerPoint documents (document.* / excel.* / powerpoint.*)
- Open ANY file in its application using TWO correct methods:

  METHOD A — Open by absolute path (PREFERRED for Chat, always works):
    computer.windows_search(query="<filename>", file_path="<absolute_path>")
    Examples:
      computer.windows_search(query="SyncNode_Data.xlsx", file_path="C:\\syncnode\\workspace\\demo\\runs\\<id>\\excel\\SyncNode_Data.xlsx")
      computer.windows_search(query="report.docx", file_path="C:\\Users\\...\\report.docx")
    This opens the file directly in its default app WITHOUT the Search UI.
    The file_path parameter is MANDATORY when opening a specific document.

  METHOD B — Open app then inject file (for run-internal orchestrated workflows only):
    computer.launch_app(executable="excel", args=["<absolute_path>"])
    computer.launch_app(executable="word",  args=["<absolute_path>"])
    computer.launch_app(executable="powerpnt", args=["<absolute_path>"])
    Examples:
      computer.launch_app(executable="excel", args=["C:\\syncnode\\workspace\\...\\SyncNode_Data.xlsx"])
      computer.launch_app(executable="word",  args=["C:\\syncnode\\workspace\\...\\report.docx"])

  METHOD C — Smart shortcut (just pass the full file path as executable):
    computer.launch_app(executable="C:\\syncnode\\workspace\\...\\SyncNode_Data.xlsx")
    The tool auto-detects .xlsx/.docx/.pptx extensions and maps to the correct app.

  NEVER: computer.launch_app(executable="excel")  ← without args, opens blank Excel, NOT your file
  NEVER: computer.windows_search(query="SyncNode_Data.xlsx")  ← without file_path, opens Bing

- To find a file path first: system.fs_search(query="SyncNode_Data.xlsx", search_path="C:\\syncnode\\workspace")
  Then use the returned path in METHOD A or B.

- Control Windows apps via UI Automation after opening:
    computer.uia_type(text="content", window_title="Excel", wait_ready_ms=3000)
    computer.uia_click(window_title="Excel", name="Save")
    computer.key_press(keys="{Ctrl}s")  ← save
    computer.key_press(keys="{Ctrl}w")  ← close current workbook in Excel
    computer.key_press(keys="{Alt}{F4}") ← close app

CRITICAL — editing Excel/Word files that are currently OPEN:
  openpyxl/python-docx cannot write a file while Office has it open (Permission denied).
  Before calling excel.write_range or excel.write_cell on an open file, you MUST close it first:
    computer.key_press(keys="{Ctrl}w")   ← closes the workbook in Excel
  Then write: excel.write_range(path="...", start_cell="A10", rows=[...])
  Then re-open: computer.windows_search(query="Battery_Data.xlsx", file_path="...")
  
  PATTERN for editing an open Excel file:
    1. computer.key_press(keys="{Ctrl}w") → close workbook
    2. excel.write_range(path="...", start_cell="A10", rows=[["China", "Export", "LFP"], ...])
    3. computer.windows_search(query="Battery_Data.xlsx", file_path="<path>") → re-open

- Search Windows taskbar for apps (computer.windows_search with query only, no file_path)
- Control Chromium browser (browser.*)

CORRECT PATTERN — "open the Excel file and add data":
  Step 1: system.fs_search(query="SyncNode_Data.xlsx", search_path="C:\\syncnode\\workspace") → get path
  Step 2: computer.windows_search(query="SyncNode_Data.xlsx", file_path="<path from step 1>") → opens in Excel
  Step 3: computer.uia_type(text="new data", window_title="Excel", wait_ready_ms=3000) → types into Excel
  Step 4: computer.key_press(keys="{Ctrl}s") → saves

SAFETY RAILS (built into the tools — you don't need to worry about these):
- fs_delete and process_kill default to DRY RUN — always show the dry-run result first
- shell commands that format drives, modify bootloader, or do mass-delete are blocked
- Writes to C:\\Windows and Program Files are blocked

When the user asks you to DO something, use the tools to actually do it.
After every tool call, summarise what happened clearly.
Be direct, powerful, and action-oriented.
Think locally. Act intelligently. You have the full machine.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────────────────────

def _get_chat_tools() -> list[dict]:
    from syncnode_backend.tools.registry import tool_registry
    allowed = {
        "document.create_docx", "document.inspect_docx", "document.read_docx",
        "excel.create", "excel.write_cell", "excel.write_range", "excel.read_cell",
        "excel.read_range", "excel.inspect",
        "powerpoint.create", "powerpoint.add_slide", "powerpoint.inspect",
        "filesystem.write", "filesystem.find", "filesystem.hash",
        "writer.generate_paragraph",
        "computer.screenshot", "computer.windows_search",
        "computer.launch_app", "computer.get_active_window",
        "computer.uia_type", "computer.uia_click", "computer.key_press",
        # Full system access
        "system.fs_read", "system.fs_list", "system.fs_search",
        "system.fs_write", "system.fs_delete",
        "system.shell",
        "system.process_list", "system.process_kill",
        "system.clipboard_get", "system.clipboard_set",
        "system.env_get", "system.registry_get",
    }
    tools = []
    for defn in tool_registry.all_enabled():
        if defn.key in allowed:
            fn_name = defn.key.replace(".", "_")
            props: dict[str, Any] = {}
            for k, v in defn.input_schema.items():
                props[k] = {"type": "string", "description": str(v)}
            tools.append({
                "type": "function",
                "function": {
                    "name": fn_name,
                    "description": defn.description,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": list(defn.required_args()),
                    },
                },
            })

    # Extra: workflow step injection (virtual tool — handled specially)
    tools.append({
        "type": "function",
        "function": {
            "name": "workflow_add_step",
            "description": (
                "Add a new step to the currently running workflow. "
                "Use this when the user asks to extend, modify, or add to the active run."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Tool key to execute (e.g. document.create_docx)"},
                    "description": {"type": "string", "description": "Human-readable description of what this step does"},
                    "inputs": {"type": "object", "description": "Input arguments for the tool"},
                },
                "required": ["action", "description"],
            },
        },
    })
    return tools


# ─────────────────────────────────────────────────────────────────────────────
# Tool execution
# ─────────────────────────────────────────────────────────────────────────────

async def _execute_tool(
    tool_name: str, tool_args: dict, run_id: Optional[str] = None
) -> dict[str, Any]:
    from syncnode_backend.tools.registry import tool_registry

    # Handle workflow step injection
    if tool_name == "workflow_add_step":
        if not run_id:
            return {"success": False, "error": "No active run to add step to"}
        return await _inject_workflow_step(run_id, tool_args)

    # Map function name back to tool key
    key = tool_name
    all_enabled = {d.key for d in tool_registry.all_enabled()}
    if key not in all_enabled:
        for defn in tool_registry.all_enabled():
            if defn.key.replace(".", "_") == tool_name:
                key = defn.key
                break

    try:
        result = await tool_registry.invoke(key, tool_args, agent_allowed_tools=list(all_enabled))
        return {"success": True, "tool": key, "result": result}
    except Exception as exc:
        logger.warning("[CHAT] tool %s failed: %s", key, exc)
        return {"success": False, "tool": key, "error": str(exc)}


async def _inject_workflow_step(run_id: str, args: dict) -> dict[str, Any]:
    """Inject a new step into a running workflow.

    Uses the real /inject-step endpoint which appends to the live orch._plan
    so the step actually executes through the normal ExecutionEngine pipeline.
    Falls back to an SSE notification-only event if the run is not live.
    """
    from syncnode_backend.api.v1.runs import _live_orchestrators, emit_sse_event
    from syncnode_backend.tools.registry import tool_registry
    from syncnode_ai.agents.registry import agent_registry

    action = str(args.get("action", "")).strip()
    description = str(args.get("description", "Chat-injected step")).strip()
    inputs = args.get("inputs") or {}
    if not isinstance(inputs, dict):
        inputs = {}

    if not action:
        return {"success": False, "error": "action is required"}

    orch = _live_orchestrators.get(run_id)
    if orch is not None and orch._plan is not None:
        # --- Live path: append to the real plan ---
        import uuid as _uuid

        # Resolve agent
        agent_key = None
        for a in agent_registry.all_enabled():
            if action in a.allowed_tools:
                agent_key = a.agent_id
                break
        if not agent_key:
            return {"success": False, "error": f"No agent found for action '{action}'"}

        # Validate tool
        try:
            tool_registry.require(action)
        except Exception as e:
            return {"success": False, "error": f"Unknown tool '{action}': {e}"}

        from syncnode_ai.planner.schemas import PlanStep, Postcondition
        new_step = PlanStep(
            step_key=f"chat_{_uuid.uuid4().hex[:8]}",
            action=action,
            description=description,
            agent_key=agent_key,
            inputs=inputs,
            postconditions=[Postcondition(assertion_type="file_exists", target="")],
            dependencies=[],
            requires_approval=False,
        )
        step_idx = len(orch._plan.steps)
        orch._plan.steps.append(new_step)
        orch._plan_step_status[step_idx] = "pending"
        orch._plan.total_steps = len(orch._plan.steps)

        await emit_sse_event(run_id, "plan.step_injected", {
            "step_key": new_step.step_key,
            "action": action,
            "description": description,
            "injected_by": "chat",
        })
        logger.info("[CHAT] live step injected run=%s action=%s step=%s",
                    run_id, action, new_step.step_key)
        return {
            "success": True,
            "message": f"Step '{description}' ({action}) injected into the live workflow.",
            "step_key": new_step.step_key,
            "step_index": step_idx,
            "note": "Will execute at the next wave dispatch.",
        }
    else:
        # --- Non-live path: emit notification only ---
        await emit_sse_event(run_id, "chat.step_requested", {
            "action": action,
            "description": description,
            "inputs": inputs,
            "note": "Run is not currently live — step could not be injected automatically.",
        })
        return {
            "success": False,
            "error": "Run is not currently executing. Step was noted but cannot be injected.",
            "hint": "Start or resume the run first, then ask again.",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Context summarizer (gemma3:1b, CPU, unloads immediately)
# ─────────────────────────────────────────────────────────────────────────────

async def _summarize_history(messages: list[dict]) -> str:
    from syncnode_ai.gateway.gateway import ModelGateway
    from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
    from syncnode_ai.gateway.schemas import Message, ModelRequest

    adapter = OllamaAdapter(
        base_url=settings.ollama_base_url,
        timeout=60.0,
        default_num_ctx=2048,
        default_num_gpu=0,
        default_keep_alive="0",
    )
    gateway = ModelGateway(adapter=adapter, model_id="gemma3:1b")
    try:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in messages if m["role"] in ("user", "assistant")
        )
        req = ModelRequest(
            model_id="gemma3:1b",
            messages=[
                Message(role="system", content="Summarize this conversation in 2-3 sentences. Return only the summary."),
                Message(role="user", content=f"Summarize:\n\n{history_text}"),
            ],
            temperature=0.0, num_gpu=0, keep_alive="0", caller="chat.summarizer",
        )
        async with scheduler.model_slot(agent_id="chat_summarizer"):
            resp = await gateway.generate(req)
        return resp.content.strip()
    except Exception as exc:
        logger.warning("[CHAT] summarizer failed: %s", exc)
        return ""
    finally:
        await adapter.close()


# ─────────────────────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str = "New Chat"
    run_id: Optional[str] = None   # attach to a specific run for full context


class SendMessageRequest(BaseModel):
    content: str
    enable_tools: bool = True
    run_id: Optional[str] = None        # override/attach run context per-message
    document_context: Optional[str] = None  # pre-parsed document text injected as context
    document_name: Optional[str] = None     # filename shown in the system prompt


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat/sessions")
async def create_session(req: CreateSessionRequest) -> dict:
    sid = str(uuid.uuid4())
    async with get_session() as db:
        db.add(ChatSession(id=sid, title=req.title, run_id=req.run_id))
    return {"session_id": sid, "title": req.title, "run_id": req.run_id, "created_at": time.time()}


@router.get("/chat/sessions")
async def list_sessions() -> dict:
    async with get_session() as db:
        result = await db.execute(
            select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50)
        )
        sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "session_id": s.id,
                "title": s.title,
                "run_id": s.run_id,
                "message_count": s.message_count,
                "summary": s.summary,
                "created_at": s.created_at.timestamp() if s.created_at else None,
                "updated_at": s.updated_at.timestamp() if s.updated_at else None,
            }
            for s in sessions
        ]
    }


@router.get("/chat/sessions/{session_id}")
async def get_session_detail(session_id: str) -> dict:
    async with get_session() as db:
        sess = await db.get(ChatSession, session_id)
        if not sess:
            raise HTTPException(404, "Session not found")
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.seq)
        )
        msgs = result.scalars().all()
    return {
        "session_id": sess.id,
        "title": sess.title,
        "summary": sess.summary,
        "message_count": sess.message_count,
        "created_at": sess.created_at.timestamp() if sess.created_at else None,
        "messages": [
            {
                "message_id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls or [],
                "tool_results": m.tool_results or [],
                "seq": m.seq,
                "created_at": m.created_at.timestamp() if m.created_at else None,
            }
            for m in msgs
        ],
    }


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    async with get_session() as db:
        sess = await db.get(ChatSession, session_id)
        if not sess:
            raise HTTPException(404, "Session not found")
        for m in (await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )).scalars().all():
            await db.delete(m)
        await db.delete(sess)
    return {"deleted": True}


@router.post("/chat/sessions/{session_id}/clear")
async def clear_session(session_id: str) -> dict:
    async with get_session() as db:
        sess = await db.get(ChatSession, session_id)
        if not sess:
            raise HTTPException(404, "Session not found")
        for m in (await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )).scalars().all():
            await db.delete(m)
        sess.message_count = 0
        sess.summary = None
    return {"cleared": True}


@router.get("/chat/sessions/{session_id}/run-context")
async def get_run_context_for_session(session_id: str, run_id: str) -> dict:
    ctx = await _build_run_context(run_id)
    return {"session_id": session_id, "run_id": run_id, "context": ctx}


@router.post("/chat/sessions/{session_id}/stream")
async def chat_stream(session_id: str, req: SendMessageRequest):
    """
    Stream SSE response for a chat message.

    SSE event shapes:
      {"type":"delta",       "content":"<token>"}
      {"type":"tool_start",  "tool":"<key>", "args":{}}
      {"type":"tool_result", "tool":"<key>", "success":bool, "result":"<text>"}
      {"type":"summary",     "text":"<summary>"}
      {"type":"status",      "text":"<info>"}
      {"type":"done",        "message_id":"<id>", "usage":{"in":N,"out":N}}
      {"type":"error",       "message":"<err>"}
    """
    async with get_session() as db:
        if not await db.get(ChatSession, session_id):
            raise HTTPException(404, "Session not found")

    async def generate():
        from syncnode_ai.gateway.gateway import ModelGateway
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        from syncnode_ai.gateway.schemas import Message, ModelRequest, ToolSchema as GWToolSchema

        def _sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # ── Load history ─────────────────────────────────────────────────
            async with get_session() as db:
                rows = (await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.seq)
                )).scalars().all()
                sess = await db.get(ChatSession, session_id)
                current_summary = sess.summary if sess else None

            history = [{"role": m.role, "content": m.content} for m in rows]
            summary_text = current_summary or ""

            # ── Context summarization if needed ──────────────────────────────
            if len(history) >= CONTEXT_TURN_LIMIT * 2:
                to_summarize = history[:-SUMMARY_KEEP_TURNS * 2]
                history = history[-SUMMARY_KEEP_TURNS * 2:]
                if to_summarize:
                    yield _sse({"type": "status", "text": "Summarizing conversation context…"})
                    summary_text = await _summarize_history(to_summarize)
                    if summary_text:
                        async with get_session() as db:
                            s = await db.get(ChatSession, session_id)
                            if s:
                                s.summary = summary_text
                        yield _sse({"type": "summary", "text": summary_text})

            # ── Persist user message ──────────────────────────────────────────
            user_msg_id = str(uuid.uuid4())
            async with get_session() as db:
                s = await db.get(ChatSession, session_id)
                seq = (s.message_count or 0) + 1
                db.add(ChatMessage(
                    id=user_msg_id, session_id=session_id,
                    role="user", content=req.content, seq=seq,
                ))
                if s:
                    s.message_count = seq

            history.append({"role": "user", "content": req.content})

            # ── Build workflow run context ────────────────────────────────────
            # Use per-request run_id first; fall back to the session's bound run_id
            run_id = req.run_id
            if not run_id and sess:
                run_id = getattr(sess, "run_id", None)
            run_ctx_text = ""
            if run_id:
                yield _sse({"type": "status", "text": "Loading workflow context…"})
                run_ctx_text = await _build_run_context(run_id)

            # ── System prompt ─────────────────────────────────────────────────
            system_parts = [BASE_SYSTEM_PROMPT]
            if summary_text:
                system_parts.append(f"\n[CONVERSATION SUMMARY]\n{summary_text}")
            if run_ctx_text:
                system_parts.append(f"\n{run_ctx_text}")
            # Document context injected from the client (pre-parsed uploaded file)
            if req.document_context:
                doc_label = req.document_name or "uploaded document"
                doc_text  = req.document_context[:12_000]
                if len(req.document_context) > 12_000:
                    doc_text += f"\n… [truncated — {len(req.document_context)} chars total]"
                system_parts.append(
                    f"\n[ATTACHED DOCUMENT: {doc_label}]\n"
                    "The user has attached this document to the conversation. "
                    "Read it carefully — you may be asked to summarise it, answer questions about it, "
                    "transform its content, or use it inside a workflow.\n"
                    f"--- BEGIN DOCUMENT ---\n{doc_text}\n--- END DOCUMENT ---"
                )
            system_content = "\n".join(system_parts)

            # ── Build model messages ──────────────────────────────────────────
            model_messages: list[Message] = [Message(role="system", content=system_content)]
            for m in history[:-1]:
                if m["role"] in ("user", "assistant"):
                    model_messages.append(Message(role=m["role"], content=m["content"]))
            model_messages.append(Message(role="user", content=req.content))

            # ── Tools ─────────────────────────────────────────────────────────
            gateway_tools: list[GWToolSchema] = []
            if req.enable_tools:
                for t in _get_chat_tools():
                    fn = t["function"]
                    gateway_tools.append(GWToolSchema(
                        name=fn["name"],
                        description=fn["description"],
                        parameters=fn.get("parameters", {}),
                    ))

            # ── Gateway ───────────────────────────────────────────────────────
            adapter = OllamaAdapter(
                base_url=settings.ollama_base_url,
                timeout=float(settings.syncnode_model_timeout),
                default_num_ctx=16384,
                default_num_gpu=settings.syncnode_gpu_layers,
                default_keep_alive=settings.syncnode_keep_alive,
            )
            gateway = ModelGateway(adapter=adapter, model_id=settings.syncnode_model_id)

            # ── Agentic loop ──────────────────────────────────────────────────
            full_response = ""
            tool_calls_made: list[dict] = []
            tool_results_list: list[dict] = []
            in_tokens = out_tokens = 0

            for _round in range(5):
                req_obj = ModelRequest(
                    model_id=settings.syncnode_model_id,
                    messages=model_messages,
                    tools=gateway_tools,
                    temperature=0.7,
                    max_tokens=3000,   # generous for conversational + tool result summaries
                    caller="chat",
                )

                pending_tcs: list[dict] = []
                round_text = ""

                async with scheduler.model_slot(agent_id="chat"):
                    async for event in gateway.stream(req_obj):
                        if event.event_type == "delta" and event.delta:
                            round_text += event.delta
                            full_response += event.delta
                            yield _sse({"type": "delta", "content": event.delta})
                        elif event.event_type == "tool_call" and event.tool_call:
                            pending_tcs.append(event.tool_call)
                        elif event.event_type == "done":
                            in_tokens += event.input_tokens
                            out_tokens += event.output_tokens

                if not pending_tcs:
                    break

                model_messages.append(Message(role="assistant", content=round_text or ""))

                for tc in pending_tcs:
                    fn = tc.get("function", tc)
                    tname = fn.get("name", "")
                    raw_args = fn.get("arguments", fn.get("args", {}))
                    targs = raw_args if isinstance(raw_args, dict) else {}

                    yield _sse({"type": "tool_start", "tool": tname, "args": targs})

                    result = await _execute_tool(tname, targs, run_id=run_id)
                    tool_calls_made.append({"tool": tname, "args": targs})
                    tool_results_list.append(result)

                    result_text = json.dumps(
                        result.get("result", result), ensure_ascii=False
                    )[:600]
                    yield _sse({
                        "type": "tool_result",
                        "tool": tname,
                        "success": result["success"],
                        "result": result_text,
                    })

                    model_messages.append(Message(
                        role="tool",
                        content=f"Tool {tname} returned: {result_text[:800]}",
                    ))

            # ── Persist assistant message ─────────────────────────────────────
            # If the model only called tools and emitted no text, generate a
            # brief summary so the chat bubble never stays stuck on "...".
            if not full_response.strip() and tool_calls_made:
                failed_tools = [r for r in tool_results_list if not r.get("success")]
                succeeded_tools = [r for r in tool_results_list if r.get("success")]
                if failed_tools:
                    hints = []
                    for r in failed_tools:
                        inner = r.get("result", r)
                        if isinstance(inner, dict):
                            hint = inner.get("hint") or inner.get("error") or ""
                        else:
                            hint = str(inner)[:200]
                        if hint:
                            hints.append(hint)
                    summary = f"The operation failed. {' '.join(hints)}" if hints else \
                              f"Tool call failed: {failed_tools[0].get('tool', 'unknown')}"
                else:
                    names = [r.get("tool", "tool") for r in succeeded_tools[:3]]
                    summary = f"Done — {', '.join(names)} completed successfully."
                full_response = summary
                yield _sse({"type": "delta", "content": summary})
            asst_id = str(uuid.uuid4())
            async with get_session() as db:
                s = await db.get(ChatSession, session_id)
                seq2 = (s.message_count or 0) + 1
                db.add(ChatMessage(
                    id=asst_id, session_id=session_id,
                    role="assistant", content=full_response,
                    tool_calls=tool_calls_made or None,
                    tool_results=tool_results_list or None,
                    seq=seq2,
                ))
                if s:
                    s.message_count = seq2
                    if s.title == "New Chat" and req.content:
                        s.title = req.content[:60] + ("…" if len(req.content) > 60 else "")

            await adapter.close()
            yield _sse({"type": "done", "message_id": asst_id,
                        "usage": {"in": in_tokens, "out": out_tokens}})

        except Exception as exc:
            logger.exception("[CHAT] stream error: %s", exc)
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")
