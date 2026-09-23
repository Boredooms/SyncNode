# PROMPT: Generate `TOOL_REGISTRY.md` Technical Specification

You are a **Principal Systems Software Engineer and Windows Automation Runtime Architect** specializing in:

- deterministic tool execution
- typed tool registries
- JSON Schema / Pydantic validation
- least-privilege authorization
- idempotent side-effect execution
- Windows UI Automation
- Win32 process/window APIs
- safe keyboard/mouse simulation
- clipboard management
- sandboxed local execution
- approval-aware agent runtimes
- audit-grade telemetry
- local-first / air-gapped AI infrastructure

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, production-grade, implementation-ready technical specification** titled:

> `TOOL_REGISTRY.md`

This document governs the **SyncNode Tool Registry & Execution Subsystem**: the deterministic runtime boundary responsible for cataloging tools, validating model-generated tool calls, resolving agent-specific permissions, enforcing risk and approval policy, acquiring required resources, executing typed deterministic tools, producing structured observations/results, enforcing idempotency, handling timeouts and recovery, and persisting tool-call telemetry.

The system gives local models the ability to propose tool calls, but:

> **Model tool calls are untrusted proposals. Deterministic SyncNode infrastructure is authoritative for schema validation, identity, permissions, risk, policy, resource acquisition, execution, observation, idempotency, and audit.**

The Tool Registry integrates with:

- Agent Registry / Spawner
- Planner
- Context Engine
- Token Management
- Model Gateway
- Policy / Approval
- Computer Runtime
- Browser Runtime
- Document Runtime
- Verification / Recovery
- PostgreSQL / SQLite
- `tool_definitions`
- `tool_calls`
- `audit_events`

Do not turn the document into a generic plugin framework. Design the actual SyncNode runtime subsystem.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architecture source of truth.

Before writing the specification:

1. Read the complete `idea.md`.
2. Extract:
   - tool registry boundaries
   - agent permissions
   - risk classes
   - approval requirements
   - Windows automation requirements
   - database schemas
   - execution lifecycle
   - concurrency constraints
   - idempotency rules
   - audit requirements
   - phase-1 security restrictions
3. Preserve SyncNode terminology wherever possible.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud execution.
6. Do not introduce unrestricted shell execution.
7. Do not introduce arbitrary PowerShell/CMD execution as a generic tool.
8. Do not allow models to manufacture tools or permissions.
9. Where implementation details are unspecified, make a concrete engineering choice and mark it:
   > **Implementation Decision**
10. Clearly distinguish:
   - tool definition/catalog state
   - model tool proposal
   - deterministic validation
   - authorization decision
   - approval state
   - runtime tool execution
   - observations
   - persisted result
   - audit event

The generated document must be directly implementable by another engineer.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & TOOL ARCHITECTURE

Position the subsystem precisely:

```text
                 Local Model / Agent
                         │
                         │ proposed tool call
                         ▼
                ┌────────────────────┐
                │   TOOL REGISTRY    │
                │                    │
                │ Lookup             │
                │ Schema Validation  │
                │ Permission Check   │
                │ Risk Evaluation    │
                │ Approval Interlock │
                │ Idempotency         │
                │ Resource Locks      │
                └─────────┬──────────┘
                          │
                          ▼
                  Deterministic Tool
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      Computer Runtime  Browser      Documents
      / Win32 / UIA     Runtime      / Files
                          │
                          ▼
                    Observation
                          │
                          ▼
                 ToolCallResult
                          │
                          ▼
                 Persistence/Audit
```

The Tool Registry SHALL own:

- immutable tool catalog access
- version resolution
- capability lookup
- tool schema validation
- agent scope filtering
- risk verification
- approval gating
- idempotency checks
- resource-lock coordination
- execution wrapper
- result normalization
- timeout handling
- telemetry persistence hooks

It SHALL NOT own:

- task planning
- model routing
- agent spawning
- human approval decisions themselves
- arbitrary execution outside registered tools
- direct policy mutation
- unrestricted system administration

---

# 1.1 Core invariants

### Model proposes; deterministic tools dispose

Model-generated calls are never trusted directly.

Required pipeline:

```text
model proposal
→ tool lookup
→ version validation
→ strict argument validation
→ canonicalization
→ authorization
→ risk classification
→ approval interlock
→ resource admission
→ idempotency check
→ execution
→ observation
→ result persistence
```

### Least privilege

An agent receives only tools allowed by:

```text
EffectiveTools =
AgentAllowedTools
∩
EnabledRegistryTools
∩
PolicyAllowedTools
∩
RuntimeAvailableTools
∩
StepRequiredTools
```

### Tool identity

A tool key and version must resolve to an immutable definition snapshot.

A model cannot substitute an arbitrary implementation path.

### Deterministic observations

State-changing tools must produce structured post-execution evidence where possible.

### Idempotency

Every side-effecting tool call must have an idempotency key.

### Fail closed

Unknown tools, invalid schemas, unauthorized calls, policy violations, and unsupported operations must not execute.

---

# 1.2 Required execution lifecycle diagram

Include a detailed Mermaid and ASCII diagram:

```text
Agent Tool Proposal
        ↓
Normalize Request
        ↓
Tool Registry Lookup
        ↓
Version / Enabled Check
        ↓
Strict Pydantic / JSON Schema Validation
        ↓
Canonical Argument Normalization
        ↓
Agent Permission Check
        ↓
Risk Classification
        ↓
Policy Evaluation
        ↓
[Approval Required?]
      /          \
    YES           NO
     ↓             ↓
WAITING_APPROVAL   │
     ↓             │
Approval Granted   │
     └──────┬──────┘
            ▼
Idempotency Lookup
            ↓
[Existing Completed Call?]
        /             \
      YES              NO
       ↓                ↓
Return Cached Result   Acquire Resources
                         ↓
                  Execute Deterministic Tool
                         ↓
                     Capture Observation
                         ↓
                    Verify Result
                         ↓
                  Persist Tool Call
                         ↓
                    Emit Audit Event
                         ↓
                     Return Result
```

---

# 2. TOOL CATALOG ARCHITECTURE & DATABASE INTEROPERABILITY

Align directly with:

```text
tool_definitions
```

Required catalog fields from the source architecture include:

```text
id
key
name
version
input_schema
output_schema
capabilities
risk_class
requires_approval
enabled
```

Do not silently invent incompatible fields.

---

# 2.1 `ToolDefinitionModel`

Provide a complete Pydantic v2 model.

Include:

```python
class ToolDefinitionModel(BaseModel):
    id: UUID
    key: str
    name: str
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    capabilities: list[str]
    risk_class: RiskClass
    requires_approval: bool
    enabled: bool
```

Add:

- semantic-version validation
- schema validation
- bounded capability/tool-name lengths
- maximum schema size
- immutable/frozen catalog representation
- definition hash

---

# 2.2 Tool versioning

Define immutable versions:

```text
tool_key + version
```

A running call must retain the exact definition version used at validation time.

Updating the catalog must not mutate active executions.

Example:

```text
file.write@1.2.0
```

and:

```text
file.write@1.3.0
```

are distinct immutable definitions.

---

# 2.3 Registry cache

Define:

```text
syncnode:tools:{tool_key}:{version}
```

with:

- TTL
- version hash
- invalidation
- enable/disable refresh
- thread-safe reads
- atomic catalog updates
- stale-cache policy

Never cache active call state inside the catalog cache.

---

# 2.4 Dynamic registration

Define:

```text
register
→ validate definition
→ validate schemas
→ validate capabilities
→ validate implementation binding
→ compute definition hash
→ persist
→ publish
→ invalidate affected caches
```

Reject duplicate `(key, version)` definitions unless they are byte-for-byte equivalent.

---

# 3. STANDARDIZED TOOL CONTRACT & EXECUTION ENVELOPE

Define a universal tool interface.

Every tool MUST expose:

```text
identity
risk
capabilities
input schema
output schema
preconditions
execute
postconditions
cleanup
```

Provide a concrete interface such as:

```python
class BaseTool(Protocol):
    key: str
    version: str
    risk_class: RiskClass

    async def validate_preconditions(
        self,
        request: "ToolExecutionContext",
        cancellation: "CancellationToken",
    ) -> "PreconditionResult":
        ...

    async def execute(
        self,
        request: "ToolExecutionContext",
        cancellation: "CancellationToken",
    ) -> "ToolCallResult":
        ...

    async def cleanup(
        self,
        request: "ToolExecutionContext",
    ) -> None:
        ...
```

Do not allow arbitrary untyped callable invocation.

---

# 3.1 Universal result envelope

Define:

```python
class ToolCallResult(BaseModel):
    success: bool
    status: ToolCallStatus
    data: dict[str, Any]
    error: ToolErrorPayload | None
    observation_id: UUID | None
    execution_time_ms: int
    idempotency_key: str
    tool_key: str
    tool_version: str
    trace_id: str
```

Validate:

- success/error consistency
- non-negative duration
- required identifiers
- bounded output size

---

# 3.2 Tool call request

Define:

```python
class ToolCallRequest(BaseModel):
    request_id: UUID
    run_id: UUID
    run_step_id: UUID
    agent_run_id: UUID
    agent_key: str
    tool_key: str
    tool_version: str | None
    arguments: dict[str, Any]
    idempotency_key: str | None
    trace_id: str
```

Add strict validation.

The model-provided `idempotency_key`, if present, must be treated as a hint and validated/re-derived deterministically.

---

# 4. WINDOWS AUTOMATION TOOL SUITE

This section MUST provide a deep, implementation-ready Windows tool surface.

Windows tools must integrate with `COMPUTER_RUNTIME.md` rather than duplicating unsafe low-level logic.

Required categories:

```text
Process / Window
UI Automation
Keyboard / Mouse
Clipboard
Observation
Verification
```

---

# 4.1 Process & lifecycle tools

Implement specifications for:

### `windows.launch_application`

Input:

```text
approved_application_key
arguments
working_directory
expected_window
timeout
```

Behavior:

```text
validate application identity
→ validate working directory
→ launch non-elevated
→ track PID
→ locate window
→ stabilize focus if requested
→ return ProcessContext
```

### `windows.find_window`

Support:

- PID
- title
- class name
- visibility
- process identity

### `windows.close_window`

Use:

```text
WM_CLOSE
→ wait
→ observe
→ force termination only if policy explicitly permits
```

Never terminate unrelated processes.

---

# 4.2 UIA semantic tools

Define:

### `uia.find_element`

Support:

```text
AutomationId
Name
ClassName
ControlType
ancestor constraints
enabled state
visibility
```

Use UIA accessibility state.

### `uia.invoke_control`

Use:

```text
IUIAutomationInvokePattern
```

### `uia.set_value`

Use:

```text
IUIAutomationValuePattern
```

### `uia.select_item`

Use:

```text
IUIAutomationSelectionItemPattern
```

### `uia.get_tree_snapshot`

Return a compact, token-efficient accessibility representation.

The output must exclude unnecessary layout containers while retaining interaction-critical fields.

---

# 4.3 Input fallback tools

Define:

### `input.click_coordinate`

Requirements:

- fresh target observation
- current foreground verification
- DPI-aware coordinate conversion
- coordinate bounds checking
- desktop mutex
- user-interference check

### `input.type_keystrokes`

Requirements:

- modifier tracking
- Unicode support
- key-down/up symmetry
- cancellation
- focus verification

### `input.clipboard_paste`

Requirements:

- clipboard snapshot metadata
- bounded write
- target focus validation
- Ctrl+V
- result re-observation
- clipboard restoration

Raw coordinates and direct input remain fallback mechanisms.

---

# 4.4 Observation tools

Define:

### `screen.capture_window`

Support:

- approved window target
- bounded resolution
- image size limits
- SHA-256 digest
- local-only storage
- observation reference

### `screen.assert_element_visible`

Support:

- semantic locator
- fresh UIA lookup
- bounding rectangle stability
- enabled/visible checks
- structured assertion result

Do not use vision output as authoritative state without runtime verification.

---

# 5. PARAMETER VALIDATION & SANITIZATION

This section must be extremely concrete.

Pipeline:

```text
Raw Model Arguments
→ JSON Decode
→ Schema Validation
→ Type Validation
→ Length / Range Validation
→ Canonicalization
→ Security Sanitization
→ Policy Check
→ Execution Context
```

---

# 5.1 Strict schema behavior

Use Pydantic v2 / JSON Schema.

Recommended:

```text
extra = "forbid"
strict types
bounded strings
bounded arrays
bounded objects
enum enforcement
```

Reject:

- unknown arguments
- wrong primitive types
- oversized strings
- oversized arrays
- nested object explosions
- invalid Unicode/control sequences where dangerous

---

# 5.2 Filesystem path guardrails

Every file path argument must pass through:

```text
canonicalize
→ resolve
→ allowed-root check
→ symlink/reparse-point policy
→ operation-specific permission
```

Provide complete reference code.

Reject:

```text
../
..\ 
UNC escape
alternate stream tricks
unsupported device paths
```

where prohibited by policy.

---

# 5.3 Command/script injection

There must be no generic shell execution tool in the default phase-1 surface.

If a narrowly scoped command adapter is needed, require:

- fixed executable identity
- fixed argument schema
- no shell interpretation
- allowlisted arguments
- explicit policy

Reject model-generated PowerShell/CMD scripts by default.

Do not rely only on regular expressions for command safety.

---

# 5.4 Resource/size limits

Define bounds for:

- argument bytes
- file sizes
- screenshots
- clipboard payloads
- UI tree nodes
- browser payloads
- output bytes
- execution duration

All limits must be configurable through typed settings.

---

# 6. AUTHORIZATION, POLICY & APPROVAL INTERLOCKS

Define the risk classes:

```text
READ
WRITE_LOCAL
DESTRUCTIVE_LOCAL
EXTERNAL_COMMUNICATION
SYSTEM_ADMIN
```

---

# 6.1 Risk enforcement

The catalog declares a baseline risk.

The runtime must recompute effective risk from:

```text
ToolDefinition.risk_class
+
Step risk
+
Argument-specific risk
+
Resource target
```

Risk cannot be lowered by the model.

---

# 6.2 Default risk policy

Document the source-architecture policy:

```text
READ
→ automatic when authorized

WRITE_LOCAL
→ allowed only within workspace/policy

DESTRUCTIVE_LOCAL
→ approval required

EXTERNAL_COMMUNICATION
→ approval required

SYSTEM_ADMIN
→ denied fail-closed
```

Where `idea.md` specifies a different policy, preserve it.

---

# 6.3 Approval flow

For approval-required calls:

```text
tool request
→ validate
→ snapshot sanitized arguments
→ create approval record
→ status = WAITING_APPROVAL
→ pause execution
→ human decision
→ revalidate current state
→ execute only if approved
```

Approval must be bound to:

- run
- step
- agent
- tool
- tool version
- sanitized argument hash
- policy version

If the proposed arguments change after approval:

```text
approval invalidated
→ new approval required
```

Do not reuse an approval for modified arguments.

---

# 6.4 Approval table interoperability

Define exact interactions with:

```text
approvals
```

without duplicating its ownership.

The Tool Registry creates/consumes approval requests but does not act as the human approval authority.

---

# 7. CONCURRENCY, DESKTOP MUTEX & IDEMPOTENCY

---

# 7.1 Desktop focus mutex

All physical Windows automation tools must acquire:

```text
syncnode_desktop_control_mutex
```

or equivalent scoped resource.

Examples:

```text
uia.invoke_control
input.click_coordinate
input.type_keystrokes
input.clipboard_paste
```

Observation-only tools may use shared access if safe.

Define:

- owner
- lease
- timeout
- fencing
- crash recovery
- release semantics

---

# 7.2 Idempotency key derivation

Define:

```text
idempotency_key =
SHA256(
    canonical_json(
        run_id,
        run_step_id,
        agent_run_id,
        tool_key,
        tool_version,
        normalized_arguments
    )
)
```

Provide exact canonicalization rules.

Do not include secrets in the persisted canonical arguments where possible; hash sensitive fields separately or represent them using stable redaction tokens.

---

# 7.3 `tool_calls` deduplication

Before executing a mutating call:

```text
SELECT existing tool_call
WHERE idempotency_key = ?
```

If:

```text
status = succeeded
```

return the stored result.

If:

```text
status = running
```

attach/reconcile rather than launching a duplicate side effect.

If:

```text
status = failed
```

allow retry only according to tool retry policy.

---

# 7.4 Idempotency race prevention

Two workers may attempt the same call concurrently.

Define a database uniqueness constraint on:

```text
idempotency_key
```

and an atomic insert/acquisition pattern.

Do not rely on application-level check-then-insert.

---

# 8. EXECUTION ENGINE & TIMEOUT MANAGEMENT

Define a controlled execution wrapper.

---

# 8.1 Execution state

Use:

```text
REQUESTED
VALIDATING
WAITING_APPROVAL
WAITING_RESOURCE
EXECUTING
OBSERVING
COMPLETED
FAILED
CANCELLED
TIMED_OUT
```

Define legal transitions.

---

# 8.2 Timeout hierarchy

Support:

```text
run timeout
>
step timeout
>
tool timeout
>
provider/API timeout
```

The earliest deadline wins.

Use monotonic timing where possible.

---

# 8.3 Soft timeout

At soft timeout:

```text
emit warning
→ issue cancellation
→ allow cooperative cleanup
```

---

# 8.4 Hard timeout

Hard timeout behavior must be platform/tool-specific.

Do not attempt unsafe Python thread termination.

For process-backed tools:

```text
request termination
→ wait
→ terminate process only if policy permits
```

For in-process async tools:

```text
cancel task
→ await bounded cleanup
→ mark timed out if still unresolved
```

Explain why forcibly killing arbitrary Python threads is unsafe.

---

# 8.5 Cleanup ordering

On all terminal paths:

```text
stop input
→ restore temporary state
→ release clipboard
→ close owned handles
→ release resource lock
→ finalize observation
→ persist result
→ emit audit
```

Cleanup must be idempotent.

---

# 9. FAILURE TAXONOMY & BOUNDED RECOVERY

Define structured errors including:

```text
TOOL_NOT_FOUND
TOOL_VERSION_NOT_FOUND
TOOL_DISABLED
INVALID_ARGUMENTS
SCHEMA_VALIDATION_FAILED
TOOL_PERMISSION_VIOLATION
RISK_POLICY_VIOLATION
APPROVAL_REQUIRED
APPROVAL_REJECTED
IDEMPOTENCY_CONFLICT
DESKTOP_MUTEX_TIMEOUT
RESOURCE_UNAVAILABLE
ELEMENT_NOT_FOUND
ELEMENT_AMBIGUOUS
PATTERN_UNSUPPORTED
STALE_UI_REFERENCE
PROCESS_LAUNCH_FAILED
WINDOW_NOT_FOUND
CLIPBOARD_BUSY
SEC_UAC_RESTRICTED
USER_INTERRUPT_DETECTED
TOOL_TIMEOUT
TOOL_EXECUTION_FAILED
OUTPUT_SCHEMA_INVALID
OBSERVATION_CAPTURE_FAILED
```

Each error must contain:

- stable code
- severity
- retryability
- run ID
- step ID
- agent run ID
- tool key/version
- trace ID
- sanitized reason
- recovery recommendation

---

# 9.1 Recovery policy

Define bounded recovery by error class.

Examples:

```text
ELEMENT_NOT_FOUND
→ refresh observation
→ retry locator once
→ fail/re-plan

STALE_UI_REFERENCE
→ re-query UIA
→ retry once

DESKTOP_MUTEX_TIMEOUT
→ wait according to bounded scheduler policy

CLIPBOARD_BUSY
→ bounded exponential backoff

APPROVAL_REJECTED
→ never auto-retry the same side effect

TOOL_PERMISSION_VIOLATION
→ fail immediately

SEC_UAC_RESTRICTED
→ fail closed
```

Do not retry side effects indiscriminately.

---

# 10. COMPLETE DATA CONTRACTS & INTERFACE DEFINITIONS

Provide complete Pydantic v2 schemas.

Required:

- `ToolDefinitionModel`
- `ToolCallRequest`
- `ToolCallResult`
- `ToolErrorPayload`
- `ToolExecutionContext`
- `PreconditionResult`
- `PostconditionResult`
- `ToolPermission`
- `ToolRiskPolicy`
- `ApprovalRequest`
- `IdempotencyRecord`
- `ResourceLockRequest`
- `ResourceLock`
- `ToolExecutionState`
- `ToolRetryPolicy`
- `ToolObservation`
- `ToolCallRecord`

---

# 10.1 `ToolRegistryProtocol`

Provide:

```python
class ToolRegistryProtocol(Protocol):
    async def register(
        self,
        definition: ToolDefinitionModel,
    ) -> ToolDefinitionModel:
        ...

    async def get(
        self,
        tool_key: str,
        version: str | None = None,
    ) -> ToolDefinitionModel | None:
        ...

    async def filter_by_agent(
        self,
        agent_key: str,
        required_tools: set[str],
    ) -> list[ToolDefinitionModel]:
        ...

    async def execute_tool(
        self,
        request: ToolCallRequest,
        cancellation: CancellationToken,
    ) -> ToolCallResult:
        ...

    async def check_idempotency(
        self,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        ...
```

Improve signatures where needed, but preserve deterministic boundaries.

---

# 11. WINDOWS API / UIA CONTRACTS

Provide concrete typed wrappers and `ctypes`/`comtypes` declarations where applicable for:

### Process APIs

```text
CreateProcessW
OpenProcess
GetExitCodeProcess
CloseHandle
TerminateProcess
```

### Window APIs

```text
EnumWindows
GetWindowThreadProcessId
IsWindowVisible
GetForegroundWindow
SetForegroundWindow
BringWindowToTop
SendMessageW
PostMessageW
```

### Desktop APIs

```text
OpenInputDesktop
GetUserObjectInformationW
```

### Input APIs

```text
SendInput
VkKeyScanExW
```

### DPI

```text
GetDpiForWindow
```

### UIA

Provide concrete COM interface usage for:

```text
IUIAutomation
IUIAutomationElement
IUIAutomationCondition
IUIAutomationCacheRequest
IUIAutomationInvokePattern
IUIAutomationValuePattern
IUIAutomationTogglePattern
IUIAutomationSelectionItemPattern
IUIAutomationExpandCollapsePattern
IUIAutomationScrollItemPattern
```

Do not simply name the APIs. Provide usable signatures or wrappers and safe error normalization.

---

# 12. REFERENCE TOOL CATALOG

Define the foundational phase-1 tool catalog as declarative records.

At minimum include:

```text
windows.launch_application
windows.find_window
windows.close_window

uia.find_element
uia.invoke_control
uia.set_value
uia.select_item
uia.get_tree_snapshot

input.click_coordinate
input.type_keystrokes
input.clipboard_paste

screen.capture_window
screen.assert_element_visible
```

For each tool provide:

- key
- version
- purpose
- capabilities
- risk
- approval policy
- input schema
- output schema
- preconditions
- postconditions
- timeout
- retry policy
- required resource locks
- implementation binding

Do not give all agents all tools.

---

# 13. COMPLETE TOOL EXECUTION PIPELINE

Provide complete Python implementation for:

```text
execute_tool(request)
```

Required sequence:

```text
1. normalize request
2. resolve tool definition
3. verify enabled
4. validate version
5. validate input schema
6. canonicalize arguments
7. compute/recompute idempotency
8. resolve agent permission
9. compute effective risk
10. evaluate policy
11. create approval request if needed
12. acquire required resources
13. re-check idempotency
14. validate preconditions
15. invoke deterministic implementation
16. capture observation
17. validate output schema
18. verify postconditions where defined
19. persist tool call atomically
20. emit audit event
21. release resources
22. return standardized result
```

Explain transaction and lock ordering to avoid deadlocks.

---

# 14. DATABASE PERSISTENCE & TELEMETRY

Align with:

```text
tool_definitions
tool_calls
audit_events
approvals
```

---

# 14.1 `tool_calls`

Map at minimum:

```text
id
run_id
run_step_id
agent_run_id
tool_key
request
response
status
idempotency_key
risk_class
error_code
started_at
completed_at
```

Also define audit-friendly metadata where supported.

---

# 14.2 Atomic result persistence

Define transaction boundaries so:

```text
tool execution
+
result persistence
+
idempotency record
```

cannot produce contradictory states.

For process-backed external effects, explain the unavoidable distinction between:

```text
physical side effect occurred
```

and:

```text
database commit succeeded
```

and define recovery behavior for that boundary.

---

# 14.3 Audit events

Emit:

```text
tool.invoked
tool.approval_requested
tool.approval_granted
tool.approval_rejected
tool.succeeded
tool.failed
tool.idempotency_hit
tool.resource_waiting
tool.timeout
tool.user_interrupted
tool.security_blocked
```

Each event includes:

- event ID
- run ID
- step ID
- agent run ID
- tool key/version
- trace ID
- timestamp
- status
- risk
- observation ID
- sanitized metadata

Never log raw secrets.

---

# 15. SECURITY MODEL

Threats to cover:

- model-generated unauthorized tool calls
- tool alias bypass
- schema confusion
- argument injection
- path traversal
- symlink/reparse-point escape
- shell injection
- arbitrary process execution
- UAC interaction
- credential capture
- malicious browser content
- clipboard leakage
- duplicate side effects
- concurrent duplicate execution
- approval replay
- stale approval
- stale target observation
- desktop focus races
- resource exhaustion
- malformed output payload
- tool-definition tampering
- version confusion
- cross-run data leakage

Required guarantees:

1. Tool definitions are immutable/versioned.
2. Model output cannot create a tool.
3. Model output cannot grant permissions.
4. Model output cannot lower risk.
5. Every call is schema-validated.
6. Every side effect is idempotency-protected.
7. High-risk actions are approval-gated.
8. System-admin actions fail closed.
9. File paths are workspace-bound.
10. Desktop actions use the desktop mutex.
11. Human interference freezes automation.
12. Tool outputs are size-bounded and validated.
13. Browser/file text remains untrusted data.
14. No default unrestricted shell tool exists.
15. Every sensitive operation is auditable.

---

# 16. OBSERVABILITY & PERFORMANCE

Define metrics:

```text
tool_lookup_latency_ms
tool_schema_validation_latency_ms
tool_authorization_latency_ms
tool_approval_wait_ms
tool_resource_wait_ms
tool_execution_latency_ms
tool_observation_latency_ms
tool_persistence_latency_ms
tool_success_count
tool_failure_count
tool_timeout_count
tool_permission_rejection_count
tool_approval_count
tool_idempotency_hit_count
desktop_mutex_wait_ms
```

Dimensions:

- tool key
- version
- agent
- risk
- run
- step
- worker
- execution state

Do not log complete arguments by default.

Prefer:

```text
argument_hash
argument_size
redacted_argument_summary
```

---

# 17. PERFORMANCE & CONCURRENCY TARGETS

Define measurable targets for:

- tool lookup
- schema validation
- permission evaluation
- idempotency check
- resource acquisition
- execution wrapper overhead
- observation generation
- persistence commit

Define bounds:

```text
max_registered_tools
max_tool_schema_bytes
max_arguments_bytes
max_output_bytes
max_concurrent_tool_calls
max_concurrent_desktop_tools
max_approval_wait
max_retry_count
```

All values must be configurable.

---

# 18. REFERENCE PACKAGE STRUCTURE

Provide a concrete implementation tree:

```text
syncnode/
└── tool_registry/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── registry.py
    ├── definitions.py
    ├── schemas.py
    ├── authorization.py
    ├── risk.py
    ├── approvals.py
    ├── idempotency.py
    ├── resources.py
    ├── executor.py
    ├── lifecycle.py
    ├── timeouts.py
    ├── observations.py
    ├── persistence.py
    ├── telemetry.py
    ├── errors.py
    └── windows/
        ├── __init__.py
        ├── process.py
        ├── windows.py
        ├── uia.py
        ├── input.py
        ├── keyboard.py
        ├── mouse.py
        ├── clipboard.py
        ├── desktop.py
        └── security.py
```

Tests:

```text
tests/
├── test_registry.py
├── test_schema_validation.py
├── test_authorization.py
├── test_risk.py
├── test_approvals.py
├── test_idempotency.py
├── test_executor.py
├── test_timeouts.py
├── test_windows.py
├── test_uia.py
├── test_input.py
├── test_clipboard.py
├── test_persistence.py
├── test_security.py
└── test_determinism.py
```

Adapt to `idea.md`.

---

# 19. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The final `TOOL_REGISTRY.md` MUST include real Python 3.12+ implementations for at least:

1. ToolDefinition validation
2. semantic-version resolution
3. tool registry lookup
4. immutable definition snapshotting
5. strict JSON Schema/Pydantic validation
6. argument canonicalization
7. workspace path validation
8. shell/command rejection policy
9. risk derivation
10. agent permission filtering
11. approval-gate creation
12. deterministic idempotency-key generation
13. idempotency database acquisition
14. resource-lock acquisition
15. desktop mutex handling
16. complete tool execution wrapper
17. soft timeout
18. hard timeout strategy
19. cleanup ordering
20. structured ToolCallResult
21. Windows `CreateProcessW` wrapper
22. Windows `EnumWindows` wrapper
23. UIA locator wrapper
24. UIA InvokePattern wrapper
25. UIA ValuePattern wrapper
26. UIA SelectionItemPattern wrapper
27. `SendInput` wrapper
28. clipboard bridge
29. observation hashing
30. tool-call persistence
31. audit event generation
32. complete `ToolRegistryProtocol`

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- fully type annotated
- async-compatible where appropriate
- Windows-compatible
- syntactically complete
- executable with documented dependencies
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder implementations
- free of unexplained magic constants

Where Windows behavior requires special handling, provide a safe wrapper and document the exact preconditions and error mapping.

---

# 20. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- integration tests
- Windows integration tests
- schema fuzz tests
- permission tests
- approval tests
- idempotency race tests
- concurrency tests
- timeout tests
- crash-recovery tests
- security tests
- deterministic replay tests
- persistence tests

Mandatory tests:

### Tool isolation

Unauthorized tools never reach execution.

### Schema isolation

Malformed or extra arguments are always rejected.

### Risk isolation

Model-provided risk cannot reduce deterministic risk.

### Approval safety

Approval-required tool cannot execute without valid approval.

### Approval binding

Changing arguments after approval invalidates that approval.

### Idempotency

Concurrent identical side-effect requests create at most one physical execution.

### Desktop safety

Two desktop tools cannot control the same physical session concurrently.

### Path safety

Workspace escapes always fail.

### Shell safety

Arbitrary PowerShell/CMD payloads are rejected.

### UIA safety

Semantic UIA execution is preferred over coordinates.

### Cleanup

All terminal states release resource locks.

### Determinism

Identical:

- tool definition
- agent permission set
- policy
- request
- resource state

produce identical:

- authorization decision
- risk classification
- idempotency key
- selected implementation
- validation result

---

# 21. INTEGRATION WITH AGENT REGISTRY / SPAWNER

Define the boundary:

```text
Agent Spawner
     ↓
agent_key
allowed_tools
risk
model/context
     ↓
Tool Registry
     ↓
effective tool surface
```

The Agent Spawner may request a tool subset.

The Tool Registry performs the authoritative final check.

An agent cannot widen its own allowlist after spawn.

---

# 22. INTEGRATION WITH COMPUTER RUNTIME

Define:

```text
Tool Registry
     ↓
windows.* / uia.* / input.* / screen.*
     ↓
Computer Runtime
     ↓
Windows
```

The Tool Registry owns tool authorization and lifecycle.

The Computer Runtime owns actual Windows/Win32/UIA mechanics.

Do not duplicate low-level Windows implementation in unrelated modules.

---

# 23. INTEGRATION WITH CONTEXT ENGINE & VERIFIER

After state-changing tools:

```text
Tool executes
   ↓
Computer/Document/Browser observation
   ↓
Context Engine delta
   ↓
Verifier assertion
```

Tool results must include observation references where available.

The model may interpret the result but cannot rewrite the canonical observation.

---

# 24. REFERENCE END-TO-END EXAMPLES

Use real SyncNode workflows.

---

## Example A — Click Word Save

```text
Model proposes:
uia.invoke_control(Name="Save", ControlType="Button")
```

Runtime:

```text
lookup tool
→ validate schema
→ check permission
→ READ/WRITE_LOCAL-compatible risk
→ acquire desktop mutex
→ validate Word foreground
→ resolve UIA element
→ invoke InvokePattern
→ capture new observation
→ verify save state
→ persist tool_call
→ audit
→ release mutex
```

---

## Example B — Coordinate fallback

```text
UIA target cannot be resolved
```

Required:

```text
reobserve
→ application adapter / vision fallback
→ fresh coordinate proposal
→ verify foreground/bounds
→ acquire desktop mutex
→ SendInput
→ reobserve
→ verify
```

---

## Example C — Email send

The send tool must:

```text
EXTERNAL_COMMUNICATION
→ approval required
→ approval record
→ WAITING_APPROVAL
→ approval granted
→ current state revalidated
→ send
→ verify
```

No model-generated "approved=true" field may satisfy this requirement.

---

## Example D — Duplicate retry

Same request arrives twice with identical normalized arguments:

```text
same idempotency key
→ first call already succeeded
→ return persisted ToolCallResult
→ do not execute physical side effect again
```

---

## Example E — UAC

```text
secure desktop detected
→ SEC_UAC_RESTRICTED
→ no input
→ audit
→ fail tool
```

---

# 25. FINAL ENGINE CONTRACT

The Tool Registry SHALL:

- maintain versioned tool definitions
- strictly validate every call
- enforce agent-scoped allowlists
- verify capabilities
- derive risk deterministically
- enforce approval
- generate/validate idempotency keys
- prevent duplicate side effects
- acquire resource locks
- provide typed execution envelopes
- integrate with Computer Runtime for Windows automation
- prioritize semantic UIA control
- expose coordinate input only as controlled fallback
- enforce path boundaries
- reject unrestricted shell execution
- bound inputs/outputs/timeouts
- persist `tool_calls`
- emit `audit_events`
- provide structured recovery errors
- remain local-first
- remain independently testable

The Tool Registry SHALL NOT:

- allow models to create tools
- expose unauthorized tools
- trust model-provided permissions
- lower deterministic risk
- approve risky operations
- execute arbitrary shell scripts
- bypass UAC
- harvest credentials
- duplicate idempotent side effects
- bypass desktop locks
- leak secrets
- silently ignore validation failures
- silently execute an unknown implementation

---

# 26. OUTPUT QUALITY BAR

The generated `TOOL_REGISTRY.md` must be:

- exhaustive
- production-grade
- implementation-ready
- deterministic
- security-focused
- Windows-aware
- concurrency-safe
- idempotency-safe
- database-aligned
- directly implementable

Do not produce:

- generic plugin-system tutorials
- generic RPA tutorials
- marketing language
- vague recommendations
- pseudo-code presented as production code
- undefined classes
- placeholder methods
- `TODO`
- `TBD`
- `pass`
- unexplained magic constants
- cloud-dependent architecture
- unrestricted shell examples
- unsafe automation shortcuts

Use throughout:

- Pydantic v2 schemas
- Python Protocols
- JSON Schema
- state machines
- Mermaid diagrams
- Win32 ctypes/comtypes signatures
- UIA pattern implementations
- approval interlocks
- idempotency equations
- SQL transaction examples
- failure taxonomies
- security invariants
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
TOOL_REGISTRY.md
```
