# ELECTRON_ARCHITECTURE.md

# SyncNode Electron Frontend Architecture
## AI IDE / Autonomous Workflow Workbench
### Frontend-only implementation specification

> **Core rule:** This document defines the Electron frontend only.
> The existing SyncNode backend is already implemented and verified.
> **DO NOT MODIFY BACKEND MODULES, BACKEND BUSINESS LOGIC, BACKEND TOOL REGISTRY, LANGGRAPH, PYTHON SERVICES, DATABASE MODELS, EXECUTION ENGINE, RECOVERY ENGINE, OR BACKEND API CONTRACTS.**
>
> The frontend must **consume the existing REST + SSE contracts exactly as they exist** and build the complete desktop experience around them.

---

# 1. Product Definition

SyncNode is an **AI-native integrated development/workflow environment** for autonomous local computer work.

It should feel closer to a premium AI IDE / agentic desktop workbench than a normal dashboard.

The frontend combines:

- task management
- project/workspace navigation
- live AI agent execution
- desktop mirroring
- workflow graphs
- tool-call activity
- agent chat
- approval controls
- model/context inspection
- artifacts
- verification evidence
- knowledge base
- workflow memory
- system health
- settings

The visual experience should communicate:

> **The AI is actively working on the computer, while the user remains in control.**

The application should feel:

- dark
- premium
- technical
- cinematic
- calm
- responsive
- spatial
- information-dense without feeling cluttered

---

# 2. Primary Design Reference

The primary structural reference is the supplied SyncNode layout concept.

The screen is divided into a **four-zone IDE workspace**:

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                                   TOP BAR                                     │
├───────────────────┬─────────────────────────────────────┬─────────────────────┤
│                   │                                     │                     │
│                   │                                     │                     │
│   TASK / WORK     │          DESKTOP MIRROR             │    AGENT / CHAT     │
│   MANAGEMENT      │          + MAIN ACTIVITY            │    PANEL            │
│                   │                                     │                     │
│                   │                                     │                     │
│                   ├─────────────────────────────────────┤                     │
│                   │                                     │                     │
│                   │       WORKFLOW / GRAPH / TRACE      │                     │
│                   │                                     │                     │
│                   │                                     │                     │
└───────────────────┴─────────────────────────────────────┴─────────────────────┘
```

The exact proportions can be fluid, but the design language must preserve these four conceptual zones.

## Zone A — Left Task / Workspace Area

Purpose:

- workspaces
- projects
- active tasks
- recent runs
- workflows
- side tasks
- native desktop activity
- knowledge
- artifacts

Example:

```text
SYNCNODE

Workspace
  ├─ Current Project
  ├─ Files
  ├─ Tasks
  ├─ Workflows
  └─ Knowledge

Current Run
  ● Create monthly report
  ● Word document
  ● Excel analysis
  ● PowerPoint summary
  ● Email draft

Activity
  ● Computer control
  ● Browser
  ● Office
  ● Verification
```

The left pane acts like a combination of:

- IDE explorer
- task manager
- agent workspace navigator

It should remain compact and visually quiet.

---

# 3. Zone B — Central Desktop Mirror

This is the **hero surface** of the application.

It should visually represent the actual Windows desktop/application environment that SyncNode is controlling.

The center should support:

- desktop mirror
- application windows
- screenshots
- focused application
- active window
- live execution overlays
- cursor/action visualization where available
- status indicators
- approval overlays

The user should be able to understand:

> "This is what the agent is currently seeing/doing."

Examples:

```text
┌───────────────────────────────────────────────────┐
│ Word                                              │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │ SyncNode Generated Report                  │  │
│  │                                             │  │
│  │ This paragraph was generated locally...    │  │
│  │                                             │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│                  ● Agent typing                   │
└───────────────────────────────────────────────────┘
```

When the agent is controlling Windows:

- show a subtle "LIVE CONTROL" state
- show current application
- show current action
- animate transitions
- show capture timestamps
- display verification state

Do not fake desktop state.

The center surface must be backed by actual backend observations/SSE data.

---

# 4. Zone C — Bottom Central Workflow / Execution Area

This area displays **what is happening internally**.

It is not another chat window.

It is the operational timeline and graph surface.

Show:

- current workflow
- graph nodes
- agent assignment
- dependency state
- execution wave
- active tool
- completed steps
- verification
- recovery
- approval
- terminal state

Example:

```text
[UNDERSTAND]
      │
      ▼
[PLAN]
      │
 ┌────┼─────────┐
 ▼    ▼         ▼
WORD EXCEL      PPT
 │     │         │
 └─────┼─────────┘
       ▼
    [EMAIL]
       │
       ▼
  [APPROVAL]
```

Nodes should animate according to backend events.

Suggested states:

```text
IDLE
QUEUED
RUNNING
WAITING
VERIFYING
RECOVERING
COMPLETED
FAILED
BLOCKED
```

Use visual transitions rather than abrupt state replacement.

---

# 5. Zone D — Right Agent / Intelligence Panel

The right side is the AI interaction area.

It should feel like a combination of:

- AI chat
- agent monitor
- model inspector
- reasoning summary
- tool timeline
- approval panel

The right side is context-sensitive.

It should support multiple tabs/views:

```text
Agent
Chat
Thinking
Tools
Model
Approval
Evidence
```

Never show private chain-of-thought.

Only show safe backend-provided information such as:

- concise agent summary
- current objective
- selected tool
- tool inputs/outputs when appropriate
- verification result
- recovery status
- model profile
- token/latency metrics

---

# 6. Overall Visual Language

## Color

Primary theme:

- near-black background
- dark charcoal surfaces
- soft off-white text
- muted gray secondary text
- restrained accent colors only for status

Status accents:

```text
green  → completed / verified
yellow → waiting / approval
blue   → active / running
red    → failed / blocked
purple → AI / intelligence
```

Do not turn the whole interface into a rainbow dashboard.

Accent colors should communicate state.

---

# 7. Typography

Use a modern technical sans-serif.

Hierarchy:

```text
App title        20–24px
Section title    13–16px
Body             12–14px
Metadata         10–12px
Telemetry        10–11px
```

Text should be compact but readable.

Avoid giant marketing typography inside the application.

---

# 8. Surfaces

Use:

- very subtle borders
- thin dividers
- soft elevation
- restrained blur
- occasional translucent surfaces

Avoid:

- excessive glassmorphism
- oversized rounded cards
- dashboard-card overload
- unnecessary gradients
- excessive shadows

The goal is:

> **IDE first, AI workspace second, dashboard third.**

---

# 9. Electron Application Shell

Recommended architecture:

```text
electron/
├─ main/
│  ├─ main.ts
│  ├─ window.ts
│  ├─ ipc.ts
│  └─ backend.ts
│
├─ preload/
│  └─ preload.ts
│
└─ renderer/
   ├─ app/
   ├─ components/
   ├─ screens/
   ├─ stores/
   ├─ hooks/
   ├─ services/
   ├─ types/
   └─ styles/
```

Recommended frontend stack:

- Electron
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Radix UI
- Framer Motion
- React Flow
- native EventSource/SSE
- fetch API

The renderer communicates with the backend through a typed frontend client.

---

# 10. Backend Boundary — ABSOLUTE FRONTEND RULE

The Electron frontend may communicate with:

```text
http://127.0.0.1:8000
```

using the documented REST/SSE endpoints.

The frontend MUST NOT:

- import Python
- import backend source code
- modify backend modules
- access backend database directly
- access backend tool implementations
- instantiate LangGraph
- instantiate LangChain
- run Ollama directly
- manipulate Windows through frontend-side hacks
- duplicate backend execution logic

The backend remains the authority.

The frontend is a **thin client + visual orchestration interface**.

Existing contract source:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

The frontend must use these as the source of truth.

---

# 11. Frontend API Layer

Create:

```text
renderer/services/api/
├─ client.ts
├─ health.ts
├─ runs.ts
├─ agents.ts
├─ tools.ts
├─ artifacts.ts
├─ observations.ts
├─ verifications.ts
├─ context.ts
├─ audit.ts
├─ approvals.ts
├─ knowledge.ts
└─ learning.ts
```

Every API function must be typed.

Example:

```ts
createRun(goal)
getRun(runId)
getRunSteps(runId)
getRunArtifacts(runId)
getRunVerifications(runId)
getRunContext(runId)
getRunAudit(runId)
terminateRun(runId)
decideApproval(runId, approvalId, decision)
listAgents()
listTools()
listKnowledge()
```

Do not duplicate backend logic in these clients.

---

# 12. SSE Architecture

SSE is the primary live-update mechanism.

Create:

```text
renderer/services/sse/
├─ runStream.ts
├─ eventParser.ts
├─ eventRouter.ts
└─ types.ts
```

A run starts with:

```text
POST /api/v1/runs
```

Immediately connect:

```text
GET /api/v1/runs/{run_id}/events
```

Every incoming event updates the frontend run store.

Typical sequence:

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
agent.started
agent.plan_summary
tool.proposed
tool.authorized
tool.started
tool.invoked
tool.completed
observation.captured
verification.passed
recovery.started
recovery.attempted
recovery.completed
artifact.created
artifact.verified
approval.requested
run.waiting_approval
workflow.memory_recorded
run.completed / run.failed / run.cancelled
```

Unknown future event types must be safely ignored/logged rather than crashing the UI.

---

# 13. Global Frontend State

Use a structured store.

Suggested domain stores:

```text
AppStore
WorkspaceStore
RunStore
AgentStore
TimelineStore
GraphStore
ArtifactStore
ApprovalStore
KnowledgeStore
HealthStore
SettingsStore
```

Avoid putting the entire application in one giant state object.

---

# 14. Run State Model

Represent:

```ts
type RunStatus =
  | "queued"
  | "running"
  | "waiting_approval"
  | "completed"
  | "failed"
  | "cancelled";
```

Track:

```text
run
steps
agents
tools
observations
verifications
artifacts
approval
context
audit
events
```

The UI should derive its visual state from these real backend objects.

---

# 15. Splash / Startup Experience

The application must have a polished startup sequence.

Do NOT use a generic static Electron splash.

Create a cinematic local-AI boot sequence.

## Splash 1 — Identity

Black screen.

Centered:

```text
SYN C N O D E
```

Then:

```text
THINK LOCALLY.
ACT INTELLIGENTLY.
```

Very subtle animated appearance.

Duration:
~600–900ms.

---

## Splash 2 — Local Runtime Initialization

Transition into a technical diagnostic sequence.

Example:

```text
INITIALIZING SYN C N O D E

● Local Runtime
● Model Gateway
● Agent Runtime
● Workflow Engine
● Desktop Control
● Knowledge
● Verification
```

Each item transitions:

```text
checking...
ready
```

These statuses must come from actual backend health calls where possible.

Do not fake "ready" for unavailable services.

---

## Splash 3 — Model / System Health

Show:

```text
LOCAL INTELLIGENCE

Model
gemma4:e4b

Runtime
Ollama

Execution
GPU

Workspace
READY

Desktop Control
READY

Knowledge
READY
```

This screen should reflect:

```text
/health
/health/ready
/health/model
/health/database
/health/rag
/health/computer
/health/browser
```

---

## Splash 4 — Enter Workspace

Animate the application shell into view.

Suggested transition:

```text
splash
↓
fade/scale
↓
shell
↓
workspace
```

Never make startup excessively slow.

---

# 16. Home Screen

The home screen should feel like an AI IDE.

Include:

```text
SYNCNODE

Good evening.

What should I work on?

┌──────────────────────────────────────────────┐
│ Describe a task...                           │
│                                              │
│                                  [Run]       │
└──────────────────────────────────────────────┘

Recent workflows

[Generate report]
[Prepare presentation]
[Analyze spreadsheet]
[Draft email]

System
● Local AI Ready
● Desktop Ready
● Knowledge Ready
```

The user should be able to start a run immediately.

---

# 17. New Task Composer

The task input is the primary entry point.

Support:

- natural-language task
- optional workspace
- optional context
- optional model profile
- optional approval preferences where supported by backend contract

The UI should NOT expose dangerous implementation controls.

Example:

```text
Create a monthly operations report from the local project files,
write the report in Word, make a supporting Excel analysis,
create a PowerPoint summary, and draft an email with all three attached.
Do not send it.
```

After submission:

```text
RUN STARTING...
```

Then transition automatically into the live execution workspace.

---

# 18. Main Agent Workspace

The main working screen follows the supplied four-zone composition.

## Left

Task/workspace management.

## Center upper

Desktop mirror / active application.

## Center lower

Workflow graph + timeline.

## Right

Agent intelligence/chat/approval.

This is the default screen during an active run.

---

# 19. Desktop Mirror UI

The desktop mirror should be visually dominant.

It should support:

### Idle

```text
DESKTOP
Waiting for activity
```

### Running

```text
LIVE
Microsoft Word
Agent: WordDocumentAgent
Action: typing paragraph...
```

### Verification

```text
VERIFYING
Checking document contents...
```

### Approval

Darkened mirror plus approval overlay:

```text
ACTION REQUIRES APPROVAL

Draft email is ready.
Three artifacts are attached.

[Review Draft]
[Approve]
[Reject]
```

The mirror itself should remain visible behind the overlay.

---

# 20. Desktop Mirror Animation

When new observations arrive:

- crossfade screenshots
- use a very subtle zoom
- highlight focused window
- transition application labels
- animate status chip

Do NOT create exaggerated animations that misrepresent actions.

If the backend only provides screenshots, animate transitions between real screenshots.

---

# 21. Cursor / Action Visualization

Where the backend provides enough data, render:

```text
● click
● type
● focus
● navigate
```

as subtle overlays.

Example:

```text
              ↓
        ┌─────────────┐
        │ Microsoft   │
        │ Word        │
        └─────────────┘
             ↑
         AI action
```

Never fabricate cursor location if the backend does not provide it.

---

# 22. Workflow Graph

Use React Flow.

Node structure:

```text
┌────────────────────┐
│ WORD DOCUMENT      │
│ Word Agent         │
│ ● Verified         │
└────────────────────┘
```

Ports:

- inputs
- outputs
- dependency links

Node states animate.

Examples:

### Pending

gray.

### Running

subtle pulse.

### Verified

green check.

### Recovery

amber animated ring.

### Failed

red state.

### Approval

yellow lock indicator.

---

# 23. Workflow Graph Interaction

Allow:

- zoom
- pan
- fit view
- click node
- inspect node
- highlight dependency path
- highlight active agent
- highlight failed/recovered step

Clicking a node opens detail in the right panel.

Do not allow the frontend to mutate workflow execution by editing graph structure unless a backend contract explicitly supports it.

---

# 24. Agent Panel

Right panel top:

```text
AGENTS

● Supervisor
● Word
● Excel
● PowerPoint
● Computer
● Browser
● Verifier
● Recovery
```

Each shows:

```text
status
current task
tool
duration
verification
```

For future agent expansion, the UI should render dynamically from `/api/v1/agents`.

Do not hardcode only eight agents into layout logic.

---

# 25. Agent Detail

Click an agent.

Show:

```text
WORD AGENT

Status
RUNNING

Current step
create_docx

Current tool
document.create_docx

Capabilities
Document creation
Document inspection
Filesystem

Verification
WAITING

Latency
1.24s
```

Use real backend values.

---

# 26. Agent Chat

Chat should be integrated into the right panel.

Use:

```text
USER
Can you explain what you are doing?

SYNCNODE
Creating the Word report first, then the spreadsheet analysis.
I will use those verified artifacts when building the email draft.
```

No chain-of-thought.

Allowed:
- concise status
- decision summaries
- current objective
- next action
- verification summary

---

# 27. Thinking Panel

The thinking window is NOT raw chain-of-thought.

Show safe execution summaries.

Example:

```text
PLAN SUMMARY

1. Prepare report
2. Create spreadsheet analysis
3. Create presentation
4. Draft email
5. Verify attachments
6. Request approval
```

During execution:

```text
CURRENT DECISION

The required Word, Excel and PowerPoint artifacts
must be verified before email attachment.
```

---

# 28. Tool Activity View

Display:

```text
TOOL ACTIVITY

✓ computer.windows_search
✓ computer.launch_app
✓ document.create_docx
✓ excel.create
● powerpoint.create
○ browser.attach_files
○ approval
```

Each row can expand.

Show:

- tool
- agent
- step
- timestamp
- duration
- success
- verification

Do not dump sensitive/raw payloads indiscriminately.

---

# 29. Model Selection Panel

Model information comes from backend health/model routes.

Show:

```text
LOCAL MODEL

Gemma 4 E4B
Ollama
GPU

Profile
planner

Capabilities
✓ completion
✓ vision
✓ tools
✓ thinking

Context
8192
```

No frontend-side model invocation.

---

# 30. Approval Experience

Approval is one of the most important UI moments.

When:

```text
approval.requested
```

the right panel becomes an approval card.

Example:

```text
REVIEW REQUIRED

The workflow has prepared an external communication.

Recipient
demo@example.com

Subject
Monthly Operations Report

Attachments
✓ Word
✓ Excel
✓ PowerPoint

Risk
External communication

Nothing has been sent.

[Reject]                [Approve]
```

Use visual emphasis but not panic styling.

The center desktop mirror remains visible.

Bottom timeline pauses.

---

# 31. Approval Animation

Transition:

```text
running
   ↓
soft dim
   ↓
yellow boundary pulse
   ↓
approval card enters
   ↓
WAITING FOR YOU
```

After approval:

```text
approval
   ↓
approved
   ↓
resume animation
```

After rejection:

```text
approval
   ↓
rejected
   ↓
failed/terminated
```

All states come from the backend.

---

# 32. Evidence Drawer

Every important execution should be inspectable.

Show:

```text
STEP EVIDENCE

Application
Microsoft Word

Observation
4:31:24 PM

Verification
PASS

Assertions
✓ application_running
✓ content_generated
✓ file_exists

Artifact
SyncNode_Word_<run>.docx

SHA256
...
```

For screenshots:

- show thumbnail
- timestamp
- step
- observation type

---

# 33. Artifact Drawer

Display produced artifacts:

```text
ARTIFACTS

WORD
SyncNode_Word_....

EXCEL
SyncNode_Excel_....

POWERPOINT
SyncNode_Presentation_....

```

Each artifact:

- type
- name
- verified
- hash
- producer
- run
- created time

Provide safe actions based on available backend functionality, such as opening the artifact through the system where appropriate.

Do not directly manipulate files outside the backend authority.

---

# 34. Knowledge Base Screen

Create a dedicated knowledge screen.

Layout:

```text
Knowledge

┌──────────────┬─────────────────────────────────────────┐
│ Documents    │ Markdown editor                        │
│              │                                         │
│ Policies     │ # Approval Rules                        │
│ Applications │                                         │
│ Workflows    │ ...                                     │
│ Tools        │                                         │
│ References   │                         [Save] [Reindex] │
└──────────────┴─────────────────────────────────────────┘
```

Support existing backend:

- list
- create
- edit
- delete
- search
- history
- reindex

Show trust badges:

```text
AUTHORITATIVE POLICY
REFERENCE
WORKFLOW
UNTRUSTED
```

Do not implement trust logic in frontend.

The backend remains authoritative.

---

# 35. Knowledge Search

When searching:

```text
Search knowledge...

approval email
```

Show:

```text
Approval Rules
AUTHORITATIVE POLICY
Score 26.0

Email Draft Workflow
WORKFLOW
Score 24.0
```

Use backend returned scores.

---

# 36. Learning Screen

Show workflow memory and candidate strategies.

Example:

```text
WORKFLOW MEMORY

Email drafting
Success 92%
Runs 18

Candidate strategies

[Review]
"Create Office artifacts before compose"
```

Review interface:

```text
Candidate Strategy

Status
CANDIDATE

[Reject]
[Approve]
```

Only reflect backend lifecycle.

Never activate directly from UI without the backend's required workflow.

---

# 37. Capabilities Screen

Show dynamic:

```text
AGENTS
TOOLS
MODELS
SYSTEM CAPABILITIES
```

Example:

```text
29 Tools

Computer
  windows_search
  launch_app
  screenshot

Word
  create_docx
  inspect_docx

Excel
  create
  write_cell
  read_cell

PowerPoint
  create
  add_slide
  inspect
```

Data comes from:

```text
GET /api/v1/tools
GET /api/v1/agents
```

---

# 38. Audit Screen

Make audit visually useful.

```text
AUDIT

001 run.created
002 run.started
003 rag.query
004 plan.created
005 agent.spawned
006 tool.authorized
...
089 approval.requested
```

Each item:

- sequence
- event
- timestamp
- agent
- step
- hash where available

Provide a verification indicator:

```text
AUDIT CHAIN
✓ VERIFIED
```

---

# 39. System Health Screen

Display:

```text
SYSTEM

Backend        ✓
Database       ✓
Local Model    ✓
RAG            ✓
Desktop        ✓
Browser        ✓
```

Use:

```text
/health
/health/ready
/health/model
/health/database
/health/rag
/health/computer
/health/browser
```

The Run button must be disabled when `/health/ready` says the system is not ready.

---

# 40. Top Bar

Top bar should stay minimal.

Left:

```text
SYNCNODE
```

Center:

```text
Workspace / Current Run
```

Right:

```text
● LOCAL
GPU
Gemma 4 E4B
Settings
```

Optional:

- minimize
- maximize
- close

Electron frameless/window styling can be used if it improves the product.

---

# 41. Bottom Status Bar

Show:

```text
SYNCNODE
● Backend Ready
● Model Ready
● Desktop Ready

RUNNING
Agent: Word
Step: create_docx
GPU
```

During waiting approval:

```text
WAITING FOR APPROVAL
```

During completion:

```text
RUN COMPLETE
```

---

# 42. Responsive Layout

Primary target:

desktop 16:9.

Minimum recommended application size:

```text
1440 × 900
```

The four zones should resize intelligently.

Suggested proportions:

```text
Left        18–22%
Center      52–62%
Right       20–26%
```

Within center:

```text
Desktop mirror    ~65%
Workflow          ~35%
```

Allow pane resizing.

Persist user pane widths locally.

---

# 43. Keyboard Shortcuts

Provide IDE-style shortcuts.

Examples:

```text
Ctrl/Cmd + K
Global command/task input

Ctrl/Cmd + Shift + P
Command palette

Ctrl/Cmd + B
Toggle left pane

Ctrl/Cmd + J
Toggle workflow panel

Ctrl/Cmd + Shift + A
Open agent panel

Esc
Close current overlay
```

Do not conflict with OS functionality unnecessarily.

---

# 44. Command Palette

Command palette should provide frontend-only navigation/actions.

Example:

```text
> New Run
> Open Active Run
> Show Agents
> Show Workflow
> Open Knowledge
> Open Artifacts
> Show Audit
> System Health
> Settings
```

Backend operations remain backend-authoritative.

---

# 45. Micro-Animations

Animation principles:

- subtle
- fast
- meaningful
- state-driven

Use Framer Motion for:

- pane transitions
- modal entry
- splash screens
- graph node state
- agent status
- approval
- notifications
- artifact arrival
- desktop observation updates

Do not animate continuously without purpose.

---

# 46. Agent Activity Animation

When an agent starts:

```text
○
↓
◐
↓
●
```

Use a subtle pulse.

When completed:

```text
✓
```

When failed:

```text
×
```

When waiting:

```text
◷
```

Keep the animation accessible and optionally respect:

```text
prefers-reduced-motion
```

---

# 47. Notification System

Use small non-blocking notifications for:

```text
Run started
Artifact verified
Recovery completed
Approval requested
Run completed
Run failed
Backend unavailable
```

Approval must use a dedicated blocking UI, not a normal toast.

---

# 48. Error UX

Never show raw Python tracebacks as the primary UI.

Instead:

```text
Something went wrong

Step
create_excel

Reason
Spreadsheet verification failed.

Recovery
Attempt 2 of 3

[View Evidence]
```

Allow a technical detail drawer for developers.

---

# 49. Offline UX

The application should visibly communicate local operation.

Use a small indicator:

```text
● LOCAL
```

Optional hover:

```text
AI execution is running locally.
No cloud AI provider is configured.
```

Do not imply network connectivity is required.

---

# 50. Navigation Model

Main navigation:

```text
Home
Runs
Workspace
Knowledge
Agents
Tools
Artifacts
Learning
Audit
Settings
```

However, during an active run the user should stay within the primary workspace.

Navigation must not destroy live SSE state.

---

# 51. Route / Screen Structure

Suggested renderer routes:

```text
/
 /home
 /runs
 /runs/:runId
 /workspace
 /knowledge
 /agents
 /tools
 /artifacts
 /learning
 /audit
 /settings
```

The active run screen is the primary experience.

---

# 52. Active Run Screen Structure

```text
RunScreen

┌──────────────────────────────────────────────────────────────────┐
│ Run Header                                                       │
├─────────────┬───────────────────────────────────┬────────────────┤
│ Task Tree   │ Desktop Mirror                    │ Agent Panel    │
│             │                                   │                │
│ Current     │                                   │ Active Agent   │
│ Workflow    │                                   │ Chat           │
│ Side Tasks  │                                   │ Thinking       │
│             │                                   │ Tools          │
│             │                                   │ Approval       │
│             ├───────────────────────────────────┤                │
│             │ Workflow / Timeline / Graph       │                │
├─────────────┴───────────────────────────────────┴────────────────┤
│ Status / Event Stream                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

# 53. Multi-Agent View

When several agents work logically in parallel:

```text
ACTIVE AGENTS

● WordAgent        RUNNING
● ExcelAgent       RUNNING
● PowerPointAgent  RUNNING
○ EmailAgent       WAITING
```

Graphically connect them to the workflow.

Use event timing to animate real concurrency.

Do not invent agent activity.

---

# 54. Parallel Execution Visualization

When a wave starts:

```text
WAVE 2

┌───────────┐
│ WORD      │
└───────────┘

┌───────────┐
│ EXCEL     │
└───────────┘

┌───────────┐
│ POWERPOINT│
└───────────┘
```

Display:

```text
3 tasks running
```

When a branch completes, its node settles.

The frontend should visualize logical parallelism without claiming physical model concurrency beyond backend telemetry.

---

# 55. Timeline View

Timeline should be dense but readable:

```text
04:31:01  RUN STARTED
04:31:03  RAG
04:31:06  PLAN
04:31:10  WORD AGENT
04:31:12  EXCEL AGENT
04:31:13  PPT AGENT
04:31:19  VERIFY
04:31:21  EMAIL
04:31:23  APPROVAL
```

Clicking an event selects its evidence.

---

# 56. Run Lifecycle UX

```text
QUEUED
  ↓
STARTING
  ↓
UNDERSTANDING
  ↓
PLANNING
  ↓
EXECUTING
  ↓
VERIFYING
  ↓
RECOVERING (optional)
  ↓
APPROVAL (optional)
  ↓
COMPLETED / FAILED
```

Use backend events to drive the displayed stage.

Do not independently infer a terminal status if the backend state says otherwise.

---

# 57. Empty States

Each screen needs a meaningful empty state.

Example:

```text
NO ACTIVE RUN

Start a task and SyncNode will build the workflow here.
```

Knowledge:

```text
NO KNOWLEDGE DOCUMENTS

Add a Markdown knowledge source to begin.
```

Artifacts:

```text
NO ARTIFACTS YET

Artifacts created during runs will appear here.
```

---

# 58. Accessibility

Implement:

- keyboard navigation
- focus states
- semantic buttons
- labels
- tooltip text
- reduced motion
- sufficient text contrast
- screen-reader-friendly important controls

Do not make animation the only source of status.

---

# 59. Performance

The frontend must remain smooth while the backend is busy.

Do not re-render the whole application on every SSE event.

Use:
- event batching where appropriate
- normalized state
- memoized components
- virtualized long timelines if necessary
- throttled screenshot updates
- lazy loading for large views

The desktop mirror and timeline should remain responsive even during long runs.

---

# 60. Screenshot Handling

When screenshot paths/hashes are returned:

- fetch through a safe backend mechanism where provided
- show thumbnail
- lazy-load
- cache responsibly
- avoid loading full-resolution captures unnecessarily

Do not assume arbitrary filesystem access from the renderer.

---

# 61. Security Boundary

Electron must:

- use a secure preload bridge
- avoid exposing Node APIs directly to the renderer
- use context isolation
- avoid unrestricted renderer filesystem access
- avoid arbitrary shell execution from UI
- validate IPC messages

The frontend itself must not become an alternate execution path around SyncNode security.

---

# 62. IPC Boundary

Electron main/preload should expose only required local application capabilities.

Example:

```text
window.syncnode
  .getAppInfo()
  .getWindowState()
  .openArtifact(...)
```

Do not expose:

```text
child_process
fs
shell
powershell
process
```

directly to renderer code.

Any OS integration must be tightly scoped and justified by frontend needs.

---

# 63. Development Modes

Support:

```text
Development
Production
```

Development may show:

```text
event inspector
debug console
API latency
SSE diagnostics
```

These should be hidden or collapsed in production.

---

# 64. Backend Integration Testing From Electron

Frontend integration tests should verify:

1. backend health
2. run creation
3. SSE connection
4. event processing
5. graph updates
6. agent updates
7. artifact updates
8. approval UI
9. terminal states

Do not modify backend tests to make frontend tests pass.

---

# 65. Electron Test Scenarios

At minimum:

## Startup

```text
Launch Electron
→ splash
→ health checks
→ workspace
```

## New Run

```text
enter goal
→ POST /runs
→ SSE
→ live UI
```

## Agent Activity

```text
agent.spawned
→ agent running
→ tool activity
→ verification
```

## Desktop

```text
observation.captured
→ desktop mirror updates
```

## Approval

```text
approval.requested
→ approval card
→ approve/reject
```

## Artifacts

```text
artifact.created
→ artifact.verified
→ artifact drawer
```

## Failure

```text
run.failed
→ error state
→ evidence
```

---

# 66. Visual Quality Gate

Before calling the frontend complete, verify:

```text
[ ] No generic dashboard appearance
[ ] Four-zone IDE structure preserved
[ ] Desktop mirror feels like the central product surface
[ ] Workflow graph is visually clear
[ ] Agent panel feels alive
[ ] Approval state is obvious
[ ] Animations are restrained and meaningful
[ ] Typography is consistent
[ ] Empty states exist
[ ] Loading states exist
[ ] Error states exist
[ ] No layout overflow at 1440x900
[ ] No visual jank during SSE activity
```

---

# 67. Final Product Feeling

The application should feel like:

```text
ANTIGRAVITY-LIKE WORKSPACE
        +
AI IDE
        +
AUTONOMOUS DESKTOP AGENT
        +
WORKFLOW GRAPH
        +
OBSERVABILITY CONSOLE
        +
HUMAN APPROVAL LAYER
```

But it must remain visually original to SyncNode.

Do not copy another product's branding or UI literally.

---

# 68. Frontend Implementation Sequence

Implement in this exact order.

## Phase 1 — Electron Shell

- Electron
- Vite
- React
- TypeScript
- secure preload
- window lifecycle
- theme

## Phase 2 — Splash System

- identity splash
- health initialization
- model/system startup
- transition to workspace

## Phase 3 — Main IDE Layout

- top bar
- left task pane
- center desktop pane
- center workflow pane
- right agent pane
- status bar

## Phase 4 — Backend Client

- REST client
- typed models
- health
- runs
- artifacts
- tools
- agents
- knowledge
- audit
- learning

## Phase 5 — SSE Engine

- connection
- parser
- router
- event store
- reconnect
- terminal handling

## Phase 6 — Live Run UX

- task composer
- run screen
- agent states
- tool activity
- workflow graph
- desktop mirror
- verification

## Phase 7 — Approval

- approval overlay
- review state
- approve
- reject
- resume/fail state

## Phase 8 — Secondary Screens

- knowledge
- agents
- tools
- artifacts
- learning
- audit
- settings

## Phase 9 — Polish

- animations
- transitions
- responsive panes
- keyboard shortcuts
- command palette
- accessibility
- performance

## Phase 10 — Integration QA

- startup
- full golden workflow visualization
- approval
- failure
- reconnect
- reload/resume where contract supports it

---

# 69. Files To Create

Suggested structure:

```text
electron/
src/
├─ app/
├─ components/
│  ├─ shell/
│  ├─ desktop/
│  ├─ workflow/
│  ├─ agents/
│  ├─ timeline/
│  ├─ approval/
│  ├─ artifacts/
│  ├─ knowledge/
│  └─ common/
├─ screens/
├─ services/
│  ├─ api/
│  └─ sse/
├─ stores/
├─ hooks/
├─ types/
├─ animations/
└─ styles/
```

Exact structure may adapt to the existing frontend project, but do not alter backend folders.

---

# 70. Critical "DO NOT TOUCH BACKEND" RULE

This rule is mandatory.

### DO NOT MODIFY:

```text
backend/
ai_ml/
database migrations
backend models
LangGraph implementation
LangChain implementation
ExecutionEngine
RecoveryEngine
ToolRegistry
AgentRegistry
VerificationEngine
Policy engine
Python tools
Ollama integration
backend routes
backend schemas
backend persistence
```

unless there is an explicit, separately authorized API-contract change.

The frontend task is:

```text
READ CONTRACTS
→ BUILD UI
→ CONNECT REST
→ CONNECT SSE
→ RENDER REAL STATE
→ SEND USER ACTIONS THROUGH EXISTING APIs
```

NOT:

```text
change backend
```

---

# 71. If an API Problem Is Found

Do not immediately edit backend code.

Use this order:

```text
1. inspect OpenAPI
2. inspect frontend API client
3. inspect actual HTTP response
4. inspect SSE event
5. determine whether frontend mapping is wrong
6. document a backend contract issue if genuinely necessary
```

Only modify backend if explicitly authorized in a separate task.

For this frontend implementation:

> **Assume backend contracts are frozen.**

---

# 72. Frozen Contract Reference

The frontend source of truth is:

```text
docs/FRONTEND_MASTER.md
docs/FRONTEND_API_INTEGRATION.md
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

The backend API guide already establishes the thin-client model:

```text
Electron
    ↓
REST + SSE
    ↓
SyncNode Backend
```

The frontend must not bypass this boundary.

---

# 73. Definition of Done

The Electron frontend is considered complete when:

```text
[ ] Electron launches cleanly
[ ] Splash sequence works
[ ] Backend health is checked
[ ] Workspace loads
[ ] Four-zone IDE layout is present
[ ] Task composer works
[ ] POST /runs works
[ ] SSE timeline works
[ ] Agent visualization works
[ ] Workflow graph works
[ ] Desktop mirror works from real backend observations
[ ] Tool timeline works
[ ] Verification evidence works
[ ] Artifact view works
[ ] Approval UI works
[ ] Approve/reject works through backend API
[ ] Knowledge editor works
[ ] Tools catalog works
[ ] Agents catalog works
[ ] Learning screen works
[ ] Audit screen works
[ ] Settings works
[ ] Failure states work
[ ] Loading states work
[ ] Offline/local status is visible
[ ] Keyboard navigation works
[ ] Responsive panes work
[ ] No backend modules were modified
[ ] OpenAPI remains the integration source of truth
[ ] SSE unknown events do not crash the application
[ ] Golden backend run is fully visualized from Electron
```

---

# 74. Final Golden Frontend Demonstration

The final demo should look like this:

```text
SYNCNODE SPLASH
      ↓
LOCAL SYSTEM CHECK
      ↓
MAIN WORKSPACE
      ↓
USER ENTERS TASK
      ↓
RUN CREATED
      ↓
LEFT:
task becomes active

CENTER:
desktop mirror wakes

BOTTOM:
workflow graph appears

RIGHT:
Supervisor begins activity
      ↓
RAG
      ↓
PLAN
      ↓
MULTI-AGENT ACTIVITY
      ↓
Word / Excel / PowerPoint
      ↓
desktop mirror shows actual work
      ↓
verification
      ↓
email draft
      ↓
three artifacts visible
      ↓
approval card
      ↓
WAITING FOR USER
```

The frontend should make the backend's real work **feel alive** without inventing work that did not happen.

---

# 75. Final Principle

The SyncNode Electron application is not a normal admin panel.

It is an:

> **AI-native desktop workbench where the user can see the autonomous workflow, see the desktop being operated, understand which agents are active, inspect what tools are executing, review verification evidence, and intervene at human approval boundaries.**

The visual hierarchy must always reinforce:

```text
USER
 ↓
TASK
 ↓
AGENTS
 ↓
WORKFLOW
 ↓
DESKTOP ACTION
 ↓
OBSERVATION
 ↓
VERIFICATION
 ↓
APPROVAL
 ↓
RESULT
```

The user should never have to wonder:

> "What is SyncNode doing right now?"

The interface must answer that visually and continuously.

---

# FINAL FRONTEND INSTRUCTION TO THE IMPLEMENTING EDITOR

Build the Electron frontend **end-to-end** from this specification.

Use the supplied four-zone reference as the primary layout:

```text
LEFT
Task / Workspace Management

CENTER TOP
Live Desktop Mirror

CENTER BOTTOM
Workflow / Graph / Execution Trace

RIGHT
Main Agent / Chat / Thinking / Tools / Model / Approval
```

Make it feel like a premium autonomous-development environment rather than a CRUD dashboard.

Implement:
- splash screens
- startup health sequence
- live workspace
- agent interface
- workflow graph
- desktop mirroring
- live tool calls
- execution state animations
- approval experience
- artifacts
- evidence
- knowledge base
- capabilities
- audit
- settings
- responsive panes
- keyboard shortcuts
- command palette
- accessibility
- SSE-driven real-time updates
- REST integration
- polished micro-interactions
- real loading/error/empty states

Most importantly:

> **DO NOT TOUCH ANY BACKEND MODULES.**

Do not edit Python files.
Do not edit LangGraph.
Do not edit LangChain.
Do not edit tool execution.
Do not edit policy.
Do not edit database logic.
Do not edit backend routes.
Do not change schemas.

Only build and modify the Electron/frontend application and its frontend-side integration layer.

The backend is the authority.
The Electron application is the visual control surface.
