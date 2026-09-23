# PROMPT: Generate `AGENT_REGISTRY_SPAWNER.md` Technical Specification

You are a **Principal Multi-Agent Systems Engineer and Distributed Runtime Architect** specializing in:

- local-first multi-agent orchestration
- agent registry design
- ephemeral agent lifecycle management
- capability-based scheduling
- least-privilege tool execution
- model/profile binding
- sandboxed execution
- concurrency/resource isolation
- durable agent telemetry
- secure on-premise AI runtimes

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, implementation-ready technical specification** titled:

> `AGENT_REGISTRY_SPAWNER.md`

This document governs the **SyncNode Agent Registry & Dynamic Spawner Subsystem**: the deterministic runtime layer responsible for storing and validating agent definitions, resolving capabilities, filtering tools according to explicit allowlists, resolving local model requirements, spawning ephemeral agent instances for planned graph steps, allocating isolated runtime state, respecting workstation and hardware concurrency constraints, handling lifecycle/cancellation/timeout behavior, and persisting execution telemetry.

The Agent Registry / Spawner must integrate directly with:

- Intent Engine
- Planner / Task Graph Engine
- LangGraph Brain
- Tool Registry
- Context Engine
- Token Management
- Model Gateway
- Computer Runtime
- Browser Runtime
- Document Runtime
- Verification / Recovery
- Policy / Approval
- PostgreSQL / SQLite

The subsystem is a **runtime boundary**, not a generic agent framework.

It MUST NOT:

- execute unauthorized tools
- expose the complete tool registry to an agent
- let the model dynamically expand its permissions
- bind to remote models
- directly approve external/destructive operations
- overwrite canonical system observations
- share untrusted scratchpad state across unrelated agent instances

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architectural source of truth.

Before generating the final specification:

1. Read the complete `idea.md`.
2. Extract:
   - component boundaries
   - agent definitions
   - tool definitions
   - model profile design
   - database schema
   - risk classes
   - concurrency assumptions
   - phase-1 constraints
   - execution lifecycle
   - telemetry requirements
   - recovery behavior
3. Preserve the terminology and architecture from `idea.md`.
4. Do not silently contradict its constraints.
5. Do not introduce cloud services.
6. Do not assume unrestricted shell, unrestricted browser automation, privilege escalation, CAPTCHA bypass, or autonomous external communication.
7. Do not hardcode one model into the agent framework.
8. Where an implementation detail is absent, make a concrete engineering decision and explicitly label it:
   > **Implementation Decision**
9. Clearly distinguish:
   - immutable agent definition
   - spawn request
   - resolved runtime configuration
   - ephemeral agent instance
   - execution state
   - tool authorization
   - model binding
   - persisted telemetry

The generated specification must be directly usable by another engineer to implement the subsystem.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & DESIGN PHILOSOPHY

Define the architecture precisely:

```text
                    LangGraph Brain
                           │
                           ▼
                    Planner / Step
                           │
                           ▼
                ┌───────────────────────┐
                │ Agent Registry       │
                │ + Capability Resolver│
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │ Agent Spawner         │
                │                      │
                │ Definition → Instance │
                └──────────┬────────────┘
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
        Tool Registry  Model Gateway  Context Engine
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                    Agent Runtime
                           │
                           ▼
               Computer / Browser /
               Document / Verifier
```

The Agent Registry SHALL own:

- immutable agent definition catalog access
- agent-version resolution
- capability lookup
- tool-allowlist resolution
- model requirement resolution
- definition validation
- definition cache management

The Spawner SHALL own:

- spawn admission
- runtime configuration assembly
- context binding
- tool-scope construction
- model binding
- scratchpad allocation
- resource acquisition
- lifecycle transitions
- cancellation
- timeout enforcement
- teardown

Neither component may execute an arbitrary tool simply because the model requests it.

---

## 1.1 Core principles

Enforce these invariants:

### Dynamic capability resolution

Agents are selected from declarative definitions.

No planner step may hardcode a model implementation or unrestricted tool set.

### Least privilege

The effective tool surface is:

```text
EffectiveTools
=
DefinitionAllowedTools
∩
RegistryEnabledTools
∩
PolicyPermittedTools
∩
StepRequiredTools
∩
RuntimeAvailableTools
```

If a tool is missing from the intersection, it must not be exposed.

### Immutable definition boundary

An `AgentDefinition` is configuration/catalog state.

An `AgentInstance` is ephemeral runtime state.

Mutating a live instance must not mutate the catalog definition.

### Model agnosticism

The agent declares requirements.

The Model Gateway resolves the concrete local model profile.

### Resource isolation

Desktop control, browser sessions, GPU memory, CPU workers, and other exclusive resources must be explicitly acquired and released.

### Fail closed

Unknown agents, tools, capabilities, model profiles, resource requirements, or permissions must prevent spawning.

---

# 1.2 Required lifecycle diagram

Include a detailed Mermaid and ASCII lifecycle:

```text
Plan Step = READY
      ↓
SpawnRequest
      ↓
Registry Lookup
      ↓
Definition Validation
      ↓
Capability Resolution
      ↓
Tool Allowlist Resolution
      ↓
Policy / Risk Validation
      ↓
Model Profile Resolution
      ↓
Context + Token Budget Binding
      ↓
Resource Acquisition
      ↓
Ephemeral AgentInstance
      ↓
INITIALIZED
      ↓
EXECUTING
      ├──────────────→ WAITING_OBSERVATION
      │                         ↓
      │                     EXECUTING
      │
      ├──────────────→ WAITING_APPROVAL
      │
      ├──────────────→ FAILED
      ├──────────────→ ABORTED
      └──────────────→ TEARDOWN
                               ↓
                        Telemetry Persisted
                               ↓
                           Resources Released
                               ↓
                              DONE
```

Clearly distinguish:

- catalog state
- runtime state
- database state
- model-generated content
- deterministic authorization decisions

---

# 2. AGENT REGISTRY ARCHITECTURE & CATALOG SCHEMA

Define `agent_definitions` as the persistent source for declarative agent configuration.

At minimum align with:

```text
id
key
name
description
version
capabilities
allowed_tools
model_requirements
risk_class
system_prompt
enabled
```

Do not invent incompatible columns if `idea.md` already defines them.

---

## 2.1 Agent definition schema

Provide complete Pydantic v2 models for:

- `AgentDefinitionModel`
- `AgentCapability`
- `ModelRequirements`
- `AgentRiskClass`
- `AgentVersion`
- `AgentDefinitionMetadata`

Include validation for:

- unique key
- valid semantic version
- bounded description length
- capability syntax
- valid tool keys
- supported risk classes
- non-empty system prompt
- bounded prompt size
- maximum tool count
- maximum capability count

A definition with `enabled=False` must not be spawnable.

---

# 2.2 Capability taxonomy

Define a stable capability vocabulary.

Include examples such as:

```text
cap:document:read
cap:document:write
cap:document:verify
cap:filesystem:read
cap:filesystem:write
cap:desktop:uia
cap:desktop:vision
cap:browser:playwright
cap:browser:a11y
cap:reasoning:decompose
cap:reasoning:repair
cap:verification:assert
cap:verification:artifact
cap:workflow:memory
```

Define:

- capability syntax
- wildcard behavior if any
- inheritance
- version compatibility
- required vs optional capability semantics

Do not permit unrestricted wildcard capability grants by default.

---

# 2.3 Registry caching

Define:

- in-memory cache
- immutable snapshots
- versioned keys
- TTL
- invalidation
- thread safety
- async access
- database refresh
- stale-read behavior

Example:

```text
syncnode:agents:{agent_key}:{version}
```

The registry cache must never cache mutable runtime state.

---

# 2.4 Registry update protocol

Agent definitions may change over time.

Define a safe update flow:

```text
DB definition changed
→ validate schema
→ validate tools
→ validate capabilities
→ validate model requirements
→ compute definition hash
→ publish version
→ invalidate old cache where appropriate
→ new spawn requests see new version
→ existing AgentInstances retain old immutable definition snapshot
```

Never mutate a running instance underneath an active task.

---

# 3. SPAWN REQUEST & AGENT MATERIALIZATION

Define an explicit spawn contract.

Required inputs:

```text
run_id
run_step_id
agent_key
agent_version
input_payload
context_snapshot_id
policy_context
model_override_policy
resource_requirements
trace_id
```

---

## 3.1 Spawn algorithm

Provide a complete deterministic sequence:

```text
1. Validate SpawnRequest.
2. Resolve agent definition.
3. Verify definition is enabled.
4. Validate step capability requirements.
5. Resolve effective tool set.
6. Resolve model profile.
7. Validate risk compatibility.
8. Bind context snapshot reference.
9. Request token budget.
10. Acquire runtime resources.
11. Allocate scratchpad.
12. Construct immutable runtime configuration.
13. Create AgentInstance.
14. Persist agent-run start state.
15. Emit `agent.spawned`.
16. Return instance.
```

If any step fails, previously acquired resources must be released in reverse order.

Provide concrete Python implementation with cancellation handling.

---

# 3.2 Agent instance isolation

Define the instance boundary.

Each `AgentInstance` MUST have isolated:

- runtime ID
- definition snapshot
- scoped tools
- model binding
- input payload
- context reference
- scratchpad
- token lease
- resource locks
- cancellation token
- execution clock
- telemetry state

The instance must not reuse mutable state from an unrelated run/step.

---

## 3.3 Scratchpad isolation

Define an in-memory or local ephemeral scratchpad.

Rules:

- scoped to one run step
- bounded size
- never used to persist secrets
- never automatically shared with sibling agents
- destroyed after teardown unless explicitly persisted through an approved artifact/memory channel
- all persisted content passes through the same sanitization/provenance rules as other context

---

# 4. LEAST-PRIVILEGE TOOL SCOPING & CAPABILITY RESOLUTION

This section must be extremely concrete.

Define tool resolution:

```text
RequestedTools
      ↓
AgentDefinition.allowed_tools
      ↓
ToolRegistry lookup
      ↓
Tool enabled?
      ↓
Policy allowed?
      ↓
Agent capability supports tool?
      ↓
Step requires tool?
      ↓
EffectiveToolSet
```

---

## 4.1 Effective tool algorithm

Implement:

```python
effective_tools = (
    agent_allowed
    ∩ registry_enabled
    ∩ policy_permitted
    ∩ capability_compatible
)
```

If a planner step requests a tool outside the set:

```text
TOOL_PERMISSION_VIOLATION
```

must be raised before model invocation.

---

## 4.2 Dynamic model-facing tool schema filtering

The model must receive only:

```text
effective_tools
```

Never inject the whole `tool_definitions` registry.

Provide code for constructing:

```python
list[ToolDefinition]
```

from the effective set.

Ensure:

- deterministic ordering
- schema validation
- no duplicate tools
- no unauthorized optional tool fields
- no hidden tool aliases that bypass permission checks

---

# 4.3 Tool-risk inheritance

Define tool risk levels:

```text
normal
sensitive
external
destructive
admin
```

The effective agent risk must be derived deterministically.

Example:

```text
instance_risk =
max(
    definition_risk,
    max(tool_risk for effective_tools),
    step_risk
)
```

Define the exact ordering.

Never allow the model to lower a risk class.

---

# 5. CORE SPECIALIZED AGENT PERSONAS & BEHAVIORAL DIRECTIVES

Define the foundational SyncNode agents as declarative registry entries, not hard-coded runtime subclasses.

---

## 5.1 Executive Planner Agent

Responsibilities:

- intent decomposition
- graph proposal
- progress interpretation
- bounded re-planning

Restrictions:

- cannot execute high-risk tools
- cannot approve operations
- cannot directly mutate OS state
- cannot send external communications

Provide:

- capability set
- allowed tool keys
- model requirements
- system prompt
- output schema
- risk class

---

## 5.2 Document Specialist Agent

Responsibilities:

- DOCX generation/modification
- XLSX generation/modification
- PPTX generation/modification
- PDF extraction/processing
- artifact structural verification

Allowed tooling should be restricted to document/file operations defined by `idea.md`.

Do not give it unrestricted shell access.

---

## 5.3 Computer Vision & OS Operator Agent

Responsibilities:

- Windows UIA inspection
- semantic interaction
- active-window control
- screenshot fallback
- observation verification

Hard restrictions:

- one physical desktop session at a time
- no credential capture
- no UAC bypass
- no unrestricted keyboard/mouse injection
- no arbitrary privileged system changes

---

## 5.4 Browser Navigator Agent

Responsibilities:

- browser navigation
- accessibility tree inspection
- semantic interaction
- file upload
- form completion

Restrictions:

- controlled browser session
- no CAPTCHA bypass
- no credential harvesting
- page content remains untrusted data
- external communication must remain policy/approval controlled

---

## 5.5 Verifier / Inspector Agent

Responsibilities:

- verify postconditions
- inspect artifact integrity
- inspect UI deltas
- compare expected vs actual state
- produce skeptical structured verification results

The verifier must not silently declare success without evidence.

---

# 5.6 Persona prompt contracts

For every foundational agent define:

```text
Role
Mission
Trusted Inputs
Untrusted Inputs
Allowed Capabilities
Allowed Tools
Forbidden Actions
Risk Rules
Required Output Schema
Verification Expectations
Escalation Rules
```

Provide exact system-prompt text for each persona.

Do not leave persona prompts as vague descriptions.

---

# 6. DYNAMIC MODEL BINDING & REQUIREMENT RESOLUTION

Model requirements must be declarative.

Example:

```text
minimum_context_tokens
requires_tool_calling
requires_vision
requires_structured_output
requires_reasoning
maximum_latency_ms
preferred_quantization
```

---

## 6.1 Model matching algorithm

Define:

```text
eligible_profiles =
profiles satisfying all hard requirements
```

Then rank candidates deterministically using:

```text
capability_fit
→ context_capacity
→ latency suitability
→ hardware suitability
→ availability
→ stable model ID
```

The model ID must be the final tie-breaker.

Do not use random selection.

---

# 6.2 Local model profile integration

Resolve through the Model Gateway's `model_profiles`.

At minimum inspect:

```text
model_id
provider
endpoint_mode
context_window
supports_vision
supports_tool_calls
supports_structured_output
tokenizer_id
resource_requirements
enabled
```

Do not bind to a disabled or stale profile.

---

# 6.3 Air-gap enforcement

Before binding:

```text
profile.provider is approved local provider
AND
endpoint is localhost / on-premise approved endpoint
AND
remote_network_required == false
```

If not:

```text
REMOTE_MODEL_DISALLOWED
```

The spawner must never silently fall back to a cloud model.

---

# 6.4 Model override rules

If a `SpawnRequest` requests a model override:

1. verify override is permitted by policy
2. verify profile exists
3. verify requirements still match
4. verify local-only policy
5. verify token/context compatibility
6. verify risk compatibility

Never allow an agent to request arbitrary model endpoints.

---

# 7. CONCURRENCY CONTROL, HARDWARE ISOLATION & WORKER POOLS

Define explicit resource management.

---

## 7.1 Resource taxonomy

Support:

```text
CPU worker
GPU
VRAM
desktop session
browser session
application lock
filesystem lock
agent slot
```

Define exclusive vs shared resources.

---

# 7.2 Desktop focus mutex

For physical desktop interaction:

```text
desktop:{machine_id}:{session_id}
```

must be an exclusive resource.

Only one Computer Operator instance may control that session at a time.

If unavailable:

```text
RESOURCE_UNAVAILABLE
```

or scheduler-wait state must be returned.

Do not spawn competing UI agents that can fight over focus.

---

# 7.3 Browser session isolation

Define browser ownership:

```text
browser:{browser_profile}:{session_id}
```

Specify:

- exclusive browser profiles where necessary
- session reuse policy
- navigation interference protection
- teardown behavior
- crash recovery

Two agents must not mutate the same browser state concurrently unless the runtime explicitly supports safe partitioning.

---

# 7.4 GPU / CPU throttling

Integrate with Token Management and hardware telemetry.

Spawn admission must account for:

```text
current GPU memory
estimated model memory
reserved token/context cost
CPU availability
max concurrent agents
```

A spawn may be denied or queued when the resource budget cannot safely accommodate it.

---

# 7.5 Worker pool lifecycle

Define:

```text
AVAILABLE
→ RESERVED
→ RUNNING
→ DRAINING
→ RELEASED
```

Workers must support:

- bounded queue
- cancellation
- crash detection
- heartbeat
- timeout
- cleanup

No abandoned agent process may retain a desktop/resource lock indefinitely.

---

# 8. AGENT EXECUTION LIFECYCLE & STATE MACHINE

Define exact states:

```text
SPAWNING
INITIALIZED
EXECUTING
WAITING_OBSERVATION
WAITING_APPROVAL
TEARDOWN
SUCCEEDED
FAILED
ABORTED
```

Provide a complete transition map.

Example:

```text
SPAWNING → INITIALIZED
INITIALIZED → EXECUTING
EXECUTING → WAITING_OBSERVATION
WAITING_OBSERVATION → EXECUTING
EXECUTING → WAITING_APPROVAL
WAITING_APPROVAL → EXECUTING
EXECUTING → SUCCEEDED
EXECUTING → FAILED
EXECUTING → ABORTED
SUCCEEDED → TEARDOWN
FAILED → TEARDOWN
ABORTED → TEARDOWN
```

Reject illegal transitions.

---

# 8.1 Cancellation

Support:

```text
POST /api/v1/runs/{id}/cancel
```

Define propagation:

```text
API cancellation
→ run cancellation signal
→ planner/scheduler
→ agent instance
→ active tool call
→ model stream
→ worker
```

Cancellation must be cooperative.

Hard termination may be used only under a configured safety timeout after cooperative cancellation fails.

---

# 8.2 Timeout hierarchy

Define:

```text
run timeout
  >
step timeout
  >
agent timeout
  >
tool timeout
```

The shortest applicable deadline must win.

Use monotonic clocks for elapsed-time enforcement.

---

# 8.3 Teardown

Teardown must:

1. stop active loops
2. cancel pending callbacks
3. release token lease
4. release resources
5. close browser/application handles where owned
6. destroy scratchpad
7. persist final telemetry
8. emit terminal lifecycle event

Teardown must be idempotent.

---

# 9. TELEMETRY, RUN ACCOUNTING & DATABASE SYNCHRONIZATION

Align with:

```text
agent_definitions
agent_runs
runs
run_steps
```

and the schemas in `idea.md`.

---

## 9.1 `agent_runs`

Record at minimum:

```text
run_step_id
agent_key
model_profile_id
status
prompt_tokens
completion_tokens
total_tokens
latency_ms
input_context_hash
structured_output
```

Also define:

- agent instance ID
- agent definition version
- resource wait duration
- spawn latency
- model binding decision
- tool count
- compaction level
- token lease ID
- trace ID
- start/end timestamps
- terminal error code

---

# 9.2 Atomic telemetry lifecycle

Define:

```text
spawn requested
→ agent_runs row created
→ state updates
→ usage reconciliation
→ terminal status
→ final telemetry commit
```

Avoid partially persisted terminal states.

Use transaction boundaries appropriate to PostgreSQL production and SQLite development.

---

# 9.3 Structured events

Define event models for:

```text
agent.spawn_requested
agent.definition_resolved
agent.tool_scoped
agent.model_bound
agent.resource_waiting
agent.spawned
agent.execution_started
agent.observation_waiting
agent.approval_waiting
agent.execution_completed
agent.execution_failed
agent.cancelled
agent.teardown_started
agent.teardown_completed
agent.faulted
```

Each event must contain:

- event ID
- timestamp
- run ID
- step ID
- agent instance ID
- agent key
- definition version
- trace ID
- reason / metadata

Never log secrets or unrestricted prompt payloads.

---

# 10. CONCRETE DATA CONTRACTS & INTERFACE DEFINITIONS

Provide complete Pydantic v2 models and typed Protocols.

---

## 10.1 `AgentDefinitionModel`

Include the database-compatible catalog fields:

```python
class AgentDefinitionModel(BaseModel):
    id: UUID
    key: str
    name: str
    description: str
    version: str
    capabilities: list[str]
    allowed_tools: list[str]
    model_requirements: ModelRequirements
    risk_class: AgentRiskClass
    system_prompt: str
    enabled: bool
```

Add validators and immutable/frozen behavior where appropriate.

---

## 10.2 `SpawnRequest`

Include:

```python
class SpawnRequest(BaseModel):
    run_id: UUID
    run_step_id: UUID
    agent_key: str
    agent_version: str | None
    input_payload: dict[str, Any]
    context_snapshot_id: UUID
    policy_context: PolicyContext
    resource_requirements: ResourceRequirements
    model_override: str | None
    trace_id: str
```

Apply strict bounds and validation.

---

## 10.3 `AgentInstance`

Include:

- instance ID
- definition snapshot
- effective tools
- model profile
- context reference
- scratchpad reference
- token lease
- acquired resources
- lifecycle state
- created time
- timeout/deadline
- cancellation handle

The mutable lifecycle fields must be separate from the immutable definition.

---

## 10.4 `AgentRegistryProtocol`

Define:

```python
class AgentRegistryProtocol(Protocol):
    async def register(
        self,
        definition: AgentDefinitionModel,
    ) -> AgentDefinitionModel:
        ...

    async def get(
        self,
        agent_key: str,
        version: str | None = None,
    ) -> AgentDefinitionModel | None:
        ...

    async def list_by_capability(
        self,
        capability: str,
    ) -> list[AgentDefinitionModel]:
        ...

    async def validate_tools(
        self,
        definition: AgentDefinitionModel,
    ) -> ToolValidationResult:
        ...
```

Add methods where needed for cache refresh, version lookup, and immutable snapshot access.

---

## 10.5 `AgentSpawnerProtocol`

Define:

```python
class AgentSpawnerProtocol(Protocol):
    async def spawn(
        self,
        request: SpawnRequest,
        cancellation: CancellationToken,
    ) -> AgentInstance:
        ...

    async def teardown(
        self,
        instance_id: UUID,
        reason: str,
    ) -> None:
        ...

    async def cancel(
        self,
        instance_id: UUID,
        reason: str,
    ) -> None:
        ...
```

---

## 10.6 `AgentRunRecord`

Define all fields required for `agent_runs` persistence and exact token accounting.

---

# 11. REQUIRED SUPPORTING SCHEMAS

Also define complete models for:

- `ModelRequirements`
- `AgentCapability`
- `AgentRiskClass`
- `ToolScope`
- `EffectiveToolSet`
- `ToolValidationResult`
- `PolicyContext`
- `ResourceRequirements`
- `ResourceLock`
- `ResourceLease`
- `ModelBinding`
- `AgentRuntimeConfig`
- `ScratchpadMetadata`
- `CancellationToken`
- `AgentLifecycleState`
- `AgentLifecycleEvent`
- `AgentRunRecord`
- `SpawnMetrics`
- `AgentExecutionResult`
- `AgentError`

No undefined types may appear in implementation examples.

---

# 12. MODEL / TOKEN / CONTEXT INTEGRATION

The spawner must integrate with the Token Management and Context Engine boundaries.

Expected sequence:

```text
SpawnRequest
   ↓
Agent Definition
   ↓
Context Snapshot
   ↓
Token Budget Calculation
   ↓
Effective Tool Schemas
   ↓
Model Profile
   ↓
Final Runtime Prompt
   ↓
Token Lease
   ↓
Model Gateway
```

The Agent Spawner must never independently invent context capacity.

It consumes the authoritative Token Manager result.

The agent instance must retain:

- input context hash
- token lease ID
- model profile ID
- prompt schema version

for telemetry.

---

# 13. SECURITY MODEL

Explicitly address:

- unauthorized tool injection
- agent-definition tampering
- stale definition execution
- remote model fallback
- cross-run scratchpad leakage
- cross-user resource sharing
- desktop control collision
- browser session collision
- path traversal
- secret exposure through prompts
- model-generated permission escalation
- tool alias bypass
- definition downgrade attacks
- resource exhaustion
- orphaned resource locks
- token-quota bypass

Required guarantees:

1. Effective tools are always allowlist-derived.
2. A model cannot add tools.
3. A model cannot change the agent's risk class.
4. A model cannot change the model endpoint.
5. Definition versions are immutable for active instances.
6. Remote models are blocked.
7. Resource ownership is explicit.
8. Scratchpads are isolated.
9. Cross-user instances cannot share exclusive desktop/session resources.
10. Teardown always releases acquired resources.
11. Unknown registry entries fail closed.
12. Tool permission violations block model invocation.
13. All security-sensitive decisions are auditable.

---

# 14. FAILURE MODES & ERROR TAXONOMY

Define a structured catalog including:

```text
AGENT_NOT_FOUND
AGENT_DISABLED
AGENT_DEFINITION_INVALID
AGENT_VERSION_NOT_FOUND
CAPABILITY_NOT_SUPPORTED
TOOL_NOT_FOUND
TOOL_PERMISSION_VIOLATION
TOOL_SCHEMA_INVALID
MODEL_PROFILE_NOT_FOUND
MODEL_PROFILE_DISABLED
MODEL_REQUIREMENTS_UNSATISFIED
REMOTE_MODEL_DISALLOWED
TOKEN_BUDGET_UNAVAILABLE
RESOURCE_UNAVAILABLE
DESKTOP_SESSION_BUSY
BROWSER_SESSION_BUSY
SPAWN_TIMEOUT
AGENT_TIMEOUT
TOOL_TIMEOUT
CANCELLED
DEFINITION_VERSION_CONFLICT
CONCURRENT_STATE_CONFLICT
SCRATCHPAD_LIMIT_EXCEEDED
AGENT_EXECUTION_FAILED
TEARDOWN_FAILED
```

Every error must include:

- stable error code
- retryability
- severity
- run ID
- step ID
- instance ID where available
- trace ID
- sanitized reason
- recovery recommendation

No secret values in errors.

---

# 15. OBSERVABILITY & AUDIT

Define metrics:

```text
agent_spawn_latency_ms
agent_definition_lookup_latency_ms
tool_scope_count
unauthorized_tool_rejections
model_binding_latency_ms
resource_wait_ms
active_agent_instances
desktop_lock_waits
browser_lock_waits
spawn_failures
agent_timeouts
agent_cancellations
teardown_failures
```

Dimensions:

- agent key
- definition version
- model profile
- run
- step
- worker
- lifecycle state
- risk class

Use hashes/references for sensitive data.

---

# 16. PERFORMANCE & CONCURRENCY TARGETS

Define measurable engineering targets such as:

- registry lookup latency
- cached-definition lookup latency
- spawn preparation latency
- tool-scope construction latency
- model binding latency
- resource-acquisition latency
- teardown latency

Give deterministic concurrency controls:

```text
max_total_agents
max_agents_per_run
max_agents_per_user
max_computer_agents_per_desktop
max_browser_agents_per_session
max_gpu_agents
```

All limits must be configurable through typed settings.

---

# 17. REFERENCE PACKAGE STRUCTURE

Provide a concrete package tree:

```text
syncnode/
└── agent_runtime/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── registry.py
    ├── definitions.py
    ├── capabilities.py
    ├── tool_scope.py
    ├── model_binding.py
    ├── resources.py
    ├── spawner.py
    ├── lifecycle.py
    ├── scratchpad.py
    ├── cancellation.py
    ├── timeouts.py
    ├── persistence.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_registry.py
        ├── test_definitions.py
        ├── test_capabilities.py
        ├── test_tool_scope.py
        ├── test_model_binding.py
        ├── test_resources.py
        ├── test_spawner.py
        ├── test_lifecycle.py
        ├── test_cancellation.py
        ├── test_persistence.py
        ├── test_security.py
        └── test_determinism.py
```

Adapt it to the exact `idea.md` architecture.

---

# 18. COMPLETE IMPLEMENTATION EXAMPLES

The generated `AGENT_REGISTRY_SPAWNER.md` MUST contain real Python 3.12+ implementations for at least:

1. agent-definition validation
2. immutable definition snapshotting
3. registry lookup
4. registry capability lookup
5. version resolution
6. capability matching
7. effective tool-set calculation
8. unauthorized-tool rejection
9. deterministic tool-schema filtering
10. risk inheritance
11. model requirement matching
12. local-only model enforcement
13. resource-lock acquisition
14. desktop focus mutex
15. browser session locking
16. spawn orchestration
17. lifecycle state transitions
18. cooperative cancellation
19. timeout enforcement
20. scratchpad isolation
21. teardown ordering
22. agent-run persistence
23. telemetry event emission
24. complete `AgentRegistryProtocol`
25. complete `AgentSpawnerProtocol`

Code requirements:

- Python 3.12+
- Pydantic v2-compatible
- fully type annotated
- async-compatible where needed
- syntactically complete
- executable
- no `TODO`
- no `TBD`
- no `pass`
- no undefined types
- no placeholder implementations
- no unexplained magic constants

Where storage/locks are abstracted, define complete Protocol interfaces and include a concrete PostgreSQL/SQLite-compatible reference or SQL transaction example where appropriate.

---

# 19. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- registry tests
- schema tests
- capability tests
- tool-permission tests
- model-binding tests
- resource-lock tests
- concurrency tests
- lifecycle tests
- cancellation tests
- persistence tests
- crash-recovery tests
- security tests
- deterministic replay tests
- integration tests

Mandatory security tests:

### Tool isolation

An agent cannot see or invoke a tool outside its effective allowlist.

### Model isolation

An agent cannot bind to an unknown or remote model.

### Definition immutability

Updating the registry does not mutate an already-running AgentInstance.

### Desktop isolation

Two Computer Agents cannot acquire the same desktop lock simultaneously.

### Browser isolation

Two incompatible agents cannot control the same browser session concurrently.

### Cancellation

Cancellation propagates to active execution and resources are eventually released.

### Teardown

Every acquired resource has exactly one release path.

### Determinism

Identical:

- definition version
- step
- policy
- tool registry
- model profiles
- resource state

must produce identical:

- effective tool set
- model binding
- risk inheritance
- spawn decision
- runtime configuration

---

# 20. DATABASE INTEROPERABILITY

Define exact synchronization semantics for:

## `agent_definitions`

Catalog source for:

- agent identity
- versions
- capabilities
- tool allowlists
- model requirements
- risk
- system prompt
- enabled state

## `agent_runs`

Runtime accounting for:

- run step
- agent key
- model profile
- status
- usage
- latency
- input context hash
- structured output
- runtime identifiers

Define foreign-key and indexing expectations based on `idea.md`.

If additional columns are required but not present in `idea.md`, introduce them under:

> Implementation Decision — Agent Runtime Persistence Extensions

Do not silently modify the source architecture.

---

# 21. REFERENCE END-TO-END EXECUTION

Use the workflow:

> “Write a story about a tree and send it to Rahul.”

Show the complete lifecycle:

```text
Planner
  ↓
READY step for Document Agent
  ↓
Registry resolves Document Agent
  ↓
Allowed document tools loaded
  ↓
Model requirement matched locally
  ↓
Context + token budget bound
  ↓
Agent spawned
  ↓
DOCX artifact created
  ↓
Verifier observes success
  ↓
Agent teardown
  ↓
Browser step READY
  ↓
Browser Agent spawned
  ↓
Playwright tools scoped
  ↓
Draft created + attachment verified
  ↓
WAITING_APPROVAL
  ↓
Approval granted
  ↓
Send step executes
  ↓
Post-send verification
  ↓
Agent teardown
  ↓
Telemetry persisted
```

Clearly label which component owns:

- planning
- spawning
- tool authorization
- model binding
- execution
- approval
- verification
- telemetry

The Agent Spawner itself must not send the email simply because it created the Browser Agent.

---

# 22. INTEGRATION CONTRACTS WITH OTHER SUBSYSTEMS

Define precise boundaries.

### Planner

Provides:

```text
run_step
agent_key
required capabilities
required tools
risk
resource requirements
```

### Context Engine

Provides:

```text
ContextSnapshot
snapshot hash
trusted observations
sanitized context
```

### Token Management

Provides:

```text
TokenBudget
TokenLease
reservation
usage reconciliation
```

### Tool Registry

Provides:

```text
ToolDefinition
tool capability
tool risk
enabled state
```

### Model Gateway

Provides:

```text
ModelProfile
model adapter
local endpoint
structured output capabilities
```

### Policy / Approval

Provides:

```text
policy permissions
risk constraints
approval state
```

### Verification / Recovery

Consumes:

```text
AgentExecutionResult
observations
verification assertions
failure context
```

---

# 23. SECURITY & TRUST BOUNDARY DIAGRAM

Include a dedicated security diagram showing:

```text
UNTRUSTED:
  model output
  retrieved content
  browser text
  user-provided paths
          │
          ▼
DETERMINISTIC VALIDATION
          │
          ├── schema validation
          ├── capability validation
          ├── tool allowlist
          ├── model profile validation
          ├── policy validation
          └── resource validation
          │
          ▼
TRUSTED RUNTIME CONFIG
          │
          ▼
EPHEMERAL AGENT INSTANCE
```

Make clear that the Agent Instance cannot elevate its own privileges.

---

# 24. FINAL ENGINE CONTRACT

The Agent Registry & Spawner SHALL:

- maintain versioned declarative agent definitions
- resolve capabilities deterministically
- validate enabled/disabled state
- resolve effective tool permissions
- expose only allowlisted tool schemas
- derive risk from trusted configuration
- resolve model profiles dynamically
- reject remote/unapproved models
- bind local context snapshots
- consume authoritative token budgets
- acquire resource locks
- isolate desktop/browser sessions
- create ephemeral agent instances
- enforce lifecycle transitions
- support cooperative cancellation
- enforce timeouts
- persist agent run telemetry
- release all resources during teardown
- remain local-first
- remain independently testable
- maintain auditable provenance

The subsystem SHALL NOT:

- expose the entire tool registry
- permit model-driven permission escalation
- permit remote model fallback
- execute arbitrary tools outside effective scope
- directly approve risky actions
- mutate immutable agent definitions in place
- share scratchpads across unrelated instances
- allow desktop-control collisions
- silently ignore resource exhaustion
- silently skip telemetry
- leak secrets through logs
- bypass policy

---

# 25. OUTPUT QUALITY BAR

The generated `AGENT_REGISTRY_SPAWNER.md` must be:

- exhaustive
- production-grade
- implementation-ready
- deterministic
- security-focused
- concurrency-safe
- model-agnostic
- resource-aware
- database-aligned
- directly usable by another engineer

Do not produce:

- generic multi-agent tutorials
- generic agent-framework comparisons
- marketing language
- vague recommendations
- pseudo-code presented as implementation
- undefined classes
- placeholder methods
- `TODO`
- `TBD`
- `pass`
- unexplained constants
- cloud-dependent runtime assumptions

Use throughout:

- Pydantic v2 schemas
- Python Protocols
- state machines
- Mermaid diagrams
- lifecycle tables
- capability matrices
- tool-permission equations
- model-matching algorithms
- resource-lock semantics
- SQL transaction examples
- telemetry schemas
- failure taxonomies
- security invariants
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
AGENT_REGISTRY_SPAWNER.md
```
