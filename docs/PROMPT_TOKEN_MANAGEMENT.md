# PROMPT: Generate `TOKEN_MANAGEMENT.md` Technical Specification

You are a **Principal AI Performance Engineer and Systems Architect** specializing in:

- local-first LLM inference
- deterministic token accounting
- dynamic context-window management
- memory/VRAM-aware inference orchestration
- reservation and lease systems
- agent-runtime budgeting
- local telemetry and SQL persistence

Your task is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, implementation-ready technical specification** titled:

> `TOKEN_MANAGEMENT.md`

The document defines the **SyncNode Token Management & Accounting Subsystem**: the deterministic runtime layer responsible for offline token estimation, exact local token counting where available, model-aware context budgeting, token reservations and leases, deterministic pruning/compaction, VRAM-aware concurrency control, streaming accounting, failure detection, and persistence of token telemetry.

The specification must integrate cleanly with the existing SyncNode architecture, especially:

- Context Engine
- LangGraph Brain / Orchestrator
- Model Gateway
- Agent Runtime
- Tool Registry
- Verification / Recovery
- Memory / Knowledge
- Audit / Telemetry
- `model_profiles`
- `agent_runs`
- `runs`
- local Ollama inference
- local Gemma 4 variants
- PostgreSQL / SQLite persistence

Do not create a generic LLM token tutorial. Design a concrete production subsystem for SyncNode.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architecture source.

Before producing the final specification:

1. Read the complete `idea.md`.
2. Extract its terminology, database entities, component boundaries, runtime constraints, functional requirements, non-functional requirements, and phase-1 scope.
3. Preserve existing SyncNode terminology wherever possible.
4. Do not silently contradict `idea.md`.
5. Do not invent cloud dependencies.
6. Do not introduce external token-counting APIs.
7. Where `idea.md` leaves an implementation detail unspecified, make a concrete engineering decision and label it clearly as an **Implementation Decision**.
8. Keep model identifiers configurable. The system may use local Gemma 4 variants through Ollama, but token-management logic must not hardcode a single model.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & DESIGN PHILOSOPHY

Position the subsystem precisely:

```text
                         SyncNode Runtime
                              │
                              ▼
                      ┌────────────────┐
                      │ Context Engine │
                      └───────┬────────┘
                              │ tokenized components
                              ▼
                      ┌────────────────┐
                      │Token Management│
                      └───────┬────────┘
                              │ bounded prompt + output grant
                              ▼
                      ┌────────────────┐
                      │ Model Gateway  │
                      └───────┬────────┘
                              │
                              ▼
                      Local Model / Ollama
```

The Token Management subsystem MUST be deterministic and must own:

- token estimation
- exact local counting
- context capacity calculation
- reserve calculation
- budget allocation
- token reservations
- step/run quotas
- lease lifecycle
- compaction requests
- completion-budget enforcement
- streaming accounting
- reconciliation
- persistence
- accounting telemetry
- overflow classification

It MUST NOT own:

- task planning
- agent selection
- tool authorization
- computer control
- approval decisions
- direct model inference
- canonical OS observations

---

## 1.1 Core invariants

The subsystem MUST enforce:

### Local-only execution

All counting and budgeting occurs locally.

No:

- cloud tokenizer API
- remote token-counting service
- external telemetry upload
- external embedding/token endpoint

is required.

### Atomic reservation

A token grant cannot be partially observed as available.

Reservation operations MUST behave atomically:

```text
available → reserved
reserved → settled
reserved → released
```

No negative available capacity is permitted.

### Strict capacity enforcement

For every inference request:

```text
prompt_tokens
+ completion_reserve
+ safety_buffer
<= model_context_window
```

The system must validate this before the request reaches the Model Gateway.

### No hallucinated capacity

The Brain or LLM must never declare that context capacity exists.

The Token Manager computes the authoritative budget.

### Fail closed

Unsafe or impossible budgeting must terminate with structured errors.

Never silently truncate critical instructions.

---

# 1.2 Required architecture diagram

Include a detailed Mermaid and/or ASCII flow:

```text
┌───────────────────────────────────────────────────────────────────┐
│                     RAW PROMPT COMPONENTS                         │
│ System │ Agent Rules │ Intent │ Tools │ Context │ History │ Images│
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │ Local Token Counter       │
                    │ Fast Estimator / Exact    │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Budget Allocation Engine  │
                    └─────────────┬────────────┘
                                  │
                        exceeds safe limit?
                             /          \
                           no            yes
                           │              │
                           │              ▼
                           │     ┌─────────────────────┐
                           │     │ Pruning Waterfall   │
                           │     └──────────┬──────────┘
                           │                │
                           │        still too large?
                           │           /        \
                           │         no          yes
                           │         │             │
                           ▼         ▼             ▼
                    ┌────────────────────┐  CONTEXT_OVERFLOW
                    │ Token Lease Issuer │
                    └─────────┬──────────┘
                              ▼
                       Model Gateway
                              ▼
                        Local Inference
                              ▼
                  Telemetry / Actual Usage
                              ▼
                    Lease Reconciliation
                              ▼
                   SQL + Structured Audit
```

---

# 2. OFFLINE TOKENIZATION & LOCAL COUNTING ENGINES

Define a dual-tier token-counting architecture.

---

## 2.1 Tier 1 — Fast heuristic estimator

Purpose:

- preliminary budgeting
- quick admission checks
- UI feedback
- early pruning threshold calculations

Requirements:

- sub-millisecond target for normal short strings
- deterministic
- zero network calls
- no dependency on model server availability
- pessimistic enough to avoid under-reservation

Provide an implementation such as:

```python
estimated_tokens = max(
    1,
    math.ceil(
        normalized_characters / chars_per_token
    )
)
```

Do not leave the constant unexplained.

Define:

- ASCII behavior
- Unicode behavior
- whitespace handling
- punctuation handling
- code-heavy input behavior
- JSON/XML behavior
- long identifiers behavior
- multilingual text behavior

---

## 2.2 Tier 2 — Exact local tokenizer

Define a local tokenizer registry supporting model-specific tokenizers.

Possible implementation families:

- Hugging Face `AutoTokenizer`
- locally cached model tokenizer files
- model-native local tokenizers where available

The design MUST keep tokenizer loading local.

Specify:

```text
model_id
architecture
tokenizer_id
tokenizer_revision
vocabulary_hash
special_token_policy
max_context_tokens
```

No tokenizer download may occur at runtime.

If tokenizer artifacts are absent locally:

```text
EXACT_COUNTER_UNAVAILABLE
```

must be surfaced and the engine may fall back to the configured conservative estimator only when policy allows it.

---

## 2.3 Tokenizer lifecycle and cache

Define:

- singleton-per-process or bounded shared cache
- LRU eviction
- maximum tokenizer instances
- thread safety
- async compatibility
- initialization locks
- warmup
- tokenizer integrity hash
- cache key format

Example namespace:

```text
syncnode:tokenizer:{model_id}:{tokenizer_revision}
```

The tokenizer cache must never contain credentials or user document content.

---

# 2.4 Counting canonicalization

Specify a canonical token-counting input representation.

Before counting:

1. Normalize string encoding to UTF-8.
2. Normalize prohibited control characters.
3. Preserve semantically meaningful whitespace where model prompts depend on it.
4. Use the exact final serialized prompt for exact counting.
5. Count tool schemas and structured envelopes as part of prompt tokens.
6. Include multimodal accounting where the active model requires it.

The token count used for dispatch must correspond to the payload actually sent to the Model Gateway.

---

# 2.5 Multimodal token equivalency

Define a model-profile-driven image accounting model.

At minimum support a configuration abstraction:

```text
image_token_cost =
    base_image_tokens
  + f(width, height, patch_size, vision_rule)
```

Do not present the formula as universally true for all model architectures.

Require the active `model_profile` to provide:

- vision enabled
- supported image dimensions
- patch size where applicable
- image token estimator
- maximum image count
- maximum pixel budget
- model-specific accounting mode

For screenshot-heavy computer-use workflows:

```text
raw screenshot
→ crop
→ resize
→ quality reduction
→ semantic UI extraction
→ retain only if still necessary
```

The Token Manager must be able to assign equivalent token cost to visual payloads before reservation.

If the model gateway reports authoritative multimodal usage, reconciliation MUST use the provider-reported usage for settlement.

---

# 3. CONTEXT WINDOW BUDGETING & PARTITIONING ENGINE

Define the authoritative context equation.

Let:

```text
Nctx = model context capacity
S    = system prompt
R    = security / agent rules
O    = completion output reserve
T    = tool schemas
I    = task intent
K    = context snapshot
H    = execution history
B    = safety buffer
```

Then:

```text
PromptBudget =
    Nctx
  - O
  - B
```

and:

```text
DynamicContextBudget =
    PromptBudget
  - S
  - R
  - T
  - I
  - H
```

The request is valid only when:

```text
S + R + O + T + I + K + H + B <= Nctx
```

Provide exact validation code.

---

# 3.1 Reserve classes

Define:

### Fixed reserves

- core system persona
- security directives
- mandatory policy instructions
- output JSON/tool-call reserve
- mandatory protocol wrappers

### Dynamic reserves

- active agent instructions
- filtered tool schemas
- task intent
- context snapshot
- execution history
- relevant workflow memory

Specify floor and ceiling values.

A fixed reserve must never be reduced below its safety floor merely to accommodate optional context.

---

# 3.2 Agent-specific allocation profiles

Provide a concrete matrix for context sizes such as:

| Agent | 8K | 16K | 32K |
|---|---:|---:|---:|
| Writer | ... | ... | ... |
| Computer Control | ... | ... | ... |
| Browser | ... | ... | ... |
| Verifier | ... | ... | ... |
| Planner | ... | ... | ... |

The table must represent **allocation policies**, not claims that one agent is universally better.

Define fields such as:

- system reserve
- rules reserve
- tool reserve
- intent reserve
- observation reserve
- history reserve
- output reserve
- safety buffer

Explain how the matrix is overridden dynamically by the active model profile.

---

# 3.3 Output reserve protection

Guarantee sufficient generation space for:

- structured JSON
- tool calls
- recovery outputs
- verification assertions

Define:

```text
min_output_reserve
max_output_reserve
default_output_reserve
```

The output reserve must be checked before lease acquisition.

A request cannot consume output reserve merely because the input context expanded.

---

# 3.4 Budget allocation algorithm

Provide full Python code for:

1. reading the model profile
2. obtaining `Nctx`
3. calculating fixed reserves
4. calculating dynamic reserves
5. allocating source quotas
6. applying minimum and maximum limits
7. scoring optional context
8. returning the final token budget

Use deterministic ordering:

```text
priority descending
→ relevance descending
→ trust descending
→ recency descending
→ stable item ID ascending
```

No random allocation.

---

# 4. DETERMINISTIC PRUNING & TRUNCATION WATERFALL

Implement the exact multi-stage pruning sequence.

The Token Manager coordinates pruning decisions while the Context Engine performs source-specific compaction.

---

## Stage 1 — Perceptual pruning

Remove or compress:

- stale screenshots
- obsolete image observations
- raw pixel-coordinate dumps
- transient visual states
- redundant UI tree records

Retain:

- semantic locator
- active control
- current focused element
- verification-critical state

---

## Stage 2 — Trace summarization

Convert older execution history into one-line milestones:

```text
step_17: SUCCESS: opened Word and focused document editor
step_18: SUCCESS: inserted generated story
step_19: SUCCESS: document saved and file existence verified
```

Preserve:

- failed verification
- policy rejection
- human approval events
- recovery evidence

when still relevant to the active step.

---

## Stage 3 — Artifact & knowledge slicing

Reduce large sources using:

- top relevance-ranked passages
- diff-focused excerpts
- file headings
- AST summaries
- function/class outlines
- document section summaries
- RAG chunk slicing

Never cut through mandatory security instructions.

---

## Stage 4 — Tool schema stripping

Remove tools that are:

- unauthorized
- irrelevant to the current agent
- outside the current execution step
- redundant
- disallowed by policy

Tool schemas required to execute the active step are protected.

---

## Stage 5 — Hard boundary

Raise:

```python
ContextOverflowError(
    code="CONTEXT_OVERFLOW",
    ...
)
```

when the minimum viable context still cannot fit.

Do not:

- silently truncate system policy
- silently truncate active security instructions
- silently reduce output reserve below its floor
- silently remove mandatory tool definitions

---

# 4.1 Compaction assertions

Every compaction operation must assert:

```text
mandatory_system_tokens retained
mandatory_security_tokens retained
active_agent_rules retained
required_tool_schemas retained
task_intent retained
minimum_output_reserve retained
safety_buffer retained
```

If any assertion fails:

```text
CONTEXT_COMPACTION_UNSAFE
```

must be raised.

---

# 5. TOKEN RESERVATION, LEASES & CONCURRENCY CONTROL

Design an explicit token lease subsystem.

---

## 5.1 Step-level leases

A lease reserves a maximum token grant:

```text
Tmax =
    estimated_prompt_tokens
  + requested_completion_tokens
  + safety_margin
```

Reservation must be atomic.

State machine:

```text
REQUESTED
   ↓
RESERVED
   ↓
IN_FLIGHT
   ↓
RECONCILING
  ↙      ↘
SETTLED  RELEASED
```

Failure state:

```text
EXPIRED / ABORTED
```

Specify legal state transitions.

---

## 5.2 Run-level token ceiling

Define:

```python
max_total_tokens
```

for an entire run.

Track cumulative:

```text
prompt_tokens
completion_tokens
total_tokens
```

across all steps.

Reject new leases when:

```text
run_consumed + requested_grant > max_total_tokens
```

This must prevent:

- runaway retries
- infinite re-planning
- recursive agent spawning
- excessive tool loops

---

## 5.3 Reservation accounting

Maintain:

```text
capacity
reserved
consumed
available
```

with invariant:

```text
capacity = available + reserved + consumed
```

No negative values.

Use atomic local locking or database transactions where shared workers are involved.

---

## 5.4 Lease expiration

Every lease must have:

- created time
- expiration time
- owner/worker ID
- run ID
- step ID
- requested tokens
- granted tokens
- consumed tokens
- state

Expired leases must be released safely.

A lease may never be silently counted as consumed merely because it expired.

---

# 5.5 Reconciliation

After inference:

```text
estimated reservation
       ↓
provider-reported actual usage
       ↓
settlement
       ↓
release unspent grant
```

Ollama usage, where available, must be preferred over heuristic estimates for final accounting.

Record the estimator used for the original reservation.

If actual usage is unavailable:

- settle using conservative configured rules
- mark usage as estimated
- never claim exact accounting

---

# 6. HARDWARE & VRAM MEMORY IMPACT

Define model-aware memory pressure controls.

Use a configurable KV-cache estimate based on the active model profile.

At minimum document the approximation:

```text
Memory_KV =
    2
  × Layers
  × KV_Heads
  × Head_Dim
  × Nctx
  × Bytes_Per_Element
```

Explain that real memory usage depends on:

- implementation
- quantization
- cache format
- batching
- speculative decoding
- multimodal features
- runtime overhead
- framework behavior

Therefore, use the equation for **planning**, not as a universal exact measurement.

---

# 6.1 VRAM pressure controller

Define states:

```text
NORMAL
WARNING
THROTTLED
CRITICAL
```

Example behavior:

### NORMAL

Normal agent concurrency and configured context.

### WARNING

Limit new concurrent leases above a configurable token threshold.

### THROTTLED

Reduce:

- concurrent model calls
- maximum active context
- image budgets
- optional history

### CRITICAL

Pause new expensive inference reservations until resources recover.

Do not automatically terminate an already-running high-priority step unless policy explicitly permits it.

---

# 6.2 Hardware telemetry

Track locally:

- GPU memory total
- GPU memory free
- GPU utilization where available
- CPU RAM pressure
- active model
- active context size
- concurrent leases

Make the hardware adapter pluggable.

Do not require NVIDIA-only behavior.

---

# 7. TELEMETRY, ACCOUNTING & PERSISTENCE

Align token accounting with:

```text
agent_runs
runs
model_profiles
```

and the persistence design from `idea.md`.

---

## 7.1 `agent_runs`

Every model invocation MUST record:

```text
prompt_tokens
completion_tokens
total_tokens
latency_ms
```

Also record, where supported:

- model ID
- tokenizer ID
- usage source
- reservation ID
- lease ID
- context capacity
- requested completion budget
- estimated prompt tokens
- actual prompt tokens
- actual completion tokens
- TTFT
- generation throughput
- finish reason
- compaction level
- trace ID

---

## 7.2 `runs`

Maintain aggregate run-level accounting:

```text
total_prompt_tokens
total_completion_tokens
total_tokens
total_model_latency_ms
step_count
```

Define transaction semantics so aggregates do not become inconsistent with constituent `agent_runs`.

---

## 7.3 Structured events

Define Pydantic models and event contracts for:

```text
token_lease.acquired
token_lease.started
token_lease.reconciled
token_lease.released
token_budget.exhausted
compaction.requested
compaction.applied
context_overflow.detected
generation_limit.triggered
usage.recorded
```

Every event must include:

- event ID
- timestamp
- run ID
- step ID
- lease ID where applicable
- trace ID
- model ID where applicable
- structured metadata

---

# 7.4 Accounting invariants

Enforce:

```text
total_tokens =
    prompt_tokens + completion_tokens
```

when both are authoritative.

For estimated usage:

```text
usage_accuracy = ESTIMATED
```

must be explicit.

No double counting across:

- streaming chunks
- final response
- retries
- reconciliations

Provide an idempotency key for usage records.

---

# 8. FAILURE MODES, EDGE CASES & CIRCUIT BREAKERS

Define complete failure behavior.

---

## 8.1 `CONTEXT_OVERFLOW`

Required behavior:

```text
detect
→ emit event
→ persist failure
→ mark current step blocked
→ release/reconcile lease if not started
→ propagate structured error to Brain
→ allow RecoveryNode to decide next action
```

Do not automatically retry endlessly.

---

## 8.2 Runaway generation breaker

Detect:

- completion token budget exhausted
- repeated identical output fragments
- repeated tool-call loops
- repeated planner states
- configured total-token ceiling exceeded

Define deterministic repetition detection.

Example:

```text
if identical normalized completion window repeats R times:
    GENERATION_LOOP_DETECTED
```

Use configurable:

- repetition window
- repetition threshold
- normalized comparison rule

---

## 8.3 Streaming accounting

For streaming Model Gateway responses:

Track:

```text
tokens_seen
elapsed_ms
tokens_per_second
last_token_timestamp
```

Use provider counts when present.

Otherwise use deterministic local increment/estimation.

Define:

- stall timeout
- maximum no-token interval
- cancellation behavior
- final reconciliation behavior

---

## 8.4 Model truncation detection

Detect finish reasons equivalent to:

```text
length
context_length
max_tokens
```

depending on provider normalization.

Required behavior:

```text
truncation detected
→ persist telemetry
→ determine whether mandatory output was lost
→ request bounded recovery OR surface failure
```

Never recursively retry without a configured maximum retry count.

---

# 9. COMPLETE DATA CONTRACTS & INTERFACES

Provide **fully syntactically valid Pydantic v2 models** and typed Python Protocols.

At minimum implement:

---

## 9.1 `TokenBudgetConfig`

Include:

```python
class TokenBudgetConfig(BaseModel):
    context_window_tokens: int
    safety_buffer_tokens: int
    min_output_reserve_tokens: int
    default_output_reserve_tokens: int
    max_output_reserve_tokens: int
    max_total_tokens: int
    estimator_chars_per_token: float
    lease_ttl_seconds: int
    max_concurrent_leases: int
```

Add validators and cross-field invariants.

---

## 9.2 `TokenUsage`

Include:

```python
class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int | None
    latency_ms: float
    usage_source: Literal["provider", "exact_local", "estimated"]
    model_id: str
    tokenizer_id: str | None
```

Enforce arithmetic invariants.

---

## 9.3 `TokenLease`

Include:

- lease ID
- run ID
- step ID
- worker ID
- granted tokens
- estimated prompt tokens
- reserved completion tokens
- safety margin
- consumed tokens
- state
- creation timestamp
- expiry timestamp
- reconciliation timestamp

---

## 9.4 `CompactionPlan`

Include:

- source snapshot
- evaluated items
- protected items
- dropped item IDs
- compressed item IDs
- tokens before
- tokens after
- waterfall stages
- reason
- deterministic decision metadata

---

## 9.5 `TokenManagerProtocol`

Provide a complete protocol:

```python
class TokenManagerProtocol(Protocol):
    async def estimate(
        self,
        payload: TokenPayload,
        model_id: str,
    ) -> TokenEstimate:
        ...

    async def count(
        self,
        payload: TokenPayload,
        model_id: str,
    ) -> ExactTokenCount:
        ...

    async def reserve(
        self,
        request: TokenReservationRequest,
    ) -> TokenLease:
        ...

    async def reconcile(
        self,
        lease_id: UUID,
        usage: TokenUsage,
    ) -> TokenLease:
        ...

    async def prune(
        self,
        request: PruningRequest,
    ) -> CompactionPlan:
        ...

    async def record(
        self,
        usage: TokenUsage,
        lease: TokenLease | None,
    ) -> None:
        ...
```

Improve signatures where necessary so the interface remains testable, cancellable, deterministic, and compatible with the SyncNode Model Gateway.

---

# 10. REQUIRED SUPPORTING SCHEMAS

Also define complete Pydantic models for:

- `TokenPayload`
- `TokenEstimate`
- `ExactTokenCount`
- `ModelTokenProfile`
- `TokenReservationRequest`
- `TokenReservationResult`
- `LeaseState`
- `CompactionStage`
- `PruningRequest`
- `BudgetAllocation`
- `BudgetComponent`
- `RunTokenBudget`
- `StreamingTokenState`
- `GenerationGuardState`
- `VRAMSnapshot`
- `VRAMPolicy`
- `TokenTelemetryEvent`
- `UsageRecord`
- `TokenManagerError`

No code example may depend on an undefined type.

---

# 11. MODEL-PROFILE INTEROPERABILITY

Define how the Token Manager consumes `model_profiles`.

At minimum the profile must expose, where available:

```text
model_id
provider
architecture
context_window
tokenizer_id
tokenizer_revision
supports_vision
supports_tool_calls
supports_structured_output
max_output_tokens
kv_cache_parameters
quantization
```

The Token Manager MUST treat `model_profiles` as the authoritative capability/configuration source for budgeting.

When a model changes:

```text
model profile changed
→ invalidate budget/tokenizer caches
→ reload tokenizer if needed
→ recalculate Nctx
→ re-evaluate image accounting
→ invalidate stale reservations
```

A lease created for one model profile cannot silently be reused for another incompatible model.

---

# 12. CACHE & INVALIDATION STRATEGY

Define caches for:

- tokenizer instances
- exact token counts
- heuristic token estimates
- model profiles
- budget calculations
- compaction decisions where safe

Cache keys must include all parameters affecting the result.

Example:

```text
syncnode:tokens:{model_id}:{tokenizer_revision}:{payload_sha256}
syncnode:budget:{model_id}:{profile_hash}:{budget_input_hash}
syncnode:lease:{lease_id}
```

Do not cache sensitive raw payloads without explicit security policy.

Prefer storing:

```text
payload_hash → token_count
```

rather than arbitrary document bodies.

---

# 13. CONCURRENCY & ATOMICITY IMPLEMENTATION

Define behavior for:

- multiple runs on one model
- multiple agents within one run
- competing leases
- worker crashes
- lease expiration
- database contention
- in-memory vs SQL-backed accounting

Provide concrete transaction semantics.

For SQL-backed reservation, specify a safe approach such as:

```text
BEGIN
→ lock quota row
→ validate available capacity
→ increment reserved amount
→ insert lease
→ COMMIT
```

Document how SQLite development mode differs from PostgreSQL production mode.

Do not rely on application-level checks alone when multiple workers share the same accounting pool.

---

# 14. REFERENCE PACKAGE STRUCTURE

Provide a concrete source tree consistent with SyncNode:

```text
syncnode/
└── token_management/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── manager.py
    ├── tokenizer.py
    ├── estimator.py
    ├── budgets.py
    ├── leases.py
    ├── pruning.py
    ├── guards.py
    ├── accounting.py
    ├── persistence.py
    ├── telemetry.py
    ├── vram.py
    ├── errors.py
    └── tests/
        ├── test_estimator.py
        ├── test_tokenizer.py
        ├── test_budget.py
        ├── test_lease.py
        ├── test_pruning.py
        ├── test_accounting.py
        ├── test_streaming.py
        ├── test_vram.py
        ├── test_persistence.py
        └── test_determinism.py
```

Adapt this tree to `idea.md` where needed.

---

# 15. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The final `TOKEN_MANAGEMENT.md` MUST contain actual Python 3.12+ implementations for the critical algorithms.

At minimum include complete code for:

1. local fast token estimation
2. exact tokenizer loading from local cache
3. tokenizer instance caching
4. SHA-256 payload hashing
5. dynamic context budget calculation
6. agent-specific budget allocation
7. deterministic reserve validation
8. token lease acquisition
9. lease expiration
10. lease reconciliation
11. run-level quota enforcement
12. compaction waterfall orchestration
13. repetition detection
14. streaming token accounting
15. usage idempotency handling
16. SQL accounting transaction logic
17. model-profile validation
18. VRAM pressure throttling
19. typed Token Manager orchestration
20. `CONTEXT_OVERFLOW` propagation

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- fully typed
- async-compatible where applicable
- syntactically complete
- executable with reasonable dependency installation
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of placeholder implementations
- free of unexplained constants

Where database access is abstracted, define the protocol and provide a concrete reference implementation or SQL example rather than leaving a hole.

---

# 16. TESTING & ACCEPTANCE CRITERIA

Define comprehensive:

- unit tests
- integration tests
- concurrency tests
- failure tests
- deterministic replay tests
- database accounting tests
- performance tests
- VRAM pressure tests
- streaming tests

Required assertions include:

### Budget correctness

```text
system
+ security
+ agent rules
+ tools
+ intent
+ context
+ history
+ output reserve
+ safety buffer
<= context window
```

always.

### Reservation correctness

```text
capacity = available + reserved + consumed
```

always.

### Usage correctness

```text
total_tokens =
prompt_tokens + completion_tokens
```

when authoritative counts exist.

### Idempotency

Replaying the same usage event must not double-count tokens.

### Determinism

Identical:

- model profile
- payload
- budget configuration
- context state
- pruning configuration

must produce identical:

- estimate
- budget allocation
- pruning stages
- reservation amount
- error classification

### Concurrency

Concurrent reservation attempts must never oversubscribe the configured accounting pool.

---

# 17. INTEGRATION WITH CONTEXT ENGINE

Define the exact boundary:

```text
Context Engine
    ↓
ContextSnapshot
    ↓
Token Manager
    ↓
BudgetAllocation
    ↓
Pruning request if required
    ↓
PackedPromptEnvelope
    ↓
Final exact/local count
    ↓
Token Lease
    ↓
Model Gateway
```

Clarify responsibility:

### Context Engine owns

- gathering context
- sanitization
- relevance
- deduplication
- context-specific compaction
- prompt envelope creation

### Token Manager owns

- token measurement
- budget math
- reservations
- leases
- completion limits
- accounting
- pruning coordination
- token telemetry

Neither subsystem may assume that the other has already guaranteed the final token boundary without explicit validation.

---

# 18. INTEGRATION WITH MODEL GATEWAY

Specify the exact handoff.

Expected sequence:

```text
1. Model Gateway supplies active model profile.
2. Token Manager computes context capacity.
3. Context Engine returns packed envelope.
4. Token Manager performs final count.
5. Token Manager verifies safe budget.
6. Token Manager reserves tokens.
7. Model Gateway invokes local model.
8. Streaming usage is tracked.
9. Provider usage is reconciled.
10. Lease is settled.
11. `agent_runs` is updated.
12. Run aggregate is updated.
```

The Model Gateway remains the inference provider boundary.

The Token Manager must not call the model directly.

---

# 19. REFERENCE END-TO-END EXECUTION

Use the workflow:

> “Write a story about a tree and send it to Rahul.”

Show how token accounting behaves across:

```text
Intent
→ Planner
→ Writer Agent
→ Context retrieval
→ Document creation
→ UI verification
→ Browser interaction
→ Approval gate
→ Send
→ Verification
```

For every model call show:

- model profile
- context capacity
- estimated prompt tokens
- exact prompt tokens if available
- output reserve
- safety buffer
- lease amount
- actual completion tokens
- total usage
- reconciliation
- cumulative run total

Demonstrate at least one case where the context exceeds the safe boundary and the pruning waterfall is triggered.

Demonstrate a terminal `CONTEXT_OVERFLOW` case.

---

# 20. SECURITY MODEL

Define threats and mitigations:

- cloud token-counting leakage
- tokenizer artifact tampering
- cache poisoning
- quota bypass
- integer overflow
- negative token values
- reservation race conditions
- stale leases
- usage replay
- cross-run accounting leakage
- cross-user quota leakage
- model-profile mismatch
- unbounded completion requests
- malformed streaming chunks
- provider usage discrepancies

Required protections:

1. local tokenizer artifacts only
2. SHA-256/version validation for tokenizer/profile assets
3. bounded integer fields
4. atomic reservation
5. lease owner validation
6. idempotent usage events
7. profile-bound reservations
8. strict maximum completion tokens
9. fail-closed accounting inconsistencies
10. auditable state transitions

---

# 21. OBSERVABILITY & OPERATIONS

Provide structured metrics:

```text
token_estimate_latency_ms
token_exact_count_latency_ms
token_reservation_latency_ms
token_reconciliation_latency_ms
tokens_reserved
tokens_consumed
tokens_released
budget_exhaustions
context_overflows
compaction_count
compaction_tokens_saved
generation_guard_trips
lease_expirations
usage_reconciliation_mismatches
```

Also define dimensions:

- model ID
- agent
- run
- step
- worker
- tokenizer
- usage source
- compaction stage

Do not log sensitive prompt payloads by default.

Use hashes and aggregate metrics instead.

---

# 22. PERFORMANCE TARGETS

Define measurable targets and explain that they are engineering targets rather than guaranteed hardware-independent facts.

At minimum specify:

- fast estimator latency target
- tokenizer cache-hit target
- budget calculation target
- lease acquisition target
- reconciliation target
- memory overhead per tokenizer instance
- maximum accounting lock duration

Give formulas for throughput:

```text
tokens_per_second =
completion_tokens / generation_seconds
```

and:

```text
token_accounting_overhead =
accounting_time_ms / inference_time_ms
```

---

# 23. FINAL SUBSYSTEM CONTRACT

End the document with a precise contract.

The Token Management subsystem SHALL:

- operate fully on-premise
- never require external token-counting APIs
- use model-aware context limits
- use local tokenization whenever exact counting is available
- maintain a conservative fallback estimator
- reserve output space before dispatch
- enforce deterministic context budgeting
- coordinate a deterministic pruning waterfall
- issue atomic token leases
- enforce run-level cumulative quotas
- reconcile estimates with actual provider usage
- persist `agent_runs` usage metrics
- maintain run-level aggregates
- detect generation runaway conditions
- detect truncation
- account for streaming responses
- respond to VRAM pressure
- fail closed on unsafe overflow
- remain independently testable
- provide typed APIs to Context Engine and Model Gateway

The subsystem SHALL NOT:

- call remote tokenizers
- upload prompts for token counting
- invoke models directly
- approve tools
- execute tools
- mutate OS state
- fabricate provider usage
- silently exceed model context
- silently strip security instructions
- silently oversubscribe token capacity
- double-count replayed telemetry

---

# 24. OUTPUT QUALITY BAR

The generated `TOKEN_MANAGEMENT.md` must be:

- exhaustive
- implementation-ready
- deterministic
- security-conscious
- concurrency-safe
- model-aware
- hardware-aware
- internally consistent
- aligned with `idea.md`
- directly usable by another engineer

Do not produce:

- generic explanations
- marketing copy
- vague recommendations
- pseudo-code masquerading as implementation
- undefined classes in code examples
- placeholder methods
- `TODO`
- `TBD`
- `pass`
- unexplained magic constants
- cloud-dependent token accounting

Use:

- equations
- state machines
- sequence diagrams
- exact invariants
- Pydantic v2 schemas
- Python Protocols
- SQL transaction examples
- deterministic algorithms
- failure-state tables
- acceptance tests
- complete implementation snippets

throughout.

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
TOKEN_MANAGEMENT.md
```
