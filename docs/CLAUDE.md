# SyncNode Frontend — CLAUDE.md

> **Scope:** This instruction file governs Claude/Claude Code-style agents working on the SyncNode Electron frontend.
>
> **Primary rule:** Build the frontend end-to-end while treating the existing backend as an external, authoritative system. **Do not modify backend implementation.**

---

## 1. Mission

Build the production-quality **SyncNode Electron frontend** under:

```text
C:\syncnode\frontend
```

The application is a sovereign, local AI workbench for confidential industrial/enterprise work. The UI must feel like a serious desktop developer tool / AI IDE, not a generic SaaS dashboard.

North star:

```text
Think locally. Act intelligently.
```

The finished application should combine:

```text
AI IDE ergonomics
+ local AI workbench
+ agent orchestration console
+ execution timeline
+ computer-operation mirror
+ artifact/evidence review
+ human approval
+ auditability
```

The frontend must expose what the backend actually knows. It must never fabricate AI activity for visual effect.

---

## 2. HARD BOUNDARY — FRONTEND ONLY

### Never modify

Do not edit, refactor, replace, or “fix”:

- `backend/`
- backend Python implementation
- LangGraph runtime
- execution engine
- recovery engine
- tool registry
- model gateway
- database code
- backend SSE producer
- backend API routes
- backend schemas
- backend prompts
- backend tests
- backend configuration
- backend runtime contracts

Do not add frontend requirements that force backend changes.

Do not create duplicate backend functionality in React/Electron.

Do not make the frontend directly control the operating system. Real computer control belongs to the backend runtime.

### Allowed

You may:

- read backend code/docs to understand contracts
- read OpenAPI/events/entities files
- run the backend locally
- run Ollama locally
- call existing backend routes
- write frontend tests
- write Electron/preload code inside frontend scope
- add frontend-only mocks/fixtures when isolated from production

### Existing backend changes

There may be backend changes from earlier work. Do not revert them blindly. At the end of your task, identify exactly which files were changed by your frontend work and ensure no new backend modifications were introduced.

---

## 3. MANDATORY READING ORDER

Before implementing significant code, inspect the repository and read the following.

### Frontend authority — read all

```text
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

Treat these as the main frontend implementation contract.

### Backend architecture — read for understanding only

Read the project docs needed to understand the existing runtime:

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

Also inspect, when present:

```text
AI_BRAIN.md
FINAL_BACKEND_ARCHITECTURE.md
FINAL_BACKEND_COMPLETION_REPORT.md
FINAL_PRE_ELECTRON_AUDIT.md
FINAL_BACKEND_AUDIT.md
FINAL_E2E_WORKFLOW.md
MULTI_AGENT_ARCHITECTURE.md
CONTEXT.md
```

### Contract authority

Prefer these machine-readable sources over guesses:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

If a generated contract and prose disagree, inspect the repository's current implementation and document the discrepancy; do not silently invent an endpoint.

---

## 4. FIRST ACTIONS

Before coding:

1. Inspect `C:\syncnode`.
2. Inspect `frontend/package.json`.
3. Identify package manager and scripts.
4. Inspect current Electron entrypoint.
5. Inspect current React/TypeScript app structure.
6. Inspect existing Tailwind/shadcn components.
7. Inspect router, state, API, and SSE code if already present.
8. Read all frontend docs above.
9. Check git status and preserve pre-existing changes.
10. Build a frontend-only implementation plan.

Do not generate a parallel frontend if one already exists.

---

## 5. PRODUCT MENTAL MODEL

SyncNode's core loop is:

```text
OBSERVE
  ↓
UNDERSTAND
  ↓
RETRIEVE
  ↓
PLAN
  ↓
POLICY
  ↓
HUMAN APPROVAL (when required)
  ↓
EXECUTE
  ↓
VERIFY
  ↓
RECOVER / REPLAN
  ↓
AUDIT
  ↓
REMEMBER
```

The frontend should make that loop legible.

The user should be able to answer at any moment:

- What is happening?
- Which run is this?
- Which step is active?
- Which agent owns the step?
- Which tool is being used?
- What was observed?
- Did verification pass?
- Did recovery happen?
- Is approval required?
- Which artifact was produced?
- What evidence supports the result?

---

## 6. VISUAL LANGUAGE

Primary aesthetic:

- black-first
- monochrome
- technical
- minimal
- compact
- high information density
- restrained
- editor-like
- premium
- accessible

Use the supplied UI references as direction for density and restraint.

Do not build:

- generic SaaS dashboards
- giant cards everywhere
- rainbow AI gradients
- excessive glassmorphism
- decorative 3D blobs
- giant marketing headings in the workbench
- random component-library visual styles
- meaningless statistics
- fake terminal logs
- fake model reasoning

Think:

```text
OpenCode / VS Code / Zed / Cursor style ergonomics
+ SyncNode's own visual identity
```

Do not clone another product.

---

## 7. DESIGN SYSTEM — SINGLE SOURCE OF VISUAL TRUTH

The authoritative file is:

```text
frontend/docs/FRONTEND_UI_DESIGN_SYSTEM.md
```

Foundation:

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Radix UI or Base UI as appropriate
- Lucide icons

Use patterns/components from modern open-source systems selectively, including:

- shadcn blocks
- React Bits
- Aceternity UI
- Magic UI
- DaisyUI patterns where appropriate
- Vercel/Geist-inspired patterns
- Astryx/Astryx design resources where compatible
- GSAP
- Framer Motion / Motion
- Lenis where a smooth-scroll surface actually benefits
- cmdk
- Sonner
- Vaul
- React Flow / XYFlow
- TanStack Table / Virtual when useful

Do not use all libraries indiscriminately.

The result must look like one product.

Third-party components are implementation inputs; SyncNode tokens and components define the final appearance.

---

## 8. ELECTRON ARCHITECTURE

The intended architecture is:

```text
Electron Main
   ↓
Preload
   ↓
Secure IPC
   ↓
React Renderer
   ↓
Frontend API client
   ↓
REST + SSE
   ↓
Existing SyncNode backend
```

Prefer:

- `contextIsolation: true`
- `nodeIntegration: false`
- narrow preload surface
- safe IPC channels
- no arbitrary shell execution from renderer
- no direct filesystem access from renderer unless explicitly mediated

Electron is responsible for desktop concerns; React is responsible for application presentation/state.

---

## 9. STARTUP / SPLASH

Implement a polished first-launch experience.

Sequence:

```text
BLACK
  ↓
SYNCNODE
  ↓
Think locally. Act intelligently.
  ↓
Local runtime
Model gateway
Workspace
  ↓
Ready
  ↓
Workbench
```

Startup checks should reflect real local status where possible. Do not fake a long progress sequence.

Motion must be subtle and quick.

---

## 10. ROUTING

Implement real deep-linkable routing. Use the repository's existing router if present.

A suitable route model is:

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
/settings
/settings/general
/settings/runtime
/settings/models
/settings/appearance
/settings/shortcuts
/settings/security
/about
```

Nested tabs may be used where they improve the desktop UX, but every meaningful surface should be deep-linkable.

Preserve selected run/tab/agent/artifact/event where appropriate.

Back/forward navigation must work.

---

## 11. MAIN WORKBENCH

Use an IDE-like shell:

```text
┌───────────────────────────────────────────────────────────────┐
│ Workspace / Run / Commands / Runtime                         │
├──────────────┬───────────────────────────────┬───────────────┤
│              │                               │               │
│ Activity     │ Main work surface             │ Inspector     │
│ / Runs       │ Intent / Plan / Desktop       │ Agent         │
│ / Knowledge  │ Timeline / Evidence           │ Context       │
│ / Files      │                               │ Tools         │
│ / Settings   │                               │ Approval      │
│              │                               │               │
├──────────────┴───────────────────────────────┴───────────────┤
│ Connection / run / runtime status                            │
└───────────────────────────────────────────────────────────────┘
```

Support:

- collapsible sidebar
- collapsible inspector
- resizable panes
- split views
- tabs
- focused mode
- persistent layout state where appropriate

---

## 12. CORE SCREENS

Implement all required screens from `FRONTEND_SCREEN_SPEC.md`.

### Home

- focused task composer
- recent work
- quick actions
- local runtime status
- sparse editor-like presentation

### Runs

- run list
- status
- timestamps
- search/filter
- open/run selection

### Active Run / Overview

- run status
- progress derived from server events
- current step
- active agent
- recent activity
- artifact summary
- approval summary

### Intent

Show the normalized intent and relevant context without inventing fields.

### Plan

Show structured plan, dependencies, agent ownership, tools, expected outputs, verification.

### Agents

Show actual agent lifecycle/state/activity from backend data.

### Timeline

Unified chronological/parallel event presentation.

### Desktop

Show actual computer observations/screenshots where the backend exposes them.

### Tools

Tool lifecycle and details.

### Artifacts

Produced files and their metadata.

### Evidence

Artifact → step → agent → tool → observation → verification chain.

### Approvals

Review and decide on actual backend approval requests.

### Knowledge

Local knowledge browsing/search.

### Learning

Workflow memory/candidates based on actual backend data.

### Audit

Searchable/filterable event explorer.

### Settings

Appearance, runtime, models, shortcuts, security, about.

---

## 13. REST + SSE

Backend base:

```text
http://127.0.0.1:8000
```

API prefix:

```text
/api/v1
```

SSE content type:

```text
text/event-stream
```

The frontend must use the actual OpenAPI/event contracts.

Core flow:

```text
POST /api/v1/runs
        ↓
run_id
        ↓
GET /api/v1/runs/{run_id}
GET /api/v1/runs/{run_id}/steps
GET /api/v1/runs/{run_id}/artifacts
        ↓
GET /api/v1/runs/{run_id}/events
```

Use one managed SSE stream per run.

Implement:

- connection state
- reconnect
- exponential/backoff strategy
- deduplication
- event normalization
- state reduction
- snapshot reconciliation
- unknown-event tolerance
- terminal-state handling
- stale/disconnected UI

Do not treat the SSE stream as an unbounded append-only UI object. Normalize server state and retain an event history for timeline/audit.

---

## 14. DOCUMENTED EVENT VOCABULARY

Support the documented event types, including:

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

Unknown events must not crash the app.

---

## 15. APPROVAL RULE

Approval is a first-class trust surface.

Use:

```text
FRONTEND_APPROVAL_FLOW.md
```

When an actual approval request is received:

- show what action is pending
- show relevant context/evidence
- show destination/target when exposed
- show artifacts when relevant
- show expected external effect
- provide approve/reject
- capture optional user reason where contract supports it

Never auto-approve.

Never create a fake approval state because the UI needs an interesting screen.

---

## 16. ARTIFACT + EVIDENCE RULE

Use:

```text
FRONTEND_ARTIFACT_EVIDENCE.md
```

Artifact identity must remain exact.

Do not claim an artifact exists simply because a step completed.

A good evidence chain is:

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

The frontend must make this trace visually obvious.

Artifacts should support at least the documented types such as DOCX, XLSX, PPTX, PDF, images, text, JSON, CSV where backend data permits.

---

## 17. AGENT / TOOL / VERIFICATION UX

Agents must be real backend entities/states, not static avatars.

Tool lifecycle should visually map to actual events:

```text
proposed → validated → authorized → started → invoked → completed/failed
```

Verification should show:

- status
- verifier/check
- evidence
- expected
- observed
- timestamp

Recovery should show:

```text
verification failed
      ↓
recovery started
      ↓
attempt
      ↓
retry / replan
      ↓
verification
```

Never hide recovery.

---

## 18. STATE ARCHITECTURE

Separate server state from UI state.

### Server state

- runs
- steps
- agents
- tools
- observations
- verifications
- recovery
- artifacts
- approvals
- context
- audit events

### UI state

- selected run
- selected step
- selected agent
- selected artifact
- selected event
- active tab
- drawers
- panel sizes
- filters
- command palette
- appearance
- keyboard/focus state

Prefer normalized state and derived selectors.

Do not duplicate data unnecessarily.

---

## 19. NO FAKE DATA POLICY

Production screens must not invent:

- agent work
- model reasoning
- token counts
- latency
- screenshots
- verification success
- artifacts
- audit entries
- approvals
- tool calls
- execution progress

Development fixtures are acceptable only when clearly isolated from live mode.

---

## 20. ERROR / EMPTY / LOADING STATES

Every feature should implement appropriate:

- loading
- empty
- populated
- partial
- stale
- disconnected
- reconnecting
- error
- cancelled
- terminal success/failure

Example local runtime error:

```text
Backend unavailable
127.0.0.1:8000

Retry connection
```

Do not show fake “online” state.

---

## 21. COMMAND PALETTE + KEYBOARD

Use the existing command infrastructure if present; otherwise use `cmdk`/equivalent.

Primary shortcut:

```text
Ctrl/Cmd + K
```

Commands may include:

- New run
- Open runs
- Search knowledge
- Open agents
- Open timeline
- Open artifacts
- Open approvals
- Open audit
- Open settings
- Toggle sidebar
- Toggle inspector
- Refresh run
- Reconnect backend
- Terminate active run

Shortcuts must invoke actual frontend behavior.

---

## 22. MOTION

Motion stack may use:

- CSS transitions
- Framer Motion / Motion
- GSAP for high-value sequences only

Use motion for:

- splash
- route transition
- drawer/panel entrance
- graph state change
- approval entrance
- verification transition
- artifact arrival

Do not animate everything.

Support reduced motion.

---

## 23. ACCESSIBILITY

Required:

- keyboard navigation
- semantic markup
- visible focus
- ARIA labels
- accessible dialogs/menus
- reasonable hit sizes
- reduced-motion support
- adequate contrast

Do not remove focus rings simply because they do not look “premium”. Make them elegant instead.

---

## 24. PERFORMANCE

The event stream can become large.

Use:

- event virtualization where needed
- memoized rows
- normalized data
- derived selectors
- lazy route loading
- efficient SSE reducer
- batched rendering where appropriate

Avoid rerendering the entire workbench on every event.

---

## 25. LOCAL DEVELOPMENT

Repository:

```text
C:\syncnode
```

Ollama should be locally available at:

```text
http://127.0.0.1:11434
```

Known model:

```text
gemma4:e4b
```

Start Ollama using the existing local setup:

```powershell
ollama serve
```

Backend:

- use the repository's existing documented FastAPI startup command/script
- do not create a new backend launcher just for convenience

Expected backend URL:

```text
http://127.0.0.1:8000
```

Verify:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/ready
http://127.0.0.1:8000/health/model
http://127.0.0.1:8000/health/database
http://127.0.0.1:8000/health/rag
http://127.0.0.1:8000/health/computer
http://127.0.0.1:8000/health/browser
```

Frontend:

```powershell
cd C:\syncnode\frontend
```

Inspect `package.json` and use the actual repository scripts, not assumed scripts. Typical commands may be:

```powershell
npm install
npm run dev
```

or their pnpm/yarn equivalent if the repository uses another package manager.

For Electron, use the existing Electron/Vite/React development script.

---

## 26. IMPLEMENTATION ORDER

### Phase A — audit

- inspect repo
- inspect frontend
- read docs
- verify contracts
- preserve git state

### Phase B — shell

- Electron window
- preload/security
- splash
- welcome
- app shell
- sidebar
- top bar
- status bar
- command palette

### Phase C — infrastructure

- router
- REST client
- SSE manager
- server state
- UI state
- reconnect/error layer

### Phase D — run UX

- home
- run creation
- active run
- intent
- plan
- agents
- timeline

### Phase E — execution evidence

- tools
- observations
- verification
- recovery
- desktop mirror
- artifacts
- evidence
- approvals

### Phase F — platform surfaces

- knowledge
- learning
- audit
- settings

### Phase G — polish

- animation
- keyboard shortcuts
- accessibility
- performance
- empty/error states
- visual QA
- Electron QA

---

## 27. GIT / DIFF DISCIPLINE

Before changes:

```powershell
git status --short
```

After changes:

```powershell
git status --short
git diff --stat
git diff -- frontend
```

Confirm the frontend task did not introduce changes under backend scope.

Do not use destructive commands to clean up unrelated work.

Do not reset the repository merely to get a clean working tree.

---

## 28. VALIDATION CHECKLIST

The application is not done because one page renders.

Verify:

```text
[ ] Electron starts
[ ] Splash renders
[ ] Welcome/home works
[ ] Main shell works
[ ] Sidebar works
[ ] Routing works
[ ] Deep links work
[ ] REST client works
[ ] SSE connects
[ ] SSE reconnect works
[ ] Unknown event does not crash UI
[ ] Run creation works
[ ] Intent renders actual data
[ ] Plan renders actual data
[ ] Agent state updates
[ ] Tool lifecycle updates
[ ] Observations render
[ ] Verification renders
[ ] Recovery renders
[ ] Desktop view renders supplied evidence
[ ] Artifacts render
[ ] Artifact evidence chain renders
[ ] Approval request renders
[ ] Approval decision calls documented endpoint
[ ] Knowledge works
[ ] Learning works
[ ] Audit works
[ ] Settings works
[ ] Loading/empty/error states work
[ ] Keyboard shortcuts work
[ ] Accessibility basics pass
[ ] Large event lists remain usable
[ ] No fake backend activity
[ ] No new backend modifications
```

---

## 29. DEFINITION OF DONE

Done means the frontend is an actual usable Electron application, not a mockup.

It must:

1. launch reliably;
2. look like a coherent premium editor/workbench;
3. navigate through real routes;
4. connect to the existing backend via REST + SSE;
5. represent actual run/agent/tool/observation/verification/recovery data;
6. provide artifact/evidence/approval experiences;
7. handle failure, reconnect, cancellation, and terminal states;
8. maintain a secure Electron boundary;
9. remain responsive for long event streams;
10. preserve the backend exactly as an external contract;
11. pass frontend/Electron validation;
12. leave no frontend TODOs that prevent normal use.

---

## 30. FINAL DIRECTIVE

Work systematically and finish the frontend.

Do not stop after creating a shell.
Do not stop after creating static routes.
Do not stop after creating mock timelines.
Do not turn the project into a visual demo.

Read the documentation, inspect the existing code, implement the real integrations, test the real flows, and polish the real Electron application.

**Frontend only. Backend untouched. Real data. Real routing. Real SSE. Real evidence. Real approval. Premium editor-grade UX.**
