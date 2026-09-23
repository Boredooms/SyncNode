# FRONTEND_SSE_STATE_MODEL.md

# SyncNode Electron Frontend
## SSE Event Architecture + State Model
### End-to-end real-time frontend state synchronization

> **Scope:** FRONTEND ONLY.
>
> This document defines how the Electron/React frontend consumes the existing SyncNode REST + SSE contracts and turns backend events into a coherent live UI.
>
> **ABSOLUTE RULE: DO NOT MODIFY THE BACKEND.**
>
> Do not edit Python, LangGraph, LangChain, ModelGateway, ExecutionEngine, RecoveryEngine, ToolRegistry, VerificationEngine, database logic, backend routes, backend schemas, or backend event generation.
>
> The frontend must consume the already-existing contracts exactly as documented.

---

# 1. CORE MODEL

SyncNode has two complementary frontend data sources:

```text
REST = authoritative snapshots
SSE  = authoritative live events
```

The frontend architecture is:

```text
                  SYNCNODE BACKEND
                         │
              ┌──────────┴──────────┐
              │                     │
            REST                   SSE
              │                     │
              ▼                     ▼
       Snapshot Hydrator       Event Stream
              │                     │
              └──────────┬──────────┘
                         ▼
                 Event Normalizer
                         │
                         ▼
                 State Reducer
                         │
                         ▼
                Domain Stores
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Run UI          Graph UI       Agent UI
          │              │              │
          ├──────────────┼──────────────┤
          ▼              ▼              ▼
      Desktop       Timeline        Approval
      Mirror        Tools           Artifacts
```

The backend remains the authority.

---

# 2. FRONTEND RESPONSIBILITIES

The frontend is responsible for:

```text
transport
parsing
normalization
state synchronization
visual state
animations
navigation
user interaction
```

The frontend is NOT responsible for:

```text
execution
planning
tool authorization
tool execution
verification policy
recovery policy
agent orchestration
workflow semantics
artifact creation
model inference
database persistence
```

---

# 3. BACKEND CONTRACT SOURCES

Before implementation, read:

```text
docs/
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
docs/FRONTEND_API_INTEGRATION.md

shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

These are the source of truth.

Do not invent event payload fields.

Do not infer missing backend behavior from frontend design mockups.

---

# 4. SSE ENDPOINT

The active run stream is:

```text
GET /api/v1/runs/{run_id}/events
```

Content type:

```text
text/event-stream
```

Expected message form:

```text
data: {JSON}


```

The first application-level event is:

```text
stream.connected
```

Heartbeat comments such as:

```text
: heartbeat
```

are transport-level keepalive messages, not application events.

---

# 5. ONE STREAM PER ACTIVE RUN

For each active run:

```text
one run
  ↓
one frontend SSE subscription
```

Do not let individual components open separate SSE connections.

Bad:

```text
AgentPanel → SSE
Timeline   → SSE
Graph      → SSE
Approval   → SSE
```

Correct:

```text
RunStreamManager
      ↓
Event Router
      ↓
Run State
 ├─ Timeline
 ├─ Agents
 ├─ Graph
 ├─ Tools
 ├─ Observations
 ├─ Verifications
 ├─ Artifacts
 ├─ Approval
 └─ Context
```

---

# 6. STREAM LIFECYCLE

```text
IDLE
 ↓
CONNECTING
 ↓
CONNECTED
 ↓
RECEIVING
 ↓
TERMINAL
 ↓
CLOSED
```

Failure:

```text
CONNECTED
 ↓
DISCONNECTED
 ↓
RECONNECTING
 ↓
CONNECTED
```

Fatal transport/configuration problem:

```text
CONNECTING
 ↓
ERROR
```

The UI should expose the connection state without treating every temporary disconnect as a failed run.

---

# 7. STREAM MANAGER

Create:

```text
src/services/sse/runStream.ts
```

Responsibilities:

- establish stream
- parse data frames
- ignore heartbeat comments
- validate event shape
- dispatch normalized events
- track connection state
- prevent duplicate subscriptions
- reconnect where appropriate
- stop on terminal event
- trigger final REST reconciliation

Suggested interface:

```ts
type StreamStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "closed"
  | "error";

interface RunStreamController {
  connect(runId: string): void;
  disconnect(runId: string): void;
  getStatus(runId: string): StreamStatus;
}
```

Adapt to the actual frontend architecture.

---

# 8. EVENT NORMALIZATION

Raw SSE payloads should not flow directly into components.

Pipeline:

```text
raw SSE
  ↓
JSON parse
  ↓
basic shape validation
  ↓
event normalization
  ↓
deduplication
  ↓
domain reducer
  ↓
state update
```

Create something equivalent to:

```text
eventParser.ts
eventNormalizer.ts
eventRouter.ts
```

The exact filenames may adapt to the existing frontend.

---

# 9. GENERIC EVENT ENVELOPE

Use the backend event contract.

Where the contract provides them, the frontend should handle:

```text
event_type
run_id
ts
event identity / sequence
payload
```

Do not require optional fields that are not guaranteed by the backend.

Keep type-specific payloads strongly typed.

---

# 10. EVENT UNION

Create a discriminated event union from the actual event contract.

Conceptually:

```ts
type SyncNodeEvent =
  | StreamConnectedEvent
  | RunCreatedEvent
  | RunStartedEvent
  | RagQueryEvent
  | RagRetrievalCompletedEvent
  | IntentCompletedEvent
  | PlanCreatedEvent
  | PlanValidatedEvent
  | PlanWaveDispatchedEvent
  | AgentSpawnedEvent
  | AgentStartedEvent
  | AgentWaitingEvent
  | AgentPlanSummaryEvent
  | AgentCompletedEvent
  | AgentFailedEvent
  | AgentCancelledEvent
  | ToolProposedEvent
  | ToolValidatedEvent
  | ToolAuthorizedEvent
  | ToolStartedEvent
  | ToolInvokedEvent
  | ToolCompletedEvent
  | ToolFailedEvent
  | ObservationCapturedEvent
  | VerificationPassedEvent
  | VerificationFailedEvent
  | RecoveryStartedEvent
  | RecoveryAttemptedEvent
  | RecoveryCompletedEvent
  | RecoveryExhaustedEvent
  | ArtifactCreatedEvent
  | ArtifactVerifiedEvent
  | ApprovalRequestedEvent
  | ApprovalDecidedEvent
  | WorkflowMemoryRecordedEvent
  | RunWaitingApprovalEvent
  | RunCompletedEvent
  | RunFailedEvent
  | RunCancelledEvent;
```

The actual event names and fields must come from:

```text
shared/events/events.json
```

If the backend defines additional events, support them.

---

# 11. UNKNOWN EVENTS

Future backend versions may add events.

Required behavior:

```text
unknown event
   ↓
log safely
   ↓
do not crash
   ↓
do not close SSE
   ↓
do not corrupt state
```

Optionally show unknown events only in development diagnostics.

Never treat unknown events as terminal.

---

# 12. EVENT DEDUPLICATION

Reconnections may cause overlap.

Use the strongest available backend identifier:

```text
event_id
sequence
or documented equivalent
```

If no unique event identity exists, use a conservative combination of:

```text
run_id
event_type
timestamp
step/tool/agent identity where available
```

Do not invent an artificial ordering that could overwrite genuine later updates.

---

# 13. ORDERING

The frontend should preserve backend event order where the stream guarantees it.

Store:

```text
timeline[]
```

in received/backend sequence order.

For state updates, do not blindly depend on arrival order when REST reconciliation provides a newer authoritative snapshot.

Use the backend's run snapshot to resolve conflicts.

---

# 14. REST + SSE RECONCILIATION

Canonical rule:

```text
REST = complete snapshot
SSE = incremental live update
```

Initial active-run flow:

```text
POST /runs
 ↓
run_id
 ↓
GET run snapshot
 ↓
open SSE
 ↓
apply live events
```

Where immediate SSE connection is possible, open it as quickly as possible after receiving `run_id`.

If events might race with initial REST fetch:

```text
connect SSE
+
hydrate REST
→ reconcile
```

or use a documented equivalent that prevents missing updates.

---

# 15. TERMINAL RECONCILIATION

When receiving:

```text
run.completed
run.failed
run.cancelled
run.waiting_approval
```

perform a final refresh:

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

This is critical.

The terminal event is a trigger to obtain the final authoritative snapshot.

---

# 16. FRONTEND DOMAIN STATE

Recommended domain state:

```text
AppState
├─ connection
├─ health
├─ workspace
├─ runs
│  ├─ activeRun
│  ├─ recentRuns
│  └─ history
├─ agents
├─ tools
├─ workflow
├─ timeline
├─ observations
├─ verifications
├─ artifacts
├─ approval
├─ context
├─ audit
├─ knowledge
├─ learning
└─ settings
```

Not all of these need separate stores if the project's state library favors another structure.

The important rule is clear separation of concerns.

---

# 17. ACTIVE RUN STATE

For the active run, maintain:

```text
run
status
goal
model_id
created_at
completed_at
error_message

steps
agents
tools
observations
verifications
artifacts
approval
context
timeline
connection
```

Where the backend exposes additional fields, preserve them through the typed domain layer.

---

# 18. RUN STATE MACHINE

Backend status:

```text
queued
running
waiting_approval
completed
failed
cancelled
```

Frontend presentation can derive richer stages:

```text
STARTING
UNDERSTANDING
PLANNING
EXECUTING
VERIFYING
RECOVERING
WAITING_FOR_APPROVAL
COMPLETED
FAILED
CANCELLED
```

The derived stage must be based on actual events.

Backend `status` remains authoritative.

---

# 19. STAGE DERIVATION

Example:

```text
run.created
→ STARTING

intent.completed
→ UNDERSTANDING complete

plan.created
→ PLANNING

tool.started
→ EXECUTING

verification.passed
→ VERIFYING complete

recovery.started
→ RECOVERING

approval.requested
→ WAITING_FOR_APPROVAL

run.completed
→ COMPLETED

run.failed
→ FAILED

run.cancelled
→ CANCELLED
```

Do not assume a particular event always exists if the backend contract does not guarantee it.

---

# 20. AGENT STATE MODEL

Frontend agent state should include the information provided by:

```text
GET /api/v1/agents
```

plus run-specific event state.

Conceptually:

```ts
interface AgentRuntimeView {
  agentId: string;
  definition?: AgentDefinition;
  status:
    | "idle"
    | "spawned"
    | "ready"
    | "running"
    | "waiting"
    | "completed"
    | "failed"
    | "cancelled";
  currentStepId?: string;
  currentTool?: string;
  summary?: string;
  startedAt?: string;
  completedAt?: string;
}
```

Do not invent backend state transitions.

---

# 21. AGENT EVENTS

Map:

```text
agent.spawned
→ create/update agent

agent.started
→ RUNNING

agent.waiting
→ WAITING

agent.plan_summary
→ safe summary text

agent.completed
→ COMPLETED

agent.failed
→ FAILED

agent.cancelled
→ CANCELLED
```

The Agent panel and Workflow graph should use the same underlying state.

---

# 22. STEP STATE

Represent backend step information:

```text
step_key
status
agent
verification
retries
```

where returned by the API.

Enhance with live event state where available.

Example presentation:

```text
PENDING
RUNNING
VERIFYING
RECOVERING
PASS
FAIL
WAITING
```

---

# 23. TOOL STATE

A tool execution should be represented by:

```text
tool_key
step_key
agent_id
status
attempt
started_at
completed_at
duration
risk
error
```

Use actual fields from API/events.

---

# 24. TOOL EVENT MAPPING

```text
tool.proposed
→ proposed

tool.validated
→ validated

tool.authorized
→ authorized

tool.started
→ running

tool.invoked
→ invoked

tool.completed
→ completed

tool.failed
→ failed
```

This should animate the tool row in the UI.

---

# 25. OBSERVATION STATE

Track:

```text
observation id
step
timestamp
type
application
window
screenshot reference/hash
```

where provided.

New:

```text
observation.captured
```

should update the latest observation for the related step/run.

---

# 26. DESKTOP MIRROR STATE

The desktop mirror consumes the latest valid observation.

Conceptually:

```ts
interface DesktopObservationView {
  timestamp: string;
  application?: string;
  windowTitle?: string;
  screenshot?: ScreenshotReference;
  stepKey?: string;
}
```

The center mirror should display the latest real observation.

Never fabricate a screenshot.

---

# 27. SCREENSHOT UPDATES

When a new screenshot arrives:

```text
current screenshot
   ↓
soft transition
   ↓
new screenshot
```

Do not reload the entire application shell.

Throttle or coalesce high-frequency observation updates if necessary while preserving the latest state.

---

# 28. VERIFICATION STATE

Maintain per-step verification:

```text
PASS
FAIL
STALE
UNAVAILABLE
```

where these are defined by the backend.

Each result may include:

```text
failure_reason
assertions
evidence
```

Render only the actual returned fields.

---

# 29. VERIFICATION EVENTS

```text
verification.passed
→ mark step verified

verification.failed
→ mark step failed/verification failed
→ surface failure reason
```

A failed verification must never be visually represented as success.

---

# 30. RECOVERY STATE

Maintain:

```text
active recovery
step
error class
tier
attempt
outcome
circuit state
```

Map:

```text
recovery.started
→ RECOVERING

recovery.attempted
→ increment attempt

recovery.completed
→ update outcome

recovery.exhausted
→ terminal recovery failure state
```

---

# 31. ARTIFACT STATE

Track:

```text
artifact_id
run_id
name
type
path/reference
sha256
verified
producer
created_at
```

where provided by the backend.

The UI should not derive artifact identity from filenames alone.

---

# 32. ARTIFACT EVENTS

```text
artifact.created
→ add artifact

artifact.verified
→ verified=true
```

When the final run snapshot is fetched:

```text
REST artifacts
→ reconcile local artifact state
```

This prevents stale local cards.

---

# 33. APPROVAL STATE

Approval is a first-class domain object.

Track:

```text
approval_id
run_id
step_key
action
risk
status
decision
reason
```

where available.

State:

```text
NONE
REQUESTED
WAITING
APPROVED
REJECTED
```

Use backend response/event semantics.

---

# 34. APPROVAL EVENT MAPPING

```text
approval.requested
→ create approval card

run.waiting_approval
→ lock workflow presentation
→ WAITING FOR USER

approval.decided
→ show decision
→ await run-state update
```

Do not locally decide that a run has resumed/failed.

Wait for backend confirmation.

---

# 35. APPROVAL STORE

Suggested:

```ts
interface ApprovalState {
  active?: ApprovalView;
  history: ApprovalView[];
  submitting: boolean;
  error?: ApiError;
}
```

---

# 36. CONTEXT / RAG STATE

Use:

```text
GET /api/v1/runs/{run_id}/context
```

and the corresponding events.

Track:

```text
rag.required
rag.reason
documents[]
provenance
```

The UI should render:

```text
knowledge used
trust tier
score
document
```

where provided.

---

# 37. RAG EVENTS

```text
rag.query
→ "Consulting knowledge..."

rag.retrieval.completed
→ populate provenance
```

Do not infer a retrieval occurred unless the backend reports it.

---

# 38. WORKFLOW GRAPH STATE

Build the graph from:

```text
plan.created
plan.validated
plan.wave_dispatched
agent events
tool/step events
verification events
artifact events
approval events
```

Store a normalized graph view model.

Example:

```text
nodes[]
edges[]
activeNode
selectedNode
wave
```

---

# 39. GRAPH NODE MODEL

Conceptually:

```ts
interface WorkflowNodeView {
  id: string;
  label: string;
  agentId?: string;
  stepKey?: string;
  status:
    | "pending"
    | "running"
    | "verifying"
    | "recovering"
    | "completed"
    | "failed"
    | "waiting";
  toolKey?: string;
}
```

Adapt to the actual plan schema.

---

# 40. PLAN EVENTS

```text
plan.created
→ build initial graph

plan.validated
→ mark plan valid

plan.wave_dispatched
→ visually activate dispatched nodes
```

Do not create a graph disconnected from the actual plan.

---

# 41. PARALLEL WAVE STATE

When:

```text
plan.wave_dispatched
```

arrives:

```text
waveId / sequence
steps[]
parallel
```

where available.

The UI can show:

```text
RUNNING 3 TASKS
```

and illuminate those nodes.

Do not claim physical concurrency beyond the backend event/telemetry.

---

# 42. TIMELINE STATE

Keep an append-oriented timeline:

```ts
interface TimelineItem {
  id: string;
  eventType: string;
  timestamp: string;
  runId: string;
  stepKey?: string;
  agentId?: string;
  toolKey?: string;
  severity?: "info" | "success" | "warning" | "error";
  summary?: string;
  payload?: unknown;
}
```

Payload should use typed event data.

---

# 43. TIMELINE RENDERING

Example:

```text
04:31:01  Run accepted
04:31:04  Consulting knowledge
04:31:07  Plan created
04:31:11  Word Agent started
04:31:12  Excel Agent started
04:31:13  PowerPoint Agent started
04:31:21  Artifacts verified
04:31:24  Email draft ready
04:31:25  Approval required
```

All timestamps originate from backend events where available.

---

# 44. TOOL TIMELINE

A focused tool timeline can group:

```text
proposed
→ authorized
→ started
→ invoked
→ observed
→ verified
```

into one expandable activity.

This is especially useful for:

```text
computer.windows_search
computer.launch_app
document.create_docx
excel.create
powerpoint.create
browser.navigate
browser.attach_file
```

---

# 45. RUN STORE UPDATE RULE

Every event should update only the minimum necessary domain state.

Example:

```text
tool.started
```

should not trigger:
- knowledge reload
- full agent catalog reload
- full audit reload

Use focused updates.

---

# 46. REDUCER ARCHITECTURE

Recommended conceptual architecture:

```text
event
 ↓
event reducer
 ├─ run reducer
 ├─ agent reducer
 ├─ step reducer
 ├─ tool reducer
 ├─ observation reducer
 ├─ verification reducer
 ├─ recovery reducer
 ├─ artifact reducer
 ├─ approval reducer
 ├─ graph reducer
 └─ timeline reducer
```

A single event may update more than one domain because the UI needs synchronized views.

---

# 47. EXAMPLE: TOOL STARTED

Input:

```text
tool.started
```

Updates:

```text
ToolStore
  current tool = running

StepStore
  current step = running

AgentStore
  current agent tool = running

TimelineStore
  append event

GraphStore
  node = running
```

Desktop mirror should update only if an actual observation arrives.

---

# 48. EXAMPLE: ARTIFACT VERIFIED

Input:

```text
artifact.verified
```

Updates:

```text
ArtifactStore
  verified = true

StepStore
  artifact-related step = verified

TimelineStore
  append

GraphStore
  node completed where contract indicates
```

Do not mark the whole run completed from one artifact event.

---

# 49. EXAMPLE: APPROVAL REQUESTED

Input:

```text
approval.requested
```

Updates:

```text
ApprovalStore
  active approval

RunStore
  presentation stage = WAITING_FOR_APPROVAL

TimelineStore
  append

Workflow
  pause/lock visual progression

UI
  open approval surface
```

The actual backend run status may arrive in the subsequent:

```text
run.waiting_approval
```

event or REST refresh.

---

# 50. EXAMPLE: RUN COMPLETED

Input:

```text
run.completed
```

Do:

```text
RunStore
  terminal event recorded

SSE
  mark terminal

REST
  fetch final snapshot

UI
  render final result
```

Then reconcile all detail resources.

---

# 51. EXAMPLE: RUN FAILED

Input:

```text
run.failed
```

Do:

```text
RunStore → failed

Timeline → append

SSE → terminal

REST → final refresh

UI → failure screen
```

Preserve evidence and artifacts already created.

---

# 52. EXAMPLE: RUN CANCELLED

Input:

```text
run.cancelled
```

Do:

```text
RunStore → cancelled

SSE → terminal

REST → final refresh

UI → cancelled state
```

Do not assume all in-flight tool events have been rendered before cancellation.

---

# 53. WAITING APPROVAL IS NOT COMPLETE

Never map:

```text
waiting_approval
```

to:

```text
completed
```

The UI must visually distinguish:

```text
WAITING FOR YOU
```

from:

```text
RUN COMPLETE
```

---

# 54. EVENT ANIMATION MODEL

Animations are derived from state transitions.

Example:

```text
PENDING → RUNNING
```

animation:

```text
fade in + pulse
```

```text
RUNNING → COMPLETED
```

animation:

```text
pulse stop + check
```

```text
RUNNING → RECOVERING
```

animation:

```text
amber transition + recovery indicator
```

```text
RUNNING → WAITING
```

animation:

```text
soft dim + approval panel
```

Never create animation without corresponding backend state.

---

# 55. ANIMATION RECONCILIATION

On reconnect:

do not replay every old animation at full intensity.

Instead:

```text
REST snapshot
→ render current truth
```

and only animate new events after reconnection.

---

# 56. STATE HYDRATION FOR EXISTING RUNS

When the user opens:

```text
/runs/:runId
```

do:

```text
load run
load steps
load tools
load observations
load verifications
load artifacts
load context
load audit
```

Then:

```text
if run is active
→ connect SSE
```

If terminal:

```text
no live SSE required
```

unless contract requires otherwise.

---

# 57. ACTIVE RUN NAVIGATION

If the user navigates away:

```text
run continues
SSE may remain managed by application-level run controller
```

Returning to the run screen:

```text
hydrate REST
reconnect/reuse stream safely
```

Do not restart the backend run.

---

# 58. MULTIPLE RUNS

The frontend may have multiple historical runs and possibly one active run.

Maintain:

```text
runsById
activeRunId
streamControllersByRunId
```

Do not create a global stream state that mixes unrelated runs.

---

# 59. RUN SWITCHING

When changing active run:

```text
unmount/stop presentation for previous run
connect/hydrate selected run
```

Do not accidentally send approval actions to the wrong run.

Approval calls must always use:

```text
run_id
approval_id
```

from the selected run.

---

# 60. EVENT CORRELATION

Where the backend provides:

```text
correlation_id
```

preserve it.

Use for:

```text
tool → observation → verification
```

visual linking.

Do not create fake correlations.

---

# 61. EVENT → EVIDENCE LINKING

Where possible link:

```text
tool event
→ step
→ observation
→ verification
→ artifact
```

This allows the evidence panel to show:

```text
what happened
what was observed
why it passed
what artifact resulted
```

---

# 62. EVENT → GRAPH LINKING

Use identifiers:

```text
step_key
agent_id
tool_key
```

to highlight related graph nodes.

Do not rely solely on display names.

---

# 63. EVENT → DESKTOP MIRROR LINKING

When:

```text
observation.captured
```

contains:

```text
step_key
```

associate the screenshot with that step.

When the user clicks the timeline event:

```text
select step
→ show its observation
```

---

# 64. EVENT → ARTIFACT LINKING

When:

```text
artifact.created
```

contains producer information:

```text
producer step
producer agent
```

link artifact card to:

```text
graph node
tool
timeline
verification
```

---

# 65. EVENT → APPROVAL LINKING

Approval should link to:

```text
step
tool/action
risk
artifacts
email/draft evidence
```

where the backend provides these references.

---

# 66. STATE PERSISTENCE

The frontend should NOT become the authoritative database.

Persist only safe UI preferences locally:

```text
theme
pane dimensions
collapsed sections
recent navigation
```

Active workflow state remains backend-owned.

---

# 67. NO LOCAL WORKFLOW AUTHORITY

Do not store:

```text
approved=true
runComplete=true
toolSucceeded=true
artifactVerified=true
```

as permanent frontend truth.

These are backend states.

The frontend may cache them temporarily for rendering but must reconcile them.

---

# 68. CONNECTION STATE VS RUN STATE

Keep separate:

```text
SSE connection
```

and:

```text
run execution
```

Example:

```text
SSE disconnected
run still running
```

The UI should show:

```text
RECONNECTING TO LIVE RUN
```

not:

```text
RUN FAILED
```

unless the backend says the run failed.

---

# 69. API ERROR VS RUN ERROR

Distinguish:

```text
transport/API error
```

from:

```text
backend run failure
```

Example:

```text
GET /runs failed
```

does not mean:

```text
run.failed
```

Likewise:

```text
run.failed
```

does not mean:

```text
frontend network failure
```

---

# 70. SSE RECONNECT POLICY

Reconnect for temporary connection loss.

Before reconnecting:

```text
check whether run is terminal
```

If active:

```text
reconnect
```

After reconnect:

```text
fetch current snapshot
```

then continue receiving events.

Use bounded backoff to avoid connection storms.

---

# 71. STREAM CLOSE POLICY

Close when:

```text
run.completed
run.failed
run.cancelled
```

For:

```text
run.waiting_approval
```

follow the backend stream contract. If the backend keeps the run stream open, stay subscribed; if it terminates the stream, keep approval state and use REST on decision/resume.

Do not assume stream behavior contrary to the actual backend implementation.

---

# 72. HEARTBEAT

Ignore:

```text
: heartbeat
```

except for optional connection health timing.

Do not append heartbeat messages to the user timeline.

---

# 73. EVENT VALIDATION

At the frontend boundary validate at minimum:

```text
event_type
run_id
```

and required fields according to the event schema.

Malformed events:

```text
log
ignore safely
keep stream alive
```

Do not crash the React tree.

---

# 74. TYPE GUARDS

Provide helpers such as:

```ts
isRunEvent(event)
isAgentEvent(event)
isToolEvent(event)
isArtifactEvent(event)
isApprovalEvent(event)
```

based on discriminated event types.

---

# 75. EVENT SELECTORS

Create reusable selectors:

```text
selectActiveRun
selectCurrentStage
selectRunningAgents
selectRunningTools
selectLatestObservation
selectFailedSteps
selectVerifiedArtifacts
selectPendingApproval
selectTimeline
selectWorkflowNodes
```

Components should consume selectors rather than rebuilding event logic.

---

# 76. STORE SELECTOR EXAMPLE

Conceptually:

```ts
const runningAgents = selectRunningAgents(state);
const activeApproval = selectPendingApproval(state);
const latestObservation = selectLatestObservation(state);
```

This keeps the UI declarative.

---

# 77. DERIVED STATE

Examples:

```text
isRunning
isWaitingApproval
isTerminal
hasFailures
hasRecovery
hasVerifiedArtifacts
hasPendingApproval
sseConnected
backendReady
```

Derived values should come from backend-backed state.

---

# 78. APPROVAL BUTTON ENABLEMENT

Enable Approve/Reject only when:

```text
approval exists
AND
approval is still actionable
AND
frontend is connected enough to submit
```

Final authority remains the backend.

If backend rejects the decision:

```text
show error
refresh approval/run
```

---

# 79. LIVE DESKTOP MIRROR SELECTOR

Use:

```text
selectLatestObservation(activeRunId)
```

not:

```text
document.querySelector(...)
```

No visual state should depend on arbitrary DOM scraping.

---

# 80. WORKFLOW ACTIVE NODE SELECTOR

Determine from:

```text
running step
running agent
latest tool
```

according to actual state.

If multiple agents are running:

```text
highlight multiple nodes
```

when backend indicates parallel activity.

---

# 81. GRAPH AUTO-CENTER

When a major state begins:

```text
active branch changes
```

the graph may gently center/zoom the relevant node.

Do not aggressively re-center on every event.

User-controlled pan/zoom should be respected.

---

# 82. TIMELINE AUTO-SCROLL

During live execution:

```text
auto-scroll only while user remains at the bottom
```

If user manually scrolls upward:

```text
do not force-scroll
```

Provide:

```text
↓ New events
```

indicator.

---

# 83. ARTIFACT ARRIVAL

When:

```text
artifact.created
```

arrives:

```text
artifact card enters
```

When:

```text
artifact.verified
```

arrives:

```text
verification badge appears
```

The artifact should remain linked to the run.

---

# 84. RAG VISUALIZATION

When:

```text
rag.retrieval.completed
```

arrives:

show:

```text
Knowledge used

Approval Rules
Authoritative policy

Workspace Rules
Authoritative policy
```

where returned.

No fabricated retrieval.

---

# 85. MEMORY VISUALIZATION

When:

```text
workflow.memory_recorded
```

arrives:

show subtle:

```text
Workflow remembered
```

with a link to learning/memory details if the backend supports it.

Do not imply model weight training.

---

# 86. AUDIT VISUALIZATION

Every significant event may appear in the audit screen.

The active timeline may use a curated presentation.

The audit screen should preserve the fuller backend event history.

---

# 87. FINAL SNAPSHOT REHYDRATION

After terminal event:

```text
fetch everything
```

and replace/merge transient state.

This ensures:

```text
event stream
```

does not leave incomplete:
- artifacts
- verification
- approval
- audit
- recovery state

---

# 88. CACHE INVALIDATION

When terminal:

invalidate/refresh:

```text
run
steps
tools
observations
verifications
artifacts
context
audit
```

Do not leave a stale active-run cache visible indefinitely.

---

# 89. BACKEND RESTART SCENARIO

If backend restarts while Electron is open:

```text
SSE disconnect
health degraded
UI shows reconnecting
```

When backend returns:

```text
health ready
hydrate active run/history
reconnect SSE for active run if appropriate
```

Do not create a duplicate run.

---

# 90. ELECTRON RESTART SCENARIO

On Electron restart:

```text
startup
→ health
→ load recent runs
→ identify non-terminal active/waiting runs
→ hydrate
→ reconnect active stream
```

Do not restart execution automatically.

---

# 91. NETWORK / LOOPBACK FAILURE

If:

```text
127.0.0.1:8000
```

is unreachable:

show:

```text
SYNCNODE BACKEND OFFLINE

Waiting for local backend...
[Retry]
```

This is a frontend connectivity state.

Do not tell the user that the workflow failed unless backend state says so.

---

# 92. EVENT LOGGING

Development logging:

```text
[SYNCNODE SSE]
run_id
event_type
timestamp
```

Do not log:
- secrets
- full sensitive email contents
- unrestricted payloads

Use safe summaries.

---

# 93. DEVELOPMENT EVENT INSPECTOR

Optional developer panel:

```text
Live SSE

event_type
run_id
step
agent
timestamp
payload
```

This is useful during frontend integration.

Keep collapsed or disabled in production.

---

# 94. STATE DEBUGGING

Optional development state panel:

```text
Connection
Run
Agents
Workflow
Tools
Approval
Artifacts
```

Do not expose it as a replacement for normal UX.

---

# 95. EVENT TO ANIMATION TABLE

Maintain a central mapping:

```text
run.created
→ run-start animation

agent.started
→ agent pulse

tool.started
→ tool spinner

observation.captured
→ desktop screenshot transition

verification.passed
→ check animation

verification.failed
→ failure pulse

recovery.started
→ amber recovery state

artifact.created
→ artifact arrival

approval.requested
→ approval panel entrance

run.completed
→ completion animation

run.failed
→ failure animation

run.cancelled
→ cancellation animation
```

---

# 96. STATE TO COLOR

Use restrained status accents:

```text
running    → blue/active
verified   → green
approval   → yellow
failed     → red
recovery   → amber
AI         → restrained purple
neutral    → gray
```

Keep the primary UI near-black/monochrome.

Do not over-color every event.

---

# 97. STATE TO ICON

Use consistent iconography:

```text
queued       clock
running      activity/spinner
verified     check
failed       x
recovery     refresh
approval     lock
artifact     file
agent        bot
tool         wrench/function
observation  eye
```

Icon semantics should remain consistent throughout the application.

---

# 98. ACTIVE RUN HEADER

Show:

```text
RUNNING
<goal>
```

or:

```text
WAITING FOR APPROVAL
<goal>
```

or:

```text
COMPLETED
<goal>
```

Add:
- elapsed time
- model
- connection status

where backend/frontend state provides them.

---

# 99. LEFT PANEL STATE

The left panel shows:

```text
current run
recent runs
tasks
workflows
workspace
```

When active run events arrive:

```text
active run
→ subtle live indicator
```

Do not animate every list item on every SSE event.

---

# 100. RIGHT PANEL STATE

The right panel changes based on:

```text
selected agent
selected tool
selected step
approval
chat/status view
```

Selection is frontend state.

The underlying data remains backend-derived.

---

# 101. CENTER UPPER STATE

Desktop mirror:

```text
latest observation
```

and:

```text
current desktop-related step
```

If no observation exists:

```text
Waiting for desktop activity
```

Do not fabricate screenshots.

---

# 102. CENTER LOWER STATE

Workflow:

```text
plan
agents
steps
waves
verification
approval
```

Timeline:

```text
SSE events
```

The user can switch between:

```text
Graph
Timeline
```

without changing backend execution.

---

# 103. GLOBAL STATUS BAR

Reflect:

```text
backend
model
database
RAG
desktop
browser
SSE
```

using actual health/connection data.

During a live run:

```text
● LIVE
```

During reconnect:

```text
◌ RECONNECTING
```

---

# 104. RUN TERMINAL PRESENTATION

## Completed

```text
RUN COMPLETE
Verified artifacts: 3
```

## Waiting approval

```text
WAITING FOR APPROVAL
Nothing has been sent.
```

## Failed

```text
RUN FAILED
<backend-provided summary>
```

## Cancelled

```text
RUN CANCELLED
```

---

# 105. FULL GOLDEN EVENT EXPERIENCE

For the final known workflow, the UI should be capable of representing:

```text
stream.connected
      ↓
run.created
      ↓
run.started
      ↓
rag.query
      ↓
rag.retrieval.completed
      ↓
intent.completed
      ↓
plan.created
      ↓
plan.validated
      ↓
plan.wave_dispatched
      ↓
agent.spawned
      ↓
agent.started
      ↓
tool.proposed
      ↓
tool.authorized
      ↓
tool.started
      ↓
tool.invoked
      ↓
observation.captured
      ↓
tool.completed
      ↓
verification.passed
      ↓
artifact.created
      ↓
artifact.verified
      ↓
...
      ↓
approval.requested
      ↓
run.waiting_approval
```

The actual event order should always follow the real backend stream.

---

# 106. THREE-ARTIFACT VISUAL STATE

When the backend reports:

```text
Word
Excel
PowerPoint
```

artifacts:

```text
Artifacts
├─ Word       ✓ verified
├─ Excel      ✓ verified
└─ PowerPoint ✓ verified
```

When all three are attached:

```text
Email Draft
Attachments
✓ Word
✓ Excel
✓ PowerPoint
```

Only display attachments reported by the backend.

---

# 107. APPROVAL FINAL STATE

The strongest final visual:

```text
┌──────────────────────────────────────────┐
│         WAITING FOR APPROVAL             │
│                                          │
│ Email draft prepared                     │
│                                          │
│ ✓ Word artifact                          │
│ ✓ Excel artifact                         │
│ ✓ PowerPoint artifact                    │
│                                          │
│ Nothing has been sent.                   │
│                                          │
│ [Reject]                     [Approve]   │
└──────────────────────────────────────────┘
```

Center desktop mirror remains visible behind the approval surface.

---

# 108. NO CHAIN-OF-THOUGHT

The frontend must never render private chain-of-thought.

Allowed:

```text
plan summary
decision summary
current task
next action
verification
recovery reason
tool activity
```

Not allowed:

```text
raw hidden reasoning
private chain of thought
internal token-by-token thought trace
```

---

# 109. CHAT STATE

If backend chat/status messages exist, map them into the right-side agent/chat panel.

If no chat endpoint exists:

do not fabricate a conversational backend.

Use:
- plan summaries
- agent summaries
- status events
- tool events
- verification
- recovery

as the truthful intelligence feed.

---

# 110. EVENT PAYLOAD SAFETY

Large payloads should not be blindly inserted into React state.

For large values:

```text
store only necessary fields
truncate UI representation
```

Preserve backend identifiers needed to fetch full evidence.

---

# 111. TIMELINE PERFORMANCE

Potentially thousands of events may arrive.

Use:
- memoized rows
- virtualization for long timelines
- normalized event storage
- bounded rendering
- pagination/history loading where appropriate

Do not render 10,000 DOM rows simultaneously if unnecessary.

---

# 112. GRAPH PERFORMANCE

React Flow should not rebuild the entire graph on every tool event.

Update only affected nodes/edges.

Use:
```text
node id
step key
agent id
```

for targeted updates.

---

# 113. SCREENSHOT PERFORMANCE

Avoid re-rendering the whole center panel for every metadata-only event.

Only update the image when a new observation/screenshot is actually available.

---

# 114. STORE UPDATE PERFORMANCE

Event reducer should be:

```text
O(1) / near-O(1)
```

for common updates where practical.

Use entity maps:

```text
agentsById
stepsById
toolsById
artifactsById
```

rather than repeated linear searches.

---

# 115. FRONTEND EVENT ARCHITECTURE DIRECTORY

Suggested:

```text
src/
├─ services/
│  └─ sse/
│     ├─ runStream.ts
│     ├─ eventParser.ts
│     ├─ eventNormalizer.ts
│     ├─ eventRouter.ts
│     └─ reconnect.ts
│
├─ stores/
│  ├─ runStore.ts
│  ├─ agentStore.ts
│  ├─ toolStore.ts
│  ├─ workflowStore.ts
│  ├─ timelineStore.ts
│  ├─ observationStore.ts
│  ├─ verificationStore.ts
│  ├─ artifactStore.ts
│  ├─ approvalStore.ts
│  ├─ contextStore.ts
│  └─ auditStore.ts
│
├─ selectors/
│
└─ types/
   └─ events/
```

Adapt to the chosen frontend architecture.

---

# 116. API + SSE CLIENT OWNERSHIP

API layer:

```text
fetch
```

SSE layer:

```text
EventSource / fetch stream
```

Stores:

```text
state
```

Components:

```text
presentation
```

Do not mix these responsibilities.

---

# 117. API ACTION FLOW

For user actions:

```text
React
 ↓
typed action/service
 ↓
HTTP API
 ↓
backend
 ↓
SSE / REST state
 ↓
store
 ↓
React UI
```

Example approval:

```text
Approve button
 ↓
decideApproval()
 ↓
POST approval decision
 ↓
backend
 ↓
SSE approval/run event
 ↓
store
 ↓
UI updates
```

Do not locally mark approval successful before backend confirmation.

---

# 118. TERMINAL STATE AUTHORITY

Backend status wins over UI-derived stage.

Example:

```text
derived stage says EXECUTING
but REST says failed
```

Result:

```text
FAILED
```

Example:

```text
derived stage says APPROVAL
but REST says completed
```

Result:

```text
COMPLETED
```

After reconciliation.

---

# 119. STALE EVENT HANDLING

A late/duplicate event after terminal state should not regress:

```text
completed
→ running
```

or:

```text
cancelled
→ queued
```

unless the backend contract explicitly defines such a transition.

Protect terminal states with backend status reconciliation.

---

# 120. APPROVAL STALE STATE

If the user keeps an approval panel open and the approval has already been decided elsewhere:

```text
POST decide
→ backend returns conflict/bad request
→ refresh approval/run
→ update UI
```

Do not show "approved" because the user clicked first.

---

# 121. RUN LIST SYNCHRONIZATION

When a run starts/completes/fails:

update:

```text
recent runs
active runs
status badges
```

without requiring full application reload.

Use SSE event + targeted REST refresh where appropriate.

---

# 122. ACTIVE RUN PRESENCE

The active run should be clearly identifiable:

```text
● LIVE
```

or:

```text
◷ WAITING
```

in the left navigation and top bar.

---

# 123. LIVE EVENT FILTERS

Allow the user to filter timeline by:

```text
all
agents
tools
verification
recovery
artifacts
approval
knowledge
```

Filtering is frontend-only.

It must not alter backend execution.

---

# 124. EVENT SEARCH

Timeline search can filter already-loaded events:

```text
Word
Excel
verification
approval
```

No backend API is required unless one already exists.

---

# 125. EVENT DETAIL VIEW

Clicking an event should open:

```text
Event
Event type
Time
Run
Agent
Step
Tool
Summary
Relevant payload
```

Use safe truncation.

---

# 126. STATE EXPORT / DEBUG

A developer-only command may export current frontend state for debugging.

Do not include secrets.

Do not confuse this export with the backend audit chain.

---

# 127. REST REFRESH STRATEGY

Do not poll every subsystem continuously while SSE is healthy.

Prefer:

```text
SSE for live run
REST on:
  initial load
  reconnect
  terminal
  explicit refresh
```

Health endpoints may have their own lightweight polling.

---

# 128. HEALTH VS RUN SSE

Health status:

```text
periodic REST
```

Run state:

```text
SSE
```

Do not use run SSE as a system health mechanism.

---

# 129. EVENT ROUTER CONTRACT

Conceptually:

```ts
function routeSyncNodeEvent(event: SyncNodeEvent) {
  switch (event.event_type) {
    case "run.created":
      // run reducer
      break;

    case "agent.started":
      // agent reducer
      break;

    case "tool.started":
      // tool + step + timeline
      break;

    case "verification.passed":
      // verification + graph + timeline
      break;

    case "approval.requested":
      // approval + run presentation + timeline
      break;

    default:
      // safely ignore/log
  }
}
```

Prefer a registry/map-based implementation if cleaner.

---

# 130. EVENT HANDLER TESTING

Every supported event should have a reducer test.

Example:

```text
input event
→ expected state mutation
```

At minimum test:

```text
stream.connected
run.created
run.started
plan.created
agent.started
tool.started
observation.captured
verification.passed
recovery.started
artifact.created
approval.requested
run.waiting_approval
run.completed
run.failed
run.cancelled
```

---

# 131. RECONNECT TESTING

Test:

```text
connect
receive events
disconnect
reconnect
REST reconcile
receive more events
terminal
```

Assertions:

```text
no duplicate timeline items
no duplicate artifacts
no duplicate agents
terminal state correct
```

---

# 132. UNKNOWN EVENT TEST

Send:

```json
{
  "event_type": "future.event",
  "run_id": "..."
}
```

Expected:

```text
no crash
stream stays alive
state unchanged except optional diagnostics
```

---

# 133. MALFORMED EVENT TEST

Send malformed payload.

Expected:

```text
safe error log
event ignored
stream remains usable
```

Do not crash React.

---

# 134. OUT-OF-ORDER TEST

Where possible, test stale/non-current events.

Expected:

```text
backend snapshot wins
terminal state protected
no regression
```

Use actual contract semantics rather than inventing artificial sequence rules.

---

# 135. APPROVAL TEST

Mock:

```text
approval.requested
run.waiting_approval
```

Render:

```text
approval card
```

Then:

```text
click Approve
```

Verify:

```text
POST /approvals/{id}/decide
```

Then simulate backend response/events.

UI updates only from confirmed backend state.

---

# 136. GOLDEN UI TEST

The final Electron integration test should consume a realistic event sequence and verify:

```text
splash
→ home
→ run
→ timeline
→ agents
→ graph
→ desktop
→ artifacts
→ approval
→ terminal
```

The test can mock the backend transport at the frontend boundary, while a separate real backend golden test already verifies backend execution.

---

# 137. REAL BACKEND + ELECTRON TEST

At least one integration test should run against the real local backend:

```text
backend running
+
Electron running
```

Then:

```text
create run
→ real SSE
→ real state updates
→ real approval
```

Do not modify the backend for the test.

---

# 138. FRONTEND-ONLY TEST DATA

Mocks may exist for:

```text
loading
failure
unknown events
reconnect
large timelines
```

These mocks must implement the same frontend event/schema shapes.

Do not invent a second incompatible backend protocol.

---

# 139. EVENT FIXTURE DIRECTORY

Suggested:

```text
tests/fixtures/events/
├─ startup.json
├─ golden-run.json
├─ approval.json
├─ failure.json
├─ recovery.json
└─ unknown.json
```

Use actual documented payload shapes.

---

# 140. FULL STATE TEST

Provide a fixture capable of producing:

```text
Word
Excel
PowerPoint
Email
Approval
```

and verify all four zones update coherently.

---

# 141. FRONTEND STATE DEBUGGING PRINCIPLE

When UI appears wrong:

trace:

```text
backend event
→ parser
→ normalizer
→ reducer
→ store
→ selector
→ component
```

Do not patch the component by inventing local state to hide a broken event mapping.

---

# 142. NO BACKEND MODIFICATION

This remains repeated intentionally because it is the primary constraint.

The frontend implementation must not:

```text
"fix" Python
"fix" FastAPI
"fix" LangGraph
"fix" SQLite
"fix" ExecutionEngine
"fix" RecoveryEngine
"fix" SSE generation
```

Instead:

```text
identify
document
adapt frontend only
```

unless a separately authorized backend change exists.

---

# 143. FRONTEND EVENT CONTRACT FREEZE

During frontend implementation:

```text
event names
existing meanings
required fields
entity identity
```

are treated as frozen.

Additive backend fields may appear.

The frontend must tolerate them.

Breaking changes require an explicit separate backend/API versioning task.

---

# 144. STATE MACHINE VISUALIZATION

The UI should make these transitions visually understandable:

```text
QUEUED
  ↓
RUNNING
  ↓
VERIFYING
  ↓
RECOVERING
  ↓
WAITING_APPROVAL
  ↓
COMPLETED
```

Alternative terminal branches:

```text
RUNNING → FAILED
RUNNING → CANCELLED
RECOVERING → RECOVERY_EXHAUSTED → FAILED
```

This is presentation, not backend execution.

---

# 145. MULTI-AGENT STATE

When multiple agents are active:

```text
agents:
  word: running
  excel: running
  powerpoint: running
  email: waiting
```

The UI should show this simultaneously.

Do not collapse all activity into one "AI is working" spinner.

---

# 146. AGENT GRAPH + TIMELINE CONSISTENCY

If:

```text
WordAgent = RUNNING
```

then:
- agent card active
- related graph node active
- relevant timeline item visible

When backend says:

```text
WordAgent = COMPLETED
```

all three settle.

This synchronization is the main reason for the centralized state model.

---

# 147. TOOL + AGENT CONSISTENCY

If:

```text
tool.started
agent = word
```

then:

```text
Word Agent
→ current tool = tool
```

Do not show a different agent as active because of component-local state.

---

# 148. ARTIFACT + STEP CONSISTENCY

If:

```text
artifact.created
producer_step=create_docx
```

then:

```text
create_docx
→ artifact available
```

If:

```text
artifact.verified
```

then:

```text
create_docx
→ verification-linked artifact verified
```

Use actual identifiers.

---

# 149. APPROVAL + EMAIL CONSISTENCY

If:

```text
approval.requested
```

for email action:

show:
- draft state
- recipient/subject if provided
- attachments if provided
- risk
- no-send status

Do not claim transmission occurred.

---

# 150. FINAL FRONTEND STATE FLOW

The canonical frontend architecture:

```text
                   USER
                    │
                    ▼
              React UI
                    │
             user action
                    │
                    ▼
              API Service
                    │
                    ▼
             SyncNode API
                    │
             ┌──────┴──────┐
             │             │
          REST            SSE
             │             │
             ▼             ▼
        Snapshot      Event Stream
             │             │
             └──────┬──────┘
                    ▼
               Normalizer
                    │
                    ▼
                Reducers
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        Run       Agents     Tools
          │         │         │
          ├─────────┼─────────┤
          ▼         ▼         ▼
       Workflow  Desktop   Timeline
          │       Mirror       │
          ├──────────┬─────────┤
          ▼          ▼         ▼
      Artifacts   Approval   Evidence
                    │
                    ▼
              REST Decision
                    │
                    ▼
                Backend
```

---

# 151. FINAL IMPLEMENTATION ORDER

Implement in this order:

```text
1. Read all docs
2. Read OpenAPI
3. Read event schema
4. Read entity schema
5. Build typed API client
6. Build SSE connection manager
7. Build parser
8. Build event union
9. Build event normalizer
10. Build reducers/stores
11. Build selectors
12. Connect run lifecycle
13. Connect agents
14. Connect tools
15. Connect workflow graph
16. Connect observations/desktop
17. Connect verification
18. Connect recovery
19. Connect artifacts
20. Connect RAG/context
21. Connect approval
22. Connect audit
23. Add reconnect/reconciliation
24. Add terminal refresh
25. Add tests
26. Connect final four-zone UI
27. Run real Electron + backend integration test
```

---

# 152. FINAL ACCEPTANCE CRITERIA

The SSE/state system is complete when:

```text
[ ] One centralized SSE stream manager exists
[ ] Typed event union exists
[ ] Events are normalized
[ ] Unknown events do not crash UI
[ ] Heartbeats are ignored
[ ] Reconnect works
[ ] REST/SSE reconciliation works
[ ] Terminal refresh works
[ ] Duplicate events do not duplicate state
[ ] Run state is authoritative
[ ] Agent state is synchronized
[ ] Tool state is synchronized
[ ] Workflow graph is synchronized
[ ] Desktop observations are synchronized
[ ] Verification is synchronized
[ ] Recovery is synchronized
[ ] Artifacts are synchronized
[ ] Approval is synchronized
[ ] RAG/context is synchronized
[ ] Audit is synchronized
[ ] Timeline is synchronized
[ ] Multiple active/historical runs are isolated
[ ] Approval uses backend confirmation
[ ] No fake activity exists
[ ] No frontend execution bypass exists
[ ] No backend files changed
[ ] Real local backend integration passes
```

---

# 153. FINAL GOLDEN EXPERIENCE

A user enters:

```text
Create a Word report, Excel analysis, PowerPoint summary,
then draft an email with all three attached. Do not send.
```

The frontend should receive and visualize:

```text
RUN CREATED
      ↓
WORKSPACE READY
      ↓
KNOWLEDGE CONSULTED
      ↓
PLAN CREATED
      ↓
AGENTS SPAWN
      ↓
MULTI-AGENT WORK
      ↓
WORD
EXCEL
POWERPOINT
      ↓
OBSERVATIONS
      ↓
VERIFICATION
      ↓
ARTIFACTS
      ↓
EMAIL DRAFT
      ↓
THREE ATTACHMENTS
      ↓
APPROVAL REQUESTED
      ↓
WAITING FOR APPROVAL
```

And the four-zone UI reflects the same state simultaneously:

```text
LEFT
Task + agents + run

CENTER TOP
Live desktop / observations

CENTER BOTTOM
Workflow graph + timeline

RIGHT
Agent + chat/status + tools + approval
```

---

# 154. FINAL RULE

The frontend must never become a second SyncNode backend.

It is:

```text
visual client
+
real-time state client
+
user interaction layer
```

The backend remains:

```text
execution authority
+
policy authority
+
agent authority
+
tool authority
+
verification authority
+
persistence authority
```

Therefore:

> **Do not touch the backend.**
>
> **Wire the entire existing backend to Electron through REST + SSE.**
>
> **Make every visible state reflect real backend state.**
>
> **Make the interface feel alive through event-driven animation, not fabricated activity.**
>
> **Keep the four-zone AI-IDE layout from FRONTEND_MASTER.md and ELECTRON_ARCHITECTURE.md.**

---

# 155. FINAL IMPLEMENTING-EDITOR INSTRUCTION

Read all existing project documentation first.

Then implement the complete frontend SSE/state architecture described here.

You must:

```text
READ EVERYTHING
→ UNDERSTAND EVERYTHING
→ BUILD TYPED CLIENT
→ BUILD SSE
→ BUILD STATE MODEL
→ CONNECT EVERY REAL BACKEND EVENT
→ CONNECT EVERY REAL API
→ CONNECT EVERY UI SURFACE
→ TEST EVERYTHING
```

The frontend must be fully wired to:

```text
Health
Runs
Steps
Agents
Tools
Observations
Desktop mirror
Verifications
Recovery
Artifacts
RAG/context
Knowledge
Learning
Approval
Audit
SSE
```

Do not stop at the API client.

Do not stop at the SSE connection.

Do not stop at stores.

The state must actually drive the complete Electron UI.

### ABSOLUTE FINAL CONSTRAINT

**DO NOT TOUCH ANY BACKEND MODULE.**

Only frontend/Electron code is in scope.

The final architecture is:

```text
                    SYNCNODE
                       │
              ┌────────┴────────┐
              │                 │
          ELECTRON           BACKEND
           FRONTEND          AUTHORITY
              │                 │
              │ REST + SSE      │
              └────────────────→│
                                │
                     execution / agents /
                     tools / verification /
                     recovery / audit /
                     persistence
```

Build the frontend around the backend exactly as it exists.
