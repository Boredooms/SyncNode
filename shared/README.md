# SyncNode Frontend Contract (`shared/`)

Stable, language-neutral contracts the future Electron client consumes. Electron
is a THIN CLIENT over these; it must never import backend Python classes.

- `events/events.json` — canonical SSE / audit event names + envelope. The
  backend emits only decision summaries, tool calls, observations, verification,
  recovery, and approval events — never private chain-of-thought.
- `schemas/entities.json` — JSON-schema shapes for Run, RunStep, Agent, ToolCall,
  Tool, Observation, Verification, Recovery, Approval, Artifact,
  KnowledgeDocument, WorkflowMemory, CandidateStrategy, ModelCall, SSEEvent.
- `openapi/openapi.json` — the live FastAPI REST contract (regenerate with
  `python scripts/export_openapi.py`).

## Endpoint groups (30 paths)

- Runs: create/get; steps, tools, observations, verifications, context (RAG
  provenance), audit, artifacts; SSE events; terminate; approvals decide.
- Knowledge: list/get/create/update/delete/history/reindex/search.
- Tools & Agents: full tool catalog + per-agent scoped tools.
- Learning: best strategies, candidate review queue, human review decisions.

## Contract stability rules

- Event names are additive: new events may be added; existing names/meanings do
  not change without a version bump here.
- Entity fields are additive; removals/renames bump `version`.
- Electron renders the full run lifecycle (agent → tool → screen → result →
  verification → recovery → approval) using only these contracts.

Electron itself is intentionally NOT built yet.
