# SyncNode — FRONTEND_MASTER.md

## Integrated Development Workbench — Master Frontend Design Specification

**Product:** SyncNode  
**Tagline:** **Think locally. Act intelligently.**  
**Client:** Electron + React + TypeScript  
**Backend:** Existing FastAPI + LangGraph + local AI runtime  
**Frontend role:** Thin client over the frozen REST + SSE contracts  
**Primary visual direction:** Dark, premium, technical, restrained, IDE/workbench-oriented  
**Primary goal:** Make SyncNode feel like a serious local AI development/automation workbench rather than a chatbot dashboard.

---

# 1. Core Product Experience

SyncNode should visually communicate that the user is not merely chatting with an AI.

The user is operating an **integrated development + agent execution environment** where:

```text
USER GOAL
   ↓
AI UNDERSTANDS
   ↓
AGENTS ARE ASSIGNED
   ↓
WORKFLOW IS BUILT
   ↓
TOOLS EXECUTE
   ↓
DESKTOP/APPS CHANGE
   ↓
THE WORK IS OBSERVED
   ↓
THE RESULT IS VERIFIED
   ↓
APPROVAL IS REQUESTED WHEN NEEDED
   ↓
AUDIT + MEMORY
```

The frontend must therefore expose both:

- **development context** — files, code, project structure, knowledge, configuration
- **agent context** — what the agents are thinking safely, planning, executing, observing and verifying
- **desktop context** — what is happening on the actual Windows machine
- **workflow context** — the graph, tasks, dependencies, status and execution timeline

The interface should feel like a blend of:

- a modern code editor / IDE
- an agentic development environment
- a workflow graph editor
- a live computer-control console

It should **not** look like a generic SaaS admin dashboard.

---

# 2. Reference Design Direction

The supplied visual references establish the design language:

- dark IDE surfaces
- thin borders
- rounded panels
- compact navigation
- strong visual hierarchy
- large central working canvas
- persistent side panels
- workflow/graph visualization
- code/document/editor surfaces
- agent activity visible without taking over the entire application
- minimal decorative noise
- premium developer-tool feeling

The supplied hand-drawn target layout is the primary structural reference.

The target is a **four-zone integrated workbench**:

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Top App Bar / Workspace / Run Status / Search / Health / Settings            │
├─────────────────────┬───────────────────────────────────┬─────────────────────┤
│                     │                                   │                     │
│  1. TASK / PROJECT  │       2. MAIN WORKSPACE           │  4. AGENT           │
│     CONTROL         │                                   │     INTELLIGENCE    │
│                     │   Code / Desktop Mirror /         │                     │
│  Tasks              │   Workflow / Document /           │  Main Agent         │
│  Files              │   Knowledge / Terminal            │  Chat               │
│  Workflows          │                                   │  Thinking           │
│  Knowledge          │                                   │  Model Selection    │
│  Recent Runs        │                                   │  Agent Activity     │
│                     │                                   │  Tool Calls         │
│                     │                                   │                     │
│                     ├───────────────────────────────────┤                     │
│                     │  3. LIVE EXECUTION / WORKFLOW    │                     │
│                     │     GRAPH + TIMELINE + STATES     │                     │
│                     │                                   │                     │
│                     │  nodes / agents / tools /        │                     │
│                     │  observations / verification      │                     │
│                     │                                   │                     │
└─────────────────────┴───────────────────────────────────┴─────────────────────┘
```

This is the **canonical SyncNode application shell**.

---

# 3. Four-Zone Layout — Canonical Structure

## Zone 1 — Task + Project Control Rail

**Position:** left side  
**Purpose:** persistent navigation, task management, project state and working context.

Recommended width:

```text
240–300px
```

This area should remain compact and information-dense.

### Primary sections

```text
SYNCNODE

Workspace
  ├─ Project
  ├─ Files
  ├─ Code
  ├─ Knowledge
  └─ Workflows

CURRENT RUN
  ├─ Active task
  ├─ Queue
  ├─ Agents
  └─ Recent runs

TOOLS
  ├─ Capabilities
  ├─ Applications
  └─ Settings
```

### Task management

The task system is a first-class feature.

A task entry should display:

```text
● Running
Create quarterly report + email
7/10 steps
3 agents active
```

Statuses:

- queued
- running
- waiting approval
- completed
- failed
- cancelled

### Left rail behavior

The left panel may collapse into an icon rail.

Expanded:

```text
[icon] Workspace
[icon] Tasks
[icon] Files
[icon] Knowledge
[icon] Workflows
[icon] Runs
```

Collapsed:

```text
│ W │
│ T │
│ F │
│ K │
│ G │
│ R │
```

Do not overload this rail with settings or rarely-used controls.

---

# 4. Zone 2 — Main Integrated Development Workspace

**Position:** center  
**Purpose:** the largest surface in the application and the place where the user actually sees the work being done.

This is the most important panel.

Recommended width:

```text
~55–65% of application width
```

The main workspace is **tabbed**, but tabs represent different views of the same active run/project context.

Canonical tabs:

```text
DESKTOP
EDITOR
WORKFLOW
FILES
KNOWLEDGE
TERMINAL
```

The user should never feel like they are switching to unrelated applications. Everything remains inside the SyncNode workbench.

---

# 5. MAIN WORKSPACE — DESKTOP MIRROR

This is the primary view for computer-use execution.

When SyncNode is operating the machine, the user should see a live representation of the controlled desktop/application area.

```text
┌──────────────────────────────────────────────────────────────┐
│ Desktop Mirror                                      100%     │
│                                                              │
│    Windows / Word / Excel / Browser / PowerPoint             │
│                                                              │
│    LIVE VIEW                                                  │
│                                                              │
│    [ screenshot / rendered desktop surface ]                │
│                                                              │
│    ● Agent executing                                         │
│    ● Mouse / keyboard activity                               │
│    ● Current application                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Desktop mirror requirements

Display:

- current application
- focused window
- live screenshot/observation
- activity status
- current step
- agent executing it
- verification state
- recovery state

Example:

```text
ACTIVE APPLICATION
Microsoft Word

STEP
Insert generated paragraph

AGENT
WordDocumentAgent

STATUS
EXECUTING

VERIFY
Waiting for content verification…
```

### Important

The desktop mirror is a **visual representation and observation surface**.

The Electron app does not directly control Windows.

All computer interaction remains in the backend.

---

# 6. MAIN WORKSPACE — CODE EDITOR

SyncNode is an integrated development environment, so a real code editor must be part of the central workspace.

This is where the user can:

- inspect repository files
- open source files
- edit code
- compare generated changes
- inspect agent-generated patches
- see diagnostics
- inspect diffs

The editor should resemble a serious developer tool, not a text area.

### Canonical editor layout

```text
┌─────────────┬───────────────────────────────────────────────┐
│ File Tree   │ file.ts                                       │
│             ├───────────────────────────────────────────────┤
│ src/        │  1 import ...                                 │
│ ├─ app/     │  2                                            │
│ ├─ agents/  │  3 export ...                                 │
│ ├─ runtime/ │  4                                            │
│ └─ tools/   │  5                                            │
│             │                                                │
│             │  [code editor]                                │
│             │                                                │
├─────────────┴───────────────────────────────────────────────┤
│ Problems │ Output │ Terminal │ Agent Patch │ Diagnostics    │
└───────────────────────────────────────────────────────────────┘
```

### Editor capabilities

At minimum:

- syntax highlighting
- line numbers
- search
- command palette
- tabs
- dirty state
- file tree
- diff viewer
- diagnostics
- read-only / edit modes
- agent-generated diff review
- save
- undo/redo

The code editor may use an embedded editor implementation appropriate for Electron, such as Monaco.

---

# 7. MAIN WORKSPACE — WORKFLOW GRAPH

The workflow graph shows the actual execution architecture.

The graph should use a React Flow-style canvas.

Example:

```text
                    ┌────────────────────┐
                    │ Supervisor Agent   │
                    └──────────┬─────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
         ┌────────────┐ ┌────────────┐ ┌─────────────┐
         │ Word Agent │ │ ExcelAgent │ │ PowerPoint  │
         └─────┬──────┘ └─────┬──────┘ └──────┬──────┘
               │              │               │
               └──────────────┼───────────────┘
                              ▼
                     ┌──────────────────┐
                     │ Email Agent      │
                     └────────┬─────────┘
                              ▼
                     ┌──────────────────┐
                     │ Approval Gate    │
                     └──────────────────┘
```

### Node information

Every graph node should show:

```text
Agent / step name
status
current tool
elapsed time
verification
retries
```

Example:

```text
WORD DOCUMENT AGENT
● EXECUTING

Create new document
Tool: document.create_docx
Verification: PASS
Duration: 2.1s
```

### Node states

Use clear state styling for:

```text
QUEUED
RUNNING
WAITING
PASSED
FAILED
RECOVERING
APPROVAL
```

Avoid excessive animation.

Animations should communicate actual state changes.

---

# 8. Zone 3 — LIVE EXECUTION / WORKFLOW TIMELINE

**Position:** bottom portion of the center workspace  
**Purpose:** show what is happening right now at execution level.

This panel should remain visible while a run is executing.

It is the most important operational visibility surface after the desktop mirror.

### Timeline format

```text
14:32:11  ● Supervisor    plan.validated
14:32:12  ● WordAgent     tool.proposed
14:32:12  ● WordAgent     document.create_docx
14:32:14  ● WordAgent     observation.captured
14:32:14  ✓ WordAgent     verification.passed
14:32:16  ● ExcelAgent    excel.create
14:32:16  ● PPTAgent      powerpoint.create
14:32:17  ● BrowserAgent  navigate
14:32:20  ● EmailAgent    attaching artifacts
14:32:22  ! Supervisor    approval.requested
```

### Timeline rows should contain

```text
timestamp
agent
icon/state
action
tool
short summary
duration
verification
```

Never display private chain-of-thought.

Display only safe decision summaries, actions, observations, verification and recovery information.

---

# 9. Zone 4 — MAIN AGENT / INTELLIGENCE PANEL

**Position:** right side  
**Purpose:** make the agent feel present and understandable without making the UI a chatbot.

Recommended width:

```text
320–420px
```

The right panel should contain multiple stacked views.

```text
┌────────────────────────────┐
│ MAIN AGENT                 │
│ Supervisor                 │
├────────────────────────────┤
│ CHAT                       │
│ User / Agent messages      │
├────────────────────────────┤
│ CURRENT TASK               │
│ Creating Office package    │
├────────────────────────────┤
│ THINKING                   │
│ Decision summaries         │
├────────────────────────────┤
│ MODEL                      │
│ Gemma 4 E4B                │
├────────────────────────────┤
│ ACTIVE AGENTS              │
│ Word       ●               │
│ Excel      ●               │
│ PPT        ●               │
│ Email      waiting         │
└────────────────────────────┘
```

---

# 10. MAIN AGENT CHAT

The chat exists for interaction with the running workspace, not as the product's only interface.

The user can:

- create a task
- refine a task
- ask what is happening
- request a pause
- approve/reject an action
- inspect the current plan
- ask about artifacts

Example:

```text
YOU
Create the quarterly report and draft the email.

SYNCNODE
I created a workflow with 8 steps across 4 agents.
3 independent preparation tasks can run safely in parallel.

CURRENTLY
Word document preparation is complete.
Excel and PowerPoint preparation are verified.
The email draft is waiting for approval.
```

Do not expose hidden chain-of-thought.

---

# 11. THINKING / DECISION SUMMARY PANEL

Call this panel **Thinking** visually, but never expose private internal reasoning.

Show safe summaries such as:

```text
UNDERSTANDING
Task requires three Office artifacts and a local draft email.

PLAN
Word + Excel + PowerPoint are independent and can be prepared before email.

POLICY
External email transmission requires human approval.

VERIFICATION
All three artifacts were created in the current run.
```

This gives the user the feeling of seeing the agent think while preserving the backend's safe information boundary.

---

# 12. MODEL SELECTION PANEL

The user should be able to inspect the active local model.

Example:

```text
MODEL
Gemma 4 E4B

Provider
Ollama / Local

Profile
planner

Context
8192

GPU
RTX 2050

Status
● LOCAL / READY
```

Optional expandable metrics:

- prompt tokens
- completion tokens
- latency
- current profile
- vision capability
- tool capability
- context window

Never imply a cloud connection when the runtime is local.

---

# 13. ACTIVE AGENTS PANEL

Display agents as live entities.

Example:

```text
ACTIVE AGENTS

● Supervisor        RUNNING
● Word Agent       COMPLETE
● Excel Agent      RUNNING
● PPT Agent        RUNNING
● Email Agent      WAITING
○ Recovery Agent   IDLE
```

Clicking an agent should focus:

- its graph node
- its recent events
- its tools
- its current task
- its observations

---

# 14. APPROVAL EXPERIENCE

Approval is a major SyncNode UX moment.

It must feel deliberate and clear.

When approval is required:

```text
┌─────────────────────────────────────────┐
│ HUMAN APPROVAL REQUIRED                 │
│                                         │
│ Send email with 3 generated artifacts   │
│                                         │
│ Recipient: user@example.com              │
│ Subject: Quarterly Report                │
│ Attachments:                             │
│  • Word report                           │
│  • Excel workbook                        │
│  • PowerPoint presentation               │
│                                         │
│ Risk: External communication             │
│                                         │
│ [ Reject ]                 [ Approve ]  │
└─────────────────────────────────────────┘
```

The UI must make it impossible to misunderstand what is being approved.

After approval:

```text
APPROVED
→ RUNNING
```

After rejection:

```text
REJECTED
→ FAILED / STOPPED
```

The frontend never calls a raw “send email” implementation.

It only submits the backend approval decision.

---

# 15. ARTIFACT / OUTPUT PANEL

Generated files are first-class objects.

The frontend should display:

```text
ARTIFACTS

DOCX
SyncNode_Word_<run>.docx
✓ verified
SHA-256  601a...

XLSX
SyncNode_Excel_<run>.xlsx
✓ verified
SHA-256  da7d...

PPTX
SyncNode_Presentation_<run>.pptx
✓ verified
SHA-256  7a0a...
```

Clicking an artifact should open an inspection view showing:

- name
- type
- size
- path
- run_id
- producer agent
- producer step
- verification
- hash
- created time

Never represent stale files as current output.

---

# 16. KNOWLEDGE BASE UX

Knowledge should feel integrated with development.

Screen structure:

```text
┌──────────────┬──────────────────────────────┐
│ Knowledge    │ approval_rules.md            │
│              │                              │
│ Policies     │ YAML front matter            │
│ Applications │                              │
│ Workflows    │ # Approval Rules             │
│ Tools        │                              │
│ References   │ ...                          │
│              │                              │
└──────────────┴──────────────────────────────┘
```

Support:

- Markdown editor
- search
- trust-tier badges
- version history
- reindex
- document metadata
- source path
- hash

Trust badges:

```text
AUTHORITATIVE POLICY
REFERENCE
WORKFLOW
UNTRUSTED
```

---

# 17. TOOL / CAPABILITIES VIEW

The capabilities screen should feel like an IDE command catalog.

Example:

```text
TOOLS

Computer
  windows_search
  launch_app
  screenshot
  uia_find

Documents
  create_docx
  inspect_docx

Excel
  create
  write_cell
  read_cell
  inspect

PowerPoint
  create
  add_slide
  inspect

Browser
  navigate
  type
  click
  attach_file
```

Click a tool to show:

- description
- input schema
- output schema
- supported agent
- permissions
- risk
- side effect
- resource locks
- verification strategy
- offline status

---

# 18. RUN DETAIL VIEW

Every run should have a full inspection mode.

```text
RUN #c0574206

STATUS
WAITING FOR APPROVAL

GOAL
Create Word + Excel + PPT and draft email.

-----------------------------------------------
PLAN
8 / 8 steps complete

-----------------------------------------------
AGENTS
4 active/complete

-----------------------------------------------
ARTIFACTS
3 verified

-----------------------------------------------
VERIFICATION
9 PASS / 0 FAIL

-----------------------------------------------
RAG
5 sources retrieved

-----------------------------------------------
AUDIT
89 events

-----------------------------------------------
MODEL
Gemma 4 E4B / Local
```

This should be useful for both normal users and developers.

---

# 19. TOP APPLICATION BAR

The top bar should be minimal.

Suggested structure:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SyncNode │ workspace │ branch │ RUN ● │ search │ model │ health │ settings │
└─────────────────────────────────────────────────────────────────────────────┘
```

Include:

- SyncNode identity
- workspace/project selector
- active run indicator
- global command/search
- model readiness
- backend health
- settings

Avoid a traditional consumer-app navbar.

---

# 20. COMMAND PALETTE

Use a command palette for advanced actions.

Examples:

```text
> Run task
> Open file
> Search knowledge
> Show agents
> Show workflow graph
> Open desktop mirror
> Inspect artifacts
> Show audit
> Approve pending action
> Pause run
> Cancel run
```

Keyboard shortcut style should feel IDE-native.

---

# 21. VISUAL LANGUAGE

## Base

Primary background:

```text
near-black / charcoal
```

Panels:

```text
slightly elevated charcoal surfaces
```

Borders:

```text
subtle low-contrast strokes
```

Text:

```text
high-contrast primary
muted secondary
```

Accent usage should be restrained.

Use semantic colors only when status needs to be obvious:

- running
- success
- warning
- approval
- failure

Do not turn the entire interface into a rainbow dashboard.

---

# 22. TYPOGRAPHY

The product should use a modern developer-tool typography system.

Suggested hierarchy:

```text
App title       13–16px
Section title   11–13px
Body            12–14px
Metadata        10–12px
Code            monospace
```

Use a clean sans-serif for application UI and a readable monospace for:

- code
- tool arguments
- logs
- hashes
- technical identifiers

Avoid giant marketing typography inside the actual workbench.

---

# 23. SPACING + DENSITY

The workbench should be information-dense but not cramped.

Recommended baseline:

```text
4px  — micro spacing
8px  — control spacing
12px — standard spacing
16px — panel spacing
24px — major section spacing
```

Panels should have consistent internal padding.

Do not create excessive empty card space like a SaaS analytics dashboard.

---

# 24. BORDER + PANEL LANGUAGE

Use a consistent surface system.

Example conceptual hierarchy:

```text
Application background
    ↓
Workspace surface
    ↓
Panel
    ↓
Nested card
    ↓
Control
```

Borders should visually separate the four major zones without making every item look boxed.

---

# 25. ANIMATION SYSTEM

Animations should communicate state, not decoration.

Use subtle motion for:

- agent spawn
- tool start
- graph transitions
- execution progress
- approval appearance
- panel expansion
- artifact creation

Examples:

```text
agent spawned
→ node softly activates

execution
→ thin progress indicator

verification pass
→ subtle confirmation transition

approval required
→ focused attention animation
```

Do not animate everything continuously.

Respect reduced-motion preferences.

---

# 26. DESKTOP MIRROR + EDITOR INTEGRATION

The most distinctive feature of the SyncNode interface is that the **real desktop and development environment coexist**.

Example flow:

```text
USER ASKS FOR WORK

Center:
Desktop Mirror
→ Word visibly opens

Bottom:
Execution timeline
→ computer.windows_search
→ launch_app
→ observation
→ verification

Right:
WordDocumentAgent
→ current step
→ decision summary

Left:
Task progress
→ Word 1/3
→ Excel 0/3
→ PPT 0/3
```

Then after Word:

```text
Center:
EDITOR / ARTIFACT INSPECTOR

Bottom:
Word PASS
Excel RUNNING
PPT RUNNING

Right:
OfficeAgent
```

The interface should continuously reorganize focus around the active work without changing the fundamental four-zone shell.

---

# 27. RESPONSIVE BEHAVIOR

Electron is desktop-first.

Primary target:

```text
1440 × 900
1920 × 1080
2560 × 1440
```

### 1440px

Keep all four zones visible.

### 1920px+

Allow:

- wider code editor
- wider desktop mirror
- expanded right agent panel
- graph controls

### Narrow desktop

Collapse the left rail first.

Then allow the right agent panel to become a drawer.

The center workspace must remain the priority.

---

# 28. MAIN APPLICATION STATES

The UI must behave differently for these states:

## IDLE

```text
No active run.
Project/workspace visible.
Start task affordance prominent.
```

## PLANNING

```text
Plan visible.
Agent roster preparing.
Graph being constructed.
```

## RUNNING

```text
Desktop/workflow/timeline active.
Agent state streaming.
```

## WAITING_APPROVAL

```text
Everything pauses visibly.
Approval card becomes primary focus.
```

## RECOVERING

```text
Recovery state visible.
Failed node highlights.
Current recovery attempt shown.
```

## COMPLETED

```text
Artifacts verified.
Run summary visible.
Audit available.
```

## FAILED

```text
Cause clearly visible.
Failed step highlighted.
Evidence and recovery attempts available.
```

---

# 29. FRONTEND STATE ARCHITECTURE

The frontend should maintain a centralized run state derived from REST + SSE.

Conceptual model:

```text
Backend
  │
  ├── REST snapshots
  │
  └── SSE events
         ↓
   Event Normalizer
         ↓
    Run Store
         ↓
 ┌───────┼────────┬────────┬─────────┐
 │       │        │        │         │
Tasks   Agents   Graph   Timeline  Artifacts
 │       │        │        │         │
 └───────┴────────┴────────┴─────────┘
                 ↓
             React UI
```

The frontend must treat SSE events as incremental state updates and REST endpoints as authoritative detail/snapshot sources.

---

# 30. BACKEND CONTRACT USAGE

Electron talks only to:

```text
http://127.0.0.1:8000
```

Base API:

```text
/api/v1
```

The frontend must use the existing backend contracts instead of creating duplicated frontend-only execution logic.

Primary run flow:

```text
POST /api/v1/runs
        ↓
SSE /api/v1/runs/{run_id}/events
        ↓
render live timeline
        ↓
approval.requested
        ↓
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
        ↓
terminal event
        ↓
GET run details
```

---

# 31. PRIMARY SCREENS

The initial Electron product should implement these screens/views.

### 1. Home / Workspace

- health
- project/workspace
- recent runs
- create task

### 2. Active Run

This is the flagship screen.

- task rail
- desktop/editor center
- workflow/timeline bottom
- agent intelligence right

### 3. Run Detail

- complete steps
- agents
- artifacts
- observations
- verification
- audit
- knowledge used

### 4. Knowledge

- Markdown files
- editor
- versions
- trust tiers
- search

### 5. Capabilities

- tools
- agents
- supported applications
- risk
- schemas

### 6. Learning

- workflow memory
- candidate strategies
- human review

### 7. Settings

- backend status
- local model
- workspace
- resource limits
- appearance

---

# 32. FLAGSHIP ACTIVE-RUN SCREEN

This is the main design to implement first.

Canonical layout:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SyncNode  /  Project  /  RUNNING ●  /  Search  /  Gemma  /  Healthy         │
├────────────────┬───────────────────────────────────────────────┬────────────┤
│ TASKS          │ WORKSPACE                                     │ AGENT      │
│                │                                               │            │
│ ● Current Task │ [DESKTOP] [EDITOR] [WORKFLOW] [FILES]        │ Supervisor │
│                │                                               │            │
│ □ Word         │                                               │ Chat       │
│ ✓ Excel        │            MAIN CANVAS                        │            │
│ ● PPT          │                                               │ Thinking   │
│ ◌ Email        │                                               │            │
│                │                                               │ Model      │
│ FILES          │                                               │            │
│                │                                               │ Agents     │
│ knowledge/     │                                               │            │
│ src/           ├───────────────────────────────────────────────┤            │
│ artifacts/     │ LIVE EXECUTION / GRAPH / TIMELINE             │            │
│                │                                               │            │
│ RUNS           │ ● WordAgent   PASS                            │            │
│                │ ● ExcelAgent  RUNNING                         │            │
│ #c0574206      │ ● PPTAgent    RUNNING                         │            │
│                │ ! EmailAgent  WAITING APPROVAL                 │            │
└────────────────┴───────────────────────────────────────────────┴────────────┘
```

This layout is the baseline.

---

# 33. ACTIVE-RUN INTERACTION MODEL

When a user clicks a task:

```text
Task selected
→ center changes to that task's relevant workspace
→ right panel focuses responsible agent
→ bottom timeline filters to that task
```

When a user clicks an agent:

```text
Agent selected
→ graph highlights agent
→ timeline filters to agent
→ right panel expands agent details
→ current tool shown
```

When a user clicks a tool event:

```text
Tool selected
→ show tool schema
→ inputs
→ safe output summary
→ observation
→ verification
→ duration
```

When a user clicks an artifact:

```text
Artifact selected
→ inspect metadata
→ verification
→ source agent/step
→ open/preview where supported
```

---

# 34. WHAT SHOULD BE VISIBLE DURING THE FINAL GOLDEN WORKFLOW

For the flagship demo, the UI should visibly communicate this progression:

```text
1. User enters goal

2. SyncNode understands it

3. Workflow graph appears

4. Agents appear/spawn

5. Windows Search activates

6. Word opens visibly

7. Word document is created

8. Excel is created/manipulated

9. PowerPoint is created

10. Three artifacts become verified

11. Email compose opens

12. Three artifacts appear as attachments

13. Verification passes

14. Approval card appears

15. Run becomes WAITING_APPROVAL
```

The user should be able to watch this from the same workbench.

---

# 35. FRONTEND EVENT-TO-UI MAPPING

The event stream drives visual state.

```text
run.created
    → task card appears

run.started
    → workspace activates

rag.query
    → knowledge activity

rag.retrieval.completed
    → knowledge chips

intent.completed
    → intent summary

plan.created
    → graph appears

plan.validated
    → graph becomes active

plan.wave_dispatched
    → parallel activity indicator

agent.spawned
    → agent appears

agent.started
    → agent becomes active

tool.proposed
    → tool queued

tool.started
    → tool running

tool.completed
    → tool complete

observation.captured
    → observation panel update

verification.passed
    → step success

verification.failed
    → step failure

recovery.started
    → recovery state

approval.requested
    → approval card

run.waiting_approval
    → workflow pause state

run.completed
    → completion state

run.failed
    → failure state
```

---

# 36. SECURITY UX

The UI must reinforce SyncNode's safety model.

Always distinguish:

```text
PROPOSED
AUTHORIZED
EXECUTING
VERIFIED
APPROVAL REQUIRED
```

Never display a tool as “executed” before the backend reports execution.

Never display a result as verified before the backend verification event.

Never show “Email sent” unless the backend explicitly confirms it.

For the Phase-1 local golden workflow, the expected terminal state is:

```text
WAITING FOR APPROVAL
```

---

# 37. OFFLINE UX

The application should clearly show local status.

Example:

```text
● LOCAL RUNTIME
Ollama connected
Gemma 4 E4B
No cloud provider
```

Optional hover/detail:

```text
Inference: Local
Endpoint: 127.0.0.1:11434
Model: gemma4:e4b
GPU: RTX 2050
```

Do not create cloud-style loading states that imply external services.

---

# 38. EMPTY STATES

Empty states should be developer-oriented.

Example:

```text
NO ACTIVE RUN

Describe what you want SyncNode to do.

[ Start a task ]
```

For Knowledge:

```text
No document selected.
Choose a Markdown knowledge file.
```

For Agents:

```text
No agents currently running.
```

---

# 39. ERROR EXPERIENCE

Errors should provide evidence, not generic failure messages.

Bad:

```text
Something went wrong.
```

Good:

```text
ExcelAgent
excel.write_cell

FAILED
Verification mismatch

Expected:
B12 = 420

Observed:
B12 = 390

Recovery:
Attempt 1/2 — REOBSERVE
```

Allow the user to inspect the underlying event.

---

# 40. DEVELOPER / DEBUG MODE

The same UI may expose a developer mode.

Additional data:

- raw event JSON
- tool schema
- agent scope
- request ID
- correlation ID
- token metrics
- timing
- model profile
- verification assertions
- audit sequence

Do not expose private model chain-of-thought.

---

# 41. ELECTRON PROJECT STRUCTURE

Suggested frontend architecture:

```text
frontend/
  electron/
    main/
    preload/
  src/
    app/
      routes/
      layouts/
    components/
      shell/
      task-rail/
      workspace/
      desktop-mirror/
      editor/
      graph/
      timeline/
      agent-panel/
      approval/
      artifacts/
      knowledge/
      capabilities/
    stores/
    api/
    sse/
    hooks/
    types/
    lib/
    styles/
```

Keep UI components independent from direct Electron APIs where possible.

Use the preload boundary for native Electron capabilities.

---

# 42. FRONTEND DOMAIN TYPES

Create strongly typed frontend models for:

```text
Run
Step
Agent
Tool
ToolCall
Observation
Verification
Artifact
Approval
KnowledgeDocument
WorkflowMemory
SSEEvent
```

Prefer generated/shared schemas where available.

Do not duplicate backend semantics unnecessarily.

---

# 43. API CLIENT RULES

Build one typed API client.

Example conceptual modules:

```text
api/
  health.ts
  runs.ts
  agents.ts
  tools.ts
  knowledge.ts
  learning.ts
  approvals.ts
```

SSE should be handled by a dedicated service:

```text
sse/
  runStream.ts
  eventNormalizer.ts
```

Do not scatter fetch calls throughout React components.

---

# 44. STATE MANAGEMENT

Use a predictable state architecture.

Recommended separation:

```text
server state
→ API/SSE-backed

UI state
→ panel selection
→ tab selection
→ expanded/collapsed panels
→ filters

workspace state
→ active project
→ open files
→ editor tabs
```

The run store should be the main operational source for the active execution screen.

---

# 45. ACCESSIBILITY

Keyboard access matters because the target audience is developers/operators.

Support:

- keyboard navigation
- visible focus
- command palette
- shortcut discovery
- reduced motion
- clear semantic labels
- sufficient contrast

---

# 46. WHAT NOT TO BUILD

Do NOT make the frontend:

- a generic chatbot
- a giant dashboard of cards
- a consumer-style AI assistant
- a fake “agent brain” with simulated progress
- a visual clone of another product
- a cloud-only AI interface

The distinctive value is the **integrated development workbench + real local agent execution + desktop observation + workflow visibility**.

---

# 47. IMPLEMENTATION PRIORITY

Build the frontend in this order.

## Phase 1 — Shell

- Electron bootstrap
- React app
- top bar
- four-zone layout
- theme
- resizable panels

## Phase 2 — Backend connectivity

- health API
- run creation
- run detail
- typed API client
- SSE

## Phase 3 — Flagship run screen

- task rail
- desktop mirror
- timeline
- agent panel
- graph
- approval card

## Phase 4 — Development workspace

- repository tree
- code editor
- terminal/output
- diff view

## Phase 5 — Supporting screens

- artifacts
- knowledge
- capabilities
- learning
- settings

## Phase 6 — Polish

- animations
- keyboard shortcuts
- performance
- persistence
- error UX

---

# 48. FLAGSHIP UI FIRST — DO NOT OVERBUILD THE FIRST ITERATION

The first working frontend should prioritize one excellent screen:

```text
ACTIVE SYNCNODE RUN
```

It must demonstrate:

```text
Task
+ Desktop
+ Agents
+ Workflow graph
+ Live timeline
+ Chat
+ Thinking summaries
+ Approval
+ Artifacts
```

This screen should make the architecture immediately understandable to someone seeing SyncNode for the first time.

---

# 49. VISUAL DESIGN PRINCIPLE

The application should always preserve this visual priority:

```text
1. What is SyncNode doing NOW?
2. What is the user asking it to do?
3. Which agent is doing it?
4. What application/workspace is being changed?
5. What happened?
6. Was it verified?
7. Does the user need to approve anything?
```

The layout exists to answer these questions continuously.

---

# 50. FINAL CANONICAL DESIGN

The final SyncNode workbench is:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYN C N O D E                                     │
│  Workspace   Run ●   Search   Local Gemma   System Healthy   Settings       │
├────────────────┬───────────────────────────────────────────────┬────────────┤
│                │                                               │            │
│ TASK / PROJECT │            MAIN DEVELOPMENT AREA              │ MAIN AGENT │
│                │                                               │            │
│ Tasks          │   ┌───────────────────────────────────────┐   │ Supervisor │
│ Files          │   │ Desktop / Editor / Workflow / Files  │   │            │
│ Knowledge      │   │                                       │   │ Chat       │
│ Workflows      │   │                                       │   │            │
│ Runs           │   │         PRIMARY LIVE CANVAS           │   │ Thinking   │
│ Agents         │   │                                       │   │            │
│                │   │                                       │   │ Model      │
│                │   │                                       │   │            │
│                │   └───────────────────────────────────────┘   │ Agents     │
│                │                                               │            │
│                ├───────────────────────────────────────────────┤            │
│                │                                               │            │
│                │      LIVE WORKFLOW / GRAPH / TIMELINE        │            │
│                │                                               │            │
│                │  agents • tools • observations • verification │            │
│                │  recovery • approvals • execution states     │            │
│                │                                               │            │
└────────────────┴───────────────────────────────────────────────┴────────────┘
```

This is the **master layout reference** for all future frontend work.

The exact proportions may evolve during implementation, but the following must remain stable:

```text
LEFT  = TASK / PROJECT CONTROL
CENTER = PRIMARY DEVELOPMENT / DESKTOP WORKSPACE
BOTTOM CENTER = LIVE EXECUTION / GRAPH / TIMELINE
RIGHT = AGENT INTELLIGENCE
TOP = GLOBAL WORKSPACE / SYSTEM CONTEXT
```

---

# 51. FRONTEND DESIGN NORTH STAR

SyncNode should feel like:

> **An IDE for autonomous local computer work.**

The user should be able to sit in one application and see:

```text
their project
+ their code
+ their tasks
+ their agents
+ their workflow graph
+ their local AI
+ their real desktop
+ their files
+ their knowledge
+ their execution timeline
+ their verification
+ their approvals
```

without having to leave the workbench.

The system should make the relationship between **intent → agent → tool → action → observation → verification → approval** visually obvious.

That relationship is the heart of the SyncNode frontend.

---

# 52. SOURCE-OF-TRUTH RULES FOR THE NEXT FRONTEND EDITOR

The next coding editor/agent must treat these documents as authoritative:

```text
FRONTEND_MASTER.md
    ↓
visual shell + UX architecture

shared/openapi/openapi.json
    ↓
REST contract

shared/events/events.json
    ↓
SSE event contract

shared/schemas/entities.json
    ↓
entity schemas

docs/FINAL_BACKEND_ARCHITECTURE.md
    ↓
backend behavior

docs/MULTI_AGENT_ARCHITECTURE.md
    ↓
agent architecture

docs/FINAL_E2E_WORKFLOW.md
    ↓
end-to-end behavior
```

Do not invent new backend APIs when an existing contract already exists.

Do not change backend semantics from the frontend.

If a UI requirement appears to need new backend data, identify the contract gap explicitly and add it to the backend through a versioned/additive contract change rather than hardcoding assumptions in the UI.

---

# 53. FINAL BUILD TARGET

The finished Electron application should open into a polished SyncNode workbench where the user can immediately understand:

```text
WHAT I ASKED
      ↓
WHAT SYNCNODE PLANNED
      ↓
WHICH AGENTS ARE WORKING
      ↓
WHAT THE COMPUTER IS DOING
      ↓
WHAT TOOLS ARE BEING USED
      ↓
WHAT HAS BEEN VERIFIED
      ↓
WHAT OUTPUT WAS PRODUCED
      ↓
WHETHER HUMAN APPROVAL IS REQUIRED
```

The flagship interaction is not the chat box.

The flagship interaction is **watching the entire intelligent workflow happen inside one integrated development environment.**

That is the canonical SyncNode frontend direction.
