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
- agent_key: which agent executes it (writer|document|office|computer|browser|system|verifier|recovery|supervisor)
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

═══════════════════════════════════════════════════════════════
RULE #1 — OPENING AN EXISTING FILE (highest priority rule)
═══════════════════════════════════════════════════════════════
When the goal is to OPEN an existing file (e.g. "open the word document you
created", "open Q4_Report.docx", "show me the file"):

  Step A — find the file:
    action: system.fs_search   agent: system
    inputs: {"query": "<filename>", "search_path": "C:\\syncnode\\workspace", "pattern": "*.docx"}
    postconditions: [{"assertion_type": "shell_output_contains", "target": "stdout", "expected": ".docx"}]

  Step B — open the file directly (depends on Step A):
    action: computer.windows_search   agent: computer
    inputs: {"query": "<filename>", "file_path": "<absolute_path_from_step_A>"}
    postconditions: [{"assertion_type": "application_running", "target": "WINWORD.EXE", "expected": "true"}]

  NEVER use computer.windows_search with just a filename as `query` and no `file_path`.
  Doing so launches Windows Search and opens Bing — this is ALWAYS wrong for opening files.
  The `file_path` parameter is MANDATORY when opening a specific document.

  If the exact path is already known (e.g. it was just created in this run and
  the orchestrator will inject it), use computer.launch_app instead:
    action: computer.launch_app   agent: computer
    inputs: {"executable": "winword"}   ← orchestrator auto-injects the .docx path

═══════════════════════════════════════════════════════════════
RULE #2 — LAUNCHING AN APP (no specific file)
═══════════════════════════════════════════════════════════════
When the goal is to launch an application WITHOUT opening a specific file
(e.g. "open Microsoft Word", "open Excel"):
  Use computer.windows_search with ONLY the app name as query:
    inputs: {"query": "Microsoft Word", "open_result": true}
  Verify with assertion_type "application_running" (target = process name "WINWORD.EXE").

═══════════════════════════════════════════════════════════════
RULE #3 — CREATING THEN OPENING (same run)
═══════════════════════════════════════════════════════════════
For LIVE document editing (create file → open in app → type → save):
  The orchestrator AUTOMATICALLY injects the correct file path into launch_app.
  Just set executable and leave args empty — the file opens automatically.
  a. computer.launch_app (computer) -> application_running
     inputs: {"executable": "winword"}   ← opens Word WITH the .docx auto-injected
     inputs: {"executable": "excel"}     ← opens Excel WITH the .xlsx auto-injected
     inputs: {"executable": "powerpnt"}  ← opens PowerPoint WITH the .pptx auto-injected
     postconditions: [{"assertion_type": "application_running", "target": "WINWORD.EXE", "expected": "true"}]

  b. computer.uia_type (computer) — type content into the live window
     inputs: {"text": "<content>", "window_title": "Word", "clear_first": false, "wait_ready_ms": 3000}
     ↑ wait_ready_ms: ALWAYS set to 3000 for Word/Excel/PowerPoint — they need time to focus.
     postconditions: [{"assertion_type": "content_typed", "target": "typed", "expected": "true"}]

     !! CRITICAL: assertion_type for computer.uia_type MUST be "content_typed" !!
     NEVER use these — they do not exist and will ALWAYS cause failure:
       ui_element_contains, ui_element_text, element_contains, element_text,
       window_text, document_text_present, text_present, word_content_verified,
       content_in_document, text_in_window, text_visible_in_window

  c. computer.key_press (computer) to save:
     inputs: {"keys": "{Ctrl}s"}
     postconditions: [{"assertion_type": "file_saved", "target": "<docx_path>"}]
     ↑ The target must be the actual file path from the create_docx step — not a bare filename.
     Leave it blank ("") — the orchestrator will fill it from the actual artifact path.

  d. computer.key_press to close (optional): inputs: {"keys": "{Alt}{F4}"}

For a multi-document + email workflow, the CORRECT plan is:
1. writer.generate_paragraph (writer)     -> content_generated
2. document.create_docx (document)        -> file_exists   (leave path blank — orchestrator scopes it)
3. excel.create (office)                  -> file_exists   (inputs: {"rows": [["Category","Value","Notes"],["Automation",95,"pass"]]})
4. powerpoint.create (office)             -> file_exists   (inputs: {"title": "SyncNode Demo", "slides": [{"title":"Metrics","body":"95% accuracy"},{"title":"Next Steps","body":"Deploy to prod"}]})
5. computer.launch_app (computer)         -> application_running
   inputs: {"executable": "winword"}
   postconditions: [{"assertion_type": "application_running", "target": "WINWORD.EXE", "expected": "true"}]
6. computer.uia_type (computer)           -> content_typed  ← MUST be "content_typed", nothing else
   inputs: {"text": "<paragraph content here>", "window_title": "Word", "clear_first": false, "wait_ready_ms": 3000}
   postconditions: [{"assertion_type": "content_typed", "target": "typed", "expected": "true"}]
7. computer.key_press (computer)          -> file_saved
   inputs: {"keys": "{Ctrl}s"}
   postconditions: [{"assertion_type": "file_saved", "target": ""}]
8. browser.navigate (browser)             -> page_loaded
   CRITICAL: embed ALL email fields in the URL using Gmail compose format:
   url = "https://mail.google.com/mail/u/0/?view=cm&fs=1&to=<RECIPIENT>&su=<SUBJECT>&body=<BODY>"
   URL-encode spaces as +, @ as %40 etc. Example:
   "https://mail.google.com/mail/u/0/?view=cm&fs=1&to=demo%40syncnode.ai&su=Battery+Tech+Package&body=Hi+Team%2C+Please+find+attached"
   The orchestrator ALSO fills the fields directly after navigation — but always embed them in the URL too.
   postconditions: [{"assertion_type": "page_loaded", "target": "mail.google.com"}]
9. browser.attach_file (browser)          -> attachment_present
   inputs: {}  ← LEAVE EMPTY — orchestrator auto-attaches ALL run artifacts
   postconditions: [{"assertion_type": "attachment_present", "target": "file"}]
10. workflow.pause (supervisor)           -> requires_approval: true  (NEVER add browser.click/send)
    inputs: {}
    postconditions: [{"assertion_type": "approval_requested", "target": ""}]

═══════════════════════════════════════════════════════════════
CRITICAL RULES (always apply)
═══════════════════════════════════════════════════════════════
- NEVER use a tool not in the list above. Unknown tools are rejected and fail the run.
- computer.windows_search and computer.launch_app use the "computer" agent.
- computer.uia_type, computer.uia_click, computer.key_press use the "computer" agent.
- excel.create, powerpoint.create use the "office" agent.
- document.create_docx, writer.generate_paragraph use "document" / "writer" agents.
- system.fs_search, system.fs_read, system.shell use the "system" agent.
- browser.* steps use the "browser" agent.
- The browser.attach_file step attaches ALL workspace artifacts automatically — do NOT put paths in inputs.
- For the final step with requires_approval=true, set action="workflow.pause" and agent="supervisor".
- NEVER pass a bare filename as computer.windows_search `query` without also providing `file_path`.

ASSERTION TYPE RULES — these MUST be followed exactly:
  computer.uia_type   → postcondition MUST be: {"assertion_type": "content_typed", "target": "typed"}
  computer.key_press  → postcondition MUST be: {"assertion_type": "file_saved",    "target": ""}
  computer.launch_app → postcondition MUST be: {"assertion_type": "application_running", "target": "WINWORD.EXE"}
  browser.navigate    → postcondition MUST be: {"assertion_type": "page_loaded",   "target": "mail.google.com"}
  browser.attach_file → postcondition MUST be: {"assertion_type": "attachment_present", "target": "file"}
  workflow.pause      → postcondition MUST be: {"assertion_type": "approval_requested", "target": ""}

  FORBIDDEN assertion types (these do not exist — using them ALWAYS fails the step):
    ui_element_contains, ui_element_text, element_contains, element_text,
    window_text, document_text_present, text_present, text_visible,
    word_content_verified, content_in_document, text_in_window,
    text_visible_in_window, paragraph_present, document_has_content

WORKFLOW.PAUSE IS ALWAYS THE LAST STEP — ABSOLUTE RULE:
  workflow.pause terminates the plan. NO steps may come after it. EVER.
  The orchestrator freezes at workflow.pause and waits for human approval.
  After approval the run is COMPLETED — it does NOT resume executing more steps.
  If you add steps after workflow.pause, they will NEVER execute and WILL confuse the run.
  WRONG (step 11 will never run):
    step 10: workflow.pause
    step 11: computer.launch_app  ← NEVER executes — run is frozen at step 10
  CORRECT:
    step 10: workflow.pause  ← last step — nothing after this

UIA_TYPE MUST NOT DUPLICATE DOCX CONTENT — RULE:
  If a plan includes both document.create_docx and computer.uia_type for the same document:
  - document.create_docx writes the content to the file on disk
  - computer.uia_type opens Word and the SAME content will be there already
  - The orchestrator automatically sets clear_first=true for uia_type to REPLACE (not append)
  - Do NOT write the same content twice — uia_type replaces the existing paragraph, not adds to it
  - This is correct behavior: the live-typing step shows the content appearing in real time

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
