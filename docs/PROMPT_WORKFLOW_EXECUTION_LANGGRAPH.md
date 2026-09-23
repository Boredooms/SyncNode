# PROMPT: Generate `WORKFLOW_EXECUTION_LANGGRAPH.md` Technical Specification

You are a **Principal AI Systems Engineer and Distributed Orchestration Architect** specializing in:

- stateful graph computation
- LangGraph internals
- durable workflow orchestration
- human-in-the-loop execution
- checkpoint persistence
- crash recovery
- conditional graph routing
- multi-agent execution
- event-driven runtime telemetry
- local-first / air-gapped AI systems

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, production-grade, implementation-ready technical specification** titled:

> `WORKFLOW_EXECUTION_LANGGRAPH.md`

This document governs the **SyncNode Workflow Execution & LangGraph Orchestration Engine**: the central runtime state machine responsible for executing complete user runs, maintaining durable workflow state, coordinating Context Engine / Intent Engine / Planner / Agent Runtime / Tool Registry / Verification, suspending safely for human approval, streaming ordered execution telemetry, handling conditional branches, and recovering from process crashes without re-running completed side effects.

This is the **execution spine of SyncNode**.

It is not a generic LangGraph tutorial.

The specification must integrate with:

- FastAPI API layer
- Context Engine
- Intent Engine
- Planner / Task DAG Engine
- Agent Registry / Spawner
- Model Gateway
- Token Management
- Tool Registry
- Computer Runtime
- Document/File Automation
- Local Knowledge RAG
- Verification / Recovery
- Policy / Approval
- PostgreSQL / SQLite
- SSE event streaming
- `runs`
- `run_steps`
- `approvals`
- `audit_events`

The workflow engine must preserve the core principle:

> **Models propose; deterministic state machines, policy checks, durable checkpoints, and verified execution state determine what actually happens.**

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architecture source of truth.

Before generating the final specification:

1. Read the complete `idea.md`.
2. Extract:
   - run lifecycle
   - step lifecycle
   - LangGraph responsibilities
   - persistence requirements
   - checkpoint semantics
   - approval requirements
   - event-streaming requirements
   - execution/recovery boundaries
   - database schema
   - concurrency assumptions
   - phase-1 constraints
3. Preserve SyncNode terminology and architecture.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud workflow services.
6. Do not assume in-memory-only execution state.
7. Do not make LangGraph responsible for authorization that belongs to policy/tool/runtime boundaries.
8. Where implementation details are unspecified, make a concrete engineering choice and explicitly label it:
   > **Implementation Decision**
9. Clearly distinguish:
   - durable database state
   - in-memory graph state
   - model-generated proposals
   - deterministic transitions
   - physical side effects
   - observations
   - verification receipts
   - approval decisions
   - SSE events
   - recovery state

The final specification must be directly implementable by another engineer.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & EXECUTION PHILOSOPHY

Position LangGraph as the execution spine:

```text
                         FastAPI
                            │
                            ▼
                         Run API
                            │
                            ▼
                    Workflow Execution Engine
                            │
               ┌────────────┼─────────────┐
               ▼            ▼             ▼
          Context        Intent         Planner
           Engine         Engine          │
               │            │             │
               └────────────┴──────┬──────┘
                                    ▼
                              Task Graph / DAG
                                    │
                                    ▼
                             LangGraph Runtime
                                    │
            ┌───────────────────────┼────────────────────────┐
            ▼                       ▼                        ▼
       Agent Runtime           Tool Registry            Verifier
            │                       │                        │
            ▼                       ▼                        ▼
       Model Gateway         Computer/Document/        Observations
                              Browser Runtime
                                    │
                                    ▼
                              Durable Checkpoint
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                     PostgreSQL              SSE
```

The Workflow Execution Engine SHALL own:

- run lifecycle
- graph compilation/loading
- graph execution
- conditional routing
- step state progression
- durable checkpoint coordination
- approval suspension/resumption
- retry/recovery transitions
- cancellation
- crash rehydration
- event ordering
- execution telemetry
- finalization

It SHALL NOT own:

- natural-language intent extraction
- tool implementation
- model inference
- UI automation mechanics
- document parsing
- direct policy authoring
- direct approval decisions

---

# 1.1 Canonical run lifecycle

Enforce:

```text
QUEUED
   ↓
PLANNING
   ↓
RUNNING
   ├── WAITING_APPROVAL
   ├── RECOVERING
   ├── COMPLETED
   ├── FAILED
   └── CANCELLED
```

Define:

- legal transitions
- illegal transitions
- state-entry side effects
- persistence rules
- event emission rules
- recovery semantics

No terminal run may transition back to an active state without creating an explicit new run/version according to `idea.md`.

---

# 1.2 Required end-to-end execution diagram

Include detailed Mermaid and ASCII diagrams covering:

```text
run_init
   ↓
context_collector
   ↓
intent_classifier
   ↓
task_planner
   ↓
step_evaluator
   ↓
[approval required?]
      /        \
    yes         no
     ↓           ↓
approval_gate   agent_dispatch
     ↓           ↓
resume          tool_executor
                   ↓
             observation_capture
                   ↓
                 verifier
                /       \
          success        failure
             ↓             ↓
      step_evaluator    recovery
             ↓             ↓
          finalizer ← re-plan/retry
```

Include durable checkpoint boundaries at every externally significant state mutation.

---

# 2. GLOBAL GRAPH STATE ARCHITECTURE — `BrainState`

Define the authoritative workflow state.

Use Pydantic v2 and/or a carefully controlled `TypedDict` boundary where required by LangGraph.

The specification must include:

### Run metadata

```text
run_id
organization_id
user_id
parent_run_id
status
sequence_no
trace_id
created_at
updated_at
```

### Cognitive/planning state

```text
task_text
context_snapshot
intent_spec
task_graph
active_step_key
scratchpad
```

### Execution state

```text
active_agent_key
active_tool_call
observation_record
verification_result
error_stack
execution_history
```

### Checkpoint/control state

```text
attempt_counts
replan_count
active_locks
pending_approval_id
current_graph_version
checkpoint_version
last_event_sequence
cancellation_requested
```

Do not store live non-serializable objects such as:

- COM handles
- file descriptors
- browser page objects
- active asyncio tasks

Store stable references instead.

---

# 2.1 Pydantic state model

Provide a complete model such as:

```python
class BrainStateModel(BaseModel):
    run_id: UUID
    organization_id: UUID
    user_id: UUID
    parent_run_id: UUID | None
    status: RunStatus
    sequence_no: int
    trace_id: str

    task_text: str
    context_snapshot: ContextSnapshot | None
    intent_spec: StructuredIntent | None
    task_graph: TaskDAG | None

    active_step_key: str | None
    active_agent_key: str | None
    active_tool_call: ToolCallRecord | None

    observation_record: ComputerObservationRecord | None
    verification_result: VerificationResult | None
    error_stack: list[WorkflowError]

    attempt_counts: dict[str, int]
    replan_count: int
    active_locks: list[ResourceLock]
    pending_approval_id: UUID | None

    execution_history: list[ExecutionMilestone]
    current_graph_version: str
    checkpoint_version: int
    last_event_sequence: int

    cancellation_requested: bool
```

Add strict bounds and cross-field validation.

---

# 2.2 Pure reducers

Define deterministic reducer functions.

Examples:

```python
def reduce_step_started(
    state: BrainStateModel,
    step_key: str,
) -> BrainStateModel:
    ...
```

```python
def reduce_step_succeeded(
    state: BrainStateModel,
    result: StepResult,
) -> BrainStateModel:
    ...
```

Reducers must:

- validate invariants
- avoid hidden I/O
- avoid model calls
- avoid mutation of unrelated state
- return deterministic new state

---

# 3. NODE TOPOLOGY & NODE HANDLER SPECIFICATIONS

Define every major graph node.

---

## 3.1 `ContextCollectorNode`

Responsibilities:

- invoke Context Engine
- bind current trusted observations
- collect local knowledge/context
- produce a bounded `ContextSnapshot`
- record snapshot hash

Inputs:

```text
task_text
workspace
current observations
run metadata
```

Outputs:

```text
context_snapshot
context_snapshot_hash
```

---

## 3.2 `IntentClassifierNode`

Invoke Intent Engine.

Outputs:

```text
StructuredIntent
grounded entities
risk classification
clarification requirement
```

If clarification is required:

```text
run → WAITING_CLARIFICATION
```

or the exact architecture-approved state.

Do not invent a new state without an explicit implementation decision.

---

## 3.3 `TaskPlannerNode`

Invoke Planner.

Outputs:

```text
TaskDAG
graph_version
plan validation result
```

No unvalidated graph may enter scheduling state.

---

## 3.4 `StepEvaluatorNode`

Responsibilities:

- evaluate DAG readiness
- resolve dependencies
- inspect step risk
- determine whether approval is required
- select next ready step(s)
- coordinate resource admission signals

It must not execute the step.

---

## 3.5 `ApprovalGateNode`

Responsibilities:

```text
create approval
→ checkpoint
→ status = WAITING_APPROVAL
→ emit ordered event
→ interrupt graph
```

Approval decisions must be external runtime inputs.

---

## 3.6 `AgentDispatchNode`

Responsibilities:

- invoke Agent Spawner
- obtain ephemeral agent instance
- bind model profile
- bind Context Engine snapshot
- obtain scoped tools
- bind token lease

Do not expose unrestricted tool catalogs.

---

## 3.7 `ToolExecutorNode`

Responsibilities:

- invoke Tool Registry
- process structured result
- preserve idempotency
- capture tool-call references
- do not execute tools directly

---

## 3.8 `ObservationNode`

Capture:

- UI state
- application state
- filesystem deltas
- document artifacts
- browser state
- tool observations

Observation remains canonical system evidence.

---

## 3.9 `VerificationNode`

Evaluate deterministic postconditions.

Output:

```text
VerificationResult
```

Possible outcomes:

```text
PASSED
FAILED
INCONCLUSIVE
```

Do not silently treat `INCONCLUSIVE` as success.

---

## 3.10 `RecoveryNode`

Implement bounded recovery:

```text
retry
→ fallback tool
→ refreshed observation
→ re-plan
→ terminal failure
```

Respect:

- per-step retry count
- run token budget
- re-plan ceiling
- policy
- approval requirements

---

## 3.11 `FinalizerNode`

Responsibilities:

- verify terminal graph state
- verify artifact references
- ensure no active lock remains
- ensure no unresolved approval
- finalize run status
- persist final checkpoint
- emit terminal SSE/audit events

---

# 4. CONDITIONAL EDGES, ROUTING & TRANSITION PREDICATES

Provide complete deterministic route functions.

---

## 4.1 `route_after_step_evaluator`

Rules:

```text
approval required → approval_gate
step ready → agent_dispatch
nothing ready but unfinished → recovery / wait according to graph state
all terminal-success → finalizer
graph invalid → recovery/failure
```

---

## 4.2 `route_after_verification`

Rules:

```text
PASSED + unfinished steps → step_evaluator
PASSED + all steps complete → finalizer
FAILED + retry available → recovery
FAILED + no retry but replan allowed → recovery
FAILED + terminal → finalizer
INCONCLUSIVE → recovery
```

---

## 4.3 `route_after_recovery`

Rules:

```text
retry approved → step_evaluator / target step
re-plan required → task_planner
terminal failure → finalizer
```

---

## 4.4 `route_after_approval`

Rules:

```text
approved → agent_dispatch
rejected → recovery or finalizer according to policy
expired → approval recovery
invalidated → new approval request
```

Approval route decisions must be deterministic and persisted.

---

# 5. HUMAN-IN-THE-LOOP & APPROVAL SUSPENSION

Define durable HITL semantics.

---

## 5.1 Interrupt protocol

Use LangGraph's supported interruption/pause mechanisms.

Required flow:

```text
Approval required
→ construct approval payload
→ persist approval row
→ persist checkpoint
→ set WAITING_APPROVAL
→ emit SSE
→ interrupt execution
```

Do not keep approval state only in memory.

---

# 5.2 Approval payload

Define:

```python
class ApprovalCheckpointPayload(BaseModel):
    approval_id: UUID
    run_id: UUID
    run_step_id: UUID
    action_summary: str
    risk_class: RiskClass
    tool_key: str
    tool_version: str
    proposed_arguments_hash: str
    artifact_references: list[UUID]
    created_at: datetime
    expires_at: datetime | None
```

Never store raw credentials or secrets.

---

# 5.3 Approval verification

When a decision arrives:

```text
validate run
→ validate approval ID
→ validate decider role
→ validate approval state
→ validate argument hash
→ validate policy version
→ persist decision atomically
→ load checkpoint
→ resume graph
```

If the arguments changed:

```text
APPROVAL_INVALIDATED
```

and require new approval.

---

# 5.4 Resume endpoint integration

Define exact endpoint behavior for:

```text
POST /api/v1/runs/{id}/approvals/{approval_id}
```

The handler must not duplicate graph execution logic.

Use:

```text
API
→ transactional approval update
→ enqueue/resume execution
→ execution engine loads checkpoint
```

Avoid running long graph execution inside the request thread.

---

# 6. DURABLE CHECKPOINTING, STATE PERSISTENCE & CRASH RECOVERY

This is a critical section.

---

# 6.1 PostgreSQL checkpoint boundary

Define durable checkpoint records containing at minimum:

```text
run_id
graph/thread ID
checkpoint version
state hash
serialized state
created_at
sequence_no
```

Align with `runs` and `run_steps` from `idea.md`.

Where a dedicated checkpoint table is not defined, explicitly introduce:

> **Implementation Decision — Workflow Checkpoint Persistence**

---

# 6.2 State serialization

Only serialize JSON-safe objects.

For non-serializable runtime handles store:

```text
reference ID
```

Examples:

```text
HWND → integer/reference metadata
browser page → browser session/page ID
COM object → no direct serialization; reacquire on resume
file handle → reopen file by validated path
```

Never serialize credentials or live secrets.

---

# 6.3 Checkpoint atomicity

Use transactional semantics.

For a critical transition:

```text
BEGIN
→ validate expected sequence
→ update runs
→ update run_steps
→ write checkpoint
→ append event/outbox record
→ COMMIT
```

If the transaction fails:

```text
no partially committed workflow state
```

---

# 6.4 Sequence numbers

Use monotonic `sequence_no` / checkpoint version.

Every persisted state mutation must verify expected version.

On conflict:

```text
CONCURRENT_STATE_CONFLICT
```

Do not overwrite newer state.

---

# 6.5 Crash recovery startup

At startup:

```text
scan active runs
→ planning/running/recovering/waiting approval
→ load latest durable checkpoint
→ verify state hash
→ inspect active tool/agent execution records
→ classify stranded operations
→ re-observe external state
→ reconstruct graph
→ resume safely
```

Do not simply replay the last graph node.

---

# 6.6 Side-effect recovery

The hardest boundary is:

```text
physical side effect
+
database checkpoint
```

Define reconciliation for cases such as:

```text
email may have sent
but backend crashed before tool result persisted
```

or:

```text
Word save may have happened
but process crashed before success checkpoint
```

Use idempotency keys and post-restart observations to determine whether a side effect already occurred.

Never blindly repeat an uncertain external side effect.

---

# 7. BOUNDED SELF-CORRECTION, RECOVERY & ANTI-LOOP SAFEGUARDS

Define:

```text
step_retry_count
run_retry_count
replan_count
```

and maximum bounds.

---

# 7.1 Step retry

A step can retry only when:

```text
retry_policy.allow_retry
AND
error.retryable
AND
attempt < max_attempts
AND
run budget permits
```

---

# 7.2 Re-planning limit

Default:

```text
max_replans_per_run = 3
```

On exceed:

```text
REPLAN_LIMIT_EXCEEDED
→ FAILED
```

---

# 7.3 Oscillation detection

Compute a planning signature:

```text
hash(
  graph_version_normalized
  +
  failed_step
  +
  error_code
  +
  relevant_observation_hash
)
```

Repeated ineffective signatures trigger:

```text
GRAPH_OSCILLATION_DETECTED
```

---

# 7.4 Tool-loop detection

Detect:

```text
same step
+
same tool
+
same normalized arguments
+
same failure
```

repeated beyond threshold.

Terminate or escalate to re-planning.

---

# 7.5 Graceful degradation

When:

- model unavailable
- token budget exhausted
- tool unavailable
- browser unavailable
- VRAM constrained

the execution engine must preserve completed work and move into a controlled recovery/failure path.

No state corruption.

---

# 8. SUBGRAPH ORCHESTRATION & DYNAMIC STEP BRANCHING

Define step-level execution as a subgraph:

```text
agent_dispatch
      ↓
tool_executor
      ↓
observation_capture
      ↓
verifier
```

The outer run graph determines:

```text
which step
when
with what dependencies
```

---

# 8.1 Fan-out

Independent branches may execute concurrently.

Example:

```text
A ──┐
    ├──→ C
B ──┘
```

A and B may run concurrently when:

- no dependency
- no conflicting resources
- no shared exclusive desktop state
- token/VRAM budget allows
- policy permits

---

# 8.2 Desktop serialization

Computer-control subgraphs must respect the physical desktop mutex.

Two UI steps may not execute concurrently against the same desktop session.

---

# 8.3 Join barrier

Define exact join semantics.

A join step becomes ready only when all required predecessors meet:

```text
succeeded
```

or their declared conditional terminal state.

If one branch fails:

```text
join blocked
→ recovery according to graph policy
```

---

# 8.4 Dynamic branches

Support conditional routes based on:

```text
verification result
approval result
tool result
resource state
```

The graph itself remains acyclic.

---

# 9. REAL-TIME SSE EVENT STREAMING & TELEMETRY

Define the internal event model and client-facing SSE model.

---

# 9.1 Event ordering

Every run must have monotonic:

```text
event_sequence
```

Example:

```text
102
103
104
105
```

No event may be emitted with a sequence lower than an already committed event for the same run.

---

# 9.2 SSE event envelope

Provide:

```python
class SSEEventEnvelope(BaseModel):
    event_id: UUID
    run_id: UUID
    sequence: int
    event_type: str
    trace_id: str
    created_at: datetime
    payload: dict[str, Any]
```

Define examples:

```text
run.started
run.planning
step.ready
agent.spawned
tool_call.started
tool_call.completed
observation.captured
verification.started
verification.completed
run.paused
run.waiting_approval
recovery.started
run.completed
run.failed
run.cancelled
```

---

# 9.3 Outbox / delivery semantics

To avoid losing events:

```text
state mutation
+
event record
```

must be persisted transactionally where possible.

SSE delivery may be at-least-once.

Clients should deduplicate using:

```text
run_id + sequence
```

Define replay semantics after reconnect.

---

# 9.4 Client reconnection

Support:

```text
Last-Event-ID
```

or an equivalent sequence parameter.

On reconnect:

```text
query persisted events after last sequence
→ replay in order
→ resume live stream
```

---

# 10. COMPLETE DATA CONTRACTS & INTERFACES

Provide complete Pydantic v2 models and Python Protocols.

Required:

- `BrainStateModel`
- `StepStateModel`
- `RunStatus`
- `StepStatus`
- `CheckpointRecord`
- `ApprovalCheckpointPayload`
- `ExecutionMilestone`
- `VerificationResult`
- `RecoveryDecision`
- `WorkflowError`
- `SSEEventEnvelope`
- `ExecutionTelemetryRecord`
- `GraphExecutionRequest`
- `RunResumeRequest`
- `RunCancellationRequest`

---

# 10.1 `GraphExecutionEngineProtocol`

Provide:

```python
class GraphExecutionEngineProtocol(Protocol):
    async def compile_graph(
        self,
        run_id: UUID,
        intent: StructuredIntent,
        context: ContextSnapshot,
        cancellation: CancellationToken,
    ) -> TaskDAG:
        ...

    async def start_run(
        self,
        request: GraphExecutionRequest,
        cancellation: CancellationToken,
    ) -> UUID:
        ...

    async def resume_run_with_approval(
        self,
        request: RunResumeRequest,
        cancellation: CancellationToken,
    ) -> None:
        ...

    async def cancel_run(
        self,
        request: RunCancellationRequest,
    ) -> None:
        ...

    async def rehydrate_stranded_runs(
        self,
        cancellation: CancellationToken,
    ) -> list[UUID]:
        ...
```

Improve signatures where required, but maintain clear subsystem boundaries.

---

# 11. LANGGRAPH STATEGRAPH IMPLEMENTATION

Provide a real LangGraph implementation.

Show:

```python
builder = StateGraph(BrainStateModel)
```

and concrete node registration for:

```text
context_collector
intent_classifier
task_planner
step_evaluator
approval_gate
agent_dispatch
tool_executor
observation
verification
recovery
finalizer
```

Define:

- entry point
- normal edges
- conditional edges
- interruption points
- checkpoint integration
- compile process
- invocation/resume semantics

The code must be compatible with the LangGraph version chosen in the source architecture or explicitly document the required version as an implementation decision.

---

# 11.1 Conditional route implementations

Provide complete Python functions:

```python
def route_after_step_evaluator(
    state: BrainStateModel,
) -> Literal[
    "approval_gate",
    "agent_dispatch",
    "finalizer",
    "recovery",
]:
    ...
```

and equivalents for:

```text
route_after_verification
route_after_recovery
route_after_approval
```

No pseudo-code.

---

# 11.2 Node idempotency

Every node handler must be safe against duplicate invocation where LangGraph/checkpoint recovery may cause re-entry.

Use:

```text
run_id
+
node_name
+
step_key
+
checkpoint_version
```

or the exact architecture-approved idempotency identity.

Do not duplicate physical side effects.

---

# 12. DATABASE INTEROPERABILITY

Align with:

```text
runs
run_steps
approvals
audit_events
```

and any checkpoint extensions required by `idea.md`.

---

## 12.1 `runs`

Persist:

```text
task_text
status
context_snapshot
plan
sequence_no
current graph/checkpoint version
```

according to the existing schema.

---

## 12.2 `run_steps`

Persist:

```text
step ID
step key
agent key
action
dependencies
status
attempt count
sequence/version
outputs
verification
error
```

Do not overwrite immutable history.

---

## 12.3 Approvals

Persist:

```text
approval request
protected action
argument hash
risk
status
decider
timestamps
policy version
```

---

## 12.4 Audit events

Persist immutable execution events.

No sensitive payloads by default.

---

# 13. CANCELLATION & USER ABORT

Define:

```text
POST /api/v1/runs/{id}/cancel
```

flow:

```text
API
→ cancellation request persisted
→ event emitted
→ execution engine observes signal
→ active node cancellation
→ agent cancellation
→ tool cancellation
→ resource release
→ checkpoint
→ CANCELLED
```

Cancellation must be idempotent.

A completed run cannot become cancelled.

---

# 14. FAILURE TAXONOMY

Define complete machine-readable errors including:

```text
GRAPH_COMPILE_FAILED
STATE_SCHEMA_INVALID
GRAPH_CHECKPOINT_CORRUPTED
CONCURRENT_STATE_CONFLICT
NODE_EXECUTION_FAILED
NODE_TIMEOUT
DEPENDENCY_STATE_INVALID
APPROVAL_REQUIRED
APPROVAL_REJECTED
APPROVAL_INVALIDATED
APPROVAL_EXPIRED
TOOL_EXECUTION_FAILED
AGENT_DISPATCH_FAILED
OBSERVATION_FAILED
VERIFICATION_FAILED
RECOVERY_EXHAUSTED
REPLAN_LIMIT_EXCEEDED
GRAPH_OSCILLATION_DETECTED
RUN_TOKEN_BUDGET_EXCEEDED
RESOURCE_UNAVAILABLE
STALE_EXTERNAL_STATE
CRASH_RECOVERY_REQUIRED
CRASH_RECOVERY_INCONCLUSIVE
SSE_EVENT_SEQUENCE_CONFLICT
RUN_CANCELLATION_REQUESTED
```

Each error must contain:

- stable code
- severity
- retryability
- run ID
- step ID where applicable
- trace ID
- checkpoint version
- sanitized reason
- recovery action

---

# 15. OBSERVABILITY & EXECUTION TELEMETRY

Define structured telemetry for:

```text
run_duration_ms
node_duration_ms
queue_wait_ms
approval_wait_ms
recovery_duration_ms
replan_count
retry_count
token_usage
tool_calls
verification_latency
checkpoint_latency
SSE_event_lag
```

Dimensions:

- run
- step
- node
- agent
- model
- tool
- graph version
- worker

Do not log raw sensitive context.

---

# 16. PERFORMANCE, CONCURRENCY & BACKPRESSURE

Define:

- maximum active runs
- maximum steps per run
- maximum concurrent steps
- maximum queued work
- checkpoint write timeout
- event-bus queue size
- SSE client limits
- graph serialization limits
- recovery worker concurrency

---

# 16.1 Event backpressure

If an SSE client cannot keep up:

```text
persist event
→ disconnect slow client
→ allow reconnect/replay
```

Do not block workflow execution indefinitely waiting for UI delivery.

---

# 16.2 Scheduler fairness

Define deterministic fairness between runs.

Do not permit one run with many fan-out branches to starve others.

Possible mechanism:

```text
per-run concurrency cap
+
round-robin/weighted queue
+
priority aging
```

Keep policy explicit and deterministic.

---

# 17. CRASH RECOVERY STATE MACHINE

Define:

```text
HEALTHY
   ↓ crash
UNKNOWN
   ↓ startup scan
REHYDRATING
   ↓
VALIDATING_CHECKPOINT
   ↓
RECONCILING_EXTERNAL_STATE
   ├── SAFE_TO_RESUME
   ├── NEEDS_REPLAN
   └── TERMINAL_FAILURE
```

For each branch define exact persistence/event behavior.

---

# 18. REFERENCE PACKAGE STRUCTURE

Provide a concrete implementation tree:

```text
syncnode/
└── workflow_execution/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── state.py
    ├── reducers.py
    ├── graph.py
    ├── nodes/
    │   ├── __init__.py
    │   ├── context.py
    │   ├── intent.py
    │   ├── planner.py
    │   ├── evaluator.py
    │   ├── approval.py
    │   ├── agent_dispatch.py
    │   ├── tool_executor.py
    │   ├── observation.py
    │   ├── verification.py
    │   ├── recovery.py
    │   └── finalizer.py
    ├── routing.py
    ├── approvals.py
    ├── checkpoints.py
    ├── persistence.py
    ├── recovery.py
    ├── cancellation.py
    ├── events.py
    ├── sse.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_state.py
        ├── test_reducers.py
        ├── test_graph.py
        ├── test_routing.py
        ├── test_approval.py
        ├── test_checkpoint.py
        ├── test_recovery.py
        ├── test_cancellation.py
        ├── test_events.py
        ├── test_sse.py
        ├── test_persistence.py
        ├── test_crash_recovery.py
        ├── test_security.py
        └── test_determinism.py
```

Adapt to the repository structure from `idea.md`.

---

# 19. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The generated `WORKFLOW_EXECUTION_LANGGRAPH.md` MUST contain real Python 3.12+ implementations for at least:

1. `BrainStateModel`
2. run lifecycle transition validation
3. step lifecycle transition validation
4. pure state reducers
5. LangGraph `StateGraph` construction
6. node registration
7. conditional routing predicates
8. graph compilation
9. step subgraph execution
10. approval interrupt
11. approval persistence
12. approval resume
13. checkpoint serialization
14. checkpoint hashing
15. PostgreSQL checkpoint persistence
16. optimistic sequence-number update
17. crash-rehydration routine
18. stranded-running-step reconciliation
19. retry accounting
20. re-plan accounting
21. oscillation detection
22. cancellation propagation
23. SSE event generation
24. monotonic event sequencing
25. reconnect/replay behavior
26. event persistence/outbox contract
27. finalization
28. complete `GraphExecutionEngineProtocol`
29. terminal error propagation
30. complete execution-engine orchestration

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- compatible with the selected LangGraph version
- fully typed
- async-compatible
- syntactically complete
- executable with documented dependencies
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder implementations
- free of unexplained magic constants

Where LangGraph APIs vary by version, identify the chosen version explicitly and isolate version-sensitive adapters.

---

# 20. TESTING & ACCEPTANCE CRITERIA

Define:

- state-machine tests
- reducer tests
- graph compilation tests
- edge-routing tests
- approval interruption tests
- checkpoint tests
- crash-recovery tests
- cancellation tests
- concurrency tests
- persistence tests
- SSE tests
- deterministic replay tests
- security tests
- integration/e2e tests

Mandatory tests:

### Run lifecycle

Illegal transitions are rejected.

### Step lifecycle

Duplicate/invalid transitions cannot corrupt state.

### Durable checkpoint

Every externally significant state transition survives process restart.

### Approval safety

A waiting-approval run never executes the protected action before valid approval.

### Approval invalidation

Changing action arguments invalidates the previous approval.

### Crash safety

A crash during a side-effect step does not blindly repeat the side effect.

### Checkpoint integrity

Corrupted state hashes are detected.

### Concurrency

Concurrent workers cannot overwrite newer workflow state.

### Event ordering

SSE events are monotonic and replayable.

### Cancellation

Cancellation propagates to active subcomponents and eventually reaches terminal `CANCELLED`.

### Recovery bounds

Replans/retries remain within configured limits.

### Determinism

Identical deterministic state and configuration produce identical route/transition decisions.

---

# 21. END-TO-END WORKFLOW EXAMPLE

Use:

> “Write a story about a tree and send it to Rahul.”

Show the complete durable execution lifecycle:

```text
POST /api/v1/runs
        ↓
QUEUED
        ↓
PLANNING
        ↓
ContextCollector
        ↓
IntentClassifier
        ↓
TaskPlanner
        ↓
RUNNING
        ↓
Document Agent
        ↓
DOCX artifact
        ↓
Observation
        ↓
Verification
        ↓
Browser Agent
        ↓
Draft email
        ↓
ApprovalGate
        ↓
WAITING_APPROVAL
        ↓
Persist checkpoint
        ↓
Human approves
        ↓
Resume graph
        ↓
Send email
        ↓
Post-send observation
        ↓
Verification
        ↓
Finalizer
        ↓
COMPLETED
```

Then include a crash scenario:

```text
send_email physical action
        ↓
backend crashes before result persistence
        ↓
startup recovery
        ↓
load checkpoint
        ↓
inspect tool-call/idempotency state
        ↓
observe current mailbox state
        ↓
determine whether send occurred
        ↓
resume OR replan safely
```

Do not blindly send a second email.

---

# 22. SECURITY MODEL

Explicitly cover:

- model-generated graph injection
- malicious state payloads
- checkpoint tampering
- replay attacks
- approval replay
- approval substitution
- sequence-number races
- duplicate side effects
- stale execution state
- cross-run state leakage
- event-order corruption
- unauthorized resume
- cancellation bypass
- tool permission bypass
- context contamination

Required guarantees:

1. Persistent checkpoints are integrity-checked.
2. State transitions are validated.
3. Approval decisions are authenticated and bound to exact actions.
4. Sequence numbers prevent stale writes.
5. Side effects are idempotency-aware.
6. Crash recovery re-observes the external world.
7. The model cannot directly set terminal run states.
8. The model cannot bypass approval.
9. Event sequences are monotonic.
10. Sensitive state is not emitted into SSE without policy.
11. Cross-run checkpoint data cannot be loaded.
12. Recovery is bounded.
13. No cloud workflow service is required.

---

# 23. INTEGRATION CONTRACTS

Define exact subsystem boundaries.

### Context Engine

Provides:

```text
ContextSnapshot
snapshot hash
delta updates
```

### Intent Engine

Provides:

```text
StructuredIntent
risk
grounded entities
```

### Planner

Provides:

```text
TaskDAG
graph validation
re-plan graph
```

### Agent Registry / Spawner

Provides:

```text
AgentInstance
scoped tools
model binding
resource state
```

### Token Management

Provides:

```text
TokenBudget
TokenLease
usage reconciliation
```

### Tool Registry

Provides:

```text
ToolCallResult
observation references
idempotency state
```

### Verifier

Provides:

```text
VerificationResult
failure evidence
```

### Policy / Approval

Provides:

```text
approval requirements
approval decisions
```

The Workflow Execution Engine orchestrates these services but does not replace them.

---

# 24. FINAL ENGINE CONTRACT

The Workflow Execution & LangGraph subsystem SHALL:

- maintain durable run state
- execute a deterministic workflow state machine
- compile and execute validated task graphs
- preserve step lifecycle invariants
- integrate Context Engine, Intent Engine, Planner, Agent Runtime, Tool Registry, and Verifier
- persist checkpoints
- support approval suspension and resumption
- enforce bounded retries
- enforce bounded re-planning
- detect workflow oscillation
- support conditional branches
- support safe fan-out and joins
- serialize physical desktop work through downstream resource locks
- support crash recovery
- re-observe external state after uncertain crashes
- prevent duplicate physical side effects
- emit ordered SSE telemetry
- support client reconnect/replay
- support cancellation
- remain auditable
- remain local-first
- remain independently testable

The subsystem SHALL NOT:

- perform arbitrary tool execution itself
- invent graph steps after validation
- bypass policy
- fabricate approvals
- directly modify OS state
- assume memory-only execution
- blindly replay uncertain side effects
- silently overwrite newer checkpoints
- emit unordered workflow events
- allow infinite retries/re-plans
- use cloud orchestration services by requirement

---

# 25. OUTPUT QUALITY BAR

The generated `WORKFLOW_EXECUTION_LANGGRAPH.md` must be:

- exhaustive
- production-grade
- implementation-ready
- state-machine precise
- checkpoint-safe
- crash-resilient
- concurrency-safe
- approval-safe
- event-ordering aware
- compatible with SyncNode

Do not produce:

- generic LangGraph tutorials
- generic workflow examples
- marketing language
- vague recommendations
- pseudo-code presented as implementation
- undefined classes
- placeholder functions
- `TODO`
- `TBD`
- `pass`
- unexplained constants
- cloud-dependent orchestration

Use throughout:

- Pydantic v2
- Python Protocols
- LangGraph `StateGraph`
- deterministic edge predicates
- state transition tables
- reducer functions
- checkpoint schemas
- SQL transactions
- optimistic concurrency control
- approval interrupt/resume semantics
- SSE envelopes
- event sequencing
- crash-recovery algorithms
- anti-loop circuit breakers
- resource-aware subgraphs
- security invariants
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
WORKFLOW_EXECUTION_LANGGRAPH.md
```
