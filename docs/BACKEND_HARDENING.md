# SyncNode Backend Hardening — Phase Report

This phase turned the working prototype into a hardened backend platform ready
to be consumed by Electron later. Electron was NOT built. Every claim below is
backed by a passing test or a verified run.

## Summary of delivered phases

| Phase | Deliverable | Evidence |
|-------|-------------|----------|
| A | Structured-output compaction + per-agent tool-schema scoping | `gateway/_schema.py`; 80–83% schema-token reduction (`scripts/measure_schema.py`); Gate B structured passes |
| B | Tool Registry hardening + strict validation + declared aliases | `tools/registry.py`; 12 anti-hallucination unit tests |
| C | Deterministic Execution Engine + resource locks | `runtime/execution_engine.py`, `runtime/locks.py`; 11 unit tests (state machine + locks) |
| D | Real Excel + PowerPoint tools; office agent; structure verifiers | `office/tools.py`; 3 office tests + 2 golden office tests |
| E | Local Markdown knowledge base + safety tiers + APIs | `knowledge/`; 9 seed docs; 6 tests (tier downgrade + injection-is-data + jailed write) |
| F | Conditional RAG genuinely used by the golden workflow | `ai_ml/rag/conditional.py`; 5 tests; golden run emits `rag.query`/`rag.retrieval.completed` with provenance |
| G | Workflow memory + deterministic reward + human-gated learning | `learning/`; 9 tests (no auto-promotion; explicit 2-step promotion) |
| H | Recovery engine: error classes, tiers, backoff, circuit breaker | `recovery/engine.py`; 8 tests |
| I | Frontend contract layer (schemas/events/OpenAPI) | `shared/`; 30-path OpenAPI export |
| J | Full regression + expanded golden E2E | 59 backend tests pass; golden E2E reaches `waiting_approval` |

## Security invariants preserved

- Tool registry is authoritative; unknown tools/args fail closed. Only
  **explicitly declared** aliases are normalized. A per-tool opt-in
  (`drop_decorative_args`) drops universally-decorative arg names
  (style/tone/length…) for content tools only; strict tools still reject them.
- Verification never weakened: assertion-type synonyms map to **real** handlers;
  unknown assertion types still FAIL CLOSED. All assertions check real evidence
  (file/hash/process/DOM), never a model claim.
- Approval boundary enforced by policy (not the model's flag): send/finalize
  browser clicks are gated; the golden run stops at `waiting_approval`.
- Knowledge safety tiers: only files under `knowledge/policies/` can be
  `authoritative_policy`; reference/workflow/untrusted content is data, never a
  control plane. Injection content cannot change policy.
- Learning is human-gated: failures create CANDIDATE strategies; promotion to
  ACTIVE requires explicit human approve→activate. No run mutates production
  policy, tool permissions, or prompts.
- Local-only inference and workspace jail unchanged.

## Verified golden run (multi-step, model-driven)

`writer → docx → verify → open Word → verify running → navigate compose →
verify page → fill fields → verify field values → attach real docx → verify
attachment → STOP at approval`. Final status `waiting_approval`, 41 audit
events, RAG retrieved `approval_rules`/`workspace_rules` (authoritative) +
`email_draft`/`word` (reference/workflow), workflow memory recorded
(`email_draft_workflow`, reward 7.2). Send never executed.

## Model-variance hardening (general, not per-token)

An 8B model emits varied tool-arg and assertion-type names each run. Rather than
patch each token, three general mechanisms absorb the variance safely:

1. Declared arg aliases + opt-in decorative-arg dropping (tool registry).
2. Assertion-type alias map + morphological normalizer (verification), still
   fail-closed on truly unknown types.
3. Postcondition target canonicalization to the artifact the tool actually
   produced; bounded inter-step data flow with placeholder/prose-path detection.

## Deferred (honest scope)

- The `ExecutionEngine` and `RecoveryEngine` are built and unit-tested but not
  yet wired into the sequential orchestrator's step loop (the orchestrator still
  fails fast). Wiring the retry/recovery loop is the natural next step and does
  not change any contract.
- Full COM-based live Office UIA manipulation (beyond launch/observe + file
  artifacts) is not implemented; deterministic file tools cover the golden path.
- ChromaDB embedding retrieval is stubbed in favor of a lexical retriever behind
  the same `Retriever` interface (swap without API changes).
