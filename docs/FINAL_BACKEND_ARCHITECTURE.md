# Final Backend Architecture

SyncNode: **think locally, act intelligently.** Fully offline. The model
PROPOSES; deterministic systems validate, authorize, execute, observe, verify,
recover, and audit. Raw model output never becomes an OS/UI action directly.

## Execution lifecycle (per tool step)

```
model proposal
  → structured schema (compact) + strict parse
  → tool registry lookup            (unknown tool -> fail closed)
  → argument normalization          (declared aliases only; decorative drop opt-in)
  → authorization / policy          (agent scope; approval for external comms)
  → ExecutionEngine.run(ToolProposal)
        PROPOSED → VALIDATED → AUTHORIZED → LOCKED (resource leases)
        → PRECONDITION → EXECUTING → OBSERVING → VERIFYING
        → PASSED | FAILED | AMBIGUOUS
  → RecoveryEngine on failure       (RETRY/REOBSERVE/FALLBACK/REPLAN/ESCALATE/ABORT, bounded, circuit breaker)
  → audit + SSE + workflow-memory trajectory
```

Every tool in a real run is executed through `ExecutionEngine` — verified in the
golden E2E (`tool.proposed` → engine state machine → verification persisted).

## Run pipeline (orchestrator)

```
POST /runs
  → run.created
  → RunArtifactRegistry.initialize()   (clean workspace/demo/runs/<run_id>/)
  → conditional RAG (rag.query / rag.retrieval.completed, provenance)
  → intent (compact schema, GPU profile)
  → plan (compact schema) → sanitize against tool registry
  → for each step: _run_step_with_recovery -> ExecutionEngine
        - data flow: run-scoped artifact paths + typed refs
        - postcondition target canonicalization
  → external-send approval boundary (policy-enforced)
  → terminal: WAITING_APPROVAL | COMPLETED | FAILED
  → workflow.memory_recorded
```

`COMPLETED` is never declared from traversal alone: an email-drafting run stops
at `WAITING_APPROVAL` by policy even if the model omitted a send step.

## Data / artifact lifecycle

- Each run gets `workspace/demo/runs/<run_id>/{word,excel,powerpoint,email}`.
- Artifact-creating tools are routed to run-scoped paths; produced files are
  registered (`artifact://run/<run_id>/<artifact_id>`) with sha256 + producer
  step; stale files (created before the run) are rejected.
- Cross-step data flows via captured artifacts, not literal model strings;
  placeholder/prose paths are detected and replaced.

## Offline model

Local Ollama `gemma4:e4b`, GPU-resident (3.2 GB / 100% GPU / ctx 4096). No cloud
LLM/embeddings/OCR/browser/email. Cloud model tags are rejected.

## Persistence

SQLite (async) with runs, steps, tool_calls, observations, verification_results,
artifacts, approvals, audit_events (hash chain), sse_events, knowledge_documents,
workflow_memory, candidate_strategies.
