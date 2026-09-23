# LangGraph Execution Model

LangGraph is the real orchestration control plane. `SyncNodeGraph`
(`backend/.../workflow/graph.py`) compiles a `StateGraph(SyncNodeState)` and
`ainvoke`s it for every run. Verified: the three-artifact golden E2E runs
entirely through this graph.

## Graph

```
START → rag → intent → plan → execute → finalize → END
```

- **rag** — conditional RAG (`rag.query`/`rag.retrieval.completed`, provenance).
- **intent** — structured intent (compact schema, GPU profile).
- **plan** — structured DAG (validated + sanitized against the tool registry).
- **execute** — runs the plan as **dependency-ordered, resource-aware waves**
  (see PARALLEL_EXECUTION). Each step is dispatched to `g_execute_step`, which
  routes through the deterministic ExecutionEngine + RecoveryEngine.
- **finalize** — resolves the terminal state (WAITING_APPROVAL / COMPLETED /
  FAILED). Re-raises an approval signal so the existing approval handling applies.

## Typed state

`SyncNodeState` (`workflow/state.py`) is a `TypedDict` with reducer annotations
(`operator.add`, dict-merge) on fields that parallel branches append to
(`completed_agents`, `artifacts`, `tool_calls`, `verifications`, `errors`, …) so
fan-in joins are deterministic rather than last-writer-wins. Terminal statuses:
`COMPLETED, WAITING_APPROVAL, FAILED, CANCELLED, PAUSED, RECOVERY_EXHAUSTED`.

## Authoritative execution

The graph never executes a tool directly. `g_execute_step → _execute_step →
_run_step_with_recovery → ExecutionEngine.run(ToolProposal)`:

```
PROPOSED → VALIDATED → AUTHORIZED → LOCKED → PRECONDITION
         → EXECUTING → OBSERVING → VERIFYING → PASSED | FAILED | AMBIGUOUS
```

On failure the RecoveryEngine classifies the error and returns a tier
(RETRY / REOBSERVE / FALLBACK / REPLAN / ESCALATE / ABORT) with backoff and a
per-(step,error) circuit breaker.

## COMPLETED is earned, not traversal

`finalize` never marks COMPLETED just because the graph reached END. An
email-drafting run stops at WAITING_APPROVAL by policy (`_external_send_pending`)
even if the model omitted a send step; any failed critical step fails the run.

## Honest scope

The graph uses wave-based `gather` fan-out rather than LangGraph `Send`
fan-out-loops (Send-based state merging proved fragile for this loop shape).
Real branch overlap is proven in `backend/tests/unit/test_graph_parallel.py`.
Physical step execution is serialized on SQLite (single writer); see
PARALLEL_EXECUTION.
