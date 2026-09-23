# FRONTEND_API_INTEGRATION.md

# SyncNode Electron Frontend — End-to-End API Integration Specification

> **PURPOSE**
>
> This document is the authoritative implementation handoff for wiring the Electron frontend to the existing SyncNode backend.
>
> The frontend must consume the backend exactly as it exists through its documented REST + SSE contracts.
>
> **ABSOLUTE RULE: DO NOT MODIFY THE BACKEND.**
>
> The implementation work covered by this document is FRONTEND ONLY.

---

# 1. NON-NEGOTIABLE FRONTEND-ONLY RULE

The backend is already implemented, tested, and treated as frozen.

The frontend implementation MUST NOT modify:

```text
backend/
ai_ml/
Python services
LangGraph
LangChain
ModelGateway
ModelRouter
ExecutionEngine
RecoveryEngine
ToolRegistry
AgentRegistry
VerificationEngine
Policy/Approval logic
Database models
Database migrations
Backend persistence
Backend routes
Backend service logic
Ollama integration
Python computer tools
Python browser tools
Python Office tools
```

Do not "fix" backend behavior from the frontend.

Do not rewrite endpoints.

Do not add frontend-specific endpoints.

Do not change API response shapes.

Do not modify backend semantics to make the UI easier.

Do not duplicate backend execution logic inside Electron.

The frontend task is:

```text
READ EXISTING CONTRACTS
        ↓
GENERATE/DEFINE TYPES
        ↓
BUILD TYPED API CLIENT
        ↓
CONNECT REST
        ↓
CONNECT SSE
        ↓
MAP EVENTS TO STATE
        ↓
RENDER REAL BACKEND STATE
        ↓
SEND USER ACTIONS THROUGH EXISTING APIs
```

Nothing in this document authorizes backend changes.

If a backend mismatch is discovered:

```text
1. inspect the existing OpenAPI contract
2. inspect the existing API integration guide
3. inspect the actual response/event
4. fix the frontend mapping if the frontend is wrong
5. document the mismatch
6. DO NOT EDIT BACKEND
```

---

# 2. READ ALL DOCUMENTATION BEFORE IMPLEMENTING

Before writing frontend code, the implementing editor must read the complete relevant documentation already present in the repository.

At minimum, read:

```text
docs/
```

including every architecture, AI/ML, execution, workflow, verification, audit, knowledge, memory, tool, and frontend-related Markdown document that is present.

Also read:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

and the frontend design documents:

```text
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
docs/FRONTEND_API_INTEGRATION.md
```

and any existing:

```text
README.md
ARCHITECTURE.md
DESIGN.md
```

that describe the current project.

Do not begin implementation after reading only one document.

Build a mental map first:

```text
SYNCNODE IDEA
     ↓
AI BRAIN
     ↓
MODEL GATEWAY
     ↓
CONTEXT / TOKEN / INTENT
     ↓
PLANNER
     ↓
AGENTS
     ↓
TOOLS
     ↓
EXECUTION
     ↓
OBSERVATION
     ↓
VERIFICATION
     ↓
RECOVERY
     ↓
RAG / KNOWLEDGE
     ↓
WORKFLOW MEMORY
     ↓
AUDIT
     ↓
REST / SSE
     ↓
ELECTRON
```

The frontend must represent this architecture instead of inventing a different product model.

---

# 3. SOURCE OF TRUTH ORDER

When documentation overlaps, use this order for API integration:

```text
1. shared/openapi/openapi.json
2. shared/events/events.json
3. shared/schemas/entities.json
4. existing frontend integration documentation
5. other architecture documents
```

Do not infer request/response fields from screenshots when a contract exists.

Do not invent fields because they would be convenient.

---

# 4. BACKEND CONNECTION

The frontend talks to the local backend:

```text
http://127.0.0.1:8000
```

API prefix:

```text
/api/v1
```

Health routes are unprefixed.

SSE:

```text
text/event-stream
```

The frontend is a local single-user thin client.

The renderer must not communicate with Ollama directly.

The renderer must not communicate with SQLite directly.

The renderer must not execute Python directly.

The renderer must not control Windows directly.

All runtime behavior goes through the backend.

---

# 5. ELECTRON BOUNDARY

Use:

```text
Electron Main
      ↓
Preload
      ↓
Renderer / React
      ↓
Typed API Client
      ↓
REST + SSE
      ↓
SyncNode Backend
```

The renderer should not receive unrestricted Node capabilities.

Use:
- context isolation
- secure preload
- minimal IPC
- typed frontend services

Do not expose unrestricted:

```text
fs
child_process
shell
process
PowerShell
Python
```

to renderer code.

---

# 6. FRONTEND API CLIENT

Create a typed API layer.

Suggested structure:

```text
src/
  services/
    api/
      client.ts
      health.ts
      runs.ts
      agents.ts
      tools.ts
      artifacts.ts
      observations.ts
      verifications.ts
      context.ts
      audit.ts
      approvals.ts
      knowledge.ts
      learning.ts
```

If the existing frontend structure differs, adapt it without changing the backend.

---

# 7. HTTP CLIENT REQUIREMENTS

Create one central HTTP client.

Responsibilities:

- base URL
- JSON headers
- timeout
- request cancellation
- response parsing
- structured error handling
- API version handling
- development diagnostics

Do not scatter raw:

```ts
fetch("http://127.0.0.1:8000/...")
```

through UI components.

All requests should go through the API service layer.

---

# 8. ERROR MODEL

Normalize HTTP failures for the frontend.

At minimum preserve:

```text
status
error
type
detail
```

Expected categories:

```text
404
resource not found

400
invalid request / invalid action

503
backend not ready

500
unexpected backend failure
```

The UI should convert these into understandable states.

Never display a raw backend stack trace as the primary UX.

A developer-details drawer may show technical information.

---

# 9. HEALTH INTEGRATION

The startup flow must call:

```text
GET /health
GET /health/ready
GET /health/model
GET /health/database
GET /health/rag
GET /health/computer
GET /health/browser
```

Use these to populate the startup sequence.

---

# 10. READY GATE

The application must not allow a new run to start until:

```json
{
  "ready": true
}
```

and:

```text
checks.model.status === "healthy"
```

are satisfied.

Render:

```text
SYSTEM READY
```

or:

```text
SYSTEM NOT READY
```

using actual backend data.

Do not hardcode "ready".

---

# 11. MODEL HEALTH UI

Show local model information from the backend.

Example information:

```text
Gemma 4 E4B
Ollama
GPU
context window
quantization
capabilities
latency
```

The frontend must not query Ollama itself.

Use the backend model-health endpoint.

---

# 12. DATABASE / RAG / COMPUTER / BROWSER STATUS

Render subsystem health:

```text
Database
RAG
Desktop
Browser
```

Each state:

```text
healthy
degraded
unavailable
unknown
```

Use backend values.

Never fake health.

---

# 13. CREATE RUN — PRIMARY USER FLOW

The primary action is:

```text
POST /api/v1/runs
```

Request:

```json
{
  "goal": "..."
}
```

The existing API guide also supports:

```json
{
  "goal": "...",
  "failure_mode": "none"
}
```

The UI should use the backend-supported shape exactly.

`failure_mode` remains testing-only if the existing backend specifies that.

Normal production UI uses:

```text
failure_mode = none
```

---

# 14. CREATE RUN CLIENT

Create:

```ts
createRun(goal: string): Promise<RunCreateResponse>
```

Do not block the UI waiting for full execution.

Expected flow:

```text
user submits goal
    ↓
POST /runs
    ↓
receive run_id
    ↓
switch to active-run screen
    ↓
connect SSE immediately
```

---

# 15. RUN OBJECT

The frontend must support the run fields returned by the actual backend.

At minimum expect the concepts:

```text
run_id
status
goal
model_id
created_at
completed_at
error_message
```

Do not assume extra fields.

Generate TypeScript types from the existing schemas/OpenAPI where practical.

---

# 16. RUN STATUS

Support:

```text
queued
running
waiting_approval
completed
failed
cancelled
```

Do not invent frontend-only backend statuses.

The UI may derive presentation stages such as:

```text
UNDERSTANDING
PLANNING
EXECUTING
VERIFYING
RECOVERING
WAITING FOR APPROVAL
```

from real events, but the backend status remains authoritative.

---

# 17. IMMEDIATELY OPEN SSE

After `POST /runs` returns:

```text
run_id
```

immediately start:

```text
GET /api/v1/runs/{run_id}/events
```

Do not wait several seconds before subscribing.

This prevents missing early events.

---

# 18. SSE CONNECTION MANAGER

Create:

```text
src/services/sse/runStream.ts
```

Responsibilities:

- connect
- parse events
- dispatch events
- reconnect where safe
- close on terminal event
- handle heartbeat
- prevent duplicate streams
- expose connection state

Connection state:

```text
CONNECTING
CONNECTED
RECONNECTING
CLOSED
ERROR
```

---

# 19. SSE MESSAGE FORMAT

Each SSE message contains:

```text
data: {json}

```

Parse the JSON into the frontend event union.

The first event is:

```text
stream.connected
```

Heartbeat comments must not be treated as application events.

---

# 20. SSE EVENT ROUTER

Create one central event router.

Example:

```ts
routeEvent(event)
```

It should dispatch by:

```text
event_type
```

to the appropriate store/reducer.

Never make every React component independently subscribe to the same SSE stream.

One run stream:

```text
SSE
 ↓
Event Router
 ↓
Run Store
 ├─ Timeline
 ├─ Agents
 ├─ Tools
 ├─ Workflow
 ├─ Observations
 ├─ Verification
 ├─ Artifacts
 ├─ Approval
 └─ Run Status
```

---

# 21. UNKNOWN SSE EVENTS

The backend may add new event types.

The frontend MUST tolerate them.

Rule:

```text
unknown event
→ log safely
→ preserve connection
→ do not crash
→ optionally show "new event" in developer diagnostics
```

Never make an unknown event fatal.

---

# 22. EVENT TYPES TO SUPPORT

Support the backend's event contract, including the current documented events:

```text
stream.connected
run.created
run.started

rag.query
rag.retrieval.completed

intent.completed

plan.created
plan.validated
plan.wave_dispatched

agent.spawned
agent.started
agent.waiting
agent.plan_summary
agent.completed
agent.failed
agent.cancelled

tool.proposed
tool.validated
tool.authorized
tool.started
tool.invoked
tool.completed
tool.failed

observation.captured

verification.passed
verification.failed

recovery.started
recovery.attempted
recovery.completed
recovery.exhausted

artifact.created
artifact.verified

approval.requested
approval.decided

workflow.memory_recorded

run.waiting_approval
run.completed
run.failed
run.cancelled
```

Exact field names must be taken from:

```text
shared/events/events.json
```

Do not invent payload contracts.

---

# 23. EVENT-DRIVEN UI

The UI should react immediately to events.

Examples:

```text
plan.created
→ populate workflow graph

agent.spawned
→ add agent node/card

tool.started
→ active tool state

tool.completed
→ completion state

observation.captured
→ update desktop mirror

verification.passed
→ show verified state

recovery.started
→ show recovery animation

artifact.created
→ add artifact

artifact.verified
→ mark verified

approval.requested
→ open approval surface

run.completed
→ completion state

run.failed
→ failure state
```

---

# 24. RUN DETAIL ENDPOINTS

Use the documented endpoints:

```text
GET /api/v1/runs/{run_id}
GET /api/v1/runs/{run_id}/steps
GET /api/v1/runs/{run_id}/tools
GET /api/v1/runs/{run_id}/observations
GET /api/v1/runs/{run_id}/verifications
GET /api/v1/runs/{run_id}/artifacts
GET /api/v1/runs/{run_id}/context
GET /api/v1/runs/{run_id}/audit
```

These are the source of truth for detailed evidence.

---

# 25. INITIAL RUN HYDRATION

When entering an existing run screen:

```text
GET run
GET steps
GET tools
GET observations
GET verifications
GET artifacts
GET context
GET audit
```

Then connect to SSE if the run is still active.

Do not rely only on local frontend state.

This allows:
- app restart
- navigation away/back
- reload
- opening historical runs

without losing state.

---

# 26. LIVE + SNAPSHOT MODEL

Use:

```text
REST = authoritative snapshot
SSE  = live updates
```

When appropriate:

```text
initial load
→ REST snapshot

live execution
→ SSE mutations

terminal
→ REST refresh
```

After terminal events, fetch the final run detail and supporting resources again.

---

# 27. TASK MANAGEMENT

The left pane must display:

```text
recent runs
active run
tasks
side tasks
workflows
workspace
```

Use real backend run data for run-related information.

Do not fabricate execution entries.

Local-only UI metadata may exist if clearly frontend-specific.

---

# 28. ACTIVE RUN SCREEN

The main active screen follows the four-zone layout from:

```text
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
```

```text
┌───────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                              │
├──────────────────┬──────────────────────────────────┬────────────────┤
│ TASK / WORKSPACE │ LIVE DESKTOP MIRROR             │ AGENT / CHAT   │
│                  │                                  │                │
│ Tasks            │                                  │ Active agent   │
│ Runs             │                                  │ Chat           │
│ Workflows        │                                  │ Thinking       │
│ Side tasks       │                                  │ Tools          │
│                  │                                  │ Approval       │
│                  ├──────────────────────────────────┤                │
│                  │ WORKFLOW / GRAPH / TIMELINE      │                │
├──────────────────┴──────────────────────────────────┴────────────────┤
│ STATUS BAR / SYSTEM                                                  │
└───────────────────────────────────────────────────────────────────────┘
```

API wiring must support every visible dynamic element.

---

# 29. AGENTS API

Use:

```text
GET /api/v1/agents
```

Render the returned agent definitions dynamically.

Do not hardcode exactly eight or twelve agents into the UI architecture.

The backend is the source of truth.

Display:

```text
agent_id
name
description
capabilities
risk
allowed_tools
scoped_tools
```

using actual response fields.

---

# 30. LIVE AGENT STATE

Combine:

```text
GET /agents
+
agent SSE events
+
run steps
```

to render current agent status.

States may include:

```text
SPAWNED
READY
RUNNING
WAITING
COMPLETED
FAILED
CANCELLED
```

Do not invent activity.

---

# 31. TOOLS API

Use:

```text
GET /api/v1/tools
GET /api/v1/tools/{key}
```

Render a capabilities view.

Each tool may show:

```text
key
name
version
description
capabilities
risk
side effect
permissions
resource locks
schema
verification strategy
```

Read actual fields from OpenAPI.

---

# 32. TOOL ACTIVITY

Run-specific tools:

```text
GET /api/v1/runs/{run_id}/tools
```

Combine with SSE.

Show:

```text
tool
agent
step
status
duration
risk
verification
```

Avoid displaying secrets or unrestricted raw inputs.

Truncate large inputs.

---

# 33. OBSERVATIONS

Run observations:

```text
GET /api/v1/runs/{run_id}/observations
```

Use for:

- desktop mirror
- browser state
- application state
- screenshot evidence
- observation timeline

Render only information actually returned by the backend.

---

# 34. DESKTOP MIRROR INTEGRATION

The frontend does not control the desktop.

The backend does.

The frontend receives:

```text
observation.captured
```

and/or observation snapshots.

Render:
- latest screenshot if safely exposed
- application
- window title
- timestamp
- active step

When a new observation arrives:

```text
old image
→ soft transition
→ new image
```

No fake interaction.

---

# 35. SCREENSHOT HANDLING

If the backend exposes a safe screenshot resource/path/hash, build a frontend image-loading abstraction.

Do not assume renderer filesystem access.

Potential model:

```text
observation
→ backend-safe resource URL
→ image component
```

If only a hash/path is exposed and no frontend-safe retrieval route exists, display metadata rather than bypassing the backend.

Do not access arbitrary `C:\...` paths from the renderer.

---

# 36. VERIFICATION API

Use:

```text
GET /api/v1/runs/{run_id}/verifications
```

Display:

```text
PASS
FAIL
STALE
UNAVAILABLE
```

plus:
- failure_reason
- assertions
- evidence summary

---

# 37. VERIFICATION UI

Example:

```text
VERIFICATION

✓ Word application running
✓ Document content generated
✓ Word artifact exists
✓ Excel structure valid
✓ PowerPoint structure valid
✓ Attachments present
```

Color/status must derive from actual result.

---

# 38. WORKFLOW GRAPH

Use React Flow or the existing project graph library.

Source:

```text
plan.created
plan.validated
plan.wave_dispatched
step/agent/tool events
```

Render:

```text
task
→ plan
→ agents
→ steps
→ artifacts
→ approval
```

Do not invent graph nodes absent from the plan/event stream.

---

# 39. GRAPH STATE MAPPING

Example:

```text
plan.created
→ PENDING

tool.started
→ RUNNING

verification.passed
→ VERIFIED

recovery.started
→ RECOVERING

verification.failed
→ FAILED

approval.requested
→ WAITING_APPROVAL

run.completed
→ COMPLETED
```

The actual step identity must come from the event.

---

# 40. PARALLEL VISUALIZATION

When:

```text
plan.wave_dispatched
```

is emitted, visualize concurrent logical work.

Example:

```text
WORD       ● RUNNING
EXCEL      ● RUNNING
POWERPOINT ● RUNNING
```

Use backend event timing rather than assuming all branches physically execute at the same time.

---

# 41. ARTIFACT API

Use:

```text
GET /api/v1/runs/{run_id}/artifacts
```

Each artifact card should render fields such as:

```text
name
type
path/reference
sha256
verified
producer
```

based on actual schema.

---

# 42. ARTIFACT EVENT HANDLING

On:

```text
artifact.created
```

insert/update the artifact.

On:

```text
artifact.verified
```

mark it verified.

After terminal state:
fetch the full artifact collection again.

---

# 43. APPROVAL API

Use:

```text
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
```

Body:

```json
{
  "decision": "approved",
  "reason": "Looks good"
}
```

or:

```json
{
  "decision": "rejected",
  "reason": "Do not send"
}
```

The exact allowed values must follow the backend contract.

---

# 44. APPROVAL UI

When:

```text
approval.requested
```

arrives:

- pause the workflow presentation
- show approval panel
- identify action
- identify risk
- show relevant evidence
- show artifacts
- show recipient/subject where provided
- display current state

The user must understand:

```text
NOT SENT
WAITING FOR USER
```

The frontend must never imply an email was sent unless the backend reports a successful send event/status.

---

# 45. APPROVAL DECISION FLOW

Approved:

```text
click Approve
→ POST decision
→ wait for SSE
→ refresh run
```

Rejected:

```text
click Reject
→ POST decision
→ wait for SSE
→ refresh run
```

Do not locally mutate the run into `completed` or `failed` without backend confirmation.

---

# 46. TERMINATE RUN

Use:

```text
POST /api/v1/runs/{run_id}/terminate
```

Expose as:

```text
Stop run
```

Confirm the user's intent if appropriate.

After request:

```text
show terminating...
→ wait for run.cancelled / final status
```

Do not assume immediate cancellation.

---

# 47. CONTEXT / RAG PANEL

Use:

```text
GET /api/v1/runs/{run_id}/context
```

Display:

```text
RAG USED
Reason
Documents
Trust
Scores
Provenance
```

Example:

```text
Approval Rules
AUTHORITATIVE POLICY

Workspace Rules
AUTHORITATIVE POLICY

Email Draft
WORKFLOW
```

The UI must not reclassify trust.

Backend trust is authoritative.

---

# 48. KNOWLEDGE API

Use:

```text
GET /api/v1/knowledge
GET /api/v1/knowledge/{id}
POST /api/v1/knowledge
PUT /api/v1/knowledge/{id}
DELETE /api/v1/knowledge/{id}
GET /api/v1/knowledge/{id}/history
POST /api/v1/knowledge/{id}/reindex
POST /api/v1/knowledge/search
```

Build the Markdown editor around these routes.

---

# 49. KNOWLEDGE EDITOR

Support:

```text
document list
document editor
create
edit
delete
history
search
reindex
```

The editor saves the complete Markdown content.

Do not create an alternate frontend-only knowledge store.

---

# 50. KNOWLEDGE TRUST UI

Display backend trust values:

```text
authoritative_policy
reference
workflow
untrusted
```

The frontend may style them, but does not enforce policy itself.

---

# 51. LEARNING API

Use:

```text
GET /api/v1/learning/memory/{task_type}
GET /api/v1/learning/candidates
POST /api/v1/learning/candidates/{candidate_id}/review
```

Render:
- prior workflow memory
- candidate strategies
- lifecycle
- review state

---

# 52. LEARNING REVIEW

The existing backend requires human-gated progression.

The UI should represent:

```text
CANDIDATE
    ↓
APPROVE
    ↓
APPROVED
    ↓
ACTIVATE
    ↓
ACTIVE
```

Only call backend actions supported by the existing contract.

Do not bypass lifecycle steps in the UI.

---

# 53. AUDIT API

Use:

```text
GET /api/v1/runs/{run_id}/audit
```

Render:
- sequence
- event type
- timestamp
- hash
- step
- agent where available

Display:

```text
AUDIT CHAIN
✓ VERIFIED
```

only when the backend provides/indicates verification.

---

# 54. OPENAPI AS TYPE SOURCE

Prefer generating or maintaining TypeScript types from:

```text
shared/openapi/openapi.json
```

and shared entities/events.

Do not manually recreate dozens of interfaces if generation can prevent contract drift.

The generated types belong in the frontend build process or a generated frontend directory.

Do not alter the source OpenAPI schema from the frontend.

---

# 55. SHARED TYPES

Keep a clear distinction:

```text
API Types
SSE Event Types
UI View Models
```

Do not mutate backend response objects directly throughout the component tree.

Use small mapping functions:

```text
API response
→ domain frontend type
→ UI component
```

---

# 56. RUN STORE

Suggested state:

```text
activeRun
runStatus
steps
agents
tools
observations
verifications
artifacts
approval
context
audit
timeline
sseConnection
```

Use normalized entities where helpful.

---

# 57. EVENT DEDUPLICATION

The frontend should tolerate:
- reconnects
- duplicate events
- terminal refreshes

Where event IDs/sequence IDs exist, use them.

If only timestamps/sequence fields exist, follow the actual event contract.

Never duplicate the same tool/agent/artifact card because a reconnect occurred.

---

# 58. SSE RECONNECT

If the connection drops:

```text
CONNECTED
   ↓
DISCONNECTED
   ↓
RECONNECTING...
   ↓
CONNECTED
```

Then:

```text
fetch current run snapshot
```

to reconcile missed events.

Do not blindly replay guessed state.

---

# 59. TERMINAL EVENT HANDLING

For:

```text
run.completed
run.failed
run.cancelled
run.waiting_approval
```

refresh:

```text
run
steps
tools
verifications
artifacts
context
audit
```

For `waiting_approval`, do not close the entire conceptual run screen. Keep it interactive and approval-ready.

---

# 60. APPLICATION NAVIGATION

Suggested routes:

```text
/
 /home
 /runs
 /runs/:runId
 /workspace
 /knowledge
 /agents
 /tools
 /artifacts
 /learning
 /audit
 /settings
```

Navigation must not destroy active run state.

A live run should continue streaming even if the user temporarily opens another screen, unless the user intentionally stops the run.

---

# 61. SCREEN-TO-API MAP

## Home

Read:

```text
/health/ready
/health/model
```

Write:

```text
POST /runs
```

## Active Run

Read:

```text
/run
/steps
/tools
/observations
/verifications
/artifacts
/context
/audit
```

Live:

```text
SSE /events
```

Write:

```text
terminate
approval decision
```

## Capabilities

Read:

```text
/tools
/agents
```

## Knowledge

Read/write:

```text
/knowledge
```

## Learning

Read/write:

```text
/learning
```

---

# 62. HOME → ACTIVE RUN TRANSITION

User:

```text
types goal
↓
clicks Run
↓
loading
↓
POST /runs
↓
receive run_id
↓
active run workspace
↓
SSE
```

The active workspace should appear almost immediately, even while the backend is thinking.

---

# 63. ACTIVE RUN VISUAL STATE MACHINE

Frontend presentation:

```text
QUEUED
  ↓
STARTING
  ↓
UNDERSTANDING
  ↓
PLANNING
  ↓
EXECUTING
  ↓
VERIFYING
  ↓
RECOVERING (optional)
  ↓
WAITING FOR APPROVAL (optional)
  ↓
COMPLETED / FAILED / CANCELLED
```

These are presentation stages derived from real events.

Backend `run.status` remains authoritative.

---

# 64. AGENT CHAT INTEGRATION

The right-side chat should reflect actual run context.

The frontend should not create fake assistant messages.

Only show:
- backend-provided summaries
- current plan
- safe status
- tool activity
- verification
- recovery
- approval

If the backend has no conversational response endpoint, do not invent one.

The chat area may therefore initially function as a run-status/agent-summary surface rather than pretending a full chat backend exists.

---

# 65. THINKING PANEL

Do NOT render private chain-of-thought.

Show safe:

```text
plan summary
decision summary
current goal
current step
next action
verification
recovery explanation
```

Use fields supplied by the backend.

---

# 66. TOOL INPUT DISPLAY

When displaying tool inputs:

- truncate long values
- redact obvious secrets if the backend returns them
- do not dump raw sensitive payloads
- provide expandable technical details

Tool metadata from `/tools` remains the primary descriptive layer.

---

# 67. MODEL PANEL

Display backend model status:

```text
model
provider
profile
capabilities
context
latency
```

Do not let the frontend bypass the model gateway.

If model selection endpoints do not exist, make the UI informational rather than pretending frontend model switching is available.

---

# 68. ARTIFACT OPENING

Use safe OS integration only where the Electron architecture explicitly allows it.

Do not expose arbitrary shell commands to the renderer.

Prefer:
- controlled preload method
- main-process validation
- explicit path/reference handling

Never open arbitrary paths supplied directly from untrusted UI state.

---

# 69. LOCAL STORAGE

Frontend-only preferences may be stored locally:

```text
theme
pane widths
collapsed sections
recent navigation
non-sensitive UI preferences
```

Do not store:
- backend credentials that do not exist
- secret model prompts
- private raw model internals
- arbitrary workflow authority state

Run state comes from backend.

---

# 70. CACHE STRATEGY

Safe cache targets:

```text
tool catalog
agent catalog
health snapshots
knowledge list
static UI data
```

Active run state should always reconcile with the backend.

Never let stale cache override a fresh backend state.

---

# 71. FRONTEND LOADING STATES

Every API-backed screen needs:

```text
loading
empty
success
error
```

Active run needs:

```text
connecting
live
reconnecting
terminal
```

---

# 72. FRONTEND ERROR STATES

Example:

```text
BACKEND UNAVAILABLE

SyncNode backend is not reachable.

[Retry]
```

Run error:

```text
RUN FAILED

The backend reported:
Spreadsheet verification failed.

[View Evidence]
```

Approval error:

```text
APPROVAL COULD NOT BE SUBMITTED

The approval state may have changed.

[Refresh]
```

Do not invent root causes.

---

# 73. OFFLINE / LOCAL INDICATOR

Always show:

```text
● LOCAL
```

where useful.

The indicator must communicate local backend operation.

It must not claim "offline" if the frontend is technically using localhost networking; use terminology that reflects local execution.

---

# 74. API LOGGING IN DEVELOPMENT

Development-only diagnostics should be available:

```text
request
method
route
status
duration
event_type
run_id
```

Do not log secrets or giant payloads by default.

---

# 75. CONTRACT VALIDATION

During development, validate actual backend responses against the known schemas where practical.

When mismatch occurs:

```text
surface clear developer error
```

Do NOT silently coerce incompatible backend data into something plausible.

---

# 76. TESTING — API CLIENT

Write frontend tests for:

```text
health
create run
get run
get steps
get tools
get observations
get verifications
get artifacts
get context
get audit
approval
terminate
knowledge
learning
```

Mock HTTP at the frontend boundary.

These tests must not modify backend source.

---

# 77. TESTING — SSE

Test:

```text
stream.connected
run.created
agent.started
tool.started
tool.completed
verification.passed
artifact.created
approval.requested
run.waiting_approval
run.completed
run.failed
run.cancelled
```

Also test:

```text
unknown event
heartbeat
disconnect
reconnect
duplicate event
terminal event
```

---

# 78. TESTING — ACTIVE RUN

Test the complete UI transition:

```text
Home
→ create run
→ queued
→ live run
→ plan
→ agents
→ tools
→ observation
→ verification
→ artifact
→ approval
→ terminal
```

Use a deterministic mock SSE sequence.

---

# 79. TESTING — APPROVAL

Test:

```text
approval.requested
→ card visible

approve
→ POST decision

rejected
→ POST decision

stale/duplicate approval
→ show error + refresh
```

Never let the frontend locally assume an approval succeeded.

---

# 80. TESTING — ARTIFACTS

Test:

```text
artifact.created
→ artifact card

artifact.verified
→ verified state

three artifacts
→ three cards

hash/path/type
→ shown from backend
```

---

# 81. TESTING — KNOWLEDGE

Test:

```text
load list
open document
edit
save
create
delete
search
reindex
history
```

Use real API shapes.

---

# 82. TESTING — HEALTH

Test:

```text
all healthy
model unhealthy
database unavailable
RAG unavailable
computer unavailable
browser unavailable
backend unreachable
```

The Run button must follow the actual readiness response.

---

# 83. TESTING — ELECTRON

End-to-end Electron tests should prove:

```text
Electron launch
→ splash
→ backend health
→ workspace
→ create run
→ SSE
→ live graph
→ agent panel
→ desktop observations
→ artifacts
→ approval
```

The backend remains a separate already-tested system.

---

# 84. REAL GOLDEN RUN VISUALIZATION

The backend's established golden flow should render as:

```text
Windows Search
      ↓
Word
      ↓
new Word document
      ↓
Excel
      ↓
PowerPoint
      ↓
local email compose
      ↓
three artifacts
      ↓
verification
      ↓
approval
      ↓
WAITING_APPROVAL
```

The frontend is visualizing the real backend run; it is not implementing this workflow itself.

---

# 85. DESKTOP MIRROR STATES

### Waiting

```text
DESKTOP
Waiting for activity
```

### Active

```text
LIVE CONTROL
Microsoft Word
WordDocumentAgent
typing...
```

### Verification

```text
VERIFYING
Checking document...
```

### Approval

```text
WAITING FOR APPROVAL
```

All labels are UI presentation around backend truth.

---

# 86. GRAPH + DESKTOP SYNCHRONIZATION

When a tool event occurs:

```text
tool.started
→ graph node starts

observation.captured
→ desktop mirror updates

verification.passed
→ graph node completes

artifact.created
→ artifact panel updates
```

The two surfaces should feel synchronized.

---

# 87. AGENT + TOOL SYNCHRONIZATION

A selected agent should highlight:
- current step
- active tool
- graph node
- desktop context where applicable

Example:

```text
Word Agent
    ↓
create_docx
    ↓
Desktop: Microsoft Word
    ↓
Verification
```

This creates the "AI IDE" feeling.

---

# 88. NO FAKE ACTIVITY

This is critical.

Never animate:

```text
agent running
tool running
desktop action
thinking
verification
```

unless the frontend has corresponding backend state/event evidence.

Animations can interpolate between real states, but cannot create fake work.

---

# 89. EVENT TIMELINE

Build a timeline from actual SSE events.

Example:

```text
04:31:01
RUN STARTED

04:31:04
RAG RETRIEVED

04:31:08
PLAN CREATED

04:31:11
WORD AGENT STARTED

04:31:12
EXCEL AGENT STARTED

04:31:14
PPT AGENT STARTED

04:31:22
EMAIL DRAFT READY

04:31:23
APPROVAL REQUESTED
```

Do not invent timestamps.

---

# 90. WINDOW / PANE RESIZING

The frontend should persist:
- left pane width
- right pane width
- lower workflow height

These are frontend-local preferences.

They must not affect backend execution.

---

# 91. COMMAND PALETTE

Frontend-only navigation:

```text
New Run
Open Run
Agents
Tools
Knowledge
Artifacts
Learning
Audit
Settings
```

Backend actions only where a documented API exists.

---

# 92. SEARCH UX

The UI can have:
- run search
- knowledge search
- tool search
- agent search

Each should map to an actual API or local frontend filtering of already-loaded data.

Do not add an undocumented backend search endpoint.

---

# 93. FRONTEND SETTINGS

Possible settings:

```text
backend URL
theme
pane layout
animations
compact mode
developer diagnostics
```

Do not provide backend-incompatible controls such as:
- arbitrary model replacement
- tool permissions
- policy overrides
- execution bypass
unless the backend contract explicitly supports them.

The frontend is not the policy authority.

---

# 94. API CONTRACT FREEZE

Treat:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

as frozen integration contracts during frontend implementation.

If new additive fields appear:

- ignore what the UI does not need
- support backward compatibility
- do not break on unknown fields

If a breaking change is required:

STOP.

Do not alter the backend as part of this frontend task.

Document the required contract change separately.

---

# 95. FRONTEND DATA FLOW

The canonical data flow is:

```text
Backend REST
      ↓
Typed API Services
      ↓
Domain Store
      ↓
UI View Models
      ↓
React Components
```

and:

```text
Backend SSE
      ↓
Event Parser
      ↓
Event Router
      ↓
Domain Store
      ↓
React Components
```

---

# 96. RECONCILIATION

The frontend must handle the fact that:

```text
SSE event stream
```

and:

```text
REST snapshots
```

may arrive at slightly different times.

Use:
- event sequence where available
- timestamps where needed
- final REST refresh after terminal
- idempotent store updates

Never duplicate artifacts, steps, or agents due to reconciliation.

---

# 97. APP STARTUP LIFECYCLE

Implement:

```text
Electron launches
    ↓
main process ready
    ↓
renderer loads
    ↓
splash
    ↓
health checks
    ↓
health/model/system panels
    ↓
ready gate
    ↓
home
```

If backend unavailable:

```text
splash
→ health failed
→ recovery/retry screen
```

Do not silently enter a fake-ready state.

---

# 98. APPLICATION SHUTDOWN

On app shutdown:

- close SSE connections
- clean frontend subscriptions
- preserve backend run state
- do not terminate backend runs automatically unless explicitly requested
- do not mutate backend state just because Electron closes

The backend remains independent.

---

# 99. MULTI-RUN SUPPORT

The UI should support historical and active runs.

Use:

```text
Runs
├─ Active
├─ Waiting approval
├─ Completed
├─ Failed
└─ Cancelled
```

Each run can open its own detail view.

Only the selected active run consumes/render-focus the full workspace.

---

# 100. HISTORICAL RUN VIEW

For a completed run:

```text
Desktop mirror
→ last known evidence

Workflow
→ final graph state

Artifacts
→ final artifact list

Verification
→ final results

Audit
→ full timeline

Context
→ RAG provenance
```

Historical screens should be read-only unless a documented backend operation exists.

---

# 101. WAITING APPROVAL RUN VIEW

For an approval run:

```text
center
→ last useful desktop observation

bottom
→ workflow paused

right
→ approval card

left
→ current task

status bar
→ WAITING FOR APPROVAL
```

This should be one of the strongest visual states in the application.

---

# 102. FAILED RUN VIEW

Show:

```text
RUN FAILED

Failed step
Failure reason
Recovery attempts
Verification
Evidence
Artifacts produced before failure

[Open Evidence]
[Back to Runs]
```

Do not fabricate recovery success.

---

# 103. COMPLETED RUN VIEW

Show:

```text
RUN COMPLETE

Verified artifacts
Workflow summary
Verification
Audit
Memory
```

No false completion.

---

# 104. EVENT-TO-VIEW MODEL

Build a deterministic mapping table in code/documentation:

```text
event_type
→ store update
→ component update
→ animation
```

Example:

```text
agent.started
→ AgentStore.running
→ AgentCard active
→ pulse

verification.passed
→ VerificationStore.pass
→ GraphNode verified
→ check animation
```

Keep the mapping centralized.

---

# 105. MODEL / TOKEN TELEMETRY

Where backend events or APIs expose telemetry, show:

```text
prompt tokens
completion tokens
latency
model
profile
```

This should be a diagnostics/agent-detail feature, not the main visual focus.

---

# 106. RESOURCE STATUS

Where the backend exposes resource information, the frontend may show:

```text
GPU
Model queue
Desktop lock
Browser
Office
```

Do not claim CPU/GPU values that are not returned by the backend.

---

# 107. SECURITY UX

The frontend should clearly communicate:

```text
LOCAL EXECUTION
```

and:

```text
APPROVAL REQUIRED
```

when appropriate.

Never display a control suggesting:
- policy bypass
- approval bypass
- unrestricted shell
- hidden execution

---

# 108. FRONTEND FILE / PATH SAFETY

Never trust a path from a user-provided string and pass it to Electron shell APIs without validation.

Prefer backend artifact identity/reference.

Example:

```text
artifact_id
run_id
```

instead of raw arbitrary filesystem path.

---

# 109. UI DATA PRIVACY

Avoid retaining sensitive run content longer than necessary.

Do not permanently store:
- screenshots
- full tool payloads
- knowledge text
- email bodies

in browser local storage unless specifically required and already supported by product requirements.

Backend remains persistence authority.

---

# 110. COMPONENT LAYERING

Suggested:

```text
components/
  shell/
  runs/
  agents/
  workflow/
  desktop/
  timeline/
  approval/
  artifacts/
  knowledge/
  learning/
  audit/
  health/
  common/
```

Components consume frontend domain state rather than directly issuing random fetches.

---

# 111. DOMAIN LAYERING

Suggested:

```text
services/
  api/
  sse/

stores/

types/

mappers/

hooks/
```

Example:

```text
API response
→ mapper
→ domain type
→ store
→ component
```

---

# 112. REACT QUERY / DATA LIBRARY

A data-fetching library may be used if already present or if it improves frontend architecture, but it must remain a frontend concern.

Do not introduce backend coupling.

---

# 113. API RETRY POLICY

Retry only safe/idempotent requests automatically.

Examples:

```text
GET health
GET runs
GET tools
GET agents
GET artifacts
```

may retry.

Do not blindly retry:

```text
POST approval decision
POST create run
DELETE knowledge
```

unless request semantics and idempotency make it safe.

---

# 114. REQUEST CANCELLATION

Use AbortController where appropriate.

Example:

```text
leave screen
→ cancel obsolete read request
```

Do not cancel a backend workflow merely because a component unmounted.

Frontend request cancellation is not run cancellation.

---

# 115. LONG-RUN UX

The backend may run for minutes.

The frontend must:

- remain responsive
- stream updates
- show live elapsed time
- show current agent/step
- allow navigation
- keep approval state visible
- reconnect SSE if necessary

Do not use a single blocking spinner for the entire run.

---

# 116. LIVE ELAPSED TIME

Elapsed time can be computed locally for presentation using backend timestamps.

Example:

```text
Running 02:14
```

Do not alter backend timestamps.

---

# 117. SEARCH / FILTER RUNS

For historical runs, frontend filtering may use fetched data.

Example:

```text
all
running
waiting approval
completed
failed
```

Do not add unsupported backend filters.

---

# 118. AGENT DETAIL PAGE

Use:

```text
GET /api/v1/agents
```

Then show:

```text
name
capabilities
tools
risk
status during active run
```

A selected agent should also show run-specific activity when available.

---

# 119. TOOL DETAIL PAGE

Use:

```text
GET /api/v1/tools/{key}
```

Show:

```text
tool metadata
input schema
output schema
risk
permissions
verification strategy
resource locks
```

This is a capabilities/inspection surface, not a tool-execution console.

---

# 120. API INTEGRATION DIRECTORY

At minimum create:

```text
src/services/api/
src/services/sse/
src/types/api/
src/types/events/
src/stores/
src/mappers/
```

Do not mix API calls with visual components.

---

# 121. GENERATED TYPES

Where practical:

```text
OpenAPI
→ generated TypeScript types
```

and:

```text
events.json
→ event union types
```

Keep generated code clearly marked.

Do not edit generated code manually unless that is the established project pattern.

---

# 122. EVENT PAYLOAD COMPATIBILITY

For event payloads:

```text
required fields
→ strictly typed

optional fields
→ optional

future fields
→ ignored safely
```

This protects frontend compatibility.

---

# 123. API BASE URL CONFIGURATION

Use an environment/config value:

```text
SYNCNODE_API_BASE_URL
```

with a local default:

```text
http://127.0.0.1:8000
```

Do not hardcode the URL everywhere.

---

# 124. SSE BASE URL

Derive SSE URL from the same backend base:

```text
${BASE}/api/v1/runs/${runId}/events
```

Do not create a separate host configuration unless the project explicitly requires it.

---

# 125. HEALTH POLLING

On startup:

```text
health check
ready check
```

After entering the workspace, periodic health polling may update the status strip.

Keep polling lightweight.

Avoid high-frequency polling.

SSE handles active run updates.

---

# 126. FRONTEND INTERACTION WITH BACKEND OWNERSHIP

The backend owns:

```text
plan
agent spawning
tools
execution
recovery
verification
approval policy
artifact creation
knowledge trust
workflow memory
audit
```

The frontend owns:

```text
navigation
layout
visualization
interaction
presentation
local UI state
API transport
SSE transport
```

Never swap these responsibilities.

---

# 127. FINAL API INTEGRATION CHECKLIST

Before declaring frontend integration complete:

```text
[ ] all docs in docs/ read
[ ] FRONTEND_MASTER.md read
[ ] ELECTRON_ARCHITECTURE.md read
[ ] OpenAPI read
[ ] event contracts read
[ ] entity schemas read

[ ] health wired
[ ] readiness wired
[ ] model health wired
[ ] database health wired
[ ] RAG health wired
[ ] computer health wired
[ ] browser health wired

[ ] create run wired
[ ] run detail wired
[ ] steps wired
[ ] tools wired
[ ] observations wired
[ ] verifications wired
[ ] artifacts wired
[ ] context wired
[ ] audit wired
[ ] terminate wired
[ ] approval wired

[ ] agents wired
[ ] tools catalog wired

[ ] knowledge CRUD wired
[ ] knowledge history wired
[ ] knowledge reindex wired
[ ] knowledge search wired

[ ] learning memory wired
[ ] learning candidates wired
[ ] candidate review wired

[ ] SSE connected
[ ] SSE parsed
[ ] SSE routed
[ ] SSE reconnects
[ ] unknown SSE events tolerated

[ ] run store
[ ] agent store
[ ] tool store
[ ] timeline store
[ ] artifact store
[ ] approval store
[ ] verification store
[ ] context store
[ ] audit store

[ ] four-zone UI connected to real state
[ ] desktop mirror connected
[ ] workflow graph connected
[ ] agent panel connected
[ ] tool panel connected
[ ] approval panel connected
[ ] artifact panel connected
[ ] evidence panel connected

[ ] no fake execution state
[ ] no fake agent activity
[ ] no backend imports
[ ] no direct Ollama calls
[ ] no direct SQLite access
[ ] no direct Python execution
[ ] no direct Windows automation
[ ] no backend module changes
```

---

# 128. FINAL INTEGRATION TEST

Run the backend exactly as already documented.

Then launch Electron.

Execute a real task using the existing backend.

The UI must visibly demonstrate:

```text
STARTUP
  ↓
HEALTH
  ↓
HOME
  ↓
USER GOAL
  ↓
POST /runs
  ↓
LIVE SSE
  ↓
RAG
  ↓
INTENT
  ↓
PLAN
  ↓
AGENTS
  ↓
TOOLS
  ↓
DESKTOP OBSERVATION
  ↓
WORD
  ↓
EXCEL
  ↓
POWERPOINT
  ↓
EMAIL
  ↓
THREE ARTIFACTS
  ↓
VERIFICATION
  ↓
APPROVAL
  ↓
WAITING_APPROVAL
```

For the known final golden workflow, visualize the backend's actual:
- Windows Search
- Word
- Excel
- PowerPoint
- local email compose
- three attachments
- verification
- approval boundary

Do not implement those operations in Electron.

The backend is performing them.

Electron only visualizes and interacts with the backend.

---

# 129. NO BACKEND PATCHING DURING FRONTEND WORK

If a test reveals:

```text
endpoint mismatch
missing field
broken event
incorrect backend response
```

DO NOT edit backend immediately.

Instead produce:

```text
FRONTEND_INTEGRATION_ISSUES.md
```

with:

```text
issue
expected contract
actual behavior
frontend impact
possible backend issue
```

Then continue all frontend work that can be completed without modifying backend.

Only a separately authorized backend task may change backend code.

---

# 130. FINAL CODE QUALITY

Frontend code must be:

- strongly typed
- componentized
- testable
- accessible
- responsive
- animation-aware
- resilient to partial backend state
- tolerant of future additive API fields
- free from duplicated API transport logic

Avoid giant components.

Avoid giant global stores.

Avoid magic strings scattered throughout code.

Centralize:
- routes
- event names
- status mapping
- API errors
- configuration

---

# 131. FINAL PERFORMANCE

The frontend must remain responsive while:
- SSE is active
- screenshots update
- workflow graph animates
- many tool events arrive
- many timeline events arrive

Use:
- memoization
- normalized state
- batched event updates where safe
- lazy rendering
- virtualized timelines where necessary

Do not re-render the entire application for each SSE event.

---

# 132. FINAL VISUAL INTEGRATION RULE

The frontend should make the backend architecture visible.

The user should understand:

```text
WHAT IS THE USER ASKING?
          ↓
WHAT IS THE AI PLANNING?
          ↓
WHICH AGENTS ARE WORKING?
          ↓
WHAT TOOL IS EXECUTING?
          ↓
WHAT IS ON THE DESKTOP?
          ↓
WHAT WAS OBSERVED?
          ↓
DID VERIFICATION PASS?
          ↓
IS RECOVERY HAPPENING?
          ↓
DO WE NEED USER APPROVAL?
          ↓
WHAT ARTIFACTS WERE PRODUCED?
```

This is why the four-zone layout matters.

---

# 133. FINAL SOURCE-OF-TRUTH UX

When a frontend display disagrees with the backend:

```text
backend wins
```

When a cached value disagrees with fresh REST:

```text
fresh REST wins
```

When SSE and REST disagree temporarily:

```text
reconcile
→ refresh
→ backend wins
```

Never invent a third state to hide inconsistency.

---

# 134. IMPLEMENTATION ORDER

Build frontend integration in this order:

```text
1. Read all docs
2. Inspect existing frontend
3. Inspect OpenAPI/events/entities
4. Set up typed API client
5. Set up SSE client
6. Create stores
7. Wire health
8. Wire runs
9. Wire live events
10. Wire agents
11. Wire tools
12. Wire observations
13. Wire verification
14. Wire artifacts
15. Wire context/RAG
16. Wire approvals
17. Wire audit
18. Wire knowledge
19. Wire learning
20. Connect all four visual zones
21. Build startup sequence
22. Add real run UX
23. Add approval UX
24. Test reconnect/error/terminal paths
25. Run full frontend integration test
```

---

# 135. FINAL ABSOLUTE INSTRUCTION

Build and wire the Electron frontend **END TO END**.

Read ALL relevant documentation in the repository first.

Use the existing:

```text
REST API
SSE event stream
OpenAPI
event schemas
entity schemas
```

as the backend contract.

Wire **everything that already exists**:

```text
health
runs
tasks
agents
tools
workflow graph
desktop observations
screenshots
tool activity
verification
recovery
artifacts
knowledge
RAG provenance
workflow memory
learning candidates
approval
audit
model status
system status
SSE
REST
```

Create the complete AI-IDE experience described in:

```text
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
```

The frontend must feel like one coherent product:

```text
SYN C N O D E
      ↓
LOCAL AI WORKSPACE
      ↓
TASK
      ↓
AGENTS
      ↓
WORKFLOW
      ↓
DESKTOP
      ↓
TOOLS
      ↓
VERIFICATION
      ↓
ARTIFACTS
      ↓
APPROVAL
      ↓
RESULT
```

### MOST IMPORTANT:

**DO NOT TOUCH THE BACKEND.**

No backend file modifications.
No Python modifications.
No database changes.
No API changes.
No LangGraph changes.
No tool changes.
No execution changes.
No policy changes.
No Ollama changes.

Only:

```text
Electron
React
TypeScript
frontend components
frontend stores
frontend API client
frontend SSE client
frontend routing
frontend state
frontend animations
frontend styles
frontend tests
frontend integration
```

are in scope.

The finished Electron application must be a **thin, polished, real-time visual client for the existing SyncNode backend**, not a second implementation of SyncNode.

---

# 136. FINAL DEFINITION OF DONE

The frontend/API integration is complete when a fresh Electron launch can:

```text
1. show splash
2. check backend health
3. show actual local model/system state
4. enter workspace
5. accept a natural-language task
6. create a real backend run
7. connect SSE immediately
8. display the live plan
9. display real agents
10. display real tool activity
11. display real desktop observations
12. display the workflow graph
13. display real verification
14. display recovery when it occurs
15. display generated artifacts
16. display RAG provenance
17. display audit events
18. show approval
19. submit approval/rejection
20. reconcile final backend state
21. browse knowledge
22. browse tools
23. browse agents
24. review learning candidates
25. remain responsive during long-running work
26. survive SSE reconnects
27. tolerate unknown future events
28. never fabricate backend activity
29. never bypass the backend
30. never modify backend modules
```

Final architectural boundary:

```text
                    SYN C N O D E
                         │
              ┌──────────┴──────────┐
              │                     │
          ELECTRON                BACKEND
          FRONTEND                AUTHORITY
              │                     │
       REST + SSE ONLY       execution / policy /
              │               tools / agents /
              └──────────────→ verification /
                              recovery / audit
```

**The backend is finished and frozen.**
**The Electron frontend is now the only implementation target.**
**Wire it all together end to end.**
