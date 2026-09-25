"""
SyncNode — Prompt Enricher.

A lightweight pre-pass that runs gemma3:1b on CPU to extract key structured
fields from any user prompt BEFORE the main gemma4:e4b intent/planning calls.

Memory safety contract:
- gemma3:1b is always invoked with num_gpu=0  (CPU only, never touches VRAM)
- keep_alive=0 so Ollama unloads it immediately after the call
- The main gateway (gemma4:e4b on GPU) is NOT created before this call returns,
  preventing any chance of concurrent VRAM pressure
- If enrichment fails for any reason the original goal is returned unchanged —
  this is a best-effort pre-pass, never a hard dependency

Output: an EnrichedContext that the orchestrator stores in self._artifacts before
the intent engine runs. Downstream tools (_inject_email_field, planner) read from
it directly without any regex fallbacks.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Enricher schema ──────────────────────────────────────────────────────────

@dataclass
class EnrichedContext:
    """Structured fields extracted from the raw user prompt."""
    recipient_email: str = ""
    subject: str = ""
    body_hint: str = ""          # Suggested email body text from the user's goal
    attachment_filename: str = ""
    save_filename: str = ""      # Desired output document filename (e.g. "tree.docx")
    requires_approval: bool = False
    goal_type_hint: str = ""     # e.g. "email_draft", "document", "spreadsheet"
    raw_extras: dict[str, Any] = field(default_factory=dict)

    def is_useful(self) -> bool:
        """True if we extracted at least one actionable field."""
        return bool(
            self.recipient_email or self.subject or self.body_hint
            or self.attachment_filename or self.save_filename
        )

    def as_context_block(self) -> str:
        """Format as a structured block prepended to the intent prompt."""
        lines = ["[PRE-EXTRACTED CONTEXT]"]
        if self.recipient_email:
            lines.append(f"recipient_email: {self.recipient_email}")
        if self.subject:
            lines.append(f"email_subject: {self.subject}")
        if self.body_hint:
            lines.append(f"email_body: {self.body_hint}")
        if self.save_filename:
            lines.append(f"save_filename: {self.save_filename}")
        if self.attachment_filename:
            lines.append(f"attachment: {self.attachment_filename}")
        if self.requires_approval:
            lines.append("requires_approval: true")
        lines.append("[END PRE-EXTRACTED CONTEXT]")
        return "\n".join(lines)


# ── Extraction prompt ────────────────────────────────────────────────────────

_ENRICHER_SYSTEM = """\
You are a structured information extractor. Given a user's automation goal, \
extract ONLY the fields that are explicitly present. Output compact JSON only — \
no markdown, no explanation, no extra keys.

Schema (use null for missing fields):
{
  "recipient_email": null,
  "subject": null,
  "body_hint": null,
  "save_filename": null,
  "attachment_filename": null,
  "requires_approval": false,
  "goal_type_hint": null
}

Rules:
- recipient_email: a valid email address (user@domain.tld) ONLY if one is explicitly stated. If absent set null.
- subject: the email subject line text ONLY if explicitly stated. If absent set null.
- body_hint: the email body text ONLY if explicitly stated verbatim. If absent set null.
- save_filename: the output document filename including extension (e.g. "report.docx") ONLY if explicitly stated. If absent set null.
- attachment_filename: the file to attach ONLY if explicitly stated. If absent set null.
- requires_approval: true only if user says "stop for approval", "wait for approval", or "before sending".
- goal_type_hint: one of document|email_draft|spreadsheet|presentation|composite based on the primary task.

CRITICAL: Never copy these instructions into your output. Never invent values.
"""


# ── Enricher class ───────────────────────────────────────────────────────────

class PromptEnricher:
    """
    Runs gemma3:1b on CPU to extract structured fields from a raw goal.

    Designed to be called ONCE per run, BEFORE the main gateway is opened,
    so there is zero overlap with gemma4:e4b VRAM usage.
    """

    ENRICHER_MODEL = "gemma3:1b"
    OLLAMA_URL = "http://127.0.0.1:11434"
    TIMEOUT_S = 30          # generous for a CPU call
    MAX_TOKENS = 256        # we only need a small JSON object

    async def enrich(self, goal: str, run_id: str = "") -> EnrichedContext:
        """
        Call gemma3:1b (CPU-only, keep_alive=0) to extract structured fields.

        Returns an EnrichedContext. On any failure returns an empty context
        so the rest of the pipeline continues unchanged.
        """
        t0 = time.monotonic()
        ctx = EnrichedContext()
        try:
            raw_json = await self._call_model(goal)
            ctx = self._parse(raw_json, goal)
            elapsed = round((time.monotonic() - t0) * 1000)
            logger.info(
                "[ENRICHER] extracted in %dms — email=%r subject=%r file=%r",
                elapsed, ctx.recipient_email, ctx.subject, ctx.save_filename,
            )
        except Exception as exc:  # noqa: BLE001 — never crash the pipeline
            logger.warning("[ENRICHER] enrichment failed (non-fatal): %s", exc)
        return ctx

    async def _call_model(self, goal: str) -> str:
        """POST to Ollama /api/chat with num_gpu=0 and keep_alive=0."""
        payload = {
            "model": self.ENRICHER_MODEL,
            "messages": [
                {"role": "system", "content": _ENRICHER_SYSTEM},
                {"role": "user", "content": f"Goal: {goal}"},
            ],
            "stream": False,
            "keep_alive": 0,          # unload immediately — no VRAM squatting
            "options": {
                "num_gpu": 0,          # ALWAYS CPU — never touch VRAM
                "num_ctx": 512,        # small context, short output
                "num_predict": self.MAX_TOKENS,
                "temperature": 0.0,   # deterministic extraction
            },
        }
        async with httpx.AsyncClient(timeout=self.TIMEOUT_S) as client:
            resp = await client.post(
                f"{self.OLLAMA_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("message", {}).get("content", "")

    def _parse(self, raw: str, goal: str) -> EnrichedContext:
        """Parse the model's JSON output with strict type validation.
        Falls back to regex when the model echoes template text or produces invalid JSON.
        """
        import re as _re

        # Strip markdown fences and find the first {...} block
        cleaned = _re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        m = _re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                data = json.loads(m.group(0))
                ctx = EnrichedContext()

                # ── recipient_email: must be a real email address ──────────
                raw_email = data.get("recipient_email") or ""
                if isinstance(raw_email, str) and _re.fullmatch(r"[\w.+-]+@[\w.-]+\.\w+", raw_email.strip()):
                    ctx.recipient_email = raw_email.strip()
                # If the model echoed template text or gave a non-email value → leave empty

                # ── subject: short text, no template phrases ────────────────
                raw_subj = data.get("subject") or ""
                if isinstance(raw_subj, str):
                    s = raw_subj.strip().strip('"').strip("'").strip()
                    if s and len(s) < 200 and not ("if present" in s.lower() or "else empty" in s.lower()):
                        ctx.subject = s

                # ── body_hint: non-empty, not a schema echo ─────────────────
                raw_body = data.get("body_hint") or ""
                if isinstance(raw_body, str):
                    b = raw_body.strip()
                    if b and "else empty" not in b.lower() and "if given" not in b.lower():
                        ctx.body_hint = b

                # ── save_filename: must end with a known extension ───────────
                raw_fn = data.get("save_filename") or ""
                if isinstance(raw_fn, str):
                    fn = raw_fn.strip()
                    if fn and _re.search(r"\.(docx|xlsx|pptx|pdf|txt)$", fn, _re.I):
                        ctx.save_filename = fn

                # ── attachment_filename: same validation ─────────────────────
                raw_att = data.get("attachment_filename") or ""
                if isinstance(raw_att, str):
                    att = raw_att.strip()
                    if att and _re.search(r"\.(docx|xlsx|pptx|pdf|txt)$", att, _re.I):
                        ctx.attachment_filename = att

                ctx.requires_approval = bool(data.get("requires_approval", False))
                raw_hint = data.get("goal_type_hint") or ""
                valid_hints = {"document", "email_draft", "spreadsheet", "presentation", "composite"}
                if isinstance(raw_hint, str) and raw_hint.strip().lower() in valid_hints:
                    ctx.goal_type_hint = raw_hint.strip().lower()

                return ctx
            except (json.JSONDecodeError, TypeError):
                pass

        # ── Regex fallback: extract directly from goal (not model output) ──
        logger.debug("[ENRICHER] JSON parse failed, falling back to regex on goal")
        ctx = EnrichedContext()
        em = re.search(r"[\w.+-]+@[\w.-]+\.\w+", goal, re.I)
        if em:
            ctx.recipient_email = em.group(0)
        fn = re.search(r"[\w_-]+\.(docx|xlsx|pptx|pdf|txt)\b", goal, re.I)
        if fn:
            ctx.save_filename = fn.group(0)
            ctx.attachment_filename = fn.group(0)
        sm = re.search(r"subject\s+([^,\.]+)", goal, re.I)
        if sm:
            ctx.subject = sm.group(1).strip().rstrip(".,;").strip('"').strip("'")
        if bm:
            ctx.body_hint = bm.group(1).strip()
        ctx.requires_approval = any(
            k in goal.lower() for k in ("stop for approval", "wait for approval", "before sending")
        )
        return ctx


# Module-level singleton — created once, reused across runs
prompt_enricher = PromptEnricher()
