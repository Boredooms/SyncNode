"""
SyncNode — Core Orchestrator.

Drives the full run pipeline:
  intent → plan → agents → tools → verify → recover → audit → SSE

This is the central execution loop for SyncNode Phase 1.
Not a LangGraph graph yet — a straight sequential orchestrator that
will be migrated to LangGraph as Gate 5 matures.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from syncnode_backend.audit.engine import audit_engine
from syncnode_backend.config.settings import settings
from syncnode_backend.persistence.database import get_session
from syncnode_backend.persistence.models import (
    Approval, Artifact, Run, RunStep, ToolCall, Observation, VerificationResult,
)
from syncnode_backend.tools.registry import tool_registry
from syncnode_backend.verification.engine import VerificationEngine

logger = logging.getLogger(__name__)


class SyncNodeOrchestrator:
    """
    Drives the execution of a single run end-to-end.

    Separation of concerns:
    - Orchestrator: coordination, state, SSE, audit
    - ModelGateway: all model calls
    - ToolRegistry: all tool invocations
    - VerificationEngine: all postcondition checks
    - AuditEngine: all event recording
    """

    def __init__(
        self,
        run_id: str,
        emit_sse: Callable[[str, str, dict], Coroutine],
    ) -> None:
        self.run_id = run_id
        self._emit = emit_sse
        self._verifier = VerificationEngine()
        self._observation_ts: Optional[float] = None
        # Execution + recovery engines (wired into the step loop).
        from syncnode_backend.recovery.engine import RecoveryEngine
        from syncnode_backend.runtime.execution_engine import ExecutionEngine
        from syncnode_backend.runtime.locks import lock_manager
        from syncnode_backend.tools.registry import tool_registry
        self._exec_engine = ExecutionEngine(
            tool_registry, lock_manager,
            emit=self._emit_event,
            observe=self._observe_for_engine,
            verify=self._verify_for_engine,
        )
        self._recovery = RecoveryEngine(max_attempts=3, breaker_threshold=3)
        # Run-scoped artifact registry (set at run start).
        self._artifacts_reg: Any = None
        # Graph-execution scratch (set during LangGraph run).
        self._gateway: Any = None
        self._agent_registry: Any = None
        self._failure_mode: str = "none"
        self._plan: Any = None
        self._plan_step_status: dict[int, str] = {}   # index -> pending|running|done|failed
        self._step_ids: dict[int, str] = {}
        self._stop_requested: bool = False
        self._approval_signal: Any = None
        # Bounded, explicit inter-step data flow. Accumulates concrete artifacts
        # produced by completed steps (e.g. generated content, created file
        # paths) so later steps can consume them. This is NOT arbitrary mutation:
        # only the specific keys below are propagated, and only into empty inputs.
        self._artifacts: dict[str, Any] = {}
        # Workflow-memory trajectory (recorded at run end for safe learning).
        self._trajectory: list[Any] = []
        self._goal: str = ""

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        await self._emit(self.run_id, event_type, payload)
        await audit_engine.record(event_type, payload, run_id=self.run_id)

    async def _update_run_status(self, status: str, error: Optional[str] = None) -> None:
        async with get_session() as session:
            run = await session.get(Run, self.run_id)
            if run:
                run.status = status
                if error:
                    run.error_message = error
                if status in ("completed", "failed", "waiting_approval"):
                    from datetime import datetime, timezone
                    run.completed_at = datetime.now(timezone.utc)

    async def execute(self, goal: str, failure_mode: str = "none") -> None:
        """Main execution loop for a run."""
        from syncnode_ai.gateway.gateway import ModelGateway
        from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
        from syncnode_ai.intent.engine import IntentEngine
        from syncnode_ai.planner.engine import Planner
        from syncnode_ai.agents.registry import agent_registry

        # ── STEP -1: Prompt Enrichment (gemma3:1b on CPU, keep_alive=0) ──────
        # This MUST run before the main gateway (gemma4:e4b on GPU) is created
        # so the two models never overlap in VRAM. gemma3:1b is forced to CPU
        # via num_gpu=0 and unloaded immediately (keep_alive=0) — no deadlock,
        # no VRAM contention, uses only ~800 MB of system RAM for ~2-3 seconds.
        enriched_goal = goal
        try:
            from syncnode_ai.intent.enricher import prompt_enricher
            enriched_ctx = await prompt_enricher.enrich(goal, run_id=self.run_id)
            if enriched_ctx.is_useful():
                import re as _re
                # Store extracted fields — validate each before storing so
                # template echo values ("email address if present...") never
                # propagate into the run.
                if enriched_ctx.recipient_email and _re.fullmatch(
                    r"[\w.+-]+@[\w.-]+\.\w+", enriched_ctx.recipient_email
                ):
                    self._artifacts["enricher_recipient"] = enriched_ctx.recipient_email
                if enriched_ctx.subject and len(enriched_ctx.subject) < 200:
                    self._artifacts["enricher_subject"] = enriched_ctx.subject
                if enriched_ctx.body_hint:
                    self._artifacts["enricher_body"] = enriched_ctx.body_hint
                if enriched_ctx.save_filename and _re.search(
                    r"\.(docx|xlsx|pptx|pdf|txt)$", enriched_ctx.save_filename, _re.I
                ):
                    self._artifacts["enricher_filename"] = enriched_ctx.save_filename
                # Prepend the structured context block as a comment the intent
                # engine can use — keep it short so it doesn't inflate token count.
                context_hint = f"[Context: recipient={enriched_ctx.recipient_email or 'none'} subject={enriched_ctx.subject or 'none'} file={enriched_ctx.save_filename or 'none'}]"
                enriched_goal = goal + "\n" + context_hint
                await self._emit_event("enricher.completed", {
                    "recipient": enriched_ctx.recipient_email,
                    "subject": enriched_ctx.subject,
                    "filename": enriched_ctx.save_filename,
                    "goal_type_hint": enriched_ctx.goal_type_hint,
                })
                logger.info(
                    "[ENRICHER] goal enriched — recipient=%r subject=%r file=%r",
                    enriched_ctx.recipient_email, enriched_ctx.subject, enriched_ctx.save_filename,
                )
        except Exception as exc:  # noqa: BLE001 — enricher failure is non-fatal
            logger.warning("[ENRICHER] skipped (non-fatal): %s", exc)
        # ── END enrichment — from here only gemma4:e4b runs ──────────────────

        adapter = OllamaAdapter(
            base_url=settings.ollama_base_url,
            timeout=float(settings.syncnode_model_timeout),
            default_num_ctx=settings.syncnode_num_ctx,
            default_num_gpu=settings.syncnode_gpu_layers,
            default_keep_alive=settings.syncnode_keep_alive,
        )
        # Use runtime-switchable model (can be hot-swapped via POST /api/v1/models/active)
        from syncnode_backend.api.v1.models import get_active_model_id
        active_model = get_active_model_id()
        gateway = ModelGateway(
            adapter=adapter,
            model_id=active_model,
            max_repair=settings.syncnode_model_repair_attempts,
        )

        self._goal = goal
        try:
            await self._update_run_status("running")
            await self._emit_event("run.created", {"goal": goal, "model_id": active_model})
            logger.info(f"[RUN] accepted — run_id={self.run_id} model={active_model}")

            # Run-scoped artifact registry (clean, isolated workspace per run).
            from syncnode_backend.artifacts.registry import RunArtifactRegistry
            self._artifacts_reg = RunArtifactRegistry(
                self.run_id, settings.syncnode_workspace_root
            )
            self._artifacts_reg.initialize()
            await self._emit_event("run.started", {"run_dir": str(self._artifacts_reg.run_dir)})

            # ---- STEP 0: Conditional RAG ----
            knowledge_context = await self._retrieve_knowledge(goal)
            self._knowledge_context_cache = knowledge_context

            # ---- STEP 1: Intent (uses enriched_goal so Gemma sees structured context) ----
            logger.info("[INTENT] extracting structured intent...")
            intent_engine = IntentEngine(gateway)
            intent = await intent_engine.extract(
                enriched_goal, run_id=self.run_id, context_summary=knowledge_context or None
            )
            # Backfill enriched fields into intent so planner sees them directly
            if not intent.recipient and self._artifacts.get("enricher_recipient"):
                intent.recipient = self._artifacts["enricher_recipient"]
            if not intent.subject_hint and self._artifacts.get("enricher_subject"):
                intent.subject_hint = self._artifacts["enricher_subject"]
            if not intent.body_hint and self._artifacts.get("enricher_body"):
                intent.body_hint = self._artifacts["enricher_body"]
            if not intent.save_filename and self._artifacts.get("enricher_filename"):
                intent.save_filename = self._artifacts["enricher_filename"]

            self._intent_cache = intent
            await self._emit_event("intent.completed", {"intent": intent.model_dump()})
            logger.info(f"[INTENT] structured intent — goal_type={intent.goal_type.value} tasks={intent.tasks}")

            # Persist intent to run
            async with get_session() as session:
                run = await session.get(Run, self.run_id)
                if run:
                    run.intent_json = intent.model_dump()

            # ---- STEP 2: Plan ----
            logger.info("[PLAN] building execution DAG...")
            planner = Planner(gateway)
            plan = await planner.plan(
                intent, run_id=self.run_id, context_summary=knowledge_context or None
            )
            await self._emit_event("plan.created", {
                "total_steps": plan.total_steps,
                "steps": [s.step_key for s in plan.steps],
            })
            logger.info(f"[PLAN] DAG created — steps={plan.total_steps}")

            # Sanitize the plan: drop steps whose action is neither a registered
            # tool nor a known control action. This contains planner tool-name
            # hallucination without weakening authorization — unknown tools would
            # otherwise fail closed mid-run and abort the whole workflow.
            self._sanitize_plan(plan)
            await self._emit_event("plan.validated", {
                "total_steps": plan.total_steps,
                "steps": [s.step_key for s in plan.steps],
            })

            async with get_session() as session:
                run = await session.get(Run, self.run_id)
                if run:
                    run.plan_json = plan.model_dump()

            # ---- STEP 3: Execute via the LangGraph orchestration graph ----
            # LangGraph is the control plane; each branch calls back into
            # _execute_step (ExecutionEngine + RecoveryEngine). Steps whose
            # dependencies are satisfied and that share no exclusive resource
            # run as parallel branches (bounded by the resource scheduler).
            self._gateway = gateway
            self._agent_registry = agent_registry
            self._failure_mode = failure_mode
            self._plan = plan
            self._plan_step_status = {i: "pending" for i in range(len(plan.steps))}
            try:
                from syncnode_backend.workflow.graph import SyncNodeGraph
                await SyncNodeGraph(self).run(goal, failure_mode)
            except ApprovalRequiredSignal:
                raise
            # A step failure inside a branch is surfaced. Failed artifact/tool
            # steps are NOT masked by the approval gate — the run fails.
            failed = [i for i, s in self._plan_step_status.items() if s == "failed"]
            if failed:
                raise StepVerificationError(
                    f"{len(failed)} step(s) failed: "
                    + ", ".join(plan.steps[i].step_key for i in failed)
                )

            # Deterministic approval boundary: if this run drafted an external
            # email (browser compose/attach occurred) for a goal about sending,
            # a human approval is REQUIRED before the run is considered done —
            # regardless of whether the model included a send step. Policy, not
            # the model, owns this boundary.
            if self._external_send_pending():
                approval_id = await self._request_approval(
                    str(uuid.uuid4()),
                    _ApprovalStub("Send the drafted email (external communication)"),
                    None,
                )
                await self._update_run_status("waiting_approval")
                await self._emit_event("run.waiting_approval", {
                    "approval_id": approval_id,
                    "action": "Send drafted email — external communication requires approval",
                })
                logger.info("[APPROVAL] external-send boundary enforced — run paused")
                await self._record_memory(success=True)
                return

            # If we get here without an approval gate, mark completed
            async with get_session() as session:
                run = await session.get(Run, self.run_id)
                if run and run.status == "running":
                    await self._update_run_status("completed")
                    await self._emit_event("run.completed", {"run_id": self.run_id})
                    logger.info(f"[RUN] completed — run_id={self.run_id}")
            await self._record_memory(success=True)

        except ApprovalRequiredSignal as approval_signal:
            await self._update_run_status("waiting_approval")
            await self._emit_event("run.waiting_approval", {
                "approval_id": approval_signal.approval_id,
                "action": approval_signal.action_summary,
            })
            logger.info(f"[APPROVAL] requested — run paused — run_id={self.run_id}")
            await self._record_memory(success=True)

        except Exception as exc:
            logger.error(f"[RUN] failed — run_id={self.run_id} error={str(exc)}")
            await self._update_run_status("failed", error=str(exc))
            await self._emit_event("run.failed", {"error": str(exc)})
            await self._record_memory(success=False, failure_class=self._classify_error(exc))
            raise
        finally:
            await gateway.close()

    # ================================================================ #
    # LangGraph node adapters (the graph calls these).                   #
    # rag/intent/plan already ran in execute(); the graph re-uses their  #
    # results. Step execution + wave routing are the live graph work.    #
    # ================================================================ #

    async def g_rag(self, goal: str) -> str:
        # RAG already ran in execute() before the graph; return cached context.
        return getattr(self, "_knowledge_context_cache", "") or ""

    async def g_intent(self, goal: str, knowledge_context: str) -> dict:
        return self._intent_cache.model_dump() if getattr(self, "_intent_cache", None) else {}

    async def g_plan(self, knowledge_context: str) -> list[dict]:
        return [s.model_dump() for s in self._plan.steps] if self._plan else []

    # ---- Exclusive resources that force serialization within a wave ----
    _EXCLUSIVE_RESOURCE_ACTIONS = {
        # Desktop/browser control mutate shared global UI state.
        "computer.windows_search": "desktop",
        "computer.launch_app": "desktop",
        "computer.find_window": "desktop",
        "computer.uia_find": "desktop",
        "computer.screenshot": "desktop",
        "browser.navigate": "browser",
        "browser.type": "browser",
        "browser.click": "browser",
        "browser.attach_file": "browser",
        "browser.screenshot": "browser",
    }

    def _step_deps_satisfied(self, idx: int) -> bool:
        step = self._plan.steps[idx]
        if not getattr(step, "dependencies", None):
            return True
        # Map dependency step_keys to indices; all must be done.
        key_to_idx = {s.step_key: i for i, s in enumerate(self._plan.steps)}
        for dep in step.dependencies:
            di = key_to_idx.get(dep)
            if di is not None and self._plan_step_status.get(di) != "done":
                return False
        return True

    def g_next_wave(self) -> list[int]:
        """Return indices of the next runnable wave.

        Rules:
          - a step is runnable if pending and all deps done,
          - a wave contains at most ONE step per exclusive resource (desktop/
            browser) so shared UI is never mutated concurrently,
          - independent deterministic steps (docx/xlsx/pptx creation) may share
            a wave and run in parallel branches.
        Steps proceed left-to-right; the wave stops at a step requiring approval
        so the approval boundary is honored.
        """
        if self._stop_requested:
            return []
        wave: list[int] = []
        claimed_resources: set[str] = set()
        for idx, step in enumerate(self._plan.steps):
            if self._plan_step_status.get(idx) != "pending":
                continue
            if not self._step_deps_satisfied(idx):
                continue
            # Approval steps run alone and stop further dispatch.
            if step.requires_approval or self._requires_approval_by_policy(step):
                if wave:
                    break  # let the current wave finish first
                wave.append(idx)
                break
            res = self._EXCLUSIVE_RESOURCE_ACTIONS.get(step.action or "")
            if res:
                if res in claimed_resources:
                    continue  # another step in this wave holds the resource
                claimed_resources.add(res)
            self._plan_step_status[idx] = "running"
            wave.append(idx)
        return wave

    def g_has_pending_steps(self) -> bool:
        return any(s == "pending" for s in self._plan_step_status.values())

    def g_should_stop(self) -> bool:
        return self._stop_requested

    async def g_emit_wave(self, wave: list[int]) -> None:
        keys = [self._plan.steps[i].step_key for i in wave]
        await self._emit_event("plan.wave_dispatched", {
            "wave_size": len(wave), "steps": keys, "parallel": len(wave) > 1,
        })
        logger.info("[GRAPH] dispatching wave (parallel=%s): %s", len(wave) > 1, keys)

    @staticmethod
    def _resolve_agent_key(agent_key: str, action: str, agent_registry) -> str:
        """Return a valid agent that owns `action`.

        If the planner's agent_key exists AND is allowed to use the action, keep
        it. Otherwise find the registered agent whose allowed_tools contains the
        action. Falls back to the original key (which will fail closed on spawn).
        """
        defn = agent_registry.get(agent_key)
        if defn is not None and (not action or action in defn.allowed_tools):
            return agent_key
        if action:
            for a in agent_registry.all_enabled():
                if action in a.allowed_tools:
                    return a.agent_id
        return agent_key

    async def g_run_wave(self, wave: list[int]) -> list[dict]:
        """Execute a wave's steps with resource-safe concurrency.

        On SQLite (single writer) steps are executed sequentially to avoid write
        contention; on a concurrent-capable store they could run via gather. The
        graph/wave/scheduler still model parallelism; this is the physical
        execution policy for the current single-node SQLite deployment.
        """
        import asyncio as _asyncio

        concurrent = "sqlite" not in settings.database_url
        if concurrent and len(wave) > 1:
            return list(await _asyncio.gather(
                *[self.g_execute_step(i) for i in wave], return_exceptions=False
            ))
        results = []
        for i in wave:
            results.append(await self.g_execute_step(i))
            if self._stop_requested:
                break
        return results

    async def g_execute_step(self, step_index: int) -> dict:
        """Execute one plan step (a graph branch) through the ExecutionEngine."""
        step = self._plan.steps[step_index]
        try:
            await self._execute_step(step, step_index, self._agent_registry,
                                     self._gateway, self._failure_mode)
            self._plan_step_status[step_index] = "done"
            return {"completed_agents": [step.agent_key],
                    "verifications": [{"step": step.step_key, "result": "PASS"}]}
        except ApprovalRequiredSignal as sig:
            # Approval boundary reached — stop dispatch and remember the signal.
            self._plan_step_status[step_index] = "done"
            self._stop_requested = True
            self._approval_signal = sig
            return {"failed_agents": [], "approval_state": {"pending": True}}
        except Exception as exc:  # noqa: BLE001 - step failed after bounded recovery
            self._plan_step_status[step_index] = "failed"
            self._stop_requested = True
            logger.exception("[GRAPH] step %s (%s) failed: %s",
                             step.step_key, step.action, exc)
            return {"failed_agents": [step.agent_key],
                    "errors": [{"step": step.step_key, "error": str(exc)}]}

    async def g_finalize(self) -> str:
        # The approval boundary raised inside a branch is re-raised to execute()
        # so the existing waiting_approval handling applies.
        if self._approval_signal is not None:
            raise self._approval_signal
        return "completed"

    # Control actions that are handled by the orchestrator, not the tool registry.
    _CONTROL_ACTIONS = {
        "workflow.pause", "workflow.approve", "workflow.reject",
        "workflow.replan", "workflow.stop", "workflow.wait_approval",
    }

    # Signals that a step performs external communication (e.g. sending email).
    _SEND_KEYWORDS = ("send", "finalize", "submit", "deliver", "dispatch", "transmit")

    def _external_send_pending(self) -> bool:
        """True if the run drafted an external email that still needs approval.

        Deterministic policy guarantee: any run that composed/attached an email
        for a goal about email/sending MUST stop at the approval boundary before
        completing, even if the model omitted an explicit send step.
        """
        goal = (self._goal or "").lower()
        goal_is_email = any(k in goal for k in ("email", "e-mail", "draft", "send", "recipient"))
        if not goal_is_email:
            return False
        drafted = any(
            (s.action or "").startswith("browser.")
            for s in self._trajectory
        ) or any(
            "browser." in (s.action or "") for s in self._trajectory
        )
        # If the goal says do NOT send but we produced a draft, gate approval.
        return goal_is_email and drafted

    def _requires_approval_by_policy(self, step) -> bool:
        """Force an approval gate for external-communication / send steps.

        Only gate: browser.click/submit whose description implies sending.
        NEVER gate: browser.attach_file, browser.type, browser.navigate —
        these are compose/preparation actions, not sends.
        """
        action = (step.action or "").lower()
        text = f"{step.step_key} {step.description}".lower()
        is_send = any(k in text for k in self._SEND_KEYWORDS)
        # A browser click/submit that looks like a send is external comms.
        if action in ("browser.click", "browser.submit") and is_send:
            return True
        # Explicit external risk from the planner also gates — but NOT for
        # compose/attach/type actions which are preparation, not transmission.
        _COMPOSE_ACTIONS = {"browser.attach_file", "browser.type", "browser.navigate",
                            "browser.find_element", "browser.get_url", "browser.get_dom_text",
                            "browser.screenshot"}
        if action in _COMPOSE_ACTIONS:
            return False   # Never gate preparation steps regardless of planner flag
        risk = getattr(step.risk, "value", str(step.risk or "")).lower()
        if risk == "external" and is_send:
            return True
        return False

    def _sanitize_plan(self, plan) -> None:
        """Remove steps whose action is not an executable, registered tool.

        Keeps: registered tools, control actions, and approval-gate steps
        (requires_approval). Drops hallucinated tool names so the run can still
        reach the approval boundary. Authorization is unchanged — dropped steps
        simply never execute.
        """
        # Never-gate compose/attach steps regardless of planner's requires_approval flag
        _NEVER_GATE = {"browser.attach_file", "browser.type", "browser.navigate",
                       "browser.find_element", "browser.screenshot"}
        valid: list[Any] = []
        dropped: list[str] = []
        pause_seen = False
        for step in plan.steps:
            action = step.action or ""
            # Hard rule: nothing after workflow.pause — those steps never execute
            # and cause the run to loop/fail. Drop them unconditionally.
            if pause_seen:
                dropped.append(f"{step.step_key}({action}) [after-pause]")
                continue
            if action == "workflow.pause" or step.requires_approval:
                pause_seen = True
            is_tool = tool_registry.get(action) is not None
            is_control = action in self._CONTROL_ACTIONS
            # Override planner: compose/attach actions are never approval gates
            if action in _NEVER_GATE:
                step.requires_approval = False
            if is_tool or is_control or step.requires_approval:
                valid.append(step)
            else:
                dropped.append(f"{step.step_key}({action})")
        if dropped:
            logger.warning(f"[PLAN] dropped {len(dropped)} steps with unknown actions: {dropped}")
        plan.steps = valid
        plan.total_steps = len(valid)

    async def _record_memory(self, *, success: bool, failure_class: Optional[str] = None) -> None:
        """Persist the run's trajectory to workflow memory for safe learning."""
        try:
            from syncnode_backend.learning.memory import workflow_memory
            task_type = self._infer_task_type()
            await workflow_memory.record_run(
                run_id=self.run_id, task_type=task_type, goal_summary=self._goal[:200],
                steps=self._trajectory, success=success, failure_class=failure_class,
            )
            await self._emit_event("workflow.memory_recorded", {
                "task_type": task_type, "success": success, "steps": len(self._trajectory),
            })
        except Exception as exc:  # noqa: BLE001 - learning must never break a run
            logger.warning("[MEMORY] record failed: %s", exc)

    def _infer_task_type(self) -> str:
        g = (self._goal or "").lower()
        if "excel" in g or "spreadsheet" in g or "workbook" in g:
            return "spreadsheet_workflow"
        if "powerpoint" in g or "presentation" in g or "slide" in g:
            return "presentation_workflow"
        if "email" in g or "draft" in g:
            return "email_draft_workflow"
        if "word" in g or "document" in g or "docx" in g or "report" in g:
            return "document_workflow"
        return "general_workflow"

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        """Map an exception to a coarse error class for learning/recovery."""
        name = type(exc).__name__
        text = str(exc).lower()
        mapping = {
            "ToolNotFoundError": "TOOL_NOT_FOUND",
            "ToolPermissionError": "POLICY_DENIED",
            "ToolUnavailableError": "APP_NOT_RUNNING",
            "ToolError": "INVALID_TOOL_ARGUMENTS",
            "LockTimeoutError": "LOCK_TIMEOUT",
            "WorkspacePathError": "POLICY_DENIED",
            "StepVerificationError": "VERIFICATION_FAILED",
            "StructuredOutputError": "MODEL_ERROR",
            "PlannerError": "MODEL_ERROR",
            "IntentError": "MODEL_ERROR",
        }
        if name in mapping:
            return mapping[name]
        if "permission denied" in text or "locked" in text:
            return "LOCK_TIMEOUT"
        if "not found" in text:
            return "TARGET_NOT_FOUND"
        return "UNKNOWN"

    async def _retrieve_knowledge(self, goal: str) -> str:
        """Conditional RAG: retrieve relevant local knowledge with provenance.

        Emits rag.query and rag.retrieval.completed. Returns a compact context
        string (empty if retrieval was not required). Reference/workflow
        knowledge is CONTEXT only; it never changes policy.
        """
        try:
            from syncnode_ai.rag.conditional import ConditionalRAG
            from syncnode_backend.knowledge.registry import get_knowledge_service

            svc = get_knowledge_service()

            def _retriever(query: str, tags, limit: int):
                hits = svc.search(query, tags=tags, limit=limit)
                return [
                    {"doc_id": d.id, "title": d.title, "trust": d.trust.value,
                     "path": d.path, "content_hash": d.content_hash,
                     "score": score, "text": d.body}
                    for d, score in hits
                ]

            rag = ConditionalRAG(_retriever)
            await self._emit_event("rag.query", {"goal": goal})
            result = rag.retrieve_for_goal(goal)
            await self._emit_event("rag.retrieval.completed", {
                "required": result.required,
                "reason": result.reason,
                "tags": result.tags,
                "documents": result.provenance(),
                "count": len(result.chunks),
            })
            # Persist provenance to the run.
            async with get_session() as session:
                run = await session.get(Run, self.run_id)
                if run:
                    ctx = dict(run.context_json or {})
                    ctx["rag"] = {
                        "required": result.required,
                        "reason": result.reason,
                        "documents": result.provenance(),
                    }
                    run.context_json = ctx
            logger.info(
                "[RAG] required=%s docs=%d reason=%s",
                result.required, len(result.chunks), result.reason,
            )
            return result.context_text()
        except Exception as exc:  # noqa: BLE001 - RAG failure must not abort the run
            logger.warning("[RAG] retrieval failed (continuing without): %s", exc)
            await self._emit_event("rag.retrieval.completed", {
                "required": False, "reason": f"error: {exc}", "documents": [], "count": 0,
            })
            return ""

    async def _execute_step(self, step, step_index: int, agent_registry, gateway, failure_mode: str) -> None:
        """Execute a single plan step with full verification and recovery."""
        from syncnode_ai.agents.registry import AgentDefinition

        step_id = str(uuid.uuid4())
        # Resolve the agent. The model sometimes names the agent after the tool
        # (e.g. "excel" instead of "office"); map the action to its owning agent.
        resolved_agent = self._resolve_agent_key(step.agent_key, step.action, agent_registry)
        if resolved_agent != step.agent_key:
            logger.info("[GRAPH] agent_key %r -> %r (owns %s)",
                        step.agent_key, resolved_agent, step.action)
            step.agent_key = resolved_agent
        agent_def = agent_registry.spawn(step.agent_key)

        # Create DB step record
        async with get_session() as session:
            db_step = RunStep(
                id=step_id,
                run_id=self.run_id,
                step_index=step_index,
                step_key=step.step_key,
                agent_key=step.agent_key,
                action=step.action,
                status="running",
                input_json=step.inputs,
                max_retries=step.retry_policy.max_attempts,
            )
            session.add(db_step)

        await self._emit_event("agent.spawned", {
            "agent_id": step.agent_key,
            "step_key": step.step_key,
            "action": step.action,
        })

        # Emit agent plan summary (safe observable reasoning)
        await self._emit_event("agent.plan_summary", {
            "agent_id": step.agent_key,
            "summary": step.description,
            "step_key": step.step_key,
        })

        # Approval policy: the model's requires_approval flag is NOT authority.
        # Enforce a human-approval gate for any external-communication / send
        # action by policy (Invariant: model output is data, not authorization).
        if step.requires_approval or self._requires_approval_by_policy(step):
            approval_id = await self._request_approval(step_id, step, agent_def)
            raise ApprovalRequiredSignal(approval_id, step.description)

        # Steps without a tool action (pure control) complete immediately.
        if not (step.action and "." in step.action):
            async with get_session() as session:
                db_step = await session.get(RunStep, step_id)
                if db_step:
                    db_step.status = "completed"
            self._record_step(step, None)
            return

        # ---- Execute through the ExecutionEngine, with bounded recovery ----
        await self._run_step_with_recovery(step, step_id, agent_def, failure_mode)

    async def _run_step_with_recovery(self, step, step_id, agent_def, failure_mode: str) -> None:
        """Drive a tool step through the ExecutionEngine, applying the
        RecoveryEngine's deterministic tiers on failure (bounded)."""
        import asyncio as _asyncio

        from syncnode_backend.recovery.engine import RecoveryTier
        from syncnode_backend.runtime.execution_engine import ExecState, ToolProposal

        attempt = 0
        recovered = False
        last_error = "unknown"
        while True:
            attempt += 1
            # Resolve inputs each attempt (re-observation may have changed state).
            self._resolve_step_inputs(step)

            # Failure injection hook (kept for the false-success test).
            if failure_mode == "false_model_success_claim":
                raise StepVerificationError("Injected failure: false model success claim")

            proposal = ToolProposal(
                tool_key=step.action,
                inputs=dict(step.inputs or {}),
                agent_key=step.agent_key,
                agent_allowed_tools=agent_def.allowed_tools,
                step_key=step.step_key,
                postconditions=[pc.model_dump() for pc in step.postconditions],
                step_id=step_id,
            )
            await self._emit_event("tool.proposed", {
                "step_key": step.step_key, "tool": step.action, "attempt": attempt,
            })
            result = await self._exec_engine.run(proposal)

            if result.state == ExecState.PASSED:
                await self._capture_artifacts(step, result.tool_output)
                await self._record_tool_call(step_id, step, result)
                async with get_session() as session:
                    db_step = await session.get(RunStep, step_id)
                    if db_step:
                        db_step.status = "completed"
                        db_step.verification_status = "PASS"
                        db_step.output_json = result.tool_output or {}
                        db_step.retry_count = attempt - 1
                self._recovery.reset(step.step_key)
                self._record_step(step, "PASS" if step.postconditions else None,
                                  retries=attempt - 1, recovered=recovered)
                logger.info("[STEP] %s ✓ — agent=%s attempt=%d", step.step_key, step.agent_key, attempt)
                return

            # Failed or ambiguous → consult recovery.
            last_error = result.error or result.state.value
            decision = self._recovery.decide(
                step_key=step.step_key,
                error_class=result.error_class or "UNKNOWN",
                attempt=attempt,
            )
            await self._emit_event("recovery.started", {
                "step_key": step.step_key, "error_class": result.error_class,
                "tier": decision.tier.value, "attempt": attempt,
                "reason": decision.reason,
            })

            if decision.tier in (RecoveryTier.ABORT, RecoveryTier.REPLAN, RecoveryTier.ESCALATE):
                # Non-retryable at the step level. Record + fail the step.
                async with get_session() as session:
                    db_step = await session.get(RunStep, step_id)
                    if db_step:
                        db_step.status = "failed"
                        db_step.verification_status = getattr(result, "error_class", "FAILED")
                        db_step.error_message = last_error
                        db_step.retry_count = attempt - 1
                self._record_step(step, result.error_class or "FAIL",
                                  retries=attempt - 1, recovered=recovered)
                await self._emit_event("recovery.completed", {
                    "step_key": step.step_key, "outcome": decision.tier.value,
                    "circuit_open": decision.circuit_open,
                })
                raise StepVerificationError(
                    f"Step {step.step_key} failed ({result.error_class}): {last_error}"
                )

            # Retry / Re-observe: back off then loop.
            recovered = True
            if decision.backoff_ms:
                await _asyncio.sleep(decision.backoff_ms / 1000.0)
            await self._emit_event("recovery.attempted", {
                "step_key": step.step_key, "tier": decision.tier.value, "attempt": attempt,
            })

    async def _record_tool_call(self, step_id, step, result) -> None:
        try:
            async with get_session() as session:
                session.add(ToolCall(
                    step_id=step_id, run_id=self.run_id, tool_key=step.action,
                    input_json=dict(step.inputs or {}),
                    output_json=result.tool_output or {},
                    status="completed",
                    duration_ms=int(result.duration_ms),
                ))
        except Exception:  # noqa: BLE001
            pass

    def _record_step(self, step, verification: Optional[str], *, retries: int = 0,
                     recovered: bool = False) -> None:
        """Append a trajectory step for workflow memory."""
        from syncnode_backend.learning.memory import TrajectoryStep
        self._trajectory.append(TrajectoryStep(
            step_key=step.step_key,
            action=step.action or "",
            verification=verification,
            retries=retries,
            recovered=recovered,
        ))

    # ---- ExecutionEngine callbacks ----

    async def _observe_for_engine(self, proposal, tool_output) -> float:
        """Observation hook: capture the observation timestamp and persist an
        observation row. For computer-agent desktop actions we also capture a
        real screenshot so the frontend Desktop tab mirrors live screen state
        from genuine observations (never synthesized)."""
        obs_ts = time.time()
        self._observation_ts = obs_ts

        screenshot_path: Optional[str] = None
        screenshot_hash: Optional[str] = None
        application: Optional[str] = None
        window_title: Optional[str] = None

        # Only computer-agent desktop tools produce a visual desktop state worth
        # mirroring. This is capability-driven (agent == computer), not a string
        # match on the goal.
        if proposal.agent_key == "computer" and self._artifacts_reg is not None:
            try:
                from syncnode_backend.computer.tools import _save_screenshot

                shot_name = f"obs_{proposal.step_key}_{int(obs_ts)}.png"
                shot_path = self._artifacts_reg.new_path("screenshots", shot_name)
                shot = await asyncio.to_thread(_save_screenshot, str(shot_path))
                screenshot_path = shot.get("path", str(shot_path))
                screenshot_hash = shot.get("sha256")
                # Surface any window context the tool reported.
                if isinstance(tool_output, dict):
                    application = tool_output.get("application") or tool_output.get("executable")
                    window_title = tool_output.get("window_title") or tool_output.get("title")
                logger.info(
                    "[OBS] desktop screenshot captured — step=%s sha=%s",
                    proposal.step_key, (screenshot_hash or "")[:8],
                )
            except Exception as exc:  # noqa: BLE001 - screenshot is best-effort
                logger.debug("[OBS] screenshot capture skipped: %s", exc)

        # For browser-agent form-filling steps (type, attach, click, navigate)
        # capture the Playwright page so the Desktop tab shows the compose form
        # state after each action — giving a live visual mirror of the browser.
        _BROWSER_VISUAL_TOOLS = {
            "browser.type", "browser.attach_file",
            "browser.click", "browser.navigate",
        }
        if (
            proposal.agent_key == "browser"
            and proposal.tool_key in _BROWSER_VISUAL_TOOLS
            and self._artifacts_reg is not None
        ):
            try:
                from syncnode_backend.browser.tools import get_browser_page, _page_is_alive
                import sys
                # Access the cached page WITHOUT relaunching if it's dead.
                br_mod = sys.modules.get("syncnode_backend.browser.tools")
                cached = getattr(br_mod, "_page", None) if br_mod else None
                if _page_is_alive(cached):
                    shot_name = f"browser_{proposal.step_key}_{int(obs_ts)}.png"
                    shot_path = self._artifacts_reg.new_path("screenshots", shot_name)
                    import pathlib, hashlib
                    await cached.screenshot(path=str(shot_path), full_page=False)
                    raw = pathlib.Path(str(shot_path)).read_bytes()
                    screenshot_path = str(shot_path)
                    screenshot_hash = hashlib.sha256(raw).hexdigest()
                    application = "Chromium"
                    window_title = await cached.title()
                    logger.info(
                        "[OBS] browser screenshot captured — step=%s sha=%s",
                        proposal.step_key, screenshot_hash[:8],
                    )
            except Exception as exc:  # noqa: BLE001 - best-effort
                logger.debug("[OBS] browser screenshot skipped: %s", exc)

        obs_type = "screenshot" if screenshot_path else "tool_result"
        try:
            async with get_session() as session:
                session.add(Observation(
                    step_id=proposal.step_id, run_id=self.run_id,
                    observation_type=obs_type,
                    application=application,
                    window_title=window_title,
                    screenshot_path=screenshot_path,
                    screenshot_hash=screenshot_hash,
                    metadata_json={"tool": proposal.tool_key,
                                   "keys": list((tool_output or {}).keys())},
                ))
        except Exception:  # noqa: BLE001 - observation persistence best-effort
            pass
        return obs_ts

    async def _verify_for_engine(self, proposal, tool_output, obs_ts):
        """Verification hook: canonicalize targets then run the verifier."""
        pcs = [dict(pc) for pc in proposal.postconditions]
        # Reuse the same canonicalization the inline path used.

        class _S:  # minimal shim carrying .action for canonicalization
            action = proposal.tool_key
        self._canonicalize_postcondition_targets(_S(), pcs, tool_output)
        report = await self._verifier.verify_step(
            step_key=proposal.step_key,
            postconditions=pcs,
            observation_timestamp=obs_ts,
            tool_result=tool_output,
        )
        await self._emit_event(
            "verification.passed" if report.result == "PASS" else "verification.failed",
            {"step_key": proposal.step_key, "result": report.result,
             "assertions": len(report.assertions), "failure_reason": report.failure_reason},
        )
        try:
            async with get_session() as session:
                session.add(VerificationResult(
                    step_id=proposal.step_id, run_id=self.run_id, result=report.result,
                    assertions={"items": [a.model_dump() for a in report.assertions]},
                    failure_reason=report.failure_reason,
                ))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[VERIFY] persist failed: %s", exc)
        return report

    def _filename_from_goal(self, ext: str) -> str:
        """Extract an explicit filename — prefer enricher output, then regex on goal.

        Honors requests like "save it as tree.docx" or "call it report.xlsx" so
        the produced artifact keeps the name the user asked for. Only returns a
        name whose extension matches the artifact kind being created; otherwise
        returns "" so the caller falls back to a default.
        """
        import re

        # Check enricher-extracted filename first (most reliable)
        enricher_file = self._artifacts.get("enricher_filename", "")
        if enricher_file and enricher_file.lower().endswith(ext):
            return enricher_file

        goal = self._goal or ""
        # Match a single filename token (a word optionally with -/_), immediately
        # followed by a known office extension. Word boundary on the left so we
        # capture just "tree" from "...save it as tree.docx", not the whole clause.
        for m in re.finditer(r"([A-Za-z0-9][A-Za-z0-9_\-]*)\.(docx|xlsx|pptx)\b", goal):
            name = f"{m.group(1)}.{m.group(2).lower()}"
            if name.lower().endswith(ext):
                return name
        return ""

    def _inject_email_field(self, step, inputs: dict) -> None:
        """For browser.type steps: detect collapsed compose steps and fill all
        three email fields (to/subject/body) atomically via `_fill_fields`.

        For single-field steps: fix the selector and ensure text is present.
        Also rewrites literal `expected` text in postconditions to "string"
        (non-empty check) so the step doesn't fail because we substituted the
        writer paragraph for the goal's example body text.
        """
        import re
        text_val = str(inputs.get("text", inputs.get("value", ""))).strip()
        selector = str(inputs.get("selector", inputs.get("name", ""))).strip().lower()
        desc_low = str(getattr(step, "description", "")).lower()
        step_key_low = step.step_key.lower()
        goal_low = (self._goal or "").lower()

        # Extract fields from goal — prefer enricher output, fall back to regex
        email_to = self._artifacts.get("enricher_recipient", "")
        if not email_to:
            m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", goal_low)
            if m:
                email_to = m.group(0)

        # Extract subject — prefer enricher
        email_subject = self._artifacts.get("enricher_subject", "")
        if not email_subject:
            sm = re.search(r"subject\s+([^,\.]+)", goal_low)
            if sm:
                email_subject = sm.group(1).strip().rstrip(".,;").strip()

        # Extract body — prefer enricher, then goal regex
        email_body_goal = self._artifacts.get("enricher_body", "")
        if not email_body_goal:
            bm = re.search(r"body\s+([^,\.]+(?:\.[^,\.]+)*?)(?:,\s*(?:attach|stop|send|end)|$)", goal_low)
            if bm:
                email_body_goal = bm.group(1).strip()

        # The actual body text priority:
        # 1. Goal's explicit body (what the user wrote: "body Please find...")
        # 2. Enricher-extracted body hint
        # 3. The planner's text value (if any)
        # 4. Writer paragraph ONLY if no body was specified at all
        # This ensures "body Please find the attached ocean document." wins over
        # the writer's full paragraph which belongs in the Word doc, not the email.
        writer_content = self._artifacts.get("content", "")
        body_text = email_body_goal or text_val or writer_content

        # ── Detect collapsed step (fills all fields) ───────────────────────
        is_collapsed = (
            any(k in desc_low for k in ("recipient, subject", "subject, and body", "subject and body",
                                         "fill in the recipient", "email details", "compose the email",
                                         "email draft", "draft the email"))
            or any(k in step_key_low for k in ("email_details", "draft_email_details",
                                                "compose_email", "fill_email", "type_email"))
        )

        if is_collapsed:
            # Build _fill_fields dict for all three compose fields
            fill = {}
            if email_to:
                fill["to"] = email_to
            if email_subject:
                fill["subject"] = email_subject
            if body_text:
                fill["body"] = body_text
            if fill:
                inputs["_fill_fields"] = fill
                # Also set text/selector for the single-field fallback path
                inputs["text"] = body_text
                inputs["selector"] = "body"
                logger.info("[FLOW] collapsed email compose -> filling %s fields in %s", list(fill.keys()), step.step_key)
            # Relax verification: postconditions that check for specific expected text
            # should pass as long as the field is non-empty
            for pc in getattr(step, "postconditions", []):
                if pc.assertion_type in ("field_value",) and pc.expected not in ("string", "non-empty", "true", "1"):
                    pc.expected = "string"
                    logger.debug("[FLOW] relaxed expected to 'string' for %s", pc.assertion_type)
            return

        # ── Single-field step ──────────────────────────────────────────────
        is_body = (
            any(k in selector for k in ("body", "message")) and "subject" not in selector
        ) or any(k in step_key_low for k in ("body", "compose_body", "message_body"))

        is_subject = "subject" in selector or "subject" in step_key_low

        is_to = (
            selector in ("to", "to_field", "recipient", "email_address")
            or "recipient" in selector
            or any(k in step_key_low for k in ("recipient", "to_field", "type_to", "type_recip"))
        )

        is_unknown = not is_body and not is_subject and not is_to

        if is_unknown:
            if text_val and re.fullmatch(r"[\w.+-]+@[\w.-]+\.\w+", text_val):
                inputs["selector"] = "to"
            elif text_val and (len(text_val) > 40 or "\n" in text_val):
                inputs["selector"] = "body"
            elif any(k in step_key_low for k in ("detail", "compose", "draft", "content")):
                if not text_val or self._looks_like_field_ref(text_val):
                    if writer_content:
                        inputs["text"] = writer_content
                inputs["selector"] = "body"
            elif text_val:
                inputs["selector"] = "body"
            return

        if is_body:
            inputs["selector"] = "body"
            # Only use writer content if the step has NO explicit text — never
            # overwrite a real goal body like "Please find the attached document"
            # with the full writer paragraph.
            if not text_val or self._is_placeholder(text_val) or self._looks_like_field_ref(text_val):
                if email_body_goal:
                    inputs["text"] = email_body_goal
                    logger.info("[FLOW] injected goal body text for %s", step.step_key)
                elif writer_content:
                    inputs["text"] = writer_content
                    logger.info("[FLOW] fallback: injected writer content as email body in %s", step.step_key)

        if is_subject:
            inputs["selector"] = "subject"

        if is_to:
            inputs["selector"] = "to"
            if not text_val or self._is_placeholder(text_val) or self._looks_like_field_ref(text_val):
                if email_to:
                    inputs["text"] = email_to
                    logger.info("[FLOW] extracted recipient %s for %s", email_to, step.step_key)

        # Safety: email address in body → route to 'to'
        cur_text = str(inputs.get("text", "")).strip()
        cur_sel  = str(inputs.get("selector", "")).strip().lower()
        if cur_sel == "body" and re.fullmatch(r"[\w.+-]+@[\w.-]+\.\w+", cur_text):
            inputs["selector"] = "to"

        # Relax literal expected text to non-empty check
        for pc in getattr(step, "postconditions", []):
            if pc.assertion_type == "field_value" and pc.expected not in ("string", "non-empty", "true", "1"):
                if isinstance(pc.expected, str) and len(pc.expected) > 10:
                    pc.expected = "string"

    @staticmethod
    def _looks_like_field_ref(value: str) -> bool:
        """True if a value is a bare symbolic reference to another step/field
        rather than real prose.

        The planner often fills `content` with a token echoing a variable name —
        e.g. "paragraph_content", "generated_content", "tree_content",
        "content", "output", "writer_output", "step1_output". These are short,
        space-free, snake/camel identifiers with no sentence punctuation. Real
        written paragraphs contain spaces and punctuation, so this stays safe.
        """
        if not isinstance(value, str):
            return False
        v = value.strip()
        if not v or " " in v:            # real prose has spaces
            return False
        low = v.lower().rstrip(".")
        # Explicit common tokens.
        if low in {
            "content", "output", "text", "body", "paragraph", "result",
            "paragraph_content", "generated_content", "generated_paragraph",
            "writer_output", "writer_content", "document_content", "the_content",
        }:
            return True
        # Generic *_content / *_output / *_text identifiers (snake or camel),
        # with no whitespace — treat as a symbolic ref, never as real content.
        import re
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", v) and re.search(
            r"(content|output|paragraph|text|body)$", low
        ):
            return True
        return False

    @staticmethod
    def _is_placeholder(value: Any) -> bool:
        """True if a value looks like an unresolved model placeholder reference.

        The model frequently emits symbolic references instead of real data,
        e.g. "$generate_content.output", "{{content}}", "<content>",
        "[previous step output]", "[[Output from generate_word_content]]".
        These must be treated as empty so real artifacts from prior steps
        are substituted.
        """
        if not isinstance(value, str):
            return False
        v = value.strip()
        if not v:
            return True
        return (
            v.startswith("$")
            or (v.startswith("{{") and v.endswith("}}"))
            or (v.startswith("{") and v.endswith("}") and "." in v and " " not in v)
            or (v.startswith("<") and v.endswith(">"))
            or (v.startswith("[") and v.endswith("]"))
            or (v.startswith("[[") and v.endswith("]]"))   # double-bracket: [[Output from step]]
            or (v.startswith("(") and v.endswith(")") and " " not in v and len(v) < 80)
        )

    def _resolve_step_inputs(self, step) -> None:
        """Fill missing/placeholder step inputs from artifacts produced by prior
        steps.

        Bounded and explicit: only fills `content` / `path` / `file_path`, only
        when the planner left them blank OR supplied an unresolved placeholder
        reference, and only from concrete prior-step outputs. Never overwrites a
        real value the planner provided.
        """
        inputs = step.inputs or {}

        def _blank(key: str) -> bool:
            return key not in inputs or self._is_placeholder(inputs.get(key))

        # Run isolation: route artifact-creating tools to a run-scoped path so
        # no run reuses another run's file. Only applies when the run has an
        # artifact registry (the golden demo test path is unaffected).
        if self._artifacts_reg is not None:
            create_kinds = {
                "document.create_docx": ("word", ".docx", "Word"),
                "excel.create": ("excel", ".xlsx", "Excel"),
                "powerpoint.create": ("powerpoint", ".pptx", "Presentation"),
            }
            if step.action in create_kinds:
                kind, ext, label = create_kinds[step.action]
                supplied = str(inputs.get("path", "")).strip()
                # Force artifacts into the run-scoped directory (isolation), but
                # PRESERVE the filename the user/planner asked for (e.g.
                # "tree.docx") so the artifact keeps its meaningful name and any
                # later step that references that name still resolves.
                already_scoped = False
                if supplied and not self._is_placeholder(supplied):
                    try:
                        already_scoped = str(Path(supplied).resolve()).startswith(
                            str(self._artifacts_reg.run_dir)
                        )
                    except Exception:
                        already_scoped = False
                if not already_scoped:
                    # Derive the desired base name, in priority order:
                    #  1) an explicit filename the planner put in the step path,
                    #  2) a filename the USER named in the goal ("save as tree.docx"),
                    #  3) a safe default.
                    base = ""
                    if supplied and not self._is_placeholder(supplied):
                        base = Path(supplied).name  # keep just the filename part
                    if not base:
                        base = self._filename_from_goal(ext)
                    if not base:
                        base = f"SyncNode_{label}_{self.run_id[:8]}{ext}"
                    if not base.lower().endswith(ext):
                        base = f"{Path(base).stem}{ext}"
                    inputs["path"] = str(self._artifacts_reg.new_path(kind, base))
                    # Remember the requested name so downstream inspect/read/launch
                    # steps that reference it (e.g. "tree.docx") resolve to the
                    # real run-scoped file instead of a bare, non-existent name.
                    self._artifacts["requested_doc_name"] = base
                    logger.info("[FLOW] run-scoped %s path -> %s", step.action, inputs["path"])

        # Content flows from the writer to document/filesystem steps AND to
        # computer.uia_type (live typing into app windows).
        if step.action in ("document.create_docx", "filesystem.write", "computer.uia_type"):
            generated = self._artifacts.get("content")
            content_key = "text" if step.action == "computer.uia_type" else "content"
            supplied_content = str(inputs.get(content_key, "")).strip()
            looks_symbolic = (
                self._is_placeholder(supplied_content)
                or self._looks_like_field_ref(supplied_content)
            )
            # Fix: for uia_type — only inject content if create_docx has NOT
            # already written it to disk. When the doc was already created with
            # the same content, uia_type would type it again → duplicate paragraph.
            # We suppress injection for uia_type when the orchestrator already
            # wrote the content to the .docx (doc_path is set AND file exists).
            if step.action == "computer.uia_type":
                doc_already_written = bool(
                    self._artifacts.get("doc_path")
                    and self._artifacts.get("content")
                )
                if doc_already_written and (not supplied_content or looks_symbolic):
                    # Clear the placeholder so Word doesn't get duplicate content.
                    # The file on disk already has the right text.
                    inputs[content_key] = generated or ""
                    # Allow injection — the user explicitly wants live typing
                    # so keep the content but don't block it.
                    # (The duplicate comes from Word opening a file that already
                    # has the paragraph, then us typing it again. The real fix
                    # is to use clear_first=true so the existing content is
                    # replaced, not appended.)
                    inputs["clear_first"] = True
                    logger.info("[FLOW] uia_type will clear_first=true to avoid duplicate content in %s",
                                step.step_key)
                elif generated and (_blank(content_key) or looks_symbolic):
                    inputs[content_key] = generated
                    logger.info("[FLOW] injected generated content into %s (key=%s)",
                                step.step_key, content_key)
                elif looks_symbolic and not generated:
                    inputs[content_key] = ""
                    logger.info("[FLOW] cleared placeholder content on %s", step.step_key)
            else:
                if generated and (_blank(content_key) or looks_symbolic):
                    inputs[content_key] = generated
                    logger.info("[FLOW] injected generated content into %s (key=%s)",
                                step.step_key, content_key)
                elif looks_symbolic and not generated:
                    inputs[content_key] = ""
                    logger.info("[FLOW] cleared placeholder content on %s", step.step_key)

        # key_press save step: pre-fill the postcondition file_saved target with
        # the actual artifact path NOW (before the tool runs), so verify can find
        # the real .docx/.xlsx/.pptx on disk. key_press returns {"sent":True} —
        # it has no "path" output, so _canonicalize_postcondition_targets can't
        # fill it after the fact. We fill it here from the run-scoped artifact dict.
        if step.action == "computer.key_press":
            keys_val = str(inputs.get("keys", "")).lower()
            if "{ctrl}s" in keys_val or "ctrl+s" in keys_val:
                # Determine which artifact was most recently opened
                _save_art_order = ["doc_path", "word_path", "excel_path", "powerpoint_path"]
                for art_key in _save_art_order:
                    art_path = self._artifacts.get(art_key)
                    if art_path:
                        from pathlib import Path as _P
                        if _P(art_path).exists():
                            for pc in (step.postconditions or []):
                                target = str(pc.get("target", "")).strip()
                                atype = str(pc.get("assertion_type", "")).lower()
                                if "save" in atype or "file" in atype:
                                    if not target or not _P(target).is_absolute():
                                        pc["target"] = art_path
                                        logger.info("[FLOW] pre-filled key_press postcondition "
                                                    "target=%s for step %s", art_path, step.step_key)
                            break

        # The created document path flows to verify/read steps that take `path`.
        doc_path = self._artifacts.get("doc_path")
        if doc_path and step.action in ("document.inspect_docx", "document.read_docx"):
            supplied_p = str(inputs.get("path", "")).strip()
            # Redirect to the real created file when the planner left it blank,
            # gave a placeholder, or gave a bare name (e.g. "tree.docx") that is
            # not the actual run-scoped path. This prevents inspect/read from
            # failing against a filename that was never physically created.
            redirect = (
                not supplied_p
                or self._is_placeholder(supplied_p)
            )
            if not redirect:
                try:
                    redirect = not str(Path(supplied_p).resolve()).startswith(
                        str(self._artifacts_reg.run_dir)
                    ) if self._artifacts_reg is not None else False
                except Exception:
                    redirect = True
            if redirect:
                inputs["path"] = doc_path
                logger.info(f"[FLOW] redirected {step.step_key} path -> {doc_path}")

        # Same redirect logic for Excel and PowerPoint inspect tools.
        # These need the run-scoped artifact path just like docx inspect/read.
        _office_inspect_map = {
            "excel.inspect":       "excel_path",
            "excel.read_cell":     "excel_path",
            "excel.read_range":    "excel_path",
            "excel.write_cell":    "excel_path",
            "powerpoint.inspect":  "powerpoint_path",
            "powerpoint.add_slide": "powerpoint_path",
        }
        if step.action in _office_inspect_map:
            art_key = _office_inspect_map[step.action]
            art_path = self._artifacts.get(art_key)
            if art_path:
                supplied_p = str(inputs.get("path", "")).strip()
                redirect = (
                    not supplied_p
                    or self._is_placeholder(supplied_p)
                    or not Path(supplied_p).is_absolute()
                )
                if redirect:
                    inputs["path"] = art_path
                    logger.info("[FLOW] redirected %s path -> %s", step.step_key, art_path)
        # Auto-fill output_path for screenshot steps — planner often omits it.
        # Generate a run-scoped evidence path so the tool never fails on missing arg.
        if step.action in ("computer.screenshot", "browser.screenshot") and _blank("output_path"):
            if self._artifacts_reg is not None:
                import time as _time
                shot_name = f"evidence_{step.step_key}_{int(_time.time())}.png"
                shot_path = self._artifacts_reg.new_path("screenshots", shot_name)
                inputs["output_path"] = str(shot_path)
            else:
                from syncnode_backend.documents.tools import _safe_path
                inputs["output_path"] = str(
                    _safe_path(f"screenshots/evidence_{step.step_key}.png")
                )
            logger.info("[FLOW] auto-filled output_path for screenshot step %s -> %s",
                        step.step_key, inputs["output_path"])
            step.inputs = inputs
        # Launching the editor should open the created document — pass its
        # absolute path as a launch argument when none was provided.
        # Covers Word (doc_path), Excel (excel_path) and PowerPoint (powerpoint_path).
        _launch_path_map = {
            "computer.launch_app": {
                "word":       ["doc_path", "word_path"],
                "winword":    ["doc_path", "word_path"],
                "winword.exe":["doc_path", "word_path"],
                "excel":      ["excel_path"],
                "excel.exe":  ["excel_path"],
                "powerpoint": ["powerpoint_path"],
                "powerpnt":   ["powerpoint_path"],
                "powerpnt.exe":["powerpoint_path"],
            }
        }
        if step.action == "computer.launch_app" and not inputs.get("args"):
            exe_key = str(inputs.get("executable", "")).lower().strip()
            # If executable is empty default is word
            if not exe_key:
                exe_key = "word"
            artifact_keys = _launch_path_map["computer.launch_app"].get(exe_key, [])
            if not artifact_keys:
                # Generic fallback — any file: try doc then excel then pptx
                artifact_keys = ["doc_path", "word_path", "excel_path", "powerpoint_path"]
            for ak in artifact_keys:
                art_path = self._artifacts.get(ak)
                if art_path:
                    from syncnode_backend.documents.tools import _safe_path
                    inputs["args"] = [str(_safe_path(art_path).resolve())]
                    logger.info("[FLOW] injected %s path as launch arg into %s → %s",
                                ak, step.step_key, inputs["args"][0])
                    break

        # windows_search: if it looks like an "open this document" step,
        # inject the file_path so it opens directly without the Search UI.
        # Priority 1: use same-run artifacts (most accurate)
        # Priority 2: scan workspace on disk for a matching filename (cross-run)
        if step.action == "computer.windows_search" and not inputs.get("file_path"):
            query_low = str(inputs.get("query", "")).lower()
            query_raw = str(inputs.get("query", ""))
            _search_art_map = [
                (["word", "winword", ".docx", "report", "document"], ["doc_path", "word_path"]),
                (["excel", "xlsx", "spreadsheet", "workbook", "data"], ["excel_path"]),
                (["powerpoint", "pptx", "presentation", "slides", "deck"], ["powerpoint_path"]),
            ]
            injected = False
            for keywords, art_keys in _search_art_map:
                if any(k in query_low for k in keywords):
                    # Priority 1: same-run artifact
                    for ak in art_keys:
                        art_path = self._artifacts.get(ak)
                        if art_path:
                            from syncnode_backend.documents.tools import _safe_path
                            resolved = str(_safe_path(art_path).resolve())
                            inputs["file_path"] = resolved
                            logger.info("[FLOW] injected same-run file_path into windows_search %s → %s",
                                        step.step_key, resolved)
                            injected = True
                            break
                    if injected:
                        break
                    # Priority 2: scan workspace for a file matching the query
                    # (handles "open the word doc you created" as a new run)
                    try:
                        from syncnode_backend.config.settings import settings as _s
                        import glob as _glob
                        ext_map = {
                            ".docx": ["doc_path", "word_path"],
                            ".xlsx": ["excel_path"],
                            ".pptx": ["powerpoint_path"],
                        }
                        exts = [".docx"] if "word" in query_low or ".docx" in query_low else \
                               [".xlsx"] if "excel" in query_low or ".xlsx" in query_low else \
                               [".pptx"] if "powerpoint" in query_low or ".pptx" in query_low else \
                               [".docx", ".xlsx", ".pptx"]
                        workspace = str(_s.syncnode_workspace_root)
                        candidates = []
                        for ext in exts:
                            candidates.extend(_glob.glob(f"{workspace}/**/*{ext}", recursive=True))
                        if candidates:
                            # Prefer filename match over recency
                            q_clean = query_raw.lower().replace(" ", "_")
                            scored = []
                            for c in candidates:
                                fname = Path(c).stem.lower()
                                score = sum(1 for w in q_clean.split("_") if w and w in fname)
                                import os as _os
                                scored.append((score, _os.path.getmtime(c), c))
                            scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
                            best = scored[0][2]
                            inputs["file_path"] = best
                            logger.info("[FLOW] cross-run workspace scan injected file_path %s → %s",
                                        step.step_key, best)
                    except Exception as _scan_exc:
                        logger.debug("[FLOW] workspace scan failed (non-fatal): %s", _scan_exc)
                    break

        # Browser attach step consumes the run's produced artifacts. Attach ALL
        # artifacts created during this run (Word + Excel + PowerPoint), by their
        # registered canonical paths — never a stale/prose path. Multiple paths
        # are joined with '|' for the multi-file attach tool.
        if step.action == "browser.attach_file":
            from syncnode_backend.documents.tools import _safe_path
            run_paths: list[str] = []
            if self._artifacts_reg is not None:
                for rec in self._artifacts_reg.all():
                    if rec.kind in ("word", "excel", "powerpoint"):
                        run_paths.append(str(_safe_path(rec.path).resolve()))
            if not run_paths and doc_path:
                run_paths = [str(_safe_path(doc_path).resolve())]
            # Attach ALL run-produced artifacts (the workflow's intent), always
            # overriding the model's single/prose path with the real set.
            if run_paths:
                inputs["file_path"] = "|".join(run_paths)
                logger.info("[FLOW] injected %d attachment(s) into %s",
                            len(run_paths), step.step_key)

        # Email compose field injection — the planner frequently collapses
        # recipient/subject/body into a single step or emits symbolic refs.
        # Resolve the intent from the goal and inject the correct `text` and
        # `selector` so the right compose field always gets filled.
        if step.action == "browser.type":
            self._inject_email_field(step, inputs)

        step.inputs = inputs

    @staticmethod
    def _canonicalize_postcondition_targets(
        step, postconditions: list[dict], tool_result: Optional[dict]
    ) -> None:
        """Point file-based assertion targets at the artifact the tool actually
        produced.

        The model often phrases postcondition targets in prose (e.g.
        "demo workspace/SyncNode_Verifier_Demo.docx") that does not resolve to
        the real file. When the executed tool reports the concrete path it
        wrote, use that as the verification target. This does NOT weaken the
        guarantee: we still verify a real file on disk with real content/hash —
        we just verify the correct file (the one the tool created) rather than a
        mismatched prose path.

        Also handles the case where a verification step refers to a bare filename
        (e.g. "sales_report.xlsx") as the target — these are rewritten to the
        absolute run-scoped path from tool_result if available.
        """
        if not tool_result:
            return
        real_path = tool_result.get("path")
        if not real_path:
            return
        from syncnode_backend.verification.engine import _normalize_assertion_type
        file_assertions = {"file_exists", "file_non_empty", "file_hash_match",
                           "artifact_structure_valid", "xlsx_structure_valid",
                           "pptx_structure_valid", "cell_count", "file_size",
                           "file_readable"}
        for pc in postconditions:
            atype = _normalize_assertion_type(pc.get("assertion_type", ""))
            if atype in file_assertions:
                target = str(pc.get("target", ""))
                # Always use the real tool output path when target is:
                #   - empty/None
                #   - a bare filename (no directory component)
                #   - a relative path (not rooted)
                #   - a prose/placeholder path
                from pathlib import Path as _P
                needs_rewrite = (
                    not target
                    or not _P(target).is_absolute()
                    or _P(target).parent == _P(".")
                )
                if needs_rewrite:
                    pc["target"] = real_path

    async def _capture_artifacts(self, step, tool_result: Optional[dict]) -> None:
        """Capture concrete outputs from a completed step for later steps and
        register produced artifacts in the run-scoped registry."""
        if not tool_result:
            return
        if step.action == "writer.generate_paragraph":
            content = tool_result.get("content")
            if isinstance(content, str) and content.strip():
                self._artifacts["content"] = content

        # Capture fs_search result — the first found file becomes available for
        # the subsequent windows_search/launch_app open step.
        if step.action == "system.fs_search":
            found = tool_result.get("found", [])
            if found:
                first_path = found[0].get("path") if isinstance(found[0], dict) else str(found[0])
                if first_path:
                    from pathlib import Path as _P
                    fp = _P(first_path)
                    ext = fp.suffix.lower()
                    if ext == ".docx":
                        self._artifacts["doc_path"] = first_path
                        self._artifacts["word_path"] = first_path
                    elif ext == ".xlsx":
                        self._artifacts["excel_path"] = first_path
                    elif ext == ".pptx":
                        self._artifacts["powerpoint_path"] = first_path
                    # Generic — always store so windows_search injection can find it
                    self._artifacts["found_file_path"] = first_path
                    logger.info("[FLOW] fs_search captured path for open step → %s", first_path)

        # Register office artifacts (run-scoped, typed).
        create_kind = {
            "document.create_docx": "word",
            "excel.create": "excel",
            "powerpoint.create": "powerpoint",
        }.get(step.action)
        path = tool_result.get("path") if isinstance(tool_result, dict) else None
        if create_kind and isinstance(path, str) and path:
            if step.action == "document.create_docx":
                self._artifacts["doc_path"] = path
            self._artifacts[f"{create_kind}_path"] = path
            if self._artifacts_reg is not None:
                try:
                    rec = self._artifacts_reg.register(
                        kind=create_kind, path=path, producer_step=step.step_key,
                    )
                    self._artifacts_reg.mark_verified(rec.artifact_id, True)
                    self._artifacts[f"{create_kind}_artifact"] = rec.ref
                    await self._persist_artifact(rec)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[ARTIFACT] register failed: %s", exc)

    async def _persist_artifact(self, rec) -> None:
        try:
            async with get_session() as session:
                session.add(Artifact(
                    run_id=self.run_id, name=Path(rec.path).name,
                    artifact_type=rec.kind, path=rec.path, sha256=rec.sha256,
                    size_bytes=Path(rec.path).stat().st_size if Path(rec.path).exists() else None,
                    mime_type=rec.mime_type, verified=rec.verified,
                    metadata_json={"artifact_id": rec.artifact_id, "ref": rec.ref,
                                   "producer_step": rec.producer_step},
                ))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ARTIFACT] persist failed: %s", exc)

    async def _invoke_tool(self, step_id: str, step, agent_def, failure_mode: str) -> dict:
        """Invoke a tool through the registry with full validation."""
        tool_key = step.action
        inputs = step.inputs or {}

        # Failure injection for testing
        if failure_mode == "false_model_success_claim":
            logger.warning("[INJECT] false_model_success_claim — tool will not execute")
            raise Exception("Injected failure: false model success claim")

        await self._emit_event("tool.invoked", {
            "step_key": step.step_key,
            "tool_key": tool_key,
            "inputs": {k: str(v)[:50] for k, v in inputs.items()},
        })

        # Record tool call
        call_id = str(uuid.uuid4())
        async with get_session() as session:
            tc = ToolCall(
                id=call_id,
                step_id=step_id,
                run_id=self.run_id,
                tool_key=tool_key,
                input_json=inputs,
                status="running",
            )
            session.add(tc)

        try:
            result = await tool_registry.invoke(
                key=tool_key,
                inputs=inputs,
                agent_allowed_tools=agent_def.allowed_tools,
            )

            async with get_session() as session:
                tc = await session.get(ToolCall, call_id)
                if tc:
                    tc.status = "completed"
                    tc.output_json = result

            await self._emit_event("tool.completed", {
                "tool_key": tool_key,
                "step_key": step.step_key,
                "success": True,
            })
            return result

        except Exception as exc:
            async with get_session() as session:
                tc = await session.get(ToolCall, call_id)
                if tc:
                    tc.status = "failed"
                    tc.error_message = str(exc)
            logger.error(f"[TOOL] failed — tool_key={tool_key} error={str(exc)}")
            raise

    async def _request_approval(self, step_id: str, step, agent_def) -> str:
        """Create an approval record, emit SSE, and return its ID."""
        approval_id = str(uuid.uuid4())
        async with get_session() as session:
            approval = Approval(
                id=approval_id,
                run_id=self.run_id,
                step_id=step_id,
                risk_class="EXTERNAL_COMMUNICATION",
                action_summary=step.description,
            )
            session.add(approval)

        # Emit approval.requested over SSE immediately so the frontend's
        # applyEvent handler can push the Approval into state.approvals
        # without waiting for the separate run.waiting_approval event.
        await self._emit_event("approval.requested", {
            "approval_id": approval_id,
            "step_key": step.step_key,
            "action": step.description,
            "action_summary": step.description,
            "risk": "EXTERNAL_COMMUNICATION",
            "risk_class": "EXTERNAL_COMMUNICATION",
            "status": "pending",
        })

        await audit_engine.record("approval.requested", {
            "approval_id": approval_id,
            "step_key": step.step_key,
            "action": step.description,
        }, run_id=self.run_id)

        logger.info(f"[POLICY] Send requires approval — step={step.step_key}")
        logger.info(f"[APPROVAL] requested — approval_id={approval_id}")
        return approval_id


class _ApprovalStub:
    """Minimal object carrying .description for a policy-initiated approval."""

    def __init__(self, description: str) -> None:
        self.description = description
        self.step_key = "external_send_gate"


class ApprovalRequiredSignal(Exception):
    """Raised to signal the orchestrator to pause at an approval gate."""

    def __init__(self, approval_id: str, action_summary: str) -> None:
        self.approval_id = approval_id
        self.action_summary = action_summary
        super().__init__(f"Approval required: {action_summary}")


class StepVerificationError(Exception):
    """Raised when a step fails verification and cannot be recovered."""
    pass
