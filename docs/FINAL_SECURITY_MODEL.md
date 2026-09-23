# Final Security Model

All invariants below are enforced in code and covered by tests.

## Local-only
- Inference is local Ollama on loopback; `:cloud` model tags are rejected
  (`ModelGateway._enforce_local_model`). No cloud embeddings/OCR/browser/email.
- RAG, knowledge, DB, tools are all local.

## Model is not authority
- Raw model output never becomes an OS/UI action. Every tool call passes:
  schema → registry → alias normalization → authorization → ExecutionEngine →
  observe → verify → audit.
- Approval boundary is policy-enforced (`_requires_approval_by_policy` +
  `_external_send_pending`), independent of the model's `requires_approval` flag.
  The golden run pauses at `WAITING_APPROVAL`; the send tool is never executed.

## Fail closed
- Unknown tool → `ToolNotFoundError`. Unknown argument → `ToolError` (only
  declared aliases normalized; decorative-drop is opt-in per tool).
- Unknown assertion type → verification FAIL (no "probably successful"
  fallback). Synonyms map only through an explicit registry + bounded normalizer.
- Unavailable tool dependency → `ToolUnavailableError`.

## Workspace + run jail
- All file writes are canonicalized and validated inside the workspace root
  (`_safe_path`). Each run is further isolated to
  `workspace/demo/runs/<run_id>/`; artifacts created before the run are rejected
  (stale-artifact protection).

## Knowledge safety tiers
- Only files under `knowledge/policies/` may be `authoritative_policy`; any other
  file claiming it is downgraded to `reference`. Reference/workflow/untrusted
  content is data, never control flow. Injection text cannot change policy.

## Learning safety
- Failures create CANDIDATE strategies; promotion to ACTIVE requires explicit
  human approve→activate. No auto-promotion. No model-weight mutation.

## Auditability
- Tamper-evident SHA-256 audit chain, persisted per run; verifiable via
  `AuditEngine.verify_chain`.

## Explicitly not done
- No UAC/secure-desktop automation, no credential harvesting, no CAPTCHA bypass,
  no anti-bot evasion, no cross-user desktop control, no real external email
  send, no unrestricted shell/arbitrary-code tool.
