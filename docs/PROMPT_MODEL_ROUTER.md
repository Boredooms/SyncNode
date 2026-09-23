# PROMPT: Generate `MODEL_ROUTER.md` Technical Specification

You are a **Principal AI Systems Engineer and Distributed Inference Architect** specializing in:

- local-first model execution
- deterministic model routing
- dynamic capability matching
- GPU/VRAM-aware scheduling
- provider health management
- model fallback systems
- air-gapped runtime security
- multi-agent inference infrastructure

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, production-grade, implementation-ready technical specification** titled:

> `MODEL_ROUTER.md`

This specification governs the **SyncNode Model Router**, the deterministic routing and scheduling subsystem embedded within the Model Gateway.

The Model Router is responsible for:

- matching agent/model requirements against local model profiles
- validating context-window capacity
- validating vision/tool/structured-output capabilities
- probing local provider health
- measuring hardware/VRAM availability
- preferring warm/resident models where appropriate
- scoring eligible candidates deterministically
- executing a bounded local fallback ladder
- enforcing strict air-gapped network policy
- generating auditable route decisions
- binding selected model profiles into `agent_runs`

The Model Router must remain separate from:

- Intent parsing
- Task planning
- Agent spawning
- Token accounting
- Tool execution
- Computer UI control
- Browser automation
- Human approval
- Verification

Those are separate SyncNode subsystems.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architectural source of truth.

Before writing the final `MODEL_ROUTER.md`:

1. Read the complete `idea.md`.
2. Extract its:
   - model profile schema
   - provider abstraction
   - Model Gateway boundaries
   - agent requirements
   - hardware assumptions
   - database entities
   - audit requirements
   - air-gap constraints
   - local runtime assumptions
   - phase-1 scope
3. Preserve SyncNode terminology.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud inference.
6. Do not introduce remote tokenizers, remote model selection services, or external orchestration dependencies.
7. Keep model IDs, context windows, capabilities, and endpoints configurable.
8. Where `idea.md` leaves implementation details unspecified, make a concrete choice and mark it:
   > **Implementation Decision**
9. Distinguish clearly between:
   - model profile metadata
   - provider runtime state
   - health state
   - hardware telemetry
   - deterministic routing decision
   - fallback decision
   - inference execution
   - persisted audit state

The output must be sufficient for another engineer to implement the subsystem without requiring another architecture document.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & DESIGN PHILOSOPHY

Position the router precisely between Agent Spawner and Model Gateway:

```text
                Agent Spawner
                     │
                     ▼
              RouteRequest
                     │
                     ▼
        ┌────────────────────────────┐
        │        MODEL ROUTER        │
        │                            │
        │ Capability Filter          │
        │ Context Validation         │
        │ Health Probe               │
        │ VRAM / Resource Probe      │
        │ Candidate Scoring          │
        │ Fallback Resolution        │
        │ Air-Gap Guard              │
        └─────────────┬──────────────┘
                      │
                      ▼
                RouteDecision
                      │
                      ▼
                Model Gateway
                      │
                      ▼
            Local Provider Runtime
                (Ollama / local)
```

The Model Router SHALL own:

- candidate discovery
- model profile validation
- capability filtering
- context-window validation
- local provider selection
- hardware-aware route evaluation
- warm-model detection
- deterministic scoring
- fallback resolution
- circuit breaking
- air-gap enforcement
- route-decision telemetry

It SHALL NOT own:

- direct tool execution
- prompt generation
- token lease issuance
- agent lifecycle
- task planning
- approval decisions
- direct UI/browser actions
- final model response processing

---

## 1.1 Core invariants

### Local-only routing

Only approved local runtime providers are eligible.

Examples may include:

```text
Ollama localhost
Approved on-premise inference socket
Approved local Unix/Windows IPC endpoint
```

Cloud APIs must never appear in the candidate pool.

### Capability correctness

A model may be selected only if every hard model requirement is satisfied.

### Context correctness

A model is ineligible when:

```text
required_context_tokens > model_context_window
```

### Deterministic routing

Given identical:

- request
- model profiles
- health state
- hardware state
- router configuration

the same route decision must be produced.

### Fail closed

No compatible local model means:

```text
MODEL_UNAVAILABLE
```

or the appropriate terminal failure.

The router must never silently choose a model that violates a hard requirement.

---

# 1.2 Required routing lifecycle diagram

Include both a Mermaid and/or ASCII diagram:

```text
Agent Spawn Request
        ↓
Normalize Route Request
        ↓
Load Model Profile Catalog
        ↓
Filter Disabled / Invalid Profiles
        ↓
Air-Gap Endpoint Validation
        ↓
Capability Filter
        ↓
Context Window Filter
        ↓
Tool / Vision / Structured Output Filter
        ↓
Provider Health Probe
        ↓
VRAM / CPU / Residency Probe
        ↓
Candidate Scoring
        ↓
Primary Model Selected
        ↓
[Admission Failure?]
       /   \
     No     Yes
     │       │
     │       ▼
     │   Fallback Tier 2
     │       ↓
     │   [Available?]
     │      /   \
     │    Yes    No
     │    │       │
     ▼    ▼       ▼
 RouteDecision   MODEL_UNAVAILABLE
        ↓
Execution Lease / Gateway
```

---

# 2. MODEL REGISTRY INTEROPERABILITY & SCHEMA MAPPING

Align directly with the `model_profiles` schema from `idea.md`.

At minimum support:

```text
id
provider
model_id
display_name
capabilities
context_window
supports_vision
supports_tools
enabled
priority
config
```

Do not invent incompatible column names when `idea.md` defines them.

---

## 2.1 `ModelProfile` contract

Provide a complete Pydantic v2 model representing the runtime profile.

Include:

```python
class ModelProfile(BaseModel):
    id: UUID
    provider: str
    model_id: str
    display_name: str
    capabilities: list[str]
    context_window: int
    supports_vision: bool
    supports_tools: bool
    enabled: bool
    priority: int
    config: dict[str, Any]
```

Expand this with fields only when justified by `idea.md` or explicitly labeled implementation decisions.

Add validators for:

- positive context window
- bounded priority
- valid model ID
- supported provider
- capability syntax
- bounded config size
- valid endpoint mode
- no remote endpoint under local-only policy

---

# 2.2 Profile lifecycle

Define:

```text
DISCOVERED
→ VALIDATED
→ ENABLED
→ HEALTHY
→ AVAILABLE
```

Failure states:

```text
INVALID
DISABLED
UNHEALTHY
QUARANTINED
UNAVAILABLE
```

Do not allow invalid/disabled profiles into route selection.

---

# 2.3 Profile caching

Define a thread-safe or async-safe profile cache.

Required behaviors:

- TTL
- version/hash
- cache refresh
- explicit invalidation
- profile update hooks
- stale profile handling
- deterministic serialization

Example key:

```text
syncnode:model_profile:{profile_id}:{profile_version}
```

Never cache secrets.

---

# 2.4 Local provider discovery

Define provider endpoint discovery for local runtimes.

For Ollama, support configuration equivalent to:

```text
http://127.0.0.1:11434
```

and explicitly validate its address.

Define:

- endpoint parser
- loopback/private network validation
- connectivity probe
- runtime identity check
- provider version capture
- multi-instance local provider strategy

Do not assume every local provider uses HTTP.

The provider boundary must be abstracted behind a Protocol.

---

# 3. CAPABILITY TAXONOMY & DYNAMIC MATCHING ENGINE

Define canonical model capabilities.

Examples:

```text
tools:native
tools:json_schema
vision:multimodal
context:8k
context:16k
context:32k
reasoning:high
reasoning:standard
streaming
structured_output
```

Capabilities in `capabilities` should be machine-readable and versionable.

---

## 3.1 Capability requirements

Define an explicit request model:

```text
required_context_tokens
requires_vision
requires_tool_calling
requires_structured_output
requires_streaming
required_capabilities
forbidden_capabilities
```

Hard requirements MUST be separate from preferences.

---

# 3.2 Context-window compatibility

Hard filter:

```text
N_required <= N_available
```

Where:

```text
N_required =
prompt_tokens
+
completion_reserve
+
safety_buffer
```

A model with insufficient context must be eliminated before scoring.

---

# 3.3 Vision interlock

If the request contains:

```text
image_count > 0
```

and:

```text
requires_vision == true
```

then:

```text
supports_vision == true
```

is mandatory.

A text-only fallback must not silently receive visual payloads.

---

# 3.4 Tool-calling interlock

If:

```text
requires_tool_calling == true
```

then the profile must support native tool calling or the exact compatible structured mechanism declared by the architecture.

Do not classify arbitrary text output as equivalent to provider-native tool calling without explicit compatibility rules.

---

# 3.5 Structured-output interlock

If the agent requires JSON Schema / structured output:

```text
supports_structured_output == true
```

must be verified.

Where capability is not explicitly known, classify it as unavailable rather than assuming support.

---

# 3.6 Capability matching algorithm

Provide complete Python code for:

```python
def is_eligible(
    request: RouteRequest,
    profile: ModelProfile,
    runtime: ProviderRuntimeState,
) -> EligibilityResult:
    ...
```

The function must:

1. reject disabled profiles
2. reject remote providers
3. reject insufficient context
4. reject missing vision
5. reject missing tools
6. reject missing structured output
7. reject forbidden capabilities
8. reject unhealthy providers
9. reject unavailable hardware
10. return explicit rejection reasons

---

# 4. HARDWARE-AWARE ROUTING & RESOURCE PROBING

Integrate routing with Token Management and local hardware telemetry.

---

## 4.1 VRAM probing

Define a hardware abstraction:

```python
class HardwareProbeProtocol(Protocol):
    async def snapshot(self) -> HardwareSnapshot:
        ...
```

`HardwareSnapshot` must capture, where available:

- total VRAM
- free VRAM
- used VRAM
- total RAM
- free RAM
- GPU utilization
- process/model residency data
- timestamp

Do not require NVIDIA-specific APIs as the only implementation.

---

# 4.2 Model memory estimate

Define:

```text
estimated_model_memory
+
estimated_kv_cache_memory
+
runtime_overhead
<= available_memory × utilization_limit
```

Use a model-profile-driven approximation.

Clearly state that the estimate is a routing heuristic and not a universal exact physical-memory measurement.

---

# 4.3 Residency / warm-model state

Integrate with local provider state.

For Ollama-style runtimes define a local probe that can retrieve loaded models and their residency.

Represent:

```python
class ModelResidency(BaseModel):
    model_id: str
    is_loaded: bool
    vram_bytes: int | None
    last_seen_at: datetime
```

Warm models may receive a deterministic scoring bonus because they can reduce cold-start cost.

The bonus must never override a hard capability or safety constraint.

---

# 4.4 Concurrency limits

Define:

```text
max_concurrent_requests_per_model
max_concurrent_requests_per_provider
max_vram_utilization
max_gpu_queue_depth
```

Candidate models must be rejected or queued when hard resource limits are exceeded.

---

# 4.5 Hardware-pressure states

Define:

```text
NORMAL
WARNING
THROTTLED
CRITICAL
```

Example:

```text
NORMAL
→ all eligible models
WARNING
→ reduce new admissions
THROTTLED
→ prefer lightweight/warm profiles
CRITICAL
→ reject or queue memory-heavy routes
```

Never route to an incompatible model simply because it has lower resource requirements.

---

# 5. MULTI-CRITERIA SCORING & ROUTE SELECTION

Define the canonical scoring formula:

```text
Score =
    w_p × Priority
  + w_w × IsWarm
  + w_c × ContextHeadroom
  - w_l × LatencyPenalty
```

Normalize each factor to `[0,1]`.

You may extend the formula with explicitly justified terms such as:

```text
resource_fit
availability
vision_fit
tool_fit
load_penalty
failure_penalty
```

but hard requirements must always be filtering constraints rather than score terms.

---

## 5.1 Feature definitions

Define exact formulas for:

### Priority

Normalize profile priority against the candidate pool:

```text
PriorityNorm =
(priority - min_priority)
/
max(max_priority - min_priority, 1)
```

### Warm score

```text
IsWarm ∈ {0,1}
```

### Context headroom

```text
ContextHeadroom =
(model_context - required_context)
/
max(model_context, 1)
```

Clamp to `[0,1]`.

### Latency penalty

Use measured local telemetry where available.

Example:

```text
LatencyPenalty =
min(p95_latency / latency_budget, 1.0)
```

or another explicit normalized formula.

---

# 5.2 Weight profiles

Define deterministic weight profiles for categories such as:

| Task Profile | Priority | Warm | Context | Latency |
|---|---:|---:|---:|---:|
| Simple Extraction | ... | ... | ... | ... |
| Structured Tool Call | ... | ... | ... | ... |
| Document Synthesis | ... | ... | ... | ... |
| Vision UI Control | ... | ... | ... | ... |
| Verification | ... | ... | ... | ... |

These are routing policies, not claims that a particular model is universally preferable.

Allow configuration overrides through typed settings.

---

# 5.3 Deterministic tie-breaking

When scores are equal:

```text
1. higher profile priority
2. greater context headroom
3. healthier provider
4. warmer residency
5. lexicographically smaller model_id
6. lexicographically smaller profile_id
```

Document the exact order.

Never use random selection.

---

# 5.4 Candidate trace

Every route evaluation should produce an auditable candidate record:

```text
candidate_model_id
eligible
rejection_reasons
feature_vector
score
provider_health
hardware_state
```

This makes routing decisions reproducible.

---

# 6. LOCAL FALLBACK LADDER & DEGRADATION POLICIES

Implement exactly three tiers.

---

## Tier 1 — Primary local model

The profile preferred by the agent/step requirements.

Example:

```text
gemma4:e3b
```

or another compatible local model profile.

The model ID is configurable and must not be hardcoded.

---

## Tier 2 — Degraded local fallback

A compatible smaller/quantized/specialized model.

Requirements:

- still local
- still policy-compatible
- still satisfies all mandatory capabilities
- still has enough context
- still supports the required interaction mode

Never degrade a hard requirement.

Example:

```text
vision-required
→ another local vision model

tool-required
→ another local tool-capable model
```

Do not route to a text-only model for a vision-required action.

---

## Tier 3 — Terminal failure

Raise:

```text
MODEL_UNAVAILABLE
```

or:

```text
VRAM_EXHAUSTED
```

depending on the failure.

Persist:

- candidate list
- rejection reasons
- hardware state
- health state
- requested capabilities
- trace ID

---

# 6.1 Fallback semantics

Fallback may occur due to:

- provider unavailable
- profile unhealthy
- model unloaded and admission denied
- VRAM shortage
- concurrency saturation
- local model load failure
- temporary circuit breaker

Fallback MUST NOT occur because the selected model violates a hard safety requirement.

---

# 6.2 Anti-flapping circuit breaker

Maintain per-profile failure counters.

States:

```text
CLOSED
OPEN
HALF_OPEN
```

Define:

- consecutive failure threshold
- open duration
- probe interval
- half-open success criterion
- half-open failure transition
- recovery reset

A circuit breaker must be local and deterministic.

---

# 7. AIR-GAP ENFORCEMENT & NETWORK INTERLOCKS

This section must contain concrete network validation code.

---

## 7.1 Allowed endpoint policy

At minimum permit:

```text
127.0.0.1
::1
```

and any explicitly configured trusted on-premise network ranges when `idea.md` permits them.

Reject public internet addresses by default.

---

## 7.2 Endpoint validation

Implement:

```python
def validate_local_endpoint(url: str, policy: AirGapPolicy) -> EndpointValidation:
    ...
```

The validator must:

1. parse scheme
2. resolve hostname
3. inspect IP addresses
4. reject public addresses
5. reject disallowed private networks
6. validate port
7. enforce approved provider schemes
8. produce a deterministic decision

Be careful about DNS rebinding.

Define whether hostname-only configuration is allowed.

---

# 7.3 Egress violation handling

If a profile attempts to use a remote endpoint:

```text
REMOTE_ENDPOINT_REJECTED
```

Required sequence:

```text
detect
→ block route
→ emit security event
→ persist audit record
→ quarantine profile if configured
→ return structured routing error
```

Do not kill the whole application process merely because one profile is invalid unless system policy explicitly requires fail-stop behavior.

---

# 8. PROVIDER HEALTH, LIFECYCLE & WARMUP

Define a provider health subsystem.

---

## 8.1 Health states

```text
UNKNOWN
HEALTHY
DEGRADED
UNHEALTHY
OFFLINE
```

Transitions must be explicit.

---

# 8.2 Health probes

For Ollama-compatible runtime examples include:

```text
/api/version
/api/tags
```

Use the Model Gateway provider adapter rather than embedding provider-specific logic throughout the router.

Health probes must be:

- local
- bounded
- asynchronous
- timeout-protected
- rate-limited
- non-invasive

---

# 8.3 Warmup

Define an optional warmup routine:

```text
profile selected
→ provider healthy
→ model availability verified
→ minimal local inference / provider-native warmup
→ residency rechecked
→ profile marked warm
```

Warmup must not occur for disabled profiles or profiles failing air-gap validation.

Make warmup idempotent.

---

# 8.4 Readiness integration

Expose a summarized router readiness signal:

```text
ready
not_ready
degraded
```

for backend readiness such as:

```text
/readyz
```

Define the difference between:

- essential default model unavailable
- optional model unavailable
- provider degraded
- all local inference unavailable

---

# 9. ROUTE DECISION & EXECUTION LEASE

Define a strong boundary between route selection and inference execution.

`RouteDecision` should identify:

```text
selected profile
provider
model ID
endpoint
fallback tier
scoring metadata
health snapshot
hardware snapshot
route policy version
```

The router does not perform model inference.

---

## 9.1 Route validity TTL

Define whether a decision can be reused.

Recommended:

```text
RouteDecision valid_until
```

Hardware/health-sensitive decisions should have short lifetimes.

A stale decision must be revalidated before execution.

---

## 9.2 Model profile binding

Once accepted by the Agent Spawner / Model Gateway:

```text
RouteDecision
→ model_profile_id
→ agent_runs.model_profile_id
```

This binding must remain auditable.

A mid-execution model swap should create a new route decision and telemetry event, not silently overwrite the original selection.

---

# 10. TELEMETRY, ROUTING DECISIONS & AUDIT PERSISTENCE

Define structured telemetry for every route attempt.

Required decision metadata:

```text
selected_model_id
candidate_models
scores
fallback_tier_used
vram_headroom_bytes
route_latency_ms
```

Also record:

- request ID
- run ID
- step ID
- agent key
- model profile ID
- provider
- health state
- hardware snapshot ID
- route policy version
- circuit-breaker state
- rejection reasons
- trace ID

---

# 10.1 `agent_runs`

Link successful/failed route resolution to:

```text
agent_runs.model_profile_id
```

Also support:

```text
routing_decision_id
```

where schema extension is permitted.

---

# 10.2 `audit_events`

Emit security/routing events such as:

```text
model.route_selected
model.route_rejected
model.fallback_invoked
model.capability_rejected
model.remote_endpoint_blocked
model.circuit_opened
model.circuit_closed
model.vram_throttled
model.health_changed
```

Never include secret configuration values.

---

# 11. COMPLETE DATA CONTRACTS & INTERFACES

Provide complete Pydantic v2 models and typed Python Protocols.

---

## 11.1 `RouteRequest`

Include:

```python
class RouteRequest(BaseModel):
    run_id: UUID
    step_id: UUID
    agent_key: str
    required_capabilities: set[str]
    context_tokens: int
    completion_reserve: int
    requires_vision: bool
    requires_tool_calling: bool
    requires_structured_output: bool
    requires_streaming: bool
    latency_budget_ms: int | None
    allow_fallback: bool
    preferred_model_id: str | None
    trace_id: str
```

Add validators and cross-field constraints.

---

## 11.2 `RouteDecision`

Include:

```text
decision_id
selected_model_profile_id
provider
model_id
endpoint
fallback_tier
candidate_evaluations
justification
health_snapshot
hardware_snapshot
route_policy_version
created_at
valid_until
```

---

## 11.3 `ModelRouterProtocol`

Provide:

```python
class ModelRouterProtocol(Protocol):
    async def resolve_route(
        self,
        request: RouteRequest,
        cancellation: CancellationToken,
    ) -> RouteDecision:
        ...

    async def get_fallback(
        self,
        request: RouteRequest,
        excluded_profile_ids: set[UUID],
        cancellation: CancellationToken,
    ) -> RouteDecision:
        ...

    async def probe_health(
        self,
        profile_id: UUID,
        cancellation: CancellationToken,
    ) -> ProviderHealth:
        ...

    async def register_profile(
        self,
        profile: ModelProfile,
    ) -> ModelProfile:
        ...
```

Improve the interface where required, but preserve deterministic boundaries.

---

## 11.4 `RoutingMetrics`

Include:

```text
evaluation_latency_ms
candidate_count
eligible_count
rejection_count
cache_hit
fallback_count
vram_probe_latency_ms
health_probe_latency_ms
circuit_breaker_state
final_selection
```

---

# 12. REQUIRED SUPPORTING SCHEMAS

Also define:

- `ModelCapabilityRequirements`
- `ModelProfile`
- `ProviderEndpoint`
- `ProviderRuntimeState`
- `ProviderHealth`
- `HardwareSnapshot`
- `ModelResidency`
- `CandidateEvaluation`
- `EligibilityResult`
- `CapabilityEvaluation`
- `RouteScore`
- `FallbackPolicy`
- `CircuitBreakerState`
- `CircuitBreakerSnapshot`
- `AirGapPolicy`
- `EndpointValidation`
- `RoutePolicy`
- `RoutingMetrics`
- `RoutingAuditEvent`
- `ModelRouterError`

No undefined types are permitted in code examples.

---

# 13. DETERMINISTIC ROUTING ALGORITHM

Provide the full algorithm in implementation-ready form.

Required sequence:

```text
1. Validate RouteRequest.
2. Load local model profiles.
3. Remove disabled profiles.
4. Validate provider endpoints.
5. Filter by hard capabilities.
6. Filter by context capacity.
7. Filter by hardware admission.
8. Filter by provider health.
9. Apply circuit-breaker exclusion.
10. Compute candidate feature vectors.
11. Normalize score components.
12. Calculate weighted score.
13. Apply deterministic tie-breaking.
14. Select Tier 1.
15. If execution admission fails, evaluate Tier 2.
16. If no compatible local candidate remains, fail.
17. Emit RouteDecision.
18. Persist route telemetry.
```

The decision must be reproducible.

---

# 14. FAILURE STATES & ERROR TAXONOMY

Define a complete machine-readable error catalog:

```text
MODEL_PROFILE_NOT_FOUND
MODEL_PROFILE_DISABLED
MODEL_CAPABILITY_MISMATCH
MODEL_CONTEXT_INSUFFICIENT
MODEL_VISION_UNSUPPORTED
MODEL_TOOL_CALLING_UNSUPPORTED
MODEL_STRUCTURED_OUTPUT_UNSUPPORTED
MODEL_STREAMING_UNSUPPORTED
PROVIDER_NOT_FOUND
PROVIDER_OFFLINE
PROVIDER_UNHEALTHY
REMOTE_ENDPOINT_REJECTED
VRAM_EXHAUSTED
RESOURCE_LIMIT_REACHED
MODEL_CIRCUIT_OPEN
MODEL_LOAD_FAILED
MODEL_WARMUP_FAILED
MODEL_UNAVAILABLE
ROUTE_EXPIRED
ROUTE_INVALID
ROUTE_POLICY_VIOLATION
ROUTE_NO_LOCAL_CANDIDATE
```

Every error must contain:

- stable error code
- severity
- retryability
- run ID
- step ID
- trace ID
- provider/model where relevant
- sanitized reason
- fallback eligibility

Never expose credential material.

---

# 15. RESILIENCE & RECOVERY

Define exact handling for:

### Provider restart

```text
health failure
→ mark degraded
→ invalidate residency
→ reject stale route
→ probe provider
→ reopen candidate pool when healthy
```

### Model load failure

```text
load failure
→ record attempt
→ update failure counter
→ release resource reservation
→ invoke Tier 2 if compatible
```

### VRAM exhaustion

```text
VRAM_EXHAUSTED
→ prevent new oversized admissions
→ prefer compatible lightweight models
→ retry only within bounded policy
→ terminal failure if no eligible model
```

### Stale route

```text
decision expired
→ revalidate health/hardware/profile
→ regenerate route
```

Do not reuse stale hardware-sensitive decisions.

---

# 16. CACHE & INVALIDATION

Define cache namespaces such as:

```text
syncnode:model_profiles:{profile_hash}
syncnode:model_health:{profile_id}
syncnode:model_residency:{provider_id}
syncnode:model_route:{route_request_hash}
syncnode:model_circuit:{profile_id}
```

For each define:

- TTL
- value schema
- invalidation triggers
- stale-use rules
- serialization format

Invalidate routing caches on:

- model profile change
- provider health change
- hardware pressure transition
- model load/unload
- policy change
- route-policy version change
- tokenizer/context profile change

Never use stale route results after a material capability change.

---

# 17. CONCURRENCY & ATOMIC RESOURCE ADMISSION

Define safe admission semantics.

For a candidate:

```text
check resource
→ reserve resource
→ recheck resource
→ commit route admission
```

Avoid TOCTOU problems.

Where multiple workers share routing capacity, use atomic locks/transactions.

Provide SQL or local lock implementation where appropriate.

---

# 18. REFERENCE PACKAGE STRUCTURE

Provide a concrete package structure:

```text
syncnode/
└── model_router/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── router.py
    ├── registry.py
    ├── capabilities.py
    ├── scoring.py
    ├── fallbacks.py
    ├── health.py
    ├── hardware.py
    ├── residency.py
    ├── circuit_breaker.py
    ├── airgap.py
    ├── cache.py
    ├── persistence.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_profiles.py
        ├── test_capabilities.py
        ├── test_airgap.py
        ├── test_hardware.py
        ├── test_scoring.py
        ├── test_fallbacks.py
        ├── test_health.py
        ├── test_residency.py
        ├── test_circuit_breaker.py
        ├── test_cache.py
        ├── test_persistence.py
        ├── test_security.py
        └── test_determinism.py
```

Adapt to the exact `idea.md` repository structure.

---

# 19. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The final `MODEL_ROUTER.md` MUST contain actual Python 3.12+ code for at least:

1. model-profile validation
2. local endpoint parsing
3. air-gap endpoint validation
4. capability matching
5. context-window eligibility
6. vision/tool/structured-output gating
7. hardware snapshot abstraction
8. VRAM admission calculation
9. model-residency tracking
10. deterministic feature normalization
11. weighted route scoring
12. deterministic tie-breaking
13. candidate evaluation
14. Tier-1 route selection
15. Tier-2 fallback selection
16. circuit-breaker state machine
17. provider health state machine
18. route TTL validation
19. route cache key construction
20. complete `resolve_route()` orchestration
21. structured routing telemetry
22. database persistence contract
23. local-provider health probe
24. resource admission logic
25. `MODEL_UNAVAILABLE` propagation

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- fully type annotated
- async-compatible where appropriate
- syntactically complete
- executable
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholders
- free of unexplained magic constants

Where provider-specific behavior is abstracted, define complete Protocol interfaces and at least one concrete local-provider reference implementation.

---

# 20. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- integration tests
- provider health tests
- hardware admission tests
- fallback tests
- circuit-breaker tests
- concurrency tests
- database tests
- security tests
- deterministic replay tests
- performance tests

Mandatory tests:

### Capability safety

A vision-required request can never route to a non-vision model.

### Context safety

A request exceeding model capacity can never be routed.

### Tool safety

A tool-required request can never route to a model lacking the required tool mechanism.

### Air-gap safety

Public/cloud endpoints are always rejected.

### Determinism

Identical routing inputs/state produce identical decisions.

### Fallback safety

Tier 2 never violates hard requirements.

### Circuit breaking

A quarantined/open model is not selected.

### VRAM safety

Oversubscribed profiles are rejected or queued.

### Stale-route safety

Expired route decisions are not directly executed.

### Concurrency

Parallel workers cannot over-admit a constrained model/resource pool.

---

# 21. INTEGRATION WITH AGENT SPAWNER

Define exact handoff:

```text
Agent Spawner
      ↓
SpawnRequest
      ↓
Model Router
      ↓
RouteDecision
      ↓
Token Manager
      ↓
Context / Prompt Assembly
      ↓
Model Gateway
      ↓
Local Provider
```

The Agent Spawner provides requirements.

The Model Router selects a concrete local model profile.

The Token Manager validates token capacity.

The Model Gateway performs inference.

No subsystem may bypass the route decision boundary without explicit policy.

---

# 22. INTEGRATION WITH MODEL GATEWAY

Define the exact contract:

```text
RouteDecision
   ↓
ProviderAdapter
   ↓
Local model invocation
```

The Model Router must never make direct inference calls.

The Model Gateway must revalidate the selected profile immediately before dispatch if health/resource state may have changed.

A mismatch between RouteDecision and actual provider profile must yield:

```text
ROUTE_PROFILE_MISMATCH
```

rather than silently executing another model.

---

# 23. REFERENCE END-TO-END EXAMPLES

Use concrete cases.

---

## Example A — Simple local text task

```text
Task:
"Extract the title from report.txt"
```

Show:

```text
requirements
→ candidate profiles
→ capability filtering
→ score
→ selected model
→ telemetry
```

---

## Example B — Vision task

```text
Task:
"Inspect the current Word window and determine which button is focused."
```

Show:

```text
requires_vision = true
→ text-only candidates rejected
→ compatible local vision profiles evaluated
→ warm/VRAM-aware scoring
→ selected route
```

---

## Example C — Tool-calling task

```text
Task:
"Open the document and save it."
```

Show:

```text
requires_tool_calling = true
→ candidates without tool support rejected
→ local tool-capable profile selected
```

---

## Example D — Fallback

Show:

```text
Tier 1:
preferred model unavailable / VRAM constrained

↓
Tier 2:
compatible smaller local model

↓
selected
```

---

## Example E — Terminal failure

Show:

```text
all local profiles fail hard requirements

→ ROUTE_NO_LOCAL_CANDIDATE
→ MODEL_UNAVAILABLE
→ audit
→ Agent Spawner receives failure
```

---

# 24. SECURITY MODEL

Threats to address:

- cloud model fallback
- endpoint spoofing
- DNS rebinding
- stale profile usage
- capability spoofing
- priority manipulation
- routing-cache poisoning
- circuit-breaker bypass
- VRAM overcommit
- model substitution during execution
- disabled-profile selection
- provider impersonation
- remote network egress
- telemetry leakage
- stale route reuse

Required guarantees:

1. Only trusted local providers are routable.
2. Provider endpoints are deterministically validated.
3. Disabled profiles cannot route.
4. Hard capabilities are filters, not soft scores.
5. Fallback cannot violate hard requirements.
6. Route decisions are versioned.
7. Route decisions expire.
8. Provider/model mismatch fails closed.
9. Resource admission is bounded.
10. Routing telemetry is auditable.
11. No remote model is silently substituted.
12. No secret configuration is emitted to telemetry.

---

# 25. PERFORMANCE & OPERATIONS

Define measurable engineering targets for:

- profile lookup
- health probe
- hardware probe
- capability filtering
- candidate scoring
- route decision generation
- route-cache lookup
- fallback resolution
- circuit-breaker evaluation

Also define:

```text
max_candidate_models
max_profile_cache_size
max_health_probe_rate
max_route_decisions_per_second
max_concurrent_routing_evaluations
```

Provide complexity analysis for:

```text
capability filtering
O(M × C)

candidate scoring
O(M)

tie breaking
O(M log M)
```

where:

- `M` = candidate model count
- `C` = average capability comparisons

---

# 26. FINAL ENGINE CONTRACT

The Model Router SHALL:

- remain local-first
- enforce air-gapped routing
- consume `model_profiles`
- filter by hard capabilities
- validate context capacity
- account for vision/tool/structured-output needs
- monitor local provider health
- monitor hardware/VRAM
- track model residency
- score candidates deterministically
- use a bounded local fallback ladder
- enforce circuit breakers
- prevent resource overcommit
- produce auditable RouteDecision objects
- bind decisions to `agent_runs.model_profile_id`
- invalidate stale decisions
- fail closed when no compatible local route exists
- remain independently testable

The Model Router SHALL NOT:

- route to public cloud models
- invent model capabilities
- ignore hard context requirements
- bypass agent model requirements
- perform inference itself
- change the agent's permissions
- silently substitute incompatible models
- silently exceed hardware constraints
- reuse expired route decisions
- hide fallback events
- leak secret configuration

---

# 27. OUTPUT QUALITY BAR

The generated `MODEL_ROUTER.md` must be:

- exhaustive
- production-grade
- deterministic
- security-focused
- hardware-aware
- concurrency-safe
- model-agnostic
- air-gap-safe
- database-aligned
- directly implementable

Do not produce:

- generic routing tutorials
- generic model comparisons
- marketing language
- vague recommendations
- pseudo-code presented as production code
- undefined classes
- placeholder functions
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
- capability matrices
- deterministic scoring equations
- hardware admission formulas
- circuit-breaker transitions
- SQL persistence examples
- security invariants
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
MODEL_ROUTER.md
```
