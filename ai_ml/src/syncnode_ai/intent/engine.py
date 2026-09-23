"""
SyncNode — Intent Engine.
"""

from __future__ import annotations

import logging
from typing import Optional

from syncnode_ai.gateway.gateway import ModelGateway
from syncnode_ai.gateway.schemas import Message, ModelRequest
from syncnode_ai.intent.schemas import StructuredIntent

logger = logging.getLogger(__name__)

# Maximum characters of the raw goal fed to the intent model.
# Prevents context overflow on complex composite prompts.
# The planner sees the full goal; intent only needs the essence.
_GOAL_MAX_CHARS = 1200

INTENT_SYSTEM_PROMPT = """You are the SyncNode Intent Engine. Extract a structured intent JSON from the user goal.

OUTPUT: ONLY valid JSON — no markdown, no code fences, no explanation.

GOAL TYPES (pick exactly one):
  CREATE_DOCUMENT   — create/write a file (docx, xlsx, pptx, txt)
  MODIFY_DOCUMENT   — edit an existing file
  READ_DOCUMENT     — read/inspect a file
  OPEN_APPLICATION  — launch an app (Word, Excel, Notepad)
  BROWSER_NAVIGATION — open a URL or web form
  EMAIL_DRAFT       — compose/draft an email
  SEARCH_FILES      — search workspace files
  EXECUTE_WORKFLOW  — run a script or automation
  COMPOSITE         — multiple different actions combined (USE THIS for goals with 2+ distinct tasks)
  UNKNOWN           — cannot classify

For COMPOSITE goals (most real user requests), list ALL tasks in order.

REQUIRED JSON FIELDS:
{
  "schema_version": "1.0",
  "goal_type": "<one of the types above>",
  "goal_summary": "<one sentence>",
  "tasks": ["<task1>", "<task2>", ...],
  "entities": [{"entity_type": "document|application|email|person|url", "value": "<name>"}],
  "applications": ["<app names>"],
  "artifacts": ["<output filenames>"],
  "recipient": "<email or null>",
  "subject_hint": "<email subject or null>",
  "body_hint": "<email body or null>",
  "save_filename": "<primary output filename or null>",
  "constraints": [{"constraint_type": "<type>", "description": "<desc>", "is_hard": true}],
  "risk_level": "low|medium|high|critical",
  "approval_required": "none|before_external_send",
  "requires_human_stop": <true if user says stop/wait/approve before sending>,
  "confidence": 1.0
}

RULES:
- If goal mentions email + "do not send" / "stop before sending" / "wait for approval": set requires_human_stop=true, approval_required="before_external_send"
- If goal mentions Word/Excel/PowerPoint + email: goal_type=COMPOSITE
- artifacts should list every output file mentioned by name
- tasks should match the sequence of actions to perform
"""


class IntentEngine:
    def __init__(self, gateway: ModelGateway):
        self._gateway = gateway

    async def extract(
        self,
        goal: str,
        run_id: str,
        context_summary: Optional[str] = None,
    ) -> StructuredIntent:
        from syncnode_ai.routing import TaskClass, profile_registry

        # Hard-cap the goal to prevent context overflow.
        # The planner receives the full goal; intent only needs structured facts.
        goal_for_intent = goal[:_GOAL_MAX_CHARS]
        if len(goal) > _GOAL_MAX_CHARS:
            goal_for_intent += "\n[… goal truncated for intent extraction — full goal passed to planner]"
            logger.info(
                "[INTENT] goal truncated %d -> %d chars for intent extraction",
                len(goal), _GOAL_MAX_CHARS,
            )

        user_content = f"Goal:\n{goal_for_intent}"
        if context_summary:
            # Cap context summary too
            user_content += f"\n\nContext (brief):\n{context_summary[:300]}"

        profile = profile_registry.get(TaskClass.FAST_STRUCTURED)

        def _build_request(content: str) -> ModelRequest:
            return ModelRequest(
                model_id=self._gateway.model_id,
                messages=[
                    Message(role="system", content=INTENT_SYSTEM_PROMPT),
                    Message(role="user", content=content),
                ],
                caller="intent",
                run_id=run_id,
            ).model_copy(update=profile.request_overrides())

        try:
            intent, _ = await self._gateway.generate_structured(
                _build_request(user_content), StructuredIntent
            )
            logger.info(
                "[INTENT] extracted — goal_type=%s tasks=%d entities=%d run_id=%s",
                intent.goal_type.value, len(intent.tasks), len(intent.entities), run_id,
            )
            return intent
        except Exception as first_exc:
            # Fallback: strip to the bare minimum goal (first 500 chars)
            # and retry once with a simpler prompt to get any valid JSON out.
            logger.warning(
                "[INTENT] first attempt failed (%s) — retrying with stripped goal",
                repr(first_exc),
            )
            bare_goal = goal[:500]
            bare_content = (
                f"Goal (simplified): {bare_goal}\n\n"
                "Produce a minimal valid JSON intent. Use goal_type=COMPOSITE if multiple tasks."
            )
            try:
                intent, _ = await self._gateway.generate_structured(
                    _build_request(bare_content), StructuredIntent
                )
                logger.info(
                    "[INTENT] fallback succeeded — goal_type=%s run_id=%s",
                    intent.goal_type.value, run_id,
                )
                return intent
            except Exception as exc:
                from syncnode_ai.errors import IntentError
                logger.exception("[INTENT] all attempts failed — run_id=%s", run_id)
                raise IntentError(f"Intent extraction failed: {repr(exc)}") from exc
