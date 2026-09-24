"""
SyncNode — Planner Engine.

Converts a StructuredIntent into an ExecutionPlan (dependency DAG).
Every step must have postconditions — this is enforced here.
"""

from __future__ import annotations

import logging
from typing import Optional

from syncnode_ai.gateway.gateway import ModelGateway
from syncnode_ai.gateway.schemas import Message, ModelRequest
from syncnode_ai.intent.schemas import StructuredIntent
from syncnode_ai.planner.schemas import (
    ExecutionPlan,
    Postcondition,
    PlanStep,
    RetryPolicy,
    StepRisk,
)

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the SyncNode Planner. Your job is to convert a structured intent
into an ordered execution plan as a JSON array of steps.

Each step MUST have:
- step_key: unique string id for this step (e.g. "create_docx")
- agent_key: which agent executes it (writer|document|computer|browser|verifier|recovery|supervisor)
- action: specific action name (e.g. "document.create_docx")
- description: what this step does
- dependencies: list of step_keys that must complete before this step
- inputs: dict of input parameters
- required_capabilities: list of capability strings needed
- allowed_tools: list of tool keys this step may use
- risk: low|medium|high|external
- postconditions: list of {assertion_type, target, expected, description} — REQUIRED
- retry_policy: {max_attempts, backoff_ms, on_timeout}
- timeout_seconds: integer
- requires_approval: boolean

IMPORTANT — use ONLY these real tool actions (unknown tools are rejected):
  writer.generate_paragraph, document.create_docx, document.inspect_docx,
  excel.create, excel.inspect, powerpoint.create, powerpoint.inspect,
  computer.windows_search, computer.launch_app, computer.find_window,
  computer.uia_find, computer.uia_type, computer.uia_click, computer.key_press,
  computer.screenshot, browser.navigate, browser.type, browser.attach_file,
  browser.screenshot, workflow.pause,
  system.fs_read, system.fs_list, system.fs_search, system.fs_write,
  system.fs_delete, system.shell, system.process_list, system.process_kill,
  system.clipboard_get, system.clipboard_set, system.env_get, system.registry_get

When the goal says to open an application from Windows, the FIRST computer step
must be computer.windows_search (inputs: {"query": "Microsoft Word", "open_result": true}).
Only launch_app as a fallback. Verify an application with assertion_type
"application_running" (target = the app's process, e.g. "WINWORD.EXE") AFTER the
step that launches it — never before.

For LIVE document editing (open app → type → save):
  The orchestrator AUTOMATICALLY injects the correct file path into launch_app.
  Just set executable and leave args empty — the file opens automatically.
  a. computer.launch_app (computer) -> application_running
     inputs: {"executable": "winword"}   ← opens Word WITH the .docx auto-injected
     inputs: {"executable": "excel"}     ← opens Excel WITH the .xlsx auto-injected
     inputs: {"executable": "powerpnt"}  ← opens PowerPoint WITH the .pptx auto-injected
  b. computer.uia_type to type content into the window
     inputs: {"text": "<content>", "window_title": "Word", "clear_first": false}
  c. computer.key_press to save: inputs: {"keys": "{Ctrl}s"}
  d. computer.key_press to close: inputs: {"keys": "{Alt}{F4}"}

  DO NOT use computer.windows_search to open a specific file — it opens the app
  without the file. Use computer.launch_app with executable only (path auto-filled).

For a multi-document + email workflow, the CORRECT plan is:
1. writer.generate_paragraph (writer)     -> content_generated
2. document.create_docx (document)        -> file_exists   (path auto-scoped, leave inputs={})
3. excel.create (office)                  -> file_exists   (inputs: {"rows": [["Category","Value","Notes"],["Automation",95,"pass"]]})
4. powerpoint.create (office)             -> file_exists   (inputs: {"title": "SyncNode Demo", "slides": [{"title":"Metrics","body":"95% accuracy"},{"title":"Next Steps","body":"Deploy to prod"}]})
5. computer.launch_app (computer)         -> application_running (inputs: {"executable": "winword"} — orchestrator injects .docx path)
6. computer.uia_type (computer)           -> content_typed (type into Word window)
   inputs: {"text": "<paragraph>", "window_title": "Word", "clear_first": false}
7. computer.key_press (computer)          -> file_saved    (inputs: {"keys": "{Ctrl}s"})
8. browser.navigate (browser)             -> page_loaded
   CRITICAL: embed ALL email fields in the URL:
   url = "https://mail.google.com/mail/u/0/?view=cm&fs=1&to=<RECIPIENT>&su=<SUBJECT>&body=<BODY>"
   URL-encode spaces as +. Example:
   "https://mail.google.com/mail/u/0/?view=cm&fs=1&to=demo@syncnode.ai&su=Q4+Package&body=Hi+Team"
   The compose fixture pre-fills To/Subject/Body — NO browser.type steps needed.
9. browser.attach_file (browser)          -> attachment_present (inputs: {} — all artifacts auto-attached)
10. workflow.pause (supervisor)           -> requires_approval: true  (NEVER add browser.click/send)

CRITICAL RULES:
- NEVER use a tool not in the list above. Unknown tools are rejected and fail the run.
- computer.windows_search and computer.launch_app use the "computer" agent.
- computer.uia_type, computer.uia_click, computer.key_press use the "computer" agent.
- excel.create, powerpoint.create, powerpoint.add_slide use the "office" agent.
- document.create_docx, writer.generate_paragraph use "document" / "writer" agents.
- browser.* steps use the "browser" agent.
- The browser.attach_file step attaches ALL workspace artifacts automatically — do NOT put paths in inputs.
- For the final step with requires_approval=true, set action="workflow.pause" and agent="supervisor".

Return ONLY a valid JSON object: {"steps": [...]}
"""


class Planner:
    """Converts StructuredIntent to an ExecutionPlan DAG."""

    def __init__(self, gateway: ModelGateway) -> None:
        self._gateway = gateway

    async def plan(
        self,
        intent: StructuredIntent,
        run_id: str,
        context_summary: Optional[str] = None,
    ) -> ExecutionPlan:
        """Generate an ExecutionPlan from a StructuredIntent."""
        from syncnode_ai.planner._output import _PlannerOutput

        intent_json = intent.model_dump_json(indent=2)
        user_content = f"Structured Intent:\n{intent_json}"
        if context_summary:
            user_content += f"\n\nContext:\n{context_summary}"

        from syncnode_ai.routing import TaskClass, profile_registry

        profile = profile_registry.get(TaskClass.PLANNER)
        request = ModelRequest(
            model_id=self._gateway.model_id,
            messages=[
                Message(role="system", content=PLANNER_SYSTEM_PROMPT),
                Message(role="user", content=user_content),
            ],
            caller="planner",
            run_id=run_id,
        ).model_copy(update=profile.request_overrides())

        try:
            output, _ = await self._gateway.generate_structured(request, _PlannerOutput)
            steps = output.steps

            # Enforce: every step must have postconditions
            for step in steps:
                if not step.postconditions:
                    logger.warning(
                        f"Step missing postconditions — failing fast — step_key={step.step_key}"
                    )
                    from syncnode_ai.errors import PlannerError
                    raise PlannerError(f"Step {step.step_key} is missing postconditions. All steps MUST have real postconditions.")

            plan = ExecutionPlan(
                run_id=run_id,
                goal_summary=intent.goal_summary,
                steps=steps,
            )
            logger.info(f"Plan created — run_id={run_id} steps={len(steps)}")
            return plan

        except Exception as exc:
            from syncnode_ai.errors import PlannerError
            logger.exception("Planning failed — run_id=%s", run_id)
            raise PlannerError(f"Planning failed: {repr(exc)}") from exc
