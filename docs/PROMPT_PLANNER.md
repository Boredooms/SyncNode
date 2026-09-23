# PROMPT: Generate `PLANNER.md` Technical Specification

You are a **Principal Distributed Systems Engineer and Lead AI Orchestration Architect** specializing in:

- deterministic task planning
- DAG compilation
- workflow scheduling
- dependency resolution
- dynamic graph mutation
- stateful multi-agent execution
- checkpointing and crash recovery
- approval-aware orchestration
- local-first / air-gapped AI systems

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, implementation-ready technical specification** titled:

> `PLANNER.md`

This document governs the **SyncNode Task Planner & Graph Engine** inside the Brain. It converts validated structured intent and trusted Context Engine snapshots into executable, dependency-aware task graphs; validates graph feasibility; injects mandatory approval barriers; schedules ready work; coordinates bounded concurrency; persists graph state; and performs bounded, non-destructive re-planning when runtime conditions invalidate the current plan.

The Planner is a **graph compiler and scheduler**, not an execution engine.

It must never directly:

- click UI
- mutate files
- invoke arbitrary shell commands
- send email
- approve risky actions
- bypass policy
- overwrite canonical observations

Those remain responsibilities of downstream execution, policy, approval, and verification subsystems.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architectural source of truth.

Before writing the specification:

1. Read the complete `idea.md`.
2. Extract its:
   - component boundaries
   - task/run state model
   - database entities
   - functional requirements
   - non-functional requirements
   - security constraints
   - phase-1 scope
   - agent/tool definitions
   - approval requirements
   - recovery requirements
3. Preserve SyncNode terminology and existing boundaries.
4. Do not silently contradict `idea.md`.
5. Do not replace the design with a generic workflow library.
6. Do not introduce cloud dependencies.
7. Do not assume unrestricted browser or shell execution.
8. Where implementation details are unspecified, make an explicit engineering choice under:
   > **Implementation Decision**
9. Clearly distinguish:
   - model-generated graph proposal
   - deterministic graph normalization
   - deterministic policy validation
   - scheduler state
   - persisted database state
   - runtime execution state
   - verifier observations

The generated specification must be suitable for direct engineering implementation without a second architecture document.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & PLANNING PHILOSOPHY

Position the Planner precisely inside the Brain:

```text
API / Run Creation
      ↓
Intent Engine
      ↓
Structured Intent
      ↓
Context Engine Snapshot
      ↓
┌───────────────────────────────┐
│      TASK PLANNER             │
│                               │
│  Graph Synthesis              │
│  Graph Validation             │
│  Policy Interlock             │
│  Approval Injection           │
│  Topological Scheduler        │
│  Re-planning                  │
│  Checkpointing                │
└──────────────┬────────────────┘
               ↓
        Agent / Tool Dispatch
               ↓
        Execution + Verification
               ↓
        Observations / Failures
               ↓
         Re-plan when needed
```

---

## 1.1 Core invariants

Enforce:

### Model proposes; deterministic infrastructure disposes

The local model may propose:

- nodes
- edges
- dependencies
- agent assignments
- action types
- inputs
- postconditions
- fallback strategies

The Planner runtime must deterministically validate every field before the graph becomes executable.

### DAG acyclicity

No executable graph may contain cycles.

### State-machine correctness

Every step must follow the allowed lifecycle:

```text
pending
  ↓
ready
  ↓
running
  ├── waiting_approval
  ├── retrying
  ├── succeeded
  ├── failed
  ├── skipped
  └── cancelled
```

Define which transitions are legal and reject invalid transitions.

### Approval isolation

High-risk operations must become explicit graph barriers.

At minimum:

```text
EXTERNAL_COMMUNICATION
DESTRUCTIVE_LOCAL
```

must be intercepted with approval where required by policy.

### Non-destructive re-planning

Completed verified work is immutable.

A failure may invalidate unfinished downstream work but must not destroy already-verified artifacts or rewrite the historical record.

### Durable orchestration state

The database is authoritative for persisted run/step state.

In-memory LangGraph state must be reconstructable after restart.

---

# 1.2 Required lifecycle diagram

Include both a Mermaid and/or ASCII diagram covering:

```text
Structured Intent + Context Snapshot
              ↓
      Local LLM Graph Proposal
              ↓
      JSON Schema Validation
              ↓
     Semantic Normalization
              ↓
     Graph Feasibility Check
              ↓
      Policy / Capability Check
              ↓
      Approval Gate Injection
              ↓
       DAG Topological Build
              ↓
       Scheduler Initialization
              ↓
         Ready Step Set
              ↓
        Agent Dispatch
              ↓
      Runtime Observation
          /          \
      Success       Failure
        ↓              ↓
  State Commit    Retry / Recovery
                       ↓
                Failure Analysis
                       ↓
                 Re-plan Engine
                       ↓
               Partial Graph Splice
                       ↓
              Persist New Version
```

Clearly distinguish probabilistic and deterministic stages.

---

# 2. TASK GRAPH ONTOLOGY & DAG DATA STRUCTURES

Define a complete graph ontology.

---

## 2.1 Graph primitives

Define:

### Node

An atomic executable intent:

```text
step_key
agent_key
action_type
inputs
dependencies
preconditions
postconditions
retry_policy
approval_requirement
resource_requirements
timeout
failure_strategy
```

### Edge

A dependency or data-flow relationship.

Support edge types such as:

```text
SEQUENCE
DATA
CONDITIONAL_SUCCESS
CONDITIONAL_FAILURE
APPROVAL
```

The graph must remain acyclic regardless of branch type.

---

## 2.2 Required Pydantic models

Provide complete Pydantic v2 models for:

- `PlanStepNode`
- `PlanStepInput`
- `OutputReference`
- `TaskEdge`
- `TaskDAG`
- `StepLifecycle`
- `RetryPolicy`
- `Postcondition`
- `Precondition`
- `ResourceRequirement`
- `ApprovalRequirement`
- `FailureStrategy`
- `GraphMetadata`
- `PlanVersion`

Add validators for:

- unique step keys
- bounded list sizes
- valid identifiers
- dependency existence
- no self-dependencies
- valid references
- valid lifecycle transitions
- timeouts and retry bounds

---

# 2.3 Canonical action types

Define a normalized action vocabulary, for example:

```text
observe
read_file
search_workspace
create_artifact
edit_file
delete_file
open_application
focus_control
navigate_browser
draft_email
attach_file
send_email
verify_artifact
verify_ui
wait_approval
recover
```

The model may propose aliases, but deterministic normalization maps them into canonical action types.

Unknown actions must fail closed.

---

# 3. PRE-FLIGHT GRAPH VALIDATION & FEASIBILITY ENGINE

The Planner must validate a model-generated graph before execution.

Implement these deterministic checks.

---

## 3.1 Structural validation

Verify:

1. graph has at least one node
2. every node has a unique `step_key`
3. all dependencies reference existing nodes
4. no node depends on itself
5. all edges reference existing nodes
6. all output references reference known producers
7. all input bindings resolve
8. all entry nodes are valid roots
9. terminal nodes are reachable
10. graph contains no cycles
11. graph version is valid
12. node retry policies are bounded
13. timeouts are within configured limits

---

## 3.2 Cycle detection

Provide a concrete implementation using Kahn's algorithm or Tarjan's algorithm.

Requirements:

- `O(V + E)`
- deterministic iteration ordering
- explicit cycle members in failure output
- stable error serialization

Required error:

```text
CYCLIC_DEPENDENCY_DETECTED
```

Never dispatch a graph that fails cycle validation.

---

## 3.3 Agent capability matrix

Validate:

```text
TaskNode.agent_key
      ↓
agent_definitions
      ↓
agent active?
      ↓
required tools
      ↓
tool_definitions
      ↓
tool explicitly allowed?
```

Reject:

```text
AGENT_NOT_FOUND
TOOL_NOT_FOUND
TOOL_PERMISSION_VIOLATION
```

Never trust the model's claim that an agent or tool exists.

---

## 3.4 Workspace/path pre-flight

Inspect static file/path arguments.

Validate:

- canonical absolute path
- allowed workspace root
- operation type
- read/write permission
- path existence where required
- destination safety
- traversal resistance
- symlink/reparse-point policy

Reuse the security contract of the Context Engine instead of reimplementing incompatible rules.

---

## 3.5 Resource feasibility

Every node may declare:

```text
gpu_tokens
gpu_memory_mb
desktop_focus
browser_session
filesystem_lock
network_policy
```

The Planner must detect obvious resource conflicts before scheduling.

Examples:

- two active computer-control nodes cannot own the same desktop focus simultaneously.
- two steps needing exclusive browser state cannot execute concurrently.
- GPU-heavy model steps may be serialized if resource policy requires it.

---

# 4. TOPOLOGICAL SCHEDULING & CONCURRENCY RESOLUTION

Define the scheduler as a deterministic state evaluator.

A node becomes `ready` only when all mandatory prerequisites are complete.

For ordinary dependencies:

```text
all(dependency.status == succeeded)
        ↓
READY
```

Conditional branches must be resolved through explicit edge conditions.

---

## 4.1 Ready-set calculation

Provide concrete Python implementation for:

```python
compute_ready_steps(graph, state)
```

Deterministic ordering must use:

```text
priority
→ sequence_rank
→ dependency depth
→ step_key
```

or another explicitly defined stable ordering.

---

# 4.2 Parallel dispatch

Identify disjoint branches that can execute concurrently.

Parallelism is constrained by:

```text
DAG dependency rules
+
agent availability
+
tool locks
+
desktop UI mutex
+
browser session ownership
+
GPU/VRAM budget
+
global worker limit
```

Define a resource-lock model.

---

# 4.3 Desktop UI mutex

Only one active operation should control the same physical desktop session at a time unless the architecture explicitly supports isolated desktops.

Define:

```text
desktop:{machine_id}:{session_id}
```

as an exclusive resource lock.

A second Computer Agent step must wait rather than race for focus.

---

# 4.4 Step barriers

For join nodes:

```text
A ──┐
    ├──→ C
B ──┘
```

C cannot become ready until all required predecessors satisfy their terminal conditions.

Define failure semantics if one branch is permanently failed.

---

# 5. POLICY INTERLOCK & APPROVAL CHECKPOINT INJECTION

Risk must be checked before scheduling.

Recognize:

```text
READ
WRITE_LOCAL
DESTRUCTIVE_LOCAL
EXTERNAL_COMMUNICATION
SYSTEM_ADMIN
```

The Planner may consume risk classifications from the Intent Engine, but it must independently validate step action semantics and refuse inconsistent risk declarations.

---

## 5.1 Approval gate transformation

Example:

```text
send_email
```

becomes:

```text
draft_email
      ↓
approval_checkpoint
      ↓
send_email
      ↓
verify_sent
```

Define exact synthetic node schema.

Approval nodes must be:

- non-bypassable
- persisted
- auditable
- dependency-bound
- tied to the protected step
- associated with the required approval policy

---

## 5.2 Run approval state

When a step reaches:

```text
waiting_approval
```

the run must transition consistently into:

```text
WAITING_APPROVAL
```

Persist an approval record before pausing.

On rejection:

```text
approval rejected
→ protected node cannot execute
→ dependents transition according to policy
→ run terminates or branches deterministically
```

Do not allow the model to approve itself.

---

# 6. DYNAMIC RE-PLANNING & GRAPH MUTATION ENGINE

Define a bounded, versioned graph mutation model.

---

## 6.1 Re-plan triggers

Re-planning may be triggered by:

- exhausted retries
- failed postcondition
- unexpected UI state
- external file modification
- missing application
- tool capability change
- stale browser state
- approval rejection when an alternate path is permitted
- resource unavailability
- verifier-detected state drift

Every trigger must be classified.

---

# 6.2 Failure isolation

Given failed step `F`:

```text
Ancestors(F) = preserve
F            = failed
Descendants(F) = stale/cancelled
Independent branches = preserve where safe
```

Define a deterministic graph-invalidation algorithm.

Do not invalidate unrelated completed or ready branches unless the dependency graph proves they are affected.

---

# 6.3 Immutable completed artifacts

Completed steps retain:

- output references
- artifact IDs
- artifact hashes
- verification assertions
- timestamps
- execution metadata

A re-plan may reference those outputs.

It must not overwrite them merely because a new graph version exists.

---

# 6.4 Graph splicing

Define:

```text
old graph version
      ↓
failure boundary
      ↓
stale downstream subgraph
      ↓
new recovery graph
      ↓
splice into new graph version
      ↓
validate
      ↓
persist atomically
```

Every graph mutation receives:

- parent graph version
- new graph version
- mutation reason
- failed step
- preserved nodes
- replaced nodes
- inserted nodes

---

# 6.5 Re-plan limits

Default bounded depth:

```text
maximum consecutive re-plans per run = 3
```

Make configurable only if `idea.md` permits.

When exceeded:

```text
REPLAN_LIMIT_EXCEEDED
```

Terminate the active planning attempt and persist the dead-letter state.

---

# 7. MODEL PROMPT ENGINEERING & PLAN SYNTHESIS

Provide the exact system prompt used by the local Model Gateway for plan generation.

The prompt must tell the model:

- output JSON only
- follow the supplied schema
- never invent tools
- never invent agent IDs
- never invent filesystem paths
- never bypass policy
- explicitly express dependencies
- express preconditions
- express postconditions
- identify required approval
- use only provided context
- propose fallback strategies without executing them

Required rule:

> The Planner model proposes a graph. Deterministic SyncNode infrastructure is authoritative for graph validity, dependencies, permissions, risk, resource feasibility, approvals, and execution readiness.

---

# 7.1 Structured-output enforcement

Define:

```text
Prompt
→ Model Gateway structured output
→ JSON parse
→ Pydantic validation
→ semantic graph normalization
→ deterministic validation
```

Specify:

- schema hash
- schema version
- maximum node count
- maximum edge count
- maximum input size
- enum enforcement
- additional-properties policy

Reject Markdown fences and conversational prose.

---

# 7.2 Few-shot planning corpus

Provide complete production-style examples for:

### A. Document workflow

```text
Generate content
→ create DOCX
→ verify artifact
```

### B. Full hybrid workflow

```text
Generate content
→ create document
→ open Word
→ manipulate document
→ verify save
→ open browser
→ compose email
→ attach document
→ approval
→ send
→ verify sent state
```

### C. Failure recovery

```text
Expected Save control missing
→ verification failure
→ bounded alternative UI strategy
→ re-plan only affected downstream graph
```

For each example show:

- input intent
- model graph proposal
- validated graph
- approval gates
- expected postconditions

---

# 8.3 Self-repair protocol

When graph synthesis fails:

```text
proposal
→ validation errors
→ bounded repair prompt
→ second proposal
→ revalidate
→ terminal planning failure
```

Maximum repair count must be configurable and bounded.

Repair prompts must contain only actionable validation errors and the minimum necessary graph/context metadata.

Do not include secrets.

---

# 8.4 Deterministic graph normalization

Before acceptance, normalize:

- node ordering
- edge ordering
- action names
- dependency arrays
- retry-policy defaults
- optional field representation
- resource declarations

Identical semantic proposals must normalize to stable serialization whenever the same environment and configuration are used.

---

# 9. DATABASE PERSISTENCE, CHECKPOINTING & CONCURRENCY

Align explicitly with:

```text
runs
run_steps
approvals
```

and any related schema in `idea.md`.

---

## 9.1 `runs`

Persist:

```text
task_text
status
plan
context_snapshot
```

along with graph version/checkpoint metadata where supported by `idea.md`.

Do not persist an unvalidated graph as the authoritative executable plan.

---

# 9.2 `run_steps`

Map each graph node into:

```text
step_key
sequence_no
agent_key
action_type
dependencies
status
inputs
postconditions
retry policy
graph version
```

Use atomic insertion.

Define initial state:

```text
pending
```

or:

```text
ready
```

based on validated dependency state.

---

# 9.3 Optimistic concurrency control

Use:

```text
sequence_no
```

or the existing version field specified by `idea.md`.

For status updates:

```text
UPDATE run_steps
SET status = :new_status,
    sequence_no = sequence_no + 1
WHERE step_id = :id
  AND sequence_no = :expected_sequence
```

If zero rows are affected:

```text
CONCURRENT_STATE_CONFLICT
```

must be surfaced.

Never overwrite a newer scheduler decision.

---

# 9.4 Crash recovery

Implement startup recovery:

```text
database scan
→ identify planning/running runs
→ load run_steps
→ load active graph version
→ reconstruct dependency state
→ reconcile stranded running steps
→ recompute ready set
→ resume safely
```

Define how to classify a step that was `running` when the worker crashed.

Do not assume a crashed action completed merely because a row says `running`.

Require observation or execution-layer reconciliation.

---

# 10. STEP LIFECYCLE STATE MACHINE

Define complete transition rules.

Required lifecycle:

```text
PENDING
  ↓
READY
  ↓
RUNNING
  ├── WAITING_APPROVAL
  ├── RETRYING
  ├── SUCCEEDED
  ├── FAILED
  ├── SKIPPED
  └── CANCELLED
```

Define allowed transitions as a static transition map.

Reject illegal transitions such as:

```text
SUCCEEDED → RUNNING
CANCELLED → READY
SKIPPED → RUNNING
```

unless an explicit graph-version migration/recovery operation is defined.

---

# 11. RESILIENCE, SAFEGUARDS & ANTI-LOOP CIRCUIT BREAKERS

Implement safeguards for:

- infinite re-planning
- graph oscillation
- duplicate plan generation
- repeated identical failed actions
- retry storms
- scheduler starvation
- orphaned nodes
- stale graph versions
- approval deadlocks
- permanently unavailable resources

---

## 11.1 Graph oscillation detection

Hash normalized planning state:

```text
graph_hash
+
failure_signature
+
relevant_observation_hash
```

Track recent planning signatures.

If the same ineffective planning state repeats beyond a configured threshold:

```text
GRAPH_OSCILLATION_DETECTED
```

Stop re-planning.

---

## 11.2 Dead-letter graph

Define persistent dead-letter representation containing:

- graph version
- failure reason
- failed node
- execution trace reference
- current observation reference
- planning attempts
- model proposal hashes
- validation errors
- resource state
- timestamps

The dead-letter graph is immutable after finalization.

---

# 12. RESOURCE-AWARE SCHEDULING

Define scheduler resource constraints.

Resources can include:

```text
CPU
GPU
VRAM
desktop UI session
browser session
filesystem lock
exclusive application
agent worker
```

Create a typed resource model.

A step may declare:

```text
required_resources
exclusive_resources
estimated_vram_mb
estimated_tokens
timeout_seconds
```

The scheduler must not dispatch a step when required exclusive resources are unavailable.

---

# 13. PRIORITY & FAIRNESS

Define deterministic scheduling priority.

Possible components:

```text
explicit priority
dependency depth
critical-path urgency
age
resource availability
```

Provide a deterministic formula and stable tie-breakers.

Do not allow priority to bypass:

- dependency requirements
- policy
- approvals
- resource locks

Prevent starvation with bounded aging.

---

# 14. CRITICAL PATH & EXECUTION EFFICIENCY

Define optional critical-path analysis.

For a DAG:

```text
CriticalPath(node)
=
duration(node)
+
max(CriticalPath(parent))
```

Use configured expected durations.

Explain how the scheduler may prioritize the critical path without violating fairness or policy.

Clearly distinguish estimated planning metadata from measured runtime telemetry.

---

# 15. COMPLETE DATA CONTRACTS & INTERFACES

Provide complete Pydantic v2 models and Python Protocols.

Required interfaces:

## `PlannerProtocol`

```python
class PlannerProtocol(Protocol):
    async def generate_plan(
        self,
        intent: StructuredIntent,
        context: ContextSnapshot,
        cancellation: CancellationToken,
    ) -> TaskDAG:
        ...

    async def validate_plan(
        self,
        graph: TaskDAG,
        cancellation: CancellationToken,
    ) -> PlanValidationResult:
        ...

    async def replan(
        self,
        context: ReplanContext,
        cancellation: CancellationToken,
    ) -> TaskDAG:
        ...

    async def schedule_next(
        self,
        state: SchedulerState,
        cancellation: CancellationToken,
    ) -> list[PlanStepNode]:
        ...
```

Improve signatures where necessary, but preserve the deterministic stage boundaries.

Required models:

- `PlanStep`
- `PlanGraph`
- `TaskDAG`
- `PlanStepNode`
- `TaskEdge`
- `SchedulerState`
- `ReplanContext`
- `FailureContext`
- `PlanValidationResult`
- `ValidationIssue`
- `ApprovalGate`
- `ResourceLock`
- `ResourceRequirement`
- `PlanningMetrics`
- `GraphMutation`
- `GraphVersion`
- `DeadLetterGraph`

No type used in code may remain undefined.

---

# 16. CONCRETE IMPLEMENTATION EXAMPLES

The final `PLANNER.md` MUST include complete Python 3.12+ code for the most important algorithms.

At minimum provide real implementations for:

1. graph normalization
2. Pydantic graph validation
3. dependency validation
4. Kahn topological sorting
5. deterministic cycle detection
6. ready-set calculation
7. state transition validation
8. resource conflict detection
9. approval-gate injection
10. partial graph invalidation
11. graph splicing/version creation
12. re-plan depth protection
13. graph oscillation detection
14. structured model-output parsing
15. bounded graph-repair loop
16. optimistic SQL step update
17. crash-state rehydration
18. deterministic scheduler ordering
19. dead-letter serialization
20. complete planner orchestration method

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- type annotated
- async-compatible where required
- syntactically complete
- executable
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder implementations
- free of unexplained constants

Where infrastructure is abstracted, define a complete Protocol and provide either a concrete reference implementation or SQL transaction example.

---

# 17. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- property tests where useful
- DAG tests
- scheduler tests
- concurrency tests
- persistence tests
- crash recovery tests
- approval tests
- re-planning tests
- security tests
- deterministic replay tests
- integration tests

Minimum required tests:

### DAG correctness

- cyclic graph rejected
- dangling dependency rejected
- self-dependency rejected
- invalid edge rejected
- unreachable terminal detected

### State correctness

- illegal transition rejected
- concurrent update conflict detected
- duplicate completion does not corrupt state

### Approval safety

- external send always receives approval gate when policy requires it
- destructive action cannot bypass gate
- approval rejection blocks protected step

### Re-planning safety

- completed artifacts preserved
- failed step isolated
- unaffected branches preserved
- stale downstream branch invalidated
- new graph version references preserved outputs

### Determinism

Identical:

- structured intent
- context snapshot
- agent registry
- tool registry
- policy
- planner configuration

must produce identical deterministic:

- graph normalization
- validation result
- approval injection
- topological order
- scheduler ordering
- graph hash

The LLM proposal itself may be probabilistic; the acceptance boundary must be deterministic.

---

# 18. OBSERVABILITY & AUDIT

Define structured events:

```text
plan.generated
plan.validated
plan.rejected
scheduler.ready
scheduler.dispatched
step.state_changed
approval.inserted
run.waiting_approval
plan.replan_requested
plan.replanned
plan.graph_mutated
plan.oscillation_detected
plan.dead_lettered
scheduler.resource_blocked
scheduler.concurrent_update_conflict
```

Each event should include:

- event ID
- run ID
- step ID where applicable
- graph version
- trace ID
- timestamp
- actor/worker ID
- reason
- deterministic hashes
- latency

Never log unrestricted sensitive prompt/context payloads.

Use references, hashes, and sanitized summaries.

---

# 19. PERFORMANCE & CONCURRENCY TARGETS

Define measurable engineering targets for:

- graph validation latency
- topological sort latency
- ready-set calculation
- scheduler dispatch decision
- graph mutation
- SQL checkpoint commit
- re-plan compilation
- maximum graph size
- maximum concurrent runs
- maximum nodes per graph version

Give algorithmic complexity:

```text
cycle detection      O(V + E)
topological sorting  O(V + E)
ready-set evaluation O(V + E)
```

Explain where database and resource-locking overhead may dominate.

---

# 20. INTEGRATION WITH LANGGRAPH BRAIN

Specify exact interaction:

```text
Intent Engine
     ↓
Structured Intent
     ↓
Planner.generate_plan()
     ↓
TaskDAG
     ↓
Planner.validate_plan()
     ↓
Approval Injection
     ↓
Persist Graph
     ↓
LangGraph Scheduler
     ↓
Agent Execution
     ↓
Verifier
     ↓
Execution Observation
     ↓
Planner.replan() when required
```

The Planner owns graph state and scheduling decisions.

LangGraph remains the runtime state orchestration mechanism.

Execution components remain responsible for actually performing actions.

---

# 21. REFERENCE END-TO-END EXAMPLE

Use:

> “Write a story about a tree and send it to Rahul.”

Show a complete plan lifecycle:

```text
STRUCTURED INTENT
        ↓
PLAN PROPOSAL
        ↓
VALIDATION
        ↓
CONTENT_GENERATION
        ↓
DOCUMENT_CREATION
        ↓
DOCUMENT_VERIFICATION
        ↓
BROWSER_DRAFT
        ↓
APPROVAL_GATE
        ↓
SEND
        ↓
POST-SEND_VERIFICATION
```

Then show a runtime failure such as:

```text
SEND step blocked because expected browser control is absent
```

Demonstrate:

```text
failure isolation
→ downstream invalidation
→ preserve document artifact
→ capture current observation
→ bounded re-plan
→ new browser recovery subgraph
→ graph version increment
→ resume
```

Also demonstrate a terminal condition after the maximum re-plan depth is exhausted.

---

# 22. SECURITY MODEL

Threats to explicitly address:

- model graph injection
- invented tools
- invented agents
- path traversal
- unauthorized application targets
- policy bypass
- approval-node removal
- dependency poisoning
- graph cycle attacks
- graph explosion / oversized DAG
- retry amplification
- re-plan loops
- stale graph version execution
- cross-run state contamination
- concurrent scheduler races
- malicious conditional branches
- resource exhaustion

Required guarantees:

1. Model output is never executable without deterministic validation.
2. Unknown actions fail closed.
3. Unknown tools fail closed.
4. Unknown agents fail closed.
5. All paths are grounded and boundary-checked.
6. Risk and approval requirements cannot be downgraded by model output.
7. Approval gates cannot be removed by re-planning.
8. Completed verified artifacts remain immutable.
9. Graph versions are explicit and persisted.
10. Scheduler state transitions are concurrency-safe.
11. Oversized graphs are rejected.
12. Re-planning is bounded.
13. No external network dependency is required.

---

# 23. REFERENCE PACKAGE STRUCTURE

Provide a concrete source tree:

```text
syncnode/
└── planner/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── compiler.py
    ├── validator.py
    ├── dag.py
    ├── scheduler.py
    ├── resources.py
    ├── approvals.py
    ├── replanning.py
    ├── mutation.py
    ├── recovery.py
    ├── persistence.py
    ├── prompts.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_graph_validation.py
        ├── test_topology.py
        ├── test_scheduler.py
        ├── test_resources.py
        ├── test_approvals.py
        ├── test_replanning.py
        ├── test_mutation.py
        ├── test_recovery.py
        ├── test_persistence.py
        ├── test_security.py
        └── test_determinism.py
```

Adapt this to `idea.md`.

---

# 24. FINAL PLANNER CONTRACT

The Planner SHALL:

- compile structured intent into a validated DAG
- use local model proposals only as advisory input
- enforce deterministic graph validation
- enforce acyclicity
- validate agents and tools
- validate workspace/path safety
- calculate dependency readiness
- schedule only dependency-safe work
- respect resource locks
- inject required approval barriers
- maintain strict step lifecycle transitions
- persist graph versions and step state
- support optimistic concurrency
- recover after process crashes
- detect graph oscillation
- bound re-planning
- preserve completed verified outputs
- splice recovery subgraphs safely
- produce auditable graph mutations
- remain locally executable
- remain independently testable

The Planner SHALL NOT:

- execute tools directly
- perform UI automation
- modify files directly
- send email directly
- approve actions
- bypass policy
- trust model-generated permissions
- invent missing tools or agents
- remove approval barriers
- overwrite completed artifacts during re-planning
- execute cyclic graphs
- silently exceed configured graph/retry/re-plan bounds
- silently ignore concurrent state conflicts

---

# 25. OUTPUT QUALITY BAR

The generated `PLANNER.md` must be:

- exhaustive
- production-grade
- implementation-ready
- deterministic at all acceptance boundaries
- concurrency-safe
- recovery-safe
- security-focused
- compatible with SyncNode
- directly usable by another engineer

Do not produce:

- generic workflow tutorials
- generic DAG explanations
- marketing content
- vague architectural recommendations
- pseudo-code presented as production implementation
- undefined classes
- placeholder functions
- `TODO`
- `TBD`
- `pass`
- unexplained magic constants
- cloud-dependent services

Use throughout:

- Pydantic v2 schemas
- Python Protocols
- state machines
- Mermaid diagrams
- DAG equations
- deterministic graph algorithms
- scheduler rules
- resource-lock models
- SQL transaction examples
- failure-state tables
- graph mutation semantics
- recovery procedures
- security invariants
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
PLANNER.md
```
