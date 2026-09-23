# FRONTEND_SCREEN_SPEC.md

# SyncNode Electron Frontend
## End-to-End Screen, Layout, Interaction, Animation & State Specification

> **SCOPE: ELECTRON / REACT FRONTEND ONLY**
>
> This is the implementation specification for the complete SyncNode frontend experience.
>
> **DO NOT MODIFY THE BACKEND.**
>
> The existing SyncNode backend is the authority and is already exposed through its documented REST + SSE contracts.
>
> The frontend must:
>
> ```text
> consume
> visualize
> interact
> approve
> inspect
> navigate
> ```
>
> through the existing APIs and event streams only.
>
> Do not modify:
>
> ```text
> backend/
> ai_ml/
> Python
> FastAPI
> LangGraph
> LangChain
> ModelGateway
> ExecutionEngine
> RecoveryEngine
> ToolRegistry
> AgentRegistry
> VerificationEngine
> database
> migrations
> persistence
> backend routes
> backend schemas
> SSE event generation
> Ollama integration
> ```
>
> Only Electron/frontend code is in scope.

---

# 1. PRODUCT EXPERIENCE

SyncNode is an AI-native desktop workbench.

The user should experience:

```text
TASK
 ↓
PLAN
 ↓
AGENTS
 ↓
WORKFLOW
 ↓
DESKTOP
 ↓
TOOLS
 ↓
OBSERVATION
 ↓
VERIFICATION
 ↓
RECOVERY
 ↓
ARTIFACTS
 ↓
APPROVAL
 ↓
RESULT
```

The frontend is not a dashboard.

It is an:

```text
AI IDE
+
DESKTOP AGENT CONTROL ROOM
+
WORKFLOW GRAPH
+
LIVE OBSERVABILITY SURFACE
+
KNOWLEDGE WORKSPACE
+
HUMAN APPROVAL CONSOLE
```

---

# 2. PRIMARY DESIGN REFERENCE

The primary layout follows the supplied four-zone concept.

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                                       │
├───────────────────┬─────────────────────────────────────┬─────────────────────┤
│                   │                                     │                     │
│                   │                                     │                     │
│ TASK / WORKSPACE  │         LIVE DESKTOP MIRROR        │  AGENT INTELLIGENCE │
│                   │                                     │                     │
│                   │                                     │                     │
│ Tasks             │                                     │ Main Agent          │
│ Runs              │                                     │ Chat                │
│ Workflows         │                                     │ Thinking Summary    │
│ Side Tasks        │                                     │ Tools               │
│ Workspace         │                                     │ Model               │
│ Knowledge         │                                     │ Approval            │
│                   ├─────────────────────────────────────┤                     │
│                   │ WORKFLOW / GRAPH / TIMELINE         │                     │
│                   │                                     │                     │
├───────────────────┴─────────────────────────────────────┴─────────────────────┤
│ STATUS / SYSTEM BAR                                                          │
└───────────────────────────────────────────────────────────────────────────────┘
```

This four-zone structure is the visual foundation of the active run experience.

---

# 3. VISUAL PHILOSOPHY

Use:

```text
near-black
charcoal
off-white
muted gray
restrained status accents
thin borders
soft depth
subtle motion
```

The interface should feel:

```text
technical
premium
calm
focused
intelligent
desktop-native
```

Avoid:

```text
generic SaaS dashboard
large marketing cards
excessive glassmorphism
rainbow UI
heavy gradients
large empty hero sections inside the app
fake activity
fake AI reasoning
```

---

# 4. APPLICATION SHELL

The application shell is persistent across most screens.

Structure:

```text
AppShell
├─ TopBar
├─ Sidebar
├─ MainContent
└─ StatusBar
```

The sidebar can collapse.

The top bar stays compact.

The status bar stays low-profile.

---

# 5. APPLICATION DIMENSIONS

Primary target:

```text
1440 × 900
```

Supported target:

```text
1280 × 800
```

Preferred:

```text
1440–2560 width
800–1440 height
```

Minimum supported size should remain usable.

The central four-zone workspace must not collapse into a mobile-style layout.

---

# 6. TOP BAR

Top bar:

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ SYNCNODE   Workspace / Run                    ● LOCAL   GPU   Settings    │
└───────────────────────────────────────────────────────────────────────────┘
```

Left:

```text
SyncNode logo/name
workspace breadcrumb
```

Center:

```text
current screen context
current run title where relevant
```

Right:

```text
LOCAL
backend status
model status
settings
window controls
```

---

# 7. TOP BAR ACTIVE RUN

During a run:

```text
SYNCNODE
/
Operations Workspace
/
Monthly Report

● RUNNING
```

When approval:

```text
● WAITING FOR APPROVAL
```

When completed:

```text
● COMPLETE
```

The state comes from backend-backed frontend state.

---

# 8. SIDEBAR

Sidebar navigation:

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

Collapsed:

```text
icons only
```

Expanded:

```text
icons + labels
```

Persist width locally.

---

# 9. SIDEBAR ACTIVE RUN

When a run is active:

```text
CURRENT RUN

● Monthly Operations Pack

Word
Excel
PowerPoint
Email
```

The active run remains visually distinct.

---

# 10. STATUS BAR

Bottom:

```text
● Backend Ready
● Local Model
● Desktop Ready
● Browser Ready

Run:
EXECUTING
Agent:
Excel
```

During approval:

```text
🔒 WAITING FOR APPROVAL
```

During reconnect:

```text
◌ RECONNECTING
```

---

# 11. SPLASH EXPERIENCE

Startup is a multi-stage sequence.

Do not use one generic splash image.

Use:

```text
Identity
→ Runtime checks
→ Model checks
→ System checks
→ Workspace
```

---

# 12. SPLASH SCREEN 1 — IDENTITY

Black background.

Centered:

```text
S Y N C N O D E
```

Subheading:

```text
THINK LOCALLY.
ACT INTELLIGENTLY.
```

Animation:

```text
fade in
+
very small scale
+
subtle tracking transition
```

No loading spinner yet.

---

# 13. SPLASH SCREEN 2 — LOCAL RUNTIME

Transition:

```text
IDENTITY
→ RUNTIME
```

Show:

```text
INITIALIZING SYN C N O D E

● Local Runtime
● Backend
● Agent Runtime
● Workflow Engine
● Desktop Control
● Knowledge
● Verification
```

Statuses:

```text
CHECKING...
READY
UNAVAILABLE
```

All status values must come from real health checks where possible.

---

# 14. SPLASH SCREEN 3 — MODEL

Show:

```text
LOCAL INTELLIGENCE

Gemma 4 E4B
Ollama
GPU
```

Capabilities:

```text
✓ Completion
✓ Vision
✓ Tools
✓ Thinking
```

Context:

```text
8192
```

Only display values supplied by backend.

---

# 15. SPLASH SCREEN 4 — ENVIRONMENT

Show:

```text
SYSTEM

Database       ✓
RAG            ✓
Desktop        ✓
Browser        ✓
```

This corresponds to actual backend health endpoints.

---

# 16. SPLASH SCREEN 5 — ENTER WORKSPACE

Show:

```text
LOCAL RUNTIME READY

Opening workspace...
```

Transition:

```text
fade
+
scale
+
shell expansion
```

The splash should not exceed a few seconds under normal startup.

If backend is unavailable, remain on a useful recovery screen instead.

---

# 17. STARTUP FAILURE SCREEN

If backend unavailable:

```text
SYNCNODE

LOCAL BACKEND UNAVAILABLE

The SyncNode backend is not reachable.

[ Retry ]

Backend
127.0.0.1:8000
```

Do not claim the backend is broken if only the connection failed.

---

# 18. HOME SCREEN

Home is the task entry point.

Structure:

```text
┌────────────────────────────────────────────────────────────┐
│ Good evening.                                              │
│ What should I work on?                                     │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Describe a task...                                    │ │
│ │                                                        │ │
│ │                                             [ Run ]     │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Recent workflows                                           │
│                                                            │
│ [Report] [Spreadsheet] [Presentation] [Email]             │
└────────────────────────────────────────────────────────────┘
```

---

# 19. HOME — HEALTH STRIP

Show:

```text
● Local AI Ready
● Desktop Ready
● Knowledge Ready
```

Use actual readiness state.

---

# 20. HOME — TASK COMPOSER

The task input is the primary control.

Support:
- multiline
- paste
- keyboard shortcuts
- submit with Ctrl/Cmd+Enter

Placeholder:

```text
Tell SyncNode what you want done...
```

---

# 21. HOME — EXAMPLE TASK

Placeholder example:

```text
Create a Word report, Excel analysis and PowerPoint summary,
then draft an email with all three attached. Do not send.
```

The example is only guidance.

Do not hardcode a workflow based on this text.

---

# 22. HOME — RECENT RUNS

Show:

```text
Recent

Monthly Operations Pack
2m ago
Waiting for approval

Sales Analysis
Yesterday
Completed

Document Preparation
2d ago
Failed
```

Use actual run data.

---

# 23. HOME — EMPTY STATE

For new installation:

```text
No runs yet.

Describe a task above and SyncNode will build
the workflow for you.
```

---

# 24. NEW RUN TRANSITION

After submit:

```text
Home
 ↓
Run created
 ↓
Active Run screen
```

Do not keep the user waiting on a blank page.

Immediately show:

```text
RUN STARTING
```

while SSE initializes.

---

# 25. RUN CREATION FEEDBACK

Immediately display:

```text
RUN CREATED

Preparing workspace...
```

Then transition into:

```text
ACTIVE RUN
```

---

# 26. ACTIVE RUN SCREEN — PRIMARY SCREEN

This is the main product surface.

```text
┌──────────────────┬──────────────────────────────┬──────────────────────────┐
│ TASK MANAGEMENT  │ LIVE DESKTOP                │ AGENT INTELLIGENCE       │
│                  │                              │                          │
│ Current task     │                              │ Active Agent             │
│ Steps            │                              │ Summary                  │
│ Side tasks       │                              │ Chat                     │
│                  │                              │ Tools                    │
│                  │                              │ Thinking                 │
│                  │                              │ Model                    │
│                  │                              │ Approval                 │
│                  ├──────────────────────────────┤                          │
│                  │ WORKFLOW / TIMELINE          │                          │
│                  │ GRAPH                        │                          │
└──────────────────┴──────────────────────────────┴──────────────────────────┘
```

---

# 27. ACTIVE RUN HEADER

Display:

```text
<goal>
RUNNING
```

Metadata:

```text
elapsed time
model
agents active
```

where available.

---

# 28. ACTIVE RUN LEFT PANE

Left pane sections:

```text
TASK
CURRENT RUN
WORKFLOW
SIDE TASKS
RECENT ACTIVITY
```

---

# 29. LEFT PANE — TASK

Example:

```text
MONTHLY OPERATIONS PACK

Create report
Analyze spreadsheet
Create presentation
Draft email
```

Check states:

```text
✓
●
○
🔒
✕
```

---

# 30. LEFT PANE — ACTIVE TASK

The selected current step gets a subtle active background.

Example:

```text
● Create Excel analysis
```

Do not use large cards.

---

# 31. LEFT PANE — SIDE TASKS

Show non-critical/supporting tasks when supplied by backend plan/state.

Example:

```text
Side tasks

Knowledge lookup
Artifact verification
```

---

# 32. LEFT PANE — RUN NAVIGATION

Show:

```text
Back to Runs
Open Workspace
Open Artifacts
```

Do not stop or alter a run unless a real API action is used.

---

# 33. CENTER TOP — DESKTOP MIRROR

The desktop mirror is the visual hero.

It should feel like a live viewport into the computer being controlled.

Structure:

```text
┌─────────────────────────────────────────────┐
│ LIVE DESKTOP                     ● LIVE     │
├─────────────────────────────────────────────┤
│                                             │
│                                             │
│         actual observation / screen         │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ Microsoft Word · Word Agent · typing...    │
└─────────────────────────────────────────────┘
```

---

# 34. DESKTOP MIRROR — NO DATA

```text
DESKTOP

Waiting for a visual observation...
```

Do not show a fabricated screenshot.

---

# 35. DESKTOP MIRROR — OBSERVATION

When observation arrives:

```text
LIVE DESKTOP

Microsoft Word
Document1

Observed 15:42:14
```

Use the actual observation.

---

# 36. DESKTOP MIRROR — IMAGE TRANSITION

When a new screenshot arrives:

```text
old
→ fade
→ new
```

Optional:

```text
small scale 1.00 → 1.015
```

No dramatic cinematic zoom.

---

# 37. DESKTOP MIRROR — ACTIVE CONTROL

When a computer tool is active:

```text
LIVE CONTROL

Microsoft Word
computer.launch_app
```

This state comes from real events.

---

# 38. DESKTOP MIRROR — APPROVAL

At approval:

```text
LIVE DESKTOP
```

remains visible behind an overlay:

```text
REVIEW REQUIRED
```

Do not replace the desktop entirely.

---

# 39. DESKTOP MIRROR — ERROR

If observation is unavailable:

```text
VISUAL OBSERVATION UNAVAILABLE

Execution state remains available
in the workflow and timeline.
```

---

# 40. CENTER BOTTOM — WORKFLOW PANEL

The workflow panel contains:

```text
Graph
Timeline
```

Use tabs:

```text
WORKFLOW
TIMELINE
```

or a split view where appropriate.

---

# 41. WORKFLOW GRAPH

Use React Flow or equivalent.

Graph:

```text
PLAN
 ↓
WORD ─────┐
EXCEL ────┼──→ EMAIL
PPT ──────┘
              ↓
          APPROVAL
```

Actual nodes derive from the backend plan.

---

# 42. GRAPH NODE STATES

Use:

```text
PENDING
RUNNING
VERIFYING
RECOVERING
COMPLETED
FAILED
WAITING
```

Visual states must be driven by real events.

---

# 43. GRAPH NODE DESIGN

Example:

```text
┌──────────────────────────────┐
│ ● EXCEL AGENT                │
│                              │
│ excel.create                 │
│ RUNNING                      │
└──────────────────────────────┘
```

Compact.

Technical.

No giant rounded dashboard cards.

---

# 44. GRAPH — ACTIVE NODE

Use:

```text
subtle border glow
pulse
```

Do not continuously animate every node.

Only active nodes animate.

---

# 45. GRAPH — COMPLETED NODE

```text
✓ VERIFIED
```

The green state means backend verification passed where applicable.

---

# 46. GRAPH — RECOVERY NODE

```text
↻ RECOVERING
Attempt 2/3
```

Use a restrained amber state.

---

# 47. GRAPH — APPROVAL NODE

```text
🔒 APPROVAL
WAITING
```

Yellow/amber emphasis.

---

# 48. GRAPH — FAILED NODE

```text
✕ FAILED
```

Keep the node visible.

Do not erase the failure after recovery.

---

# 49. GRAPH NODE DETAIL

Click node:

Right panel opens:

```text
STEP
create_excel

Agent
Excel

Tool
excel.create

Status
COMPLETED

Verification
PASS
```

Timeline highlights related events.

---

# 50. GRAPH CONTROLS

Provide:

```text
Zoom in
Zoom out
Fit view
Reset
```

Keep controls unobtrusive.

---

# 51. GRAPH SELECTION

Selecting a node must:

```text
select step
→ highlight timeline events
→ update evidence
→ highlight agent
```

This is frontend-only selection state.

---

# 52. TIMELINE PANEL

Timeline is the operational history.

Example:

```text
15:42:10  Run accepted
15:42:11  Workspace ready
15:42:13  Knowledge retrieved
15:42:16  Plan validated
15:42:18  Word Agent started
15:42:18  Excel Agent started
15:42:19  PowerPoint Agent started
15:42:22  Excel verified
15:42:25  Email draft ready
15:42:26  Approval required
```

---

# 53. TIMELINE HEADER

Show:

```text
LIVE ACTIVITY

● LIVE
89 events
```

Actual count.

---

# 54. TIMELINE FILTERS

Filter chips:

```text
All
Agents
Tools
Observation
Verification
Recovery
Artifacts
Knowledge
Approval
```

Frontend-only filtering.

---

# 55. TIMELINE SEARCH

Search local events:

```text
Search activity...
```

Example:

```text
Excel
```

shows Excel-related events.

---

# 56. TIMELINE GROUPING

Group technical lifecycle events:

```text
✓ document.create_docx
Verified

▸ 7 events
```

Expanded:

```text
proposed
validated
authorized
started
invoked
completed
verified
```

---

# 57. TIMELINE EVENT TYPES

Render:

```text
run
plan
agent
tool
observation
verification
recovery
artifact
rag
approval
memory
terminal
```

---

# 58. TIMELINE — AGENT EVENT

Example:

```text
● WORD AGENT STARTED

Preparing document artifact
```

Use safe backend summary.

---

# 59. TIMELINE — TOOL EVENT

Example:

```text
● document.create_docx
Word Agent
RUNNING
```

---

# 60. TIMELINE — OBSERVATION

Example:

```text
◉ OBSERVATION CAPTURED

Microsoft Word
[thumbnail]
```

---

# 61. TIMELINE — VERIFICATION

Success:

```text
✓ VERIFICATION PASSED

file_exists
content_generated
```

Failure:

```text
✕ VERIFICATION FAILED

Spreadsheet structure mismatch
```

---

# 62. TIMELINE — RECOVERY

```text
↻ RECOVERY

Step: browser.type
Strategy: REOBSERVE
Attempt 2/3
```

---

# 63. TIMELINE — ARTIFACT

```text
FILE CREATED

SyncNode_Excel_<run>.xlsx
✓ Verified
```

---

# 64. TIMELINE — RAG

```text
KNOWLEDGE RETRIEVED

5 local documents
```

Expandable to provenance.

---

# 65. TIMELINE — APPROVAL

```text
🔒 APPROVAL REQUIRED

External communication is ready.
```

Click opens approval panel.

---

# 66. TIMELINE — TERMINAL

Completed:

```text
✓ RUN COMPLETE
```

Failed:

```text
✕ RUN FAILED
```

Cancelled:

```text
RUN CANCELLED
```

---

# 67. TIMELINE AUTO-SCROLL

Rules:

```text
user at bottom
→ auto-scroll

user scrolls up
→ stop auto-scroll

new events
→ "N new events"

click
→ return live
```

---

# 68. RIGHT PANEL — INTELLIGENCE

Right panel tabs:

```text
AGENT
CHAT
THINKING
TOOLS
MODEL
APPROVAL
EVIDENCE
```

The exact tab visibility can be context-sensitive.

---

# 69. RIGHT PANEL — AGENT TAB

Example:

```text
WORD AGENT

● RUNNING

Current Step
create_docx

Tool
document.create_docx

Capabilities
Document creation
Verification
```

---

# 70. AGENT ROSTER

Compact roster:

```text
● Supervisor      running
● Word            running
● Excel           running
● PowerPoint      running
○ Browser         waiting
```

Render dynamically from backend definitions/state.

---

# 71. RIGHT PANEL — CHAT

Chat-like presentation is allowed for safe status communication.

Example:

```text
SYNCNODE

I'm preparing the Word document before
the final email draft.
```

This is status communication, not hidden chain-of-thought.

---

# 72. CHAT — USER MESSAGE

User can see their current request:

```text
Create the monthly operations pack...
```

If a conversational backend endpoint does not exist, do not invent one.

The frontend should not pretend chat messages are being generated by a nonexistent API.

---

# 73. RIGHT PANEL — THINKING

Show:

```text
PLAN SUMMARY

1. Create Word report
2. Create Excel analysis
3. Create PowerPoint summary
4. Draft email
5. Verify artifacts
6. Request approval
```

No private reasoning.

---

# 74. RIGHT PANEL — CURRENT DECISION

Example:

```text
CURRENT DECISION

All required artifacts must be verified
before they are attached to the email draft.
```

Only if supplied by backend-safe summaries.

---

# 75. RIGHT PANEL — TOOLS

Show:

```text
CURRENT TOOL

excel.write_cell
● RUNNING

Agent
Excel

Resource
Excel
```

Below:

```text
Recent tools
✓ excel.create
✓ document.create_docx
● excel.write_cell
```

---

# 76. RIGHT PANEL — MODEL

Show:

```text
LOCAL MODEL

Gemma 4 E4B
Ollama
GPU

Profile
planner

Context
8192

Capabilities
Completion
Vision
Tools
Thinking
```

Use backend model-health data.

---

# 77. RIGHT PANEL — APPROVAL

When active, switch to:

```text
REVIEW REQUIRED

External communication

Recipient
demo@example.com

Subject
Monthly Operations Report

Attachments
✓ Word
✓ Excel
✓ PowerPoint

Nothing has been sent.

[ Reject ]         [ Approve ]
```

Use actual data.

---

# 78. APPROVAL OVERLAY

During approval, the main screen can receive a subtle global dim:

```text
desktop
graph
timeline
```

remain visible.

Approval card becomes the focus.

---

# 79. APPROVAL — APPROVE

Button:

```text
Approve
```

state:

```text
Submitting...
```

Then wait for backend confirmation.

Do not immediately switch to success.

---

# 80. APPROVAL — REJECT

Button:

```text
Reject
```

May open optional reason field.

Then:

```text
Submitting...
```

Wait for backend.

---

# 81. APPROVAL — FINAL

After backend confirms waiting:

```text
WAITING FOR APPROVAL
```

Nothing should indicate the external action occurred.

---

# 82. EVIDENCE PANEL

Evidence shows what actually happened.

Structure:

```text
EVIDENCE

Step
create_docx

Tool
document.create_docx

Observation
...

Verification
PASS

Assertions
✓ content_generated
✓ file_exists

Artifact
SyncNode_Word_<run>.docx
```

---

# 83. EVIDENCE — SCREENSHOT

Show:

```text
OBSERVATION
15:42:14

[ screenshot ]
```

Click expands.

---

# 84. EVIDENCE — ARTIFACT

Show:

```text
ARTIFACT

Word
SyncNode_Word_<run>.docx

Verified
✓

SHA256
...
```

---

# 85. EVIDENCE — ERROR

Example:

```text
FAILURE

verification failed

Reason
Expected cell value did not match observed value.

Recovery
Attempt 2
```

---

# 86. ARTIFACT SCREEN

Dedicated artifact screen.

Layout:

```text
Artifacts

┌──────────────┬────────────────────────────────────┐
│ Filters      │ Artifact                           │
│              │                                    │
│ Word         │ SyncNode_Word_<run>.docx           │
│ Excel        │ ✓ VERIFIED                         │
│ PowerPoint   │                                    │
│ Other        │ Producer: Word Agent               │
└──────────────┴────────────────────────────────────┘
```

---

# 87. ARTIFACT CARD

Show:

```text
WORD
SyncNode_Word_<run>.docx
✓ VERIFIED

Created
15:42

Producer
Word Agent
```

---

# 88. ARTIFACT FILTERS

Frontend filters:

```text
All
Word
Excel
PowerPoint
Other
Verified
Unverified
```

---

# 89. ARTIFACT DETAIL

Show:

```text
Artifact
id
run
producer
type
verification
hash
created_at
```

Where available.

---

# 90. ARTIFACT OPEN ACTION

Provide a safe:

```text
Open
```

only through controlled Electron/main-process integration.

Do not expose unrestricted shell or arbitrary filesystem access to renderer.

---

# 91. RUNS SCREEN

Runs list:

```text
RUNS

Search...

ACTIVE
Monthly Operations Pack
RUNNING

WAITING
Quarterly Report
WAITING FOR APPROVAL

COMPLETED
Sales Analysis
COMPLETED

FAILED
Document Migration
FAILED
```

---

# 92. RUN CARD

Example:

```text
MONTHLY OPERATIONS PACK
Create report + spreadsheet + presentation

WAITING FOR APPROVAL

3 artifacts
10 steps
3 agents

2m ago
```

Use actual returned data.

---

# 93. RUN DETAIL SCREEN

Run detail contains:

```text
Summary
Workflow
Timeline
Artifacts
Verification
Context
Audit
```

Historical runs are primarily read-only unless an API supports an action.

---

# 94. ACTIVE RUN VS HISTORY

Active:

```text
live stream
interactive approval
live desktop
animations
```

Historical:

```text
snapshot
timeline
graph
evidence
artifacts
audit
```

Reduce live-style animation in history.

---

# 95. KNOWLEDGE SCREEN

Structure:

```text
Knowledge

┌────────────────────┬────────────────────────────────────┐
│ Documents          │ Markdown editor                    │
│                    │                                    │
│ Policies           │ # Approval Rules                   │
│ Applications       │                                    │
│ Workflows          │ content...                         │
│ Tools              │                                    │
│ References         │                  [Save] [Reindex]  │
└────────────────────┴────────────────────────────────────┘
```

---

# 96. KNOWLEDGE LIST

Each row:

```text
Approval Rules
AUTHORITATIVE POLICY
Updated 2h ago
```

Backend trust value is authoritative.

---

# 97. KNOWLEDGE EDITOR

Use a serious Markdown editing surface.

Support:
- syntax highlighting
- line numbers optional
- preview optional
- save
- revert/history where API allows

Do not alter front matter semantics.

---

# 98. KNOWLEDGE HISTORY

Show:

```text
Version 4
Today
hash...

Version 3
Yesterday
hash...
```

Use backend history.

---

# 99. KNOWLEDGE SEARCH

Search bar:

```text
Search knowledge...
```

Results:

```text
Approval Rules
AUTHORITATIVE POLICY
Score 26.0
```

Use actual backend results.

---

# 100. KNOWLEDGE REINDEX

Button:

```text
Reindex
```

Click:

```text
Reindexing...
```

Wait for backend response.

---

# 101. AGENTS SCREEN

Dedicated agent catalog:

```text
AGENTS

Supervisor
Workflow coordination

Word
Document automation

Excel
Spreadsheet operations

PowerPoint
Presentation operations

Computer
Windows interaction

Browser
Browser/email

Verifier
Evidence verification

Recovery
Failure recovery
```

Render dynamically from `/api/v1/agents`.

---

# 102. AGENT DETAIL SCREEN

Show:

```text
Agent
Word

Capabilities
Document creation
Document inspection

Allowed tools
document.create_docx
document.read_docx
...
```

Use backend metadata.

---

# 103. AGENT LIVE STATE

When an agent is active, its detail view can show:

```text
RUNNING

Current run
Monthly Operations Pack

Current step
create_docx

Current tool
document.create_docx
```

---

# 104. TOOLS SCREEN

Tools catalog:

```text
TOOLS

Computer
Browser
Documents
Excel
PowerPoint
Filesystem
Writer
```

---

# 105. TOOL DETAIL SCREEN

Example:

```text
document.create_docx

Create DOCX

Risk
Medium

Side effect
IDEMPOTENT_LOCAL

Verification
Always

Input schema
...
```

Use actual backend metadata.

---

# 106. TOOL SCHEMA VIEW

Expandable:

```text
Input

path
string
required

content
string
required
```

Do not create execution controls unless an explicit backend API supports them.

---

# 107. LEARNING SCREEN

Structure:

```text
Learning

Workflow Memory
Candidate Strategies
```

---

# 108. WORKFLOW MEMORY

Example:

```text
Email draft workflow

Success
91%

Runs
18

Reward
9.6
```

Use actual backend values.

---

# 109. CANDIDATE STRATEGIES

Show:

```text
CANDIDATE

Create Office artifacts before compose

Status
CANDIDATE

Source
Run <id>

[ Review ]
```

---

# 110. LEARNING REVIEW

Review:

```text
Candidate Strategy
Summary
Tool sequence
Rationale
Source run
Lifecycle
```

Buttons follow existing backend lifecycle.

---

# 111. AUDIT SCREEN

Audit is technical and dense.

```text
AUDIT

001 run.created
002 run.started
003 rag.query
004 plan.created
005 agent.spawned
006 tool.authorized
...
```

---

# 112. AUDIT EVENT DETAIL

Click event:

```text
Audit event

Sequence
89

Type
approval.requested

Timestamp
...

Hash
...
```

---

# 113. AUDIT STATUS

Show:

```text
AUDIT CHAIN
✓ VERIFIED
```

only when verification is actually available from backend state.

---

# 114. SYSTEM HEALTH SCREEN

Show:

```text
SYSTEM HEALTH

Backend       ✓
Database      ✓
Model         ✓
RAG           ✓
Desktop       ✓
Browser       ✓
```

Each can expand.

---

# 115. MODEL HEALTH DETAIL

Show:

```text
Gemma 4 E4B
GPU
Context
Quantization
Capabilities
Latency
```

Actual backend values only.

---

# 116. SETTINGS SCREEN

Frontend settings may include:

```text
Appearance
Layout
Animations
Backend URL
Developer diagnostics
Keyboard shortcuts
```

Do not expose frontend controls that imply unsupported backend capabilities.

---

# 117. SETTINGS — APPEARANCE

Options:

```text
Dark
System
```

Primary SyncNode theme remains dark.

---

# 118. SETTINGS — LAYOUT

Controls:

```text
Sidebar width
Agent panel width
Workflow panel height
Compact mode
```

Persist locally.

---

# 119. SETTINGS — MOTION

Options:

```text
Full
Reduced
Off
```

Also respect:

```text
prefers-reduced-motion
```

---

# 120. SETTINGS — DEVELOPER MODE

Optional:

```text
Show SSE diagnostics
Show event payloads
Show API latency
Show state inspector
```

Disabled by default.

---

# 121. COMMAND PALETTE

Shortcut:

```text
Ctrl/Cmd + Shift + P
```

Commands:

```text
New Run
Open Runs
Open Knowledge
Open Agents
Open Tools
Open Artifacts
Open Learning
Open Audit
Open Settings
```

---

# 122. GLOBAL SEARCH

Command palette can also search:

```text
runs
knowledge
agents
tools
```

Do not create unsupported backend search APIs.

Use existing endpoints or local filtering.

---

# 123. NOTIFICATIONS

Use subtle toasts:

```text
Run started
Artifact verified
Recovery completed
Knowledge saved
```

Do not use toasts for approval requests.

Approval gets a dedicated blocking surface.

---

# 124. APPROVAL NOTIFICATION

When approval requested:

```text
REVIEW REQUIRED
```

The application should visually redirect attention.

---

# 125. ERROR TOAST

Example:

```text
Could not load artifacts.
[Retry]
```

Never display raw stack traces.

---

# 126. LOADING STATES

Every screen needs:

```text
loading
empty
success
error
```

Do not use blank content while data loads.

---

# 127. EMPTY STATES

Examples:

Runs:

```text
No runs yet.
Start your first task.
```

Agents:

```text
No agent definitions available.
```

Tools:

```text
No tools available.
```

Knowledge:

```text
No knowledge documents.
```

Artifacts:

```text
No artifacts yet.
```

---

# 128. ERROR STATES

Always communicate:

```text
what failed
what resource was affected
possible next safe action
```

without inventing causes.

---

# 129. DESKTOP MIRROR FALLBACK

If no image:

```text
Visual observation unavailable
```

but keep:

```text
application
window
step
timestamp
```

if available.

---

# 130. SSE DISCONNECTED STATE

Show:

```text
◌ RECONNECTING TO LIVE RUN...
```

Do not show:

```text
RUN FAILED
```

unless backend run state says failed.

---

# 131. REST FAILURE STATE

If the UI cannot load a snapshot:

```text
Unable to load run details.

[Retry]
```

This is not automatically a run failure.

---

# 132. RUN FAILURE STATE

When backend says:

```text
failed
```

show:

```text
RUN FAILED

Failed step
Reason

[View Evidence]
```

---

# 133. RUN COMPLETION STATE

When backend says:

```text
completed
```

show:

```text
RUN COMPLETE

Verified artifacts
N

Steps
N
```

where counts exist.

---

# 134. WAITING APPROVAL STATE

When:

```text
waiting_approval
```

show:

```text
WAITING FOR APPROVAL

The workflow has paused safely.
Nothing has been sent.
```

Only make the latter statement if the backend contract confirms the send was not executed / the workflow is at the intended approval state.

---

# 135. WORKFLOW REPLAY

Historical runs may support a visual replay mode.

Replay must be frontend-only.

It must never execute tools.

UI:

```text
REPLAY
```

with timeline cursor.

---

# 136. REPLAY CONTROLS

Optional:

```text
Play
Pause
Step forward
Timeline scrub
```

The replay only animates existing events/evidence.

---

# 137. NO RE-EXECUTION FROM REPLAY

Never use replay to call:

```text
POST /runs
```

or execute a tool.

It is visual only.

---

# 138. ARTIFACT RELATIONSHIP VIEW

A run detail screen may show:

```text
Run
 │
 ├─ Word artifact
 ├─ Excel artifact
 ├─ PowerPoint artifact
 └─ Email draft
```

Use backend artifact relationships.

---

# 139. RAG PROVENANCE VIEW

Show:

```text
Knowledge used

Approval Rules
authoritative_policy

Workspace Rules
authoritative_policy

Email Draft
workflow
```

Use actual backend values.

---

# 140. STEP DETAIL

Each step detail:

```text
Step
agent
tool
status
verification
retries
evidence
artifact
```

Only fields supported by backend.

---

# 141. EVENT DETAIL DRAWER

Generic drawer:

```text
Event
Type
Timestamp
Run
Agent
Step
Tool
Payload
```

Large payloads collapsed.

---

# 142. MOBILE-LIKE PANELS ARE NOT PRIMARY

The app is desktop-first.

Do not redesign into:
- stacked mobile cards
- dashboard tile grid

on normal desktop sizes.

---

# 143. PANE RESIZING

Users can resize:

```text
left panel
right panel
workflow panel
```

Use drag handles.

Keep minimum widths.

---

# 144. PANE STATE PERSISTENCE

Persist:

```text
left width
right width
workflow height
collapsed sidebar
```

Frontend-only.

---

# 145. KEYBOARD SHORTCUTS

Recommended:

```text
Ctrl/Cmd + K
New task / command

Ctrl/Cmd + Shift + P
Command palette

Ctrl/Cmd + B
Toggle sidebar

Ctrl/Cmd + J
Toggle workflow

Esc
Close overlay

Ctrl/Cmd + Enter
Submit task
```

---

# 146. FOCUS MANAGEMENT

Approval overlay:

```text
focus approve/reject controls
```

Modal close:

```text
restore previous focus
```

Keyboard navigation must be predictable.

---

# 147. ACCESSIBILITY

Support:
- semantic buttons
- labels
- keyboard focus
- status text
- reduced motion
- accessible contrast
- screen reader-friendly state descriptions

Never rely on color alone.

---

# 148. ANIMATION SYSTEM

Use one coherent animation system.

Recommended:
- Framer Motion
- CSS transitions

Use motion for:

```text
splash
pane transitions
state changes
graph nodes
agent activity
timeline arrival
approval
artifact arrival
```

---

# 149. ANIMATION TIMING

Typical:

```text
micro interaction
120–180ms

panel transition
180–260ms

major screen transition
250–450ms

splash stage
600–900ms
```

Do not make ordinary interactions slow.

---

# 150. ANIMATION EASING

Use smooth, professional easing.

Avoid:
- elastic excessive bounce
- giant spring motion
- exaggerated camera movement

---

# 151. AGENT ANIMATION

Running:

```text
subtle pulse
```

Waiting:

```text
slow opacity shift
```

Completed:

```text
check
```

Failed:

```text
small state transition
```

---

# 152. TOOL ANIMATION

Running:

```text
spinner
```

Authorized:

```text
small approval/check state
```

Completed:

```text
check
```

Verified:

```text
check + subtle settle
```

---

# 153. ARTIFACT ANIMATION

New artifact:

```text
fade + translate
```

Verified:

```text
badge appears
```

---

# 154. RECOVERY ANIMATION

Use:

```text
amber circular activity indicator
```

with:

```text
Attempt 2/3
```

---

# 155. APPROVAL ANIMATION

Transition:

```text
normal
→ slight environment dim
→ boundary pulse
→ approval card
```

No screen takeover unless necessary.

---

# 156. DESKTOP SCREENSHOT ANIMATION

New observation:

```text
crossfade
```

Avoid flashing.

---

# 157. GRAPH ANIMATION

Edges can animate while active:

```text
flowing dash
```

only for currently active paths.

Do not animate all edges forever.

---

# 158. TERMINAL ANIMATION

Completed:

```text
active states settle
checks appear
```

Failed:

```text
motion stops
failure highlighted
```

Waiting:

```text
workflow pauses
approval boundary remains visible
```

---

# 159. NO FAKE ANIMATION

Never do:

```text
agent appears running
```

because a timer says so.

Instead:

```text
agent.started
```

causes the animation.

---

# 160. NO FAKE THINKING

Do not animate:

```text
"thinking..."
```

unless the backend provides an appropriate safe activity state.

Prefer:

```text
PLANNING
CURRENT ACTION
DECISION SUMMARY
```

---

# 161. NO FAKE TOOL CALLS

The UI must not display:

```text
fake tool started
```

for visual polish.

Everything must correspond to actual backend data.

---

# 162. SCREEN STATE MODEL

Each screen should have:

```text
initial
loading
ready
empty
error
```

Active run additionally:

```text
live
reconnecting
approval
terminal
```

---

# 163. HOME SCREEN DATA

Reads:

```text
health/ready
health/model
recent run data
```

Writes:

```text
POST /runs
```

---

# 164. ACTIVE RUN DATA

Reads:

```text
run
steps
tools
observations
verifications
artifacts
context
audit
```

Live:

```text
SSE
```

Writes:

```text
terminate
approval decision
```

---

# 165. KNOWLEDGE DATA

Reads/writes existing knowledge endpoints.

---

# 166. AGENT DATA

Reads:

```text
GET /api/v1/agents
```

and run events.

---

# 167. TOOL DATA

Reads:

```text
GET /api/v1/tools
GET /api/v1/tools/{key}
```

---

# 168. LEARNING DATA

Reads:

```text
/learning/memory
/learning/candidates
```

Writes:

```text
review candidate
```

---

# 169. AUDIT DATA

Reads:

```text
/audit
```

---

# 170. API BOUNDARY

All API calls go through:

```text
frontend API client
```

No random fetch calls inside components.

---

# 171. SSE BOUNDARY

All active run event subscriptions go through:

```text
run stream manager
```

No component-level EventSource duplication.

---

# 172. STATE BOUNDARY

The state layer owns:

```text
run
agents
tools
graph
timeline
observations
verification
recovery
artifacts
approval
context
audit
```

Components render state.

---

# 173. SCREEN ROUTES

Recommended:

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

---

# 174. SCREEN TRANSITIONS

Home → Run:

```text
fast transition
```

Run → Knowledge:

```text
preserve active run
```

Knowledge → Run:

```text
rehydrate/reselect
```

Do not terminate active backend work due to navigation.

---

# 175. ACTIVE RUN PERSISTENCE

On route change:

```text
active run remains active
```

Returning:

```text
hydrate REST
connect/reuse SSE
```

---

# 176. ELECTRON RESTART

On restart:

```text
splash
→ health
→ runs
→ identify active/waiting runs
→ hydrate
→ resume visualization
```

Do not automatically restart backend execution.

---

# 177. APP CLOSE

On close:

```text
disconnect frontend streams
```

Do not terminate active run automatically unless explicitly designed and documented.

---

# 178. SYSTEM WINDOW CONTROLS

Electron main process handles:
- minimize
- maximize
- close

Renderer may trigger through safe preload APIs.

---

# 179. SECURE ELECTRON

Use:

```text
contextIsolation: true
nodeIntegration: false
```

and a minimal preload bridge.

Do not expose arbitrary Node APIs.

---

# 180. FRONTEND FILE ACCESS

Renderer should not read arbitrary:

```text
C:\...
```

paths.

Use backend-approved artifact references or safe main-process functionality.

---

# 181. BACKEND CONTRACT VERSIONING

Treat:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

as frozen contracts.

Additive fields:

```text
ignore safely if unused
```

Breaking changes:

```text
stop frontend implementation
document separately
do not patch backend here
```

---

# 182. FINAL FRONTEND GOLDEN WORKFLOW

The frontend must visually support the existing real golden run:

```text
Windows Search
 ↓
Microsoft Word
 ↓
new Word document
 ↓
Excel
 ↓
PowerPoint
 ↓
email compose
 ↓
three current-run artifacts
 ↓
verification
 ↓
approval
 ↓
WAITING FOR APPROVAL
```

Electron does not execute these actions itself.

It visualizes backend execution.

---

# 183. GOLDEN RUN — LEFT PANE

At final state:

```text
CURRENT TASK

Monthly Operations Pack

✓ Word
✓ Excel
✓ PowerPoint
✓ Email Draft
🔒 Approval
```

---

# 184. GOLDEN RUN — CENTER

Center upper:

```text
LIVE DESKTOP
Email Draft / latest observation
```

Center lower:

```text
Word ✓
Excel ✓
PowerPoint ✓
Email ✓
Approval 🔒
```

---

# 185. GOLDEN RUN — RIGHT

```text
REVIEW REQUIRED

3 verified artifacts attached

Nothing has been sent.

[Reject] [Approve]
```

---

# 186. GOLDEN RUN — STATUS BAR

```text
● LOCAL
● BACKEND CONNECTED
WAITING FOR APPROVAL
```

---

# 187. FINAL RUN EVIDENCE

The user should be able to inspect:

```text
Word artifact
Excel artifact
PowerPoint artifact
verification
RAG provenance
audit
workflow memory
approval
```

all from the same run.

---

# 188. NO BACKEND CHANGES DURING UI QA

If anything looks inconsistent:

```text
inspect frontend mapping first
```

Do not change backend.

Examples:

```text
wrong event rendering
→ fix event mapper

wrong graph status
→ fix reducer

wrong approval UI
→ fix approval state mapping

wrong screenshot
→ fix observation mapper
```

---

# 189. FRONTEND QA — SCREEN CHECKLIST

## Splash

```text
[ ] identity
[ ] health
[ ] model
[ ] system
[ ] transition
[ ] unavailable state
```

## Home

```text
[ ] task composer
[ ] run action
[ ] recent runs
[ ] health strip
[ ] empty state
```

## Active Run

```text
[ ] left task area
[ ] desktop mirror
[ ] workflow graph
[ ] timeline
[ ] agent panel
[ ] tool panel
[ ] approval
[ ] evidence
```

## Runs

```text
[ ] list
[ ] filters
[ ] detail
[ ] history
```

## Knowledge

```text
[ ] list
[ ] editor
[ ] history
[ ] search
[ ] reindex
```

## Agents

```text
[ ] catalog
[ ] detail
[ ] live state
```

## Tools

```text
[ ] catalog
[ ] detail
[ ] schema
```

## Artifacts

```text
[ ] list
[ ] filter
[ ] detail
[ ] safe open
```

## Learning

```text
[ ] memory
[ ] candidates
[ ] review
```

## Audit

```text
[ ] event list
[ ] detail
[ ] chain status
```

## Settings

```text
[ ] appearance
[ ] layout
[ ] motion
[ ] backend URL
[ ] diagnostics
```

---

# 190. FRONTEND QA — LIVE RUN CHECKLIST

```text
[ ] POST run works
[ ] SSE opens immediately
[ ] run state updates
[ ] plan appears
[ ] agents appear
[ ] tools appear
[ ] desktop updates
[ ] timeline updates
[ ] graph updates
[ ] verification updates
[ ] recovery updates
[ ] artifacts appear
[ ] RAG appears
[ ] approval appears
[ ] terminal state correct
```

---

# 191. FRONTEND QA — APPROVAL

```text
[ ] approval card visible
[ ] correct action
[ ] correct risk
[ ] artifacts shown
[ ] nothing falsely marked sent
[ ] approve submits
[ ] reject submits
[ ] backend confirmation updates state
```

---

# 192. FRONTEND QA — RECONNECT

```text
[ ] disconnect
[ ] reconnect state
[ ] REST reconciliation
[ ] no duplicate events
[ ] no duplicate artifacts
[ ] live stream resumes
```

---

# 193. FRONTEND QA — ERROR

```text
[ ] API error
[ ] SSE error
[ ] run failed
[ ] verification failed
[ ] recovery
[ ] unavailable screenshot
[ ] unavailable health
```

---

# 194. FRONTEND QA — ACCESSIBILITY

```text
[ ] keyboard
[ ] focus
[ ] reduced motion
[ ] screen reader labels
[ ] status not color-only
```

---

# 195. FRONTEND QA — PERFORMANCE

```text
[ ] no full-app rerender per SSE event
[ ] timeline virtualization where needed
[ ] screenshot throttling
[ ] smooth graph
[ ] responsive approval
[ ] stable long-running session
```

---

# 196. FRONTEND QA — SECURITY

```text
[ ] nodeIntegration disabled
[ ] contextIsolation enabled
[ ] no direct shell
[ ] no direct Python
[ ] no direct database
[ ] no direct Ollama
[ ] no backend imports
```

---

# 197. FINAL FRONTEND IMPLEMENTATION ORDER

Build:

```text
1. Electron shell
2. secure preload
3. splash sequence
4. health integration
5. home
6. API client
7. SSE manager
8. state model
9. runs
10. active run
11. four-zone layout
12. desktop mirror
13. workflow graph
14. timeline
15. agent panel
16. tool panel
17. verification/evidence
18. artifacts
19. approval
20. knowledge
21. agents
22. tools
23. learning
24. audit
25. settings
26. command palette
27. animations
28. accessibility
29. error/reconnect handling
30. integration tests
```

---

# 198. FINAL IMPLEMENTATION RULE

Do not create separate disconnected screens.

Every screen must fit one coherent product.

The navigation should feel like:

```text
SYNCNODE
│
├─ Home
│
├─ Runs
│    └─ Active Run
│          ├─ Agents
│          ├─ Graph
│          ├─ Timeline
│          ├─ Desktop
│          ├─ Evidence
│          └─ Approval
│
├─ Workspace
├─ Knowledge
├─ Agents
├─ Tools
├─ Artifacts
├─ Learning
├─ Audit
└─ Settings
```

---

# 199. FINAL VISUAL PRINCIPLE

The most important screen is the active run.

It must visually communicate:

```text
LEFT:
WHAT IS BEING DONE

CENTER:
WHAT IS HAPPENING ON THE COMPUTER

BOTTOM CENTER:
HOW THE WORKFLOW IS PROGRESSING

RIGHT:
WHICH AGENT IS WORKING + WHAT THE USER NEEDS TO KNOW
```

---

# 200. FINAL USER TRUST PRINCIPLE

At every moment:

```text
WHAT IS SHOWN
=
WHAT THE BACKEND ACTUALLY REPORTS
```

Never:

```text
visual polish
>
truth
```

The interface must make the system understandable without pretending work occurred.

---

# 201. FINAL FRONTEND DEFINITION OF DONE

The complete screen system is done when:

```text
[ ] Electron launches
[ ] splash works
[ ] system health works
[ ] Home works
[ ] Runs works
[ ] Active Run works
[ ] four-zone IDE layout works
[ ] Desktop mirror works
[ ] Workflow graph works
[ ] Timeline works
[ ] Agent panel works
[ ] Tool activity works
[ ] Evidence works
[ ] Artifacts work
[ ] Approval works
[ ] Knowledge works
[ ] Agents screen works
[ ] Tools screen works
[ ] Learning works
[ ] Audit works
[ ] Settings works
[ ] Command palette works
[ ] keyboard navigation works
[ ] animations work
[ ] reduced motion works
[ ] reconnect works
[ ] terminal reconciliation works
[ ] unknown events do not crash
[ ] no fabricated activity
[ ] no hidden chain-of-thought
[ ] no backend modifications
```

---

# 202. FINAL INTEGRATION PRINCIPLE

The frontend should make this backend architecture visible:

```text
USER
 ↓
TASK
 ↓
UNDERSTANDING
 ↓
KNOWLEDGE
 ↓
PLAN
 ↓
AGENTS
 ↓
PARALLEL WORK
 ↓
TOOLS
 ↓
DESKTOP / FILE OPERATIONS
 ↓
OBSERVATION
 ↓
VERIFICATION
 ↓
RECOVERY
 ↓
ARTIFACTS
 ↓
APPROVAL
 ↓
RESULT
```

Not through technical jargon everywhere, but through a coherent visual language.

---

# 203. FINAL ABSOLUTE BACKEND RESTRICTION

**DO NOT TOUCH THE BACKEND.**

This means:

```text
NO Python edits
NO FastAPI edits
NO LangGraph edits
NO LangChain edits
NO database edits
NO tool edits
NO agent-runtime edits
NO execution-engine edits
NO recovery-engine edits
NO policy edits
NO verification-engine edits
NO SSE-generation edits
NO API-route edits
NO schema edits
```

Only frontend work:

```text
Electron
React
TypeScript
CSS/Tailwind
shadcn/Radix
Framer Motion
React Flow
API client
SSE client
frontend stores
frontend tests
```

---

# 204. FINAL IMPLEMENTING-EDITOR COMMAND

Read all SyncNode documentation in `docs/` before implementation.

Read:

```text
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
docs/FRONTEND_API_INTEGRATION.md
docs/FRONTEND_SSE_STATE_MODEL.md
docs/FRONTEND_AGENT_TIMELINE.md
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

Then build the entire frontend from this screen specification.

Do not build only the visual shell.

Do not build only mock screens.

Do not build only disconnected pages.

Wire the real:

```text
REST
+
SSE
+
state model
+
run lifecycle
+
agent lifecycle
+
tool lifecycle
+
graph
+
desktop observations
+
verification
+
recovery
+
artifacts
+
knowledge
+
RAG provenance
+
learning
+
approval
+
audit
```

through the actual backend contracts.

---

# 205. FINAL DELIVERABLE

The final Electron application should feel like:

```text
        SYN C N O D E

   AI IDE FOR AUTONOMOUS WORK
             +
     LOCAL DESKTOP AGENT
             +
       WORKFLOW ENGINE
             +
      LIVE OBSERVABILITY
             +
       HUMAN CONTROL
```

The user enters one task.

SyncNode visibly turns that task into:

```text
a workflow
an agent activity stream
a desktop operation
a graph
a timeline
tool calls
verification
artifacts
approval
```

all synchronized from the real backend.

---

# 206. FINAL COMMAND TO THE IMPLEMENTING EDITOR

**BUILD THE FRONTEND END TO END.**

Read the complete documentation first.

Use the supplied four-zone design as the main IDE layout.

Use the existing backend REST + SSE contracts.

Connect every supported feature.

Make every screen real and functional.

Make all live animation event-driven.

Make all state backend-derived.

Make Electron secure.

Make the interface polished, technical, minimal and premium.

And most importantly:

> **DO NOT TOUCH THE BACKEND.**
>
> **DO NOT MODIFY BACKEND MODULES.**
>
> **DO NOT PATCH THE API TO FIT THE FRONTEND.**
>
> **THE FRONTEND MUST ADAPT TO THE EXISTING BACKEND CONTRACTS.**

The backend is the authority.

The Electron application is the visual workspace and human-control surface.

Build everything else end to end.
