# SyncNode Frontend — AGENTS.md

## Agent Operating Contract

You are an implementation agent working on the **SyncNode Electron frontend**.

Your job is to make the frontend production-ready, integrated, polished, and complete.

Your operating rule is:

> **Read first. Inspect second. Implement third. Validate last. Never invent backend behavior.**

The application lives at:

```text
C:\syncnode\frontend
```

The backend lives at:

```text
C:\syncnode\backend
```

The frontend must consume the backend but **must not modify it**.

---

# 1. NON-NEGOTIABLE SCOPE

## You may modify

Only frontend/Electron/frontend-documentation/test assets that are explicitly part of the frontend task.

Normal scope:

```text
frontend/**
```

## You must not modify

```text
backend/**
```

and must not change:

- backend Python files
- backend API behavior
- backend endpoints
- backend SSE events
- LangGraph
- model routing
- execution tools
- computer runtime
- verification/recovery implementation
- database implementation
- backend configuration
- backend test expectations

Reading backend code is allowed and encouraged.

Running the backend is allowed.

Editing backend is not allowed.

If a backend limitation appears, use the current documented contract or report the limitation instead of quietly changing backend code.

---

# 2. REQUIRED SOURCE TREE RECONNAISSANCE

Start every substantial frontend task by inspecting:

```text
C:\syncnode
C:\syncnode\frontend
C:\syncnode\frontend\docs
```

Inspect at least:

```text
frontend/package.json
frontend/docs/ELECTRON_ARCHITECTURE.md
frontend/docs/FRONTEND_MASTER.md
frontend/docs/FRONTEND_API_INTEGRATION.md
frontend/docs/FRONTEND_SSE_STATE_MODEL.md
frontend/docs/FRONTEND_AGENT_TIMELINE.md
frontend/docs/FRONTEND_SCREEN_SPEC.md
frontend/docs/FRONTEND_APPROVAL_FLOW.md
frontend/docs/FRONTEND_ARTIFACT_EVIDENCE.md
frontend/docs/FRONTEND_UI_DESIGN_SYSTEM.md
```

Then inspect the existing source tree before creating new files.

---

# 3. BACKEND DOCUMENTATION TO READ

Read the backend architecture documents only to understand the product and contracts:

```text
docs/01_idea.md
docs/02_AI_BRAIN.md
docs/03_MODEL_GATEWAY.md
docs/04_PROMPT_CONTEXT_ENGINE.md
docs/05_PROMPT_TOKEN_MANAGEMENT.md
docs/06_PROMPT_INTENT_ENGINE.md
docs/07_PROMPT_PLANNER.md
docs/08_PROMPT_AGENT_REGISTRY_SPAWNER.md
docs/09_PROMPT_MODEL_ROUTER.md
docs/10_VISION_MULTIMODAL.md
docs/11_TOOL_REGISTRY.md
docs/12_COMPUTER_CONTROL.md
docs/13_DOCUMENT_FILE_AUTOMATION.md
docs/14_LOCAL_KNOWLEDGE_RAG.md
docs/15_WORKFLOW_EXECUTION_LANGGRAPH.md
docs/16_VERIFICATION_RECOVERY_AUDIT.md
docs/END_TO_END_VERIFIER_WORKFLOW.md
```

Also inspect relevant final/audit/context documentation when present.

Machine-readable contracts take priority for exact payloads:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

---

# 4. PRODUCT CONTEXT

SyncNode is a sovereign on-premise AI workbench.

Its fundamental workflow is:

```text
Observe
→ Understand
→ Retrieve
→ Plan
→ Policy
→ Approval when required
→ Execute
→ Verify
→ Recover/Replan
→ Audit
→ Remember
```

The frontend is the user's control and observability surface for this workflow.

It is not merely a chat application.

It is not merely a dashboard.

It is not merely RPA.

It is a desktop AI workbench with:

- runs
- agents
- tools
- context/RAG
- computer operation evidence
- verification
- recovery
- artifacts
- approvals
- audit

---

# 5. UI NORTH STAR

Build a **premium monochrome editor-like desktop application**.

Visual references may include the ergonomics of:

- OpenCode
- VS Code
- Zed
- Cursor
- Raycast
- modern Vercel/Geist tooling
- modern AI IDEs

Use those references for:

- compactness
- information hierarchy
- keyboard-first interaction
- split panes
- inspectors
- command palettes
- technical typography
- dense timelines

Do not copy their branding or layout literally.

The product should still feel unmistakably SyncNode.

---

# 6. DESIGN SYSTEM RULES

Primary authority:

```text
frontend/docs/FRONTEND_UI_DESIGN_SYSTEM.md
```

Base stack:

```text
React
TypeScript
Tailwind
shadcn/ui
Radix/Base UI
Lucide
```

Use selected patterns from:

```text
shadcn blocks
React Bits
Aceternity UI
Magic UI
DaisyUI
Vercel / Geist patterns
Astryx resources
GSAP
Framer Motion / Motion
Lenis when justified
cmdk
Sonner
Vaul
React Flow / XYFlow
TanStack Table / Virtual
```

These are component/pattern sources, not independent design systems.

Normalize everything through SyncNode tokens.

Avoid:

- noisy gradients
- giant glass cards
- excessive rounded containers
- generic AI sparkle effects
- decorative illustrations inside operational surfaces
- random colors
- oversized dashboard widgets

---

# 7. ELECTRON REQUIREMENTS

Use a secure renderer architecture:

```text
Electron Main
→ Preload
→ Secure IPC
→ React Renderer
→ API/SSE clients
→ Backend
```

Prefer:

```text
contextIsolation: true
nodeIntegration: false
```

Expose only necessary preload APIs.

Never expose arbitrary shell or filesystem access to renderer code.

Do not duplicate backend computer-control capabilities in the renderer.

---

# 8. APP EXPERIENCE

The application should open with a polished splash experience.

Suggested sequence:

```text
SYNCNODE
Think locally. Act intelligently.

Local runtime
Model gateway
Workspace

Ready
```

Then transition into the workbench.

The splash should be fast and based on meaningful startup checks where practical.

---

# 9. WORKBENCH STRUCTURE

Use an editor-style layout:

```text
┌────────────────────────────────────────────────────────────┐
│ top bar / tabs / commands                                 │
├─────────────┬──────────────────────────────┬───────────────┤
│ left rail   │ primary work surface         │ inspector     │
│             │                              │               │
│ Runs        │ Intent / Plan                │ Agent         │
│ Knowledge   │ Timeline / Desktop           │ Context       │
│ Agents      │ Artifacts / Evidence         │ Tools         │
│ Audit       │                              │ Approval      │
│ Settings    │                              │               │
├─────────────┴──────────────────────────────┴───────────────┤
│ runtime / connection / run status                          │
└────────────────────────────────────────────────────────────┘
```

Panels can collapse and resize.

Do not force every panel onto every screen.

---

# 10. ROUTING REQUIREMENTS

Implement real routing.

Recommended route map:

```text
/
/welcome
/home
/runs
/runs/:runId
/runs/:runId/overview
/runs/:runId/intent
/runs/:runId/plan
/runs/:runId/agents
/runs/:runId/timeline
/runs/:runId/desktop
/runs/:runId/tools
/runs/:runId/artifacts
/runs/:runId/evidence
/runs/:runId/approvals
/runs/:runId/audit
/knowledge
/knowledge/:id
/learning
/settings/general
/settings/runtime
/settings/models
/settings/appearance
/settings/shortcuts
/settings/security
/about
```

Preserve run identity and selection state where useful.

Deep links must work.

Back/forward must work.

---

# 11. LIVE DATA CONTRACT

Backend base URL:

```text
http://127.0.0.1:8000
```

Ollama:

```text
http://127.0.0.1:11434
```

Known local model:

```text
gemma4:e4b
```

Use REST + SSE only for backend integration unless an explicitly documented frontend-safe IPC capability is required.

Primary run sequence:

```text
POST /api/v1/runs
→ receive run_id
→ fetch run snapshot
→ fetch required collections
→ open one SSE stream
→ reduce events into normalized state
→ reconcile with REST snapshots
```

---

# 12. HEALTH ENDPOINTS

Use the documented health APIs for connection/status surfaces:

```text
GET /health
GET /health/ready
GET /health/model
GET /health/database
GET /health/rag
GET /health/computer
GET /health/browser
```

Do not show green/healthy indicators when the actual response is unavailable or unhealthy.

---

# 13. RUN ENDPOINTS

Core documented run surfaces include:

```text
GET /api/v1/runs/{run_id}
GET /api/v1/runs/{run_id}/steps
GET /api/v1/runs/{run_id}/tools
GET /api/v1/runs/{run_id}/observations
GET /api/v1/runs/{run_id}/verifications
GET /api/v1/runs/{run_id}/artifacts
GET /api/v1/runs/{run_id}/context
GET /api/v1/runs/{run_id}/audit
GET /api/v1/runs/{run_id}/events
POST /api/v1/runs/{run_id}/terminate
```

Approval:

```text
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
```

Knowledge, learning, agents, and tools should follow the current contract docs/OpenAPI rather than assumptions.

---

# 14. SSE RULES

Expected event vocabulary includes:

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
agent.plan_summary
agent.started
agent.waiting
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
approval.requested
approval.decided
workflow.memory_recorded
run.waiting_approval
run.completed
run.failed
run.cancelled
```

Implement:

- one connection per run
- reconnect
- backoff
- dedupe
- event ordering safeguards where needed
- state reconciliation
- terminal-state handling
- unknown-event tolerance
- disconnected/stale presentation

Never crash because an unknown event arrives.

Never emit frontend-created fake backend events.

---

# 15. DATA INTEGRITY

The frontend must not claim success because a previous event happened.

Examples:

- `step completed` does not automatically mean artifact exists.
- `artifact listed` does not automatically mean verification passed.
- `agent completed` does not mean every downstream artifact completed.
- approval UI visible does not mean approval granted.
- an intended tool call does not mean it executed.

Always use the most specific server evidence available.

---

# 16. CORE SCREENS TO BUILD

Build these operational surfaces:

```text
Home
Runs
Active Run
Intent
Plan
Agents
Timeline
Desktop
Tools
Artifacts
Evidence
Approvals
Knowledge
Learning
Audit
Settings
```

Each must feel part of one product.

---

# 17. INTENT EXPERIENCE

Intent should read like an AI task inspector.

Show actual backend data such as:

- goal
- normalized intent
- classification
- capabilities
- constraints
- requested applications
- artifacts
- relevant context
- ambiguity/assumptions where exposed

Prefer structured rows/collapsibles over giant cards.

---

# 18. PLAN EXPERIENCE

Plan should visually expose:

- steps
- dependencies
- wave/batch information
- agent ownership
- tools
- inputs/outputs
- expected verification
- risk/approval data when provided

Use React Flow/XYFlow where it genuinely improves understanding.

Keep nodes compact.

---

# 19. AGENT EXPERIENCE

Render real agents and states.

Typical runtime agents may include:

```text
Supervisor
Writer
Document
Office
Computer
Browser
Verifier
Recovery
```

Do not assume these are always active.

Show:

- state
- responsibility
- current step
- tools
- latest activity
- observation
- verification
- artifacts
- errors
- timing where available

Agent details can open in an inspector/drawer.

---

# 20. TOOL / TIMELINE EXPERIENCE

A tool event should be displayed using actual lifecycle data:

```text
proposed
→ validated
→ authorized
→ started
→ invoked
→ completed / failed
```

The unified timeline must support grouping for:

- RAG
- intent
- planning
- agent lifecycle
- tool activity
- observations
- verification
- recovery
- approvals
- artifacts
- completion

Parallel backend activity should remain visually parallel when the event data supports it.

---

# 21. DESKTOP VIEW

Show the backend's actual computer observations/screenshot evidence.

Possible display fields:

- application
- window
- action
- observation
- screenshot
- related step
- tool
- verification

Never imply that React itself is performing the OS action.

---

# 22. ARTIFACT VIEW

Use:

```text
frontend/docs/FRONTEND_ARTIFACT_EVIDENCE.md
```

For artifacts show only data actually available from the contract.

Useful fields may include:

- filename
- type
- run
- step
- agent
- timestamp
- size
- path/location
- checksum
- verification

Link artifacts to their provenance.

---

# 23. EVIDENCE VIEW

The evidence surface should make this chain visible:

```text
Run
 ↓
Step
 ↓
Agent
 ↓
Tool
 ↓
Observation
 ↓
Artifact
 ↓
Verification
```

Use compact evidence rows, expandable detail, and direct cross-links between related entities.

Avoid decorative “trust” banners with no evidence behind them.

---

# 24. APPROVAL VIEW

Use:

```text
frontend/docs/FRONTEND_APPROVAL_FLOW.md
```

Approval cards/sheets should show:

- action
- target
- reason/context
- related step
- agent/tool
- artifacts
- evidence
- expected external effect

Then:

```text
Reject    Approve
```

Call the documented approval endpoint.

Do not auto-approve.

Do not infer approval from a button click unless the server confirms it.

---

# 25. KNOWLEDGE / RAG

The knowledge experience must use the backend's actual APIs.

Show:

- documents
- search
- results
- relevance where available
- snippets
- provenance
- ingestion/index state

A run's context view should make retrieved evidence understandable without pretending the frontend performs RAG itself.

---

# 26. LEARNING

Learning/workflow-memory screens must use actual backend responses.

Do not write language such as “SyncNode learned this” unless the server data supports the statement.

---

# 27. AUDIT

Audit should provide:

- event type
- timestamp
- run
- agent
- tool
- outcome/status
- event details
- filters
- search

The audit screen should feel like an engineering event explorer.

---

# 28. ERROR STATES

Build first-class handling for:

```text
loading
empty
partial
stale
disconnected
reconnecting
request failed
run failed
run cancelled
approval pending
terminal success
```

Do not replace an error with an empty state.

Do not replace disconnected state with stale-looking “online” state.

---

# 29. COMMAND PALETTE

Support at minimum:

```text
Ctrl/Cmd + K
```

Possible actions:

- New run
- Search knowledge
- Open run
- Open artifact
- Open approval
- Open audit
- Toggle sidebar
- Toggle inspector
- Refresh
- Reconnect
- Terminate run
- Settings

Use the current shell/router rather than hard-coding navigation strings in many places.

---

# 30. COMPONENT OWNERSHIP

Use reusable SyncNode primitives instead of page-specific one-offs.

Useful component families:

```text
Shell
Sidebar
TopBar
CommandPalette
StatusBar
RunHeader
RunTabs
RunStatus
AgentList
AgentInspector
ToolRow
Timeline
ObservationPanel
VerificationRow
RecoveryTrace
ArtifactRow
ArtifactPreview
EvidenceChain
ApprovalPanel
DesktopMirror
KnowledgeSearch
AuditTable
```

Keep styling centralized.

---

# 31. NO VISUAL INCONSISTENCY

Do not allow:

- three different button radii
- multiple unrelated dark grays
- several border opacities without token rationale
- random component spacing
- arbitrary icon sizes
- per-page typography systems

Define shared tokens first, then build components from those tokens.

---

# 32. ANIMATION POLICY

Animation should communicate:

- hierarchy
- state change
- transition
- attention
- completion

Use:

- CSS for micro interactions
- Motion/Framer Motion for React state transitions
- GSAP sparingly for splash/high-value choreography

Do not create perpetual CPU-heavy animation.

Respect reduced motion.

---

# 33. ACCESSIBILITY

Every interactive control needs:

- keyboard access
- visible focus
- semantic label
- appropriate ARIA
- predictable Escape behavior

Dialogs and drawers must trap/restore focus correctly.

Tooltips should supplement, not replace, labels.

---

# 34. PERFORMANCE

Large runs can produce many timeline/audit events.

Use:

- virtualization
- memoized rows
- stable keys
- normalized data
- selectors
- lazy screens
- efficient subscriptions

Do not rebuild the entire page tree on every SSE event.

---

# 35. LOCAL STARTUP

From:

```powershell
cd C:\syncnode
```

Run the existing local Ollama setup if required:

```powershell
ollama serve
```

Verify the model is present/runnable according to the existing local setup:

```text
gemma4:e4b
```

Start the backend using the repository's established command/script. Do not create backend modifications to support frontend development.

Expected backend:

```text
http://127.0.0.1:8000
```

Then:

```powershell
cd C:\syncnode\frontend
```

Inspect `package.json` and use the repository's actual scripts.

Commonly:

```powershell
npm install
npm run dev
```

But use `pnpm`/other tools if the repository already dictates that.

---

# 36. TESTING REQUIREMENTS

At minimum, test:

### Unit / component

- route mapping
- API parsing
- SSE parsing
- event reducer
- deduplication
- state derivation
- approval state
- evidence state
- timeline grouping

### Integration

- create run
- receive events
- reconnect
- hydrate after refresh
- approval decision
- artifact rendering
- terminal run states

### Electron / browser automation

- app launch
- splash → workbench
- run creation
- active run navigation
- timeline
- agent inspector
- artifact/evidence view
- approval flow
- settings
- reconnect state

---

# 37. GIT SAFETY

Before implementation:

```powershell
git status --short
```

After implementation:

```powershell
git status --short
git diff --stat
```

Review changed paths.

Frontend work should not add modifications to backend files.

Do not use destructive reset/checkout commands on unrelated work.

---

# 38. IMPLEMENTATION PHASES

Use this order unless existing code requires a safe variation.

### 1. Discover

- inspect repo
- read docs
- inspect frontend architecture
- inspect contracts
- inspect current state

### 2. Foundation

- tokens
- primitives
- fonts
- shell
- Electron security

### 3. Navigation

- routes
- sidebar
- top bar
- command palette
- deep links

### 4. Backend integration

- API client
- SSE manager
- state layer
- reconnect/error handling

### 5. Core run UX

- home
- runs
- active run
- intent
- plan
- agents
- timeline

### 6. Trust/evidence UX

- tools
- observations
- verification
- recovery
- artifacts
- evidence
- approvals
- desktop

### 7. Secondary surfaces

- knowledge
- learning
- audit
- settings

### 8. Quality

- accessibility
- performance
- loading/error/empty states
- animation
- visual QA
- Electron QA

---

# 39. “DONE” CRITERIA

Do not declare done until:

```text
[ ] App launches in Electron
[ ] Splash is polished
[ ] Main shell feels like an editor
[ ] Routes are real
[ ] Run creation uses live API
[ ] SSE is live
[ ] SSE reconnects
[ ] Run state updates correctly
[ ] Intent works
[ ] Plan works
[ ] Agents work
[ ] Timeline works
[ ] Tool lifecycle works
[ ] Observations work
[ ] Verification works
[ ] Recovery works
[ ] Desktop mirror works with available evidence
[ ] Artifacts work
[ ] Artifact evidence chain works
[ ] Approval workflow works
[ ] Knowledge works
[ ] Learning works
[ ] Audit works
[ ] Settings works
[ ] Keyboard shortcuts work
[ ] Empty/loading/error states exist
[ ] No fake backend activity
[ ] No backend files modified
[ ] Performance remains usable
[ ] Electron security boundary is preserved
```

---

# 40. FINAL AGENT BEHAVIOR

When asked to implement a frontend feature:

1. find the relevant frontend specification;
2. inspect existing implementation before creating anything;
3. inspect backend contract only when needed for data shape;
4. implement inside frontend scope;
5. integrate with real REST/SSE data;
6. add loading/empty/error states;
7. add tests;
8. run the feature locally;
9. inspect the UI visually;
10. review git diff for unintended backend changes.

When uncertain:

- prefer repository documentation over assumptions;
- prefer machine-readable API contracts over prose guesses;
- prefer existing frontend patterns over new duplicate abstractions;
- prefer server truth over optimistic UI;
- prefer a clear limitation over fabricated functionality.

The goal is not to create the most code.

The goal is to create a **coherent, real, premium, trustworthy SyncNode frontend**.

**Frontend only. Read everything. Use the contracts. No fake data. No backend edits. Finish the Electron app end-to-end.**
