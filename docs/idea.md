# SyncNode - Technical Blueprint & Architecture

## 1. Executive Summary & Problem Space

### Problem Statement

SyncNode is a sovereign, on-premise, local multi-agent AI workbench for confidential knowledge work and controlled computer automation.

The precise problem is not simply “how to chat with a local LLM.” The problem is how to turn a natural-language goal into a **durable, observable, permissioned and verifiable workflow** that can operate on a real Windows workstation while sensitive data remains inside the organization's controlled environment.

Typical target workflows include:

- Reading local documents, spreadsheets and PDFs.
- Creating or modifying DOCX, PPTX, XLSX and other business artifacts.
- Searching organizational files and local knowledge.
- Launching and interacting with Windows applications such as Microsoft Word.
- Opening a browser, navigating a web application, drafting an email and attaching a locally generated artifact.
- Coordinating multiple specialized agents on a single goal.
- Using multimodal perception to understand screenshots, scans and visual UI state.
- Pausing for human approval before high-impact or external side effects.
- Verifying actual application/file state after every meaningful computer action.
- Recovering from application changes, missing controls, stale state, tool failures or unexpected results.

Existing assistants usually solve only part of this problem: conversational generation, isolated RAG, script-based automation, computer-use experimentation, or static RPA. SyncNode combines these concerns behind a single local orchestration runtime.

### Core Value Proposition

SyncNode provides a **model-agnostic, agent-oriented execution backend** where:

```text
Natural-language goal
        ↓
Context collection
        ↓
Intent extraction
        ↓
Task decomposition
        ↓
Agent spawning / routing
        ↓
Local model inference
        ↓
Tool execution
        ↓
Real computer interaction
        ↓
Observation + verification
        ↓
Recovery / re-planning
        ↓
Human approval where required
        ↓
Auditable result
```

The central engineering principle is:

> **The model proposes; deterministic infrastructure validates, authorizes, executes and verifies.**

The local model is therefore not granted unrestricted control over Windows, files, browsers or external side effects. It produces structured intent, plans, semantic actions and tool calls. SyncNode's runtime decides whether and how those requests can be executed.

### Target Audience & Consumers

**Primary users**

- Confidential enterprise knowledge workers.
- Engineers, analysts, operations teams and administrators.
- Government/public-sector teams.
- Organizations with air-gapped or restricted-network environments.
- Technical users who want a local autonomous workbench.

**Backend consumers**

- SyncNode Electron desktop client.
- Automated local workflows.
- Internal integration modules.
- Administrative tooling.
- Future internal APIs or organization-specific clients.

**Phase-1 deployment model**

A modular monolith running on a single Windows workstation or internal GPU server, with all core runtime dependencies local.

---

## 2. Requirements & Constraints

### Functional Requirements (FRs)

| ID | Requirement | Acceptance Condition |
|---|---|---|
| FR-01 | Accept user goals and create executable runs | `POST /api/v1/runs` creates a durable run and returns `run_id`. |
| FR-02 | Collect local execution context | Run captures relevant workspace, files, active application, UI state and policy context before planning. |
| FR-03 | Convert natural language to structured intent | Intent conforms to a versioned schema and rejects malformed or unsupported requests. |
| FR-04 | Generate executable task graphs | Planner produces ordered/dependent steps with agent, tool, input and verification requirements. |
| FR-05 | Dynamically spawn specialized agents | Agent registry resolves capabilities to runtime agent instances without hard-coded model dependencies. |
| FR-06 | Route inference to local models | Model registry selects an available local provider/model based on capability, hardware and policy. |
| FR-07 | Execute typed local tools | Tool calls are schema validated, policy checked, authorized and executed by deterministic code. |
| FR-08 | Control real Windows/browser applications | Computer runtime can observe and manipulate supported Windows applications and browser sessions using semantic automation with visual fallback. |
| FR-09 | Generate and modify business artifacts | DOCX/PPTX/XLSX/PDF/code workflows can create local output artifacts. |
| FR-10 | Maintain stepwise execution state | Every step has lifecycle state, timestamps, input/output references and retry metadata. |
| FR-11 | Verify results after actions | File, UI, application or semantic assertions can mark a step as verified or failed. |
| FR-12 | Support bounded recovery | Failed steps can retry, re-observe, re-route or trigger a re-plan with explicit attempt limits. |
| FR-13 | Require human approval for sensitive actions | External communication, destructive file operations and configured sensitive actions pause at an approval gate. |
| FR-14 | Stream live execution events | Client can subscribe to run events without polling the entire run state. |
| FR-15 | Record audit history | Security and execution-relevant events are immutable and correlate to run/step/tool IDs. |
| FR-16 | Support multimodal inference | Model adapter accepts text plus image observations where the selected local model supports vision. |
| FR-17 | Manage prompt/token budgets | Prompt construction enforces context limits, tool-definition limits, history summarization and per-call token budgets. |
| FR-18 | Maintain session/workflow memory | Successful workflow patterns and task context can be persisted independently of transient run state. |

### Non-Functional Requirements (NFRs)

These are Phase-1 engineering targets for a single-node deployment; they are targets, not measured claims.

| Category | Target |
|---|---|
| API latency | p95 < 150 ms for local CRUD/read endpoints excluding model/tool execution; p99 < 500 ms. |
| Run creation | p95 < 250 ms until durable `queued` response. |
| Event delivery | p95 < 250 ms from event creation to subscribed client for local SSE transport. |
| Tool dispatch overhead | p95 < 100 ms excluding the actual external operation. |
| Brain orchestration overhead | p95 < 200 ms between completed graph nodes when no model call is required. |
| Availability | 99.5% target for the local backend process while running; future HA target 99.9% when deployed redundantly. |
| Data durability | Every accepted run/approval/audit event must be durably committed before acknowledging success. |
| Consistency | Strong consistency for run state, approvals, authorization, tool permissions and artifacts metadata; eventual consistency allowed for search indexes and workflow analytics. |
| Event ordering | Per-run event order is monotonic by sequence number; cross-run global ordering is not required. |
| Throughput | Initial target: 20 run submissions/minute, 100 event writes/sec, 20 concurrent active agent steps on a capable internal server. |
| Persistence | No execution state is memory-only. Crash recovery must reconstruct active runs from durable state. |
| Recovery | No unbounded automatic retry loops. Each tool/step has explicit retry budget and failure policy. |
| Observability | 100% of runs have correlation ID, model call records, tool call records and terminal status. |
| Security | No model-generated action executes outside an allowlisted tool surface. |
| Offline operation | Core inference, file operations, RAG, execution and UI automation must function without public Internet access. |
| Determinism | Deterministic tool execution and verification must not rely on model-generated assertions alone. |

### Hard Constraints & Out of Scope

**Hard constraints**

- Runtime data is local/on-premise.
- Core workflows do not require public cloud AI APIs.
- Model provider is abstracted behind an adapter.
- Computer actions are mediated by a controlled execution layer.
- Sensitive external side effects require policy/approval.
- All high-risk actions are auditable.
- A workflow must fail closed when a target cannot be confidently resolved.

**Phase-1 out of scope**

- Multi-region deployment.
- Kubernetes-based distributed orchestration.
- Training a foundation model from scratch.
- Automatic model fine-tuning during production runs.
- Unrestricted autonomous web browsing across arbitrary sites.
- Unrestricted shell/root/administrator access.
- Automatic outbound email/message sending without an approval policy.
- Cloud-dependent embeddings, OCR or document storage.
- Fully automatic workflow learning that mutates production agent policies without review.
- Cross-user desktop control.
- Control of protected desktop/UAC/credential prompts.
- Autonomous handling of CAPTCHAs or anti-bot bypass.

---

## 3. High-Level Architecture & System Flow

### Architectural Style

**Recommended style: Modular Monolith + Event-Driven Internal Runtime.**

The first deployment should not be split into microservices. SyncNode needs tight coordination among the planner, agent runtime, tool policy, computer state, verifier and persistent graph state. A modular monolith minimizes distributed-systems failure modes while keeping module boundaries strict enough for later extraction.

The execution engine is event-driven internally, while external consumers use REST and Server-Sent Events (SSE).

**Why not microservices in Phase 1?**

- The primary deployment is one workstation/server.
- Most operations are low-latency in-process calls.
- Model inference and UI automation already introduce long-running operations; adding network hops would increase complexity without providing immediate value.
- Durable state, concurrency control and auditability are easier to reason about in one transaction boundary.

**Migration path:** extract model inference workers, knowledge ingestion, browser execution and heavy compute into separate processes/services only when CPU/GPU isolation, scale or organizational deployment demands it.

### Component Breakdown

#### 1. API Layer

Responsibilities:

- Authentication/session validation.
- Run lifecycle endpoints.
- Approval endpoints.
- Agent/model/tool discovery.
- Workspace and artifact metadata APIs.
- Event streaming.

#### 2. Brain / Orchestrator

Responsibilities:

- LangGraph state machine.
- Context assembly.
- Intent extraction.
- Task decomposition.
- Dynamic agent dispatch.
- Agent dependency handling.
- Re-planning.
- Run state transitions.

#### 3. Model Gateway

Responsibilities:

- Provider abstraction.
- Ollama integration.
- Model health/capability discovery.
- Model routing.
- Timeout/cancellation.
- Prompt/token budget enforcement.
- Structured output validation.
- Vision request packaging.
- Model telemetry.

Current deployment default should be configurable, for example `MODEL_ID=gemma4:e3b`; a larger Gemma variant can be selected when the target hardware supports it. The supplied environment already uses Ollama and a local Gemma 4 E3B deployment. fileciteturn6file0L11-L17

#### 4. Context Engine

Responsibilities:

- Current run context.
- Workspace context.
- Filesystem discovery.
- Active application/window context.
- UI Automation tree snapshots.
- Browser/DOM context.
- Relevant memory and knowledge retrieval.
- Context ranking and compaction.

#### 5. Agent Runtime

Responsibilities:

- Agent configuration resolution.
- Agent-specific system instructions.
- Tool permission filtering.
- Step execution.
- Result normalization.
- Agent lifecycle telemetry.

#### 6. Tool Registry

Responsibilities:

- Typed tool schemas.
- Capability declarations.
- Versioning.
- Permissions.
- Risk classification.
- Deterministic invocation.

#### 7. Execution Engine

Responsibilities:

- Validate action.
- Acquire required locks.
- Bring target application to required state.
- Invoke deterministic adapter.
- Capture observation.
- Return structured result.

#### 8. Computer Runtime

Responsibilities:

- Windows process/app lifecycle.
- Windows UI Automation.
- Keyboard/mouse fallback.
- Screenshots.
- Active window tracking.
- Clipboard.
- Browser control.
- Semantic target resolution.

Microsoft documents Windows UI Automation as a programmatic interface for discovering and manipulating UI elements across supported application frameworks, with element properties, control patterns and events. citeturn173198search2turn173198search5

#### 9. Document Runtime

Responsibilities:

- DOCX read/write through `python-docx`.
- XLSX through `openpyxl`.
- PPTX through `python-pptx`.
- PDF parsing/rendering through a local PDF library.
- Artifact hashing.
- Post-write verification.

#### 10. Browser Runtime

Responsibilities:

- Playwright-controlled Chromium session.
- Browser lifecycle.
- DOM/role-based locators.
- Navigation policy.
- Download/upload handling.
- Screenshot fallback.

Playwright recommends user-facing and accessibility-based locators such as role, label and text, which is appropriate for SyncNode's semantic browser-control layer. citeturn173198search1

#### 11. Policy / Approval Engine

Responsibilities:

- Risk classification.
- Allow/deny rules.
- Approval checkpoints.
- Per-tool authorization.
- External side-effect controls.
- Destructive-operation controls.

#### 12. Verification / Recovery Engine

Responsibilities:

- Postcondition checks.
- Application-state verification.
- Artifact validation.
- Retry policy.
- Re-observation.
- Re-planning.
- Terminal failure classification.

#### 13. Memory / Knowledge Layer

Responsibilities:

- Session context.
- Workflow memory.
- Enterprise knowledge.
- Vector retrieval.
- Structured metadata.
- Optional graph relationships.

#### 14. Audit / Telemetry Layer

Responsibilities:

- Structured event logging.
- Run traces.
- Model/token metrics.
- Tool telemetry.
- Approval history.
- Security events.

### Component Interaction (Text Diagram/Flow)

```text
Electron / Local Client
        |
        | HTTPS/localhost REST
        v
+-------------------------+
| FastAPI API             |
| Auth / Runs / Approval  |
+------------+------------+
             |
             v
+-------------------------+
| SyncNode Orchestrator   |
| LangGraph runtime       |
+------------+------------+
             |
      +------+-------+-------------------+----------------+
      |              |                   |                |
      v              v                   v                v
 Context         Intent/Plan        Model Gateway       Memory
 Engine              |                   |                |
      |              |                   v                |
      |              |              Ollama/local          |
      |              |              models                 |
      +--------------+------------------+-----------------+
                                     |
                                     v
                              Agent Runtime
                                     |
                                     v
                               Tool Registry
                                     |
                     +---------------+----------------+
                     |               |                |
                     v               v                v
                Documents       Computer Runtime   Sandbox
                     |               |
                     |         +-----+------+
                     |         |            |
                     |        UIA        Browser
                     |         |        Playwright
                     |         +-----+------+
                     |               |
                     +-------+-------+
                             v
                         Observation
                             |
                             v
                          Verifier
                         /        \
                       pass       fail
                        |           |
                        |     Recovery/Replan
                        |           |
                        +-----+-----+
                              |
                              v
                           Artifact
                              |
                              v
                         Audit / Events
                              |
                              v
                        SSE → Electron
```

### Primary Execution Sequence

```text
1. Authenticate user/session.
2. Create durable run.
3. Collect minimal relevant context.
4. Classify intent and constraints.
5. Generate structured task graph.
6. Validate plan against capability and policy constraints.
7. Spawn or dispatch agents.
8. Route each model call to an available local model/provider.
9. Build bounded prompt from task + relevant context + tools.
10. Execute tool/action request through the deterministic executor.
11. Capture real application/file/browser state.
12. Verify postconditions.
13. If verified, continue to the next dependency-ready step.
14. If failed, re-observe/retry/re-plan according to the retry policy.
15. If an approval gate is reached, persist the run in `WAITING_APPROVAL` and emit an event.
16. Resume only after approval/rejection.
17. Produce final artifacts and execution summary.
18. Persist audit and terminal status.
```

### Communication Protocols

| Protocol | Use | Rationale |
|---|---|---|
| REST/JSON | Electron → backend commands and state reads | Simple, explicit, debuggable. |
| SSE | Backend → Electron live run events | One-way streaming is sufficient and easier than WebSockets for the primary execution trace. |
| In-process Python calls | Brain → agent/tool modules | Avoid unnecessary network hops in modular monolith. |
| Optional local IPC | Future isolated browser/sandbox workers | Process isolation without requiring distributed networking. |
| Optional gRPC | Phase 2 extracted inference/execution workers | Useful only when process/service extraction becomes necessary. |
| Queue | Heavy, parallel or isolated work | Phase 1 can use a local durable task table + worker loop; Redis/Streams can be introduced later. |

---

## 4. Data Layer & Schema Architecture

### Storage Strategy

**Primary database: PostgreSQL for production-capable deployments; SQLite supported for local single-user development.**

PostgreSQL is preferred for:

- strong transactional semantics,
- concurrent writes,
- row-level locking,
- JSONB for evolving execution metadata,
- durable audit records,
- future multi-user support.

SQLite remains useful for development and lightweight offline packaging, provided that the same repository/service interfaces are maintained.

**Vector store:** Qdrant for scalable local vector retrieval; ChromaDB may be used for a lightweight prototype. Vector similarity is advisory only and can never authorize an action.

**Search:** PostgreSQL full-text search initially. A dedicated search engine is not needed in Phase 1.

**Object/file storage:** local managed workspace directories with content hashes and metadata stored in SQL. For server deployment, use a mounted internal storage volume rather than public cloud object storage.

**Cache:** Redis optional for hot state, distributed locks and event fan-out when multiple backend workers are introduced. Do not make Redis a single point of truth for run state.

### Logical Data Model

```text
Organization
  └── Users
       └── Sessions
            └── Runs
                 ├── Run Steps
                 │    ├── Agent Runs
                 │    ├── Tool Calls
                 │    ├── Observations
                 │    └── Approvals
                 ├── Artifacts
                 └── Audit Events

Agent Definitions
  ├── Tool Permissions
  └── Model Requirements

Model Profiles
  └── Providers

Knowledge Documents
  ├── Knowledge Chunks
  └── Embeddings / Vector IDs

Workflow Memories
  └── References to validated Runs / Artifacts
```

### Entity Relationship & Data Models

The following PostgreSQL-style DDL is the canonical Phase-1 logical schema.

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email TEXT NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'operator'
        CHECK (role IN ('admin', 'operator', 'reviewer', 'viewer')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, lower(email))
);
CREATE INDEX idx_users_org ON users(organization_id);

CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    access_token_hash TEXT NOT NULL UNIQUE,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    refresh_expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    device_name TEXT,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expiry ON sessions(expires_at);

CREATE TABLE model_profiles (
    id UUID PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    capabilities JSONB NOT NULL,
    context_window INTEGER,
    supports_vision BOOLEAN NOT NULL DEFAULT false,
    supports_tools BOOLEAN NOT NULL DEFAULT false,
    enabled BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 100,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, model_id)
);
CREATE INDEX idx_models_capabilities ON model_profiles USING GIN (capabilities);

CREATE TABLE agent_definitions (
    id UUID PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    capabilities JSONB NOT NULL,
    allowed_tools JSONB NOT NULL,
    model_requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_class TEXT NOT NULL DEFAULT 'normal'
        CHECK (risk_class IN ('normal', 'sensitive', 'external', 'destructive')),
    system_prompt TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tool_definitions (
    id UUID PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    capabilities JSONB NOT NULL,
    risk_class TEXT NOT NULL DEFAULT 'normal'
        CHECK (risk_class IN ('read', 'write', 'destructive', 'external')),
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE runs (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    task_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN (
            'queued','planning','running','waiting_approval',
            'recovering','completed','failed','cancelled'
        )),
    current_step_id UUID,
    parent_run_id UUID REFERENCES runs(id),
    policy_version TEXT NOT NULL,
    context_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    plan JSONB,
    result JSONB,
    error_code TEXT,
    error_message TEXT,
    attempt INTEGER NOT NULL DEFAULT 0,
    sequence_no BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_runs_user_created ON runs(user_id, created_at DESC);
CREATE INDEX idx_runs_org_status ON runs(organization_id, status);
CREATE INDEX idx_runs_parent ON runs(parent_run_id);

CREATE TABLE run_steps (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_key TEXT NOT NULL,
    sequence_no INTEGER NOT NULL,
    agent_key TEXT NOT NULL,
    action_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending','ready','running','waiting_approval',
            'retrying','succeeded','failed','skipped','cancelled'
        )),
    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,
    input JSONB NOT NULL DEFAULT '{}'::jsonb,
    output JSONB,
    verification JSONB,
    retry_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, step_key)
);
CREATE INDEX idx_steps_run_status ON run_steps(run_id, status);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    run_step_id UUID NOT NULL REFERENCES run_steps(id) ON DELETE CASCADE,
    agent_key TEXT NOT NULL,
    model_profile_id UUID REFERENCES model_profiles(id),
    status TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    input_context_hash TEXT,
    output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_runs_step ON agent_runs(run_step_id);

CREATE TABLE tool_calls (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    run_step_id UUID REFERENCES run_steps(id) ON DELETE SET NULL,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    tool_key TEXT NOT NULL,
    request JSONB NOT NULL,
    response JSONB,
    status TEXT NOT NULL
        CHECK (status IN ('requested','validated','approved','running','succeeded','failed','denied')),
    idempotency_key TEXT,
    risk_class TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, idempotency_key)
);
CREATE INDEX idx_tool_calls_run_created ON tool_calls(run_id, created_at);

CREATE TABLE approvals (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    run_step_id UUID NOT NULL REFERENCES run_steps(id) ON DELETE CASCADE,
    action_summary TEXT NOT NULL,
    risk_class TEXT NOT NULL,
    requested_by UUID NOT NULL REFERENCES users(id),
    decided_by UUID REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','approved','rejected','expired')),
    expires_at TIMESTAMPTZ,
    decision_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at TIMESTAMPTZ
);
CREATE INDEX idx_approvals_pending ON approvals(status, created_at);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    run_step_id UUID REFERENCES run_steps(id) ON DELETE SET NULL,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created'
        CHECK (status IN ('created','verified','invalid','deleted')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, sha256)
);
CREATE INDEX idx_artifacts_run ON artifacts(run_id);
CREATE INDEX idx_artifacts_sha256 ON artifacts(sha256);

CREATE TABLE computer_observations (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    run_step_id UUID REFERENCES run_steps(id) ON DELETE SET NULL,
    application TEXT,
    process_name TEXT,
    window_title TEXT,
    ui_tree JSONB,
    browser_state JSONB,
    screenshot_path TEXT,
    screenshot_sha256 TEXT,
    observation_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_computer_obs_run_created ON computer_observations(run_id, created_at);

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT,
    sha256 TEXT NOT NULL,
    title TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    ingestion_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, sha256)
);

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    vector_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX idx_knowledge_chunks_doc ON knowledge_chunks(document_id);

CREATE TABLE workflow_memories (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    source_run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
    workflow_key TEXT NOT NULL,
    trigger_pattern TEXT NOT NULL,
    workflow JSONB NOT NULL,
    validation_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (validation_status IN ('candidate','verified','retired')),
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_workflow_memory_org_key ON workflow_memories(organization_id, workflow_key);

CREATE TABLE audit_events (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
    run_step_id UUID REFERENCES run_steps(id) ON DELETE SET NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    trace_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_run_created ON audit_events(run_id, created_at);
CREATE INDEX idx_audit_trace ON audit_events(trace_id);
```

### State Machines

#### Run State Machine

```text
QUEUED
  |
  v
PLANNING
  |
  v
RUNNING <------------------+
  |                         |
  +--> WAITING_APPROVAL ----+
  |          |
  |          +--> REJECTED --> FAILED
  |
  +--> RECOVERING --> RUNNING
  |
  +--> COMPLETED
  |
  +--> FAILED
  |
  +--> CANCELLED
```

Rules:

- `COMPLETED` and `FAILED` are terminal.
- `WAITING_APPROVAL` must have at least one pending approval row.
- `RECOVERING` requires a recorded failure or verification mismatch.
- Cancellation is cooperative: the current tool must receive a cancellation signal, then the run is marked `cancelled` only after cleanup completes.

#### Step State Machine

```text
PENDING → READY → RUNNING → SUCCEEDED
                       |
                       +→ WAITING_APPROVAL → RUNNING
                       |
                       +→ RETRYING → RUNNING
                       |
                       +→ FAILED
                       |
                       +→ SKIPPED
                       |
                       +→ CANCELLED
```

#### Computer Action State Machine

```text
PROPOSED
   ↓
SCHEMA_VALIDATED
   ↓
TARGET_RESOLVED
   ↓
POLICY_ALLOWED
   ↓
[APPROVAL REQUIRED?]
   ├── yes → WAITING_APPROVAL → APPROVED
   └── no  ───────────────────┘
                ↓
             EXECUTING
                ↓
            OBSERVING
                ↓
            VERIFYING
          /           \
      PASSED          FAILED
        |                |
        v                v
     COMPLETE       RECOVER / RETRY / FAIL
```

### Caching Layer

**Pattern:** cache-aside.

**Never cache as authoritative state:** approvals, run status, authorization decisions, artifact metadata or audit records.

Recommended keys:

```text
syncnode:model:{provider}:{model_id}
syncnode:agent:{agent_key}:{version}
syncnode:tool:{tool_key}:{version}
syncnode:context:{user_id}:{workspace_hash}
syncnode:knowledge:{org_id}:{query_hash}
syncnode:ui:{machine_id}:{window_hash}
syncnode:lock:{resource_key}
```

TTL guidance:

- Model metadata: 5–15 minutes.
- Agent/tool definitions: 5 minutes or explicit version invalidation.
- Context snapshots: 30–120 seconds.
- UI observation cache: seconds, never minutes.
- Knowledge search result cache: 1–5 minutes for stable documents.

Invalidate immediately when:

- model registry changes,
- agent/tool version changes,
- permissions change,
- workspace files are modified,
- current application/window changes,
- policy changes.

---

## 5. API Design & Core Contracts

### Standard Error Envelope

All non-2xx responses use:

```json
{
  "error": {
    "code": "RUN_NOT_FOUND",
    "message": "The requested run does not exist.",
    "details": {},
    "trace_id": "01JXYZ..."
  }
}
```

### 1. `POST /api/v1/auth/login`

- **Purpose & Access:** Public local-authentication endpoint.
- **Request Headers & Parameters / Body:**

```json
{
  "email": "operator@example.local",
  "password": "********",
  "device_name": "SyncNode Desktop"
}
```

- **Success Response (2xx):** `200 OK`

```json
{
  "data": {
    "user": {
      "id": "uuid",
      "display_name": "Operator",
      "role": "operator"
    },
    "access_token": "opaque-short-lived-token",
    "expires_in": 600,
    "refresh_token": "opaque-rotating-token"
  }
}
```

- **Error Responses (4xx/5xx):**
  - `401 AUTH_INVALID`
  - `423 USER_DISABLED`
  - `429 AUTH_RATE_LIMITED`
- **Rate Limiting & Throttling Rules:** Token bucket, 5 failed login attempts/minute/IP+account tuple, temporary backoff after repeated failures.

### 2. `POST /api/v1/runs`

- **Purpose & Access:** Authenticated operator/reviewer/admin; creates a new AI workflow.
- **Request Headers & Parameters / Body:**

Headers:

```text
Authorization: Bearer <access_token>
Idempotency-Key: <uuid>
X-Request-ID: <client-request-id>
```

Body:

```json
{
  "task": "Write a story about a tree, create a Word document, then draft an email with the document attached.",
  "workspace_id": "workspace-local",
  "mode": "autonomous_with_approval",
  "constraints": {
    "allow_external_send": true,
    "require_approval_for": ["external_send", "destructive"]
  },
  "attachments": []
}
```

- **Success Response (2xx):** `202 Accepted`

```json
{
  "data": {
    "run_id": "uuid",
    "status": "queued",
    "trace_id": "trace-uuid"
  }
}
```

- **Error Responses (4xx/5xx):**
  - `400 INVALID_TASK`
  - `401 UNAUTHENTICATED`
  - `403 POLICY_DENIED`
  - `409 IDEMPOTENCY_CONFLICT`
  - `429 RUN_RATE_LIMITED`
  - `503 BRAIN_UNAVAILABLE`
- **Rate Limiting & Throttling Rules:** Token bucket per user; default 10 run creations/minute with burst 3. Heavy compute is separately concurrency-limited.

### 3. `GET /api/v1/runs/{run_id}`

- **Purpose & Access:** Authenticated users with access to the run.
- **Request Headers & Parameters / Body:**

```text
Authorization: Bearer <access_token>
```

Optional query parameters:

```text
?include=plan,steps,artifacts,approval
```

- **Success Response (2xx):** `200 OK`

```json
{
  "data": {
    "run_id": "uuid",
    "status": "waiting_approval",
    "task": "Write a story about a tree...",
    "plan": {
      "version": 1,
      "steps": 7
    },
    "current_step": "email.send",
    "artifacts": [
      {
        "id": "uuid",
        "filename": "tree_story.docx",
        "status": "verified"
      }
    ],
    "pending_approval": {
      "id": "uuid",
      "action": "send_external_email"
    }
  }
}
```

- **Error Responses (4xx/5xx):** `401`, `403`, `404 RUN_NOT_FOUND`, `500 RUN_READ_FAILED`.
- **Rate Limiting & Throttling Rules:** Fixed window, 120 requests/minute/user; cached reads may be served from memory.

### 4. `GET /api/v1/runs/{run_id}/events`

- **Purpose & Access:** Authenticated run participant.
- **Request Headers & Parameters / Body:**

```text
Authorization: Bearer <access_token>
Accept: text/event-stream
Last-Event-ID: <sequence-no>
```

- **Success Response (2xx):** `200 OK` SSE stream.

Example event:

```text
event: tool_call
id: 184
retry: 3000
data: {"run_id":"uuid","step_id":"uuid","tool":"computer.open_application","status":"started"}
```

- **Error Responses (4xx/5xx):** `401`, `403`, `404`, `409 EVENT_STREAM_NOT_RESUMABLE` if the requested sequence was compacted beyond retention.
- **Rate Limiting & Throttling Rules:** Maximum 3 concurrent event streams/session; reconnect permitted with `Last-Event-ID`.

### 5. `POST /api/v1/runs/{run_id}/approvals/{approval_id}`

- **Purpose & Access:** Authenticated reviewer/operator/admin according to policy; performs explicit human approval or rejection.
- **Request Headers & Parameters / Body:**

```json
{
  "decision": "approved",
  "reason": "Verified recipient and attachment."
}
```

- **Success Response (2xx):** `200 OK`

```json
{
  "data": {
    "approval_id": "uuid",
    "status": "approved",
    "run_status": "running"
  }
}
```

- **Error Responses (4xx/5xx):** `401`, `403`, `404`, `409 APPROVAL_ALREADY_DECIDED`, `410 APPROVAL_EXPIRED`.
- **Rate Limiting & Throttling Rules:** Fixed window, 30 decisions/minute/user.

### Additional Operational Endpoints

```text
GET  /api/v1/health
GET  /api/v1/livez
GET  /api/v1/readyz
GET  /api/v1/models
GET  /api/v1/agents
GET  /api/v1/tools
GET  /api/v1/workspace/context
POST /api/v1/computer/observe
POST /api/v1/runs/{run_id}/cancel
```

---

## 6. Security, Authentication & Authorization

### Auth Flow

**Recommended token architecture: opaque server-tracked sessions.**

```text
Login
  ↓
Password verification
  ↓
Create session row
  ↓
Short-lived access token (10 min)
  ↓
Rotating refresh token (30 days default)
  ↓
Refresh request
  ↓
Revoke old refresh token
  ↓
Issue new access + refresh token pair
```

For Electron:

- Store refresh token in Windows Credential Manager/secure OS storage.
- Keep access token in process memory where possible.
- Never store bearer tokens in plaintext project files.
- Invalidate all sessions on password reset or administrator revocation.

### Access Control

Use RBAC initially with policy attributes layered on top for action risk.

| Role | View Runs | Create Runs | Approve External | Manage Agents | Manage Models | Manage Policies |
|---|---:|---:|---:|---:|---:|---:|
| viewer | Yes | No | No | No | No | No |
| operator | Yes | Yes | Configurable | No | No | No |
| reviewer | Yes | Yes | Yes | No | No | No |
| admin | Yes | Yes | Yes | Yes | Yes | Yes |

Additional ABAC checks:

```text
organization_id matches
AND
workspace access allowed
AND
tool risk allowed for user
AND
current run policy allows action
AND
application/session is owned by the current OS user
```

### Data Protection

- Encrypt persistent secrets using OS-managed secret storage where possible.
- Encrypt PostgreSQL storage volumes when provided by the deployment host.
- Use TLS for remote internal-server mode; localhost can use loopback-only HTTP when the threat model explicitly permits it.
- Never log passwords, tokens, raw email bodies containing secrets, or raw authorization headers.
- Redact sensitive tool arguments in logs based on tool schema.
- Use parameterized SQL only.
- Validate all file paths against an allowed workspace root to prevent path traversal.
- Canonicalize and validate paths before access.
- Do not allow arbitrary URLs from model output without SSRF policy checks.
- Restrict browser navigation to configured domains for automation profiles.
- Sanitize generated HTML/Markdown before rendering inside Electron.
- Use strict CSP in Electron.
- Disable arbitrary `nodeIntegration` in renderer processes.
- Keep shell execution behind an allowlist/sandbox.
- Do not allow model-generated PowerShell to execute with administrator privileges by default.

### External Side-Effect Policy

Actions are classified as:

```text
READ
WRITE_LOCAL
DESTRUCTIVE_LOCAL
EXTERNAL_COMMUNICATION
SYSTEM_ADMIN
```

Default behavior:

- `READ`: automatic.
- `WRITE_LOCAL`: automatic inside approved workspace.
- `DESTRUCTIVE_LOCAL`: approval required.
- `EXTERNAL_COMMUNICATION`: approval required.
- `SYSTEM_ADMIN`: denied in Phase 1.

For the canonical email workflow, SyncNode may automatically create a draft and attach the local artifact, but the final Send operation remains approval-gated.

---

## 7. Asynchronous Jobs, Queues & Event Processing

### Queue/Broker Architecture

Phase 1 uses a durable SQL-backed execution queue plus the LangGraph runtime. This avoids introducing a mandatory broker into the first single-node deployment.

Logical queues:

```text
runs.planning
runs.execution
runs.verification
runs.recovery
knowledge.ingestion
artifacts.verification
notifications.internal
```

Phase 2 can move hot queues/event fan-out to Redis Streams or another on-prem broker if multiple worker processes are required.

### Event Envelope

Every internal event uses:

```json
{
  "event_id": "uuid",
  "event_type": "tool_call.started",
  "event_version": 1,
  "trace_id": "trace-uuid",
  "run_id": "run-uuid",
  "step_id": "step-uuid",
  "agent_id": "computer-agent",
  "occurred_at": "2026-09-18T12:00:00Z",
  "sequence_no": 183,
  "payload": {}
}
```

### Background Tasks

- Workflow execution.
- Knowledge ingestion.
- OCR/parsing.
- Embedding generation.
- Artifact verification.
- Thumbnail/screenshot generation.
- Memory extraction from verified runs.
- Cleanup of expired temporary files.
- Session expiration.
- Audit retention/export.

### Reliability

Retry policy:

```text
attempt 1 → 250 ms + jitter
attempt 2 → 1 s + jitter
attempt 3 → 4 s + jitter
then → recovery/failure policy
```

Use exponential backoff with jitter for transient infrastructure failures. Never automatically retry destructive/external side effects unless the operation has a documented idempotency strategy.

### Idempotency

All mutation endpoints accept `Idempotency-Key` where appropriate.

Tool idempotency examples:

```text
create_document
  key = run_id + step_id + logical_artifact_name

send_email
  key = approval_id + normalized_message_hash

write_file
  key = run_id + step_id + destination_path + content_hash
```

A duplicate request must return the original operation result rather than execute a second side effect.

### Dead-Letter Handling

Failed durable jobs are moved to a dead-letter state when:

- retry budget is exhausted,
- schema incompatibility persists,
- an adapter reports unsupported application state,
- policy denies every available recovery strategy.

DLQ records remain queryable and are linked to the originating run/step.

---

## 8. Reliability, Edge Cases & Failure Modes

### Concurrency & Race Conditions

**Database locking**

Use optimistic locking for most run rows via `sequence_no` or `updated_at` comparison.

Example:

```sql
UPDATE runs
SET status = 'running', sequence_no = sequence_no + 1
WHERE id = $1
  AND sequence_no = $2;
```

If affected rows = 0, reload state and retry the transition.

**Pessimistic locking**

Use `SELECT ... FOR UPDATE` when resolving approval decisions and terminal run transitions.

**Distributed/local locks**

Phase 1: PostgreSQL advisory locks are sufficient for single-node/multi-process coordination.

Phase 2: Redis distributed locks may be introduced if workers span processes/hosts.

### Failure Handling

#### Model unavailable

```text
Model call
  ↓
health check fails
  ↓
try configured fallback model
  ↓
if no compatible model
  ↓
WAITING/FAILED with MODEL_UNAVAILABLE
```

Never silently switch to a cloud model.

#### Tool timeout

- Cancel the tool if safe.
- Capture observation.
- Mark `TOOL_TIMEOUT`.
- Retry only when operation classification allows.

#### UI target missing

```text
UIA lookup
  ↓
not found
  ↓
refresh UI tree
  ↓
re-resolve
  ↓
vision fallback if policy permits
  ↓
if confidence insufficient → STOP
```

No blind coordinate click is allowed after target-resolution failure.

#### Application closes unexpectedly

- Detect process exit.
- Capture last observation.
- Compare desired state to persistent task state.
- Relaunch only if the agent policy permits application restart.
- Re-open the required artifact if safe.
- Verify before continuing.

#### Browser navigation changes

- Re-resolve by role/text/label rather than DOM index.
- Check origin and allowed domain.
- If page is unexpected, stop and request recovery.

Playwright's locator model is designed to resolve elements at interaction time and supports user-facing role/label selectors, which reduces dependence on brittle DOM coordinates. citeturn173198search1

#### Vision ambiguity

If confidence is below the tool's configured threshold:

```text
DO NOT ACT
       ↓
collect richer observation
       ↓
UIA/DOM lookup
       ↓
second local model call if allowed
       ↓
if still ambiguous → human review / failure
```

#### Context overflow

- Drop stale observations first.
- Summarize completed history.
- Keep current plan and pending verifications intact.
- Keep only tool schemas required by the current agent.
- Refuse execution if the model cannot receive the minimum required context safely.

#### Crash recovery

On backend startup:

```text
find runs where status IN (planning,running,recovering,waiting_approval)
        ↓
validate latest checkpoint
        ↓
reconstruct graph state
        ↓
mark in-flight tool calls as UNKNOWN
        ↓
re-observe before any retry
        ↓
resume or fail safely
```

Never automatically repeat a possibly completed external side effect after a crash without checking its postcondition/idempotency state.

### Boundary Cases

#### Large data surge

- Apply per-run file-size limits.
- Stream large file processing instead of loading entire files into memory.
- Chunk document ingestion.
- Cap screenshot history.
- Use artifact references instead of repeatedly embedding entire documents.

#### Network partitions

Core local workflows should continue when the public network disappears. Internal remote-server mode must distinguish local runtime failure from client connectivity failure.

#### Webhook replay

Phase 1 external webhooks are optional. Any future inbound webhook must use:

```text
signature verification
+ timestamp tolerance
+ idempotency key
+ replay cache
```

#### Clock drift

- Use server timestamps as authoritative.
- Store timezone-aware `TIMESTAMPTZ`.
- Do not derive policy expiry exclusively from client time.

#### File replaced during execution

Compare SHA-256/hash and modification metadata before writing or attaching. If source content changes unexpectedly, invalidate the plan step and re-observe.

#### User manually interacts with the computer during autonomous execution

The computer runtime should detect unexpected focus/window changes. Default behavior:

```text
unexpected human interaction
        ↓
freeze current autonomous action
        ↓
re-observe
        ↓
reconcile state
        ↓
continue only if safe
```

#### Protected desktop / UAC / credential dialogs

Phase 1: stop and request human intervention. SyncNode must not attempt to defeat OS privilege boundaries.

---

## 9. Observability & Operational Readiness

### Structured Logging

Every log line is JSON.

Example:

```json
{
  "timestamp": "2026-09-18T12:00:00.123Z",
  "level": "INFO",
  "service": "syncnode-backend",
  "module": "execution",
  "event": "tool_call.completed",
  "trace_id": "trace-uuid",
  "run_id": "run-uuid",
  "step_id": "step-uuid",
  "agent_id": "computer-agent",
  "tool": "computer.click_control",
  "status": "succeeded",
  "duration_ms": 142,
  "error_code": null
}
```

### Telemetry & Metrics

#### Golden Signals

**Latency**

- API p50/p95/p99.
- Model time-to-first-token.
- Model total latency.
- Tool latency.
- UIA resolution latency.
- Browser action latency.
- Verification latency.

**Traffic**

- Runs/minute.
- Agent dispatches/minute.
- Tool calls/minute.
- Model calls/minute.
- Screenshots/minute.

**Errors**

- Failed runs.
- Tool failures.
- Verification failures.
- Model failures.
- Policy denials.
- Human rejections.
- Browser/application adapter failures.

**Saturation**

- GPU memory.
- CPU utilization.
- RAM utilization.
- Disk usage.
- Queue depth.
- Active run count.
- Active computer sessions.

### AI-Specific Metrics

Every model call should record:

```text
model_id
provider
capability
prompt_tokens
completion_tokens
total_tokens
latency_ms
model_load_ms when available
context_hash
vision_image_count
tool_definition_count
structured_output_valid
retry_count
```

The backend should expose **decision summaries and execution traces**, not depend on raw hidden model reasoning as an authorization mechanism.

### Execution Trace

Example:

```text
[12:02:01] RUN CREATED
[12:02:02] CONTEXT COLLECTED
[12:02:03] INTENT CLASSIFIED
[12:02:04] PLAN CREATED (7 steps)
[12:02:05] WRITER AGENT SPAWNED
[12:02:07] GEMMA MODEL CALL COMPLETE
[12:02:09] DOCX CREATED
[12:02:10] ARTIFACT VERIFIED
[12:02:11] COMPUTER AGENT SPAWNED
[12:02:12] WORD LAUNCH REQUESTED
[12:02:14] WORD WINDOW DETECTED
[12:02:15] UI TARGET RESOLVED
[12:02:16] ACTION EXECUTED
[12:02:17] SCREEN OBSERVED
[12:02:18] POSTCONDITION VERIFIED
[12:02:21] EMAIL DRAFT READY
[12:02:22] APPROVAL REQUIRED
[12:02:22] RUN PAUSED
```

### Health Checks

`GET /livez`

Returns success if the process/event loop is alive.

`GET /readyz`

Returns ready only when:

- DB connection is healthy.
- Model provider is reachable locally or marked explicitly unavailable but not required for the requested readiness profile.
- workspace root is accessible.
- tool registry is loaded.
- policy registry is loaded.
- required encryption/secret storage is available.

### Restart Criteria

Restart only after:

- repeated event-loop stalls,
- unrecoverable memory pressure,
- fatal initialization failure,
- deadlocked execution worker.

Before restart:

- persist current run checkpoint,
- mark in-flight external side effects `UNKNOWN` when necessary,
- emit a shutdown audit event.

---

## 10. Execution Roadmap & Tech Stack Recommendation

### Recommended Tech Stack

| Layer | Recommendation | Rationale |
|---|---|---|
| Language | Python 3.12+ | Strong local AI/tooling ecosystem and natural fit for LangGraph, FastAPI and document libraries. |
| API | FastAPI | Lightweight typed REST backend and straightforward SSE support. |
| Orchestration | LangGraph | Stateful graph execution, checkpointing, dynamic routing and human-in-the-loop patterns. |
| Model integration | LangChain + provider adapters | Standardized tool/model abstractions without coupling the core graph to one vendor. |
| Local inference | Ollama first | Simple local provider boundary; current environment already uses it. fileciteturn6file0L11-L17 |
| Default model | Configurable Gemma 4 local model | Multimodal/agent-capable local reasoning path; exact tag remains deployment-configurable. |
| Primary DB | PostgreSQL | Transactions, JSONB, concurrency and audit durability. |
| Dev DB | SQLite | Zero-infrastructure local development. |
| Vector DB | Qdrant | Local vector retrieval with clear separation from authorization state. |
| Cache/locks | Redis, Phase 2 | Hot state, distributed locks and event fan-out after worker extraction. |
| Documents | python-docx / openpyxl / python-pptx / local PDF parser | Deterministic office artifact manipulation. |
| Windows automation | Windows UI Automation + Python adapter | Semantic application control and UI inspection. Microsoft's API exposes an accessibility/control tree and control patterns for programmatic interaction. citeturn173198search2turn173198search7 |
| Browser automation | Playwright | Semantic locators, auto-waiting and reliable browser interactions. citeturn173198search1 |
| Vision | Local multimodal model through model gateway | Screenshot/document perception without a cloud dependency. |
| OCR | PaddleOCR, local | Local scanned-document extraction. |
| Sandbox | Restricted Python subprocess/container profile | Controlled code execution without unrestricted host access. |
| Frontend | Electron + React + TypeScript | Native desktop UX, local system integration and future live execution workbench. |
| UI component base | shadcn/ui + Radix | Accessible primitives and owned visual system. |
| Workflow graph UI | React Flow | Direct mapping of backend task graph into visible execution topology. |
| Testing | pytest + httpx + Playwright + deterministic tool fixtures | Unit, API, browser and integration coverage. |
| Observability | OpenTelemetry-compatible traces + JSON logging + Prometheus-compatible metrics | Run-level and model/tool telemetry. |
| CI/CD | GitHub Actions | Automated lint/test/build/release pipeline. |
| Packaging | PyInstaller or equivalent backend bundle + Electron installer | Offline workstation installation. |

### Phase 1 (MVP/Foundation): 2-3 week critical path deliverables

#### Week 1 — Brain + Backend Core

```text
1. Repository/module structure
2. FastAPI application
3. PostgreSQL/SQLite repository layer
4. Ollama model adapter
5. Model registry
6. Pydantic schemas
7. Prompt builder + token budget manager
8. LangGraph state
9. Intent analyzer
10. Planner
11. Agent registry
12. Tool registry
13. Run persistence
14. Event bus + SSE
15. Basic auth/session layer
```

**Definition of done:**

```text
POST /runs
  ↓
Gemma/Ollama
  ↓
structured intent
  ↓
structured plan
  ↓
agent selected
  ↓
tool selected
  ↓
result persisted
  ↓
SSE trace visible
```

#### Week 2 — Real Execution

Implement the first genuine vertical slice:

```text
User:
"Write a story about a tree and create a Word document."

Gemma
 ↓
Writer Agent
 ↓
create_docx
 ↓
save artifact
 ↓
re-open/read
 ↓
verify
```

Then implement:

```text
Computer Agent
 ↓
launch Microsoft Word
 ↓
observe window
 ↓
UIA target resolution
 ↓
click/type
 ↓
save
 ↓
observe again
 ↓
verify
 ↓
close Word
```

Then:

```text
Browser Agent
 ↓
launch Chrome
 ↓
open configured mail site
 ↓
create draft
 ↓
find local artifact
 ↓
attach
 ↓
verify attachment
 ↓
WAITING_APPROVAL
```

#### Week 3 — Hardening + Golden Integration Test

Add:

- bounded retries,
- recovery/re-planning,
- approval gates,
- crash recovery,
- token telemetry,
- model fallback selection,
- computer-state interruption detection,
- artifact hashing,
- audit export,
- deterministic integration fixtures.

### Golden End-to-End Acceptance Test

The backend must be able to execute and report the following flow:

```text
USER GOAL
"Write a story about a tree and send it to Rahul."

1. Understand request
2. Build plan
3. Spawn Writer Agent
4. Generate story locally
5. Create tree_story.docx
6. Verify artifact
7. Spawn Computer Agent
8. Open Microsoft Word on the real desktop
9. Observe Word window
10. Locate editor semantically
11. Insert/write content
12. Save document
13. Verify saved state
14. Close Word
15. Open Chrome
16. Navigate to approved mail application
17. Create draft
18. Find tree_story.docx from local workspace
19. Attach document
20. Verify attachment is visible
21. Prepare recipient/body/subject
22. Present floating approval request
23. WAIT
24. User approves Send
25. Re-observe mail UI
26. Execute Send
27. Verify successful send through observable application state
28. Mark run COMPLETED
29. Persist complete trace/audit
```

**The test is successful only when actual Windows/application state changes and the verifier can prove the postconditions.** A model response claiming success is not sufficient evidence.

### Phase 2 (Scale & Hardening)

The next horizon should add:

- Redis Streams or equivalent local broker.
- Separate model workers and GPU-aware scheduling.
- Separate browser/computer worker process.
- Read/write splitting where deployment size warrants it.
- Qdrant-backed enterprise RAG at scale.
- OCR/vision preprocessing workers.
- Fine-grained organizational policy packs.
- Agent versioning and signed configurations.
- Workflow-memory promotion from verified runs.
- Hardware-aware model benchmarking and routing.
- Internal multi-user workspaces.
- Process isolation for risky tools.
- Event replay and deterministic run simulation.
- Backpressure and queue-depth controls.
- Offline package/update mechanism.
- Full Electron system-tray lifecycle and emergency stop.

### Performance Tuning Priorities

1. Reduce unnecessary model calls.
2. Keep tool schemas agent-specific.
3. Summarize stale context instead of carrying full history.
4. Reuse model instances where the runtime allows.
5. Keep screenshots only when they contribute to decisions or verification.
6. Cache immutable model/agent/tool metadata.
7. Move heavy OCR/embedding/file parsing off the API event loop.
8. Separate computer-control sessions from general backend concurrency limits.
9. Measure prompt tokens and execution latency per step.
10. Treat verification as a first-class latency budget rather than an afterthought.

### Final Architecture Contract

SyncNode should preserve the following invariant throughout implementation:

```text
               AI / ML
                 |
        proposes intent/plan/action
                 |
                 v
       Schema + Semantic Validation
                 |
                 v
              Policy
                 |
                 v
        Human Approval if required
                 |
                 v
        Deterministic Execution
                 |
                 v
         Real System / Computer
                 |
                 v
             Observation
                 |
                 v
             Verification
                 |
           +-----+-----+
           |           |
         PASS         FAIL
           |           |
           v           v
       Continue    Recover/Replan
           |           |
           +-----+-----+
                 |
                 v
             Audit/Trace
```

The architecture is therefore **not “Gemma controls Windows.”** It is:

```text
Local model
    +
Stateful orchestration
    +
Specialized agents
    +
Context / memory
    +
Typed tools
    +
Windows UIA / browser runtime
    +
Vision fallback
    +
Policy / human approval
    +
Verification / recovery
    +
Durable audit
    =
SyncNode
```

The backend must be considered complete only when this contract is observable through APIs and the golden end-to-end test can be executed against real local applications rather than simulated mocks.
