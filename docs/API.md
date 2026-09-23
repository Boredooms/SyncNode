# SyncNode Backend API — End-to-End Frontend Integration Guide

This is the authoritative contract for connecting the Electron (or any) frontend
to the SyncNode backend. The frontend is a **thin client**: it talks only to
REST + SSE. It never imports backend Python and never touches the model,
filesystem, or OS directly.

- Base URL: `http://127.0.0.1:8000`
- API prefix: `/api/v1` (health endpoints are unprefixed)
- Content type: `application/json` (SSE stream is `text/event-stream`)
- Auth: none in Phase 1 (local, single-user, loopback only)
- Machine-readable schema: `shared/openapi/openapi.json` (regenerate with
  `python scripts/export_openapi.py`)
- Event/entity contracts: `shared/events/events.json`, `shared/schemas/entities.json`

Everything below is verified against the running backend (30 routes).

---

## 0. The one flow you must implement

```
                    ┌─────────────────────────────────────────────┐
  user types goal   │  POST /api/v1/runs   {goal}                  │
        ───────────►│  → { run_id, status:"queued" }               │
                    └───────────────┬─────────────────────────────┘
                                    │  immediately
                    ┌───────────────▼─────────────────────────────┐
   live timeline    │  GET /api/v1/runs/{run_id}/events  (SSE)     │
        ◄───────────│  render events as they arrive               │
                    └───────────────┬─────────────────────────────┘
                                    │  on approval.requested
                    ┌───────────────▼─────────────────────────────┐
   approval card    │  POST /api/v1/runs/{id}/approvals/{aid}/decide│
                    │       {decision:"approved"|"rejected"}       │
                    └───────────────┬─────────────────────────────┘
                                    │  on run.completed / .failed / .waiting_approval
                    ┌───────────────▼─────────────────────────────┐
   final detail     │  GET /runs/{id} + /steps + /artifacts +      │
        ◄───────────│  /verifications + /audit + /context          │
                    └─────────────────────────────────────────────┘
```

Everything else (knowledge editor, tool catalog, agent view, learning review) is
a separate screen that reads/writes its own endpoints.

---

## 1. Startup / health (render a status bar)

Poll these on app launch and show a health strip. All are unprefixed.

| Method | Path | Use |
|--------|------|-----|
| GET | `/health` | liveness — is the server up |
| GET | `/health/ready` | overall readiness (db + model + rag) — gate "Start" button |
| GET | `/health/model` | Gemma/Ollama status, model id, latency, capabilities |
| GET | `/health/database` | SQLite connectivity |
| GET | `/health/rag` | ChromaDB/knowledge status |
| GET | `/health/computer` | Windows UIA availability (desktop control) |
| GET | `/health/browser` | Playwright browser availability |

`GET /health/ready` →
```json
{
  "ready": true,
  "checks": {
    "database": {"status": "ok"},
    "model": {"status": "healthy", "model_id": "gemma4:e4b", "latency_ms": 20.7},
    "rag": {"status": "ok", "collections": 0}
  },
  "ts": 1789768667.4
}
```
Frontend rule: only enable "Run" when `ready === true` and `checks.model.status === "healthy"`.

`GET /health/model` returns `target_profile.capabilities` (completion, vision,
tools, thinking, context_window, quantization) — use it to show model info.

---

## 2. Runs — create and drive a workflow

### 2.1 Create a run
`POST /api/v1/runs`
```json
{ "goal": "Create a Word doc about X, an Excel table, a PPTX, then draft an email with all three attached. Do not send.",
  "failure_mode": "none" }
```
Response (returns immediately; work runs in the background):
```json
{ "run_id": "c0574206-...", "status": "queued", "goal": "...", "created_at": "...", "model_id": "gemma4:e4b" }
```
`failure_mode` is for testing only (`none` | `false_model_success_claim`); the UI
always sends `none`.

**Immediately after creating, open the SSE stream (§3) with the returned `run_id`.**

### 2.2 Run status + detail (poll or fetch on terminal event)
| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/v1/runs/{run_id}` | run status, goal, model_id, created/completed_at, error_message |
| GET | `/api/v1/runs/{run_id}/steps` | ordered steps: step_key, status, agent, verification, retries |
| GET | `/api/v1/runs/{run_id}/tools` | tool calls: tool_key, status, side_effect_type, duration_ms, error |
| GET | `/api/v1/runs/{run_id}/observations` | observations: type, application, window_title, screenshot_path/hash |
| GET | `/api/v1/runs/{run_id}/verifications` | verification results: result (PASS/FAIL/STALE/UNAVAILABLE), failure_reason, assertions |
| GET | `/api/v1/runs/{run_id}/artifacts` | produced files: name, type, path, sha256, verified |
| GET | `/api/v1/runs/{run_id}/context` | intent + RAG provenance (which knowledge the run used) |
| GET | `/api/v1/runs/{run_id}/audit` | tamper-evident audit chain: seq, type, hash, ts |
| POST | `/api/v1/runs/{run_id}/terminate` | cancel a running run |

`GET /runs/{id}` status is one of:
`queued | running | waiting_approval | completed | failed | cancelled`.

`GET /runs/{id}/steps` →
```json
{ "run_id": "...", "steps": [
  {"step_key":"create_docx","status":"completed","agent":"document","verification":"PASS","retries":0},
  {"step_key":"attach_files","status":"completed","agent":"browser","verification":"PASS","retries":0}
]}
```

`GET /runs/{id}/artifacts` → (the three produced documents in a golden run)
```json
{ "run_id":"...", "artifacts":[
  {"name":"SyncNode_Word_c0574206.docx","type":"word","path":"C:\\syncnode\\workspace\\demo\\runs\\c0574206\\word\\...docx","sha256":"601a...","verified":true},
  {"name":"SyncNode_Excel_c0574206.xlsx","type":"excel","path":"...","sha256":"da7d...","verified":true},
  {"name":"SyncNode_Presentation_c0574206.pptx","type":"powerpoint","path":"...","sha256":"7a0a...","verified":true}
]}
```

`GET /runs/{id}/context` → RAG provenance for the "knowledge used" panel:
```json
{ "run_id":"...", "context": { "rag": {
  "required": true, "reason": "task references: email, word, ...",
  "documents": [
    {"doc_id":"approval_rules","path":"policies/approval_rules.md","trust":"authoritative_policy","content_hash":"...","score":26.0}
  ]}}}
```

---

## 3. SSE — the live run timeline (primary UX)

`GET /api/v1/runs/{run_id}/events` → `text/event-stream`. Each message is
`data: {json}\n\n`. Consume with `EventSource` (or a fetch reader in Electron).
The stream sends a `: heartbeat` comment every ~30 s while idle and ends after a
terminal event.

```js
const es = new EventSource(`http://127.0.0.1:8000/api/v1/runs/${runId}/events`);
es.onmessage = (m) => {
  const evt = JSON.parse(m.data);
  timeline.push(evt);                      // evt.event_type, evt.run_id, evt.ts, ...
  if (["run.completed","run.failed","run.waiting_approval"].includes(evt.event_type)) {
    es.close();                            // stream ends on terminal events
    refreshRunDetail(runId);               // fetch steps/artifacts/verifications
  }
};
```

Every event has: `event_type`, `run_id`, `ts`, plus a type-specific payload.
The first message is always `{"event_type":"stream.connected","run_id":...}`.

### Event types the frontend renders (in order of a typical run)

| event_type | Render as | Key payload fields |
|------------|-----------|--------------------|
| `stream.connected` | (internal) stream open | run_id |
| `run.created` | "Run accepted" | goal, model_id |
| `run.started` | "Workspace ready" | run_dir |
| `rag.query` | "Consulting knowledge…" | goal |
| `rag.retrieval.completed` | knowledge chips | required, reason, documents[], count |
| `intent.completed` | parsed goal card | intent |
| `plan.created` | plan list | total_steps, steps[] |
| `plan.validated` | plan confirmed | total_steps, steps[] |
| `plan.wave_dispatched` | "Running N steps (parallel)" | wave_size, steps[], parallel |
| `agent.spawned` | agent chip appears | agent_id, step_key, action |
| `agent.plan_summary` | agent's stated intent (safe, not chain-of-thought) | agent_id, summary, step_key |
| `tool.proposed` | tool row (pending) | tool, step_key, attempt |
| `tool.authorized` | tool row (authorized) | tool, agent, risk |
| `tool.started` | tool row (running) | tool, step_key |
| `tool.invoked` | tool inputs (truncated) | tool_key, inputs |
| `tool.completed` | tool row (done) | tool_key, step_key, success |
| `observation.captured` | "Observed environment" (+ screenshot ref) | step_key, ts |
| `verification.passed` | green check | step_key, assertions |
| `verification.failed` | red X + reason | step_key, result, failure_reason |
| `recovery.started` | "Recovering…" | step_key, error_class, tier, attempt |
| `recovery.attempted` | retry counter | step_key, tier, attempt |
| `recovery.completed` | recovery outcome | step_key, outcome, circuit_open |
| `approval.requested` | **approval card** (blocking) | approval_id, step_key, action, risk |
| `approval.decided` | approval resolved | approval_id, decision |
| `workflow.memory_recorded` | "Learned from run" | task_type, success, steps |
| `run.waiting_approval` | **paused banner + approve/reject** | approval_id, action |
| `run.completed` | success banner | run_id |
| `run.failed` | error banner | error |
| `run.cancelled` | cancelled banner | — |

Rule: **never render private chain-of-thought.** The backend only emits decision
summaries, tool calls, observations, verifications, recovery, and approvals.

---

## 4. Approvals — the human boundary

External communication (sending email) never happens automatically. When a run
needs approval it emits `approval.requested` / `run.waiting_approval` and pauses
at `waiting_approval`. The frontend shows an approval card and posts the decision.

`POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide`
```json
{ "decision": "approved", "reason": "Looks good" }   // or "rejected"
```
Response:
```json
{ "approval_id": "...", "decision": "approved" }
```
- `approved` → run continues (status returns to `running`).
- `rejected` → run ends `failed`. The send is never performed on rejection.

The `approval_id` comes from the `approval.requested` / `run.waiting_approval`
SSE event (field `approval_id`).

---

## 5. Tools & Agents catalog (for a "capabilities" screen)

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/v1/tools` | full tool catalog (29 tools) with metadata |
| GET | `/api/v1/tools/{key}` | one tool's full metadata + schemas |
| GET | `/api/v1/agents` | agent definitions + their scoped tools |

`GET /api/v1/tools` →
```json
{ "tools": [
  {"key":"document.create_docx","name":"Create DOCX","version":1,"description":"...",
   "capabilities":["document_creation"],"risk_class":"medium","side_effect_type":"IDEMPOTENT_LOCAL",
   "idempotency":"idempotent","verification_strategy":"always","required_permissions":[],
   "supported_applications":[],"resource_locks":[],"input_schema":{...},"output_schema":{...}}
]}
```

`GET /api/v1/agents` → each agent with `agent_id, name, description, capabilities,
risk_class, allowed_tools, scoped_tools`. Use this to draw the agent roster and
which tools each agent may call.

---

## 6. Knowledge base (Markdown editor screen)

The knowledge base is editable local Markdown with YAML front matter and trust
tiers. These endpoints power the editor.

| Method | Path | Use |
|--------|------|-----|
| GET | `/api/v1/knowledge` | list documents (summaries) |
| GET | `/api/v1/knowledge/{id}` | full document incl. `body` |
| POST | `/api/v1/knowledge` | create `{path, content}` (path must end `.md`) |
| PUT | `/api/v1/knowledge/{id}` | update `{path, content}` |
| DELETE | `/api/v1/knowledge/{id}` | delete |
| GET | `/api/v1/knowledge/{id}/history` | version/hash history |
| POST | `/api/v1/knowledge/{id}/reindex` | re-parse + record metadata |
| POST | `/api/v1/knowledge/search` | `{query, tags?, limit?}` → ranked docs w/ score |

Document summary shape:
```json
{ "id":"approval_rules","type":"policy","path":"policies/approval_rules.md",
  "title":"Approval Rules","trust":"authoritative_policy","version":1,"status":"active",
  "tags":["approval","email"],"content_hash":"..." }
```
Trust tiers (`trust`): `authoritative_policy` (only files under `policies/`),
`reference`, `workflow`, `untrusted`. The editor should badge these; the backend
enforces that a non-policy file cannot claim `authoritative_policy`.

`POST /api/v1/knowledge` body: `content` is the full Markdown including front
matter, e.g.:
```
---
id: excel
type: application
trust: reference
status: active
tags:
  - office
---
# Microsoft Excel
...
```

---

## 7. Learning (workflow memory review screen)

Learning is human-gated; candidate strategies are never auto-promoted.

| Method | Path | Use |
|--------|------|-----|
| GET | `/api/v1/learning/memory/{task_type}` | best past strategies (hints) for a task type |
| GET | `/api/v1/learning/candidates` | candidate strategies (review queue); `?lifecycle=CANDIDATE` filter |
| POST | `/api/v1/learning/candidates/{id}/review` | human decision |

Review body:
```json
{ "decision": "approve", "reviewer": "human", "reason": "..." }
```
`decision` ∈ `approve` | `reject` | `activate` | `deprecate`. Promotion to ACTIVE
requires two explicit steps: `approve` (CANDIDATE→APPROVED) then `activate`
(APPROVED→ACTIVE). The UI should present this as a two-step review.

Candidate shape: `{id, task_type, summary, proposed_tool_sequence, rationale,
lifecycle, source_run_id, reviewed_by, review_reason}` where lifecycle ∈
`CANDIDATE | EVALUATING | APPROVED | ACTIVE | DEPRECATED | REJECTED`.

---

## 8. Complete route table (30 routes)

```
GET   /health
GET   /health/ready
GET   /health/model
GET   /health/database
GET   /health/rag
GET   /health/computer
GET   /health/browser

POST  /api/v1/runs
GET   /api/v1/runs/{run_id}
GET   /api/v1/runs/{run_id}/steps
GET   /api/v1/runs/{run_id}/tools
GET   /api/v1/runs/{run_id}/observations
GET   /api/v1/runs/{run_id}/verifications
GET   /api/v1/runs/{run_id}/artifacts
GET   /api/v1/runs/{run_id}/context
GET   /api/v1/runs/{run_id}/audit
GET   /api/v1/runs/{run_id}/events         (SSE, text/event-stream)
POST  /api/v1/runs/{run_id}/terminate
POST  /api/v1/runs/{run_id}/approvals/{approval_id}/decide

GET   /api/v1/tools
GET   /api/v1/tools/{key}
GET   /api/v1/agents

GET   /api/v1/knowledge
POST  /api/v1/knowledge
GET   /api/v1/knowledge/{doc_id}
PUT   /api/v1/knowledge/{doc_id}
DELETE /api/v1/knowledge/{doc_id}
GET   /api/v1/knowledge/{doc_id}/history
POST  /api/v1/knowledge/{doc_id}/reindex
POST  /api/v1/knowledge/search

GET   /api/v1/learning/memory/{task_type}
GET   /api/v1/learning/candidates
POST  /api/v1/learning/candidates/{candidate_id}/review
```

---

## 9. Errors

- `404` — run / approval / knowledge / tool not found.
- `400` — bad request (e.g. approval already decided, knowledge path not `.md`,
  invalid review decision).
- `503` — from `/health/ready` when a critical subsystem is down.
- `500` — unhandled: body `{ "error": "...", "type": "ExceptionType" }`.

Errors are JSON. Show `error`/`detail` in a toast; for `/health/ready` 503, keep
the "Run" button disabled and show which check failed.

---

## 10. Minimal frontend client (reference)

```ts
const BASE = "http://127.0.0.1:8000";

export async function createRun(goal: string) {
  const r = await fetch(`${BASE}/api/v1/runs`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, failure_mode: "none" }),
  });
  return r.json(); // { run_id, status, ... }
}

export function streamRun(runId: string, onEvent: (e: any) => void) {
  const es = new EventSource(`${BASE}/api/v1/runs/${runId}/events`);
  es.onmessage = (m) => {
    const e = JSON.parse(m.data);
    onEvent(e);
    if (["run.completed","run.failed","run.waiting_approval"].includes(e.event_type)) es.close();
  };
  return () => es.close();
}

export async function decideApproval(runId: string, approvalId: string, decision: "approved"|"rejected") {
  const r = await fetch(`${BASE}/api/v1/runs/${runId}/approvals/${approvalId}/decide`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  return r.json();
}

export const getRun          = (id: string) => fetch(`${BASE}/api/v1/runs/${id}`).then(r => r.json());
export const getSteps        = (id: string) => fetch(`${BASE}/api/v1/runs/${id}/steps`).then(r => r.json());
export const getArtifacts    = (id: string) => fetch(`${BASE}/api/v1/runs/${id}/artifacts`).then(r => r.json());
export const getVerifications= (id: string) => fetch(`${BASE}/api/v1/runs/${id}/verifications`).then(r => r.json());
export const getContext      = (id: string) => fetch(`${BASE}/api/v1/runs/${id}/context`).then(r => r.json());
export const getAudit        = (id: string) => fetch(`${BASE}/api/v1/runs/${id}/audit`).then(r => r.json());
export const listTools       = ()           => fetch(`${BASE}/api/v1/tools`).then(r => r.json());
export const listAgents      = ()           => fetch(`${BASE}/api/v1/agents`).then(r => r.json());
export const listKnowledge   = ()           => fetch(`${BASE}/api/v1/knowledge`).then(r => r.json());
```

---

## 11. Suggested screen → endpoint map

| Screen | Reads | Writes |
|--------|-------|--------|
| Home / new run | `/health/ready`, `/health/model` | `POST /runs` |
| Run timeline (live) | SSE `/runs/{id}/events` | `POST /runs/{id}/terminate` |
| Approval card | (from SSE) | `POST /runs/{id}/approvals/{aid}/decide` |
| Run detail / evidence | `/runs/{id}` `/steps` `/tools` `/observations` `/verifications` `/artifacts` `/context` `/audit` | — |
| Capabilities | `/tools`, `/agents` | — |
| Knowledge editor | `/knowledge`, `/knowledge/{id}`, `/knowledge/{id}/history` | POST/PUT/DELETE `/knowledge`, `/reindex`, `/search` |
| Learning review | `/learning/candidates`, `/learning/memory/{task}` | `POST /learning/candidates/{id}/review` |

---

## 12. Contract stability

- Event names and entity fields are additive. New events/fields may appear;
  existing names/meanings do not change without a version bump in
  `shared/events/events.json` / `shared/schemas/entities.json`.
- Regenerate the REST contract after backend API changes:
  `python scripts/export_openapi.py` → `shared/openapi/openapi.json`.
- The frontend should tolerate unknown `event_type` values (ignore/log), so a
  newer backend never breaks an older client.
