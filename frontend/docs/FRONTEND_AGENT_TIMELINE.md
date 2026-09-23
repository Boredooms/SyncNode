# FRONTEND_AGENT_TIMELINE.md

# SyncNode Electron Frontend
## Agent Timeline, Live Execution Visualization & AI Workspace Behavior

> **Scope: FRONTEND ONLY**
>
> This document defines how the Electron frontend visualizes SyncNode's real agent activity, workflow execution, tool calls, observations, verification, recovery, artifacts, approvals, and terminal states.
>
> **ABSOLUTE RULE: DO NOT MODIFY THE BACKEND.**
>
> Do not modify Python modules, LangGraph, LangChain, ModelGateway, ExecutionEngine, RecoveryEngine, ToolRegistry, AgentRegistry, VerificationEngine, API routes, database logic, persistence, SSE generation, or backend schemas.
>
> The frontend consumes the existing REST + SSE contracts only.
>
> The UI must visualize actual backend activity. It must never fabricate agent work, tool execution, desktop activity, verification, or completion.

---

# 1. PURPOSE

SyncNode is not supposed to look like a conventional admin dashboard.

The live execution experience should feel like an:

```text
AI IDE
+
AUTONOMOUS WORKFLOW ENGINE
+
DESKTOP AGENT
+
LIVE OBSERVABILITY CONSOLE
+
HUMAN APPROVAL WORKSPACE
```

The Agent Timeline is one of the primary surfaces that creates this experience.

The user should continuously understand:

```text
What did I ask?
        ↓
What is being planned?
        ↓
Which agent is working?
        ↓
What step is active?
        ↓
Which tool is running?
        ↓
What happened on the desktop?
        ↓
What was observed?
        ↓
Did verification pass?
        ↓
Is recovery occurring?
        ↓
What artifacts were produced?
        ↓
Does the workflow require my approval?
        ↓
What is the final state?
```

The timeline must answer these questions visually without exposing private chain-of-thought.

---

# 2. PRIMARY DESIGN PRINCIPLE

The timeline is:

```text
EVENT → STATE → VISUALIZATION
```

not:

```text
MODEL → TEXT → CHAT BUBBLE
```

The backend's event stream is authoritative.

The frontend converts backend events into:

- timeline entries
- agent cards
- workflow-node states
- tool rows
- desktop status
- verification badges
- recovery indicators
- artifact cards
- approval state

---

# 3. CORE EXECUTION VISUAL

The main active-run experience follows the established four-zone SyncNode layout:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                                     │
├───────────────────┬─────────────────────────────────────┬───────────────────┤
│ TASK / WORKSPACE  │ LIVE DESKTOP MIRROR                │ AGENT INTELLIGENCE │
│                   │                                     │                   │
│ Active task       │                                     │ Agent             │
│ Subtasks          │                                     │ Summary           │
│ Recent runs       │                                     │ Chat/status       │
│ Workflows         │                                     │ Tools             │
│ Workspace         │                                     │ Thinking summary  │
│                   │                                     │ Approval          │
│                   ├─────────────────────────────────────┤                   │
│                   │ WORKFLOW GRAPH / TIMELINE           │                   │
├───────────────────┴─────────────────────────────────────┴───────────────────┤
│ STATUS BAR                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

The bottom-center timeline is the continuous execution history.

The graph and timeline should remain synchronized.

---

# 4. TIMELINE IS NOT A CHAT

Do not turn the timeline into conversational messages.

Bad:

```text
AI:
I'm now going to work on the Excel file...
```

Good:

```text
15:42:10
Excel Agent
excel.create
RUNNING
Creating workbook

15:42:12
Excel Agent
excel.create
COMPLETED
Verification pending
```

The timeline should be operational.

---

# 5. THREE-LAYER EXECUTION VIEW

The main run visualization has three synchronized layers:

```text
LAYER 1
AGENT
Who is doing the work?

LAYER 2
STEP / TOOL
What is being done?

LAYER 3
EVIDENCE
What happened and did it verify?
```

Example:

```text
Word Agent
    │
    ├─ document.create_docx
    │
    ├─ observation.captured
    │
    └─ verification.passed
```

---

# 6. EVENT SOURCES

Primary live events come from:

```text
GET /api/v1/runs/{run_id}/events
```

Initial/historical data comes from:

```text
GET /api/v1/runs/{run_id}
GET /api/v1/runs/{run_id}/steps
GET /api/v1/runs/{run_id}/tools
GET /api/v1/runs/{run_id}/observations
GET /api/v1/runs/{run_id}/verifications
GET /api/v1/runs/{run_id}/artifacts
GET /api/v1/runs/{run_id}/context
GET /api/v1/runs/{run_id}/audit
```

The timeline uses the existing backend contract.

Do not create a second event system in the frontend.

---

# 7. LIVE EVENT PIPELINE

The frontend flow is:

```text
SSE
 ↓
Event Parser
 ↓
Event Validation
 ↓
Event Normalizer
 ↓
Event Deduplication
 ↓
Domain Reducers
 ↓
Timeline Store
 ↓
Agent Store
 ↓
Tool Store
 ↓
Workflow Store
 ↓
UI
```

A single event may update several stores.

Example:

```text
tool.started
→ ToolStore
→ StepStore
→ AgentStore
→ TimelineStore
→ WorkflowStore
```

---

# 8. CENTRAL EVENT ROUTER

Create a centralized event routing layer.

Suggested:

```text
src/services/sse/eventRouter.ts
```

Responsibilities:

- inspect event_type
- validate supported event
- route to reducer(s)
- append timeline item
- preserve correlation
- ignore unknown events safely

Do not allow every component to subscribe directly to SSE.

---

# 9. EVENT CATEGORIES

Group events into:

```text
RUN
PLAN
AGENT
TOOL
OBSERVATION
VERIFICATION
RECOVERY
ARTIFACT
KNOWLEDGE/RAG
APPROVAL
MEMORY
TERMINAL
TRANSPORT
```

This is primarily a frontend organization mechanism.

Actual event names remain the backend contract.

---

# 10. RUN EVENTS

Current relevant events include:

```text
run.created
run.started
run.waiting_approval
run.completed
run.failed
run.cancelled
```

Render:

```text
run.created
→ "Run accepted"

run.started
→ "Workspace ready"

run.waiting_approval
→ "Waiting for approval"

run.completed
→ "Run complete"

run.failed
→ "Run failed"

run.cancelled
→ "Run cancelled"
```

---

# 11. PLAN EVENTS

Relevant:

```text
intent.completed
plan.created
plan.validated
plan.wave_dispatched
```

Timeline:

```text
Intent completed
Plan created
Plan validated
Wave dispatched
```

The graph should update at the same time.

---

# 12. AGENT EVENTS

Relevant:

```text
agent.spawned
agent.started
agent.waiting
agent.plan_summary
agent.completed
agent.failed
agent.cancelled
```

These create the live agent experience.

---

# 13. AGENT SPAWNED

When:

```text
agent.spawned
```

arrives:

Timeline entry:

```text
AGENT SPAWNED
Word Agent
Preparing create_docx
```

Agent card:

```text
Word
SPAWNED
```

Graph:

```text
Word node
→ visible
→ pending/queued
```

Animation:

```text
fade + subtle scale in
```

---

# 14. AGENT STARTED

When:

```text
agent.started
```

arrives:

Agent card:

```text
● RUNNING
```

Timeline:

```text
WORD AGENT
Started
```

Graph node:

```text
RUNNING
```

Animation:

```text
subtle pulse
```

---

# 15. AGENT PLAN SUMMARY

When:

```text
agent.plan_summary
```

arrives, show the safe summary.

Example:

```text
Word Agent

Preparing the document artifact before the
email composition step.
```

Do NOT show:

```text
private chain-of-thought
hidden reasoning
token-by-token thought
```

Only backend-provided safe summaries.

---

# 16. AGENT WAITING

When:

```text
agent.waiting
```

arrives:

```text
Word Agent
WAITING
```

Possible visual explanation:

```text
Waiting for dependency
Waiting for approval
Waiting for resource
```

Only display the reason if the backend provides it.

Do not infer a reason.

---

# 17. AGENT COMPLETED

When:

```text
agent.completed
```

arrives:

Agent card:

```text
✓ COMPLETED
```

Timeline:

```text
Word Agent completed
```

Graph node:

```text
COMPLETED
```

Animation:

```text
pulse stop
→ check appears
```

---

# 18. AGENT FAILED

When:

```text
agent.failed
```

arrives:

```text
Word Agent
FAILED
```

Show backend-provided safe error summary.

Add:

```text
[View Evidence]
```

The failure should propagate to the corresponding step/tool state.

---

# 19. AGENT CANCELLED

When:

```text
agent.cancelled
```

arrives:

```text
Word Agent
CANCELLED
```

Use a neutral cancellation state.

Do not style cancellation as failure unless the backend reports the run as failed.

---

# 20. TOOL EVENT LIFECYCLE

Tool lifecycle:

```text
tool.proposed
      ↓
tool.validated
      ↓
tool.authorized
      ↓
tool.started
      ↓
tool.invoked
      ↓
tool.completed
```

Failure branch:

```text
tool.failed
```

Verification:

```text
observation.captured
      ↓
verification.passed / failed
```

---

# 21. TOOL PROPOSED

Visual:

```text
TOOL PROPOSED

document.create_docx
Agent: Word
```

Status:

```text
PENDING AUTHORIZATION
```

Do not imply execution has begun.

---

# 22. TOOL VALIDATED

Visual:

```text
✓ Tool validated
document.create_docx
```

This indicates schema/registry validation has happened.

Do not show this as successful execution.

---

# 23. TOOL AUTHORIZED

Visual:

```text
✓ AUTHORIZED
```

Optional metadata:

```text
Agent: Word
Risk: medium
```

Only show fields returned by backend events.

---

# 24. TOOL STARTED

This is the strongest active-tool state.

Example:

```text
● RUNNING

document.create_docx

Word Agent
```

The related graph node pulses.

The agent card shows:

```text
Current tool
document.create_docx
```

---

# 25. TOOL INVOKED

If backend provides:

```text
tool.invoked
```

show concise technical information.

Example:

```text
INPUT

path
SyncNode_Word_<run>.docx

content
Generated report paragraph...
```

Large inputs must be truncated.

Sensitive information should not be exposed unnecessarily.

---

# 26. TOOL COMPLETED

Show:

```text
✓ COMPLETED
document.create_docx
```

But do not automatically call it verified.

The next evidence layer determines verification.

---

# 27. TOOL FAILED

Show:

```text
✕ FAILED
document.create_docx

Reason
<backend error summary>
```

Then, if recovery starts:

```text
↻ RECOVERING
```

The timeline should make the transition obvious.

---

# 28. OBSERVATION EVENT

When:

```text
observation.captured
```

arrives:

```text
OBSERVED
Microsoft Word
```

Update:

- desktop mirror
- evidence drawer
- timeline
- selected step

Where a screenshot exists, show a thumbnail.

---

# 29. OBSERVATION TIMELINE ITEM

Example:

```text
15:42:14

OBSERVATION

Microsoft Word
Window: Document1

Screenshot captured

[View]
```

Clicking:

```text
View
```

selects the observation in the center/right evidence surface.

---

# 30. VERIFICATION EVENTS

```text
verification.passed
verification.failed
```

These are more important than simple tool completion.

The visual hierarchy should communicate:

```text
Tool completed
≠
Verified success
```

---

# 31. VERIFICATION PASSED

Display:

```text
✓ VERIFIED

Word document content
```

or:

```text
✓ VERIFIED
file_exists
```

Where assertion details are provided:

```text
✓ content_generated
✓ file_exists
```

---

# 32. VERIFICATION FAILED

Display:

```text
✕ VERIFICATION FAILED

Spreadsheet structure did not match expected state.
```

Add:

```text
Recovery may follow
```

only if the backend actually reports recovery.

---

# 33. RECOVERY EVENTS

Relevant:

```text
recovery.started
recovery.attempted
recovery.completed
recovery.exhausted
```

These need a dedicated visual identity.

---

# 34. RECOVERY STARTED

Example:

```text
↻ RECOVERY STARTED

Step
browser.type

Failure
selector mismatch

Strategy
REOBSERVE
```

Show only backend-provided classification.

---

# 35. RECOVERY ATTEMPTED

Example:

```text
RECOVERY
Attempt 2 / 3
Strategy: RETRY
```

A small progress indicator:

```text
●───○───○
```

can be used.

---

# 36. RECOVERY COMPLETED

Example:

```text
✓ RECOVERY COMPLETED

browser.type
```

Then the original step can return to:

```text
RUNNING
```

or:

```text
VERIFIED
```

according to backend state.

---

# 37. RECOVERY EXHAUSTED

Display prominently:

```text
RECOVERY EXHAUSTED

The backend could not safely recover this step.
```

Show:

```text
Attempts
Failure
Evidence
```

The run should remain failed unless the backend says otherwise.

---

# 38. ARTIFACT EVENTS

Relevant:

```text
artifact.created
artifact.verified
```

Artifact entries should appear in:

- timeline
- artifact drawer
- related graph node

---

# 39. ARTIFACT CREATED

Example:

```text
ARTIFACT CREATED

Word
SyncNode_Word_<run>.docx
```

Animation:

```text
slide/fade into artifact list
```

---

# 40. ARTIFACT VERIFIED

Example:

```text
✓ ARTIFACT VERIFIED

SyncNode_Word_<run>.docx
```

Show:

```text
Word
verified
sha256...
```

if backend supplies them.

---

# 41. RAG EVENTS

Relevant:

```text
rag.query
rag.retrieval.completed
```

Timeline:

```text
KNOWLEDGE
Consulting local knowledge...
```

then:

```text
KNOWLEDGE READY
5 documents retrieved
```

---

# 42. RAG DETAIL

A selected RAG event can show:

```text
Reason
task references email, Word, Excel

Documents
Approval Rules
Workspace Rules
Word Reference
Email Draft
```

Trust badges use backend values.

---

# 43. MEMORY EVENT

When:

```text
workflow.memory_recorded
```

arrives:

```text
WORKFLOW REMEMBERED

Trajectory saved
```

Do not imply:
- model retraining
- weight update
- automatic strategy activation

The UI should accurately describe workflow memory.

---

# 44. APPROVAL EVENTS

Relevant:

```text
approval.requested
approval.decided
run.waiting_approval
```

Approval is a special blocking visual state.

---

# 45. APPROVAL REQUESTED

When:

```text
approval.requested
```

arrives:

1. keep timeline visible
2. keep graph visible
3. keep desktop mirror visible
4. open approval panel
5. highlight current step
6. show action/risk
7. show relevant artifacts/evidence
8. clearly state nothing has happened beyond what backend reports

---

# 46. APPROVAL VISUAL

```text
┌────────────────────────────────────────────┐
│             REVIEW REQUIRED               │
│                                            │
│ External communication is ready.           │
│                                            │
│ Recipient                                  │
│ demo@example.com                           │
│                                            │
│ Attachments                                │
│ ✓ Word                                     │
│ ✓ Excel                                    │
│ ✓ PowerPoint                               │
│                                            │
│ Nothing has been sent.                     │
│                                            │
│ [Reject]                     [Approve]    │
└────────────────────────────────────────────┘
```

Use actual backend data.

---

# 47. WAITING APPROVAL STATE

When:

```text
run.waiting_approval
```

the overall shell should show:

```text
WAITING FOR APPROVAL
```

The bottom timeline stops advancing until more backend events arrive.

The workflow graph shows the blocked boundary.

---

# 48. APPROVAL DECIDED

When:

```text
approval.decided
```

show:

```text
APPROVED
```

or:

```text
REJECTED
```

Then await backend state transition.

Do not locally force the run into completed/failed.

---

# 49. RUN TERMINAL EVENTS

```text
run.completed
run.failed
run.cancelled
```

These are global.

---

# 50. RUN COMPLETED

Timeline final entry:

```text
✓ RUN COMPLETE
```

Show:

```text
Verified artifacts: N
Steps completed: N
```

only using actual backend data.

Do not infer numbers.

---

# 51. RUN FAILED

Timeline:

```text
✕ RUN FAILED
```

Show:

```text
Failed step
Reason
Recovery attempts
Evidence
```

Backend remains authoritative.

---

# 52. RUN CANCELLED

Timeline:

```text
RUN CANCELLED
```

Use neutral styling.

---

# 53. CURRENT EXECUTION HEADER

At the top of the timeline panel:

```text
CURRENT ACTIVITY

● Word Agent
  document.create_docx

2 active agents
7 completed steps
1 waiting
```

Numbers must come from actual state.

---

# 54. AGENT ROSTER

Right panel can have:

```text
AGENTS

● Supervisor        coordinating
● Word              running
● Excel             running
● PowerPoint        running
○ Browser           waiting
○ Verifier          waiting
```

Render dynamically from:

```text
GET /api/v1/agents
```

and active run events.

Do not hardcode agent count.

---

# 55. AGENT CARD

Each card:

```text
┌─────────────────────────┐
│ ● WORD                  │
│ WordDocumentAgent       │
│                         │
│ create_docx             │
│ RUNNING                 │
│                         │
│ 00:12                   │
└─────────────────────────┘
```

Use backend-derived values.

---

# 56. SELECTED AGENT

Clicking the agent opens detailed right panel:

```text
WORD AGENT

Current step
create_docx

Current tool
document.create_docx

Status
RUNNING

Summary
Preparing the document artifact.

Recent activity
...
```

Do not show private reasoning.

---

# 57. AGENT ACTIVITY THREAD

For a selected agent, create a filtered timeline:

```text
Word Agent

15:42:10 spawned
15:42:11 started
15:42:13 document.create_docx proposed
15:42:13 authorized
15:42:14 invoked
15:42:15 verification passed
15:42:15 completed
```

This is extremely useful for the AI-IDE feel.

---

# 58. GLOBAL TIMELINE VS AGENT TIMELINE

Support both:

```text
GLOBAL
all run events

AGENT
events related to selected agent

STEP
events related to selected step

TOOL
events related to selected tool
```

The same source events are filtered, not duplicated backend data.

---

# 59. FILTER BAR

Timeline filters:

```text
All
Agents
Tools
Observations
Verification
Recovery
Artifacts
Knowledge
Approval
```

Frontend-only filters.

They must not alter execution.

---

# 60. EVENT SEVERITY

Recommended presentation levels:

```text
neutral
info
active
success
warning
error
blocking
```

Examples:

```text
run.started        info
tool.started       active
verification.passed success
recovery.started   warning
run.failed         error
approval.requested blocking
```

---

# 61. ICON SYSTEM

Suggested semantics:

```text
run      play/activity
agent    bot
tool     wrench
observe  eye
verify   check
recovery refresh
artifact file
knowledge book/search
approval lock
completed check
failed x
cancelled stop
```

Keep icons consistent across timeline, graph, and side panels.

---

# 62. TIMESTAMP FORMAT

Timeline should show compact local time:

```text
15:42:10
```

For older events:

```text
Sep 19 · 15:42
```

The raw backend timestamp should remain available in detail view.

---

# 63. ELAPSED TIME

For active runs:

```text
RUNNING 02:14
```

Derived from backend timestamps plus local time.

This is presentation-only.

---

# 64. DURATION PER EVENT

Where backend provides duration:

```text
document.create_docx
1.24s
```

Show on expanded rows.

---

# 65. TOOL PAYLOAD EXPANSION

Collapsed:

```text
document.create_docx
RUNNING
```

Expanded:

```text
Agent
Word

Inputs
path = ...
content = ...

Resource
document

Verification
file_exists
```

Only show values returned by backend/API.

---

# 66. TOOL OUTPUT EXPANSION

If tool results are available:

```text
Result
success=true

artifact_id
...

summary
...
```

Do not expose unnecessary internals.

---

# 67. EVENT GROUPING

Do not render every low-value backend event as an enormous card.

Group related lifecycle events.

Example:

```text
document.create_docx
  proposed
  validated
  authorized
  started
  invoked
  completed
  verified
```

can become one expandable tool activity.

Collapsed view:

```text
✓ document.create_docx
Verified
```

Expanded view:

```text
proposal
authorization
execution
observation
verification
```

---

# 68. GROUPING RULE

Group by:

```text
run_id
step_key
tool_key
agent_id
```

where available.

Never group unrelated steps together.

---

# 69. ACTIVE GROUP

The currently executing tool group should remain open automatically.

Example:

```text
● browser.attach_file
RUNNING
```

When completed:

```text
✓ browser.attach_file
VERIFIED
```

Collapse may happen only when the user is not interacting with it.

---

# 70. AUTO-SCROLL

During live execution:

```text
auto-scroll
```

ONLY while the user is near the bottom.

When the user scrolls upward:

```text
pause auto-scroll
```

Show:

```text
↓ 4 new events
```

Clicking it returns to live bottom.

---

# 71. TIMELINE DENSITY

Offer two frontend display modes:

```text
Comfortable
Compact
```

Comfortable:

```text
more spacing
more summaries
```

Compact:

```text
more events visible
```

This is frontend-only.

---

# 72. TIMELINE ANIMATION

New events may enter with:

```text
fade + translateY(4px)
```

Avoid large animations.

The animation should communicate:

```text
new event arrived
```

not:

```text
entertainment
```

---

# 73. ACTIVE AGENT PULSE

Running agent:

```text
subtle 1.5–2s pulse
```

Respect:

```text
prefers-reduced-motion
```

When complete:

```text
pulse stops
check appears
```

---

# 74. TOOL SPINNER

Use a compact spinner only for truly active states:

```text
tool.started
```

Do not show spinners for:
- proposed
- validated
- authorized
- completed
- verified

---

# 75. RECOVERY ANIMATION

Use:

```text
amber circular motion
```

with text:

```text
Recovering...
Attempt 2/3
```

On success:

```text
motion stops
green check
```

On exhaustion:

```text
motion stops
red state
```

---

# 76. VERIFICATION ANIMATION

Pass:

```text
check draws in
```

Fail:

```text
small red transition
```

Do not flash violently.

---

# 77. ARTIFACT ARRIVAL ANIMATION

When a new artifact is created:

```text
artifact card
→ slide/fade in
→ verified badge later
```

This creates a sense of tangible output.

---

# 78. APPROVAL ANIMATION

Approval is important enough for a stronger but restrained transition:

```text
active execution
→ background dim
→ yellow boundary glow
→ approval card enters
```

The desktop mirror remains visible.

---

# 79. TERMINAL ANIMATION

Completed:

```text
timeline settles
graph nodes settle
artifact badges final
```

Failed:

```text
active animation stops
failure state appears
evidence remains visible
```

Cancelled:

```text
active animation stops
neutral final state
```

---

# 80. DESKTOP + TIMELINE SYNCHRONIZATION

When:

```text
tool.started
```

the timeline marks the tool active.

When:

```text
observation.captured
```

the desktop mirror changes.

When:

```text
verification.passed
```

timeline + graph settle.

This creates the impression of:

```text
SEE
→ ACT
→ OBSERVE
→ VERIFY
```

without fabricating any of those stages.

---

# 81. DESKTOP MIRROR ACTIVE BANNER

When a computer-related step is running:

```text
LIVE DESKTOP

Microsoft Word
Word Agent
document.create_docx
```

If no desktop action is active:

```text
DESKTOP
Last observation
```

Use only actual backend data.

---

# 82. TOOL → DESKTOP LINK

Computer tools can display:

```text
computer.windows_search
```

with:

```text
LIVE DESKTOP
Windows Search
```

Then:

```text
computer.launch_app
```

with:

```text
LIVE DESKTOP
Microsoft Word
```

The timeline and center mirror change together.

---

# 83. BROWSER TOOL LINK

Browser activity:

```text
browser.navigate
browser.type
browser.attach_file
```

should update the right-side activity and center observation if backend provides browser screenshots/DOM state.

---

# 84. OFFICE TOOL LINK

Office artifact tools:

```text
document.create_docx
excel.create
excel.write_cell
powerpoint.create
powerpoint.add_slide
```

should be displayed under their relevant agents.

Even when an operation is file-based rather than visible UI automation, the timeline must make that distinction clear.

Example:

```text
EXCEL AGENT
excel.create
LOCAL FILE OPERATION
```

rather than implying Excel is visibly open if it is not.

---

# 85. AGENT ICON + APP ICON

Where useful, visually combine:

```text
Agent icon
+
Application icon
```

Example:

```text
Word Agent
[agent icon] [Word]
```

Use generic/local icons or project assets as appropriate.

Do not depend on proprietary assets that cannot be redistributed.

---

# 86. WORKFLOW GRAPH SYNC

Timeline selection should select the graph node.

Graph node selection should scroll/focus the related timeline activity.

This two-way frontend interaction is important.

---

# 87. TIMELINE → GRAPH

Click:

```text
create_excel
```

Then:

```text
graph node selected
```

and:

```text
right panel = step evidence
```

---

# 88. GRAPH → TIMELINE

Click:

```text
Excel Agent node
```

Then:

```text
timeline filtered/highlighted
```

to that agent.

---

# 89. TIMELINE → EVIDENCE

Click:

```text
verification.passed
```

Open:

```text
Evidence drawer
```

with:
- assertions
- observation
- artifact
- timestamp

---

# 90. EVIDENCE DRAWER

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
SyncNode_Word_...

SHA256
...
```

Only actual returned data.

---

# 91. SELECTED EVENT DETAIL

Right panel detail mode:

```text
EVENT

tool.completed

Time
15:42:14

Agent
Word

Step
create_docx

Tool
document.create_docx

Status
SUCCESS
```

Use exact backend terminology.

---

# 92. SAFE SUMMARY LANGUAGE

The UI can transform technical backend data into short labels:

```text
tool.started
→ Working

verification.passed
→ Verified

recovery.started
→ Recovering

approval.requested
→ Review required
```

Do not change the underlying meaning.

---

# 93. NO FABRICATED "AI THINKING"

Do not create fake:

```text
Analyzing...
Thinking...
Considering...
Reasoning...
```

unless corresponding safe backend events/data exist.

Use:

```text
PLAN
CURRENT ACTION
DECISION SUMMARY
```

instead.

---

# 94. SAFE AGENT SUMMARY

Good:

```text
Creating the workbook and preparing its calculated values.
```

Bad:

```text
I think I should manipulate column C because...
```

Only safe backend summary content belongs here.

---

# 95. CURRENT ACTION BAR

At the top of the right panel:

```text
CURRENTLY WORKING ON

PowerPoint Agent
powerpoint.add_slide
```

If there are multiple active agents:

```text
CURRENTLY ACTIVE

Word
Excel
PowerPoint
```

Use real active state.

---

# 96. PARALLEL EXECUTION PRESENTATION

When backend indicates a wave:

```text
WAVE 3
3 tasks active
```

show:

```text
WORD       ●
EXCEL      ●
POWERPOINT ●
```

Do not collapse them into one generic "AI Working" indicator.

---

# 97. RESOURCE-AWARE PRESENTATION

If backend telemetry exposes:

```text
model queue
resource lock
```

show concise state:

```text
GPU MODEL QUEUE
1 active · 2 waiting
```

or:

```text
DESKTOP LOCK
Word Agent
```

Only when the backend actually exposes relevant data.

---

# 98. PARALLEL VS SERIAL

The UI must not claim:

```text
3 model calls running simultaneously
```

unless backend telemetry confirms it.

It may safely say:

```text
3 workflow branches active
```

when graph/wave state reports this.

---

# 99. AGENT DEPENDENCIES

Timeline should visually show when an agent is waiting on another.

Example:

```text
Email Agent
WAITING

Waiting for:
Word
Excel
PowerPoint
```

Only show explicit dependencies from backend plan/state.

---

# 100. JOIN VISUALIZATION

When a join occurs:

```text
Word ─┐
Excel ├─→ EMAIL
PPT  ─┘
```

Animate completion lines converging.

This should be driven by plan dependency state.

---

# 101. FAILURE BRANCH VISUALIZATION

Example:

```text
Word ✓
Excel ✕
PowerPoint ✓
   │
   ↓
Recovery
   │
   ↓
Excel ✓
```

This demonstrates recovery without hiding the original failure.

---

# 102. ORIGINAL FAILURE PRESERVATION

When recovery succeeds:

Do not erase the failed event.

Timeline:

```text
✕ Excel verification failed
↻ Recovery attempt 1
✓ Excel verification passed
```

This is important for trust.

---

# 103. AUDIT CONSISTENCY

The visible timeline may group events.

The audit screen should preserve the fuller sequence.

Provide:

```text
View audit
```

from relevant event details where possible.

---

# 104. EVENT GROUP EXPANSION

Default:

```text
✓ Word document
Verified
```

Expanded:

```text
15:42:10 agent.started
15:42:11 tool.proposed
15:42:11 tool.validated
15:42:11 tool.authorized
15:42:12 tool.started
15:42:14 tool.completed
15:42:14 observation.captured
15:42:15 verification.passed
15:42:15 agent.completed
```

This gives both overview and audit-like detail.

---

# 105. RUN SUMMARY

At the top/bottom of the timeline:

```text
RUN SUMMARY

Steps
10

Agents
5

Artifacts
3

Verified
9

Recoveries
1

Approval
Required
```

Use real backend counts.

---

# 106. AGENT SUMMARY

For the selected agent:

```text
AGENT SUMMARY

Status
COMPLETED

Steps
3

Tools
5

Verification
PASS

Duration
12.4s
```

Only show available values.

---

# 107. TOOL SUMMARY

For selected tool:

```text
TOOL

document.create_docx

Agent
Word

Status
COMPLETED

Verification
PASS

Duration
1.8s
```

---

# 108. OBSERVATION SUMMARY

For selected observation:

```text
OBSERVATION

Application
Microsoft Word

Window
Document1

Time
15:42:14

Screenshot
[thumbnail]
```

---

# 109. RECOVERY SUMMARY

For selected recovery:

```text
RECOVERY

Step
browser.type

Class
selector mismatch

Strategy
REOBSERVE

Attempt
2/3

Outcome
Recovered
```

---

# 110. APPROVAL SUMMARY

For selected approval:

```text
APPROVAL

Action
External email communication

Status
WAITING

Attachments
3

Send
NOT EXECUTED
```

---

# 111. ARTIFACT SUMMARY

For selected artifact:

```text
ARTIFACT

SyncNode_Excel_<run>.xlsx

Type
Excel

Verified
YES

Producer
Excel Agent

SHA256
...
```

---

# 112. TIMELINE SEARCH

Support local filtering:

```text
search: Excel
```

Results:

```text
Excel Agent
excel.create
excel.write_cell
verification.passed
```

No backend changes required.

---

# 113. TIMELINE DATE GROUPING

For long historical runs:

```text
TODAY
  events...

YESTERDAY
  events...
```

For active runs, keep continuous chronological presentation.

---

# 114. HISTORICAL RUN TIMELINE

A completed run should retain the same timeline structure.

Difference:

```text
LIVE
```

becomes:

```text
HISTORICAL
```

and animations are reduced.

---

# 115. HISTORICAL RUN EVIDENCE

The user can select:

```text
event
step
agent
tool
artifact
```

and inspect persisted details through REST endpoints.

---

# 116. RECONNECT BEHAVIOR

When SSE disconnects:

```text
LIVE STREAM INTERRUPTED
```

but do not mark the run failed.

Show:

```text
↻ Reconnecting...
```

Then:

```text
REST reconciliation
↓
SSE reconnect
↓
resume live timeline
```

---

# 117. RECONNECT ANIMATION

Use subtle:

```text
● LIVE
```

to:

```text
◌ RECONNECTING
```

then back:

```text
● LIVE
```

No dramatic warning for a transient transport issue.

---

# 118. STREAM TERMINATION

On terminal event:

```text
stream closes
```

then:

```text
final REST refresh
```

Timeline should show the final backend state.

---

# 119. DUPLICATE EVENTS

If an event is received twice:

```text
same timeline item
```

not:

```text
two timeline entries
```

Use the strongest available event identity/sequence from backend.

---

# 120. UNKNOWN EVENTS

Display in developer diagnostics only, or optionally:

```text
New backend event
```

but do not crash.

The main timeline should tolerate backend evolution.

---

# 121. MALFORMED EVENT

If malformed:

```text
event ignored
```

and stream remains active.

Do not render broken state.

---

# 122. EVENT STORE SIZE

Do not allow an unbounded browser-memory timeline for extremely long runs.

Implement safe retention/rendering strategy.

Possible:

```text
all events in normalized store
virtualized presentation
```

or pagination/history loading where applicable.

---

# 123. VIRTUALIZED TIMELINE

If event count becomes large:

use virtualization.

Only render visible rows.

Preserve:
- scroll position
- selection
- grouping
- filters

---

# 124. TIMELINE PERFORMANCE

Do not rerender every event across the full UI tree.

Use:

```text
memoized rows
selectors
normalized entities
targeted updates
```

The desktop mirror should remain smooth while timeline grows.

---

# 125. ACCESSIBILITY

Timeline must support:

- keyboard navigation
- visible focus
- semantic event items
- status labels
- screen-reader context
- reduced motion

Example screen-reader-friendly label:

```text
15:42:15, Word Agent, verification passed.
```

---

# 126. COLOR ACCESSIBILITY

Never rely on color alone.

Use:

```text
✓ Verified
✕ Failed
↻ Recovery
🔒 Approval
```

or icon + text.

---

# 127. KEYBOARD NAVIGATION

Suggested:

```text
↑ / ↓
move event selection

Enter
expand event

Esc
close detail

Ctrl/Cmd + K
global command

Ctrl/Cmd + J
toggle timeline
```

Exact shortcuts may follow the existing Electron architecture.

---

# 128. TIMELINE CONTEXT MENU

Optional actions:

```text
Open evidence
Focus graph node
Show agent
Show tool details
Copy event summary
```

These are frontend-only.

Do not expose dangerous execution actions through context menus.

---

# 129. DO NOT ADD DIRECT EXECUTION BUTTONS

The timeline should not expose arbitrary:

```text
Run tool
Retry tool
Execute again
Send
```

unless there is an explicit backend API for the exact action and policy.

The timeline is primarily observational.

---

# 130. USER CONTROL

Allowed primary user controls:

```text
start run
stop/terminate run
approve
reject
navigate
inspect
filter
open artifact
edit knowledge
review learning candidate
```

Only where backend contracts support the action.

---

# 131. TOOL RISK DISPLAY

Where backend provides risk:

```text
LOW
MEDIUM
HIGH
```

Display with restrained status styling.

Approval panel should emphasize external/irreversible actions.

Do not invent risk levels.

---

# 132. TOOL SIDE-EFFECT DISPLAY

Where provided:

```text
READ_ONLY
REVERSIBLE_LOCAL
IDEMPOTENT_LOCAL
EXTERNAL
```

Use backend terminology.

---

# 133. CURRENT RESOURCE DISPLAY

Where resource locks are exposed:

```text
Desktop
Word
Browser
GPU
```

This is useful to explain waiting states.

Only show real backend data.

---

# 134. AGENT WAITING EXPLANATION

Example:

```text
PowerPoint Agent
WAITING

Waiting for:
Excel analysis
```

or:

```text
Waiting for GPU model slot
```

only if backend provides this information.

---

# 135. MODEL ACTIVITY

Where backend exposes model telemetry:

```text
MODEL
Gemma 4 E4B

Profile
planner

Latency
1.8s

Tokens
...
```

This belongs in details, not every timeline row.

---

# 136. MODEL QUEUE

If several agents need model inference on a constrained machine:

```text
Model Queue

● Word Agent      running
○ Excel Agent     waiting
○ PowerPoint      waiting
```

Use actual scheduler telemetry.

---

# 137. TOKEN TELEMETRY

Optional detail:

```text
Prompt
1024

Completion
312

Latency
2.4s
```

Keep this out of the default timeline unless useful.

---

# 138. PLAN SUMMARY PANEL

At run start:

```text
PLAN

1. Create Word report
2. Create Excel analysis
3. Create PowerPoint summary
4. Draft email
5. Verify attachments
6. Request approval
```

As steps progress, update check states.

This should be linked to timeline events.

---

# 139. PLAN STEP STATE

```text
○ pending
● running
↻ recovering
✓ verified
✕ failed
🔒 waiting approval
```

Use the backend state.

---

# 140. TIMELINE + PLAN

The plan is the future.

The timeline is the history.

The UI should distinguish:

```text
PLAN
what should happen

TIMELINE
what did happen
```

Do not conflate them.

---

# 141. LIVE PLAN UPDATE

If a real replan occurs and backend emits corresponding plan events:

show:

```text
PLAN UPDATED
```

and visually mark the new branch.

Do not silently replace old plan history.

---

# 142. RECOVERY / REPLAN TIMELINE

Example:

```text
Plan v1
   ↓
Step failed
   ↓
Recovery
   ↓
Plan updated
   ↓
New step
```

This should be visible.

---

# 143. EVENT RELATIONSHIP MODEL

Maintain relationships:

```text
run
 └─ plan
    └─ step
       ├─ agent
       ├─ tool
       ├─ observation
       ├─ verification
       └─ artifact
```

Approval may attach to a step/tool.

Recovery attaches to a failed step.

---

# 144. CORRELATION MODEL

Use actual backend identifiers where available:

```text
run_id
step_key
agent_id
tool_call_id
artifact_id
approval_id
correlation_id
```

Do not use display names as primary identifiers.

---

# 145. STEP DETAIL PAGE/VIEW

Click step:

```text
STEP
create_docx

Agent
Word

Tool
document.create_docx

Status
COMPLETED

Verification
PASS

Artifact
...
```

Timeline related events highlighted.

---

# 146. AGENT DETAIL VIEW

Click agent:

```text
AGENT
Word

Status
COMPLETED

Current/last step
create_docx

Activity
...
```

Timeline filtered to that agent.

---

# 147. TOOL DETAIL VIEW

Click tool:

```text
TOOL
document.create_docx

Agent
Word

Risk
Medium

Execution
Completed

Verification
Pass
```

Use backend contract data.

---

# 148. ARTIFACT DETAIL VIEW

Click artifact:

```text
ARTIFACT
Word

Run
<run_id>

Producer
Word Agent

Verified
Yes

SHA256
...
```

Related step/timeline event highlighted.

---

# 149. APPROVAL DETAIL VIEW

Click approval:

```text
APPROVAL
External communication

Status
Waiting

Attachments
3

Nothing sent
```

Buttons:

```text
Reject
Approve
```

only when actionable.

---

# 150. FINAL RUN SUMMARY

At terminal:

```text
RUN COMPLETE

10 steps
5 agents
3 artifacts
9 verifications
74 audit events
```

Only actual data.

For waiting:

```text
WAITING FOR APPROVAL

3 artifacts ready
0 sends executed
```

Only actual data.

---

# 151. THREE-ARTIFACT GOLDEN TIMELINE

The known SyncNode golden workflow should look approximately like:

```text
Run accepted
      ↓
Workspace ready
      ↓
Consulting knowledge
      ↓
Knowledge retrieved
      ↓
Intent completed
      ↓
Plan created
      ↓
Plan validated
      ↓
Wave dispatched
      ↓
Computer Agent
Windows Search
      ↓
Word
      ↓
Excel
      ↓
PowerPoint
      ↓
Verification
      ↓
Email compose
      ↓
Attach Word
      ↓
Attach Excel
      ↓
Attach PowerPoint
      ↓
Draft verified
      ↓
Approval requested
      ↓
WAITING FOR APPROVAL
```

This is a visualization of backend events, not a hardcoded frontend workflow.

---

# 152. FINAL GOLDEN VISUAL STATE

At the final approval point:

LEFT:

```text
TASK
Create report + analysis + presentation + email

✓ Word
✓ Excel
✓ PowerPoint
✓ Email draft
```

CENTER TOP:

```text
Desktop / Email Draft
```

CENTER BOTTOM:

```text
Word ✓
Excel ✓
PPT ✓
Email ✓
Approval 🔒
```

RIGHT:

```text
REVIEW REQUIRED

3 attachments
Nothing sent

[Reject]
[Approve]
```

BOTTOM STATUS:

```text
WAITING FOR APPROVAL
● BACKEND CONNECTED
● LOCAL
```

---

# 153. MULTI-AGENT FINAL STATE

During parallel work:

```text
SUPERVISOR        ●
WORD              ●
EXCEL             ●
POWERPOINT        ●
EMAIL             ○ waiting
VERIFIER          ○ waiting
```

The graph should show corresponding branches.

Timeline should show their events interleaved by actual event timestamps/order.

---

# 154. EVENT ORDER VS VISUAL GROUPING

The timeline may visually group by agent or step.

But the source event ordering remains available.

Use:

```text
Global order
```

for the main timeline.

Filter/group only presentation.

---

# 155. INTERLEAVED PARALLEL TIMELINE

Example:

```text
15:42:10  Word Agent started
15:42:10  Excel Agent started
15:42:11  PowerPoint Agent started
15:42:12  Excel create completed
15:42:13  Word create completed
15:42:14  PowerPoint create completed
```

Do not reorder events to make the workflow look cleaner.

Preserve actual order.

---

# 156. EVENT TIME PRECISION

Display milliseconds only where useful:

```text
developer diagnostics
```

Normal UI:

```text
15:42:14
```

---

# 157. TIMELINE COLOR RULE

Primary surface:

```text
near black
gray
off-white
```

Accent only for state.

Do not make every agent a different rainbow color.

---

# 158. AGENT IDENTITY COLORS

Prefer a mostly monochrome roster.

Optional subtle identity accents may exist for:
- AI
- system
- approval
- recovery

But state is more important than agent branding.

---

# 159. DESKTOP MIRROR EMPHASIS

When desktop observation arrives:

The timeline item may briefly highlight:

```text
DESKTOP OBSERVED
```

The center mirror updates.

This creates a connection:

```text
timeline event
↔ desktop
```

---

# 160. TOOL ACTIVITY EMPHASIS

When a tool starts:

```text
timeline
→ current tool row

right panel
→ agent current action

center
→ desktop/browser observation if available
```

This produces a coherent live execution scene.

---

# 161. NO MODAL FOR NORMAL EVENTS

Do not open modals for:

```text
tool started
agent started
verification passed
artifact created
```

Use inline timeline.

Reserve modal/large overlays for:

```text
approval
critical error
important evidence
```

---

# 162. APPROVAL AS INTERRUPT

Approval is an intentional workflow interruption.

Visual:

```text
normal activity
→ approval interrupt
→ user decision
→ backend resumes/stops
```

This is the strongest state transition in the product.

---

# 163. USER DECISION FEEDBACK

After click:

```text
Approve
```

show:

```text
Submitting...
```

Then wait for backend event.

Do not immediately say:

```text
Approved
```

until backend confirms.

---

# 164. ERROR DURING APPROVAL

Example:

```text
Approval request could not be submitted.

The approval state may have changed.

[Refresh]
```

This is frontend transport/interaction state, not a run failure unless backend confirms.

---

# 165. TIMELINE EXPORT

Optional frontend action:

```text
Export visible timeline
```

The implementation may produce local JSON/CSV/text from currently loaded frontend data.

Do not alter backend audit records.

---

# 166. RUN REPLAY

A historical visualization may replay backend event history visually.

Important:

Replay is presentation only.

It must NOT:
- execute tools
- launch apps
- send email
- rerun workflows

A replay is not a second execution.

---

# 167. REPLAY MODE VISUAL

```text
REPLAY
```

with:

```text
timeline
graph
desktop evidence
```

and disabled execution controls.

---

# 168. LIVE VS REPLAY

Live:

```text
● LIVE
```

Replay:

```text
○ REPLAY
```

Historical:

```text
HISTORICAL
```

---

# 169. DEVELOPER MODE

Optional developer timeline diagnostics:

```text
event type
raw payload
sequence
correlation
transport timestamp
```

Keep collapsed.

This helps frontend integration without changing backend.

---

# 170. PRODUCTION MODE

Default production view should emphasize:

```text
agent
action
result
verification
```

and hide unnecessary implementation details.

---

# 171. TIMELINE SEARCH + FILTER COMBINATION

Support:

```text
Search: verification
Filter: Agent
Agent: Excel
```

Frontend-only filtering.

---

# 172. EVENT PINNING

Optional feature:

Allow user to pin important events:

```text
approval
failure
artifact
verification
```

Pins are frontend-only and should not alter backend.

---

# 173. EVENT NOTES

Optional frontend-local notes may be attached to timeline items.

Do not write them into backend audit unless an explicit backend note API exists.

---

# 174. RUN COMPARISON

Historical run comparison may compare frontend-loaded:
- duration
- steps
- artifacts
- recovery
- verification

Do not modify workflow behavior.

---

# 175. MULTI-AGENT COUNTER

At top:

```text
3 agents active
```

Derived from actual agent state.

When count changes:

```text
subtle number transition
```

---

# 176. CURRENT STEP COUNTER

Example:

```text
Step 6 / 10
```

Only if backend plan provides a meaningful ordered plan.

Do not create fake numbering when dynamic replanning changes the structure.

---

# 177. PROGRESS BAR

A progress indicator may show:

```text
verified critical steps / total critical steps
```

only where backend semantics allow.

Never equate:

```text
90% steps completed
```

with:
```text
90% guaranteed success
```

The terminal state still comes from backend.

---

# 178. INDETERMINATE STATE

If progress cannot be measured safely:

```text
ACTIVE
```

with activity pulse.

Do not invent percentages.

---

# 179. TIMELINE EMPTY STATE

Before a run:

```text
NO ACTIVITY YET

Start a task to see the workflow here.
```

During connection:

```text
CONNECTING TO LIVE RUN...
```

---

# 180. TIMELINE ERROR STATE

If event stream fails:

```text
LIVE STREAM UNAVAILABLE

The run may still be active.

[Reconnect]
```

Then reconcile through REST.

---

# 181. EVENT STREAM HEALTH

Status:

```text
● LIVE
◌ RECONNECTING
× OFFLINE
```

Do not confuse SSE health with run status.

---

# 182. AGENT TIMELINE COMPONENT STRUCTURE

Suggested:

```text
AgentTimeline
├─ TimelineHeader
├─ TimelineFilters
├─ TimelineList
│  ├─ RunEvent
│  ├─ AgentEvent
│  ├─ ToolEventGroup
│  ├─ ObservationEvent
│  ├─ VerificationEvent
│  ├─ RecoveryEvent
│  ├─ ArtifactEvent
│  └─ ApprovalEvent
└─ TimelineFooter
```

---

# 183. EVENT GROUP COMPONENTS

Suggested:

```text
ToolExecutionGroup
AgentActivityGroup
RecoveryGroup
ArtifactGroup
ApprovalGroup
```

These are frontend presentation abstractions.

---

# 184. DATA MODEL

Conceptually:

```ts
interface TimelineEventView {
  id: string;
  eventType: string;
  runId: string;
  timestamp: string;
  agentId?: string;
  stepKey?: string;
  toolKey?: string;
  severity: TimelineSeverity;
  summary: string;
  status?: string;
  payload?: unknown;
}
```

Actual API/event types must derive from the repository contracts.

---

# 185. GROUP MODEL

Conceptually:

```ts
interface TimelineGroupView {
  id: string;
  kind: "tool" | "agent" | "recovery" | "artifact" | "approval";
  title: string;
  state: string;
  eventIds: string[];
  expanded: boolean;
}
```

---

# 186. SELECTION MODEL

Maintain frontend selection:

```text
selectedEventId
selectedAgentId
selectedStepKey
selectedToolCallId
selectedArtifactId
```

Selection does not modify backend execution.

---

# 187. ACTIVE MODEL

Derived:

```text
activeAgent
activeStep
activeTool
activeObservation
pendingApproval
```

Selectors should compute these from synchronized state.

---

# 188. EVENT LOOKUP

Keep normalized maps:

```text
eventsById
agentsById
stepsById
toolsById
artifactsById
```

This keeps selection and updates efficient.

---

# 189. TIMELINE ORDER STORE

Keep a separate ordered ID list:

```text
timelineOrder[]
```

so filtering and rendering do not mutate source event identity.

---

# 190. EVENT IMMUTABILITY

Once an event is stored:

do not mutate historical event payloads.

Derived presentation state may be updated separately.

---

# 191. EVENT RETENTION

Historical data should remain available as long as run detail is loaded.

Large histories can be virtualized or loaded incrementally.

---

# 192. FINAL EVENT RECONCILIATION

After terminal:

```text
REST snapshot
→ reconcile all stores
→ freeze live event animation
```

The final screen should represent the backend's final truth.

---

# 193. BACKEND CONTRACT PROTECTION

Do not "simplify" events by changing backend contracts.

Frontend mapping may simplify presentation.

Example:

```text
tool.completed
→ "Tool finished"
```

But the underlying event object remains intact.

---

# 194. EVENT SCHEMA VERSIONING

If event schema versioning exists:

support it.

If a new version introduces additive fields:

ignore unsupported fields safely.

Do not modify backend versioning.

---

# 195. FRONTEND-ONLY MOCKING

For component tests, use fixture events shaped exactly like the backend contract.

Do not invent simplified fake event names like:

```text
AI_DID_THING
```

Use real contract names.

---

# 196. CORE FRONTEND TEST SET

Test:

```text
run.created
run.started
agent.spawned
agent.started
agent.plan_summary
tool.proposed
tool.authorized
tool.started
tool.completed
observation.captured
verification.passed
recovery.started
artifact.created
artifact.verified
approval.requested
run.waiting_approval
run.completed
run.failed
run.cancelled
```

---

# 197. TEST: PARALLEL AGENTS

Feed events:

```text
Word started
Excel started
PowerPoint started
```

Verify:

```text
three agent cards active
three graph nodes active
timeline interleaved
```

No fake ordering.

---

# 198. TEST: RECOVERY

Feed:

```text
verification.failed
recovery.started
recovery.attempted
recovery.completed
verification.passed
```

Verify:

```text
failure remains visible
recovery visible
final step verified
```

---

# 199. TEST: APPROVAL

Feed:

```text
approval.requested
run.waiting_approval
```

Verify:

```text
approval card appears
timeline pauses visually
desktop remains visible
run not marked completed
```

---

# 200. TEST: TERMINAL

Feed:

```text
run.completed
```

Verify:

```text
completion state
stream closed/reconciled
final REST refresh triggered
```

---

# 201. TEST: FAILURE

Feed:

```text
run.failed
```

Verify:

```text
failure state
evidence accessible
timeline preserved
```

---

# 202. TEST: RECONNECT

Simulate:

```text
connected
events
disconnect
reconnect
snapshot
events
terminal
```

Verify:
- no duplicates
- correct ordering
- final state correct

---

# 203. TEST: UNKNOWN EVENT

Unknown event:

```json
{
  "event_type": "new.backend.feature",
  "run_id": "..."
}
```

Verify:
- no crash
- stream remains active
- timeline remains usable

---

# 204. TEST: MALFORMED EVENT

Malformed event should be ignored safely.

Verify:
- no React crash
- no state corruption

---

# 205. TEST: HISTORICAL RUN

Load a completed run through REST.

Verify:

```text
timeline populated
graph populated
artifacts populated
audit populated
```

No live SSE required.

---

# 206. TEST: ACTIVE RUN HYDRATION

Open active run:

```text
REST snapshot
+
SSE
```

Verify the final UI is consistent.

---

# 207. TEST: AGENT FILTER

Select:

```text
Excel
```

Verify only relevant agent events are shown in the filtered view.

Global event data remains intact.

---

# 208. TEST: TOOL FILTER

Select:

```text
verification
```

Show only verification events.

---

# 209. TEST: GRAPH SELECTION

Click a graph node.

Verify:
- timeline filters/highlights related events
- evidence panel selects related step

---

# 210. TEST: TIMELINE SELECTION

Click a timeline event.

Verify:
- graph node selects
- agent panel selects
- evidence opens where applicable

---

# 211. TEST: APPROVAL ERROR

Simulate backend error on approval decision.

Verify:

```text
error toast
refresh
no false approval state
```

---

# 212. TEST: LONG TIMELINE

Generate thousands of events.

Verify:
- smooth scrolling
- no obvious input lag
- virtualized rendering works
- selection remains accurate

---

# 213. TEST: REDUCED MOTION

When:

```text
prefers-reduced-motion
```

verify animations reduce without losing status clarity.

---

# 214. EVENT-DRIVEN DESIGN RULE

Never implement:

```text
setTimeout(() => showAgentRunning(), 5000)
```

to fake backend activity.

Instead:

```text
agent.started
→ show running
```

Time-based animations may happen only after a real state transition.

---

# 215. NO POLLING-BASED ACTIVITY SIMULATION

Do not simulate:
- agent progress
- tool completion
- verification
- recovery

using frontend timers.

Timers may be used only for:
- elapsed-time display
- UI animation
- debounce
- reconnect backoff

---

# 216. NO HARDCODED GOLDEN RUN

Do not build a special case:

```text
if goal includes "Word Excel PowerPoint"
```

in the frontend to fake timeline events.

The same generic event architecture must support the golden workflow.

---

# 217. DYNAMIC AGENT SUPPORT

If backend adds another agent:

frontend should display it from:

```text
GET /agents
```

and incoming events.

Do not require frontend source changes merely because an agent was added.

---

# 218. DYNAMIC TOOL SUPPORT

If backend adds another tool:

the timeline can display:

```text
tool key
status
agent
step
```

using generic event rendering.

Tool-specific visual enhancements can be registered separately.

---

# 219. TOOL ICON REGISTRY

Optional frontend map:

```text
document → file-text
excel → grid
powerpoint → presentation
browser → globe
computer → monitor
filesystem → folder
verification → shield-check
```

Fallback:

```text
wrench
```

Unknown tools must still render.

---

# 220. AGENT ICON REGISTRY

Optional frontend map:

```text
supervisor → network
writer → pen
document → file-text
office → briefcase
computer → monitor
browser → globe
verifier → shield-check
recovery → refresh
```

Unknown agent:

```text
bot
```

---

# 221. EVENT SUMMARY GENERATION

Where backend already supplies:

```text
summary
```

use it.

Do not generate a model response to summarize every event.

Frontend formatting should be deterministic.

---

# 222. TIMELINE TEXT TEMPLATES

Use deterministic templates.

Examples:

```text
agent.started
→ "{agent} started {step}"

tool.started
→ "{tool} started"

verification.passed
→ "{step} verified"

artifact.created
→ "{artifact} created"

approval.requested
→ "Approval required"
```

Only use placeholders actually present.

---

# 223. LOCALIZATION

Keep timeline strings in a frontend translation layer if localization is later required.

Backend event keys remain stable.

---

# 224. TOOL INPUT REDACTION

If raw inputs are displayed, apply frontend presentation redaction only where necessary.

Do not claim that frontend redaction replaces backend privacy controls.

Never expose obvious credentials/secrets in normal UI.

---

# 225. TOOL OUTPUT REDACTION

Same principle.

Large or sensitive backend values should be collapsed/truncated.

---

# 226. ARTIFACT PATH DISPLAY

Prefer:

```text
SyncNode_Word_<run>.docx
```

with an expandable location.

Do not show unnecessarily long absolute Windows paths in the main card.

---

# 227. ARTIFACT ID DISPLAY

Show artifact identity in technical detail:

```text
artifact_id
```

where useful.

---

# 228. VERIFICATION DETAIL

Show exact assertion names where useful:

```text
file_exists
content_generated
application_running
attachment_present
```

These are useful for technical trust.

---

# 229. RECOVERY DETAIL

Show:

```text
class
tier
attempt
```

only if returned by backend.

---

# 230. MODEL DETAIL

Show safe telemetry:

```text
model
profile
latency
tokens
```

in detail.

---

# 231. EVENT CLICKABILITY

Not every event must open a detail panel.

High-value events:

```text
tool
verification
recovery
artifact
approval
observation
agent
```

should be interactive.

---

# 232. EVENT HOVER

Hover can show:
- timestamp
- agent
- step
- tool
- short status

Do not create heavy tooltips for every row.

---

# 233. ACTIVE TOOL PIN

The current tool can be pinned at the top of the timeline:

```text
CURRENT TOOL
document.create_docx
RUNNING
```

When it completes, remove or update.

---

# 234. ACTIVE AGENT PIN

Current active agent can be shown in top bar:

```text
Word Agent · Running
```

If multiple:

```text
3 agents active
```

---

# 235. CURRENT STAGE LABEL

Top center:

```text
EXECUTING
```

or:

```text
VERIFYING
```

or:

```text
WAITING FOR APPROVAL
```

Derived from real events/backend state.

---

# 236. RUN STATUS CHIP

Always visible:

```text
QUEUED
RUNNING
WAITING
COMPLETED
FAILED
CANCELLED
```

Use actual backend run status.

---

# 237. FINAL STAGE TRANSITION

At terminal:

```text
running
→ completed
```

or:

```text
running
→ failed
```

Do not animate intermediate stages after terminal.

---

# 238. TIMELINE FOOTER

Optional:

```text
89 events
Live
```

or:

```text
89 events
Historical
```

Use actual count from local state.

---

# 239. RUN EVENT COUNT

If using:

```text
89 events
```

this is presentation data.

The audit count remains backend-authoritative.

---

# 240. PERFORMANCE TARGET

The timeline should remain usable with:
- hundreds of events
- thousands of events
- rapid SSE bursts

Do not tie event arrival to blocking layout work.

---

# 241. EVENT BATCHING

For bursts:

```text
10 events in 20ms
```

the state layer may batch React updates if safe.

Do not reorder them.

---

# 242. ANIMATION QUEUE

Do not create a huge animation backlog.

For high-frequency events:
- update state immediately
- reduce animation intensity
- preserve latest state

---

# 243. DESKTOP SCREENSHOT THROTTLING

If many observations arrive:
- show latest
- avoid decoding all images simultaneously
- use thumbnails
- lazy load

---

# 244. TIMELINE MEMORY

Keep normalized event state.

For long runs:
- virtualize
- release unused UI objects
- preserve necessary identifiers

Do not delete evidence arbitrarily.

---

# 245. BACKEND AUTHORITY REMINDER

At every layer:

```text
backend event
    >
frontend derived state
    >
animation
```

Never reverse this.

---

# 246. FRONTEND CONTRACT REMINDER

Use:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

Do not manually invent a parallel contract.

---

# 247. NO BACKEND EDITS

Again:

```text
DO NOT MODIFY BACKEND.
```

Not for:
- timeline fixes
- animation fixes
- state mapping
- visual bugs
- API client convenience
- event display

Frontend must adapt to the existing contract.

---

# 248. IF EVENT DATA IS MISSING

If a desired UI element needs backend data that does not exist:

do not fabricate it.

Use a truthful fallback:

```text
Not available
```

or hide the field.

Document the gap if needed.

---

# 249. IF SCREENSHOT IS MISSING

Do not create a placeholder fake desktop screenshot.

Show:

```text
No visual observation available
```

while still displaying any metadata that exists.

---

# 250. IF AGENT SUMMARY IS MISSING

Do not invent reasoning.

Show:

```text
No summary available
```

or simply show current action/tool.

---

# 251. IF TOOL RESULT IS MISSING

Show tool lifecycle without fake output.

---

# 252. IF VERIFICATION IS MISSING

Do not show a green verified badge merely because tool completed.

Show:

```text
Completed
Verification unavailable
```

where appropriate.

---

# 253. IF APPROVAL INFORMATION IS INCOMPLETE

Show only what backend provides.

Example:

```text
Approval required
Details unavailable
```

rather than fabricated recipient/risk.

---

# 254. TIMELINE TRUST MODEL

The user should learn to interpret:

```text
Blue / active
→ currently happening

Green / verified
→ evidence-backed success

Amber / recovery
→ backend is recovering

Yellow / approval
→ user control required

Red / failed
→ backend reports failure
```

This becomes a consistent product language.

---

# 255. MAIN UX PRINCIPLE

The timeline must create:

```text
VISIBILITY
without
NOISE
```

Every event should communicate a useful change.

Group technical lifecycle events where appropriate.

Keep evidence accessible.

---

# 256. FINAL INTEGRATED EXPERIENCE

A real run should feel like:

```text
USER
  ↓
Task submitted
  ↓
PLAN
  ↓
AGENTS APPEAR
  ↓
WORKFLOW BRANCHES
  ↓
TOOLS EXECUTE
  ↓
DESKTOP CHANGES
  ↓
OBSERVATIONS ARRIVE
  ↓
VERIFICATION
  ↓
RECOVERY if required
  ↓
ARTIFACTS ARRIVE
  ↓
EMAIL DRAFT
  ↓
APPROVAL
  ↓
USER DECISION
  ↓
FINAL STATE
```

Every transition is driven by real backend state/events.

---

# 257. FINAL UI SCENE

The ideal active workspace at peak execution:

```text
LEFT
────────────────────────
TASK

Monthly Operations Pack

✓ Word
● Excel
● PowerPoint
○ Email

RECENT
...

CENTER TOP
────────────────────────
LIVE DESKTOP

Microsoft Excel

[actual observation]

LIVE CONTROL
Excel Agent
excel.write_cell

CENTER BOTTOM
────────────────────────
WORKFLOW

        PLAN
          │
   ┌──────┼───────┐
   ▼      ▼       ▼
 WORD    EXCEL    PPT
   ✓      ●       ●
           │
           ▼
         EMAIL
           ○

TIMELINE

15:42:10 Word ✓
15:42:11 Excel ●
15:42:11 PPT ●
15:42:13 Word verified
15:42:15 Excel writing...
...

RIGHT
────────────────────────
AGENTS

● Excel Agent
  excel.write_cell

○ Word Agent
  completed

● PowerPoint Agent
  running

CHAT / SUMMARY

Preparing the remaining
artifacts before email.

TOOLS

excel.write_cell
RUNNING
```

This is the intended AI-IDE feel.

---

# 258. FINAL APPROVAL SCENE

At the end:

```text
LEFT
Task
✓ Word
✓ Excel
✓ PowerPoint
✓ Email draft

CENTER TOP
Email draft / desktop evidence

CENTER BOTTOM
Word ✓
Excel ✓
PPT ✓
Email ✓
Approval 🔒

RIGHT

REVIEW REQUIRED

Recipient
demo@example.com

Attachments
✓ Word
✓ Excel
✓ PowerPoint

Nothing has been sent.

[Reject] [Approve]
```

Bottom:

```text
WAITING FOR APPROVAL
● LOCAL
● BACKEND CONNECTED
```

---

# 259. FINAL FRONTEND IMPLEMENTATION TASK

Build the complete Agent Timeline system.

It must:

```text
read all documentation first
↓
read OpenAPI
↓
read event contracts
↓
read entity contracts
↓
build typed event layer
↓
build centralized SSE routing
↓
build normalized timeline state
↓
connect agent state
↓
connect tool state
↓
connect workflow graph
↓
connect observations
↓
connect verification
↓
connect recovery
↓
connect artifacts
↓
connect RAG
↓
connect approval
↓
connect audit
↓
connect terminal state
↓
build animations
↓
build filtering
↓
build evidence interactions
↓
test reconnection
↓
test duplicates
↓
test unknown events
↓
test parallel events
↓
test approval
↓
test full real backend integration
```

The implementation must be generic.

Do not hardcode the golden workflow.

---

# 260. FINAL ABSOLUTE CONSTRAINT

**DO NOT TOUCH THE BACKEND.**

Do not edit:

```text
backend/
ai_ml/
Python
LangGraph
LangChain
ModelGateway
ExecutionEngine
RecoveryEngine
ToolRegistry
AgentRegistry
VerificationEngine
database
migrations
FastAPI routes
SSE event generation
backend schemas
```

Only modify:

```text
Electron
React
TypeScript
frontend services
frontend stores
frontend components
frontend styles
frontend animation system
frontend tests
```

---

# 261. FINAL DEFINITION OF DONE

The Agent Timeline subsystem is complete when:

```text
[ ] live SSE stream works
[ ] events are typed
[ ] events are normalized
[ ] duplicates handled
[ ] unknown events tolerated
[ ] reconnect works
[ ] terminal reconciliation works

[ ] run events render
[ ] plan events render
[ ] agents render
[ ] tools render
[ ] observations render
[ ] verification renders
[ ] recovery renders
[ ] artifacts render
[ ] RAG renders
[ ] memory renders
[ ] approvals render
[ ] terminal state renders

[ ] global timeline works
[ ] agent filter works
[ ] step filter works
[ ] tool filter works
[ ] search works
[ ] event selection works
[ ] graph selection sync works
[ ] evidence selection works

[ ] active agent state works
[ ] current tool works
[ ] parallel branches display correctly
[ ] recovery history preserved
[ ] no fake activity
[ ] no fake reasoning
[ ] no fake verification
[ ] no fake completion
[ ] no direct backend modification
```

---

# 262. FINAL PRODUCT PRINCIPLE

SyncNode should make autonomous execution understandable without exposing private reasoning.

The user should see:

```text
WHAT
WHO
ACTION
OBSERVATION
RESULT
VERIFICATION
RECOVERY
APPROVAL
```

and never need to ask:

> "What is the AI doing right now?"

The timeline, graph, desktop mirror, agent panel, and evidence surfaces should answer that continuously.

---

# 263. FINAL IMPLEMENTING EDITOR INSTRUCTION

Read the complete SyncNode documentation and frontend specifications before coding.

Then implement this timeline architecture against the existing backend.

Use the real REST + SSE contracts.

Make the timeline deeply integrated with:

```text
agents
workflow graph
desktop mirror
tools
verification
recovery
artifacts
RAG
approval
audit
```

The frontend should feel like a living AI development/workflow environment.

But every visual state must be grounded in backend truth.

### FINAL RULE:

**DO NOT TOUCH THE BACKEND.**

The backend is already the authority.

The Electron frontend is the observation, interaction, visualization, and approval surface.

Build the complete Agent Timeline around that boundary and make the entire run experience feel coherent, alive, precise, and trustworthy.
