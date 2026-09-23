# FRONTEND_APPROVAL_FLOW.md

# SyncNode Electron Frontend
## End-to-End Approval Architecture, Backend Route Wiring, State Machine, Evidence Review & Safe Resume

> **SCOPE: FRONTEND ONLY**
>
> This document defines the complete Electron/React frontend implementation for SyncNode's human approval boundary.
>
> The backend is already the authority for:
>
> - policy
> - approval creation
> - approval state
> - execution
> - send authorization
> - audit
> - persistence
> - workflow continuation
>
> **DO NOT MODIFY THE BACKEND.**
>
> Do not edit:
>
> ```text
> backend/
> ai_ml/
> Python
> FastAPI routes
> LangGraph
> LangChain
> ExecutionEngine
> RecoveryEngine
> ToolRegistry
> AgentRegistry
> VerificationEngine
> policy
> database
> persistence
> SSE generation
> schemas
> ```
>
> The frontend must consume the existing REST + SSE contracts exactly as documented.
>
> The frontend implementation is:
>
> ```text
> observe
> present
> review
> decide
> submit decision
> reconcile
> resume visualization
> ```
>
> It is NOT:
>
> ```text
> authorize
> execute
> send
> bypass policy
> mutate backend state locally
> ```

---

# 1. WHY APPROVAL IS A FIRST-CLASS SYSTEM

SyncNode is designed around:

```text
AI proposes.
Deterministic systems authorize.
The human approves sensitive actions.
```

Approval is therefore not a generic modal.

It is a first-class workflow state.

The user must clearly understand:

```text
WHAT WILL HAPPEN?
WHO REQUESTED IT?
WHAT IS READY?
WHAT IS RISKY?
WHAT HAS ALREADY HAPPENED?
WHAT HAS NOT HAPPENED?
WHAT AM I APPROVING?
```

For external communication:

```text
DRAFT READY
→ REVIEW
→ APPROVAL
→ BACKEND DECISION
→ CONTINUE OR STOP
```

The frontend must make this boundary visually unambiguous.

---

# 2. APPROVAL ARCHITECTURE

Canonical flow:

```text
SYNCNODE BACKEND
      │
      │ approval.requested
      ▼
ELECTRON SSE EVENT
      │
      ▼
Approval Event Router
      │
      ▼
Approval Store
      │
      ├───────────────┐
      ▼               ▼
Run Store         Timeline Store
      │               │
      └──────┬────────┘
             ▼
      Approval Surface
             │
       user reviews
             │
     ┌───────┴────────┐
     ▼                ▼
  REJECT            APPROVE
     │                │
     └───────┬────────┘
             ▼
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
             │
             ▼
        BACKEND POLICY
             │
             ▼
       SSE / REST update
             │
       ┌─────┴─────┐
       ▼           ▼
    rejected     approved
       │           │
       ▼           ▼
  run failed    run resumes
```

The frontend does not decide the result.

---

# 3. BACKEND ROUTES USED BY THE FRONTEND

Use the existing approval route:

```text
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
```

Request:

```json
{
  "decision": "approved",
  "reason": "Looks good"
}
```

or:

```json
{
  "decision": "rejected",
  "reason": "Do not proceed"
}
```

The exact supported values must follow the current OpenAPI/schema.

Do not alter the route.

Do not add another approval endpoint.

---

# 4. RUN ROUTES RELEVANT TO APPROVAL

The frontend should also use:

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
```

Approval review should not rely on one event payload alone.

The frontend must gather enough persisted evidence for the user to make an informed decision.

---

# 5. PRIMARY APPROVAL EVENTS

Relevant backend events include:

```text
approval.requested
approval.decided
run.waiting_approval
```

Potentially also:

```text
tool.proposed
tool.authorized
tool.started
tool.completed
observation.captured
verification.passed
artifact.created
artifact.verified
```

The approval surface should use these supporting events when available.

---

# 6. APPROVAL EVENT LIFECYCLE

Canonical frontend lifecycle:

```text
NORMAL RUNNING
      ↓
approval.requested
      ↓
APPROVAL REQUESTED
      ↓
run.waiting_approval
      ↓
WAITING FOR USER
      ↓
user decision
      ↓
POST decision
      ↓
backend confirms
      ↓
approval.decided
      ↓
approved / rejected
      ↓
backend updates run
      ↓
running / failed / terminal
```

Do not collapse:

```text
approval.requested
```

and:

```text
approval.decided
```

into one state.

---

# 7. APPROVAL STATE MACHINE

Frontend presentation state:

```text
NONE
 ↓
REQUESTED
 ↓
WAITING
 ├─→ SUBMITTING_APPROVAL
 │       ├─→ APPROVED_CONFIRMED
 │       └─→ REJECTED_CONFIRMED
 │
 └─→ STALE / REFRESH_REQUIRED
```

Final run state comes from backend:

```text
running
waiting_approval
completed
failed
cancelled
```

The frontend approval state is not a replacement for run state.

---

# 8. APPROVAL DATA MODEL

Conceptually:

```ts
interface ApprovalView {
  approvalId: string;
  runId: string;
  stepKey?: string;
  action?: string;
  risk?: string;
  status:
    | "requested"
    | "waiting"
    | "approved"
    | "rejected";
  decision?: "approved" | "rejected";
  reason?: string;
  createdAt?: string;
  decidedAt?: string;
}
```

Use actual backend field names from OpenAPI.

Do not invent fields merely because the UI would benefit from them.

---

# 9. APPROVAL STORE

Suggested:

```text
src/stores/approvalStore.ts
```

State:

```text
activeApproval
approvalHistory
submitting
error
```

Example:

```ts
interface ApprovalState {
  activeApproval?: ApprovalView;
  history: ApprovalView[];
  submitting: boolean;
  error?: ApiError;
}
```

The store is frontend state only.

Backend remains authoritative.

---

# 10. APPROVAL EVENT ROUTER

Map:

```text
approval.requested
→ create active approval

run.waiting_approval
→ mark approval/run as waiting

approval.decided
→ update decision

run.completed
→ clear active approval

run.failed
→ clear active approval

run.cancelled
→ clear active approval
```

Do not mark approved merely because the button was clicked.

---

# 11. APPROVAL REQUESTED

When:

```text
approval.requested
```

arrives:

```text
timeline
→ approval item

run state
→ approval candidate

approval store
→ active approval

right panel
→ approval tab

center
→ retain current desktop/workflow state

status
→ REVIEW REQUIRED
```

This should happen immediately.

---

# 12. APPROVAL REQUESTED UX

Use a strong but calm transition.

```text
ACTIVE RUN
      ↓
activity gently dims
      ↓
approval boundary highlighted
      ↓
approval card enters
      ↓
WAITING FOR USER
```

Do not completely hide the live workspace.

The user should still see:
- workflow
- desktop state
- artifacts
- evidence

---

# 13. APPROVAL CARD

Primary layout:

```text
┌────────────────────────────────────────────────┐
│                REVIEW REQUIRED                 │
│                                                │
│ External communication is ready.               │
│                                                │
│ ACTION                                         │
│ Draft email for external communication         │
│                                                │
│ RECIPIENT                                      │
│ demo@example.com                               │
│                                                │
│ SUBJECT                                        │
│ Monthly Operations Report                      │
│                                                │
│ ATTACHMENTS                                    │
│ ✓ Word                                         │
│ ✓ Excel                                        │
│ ✓ PowerPoint                                   │
│                                                │
│ RISK                                           │
│ External communication                         │
│                                                │
│ Nothing has been sent.                         │
│                                                │
│ [ Reject ]                       [ Approve ]  │
└────────────────────────────────────────────────┘
```

Only show fields returned by backend/evidence.

---

# 14. APPROVAL CARD HIERARCHY

Priority:

```text
1. What action needs approval?
2. What will happen?
3. What artifacts/content are involved?
4. Risk
5. Current state
6. Approve/Reject
```

Do not bury the decision.

---

# 15. WHAT HAS NOT HAPPENED

For a draft-only workflow, clearly communicate:

```text
NOT SENT
```

or:

```text
Nothing has been sent.
```

only when supported by backend state/evidence.

This is especially important for email.

Do not show generic "success" styling at the approval boundary.

---

# 16. WHAT HAS ALREADY HAPPENED

Show completed verified work:

```text
✓ Word document created
✓ Excel analysis created
✓ PowerPoint created
✓ Email draft prepared
✓ Attachments verified
```

Use backend-backed state.

---

# 17. APPROVAL EVIDENCE STRIP

Within approval card:

```text
READY TO REVIEW

Word         ✓ Verified
Excel        ✓ Verified
PowerPoint   ✓ Verified
Email        ✓ Draft verified
```

This should be derived from artifacts/verifications.

---

# 18. APPROVAL EVIDENCE DRAWER

Provide:

```text
View evidence
```

which opens:

```text
Step
Tool
Observation
Verification
Artifact
```

Example:

```text
Verification
PASS

Assertion
attachment_present

Artifact
SyncNode_Excel_<run>.xlsx
```

---

# 19. APPROVAL + WORKFLOW GRAPH

When waiting:

```text
Word ✓
Excel ✓
PPT ✓
Email ✓
Approval 🔒
```

The approval node should be visually distinct.

Do not animate upstream completed nodes.

---

# 20. APPROVAL + DESKTOP MIRROR

The desktop mirror remains visible.

Example:

```text
LIVE DESKTOP

Email compose draft

Recipient
demo@example.com

Attachments
3
```

A subtle overlay:

```text
WAITING FOR APPROVAL
```

may appear.

Do not fabricate UI state that is not in observation evidence.

---

# 21. APPROVAL + TIMELINE

Timeline:

```text
15:42:21  Email draft prepared
15:42:22  Attachment verified
15:42:23  Approval requested
15:42:23  Waiting for approval
```

Then after decision:

```text
15:42:35  Approval approved
```

or:

```text
15:42:35  Approval rejected
```

Use backend timestamps.

---

# 22. APPROVAL + AGENT PANEL

When approval is active:

```text
SUPERVISOR
WAITING

Action
External communication

Status
Awaiting user decision
```

Other agents:

```text
Word       completed
Excel      completed
PowerPoint completed
Email      waiting
```

Only show actual states.

---

# 23. APPROVAL + ARTIFACT PANEL

The artifact panel should show:

```text
Word
✓ VERIFIED

Excel
✓ VERIFIED

PowerPoint
✓ VERIFIED
```

Where the backend confirms them.

---

# 24. APPROVAL + RAG CONTEXT

Optional expandable section:

```text
Knowledge used

Approval Rules
AUTHORITATIVE POLICY

Workspace Rules
AUTHORITATIVE POLICY
```

Use:

```text
GET /api/v1/runs/{run_id}/context
```

Do not let the user edit policy from the approval surface.

---

# 25. APPROVAL + AUDIT

Approval card can link:

```text
View audit
```

and select:

```text
approval.requested
```

in the audit timeline.

---

# 26. APPROVE BUTTON

Default:

```text
Approve
```

Primary action.

When clicked:

```text
Approve
→ submitting
```

Button text:

```text
Approving...
```

Disable duplicate clicks.

---

# 27. REJECT BUTTON

Default:

```text
Reject
```

Secondary/outline action.

When clicked:

```text
Reject
→ optional reason
→ submitting
```

Do not immediately terminate the run locally.

---

# 28. REASON FIELD

If supported by the current frontend/backend contract:

```text
Reason
[ optional explanation... ]
```

Use the backend's accepted request body.

Do not send unsupported fields.

---

# 29. APPROVAL SUBMISSION FLOW

Frontend:

```text
click Approve
 ↓
set submitting=true
 ↓
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
 ↓
HTTP response received
 ↓
await SSE/backend state
 ↓
approval.decided
 ↓
run state transition
```

The POST response itself is not necessarily the complete run outcome.

---

# 30. APPROVAL SUBMISSION LOCK

While submitting:

```text
Approve disabled
Reject disabled
```

Prevent accidental double submission.

If request fails:

```text
re-enable actions
show error
refresh approval
```

---

# 31. APPROVAL SUCCESS

After backend confirms approval:

```text
approval.decided
decision=approved
```

show:

```text
✓ APPROVED
```

Then:

```text
WAITING
→ RUNNING
```

only when backend reports that transition.

---

# 32. APPROVAL REJECTION

After backend confirms:

```text
approval.decided
decision=rejected
```

show:

```text
REJECTED
```

Then refresh run.

If backend ends the run:

```text
run.failed
```

show final failure state.

---

# 33. DO NOT LOCALLY RESUME EXECUTION

After approve, frontend must never:

```text
start next tool
send email
execute workflow
```

It only waits for backend confirmation.

---

# 34. DO NOT LOCALLY FAIL EXECUTION

After reject, frontend must never:

```text
mark failed
terminate backend
delete artifacts
```

unless an explicit backend endpoint/action says so.

Wait for backend.

---

# 35. APPROVAL DECIDED EVENT

When:

```text
approval.decided
```

arrives:

```text
ApprovalStore
→ decision

Timeline
→ append

Approval UI
→ show decision

Run
→ await backend terminal/resume state
```

---

# 36. APPROVAL DECISION CONFLICT

If two clients attempt decisions:

```text
Client A → approve
Client B → reject
```

backend decides the truth.

Frontend receiving an error should:

```text
refresh approval
refresh run
```

Do not try to resolve the conflict in frontend.

---

# 37. STALE APPROVAL

An approval may no longer be actionable.

Symptoms:

```text
400
conflict-like backend response
```

UI:

```text
This approval is no longer active.

[Refresh]
```

Do not leave an indefinitely enabled approve button.

---

# 38. APPROVAL NETWORK ERROR

If POST fails due to transport:

```text
Could not submit approval.
```

Do not claim rejection/approval.

Refresh when appropriate.

---

# 39. APPROVAL BACKEND ERROR

If backend returns:

```text
400
```

for invalid/stale decision:

```text
The approval state has changed.
```

Then:

```text
refresh
```

---

# 40. APPROVAL SERVER UNAVAILABLE

If:

```text
503 / network unavailable
```

show:

```text
SyncNode backend unavailable.

Your approval decision was not confirmed.

[Retry]
```

Do not claim it was submitted successfully.

---

# 41. APPROVAL DOUBLE-CLICK

Prevent with:

```text
submitting=true
```

and disable.

---

# 42. APPROVAL REFRESH

Provide:

```text
Refresh
```

for stale/error state.

It should call:

```text
GET /runs/{run_id}
```

and approval-related snapshot/evidence endpoints as supported.

---

# 43. APPROVAL STATE AFTER REFRESH

Possible:

```text
waiting_approval
```

→ card remains

```text
running
```

→ approval no longer active

```text
failed
```

→ show failure

```text
completed
```

→ show completion

```text
cancelled
```

→ show cancellation

The backend wins.

---

# 44. RUN STATUS + APPROVAL

Rules:

```text
waiting_approval
→ Approval surface open

running
→ Approval surface only if still pending from backend

completed
→ Approval closed

failed
→ Approval closed

cancelled
→ Approval closed
```

Do not leave an approval overlay open when the backend says the run is terminal.

---

# 45. APPROVAL REOPENING

If the user navigates away and returns while the run is still:

```text
waiting_approval
```

rehydrate:

```text
GET run
GET steps
GET artifacts
GET verifications
GET context
```

and restore approval UI.

Do not require the original SSE event to still exist.

---

# 46. ELECTRON RESTART DURING APPROVAL

On app restart:

```text
splash
→ health
→ find active/waiting runs
→ hydrate run
```

If backend says:

```text
waiting_approval
```

reopen the approval experience.

Do not generate a new approval.

---

# 47. MULTIPLE WAITING RUNS

If multiple runs can be waiting:

Sidebar:

```text
WAITING

● Monthly Report
● Procurement Draft
```

Each approval belongs to:

```text
run_id + approval_id
```

Selecting one changes the active run.

Do not mix approval state between runs.

---

# 48. ACTIVE APPROVAL IDENTIFIER

Never rely on:

```text
selectedRunId only
```

for decisions.

Use:

```text
run_id
approval_id
```

from backend state.

---

# 49. APPROVAL HISTORY

Keep a frontend history for the currently loaded run:

```text
requested
approved/rejected
timestamp
```

Historical audit remains backend-owned.

---

# 50. APPROVAL + RUN DETAIL

The run detail should have:

```text
Overview
Workflow
Timeline
Artifacts
Evidence
Approval
Audit
```

Approval becomes selected when pending.

---

# 51. APPROVAL DETAIL DRAWER

Display:

```text
Approval
ID
Run
Step
Action
Risk
Requested
Decision
Reason
```

Use only actual fields.

---

# 52. APPROVAL RISK PRESENTATION

If risk exists:

```text
Risk
External communication
```

Use a restrained warning indicator.

Do not use sensational language.

---

# 53. HIGH-ATTENTION VISUAL STATE

Approval may use:

```text
yellow/amber
```

with:

```text
lock icon
```

The application should not feel like an emergency alarm.

---

# 54. APPROVAL BOUNDARY LANGUAGE

Preferred:

```text
Review required
Approval required
Waiting for approval
```

Avoid:

```text
DANGER
CRITICAL ALERT
SYSTEM THREAT
```

unless backend evidence actually warrants such language.

---

# 55. EXTERNAL EMAIL APPROVAL

Known product pattern:

```text
draft
→ attachments
→ review
→ approval
→ no automatic send
```

The frontend should show:

```text
Send has not been executed.
```

only when backend state/evidence supports this.

---

# 56. APPROVAL BEFORE SEND

The frontend should never show:

```text
Sent
```

from:

```text
approval.requested
```

or:

```text
approval.decided approved
```

alone.

The send outcome, if ever supported, must come from backend execution state/event.

---

# 57. APPROVAL + NO-SEND GOLDEN TEST

For the local golden workflow:

```text
approval.requested
→ run.waiting_approval
```

Expected UI:

```text
WAITING FOR APPROVAL
Nothing has been sent.
```

Do not render a send-success message.

---

# 58. APPROVAL + THREE ARTIFACTS

The final UI should show:

```text
Attachments

✓ SyncNode_Word_<run>.docx
✓ SyncNode_Excel_<run>.xlsx
✓ SyncNode_Presentation_<run>.pptx
```

These must come from backend artifact state.

---

# 59. APPROVAL + VERIFICATION

Display:

```text
Verified
9 PASS
```

only if the backend actually returns those results/counts.

Do not infer a count from visual cards.

---

# 60. APPROVAL + OBSERVATIONS

Provide an expandable:

```text
Latest observation
```

for the email/application state.

This can include:
- screenshot
- application
- window
- timestamp

if available.

---

# 61. APPROVAL + TOOL HISTORY

Show:

```text
Recent tools

browser.navigate ✓
browser.type ✓
browser.attach_file ✓
```

only from actual tool state.

---

# 62. APPROVAL + RECOVERY

If recovery happened before approval:

```text
Recovered
```

can be shown in timeline/evidence.

Do not make recovery itself an approval reason unless backend says so.

---

# 63. APPROVAL + PLAN

Show the final validated plan relevant to the approval:

```text
Email draft
→ verify attachments
→ request approval
```

If replan occurred, use the latest backend plan.

---

# 64. APPROVAL + AGENT SUMMARY

Supervisor or Email Agent summary may be shown:

```text
Draft prepared and verified.
Awaiting your approval before external communication.
```

Use backend-safe summary content if available.

---

# 65. APPROVAL + WORKFLOW MEMORY

After approval is decided, the backend may emit:

```text
workflow.memory_recorded
```

This belongs in timeline/history, not inside the approval decision itself.

---

# 66. APPROVAL + AUDIT

When approval is requested and decided:

```text
audit
→ request
→ decision
```

The frontend may link to those entries.

Do not create frontend audit entries.

---

# 67. APPROVAL UI COMPONENT TREE

Suggested:

```text
ApprovalPanel
├─ ApprovalHeader
├─ ActionSummary
├─ RiskBadge
├─ RecipientSummary
├─ SubjectSummary
├─ ArtifactList
├─ VerificationSummary
├─ EvidenceLink
├─ ApprovalHistory
└─ ApprovalActions
   ├─ RejectButton
   └─ ApproveButton
```

---

# 68. APPROVAL OVERLAY COMPONENT

Suggested:

```text
ApprovalOverlay
├─ Backdrop
├─ ApprovalPanel
└─ KeyboardFocusTrap
```

Do not prevent the user from accessing necessary evidence.

---

# 69. APPROVAL FOCUS MANAGEMENT

When approval opens:

```text
focus approval card heading
```

Then:

```text
Tab
→ action summary
→ evidence
→ reject
→ approve
```

Keep focus within modal/dialog if using modal semantics.

---

# 70. ESCAPE BEHAVIOR

Pressing:

```text
Esc
```

may collapse/close the visual approval drawer only if safe.

It must NOT:
- reject approval
- approve approval
- terminate run

unless specifically mapped through a deliberate action.

A collapsed approval must remain visibly available in the run state.

---

# 71. APPROVAL MOBILE/SMALL WIDTH

The app is desktop-first.

If right panel becomes too narrow:

```text
Approval becomes a larger drawer/overlay
```

but remains within the desktop workspace.

---

# 72. APPROVAL RESPONSIVE BEHAVIOR

At 1440x900:

```text
right-side approval panel
```

At smaller supported sizes:

```text
wider overlay
```

Do not destroy the workflow/desktop context.

---

# 73. APPROVAL ANIMATION

Opening:

```text
background dim
→ panel fade/slide
→ lock indicator appears
```

Approving:

```text
submitting
→ button spinner
→ backend-confirmed approved
```

Rejecting:

```text
submitting
→ backend-confirmed rejected
```

---

# 74. APPROVAL SUCCESS ANIMATION

Do not celebrate too early.

Correct:

```text
Approved
→ backend resumes
→ active execution
```

Then activity animations resume from real events.

---

# 75. APPROVAL REJECTION ANIMATION

```text
Rejected
→ approval card settles
→ run status updates from backend
```

No dramatic failure explosion.

---

# 76. APPROVAL FAILURE STATE

If approval submission fails:

```text
Approval not confirmed
```

and keep the card.

---

# 77. APPROVAL STALE STATE ANIMATION

If stale:

```text
approval card
→ neutral transition
→ "No longer active"
```

then refresh.

---

# 78. APPROVAL BUTTON TEXT

Normal:

```text
Approve
Reject
```

Submitting:

```text
Approving...
Rejecting...
```

Confirmed:

```text
Approved
Rejected
```

These states must follow backend confirmation.

---

# 79. APPROVAL REASON DISPLAY

If decision reason exists:

```text
Reason
"Looks good"
```

Show it in detail/history.

---

# 80. APPROVAL AUDIT NAVIGATION

Click:

```text
View audit
```

scroll/focus the audit entry where possible.

---

# 81. APPROVAL EVIDENCE NAVIGATION

Click:

```text
View evidence
```

select:
- relevant step
- verification
- artifact
- observation

---

# 82. APPROVAL ARTIFACT NAVIGATION

Click attachment:

```text
artifact detail
```

not an arbitrary filesystem access.

---

# 83. APPROVAL TIMELINE NAVIGATION

Click approval event:

```text
Approval panel selected
```

The UI remains synchronized.

---

# 84. APPROVAL GRAPH NAVIGATION

Click approval node:

```text
Approval panel open
```

and highlight related step.

---

# 85. APPROVAL STATE RECONCILIATION

Potential sequence:

```text
approval.requested
→ UI opens

REST says waiting_approval
→ UI confirms

approval.decided approved
→ UI says approved

REST says running
→ UI resumes
```

This is the ideal flow.

---

# 86. EVENT ARRIVAL RACE

Possible:

```text
run.waiting_approval
```

arrives before:

```text
approval.requested
```

Frontend must handle either order.

Use:
- state merge
- REST hydration
- pending approval reconciliation

Do not crash.

---

# 87. APPROVAL DATA ARRIVAL RACE

Possible:

```text
approval.requested
```

contains minimal data.

Then REST returns full approval details.

Use:

```text
event
→ create placeholder
→ REST hydrate
→ enrich
```

Do not duplicate approval cards.

---

# 88. DUPLICATE APPROVAL EVENT

If duplicate:

```text
approval.requested
```

received:

update existing approval.

Do not create two approval panels.

---

# 89. DUPLICATE DECISION EVENT

If duplicate:

```text
approval.decided
```

do not duplicate history.

---

# 90. APPROVAL EVENT IDENTITY

Use:

```text
approval_id
```

as primary identity where available.

---

# 91. APPROVAL STORE MERGE

When event arrives:

```text
merge by approval_id
```

Do not replace unrelated approval objects.

---

# 92. MULTI-RUN APPROVAL STORE

Use:

```text
approvalsById
activeApprovalByRunId
```

conceptually.

Do not store one global approval that can be overwritten by another run.

---

# 93. ACTIVE APPROVAL SELECTOR

Conceptually:

```ts
selectActiveApproval(runId)
```

must return the approval for the selected run.

---

# 94. APPROVAL ACTION SAFETY

Before sending decision:

validate frontend presence of:

```text
run_id
approval_id
decision
```

Do not submit if missing.

---

# 95. APPROVAL API CLIENT

Create:

```text
src/services/api/approvals.ts
```

Example:

```ts
export async function decideApproval(
  runId: string,
  approvalId: string,
  decision: "approved" | "rejected",
  reason?: string
) {
  // typed POST to existing backend route
}
```

Use actual generated types if available.

---

# 96. NO DIRECT FETCH IN APPROVAL COMPONENT

Bad:

```ts
fetch("/api/v1/runs/...")
```

inside JSX component.

Good:

```text
ApprovalPanel
→ useApprovalActions()
→ approvals.ts
→ backend
```

---

# 97. APPROVAL HOOK

Suggested:

```text
useApproval(runId)
useApprovalActions(runId)
```

Responsibilities:
- select active approval
- submit decision
- expose pending/error state

---

# 98. APPROVAL ACTION STATE

Possible:

```text
idle
submitting
success
error
stale
```

Backend run state remains separate.

---

# 99. APPROVAL ERROR MODEL

Frontend action errors:

```text
validation error
network error
backend error
stale approval
unknown error
```

Map to user-readable text.

Do not fabricate technical causes.

---

# 100. APPROVAL TOASTS

Do not use a normal toast as the only approval UX.

Approval is a primary screen.

Toasts may supplement:

```text
Approval submitted
```

after backend response, while the main state waits for confirmation.

---

# 101. APPROVAL SOUND

Optional subtle notification sound may occur on approval request if product settings allow.

Keep disabled by default or respectful.

Do not use alarming sounds.

---

# 102. APPROVAL ACCESSIBILITY

Use:

```text
role="dialog"
aria-labelledby
aria-describedby
```

where appropriate.

Buttons need clear labels.

Example:

```text
Approve external communication
Reject external communication
```

---

# 103. APPROVAL KEYBOARD ACTIONS

Avoid dangerous single-key shortcuts.

Do not map:

```text
Enter = Approve
```

automatically.

Explicit focus + button activation is safer.

---

# 104. APPROVAL CONFIRMATION FOR HIGH-RISK ACTIONS

Do not invent a second confirmation if backend does not require it.

If product design wants a confirmation step, it must remain a frontend interaction before submitting the existing approved decision.

---

# 105. APPROVAL REVIEW SUMMARY

Show compact:

```text
1 action
3 attachments
9 verifications
0 sends
```

where backend evidence supports these values.

---

# 106. APPROVAL REVIEW DETAILS

Expandable:

```text
Plan
Tools
Observations
Verification
Artifacts
Context
Audit
```

This creates a deep-review path without cluttering the primary card.

---

# 107. APPROVAL COLLAPSED STATE

If user collapses the approval panel:

```text
WAITING FOR APPROVAL
```

must remain visible in:
- top bar
- status bar
- left run item
- workflow graph approval node

This prevents accidental loss of the approval state.

---

# 108. APPROVAL RETURN FROM OTHER SCREEN

If user opens Knowledge while approval is pending:

the approval indicator persists.

Returning to run:

```text
approval panel
```

can be restored.

---

# 109. APPROVAL ROUTE GUARD

If the user navigates to another route while approval is pending:

do not discard approval state.

---

# 110. APPROVAL ON APP RELOAD

After reload:

```text
GET recent runs
```

identify:

```text
waiting_approval
```

restore the approval state from backend snapshot.

---

# 111. APPROVAL + SSE DISCONNECT

If SSE disconnects while approval is open:

```text
approval remains visible
```

but state indicator becomes:

```text
RECONNECTING
```

Do not assume decision state changed.

---

# 112. APPROVAL + SSE RECONNECT

On reconnect:

```text
REST refresh
→ SSE resume
```

If approval already decided:

update.

If still waiting:

keep card.

---

# 113. APPROVAL + BACKEND RESTART

If backend restarts:

```text
SSE disconnected
health degraded
```

Approval card may temporarily show:

```text
Decision unavailable while reconnecting
```

Do not submit duplicate actions automatically.

---

# 114. APPROVAL REQUEST EXPIRATION

If backend reports the request is no longer active:

```text
Approval expired/no longer available
```

Only use wording supported by backend state.

---

# 115. APPROVAL HISTORY SCREEN

Run detail may show:

```text
Approval History

Requested
15:42

Approved
15:44
```

or:

```text
Rejected
15:44
```

Use actual decision history.

---

# 116. APPROVAL AUDIT RELATION

The frontend can show:

```text
Approval requested
↓
Approval decided
```

linked to audit.

---

# 117. APPROVAL + FINAL STATUS

After decision:

```text
approved
→ backend continues

rejected
→ backend determines terminal state
```

Do not infer the exact terminal state from UI action alone.

---

# 118. APPROVAL + REAL SEND

If the backend later reports a real external send result in a separate event, only then can the frontend show:

```text
Sent
```

The current local golden flow is expected to stop at approval.

---

# 119. APPROVAL SECURITY UI

Do not expose controls to:
- bypass approval
- force approve
- execute send anyway
- modify policy
- change risk classification

The frontend is not an authority layer.

---

# 120. APPROVAL STATE COLOR

Use:

```text
yellow/amber
```

for waiting.

Green:

```text
approved/confirmed
```

Red:

```text
rejected/error
```

Neutral:

```text
inactive
```

Never rely on color alone.

---

# 121. APPROVAL ICONOGRAPHY

Use:

```text
lock
shield
check
x
```

Keep visual language consistent.

---

# 122. APPROVAL MOTION REDUCED

Respect reduced motion.

When reduced:

```text
no large dim transition
no pulsing
```

but preserve clear visual state.

---

# 123. APPROVAL EVENT TIMELINE GROUP

Group:

```text
approval.requested
run.waiting_approval
approval.decided
```

as:

```text
Approval lifecycle
```

if useful.

Expanded view retains actual events.

---

# 124. APPROVAL DETAIL PAYLOAD

Never assume:

```text
recipient
subject
risk
attachments
```

are always present.

Use:
- backend event payload
- REST details
- artifacts
- steps
- context

where available.

---

# 125. APPROVAL DATA FALLBACK

If recipient unavailable:

```text
Recipient
Not provided
```

or hide field.

Do not invent.

---

# 126. APPROVAL ACTION FALLBACK

If action unavailable:

```text
Review required
```

instead of guessing exact operation.

---

# 127. APPROVAL ARTIFACT FALLBACK

If attachments are not included in approval payload:

load from:

```text
GET /artifacts
```

and/or run evidence.

Do not infer from filenames alone.

---

# 128. APPROVAL VERIFICATION FALLBACK

If approval payload has no verification summary:

use:

```text
GET /verifications
```

to assemble evidence.

---

# 129. APPROVAL OBSERVATION FALLBACK

If no screenshot is provided:

show textual evidence only.

Do not fabricate visual evidence.

---

# 130. APPROVAL RISK FALLBACK

If backend does not provide a risk value:

do not invent "high/medium/low".

Show:

```text
Risk information unavailable
```

or hide it.

---

# 131. APPROVAL UI DATA FLOW

Canonical:

```text
approval.requested
        ↓
approval identity
        ↓
load/enrich run snapshot
        ↓
load artifacts
        ↓
load verifications
        ↓
load context if useful
        ↓
render approval
```

---

# 132. APPROVAL REQUEST HYDRATION

On request:

```text
GET run
GET steps
GET tools
GET artifacts
GET verifications
GET observations
GET context
```

Do not necessarily wait for all before showing the initial approval.

Show:
```text
Approval requested
Loading review evidence...
```

Then progressively enrich.

---

# 133. APPROVAL PROGRESSIVE LOADING

Initial:

```text
Review required
Action
Risk
```

Then:

```text
Artifacts
Verification
Observation
```

Then:

```text
Context
Audit
```

This keeps the card responsive.

---

# 134. APPROVAL EVIDENCE LOADING

Use skeleton states:

```text
Loading artifacts...
Loading verification...
```

Do not show false checkmarks while loading.

---

# 135. APPROVAL CARD LOADING

Initial state:

```text
Review required
Loading details...
```

Buttons should remain disabled until required approval identity/decision data is valid.

---

# 136. APPROVAL ACTION DISABLE RULES

Disable when:

```text
missing approval_id
missing run_id
submitting
known stale
backend disconnected if submission cannot succeed
```

Reconnect state should not accidentally enable action if transport is unavailable.

---

# 137. APPROVAL BUTTON ERROR RECOVERY

After failed POST:

```text
Approval not confirmed.
```

Then:

```text
GET run
```

and refresh approval.

---

# 138. APPROVAL STATE RESTORE

If frontend store is lost:

```text
REST
→ reconstruct active approval
```

No frontend-only persistence is required for approval authority.

---

# 139. APPROVAL HISTORY RESTORE

Historical decisions come from backend-supported data/audit.

Do not rely solely on local store history.

---

# 140. APPROVAL + TERMINATION

If user presses Stop Run while approval is pending:

use the existing run termination API:

```text
POST /api/v1/runs/{run_id}/terminate
```

Then wait for backend state.

Do not interpret Stop as Reject unless backend semantics explicitly define that.

---

# 141. STOP VS REJECT

These are different actions:

```text
Reject approval
```

versus:

```text
Terminate run
```

Do not conflate them.

---

# 142. APPROVAL + NAVIGATION

Navigation should not submit/modify approval.

Only explicit Approve/Reject/Stop actions do.

---

# 143. APPROVAL + WINDOW CLOSE

Closing Electron should not automatically:
- approve
- reject
- terminate

unless separately designed and authorized.

---

# 144. APPROVAL + MULTI-WINDOW

If multiple Electron windows are supported:

backend is authority.

A second window may receive the same approval.

Backend resolves concurrent decisions.

---

# 145. APPROVAL TEST FIXTURE

Create frontend event fixtures:

```text
approval.requested.json
run.waiting_approval.json
approval.decided.approved.json
approval.decided.rejected.json
```

Use the actual contract shapes.

---

# 146. APPROVAL COMPONENT TEST

Verify:

```text
approval requested
→ panel visible
→ user sees action
→ approve button visible
→ reject button visible
```

---

# 147. APPROVAL SUBMIT TEST

Mock:

```text
POST /approvals/{id}/decide
```

Verify:
- correct run_id
- correct approval_id
- correct decision
- optional reason only when supported

---

# 148. APPROVAL RESPONSE TEST

After successful POST:

do not immediately mark run approved.

Wait for:

```text
approval.decided
```

and/or REST refresh.

---

# 149. APPROVAL REJECT TEST

Verify:

```text
rejected
```

appears only after backend confirmation.

---

# 150. STALE APPROVAL TEST

Simulate backend rejection of decision.

Verify:

```text
stale card
refresh
no false state
```

---

# 151. APPROVAL RECONNECT TEST

Simulate:

```text
approval requested
SSE disconnected
SSE reconnect
REST says waiting
```

Verify:
```text
approval remains
```

---

# 152. APPROVAL DECIDED DURING DISCONNECT

Simulate:

```text
SSE disconnected
user returns
REST says approved/running
```

Verify:

```text
approval panel closes
run state reconciles
```

---

# 153. DUPLICATE APPROVAL TEST

Send duplicate events.

Verify:

```text
one approval card
one history entry
```

---

# 154. UNKNOWN EVENT TEST

Send:

```text
approval.future_field_changed
```

or another unknown event.

Verify:
- no crash
- existing approval preserved

---

# 155. APPROVAL UI E2E TEST

Run:

```text
Home
→ create mock/real run
→ receive approval
→ approval panel
→ inspect evidence
→ click approve
→ backend confirmation
→ resumed state
```

---

# 156. GOLDEN APPROVAL TEST

Using the real local golden backend:

```text
Word
Excel
PowerPoint
Email Draft
Three attachments
Verification
Approval
```

The Electron frontend must show:

```text
WAITING FOR APPROVAL
```

with all verified evidence.

---

# 157. NO-SEND ASSERTION IN UI TEST

The frontend must not display:

```text
email sent
```

in the golden approval state.

Backend state is authoritative.

---

# 158. APPROVAL + THREE ATTACHMENT ASSERTION

UI test should verify:

```text
Word
Excel
PowerPoint
```

are all visible as current-run verified attachments when backend reports them.

---

# 159. APPROVAL + ARTIFACT HASH

Optional evidence drawer shows:

```text
SHA256
...
```

if backend exposes it.

Do not compute a competing frontend hash and treat it as authority unless only for display/diagnostics.

---

# 160. APPROVAL + RAG

When approval is active:

show optional:

```text
Why this was planned
```

containing safe plan/context summaries.

Do not expose private model reasoning.

---

# 161. APPROVAL + SAFE THINKING

Never show chain-of-thought.

Only:

```text
Plan summary
Decision summary
Verification summary
```

---

# 162. APPROVAL + LOCAL MODEL

Model panel may show:

```text
Gemma 4 E4B
Ollama
GPU
```

but approval UI should not depend on model availability after the request unless backend does.

---

# 163. APPROVAL + HEALTH

If backend becomes unhealthy:

```text
Approval decision may not be submitted.
```

Do not automatically alter approval state.

---

# 164. APPROVAL + BROWSER

For local compose:

show:

```text
Browser / Email Draft
```

and relevant observation.

Do not confuse local compose with real external sending.

---

# 165. APPROVAL + APPLICATION STATE

Center mirror should show current application observation if available.

---

# 166. APPROVAL + VERIFICATION STATE

All critical verification results should remain inspectable.

---

# 167. APPROVAL + FAILURE BEFORE APPROVAL

If a critical step fails before approval:

```text
approval should not remain active
```

unless backend explicitly says it remains actionable.

The run state wins.

---

# 168. APPROVAL + RECOVERY BEFORE APPROVAL

Recovery history remains visible.

The approval card should represent the latest confirmed state.

---

# 169. APPROVAL + REPLAN BEFORE APPROVAL

If backend replans and then requests approval:

the approval card should use:
- latest plan
- current evidence
- current artifacts

Do not show outdated plan information as authoritative.

---

# 170. APPROVAL + ARTIFACT REFRESH

When a verified artifact arrives immediately before approval:

the card should update.

Do not freeze artifact list at first approval event.

---

# 171. APPROVAL ARTIFACT COUNT

If backend exposes attachment list:

display actual count.

Otherwise:
```text
attachments present
```

without inventing count.

---

# 172. APPROVAL SUMMARY HEADER

Example:

```text
REVIEW REQUIRED
External communication
3 verified attachments
```

---

# 173. APPROVAL FULLSCREEN OPTION

Optional:

```text
Focus review
```

can expand approval into a larger centered panel.

Still keep evidence accessible.

---

# 174. APPROVAL PANEL WIDTH

Suggested:

```text
360–520px
```

depending on window.

---

# 175. APPROVAL CARD SPACING

Prioritize readability.

Avoid giant cards with excessive empty space.

---

# 176. APPROVAL VISUAL TOKENS

Use:

```text
background: dark
border: subtle amber
icon: lock
primary: neutral/white
approval accent: yellow/amber
```

The overall app remains monochrome-first.

---

# 177. APPROVAL MICRO-ANIMATIONS

Use:
- fade
- small translate
- border glow
- button spinner

Avoid:
- shaking
- alarming flashes
- giant modal zoom

---

# 178. APPROVAL REDUCED MOTION

If reduced motion:

```text
instant state change
minimal fade
```

---

# 179. APPROVAL SOUND/NOTIFICATION SETTINGS

Optional.

Respect user's settings.

---

# 180. APPROVAL SCREEN RE-ENTRY

Returning to a waiting run should immediately show:

```text
WAITING FOR APPROVAL
```

not a generic run screen until the user finds the approval.

---

# 181. APPROVAL BADGE IN SIDEBAR

Example:

```text
Runs
  ● 2 waiting
```

If actual backend run list supports it.

---

# 182. APPROVAL BADGE IN TOP BAR

```text
🔒 WAITING
```

while active.

---

# 183. APPROVAL BADGE IN GRAPH

```text
🔒 APPROVAL
```

---

# 184. APPROVAL BADGE IN TIMELINE

```text
REVIEW REQUIRED
```

---

# 185. APPROVAL BADGE IN STATUS BAR

```text
WAITING FOR APPROVAL
```

These four surfaces should reinforce one state.

---

# 186. APPROVAL CONSISTENCY RULE

At all times:

```text
Approval panel
=
Run status
=
Graph approval node
=
Timeline approval event
=
Sidebar badge
```

within frontend synchronization limits.

If temporary mismatch occurs:

```text
REST reconciliation
```

resolves it.

---

# 187. APPROVAL + SSE EVENT ORDER

Do not require an exact hardcoded event sequence.

Implement robust event handling.

---

# 188. APPROVAL + REST SNAPSHOT ORDER

Do not assume SSE always arrives after REST.

Merge safely.

---

# 189. APPROVAL + CACHE

Approval state should not come from stale local cache when fresh backend data exists.

---

# 190. APPROVAL + ROUTER

If user deep-links to:

```text
/runs/<runId>
```

and backend says:

```text
waiting_approval
```

open approval UI.

---

# 191. APPROVAL + HISTORY

If run is already:

```text
completed
```

show past approval history if available, but no active approval controls.

---

# 192. APPROVAL + FAILED HISTORY

If run failed after rejection:

show:

```text
Approval
Rejected

Final run state
Failed
```

if backend reports both.

---

# 193. APPROVAL + TERMINAL HISTORY

Historical approval decisions remain inspectable.

---

# 194. APPROVAL + AUDIT CHAIN

Audit remains backend-owned.

Frontend displays it.

---

# 195. APPROVAL + LEARNING

If workflow memory records after decision:

show in timeline:

```text
Workflow remembered
```

but do not alter approval UI.

---

# 196. APPROVAL + KNOWLEDGE

Knowledge context can be shown as supporting evidence.

Never treat frontend knowledge display as policy authority.

---

# 197. APPROVAL + TOOLS CATALOG

The approval panel may link to tool detail if useful:

```text
browser.attach_file
```

but do not expose an execution button.

---

# 198. APPROVAL + AGENT DETAIL

Link:

```text
Email Agent
```

to its activity if useful.

---

# 199. APPROVAL + EVIDENCE DEEP LINK

Every approval-related event should ideally let the user inspect:

```text
step
tool
observation
verification
artifact
```

where identifiers are available.

---

# 200. APPROVAL + TIMELINE FILTER

Selecting Approval filter should show:

```text
approval.requested
approval.decided
run.waiting_approval
```

and related evidence.

---

# 201. APPROVAL + EXPORT

Optional frontend-only export of the visible review summary:

```text
Action
Risk
Artifacts
Verification
Decision
```

Do not modify backend audit.

---

# 202. APPROVAL + PRINT/PDF

Optional frontend-side review view may be printable.

Do not generate authoritative documents that claim backend audit status beyond the loaded data.

---

# 203. APPROVAL + DEVELOPER MODE

Developer details may expose:

```text
run_id
approval_id
event_type
timestamp
payload
```

Keep collapsed.

---

# 204. APPROVAL + PROD MODE

Default:

```text
Action
Risk
Artifacts
Verification
Decision
```

No raw payload dump.

---

# 205. APPROVAL + ERROR DETAILS

Developer mode may show:
- HTTP status
- response type
- request id

where available.

---

# 206. APPROVAL + PRIVACY

Avoid storing approval content permanently in renderer localStorage.

Run data remains backend-owned.

---

# 207. APPROVAL + SENSITIVE CONTENT

If email body contains sensitive enterprise content:

do not expose the entire body in a notification/toast.

Use:
```text
View draft
```

within the controlled run UI.

---

# 208. APPROVAL + SCREENSHOT PRIVACY

Screenshot evidence should appear only within the active run evidence surface.

---

# 209. APPROVAL + CROSS-RUN ISOLATION

Approval panel must never display:
- artifacts from another run
- recipient from another run
- approval_id from another run

All references must include/run within selected run context.

---

# 210. APPROVAL ID VALIDATION

Before POST:

```text
approval.run_id === selected.run_id
```

or equivalent frontend consistency check.

If mismatch:

```text
refresh
```

Do not submit.

---

# 211. APPROVAL ACTION SERIALIZATION

Only one decision can be submitted at a time per approval.

---

# 212. APPROVAL REENTRY

After decision submission, disable active buttons until backend confirms.

---

# 213. APPROVAL BACKEND RESPONSE CACHE

Store response only as transient action state.

Final status comes from backend run/approval state.

---

# 214. APPROVAL COMPONENT DATA DEPENDENCIES

ApprovalPanel may consume:

```text
approval
run
artifacts
verifications
observations
context
timeline
```

but should not fetch them independently in multiple places.

Prefer shared hooks/store selectors.

---

# 215. APPROVAL HOOK COMPOSITION

Conceptual:

```text
useActiveRun
useActiveApproval
useRunArtifacts
useRunVerifications
useRunContext
useApprovalActions
```

---

# 216. APPROVAL REVIEW SELECTORS

Suggested:

```text
selectApprovalSummary
selectApprovalArtifacts
selectApprovalVerificationSummary
selectApprovalEvidence
selectApprovalStatus
selectApprovalActionable
```

---

# 217. APPROVAL SUMMARY DERIVATION

Example:

```text
Action
Recipient
Subject
Attachment count
Verification count
Risk
```

Derived from synchronized backend-backed state.

---

# 218. APPROVAL STATE TELEMETRY

Optional:

```text
Requested at
Time waiting
```

Use backend timestamp + local elapsed calculation.

---

# 219. WAITING DURATION

Example:

```text
Waiting 00:42
```

This is frontend-derived.

---

# 220. APPROVAL TIMEOUT

Do not invent a timeout unless backend/product contract defines one.

---

# 221. APPROVAL AUTO-EXPIRY

Do not implement frontend automatic rejection/approval.

Backend decides expiration if supported.

---

# 222. APPROVAL REMINDER

Optional subtle reminder if user navigates away:

```text
1 approval waiting
```

No backend change.

---

# 223. APPROVAL IN RUN LIST

Show:

```text
WAITING FOR APPROVAL
```

for waiting runs.

---

# 224. APPROVAL SEARCH

Run search can find:

```text
approval
waiting
```

using local run metadata.

---

# 225. APPROVAL NOTIFICATION BADGE

Use:

```text
●
```

or number in sidebar.

Only actual waiting approvals.

---

# 226. APPROVAL RESUME INDICATOR

After approved and backend says running:

```text
Approval complete
Resuming workflow...
```

Then actual tool/agent events resume.

---

# 227. APPROVAL REJECTION INDICATOR

After backend confirms rejection:

```text
Approval rejected
```

Then await final backend state.

---

# 228. APPROVAL ERROR RECOVERY FLOW

If decision POST fails:

```text
Approval panel
 ↓
error
 ↓
refresh
 ↓
new state
```

Not:

```text
error
 ↓
auto retry approve
```

unless idempotency and product contract explicitly support it.

---

# 229. APPROVAL RETRY

A manual Retry button may resubmit if:
- approval still active
- previous request was not confirmed
- backend contract makes it safe

Do not retry after confirmed decision.

---

# 230. APPROVAL DECISION IDEMPOTENCY

Do not invent an idempotency mechanism.

Use backend semantics.

If backend exposes request IDs/idempotency keys, integrate them.

---

# 231. APPROVAL TEST: DOUBLE SUBMIT

Click Approve twice quickly.

Expected:

```text
one request
one button submission
```

---

# 232. APPROVAL TEST: SWITCH RUN

Open approval for Run A.

Switch to Run B.

Click Approve.

Verify:

```text
decision uses B's run_id and approval_id
```

---

# 233. APPROVAL TEST: APP RELOAD

Open waiting approval.

Reload Electron.

Verify:

```text
approval restored
```

from backend.

---

# 234. APPROVAL TEST: SSE DROP

Disconnect SSE.

Approval remains.

Reconnect.

State reconciles.

---

# 235. APPROVAL TEST: DECISION DURING RECONNECT

If UI has an actionable approval and transport recovers:

allow decision only when request can be safely submitted.

---

# 236. APPROVAL TEST: STALE EVENT

Old approval event must not overwrite newer backend state.

---

# 237. APPROVAL TEST: TERMINAL EVENT

If:

```text
run.completed
```

arrives while approval card is open:

final REST refresh.

If backend says completed:

close approval.

---

# 238. APPROVAL TEST: FAILURE EVENT

If:

```text
run.failed
```

arrives:

close approval and show failure.

---

# 239. APPROVAL TEST: CANCELLED

If:

```text
run.cancelled
```

arrives:

close approval.

---

# 240. APPROVAL TEST: UNKNOWN APPROVAL FIELD

Extra backend field:

```text
new_field
```

must not break UI.

---

# 241. APPROVAL TEST: MISSING OPTIONAL FIELD

Missing:

```text
risk
```

should not break.

---

# 242. APPROVAL TEST: MISSING EVIDENCE

No screenshot.

UI still functions.

---

# 243. APPROVAL TEST: MISSING ARTIFACTS

No attachment list.

Approval remains functional if action identity exists.

---

# 244. APPROVAL TEST: MISSING SUMMARY

No summary.

Use minimal factual state.

---

# 245. APPROVAL TEST: NO ACTIVE APPROVAL

Run is running/completed.

Approval route/screen shows:

```text
No approval pending.
```

---

# 246. APPROVAL API CONTRACT TEST

Verify frontend calls:

```text
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
```

with the exact supported body.

---

# 247. APPROVAL REST CONTRACT TEST

Verify frontend can read:

```text
run
```

and determine:

```text
waiting_approval
```

without local assumptions.

---

# 248. APPROVAL SSE CONTRACT TEST

Verify:

```text
approval.requested
run.waiting_approval
approval.decided
```

parse correctly.

---

# 249. APPROVAL E2E — FRONTEND

Test:

```text
Launch Electron
→ backend ready
→ run
→ approval event
→ approval UI
→ evidence
→ approve
→ backend confirmation
→ resumed state
```

---

# 250. APPROVAL E2E — REJECTION

Test:

```text
run
→ approval
→ reject
→ backend confirmation
→ failed/terminal state
```

depending on actual backend result.

---

# 251. APPROVAL E2E — GOLDEN

Known final golden:

```text
Word
Excel
PowerPoint
Email
three attachments
verification
approval
```

must visually reach:

```text
WAITING FOR APPROVAL
```

---

# 252. APPROVAL GOLDEN SCREEN

Expected visual:

```text
┌─────────────────────────────────────────────────────────┐
│ MONTHLY OPERATIONS PACK                                 │
│                                                         │
│ ● WAITING FOR APPROVAL                                  │
├────────────────────┬──────────────────────┬─────────────┤
│ TASK               │ DESKTOP / WORKFLOW   │ REVIEW      │
│                    │                      │             │
│ ✓ Word             │ Email draft         │ REVIEW      │
│ ✓ Excel            │                      │ REQUIRED    │
│ ✓ PowerPoint       │ [actual state]      │             │
│ ✓ Email draft      │                      │ Recipient   │
│ 🔒 Approval        │                      │ Subject     │
│                    │ WORD ✓              │             │
│                    │ EXCEL ✓             │             │
│                    │ PPT ✓               │             │
│                    │ EMAIL ✓             │             │
├────────────────────┴──────────────────────┤             │
│ TIMELINE: Word ✓ | Excel ✓ | PPT ✓ |    │ [Reject]    │
│ Email ✓ | Approval 🔒                    │ [Approve]   │
└───────────────────────────────────────────┴─────────────┘
```

---

# 253. APPROVAL REVIEW CHECKLIST FOR USER

The UI should make these easy to verify:

```text
[ ] Action understood
[ ] Recipient visible if available
[ ] Subject visible if available
[ ] Body/draft accessible
[ ] Three artifacts visible
[ ] Artifacts verified
[ ] No-send state clear
[ ] Risk visible when available
[ ] Evidence accessible
```

---

# 254. APPROVAL DO-NOT

Never:

```text
[ ] auto-approve
[ ] auto-reject
[ ] send from Electron
[ ] call send API not defined by backend
[ ] bypass backend policy
[ ] change approval ID
[ ] infer approval from a timer
[ ] claim send success from approval
[ ] modify backend to simplify UI
```

---

# 255. APPROVAL SCREEN IMPLEMENTATION ORDER

Implement:

```text
1. approval API client
2. approval event types
3. approval reducer/store
4. approval selectors
5. approval panel
6. approval overlay
7. approval actions
8. evidence loading
9. artifact integration
10. verification integration
11. run reconciliation
12. SSE reconnect
13. stale-state handling
14. multi-run handling
15. accessibility
16. animation
17. tests
18. real Electron + backend validation
```

---

# 256. FRONTEND FILE STRUCTURE

Suggested:

```text
src/
├─ services/
│  └─ api/
│     └─ approvals.ts
│
├─ hooks/
│  └─ useApproval.ts
│
├─ stores/
│  └─ approvalStore.ts
│
├─ selectors/
│  └─ approvalSelectors.ts
│
├─ components/
│  └─ approval/
│     ├─ ApprovalPanel.tsx
│     ├─ ApprovalOverlay.tsx
│     ├─ ApprovalActions.tsx
│     ├─ ApprovalSummary.tsx
│     ├─ ApprovalEvidence.tsx
│     └─ ApprovalHistory.tsx
│
└─ tests/
   └─ approval/
```

Adapt to the existing frontend structure.

---

# 257. API CLIENT TYPE SAFETY

Use existing generated/shared types where available.

Do not redefine:

```text
approval decision values
```

differently in multiple files.

---

# 258. APPROVAL EVENT TYPE SAFETY

Use actual event contracts.

No:

```ts
event as any
```

throughout the approval system.

Use targeted parsing/guards.

---

# 259. APPROVAL UI STATE VS BACKEND STATE

Clearly separate:

```text
Frontend UI:
submitting
expanded
selected evidence
```

from:

```text
Backend:
waiting_approval
approved
rejected
running
failed
```

---

# 260. APPROVAL PANEL STATE

Conceptually:

```ts
interface ApprovalPanelState {
  open: boolean;
  selectedApprovalId?: string;
  expandedEvidence: boolean;
  submitting: boolean;
  error?: string;
}
```

---

# 261. APPROVAL BACKEND STATE

Conceptually:

```text
approval
run.status
events
artifacts
verifications
```

---

# 262. NO STATE DUPLICATION

Do not store separate inconsistent copies:

```text
approval.status
run.status
```

inside independent components.

Use centralized store/selectors.

---

# 263. APPROVAL REFRESH BUTTON

Safe action:

```text
Refresh
```

calls backend.

Do not refresh by reconstructing fake local state.

---

# 264. APPROVAL USER DECISION CONFIRMATION

After click:

```text
Submitting...
```

After response:

```text
Decision submitted
```

Then backend events determine final state.

---

# 265. APPROVAL HISTORY DETAIL

History item:

```text
Approved
by user
15:42
```

only when backend provides decision/reviewer information.

---

# 266. APPROVAL REVIEWER

Do not assume reviewer name.

If backend provides:

```text
reviewed_by
```

show it.

Otherwise:

```text
User
```

may be acceptable as UI context only if product semantics support it.

---

# 267. APPROVAL REQUEST TIMESTAMP

Use backend timestamp.

---

# 268. APPROVAL DECISION TIMESTAMP

Use backend timestamp.

---

# 269. APPROVAL WAIT TIMER

Derived:

```text
now - requested_at
```

only for visual elapsed time.

---

# 270. APPROVAL + CLOCK SKEW

Use backend timestamps only as reference.

Frontend elapsed display is approximate.

---

# 271. APPROVAL + PERFORMANCE

Approval opening should be immediate on event.

Detailed evidence can load asynchronously.

---

# 272. APPROVAL + LARGE ARTIFACT LIST

Virtualize or collapse when many attachments exist.

The current golden use case has three artifacts.

---

# 273. APPROVAL + LARGE AUDIT

Do not load the full audit inside the approval card.

Link to audit screen.

---

# 274. APPROVAL + LARGE TOOL HISTORY

Show concise summary and link to tools/timeline.

---

# 275. APPROVAL + LARGE OBSERVATION

Show latest relevant observation only.

---

# 276. APPROVAL + LARGE RAG

Show top relevant provenance and link to full context.

---

# 277. APPROVAL + LONG EMAIL BODY

Collapse body initially:

```text
View full draft
```

Do not overwhelm approval surface.

---

# 278. APPROVAL + BODY PREVIEW

Show a safe preview when backend provides body content.

Example:

```text
Hello team,

Please find attached...
```

Keep expandable.

---

# 279. APPROVAL + ATTACHMENT PREVIEW

Each:

```text
Word
Excel
PowerPoint
```

may show:
- icon
- filename
- verified

Avoid embedding complex Office viewers unless separately required.

---

# 280. APPROVAL + ARTIFACT OPEN

Use the same safe artifact-open mechanism as the artifact screen.

---

# 281. APPROVAL + EMAIL DRAFT

If backend exposes enough data, show:

```text
To
Subject
Body
Attachments
```

Do not invent missing fields.

---

# 282. APPROVAL + BROWSER OBSERVATION

If local compose screenshot available, show it in evidence.

---

# 283. APPROVAL + APPLICATION LABEL

Example:

```text
Email Draft
Local browser compose fixture
```

Only if backend indicates it.

---

# 284. APPROVAL + NO CLOUD

Approval screen does not need to expose provider internals.

Optional footer:

```text
● LOCAL
```

---

# 285. APPROVAL + SYSTEM HEALTH

Status bar remains:

```text
● Backend
● Local
```

If reconnecting:

```text
◌ Reconnecting
```

---

# 286. APPROVAL + OFFLINE

If backend is unavailable:

```text
Decision not confirmed.
```

Never imply completion.

---

# 287. APPROVAL + SESSION LOSS

If Electron closes:

backend approval remains.

Reopening reads backend state.

---

# 288. APPROVAL + MULTI-USER

Phase 1 is local single-user.

Do not build multi-user reviewer routing in frontend unless backend supports it.

---

# 289. APPROVAL + AUTH

Current local backend has no Phase-1 auth.

Do not invent authentication controls.

---

# 290. APPROVAL + POLICY

Never expose a "disable approval" switch unless backend explicitly provides one.

---

# 291. APPROVAL + RISK OVERRIDE

Never provide:

```text
Approve anyway
Ignore policy
Skip approval
```

---

# 292. APPROVAL + DEBUG BYPASS

Developer mode must not bypass approval.

---

# 293. APPROVAL + TEST MODE

Backend `failure_mode` remains testing-only where defined.

Do not expose arbitrary failure mode controls in normal approval UI.

---

# 294. APPROVAL + TERMINATE

Stop action remains separate from approval.

---

# 295. APPROVAL + REPLAY

Historical replay must not permit approval submission.

If viewing an old run:

```text
READ ONLY
```

---

# 296. APPROVAL + HISTORICAL RUN

If historical run has past approval:

show:

```text
Approved
```

or:

```text
Rejected
```

but no active buttons.

---

# 297. APPROVAL + HIDDEN STATE

Never hide waiting state because user changed tabs.

Keep global indicator.

---

# 298. APPROVAL + NOTIFICATION CENTER

Optional:

```text
1 approval waiting
```

Click opens run.

---

# 299. APPROVAL + COMMAND PALETTE

Command palette can include:

```text
Open approval
```

when one is pending.

Do not include:

```text
Approve now
```

without explicit selection/review.

---

# 300. APPROVAL + DEEP LINK

Deep link:

```text
syncnode://run/<run_id>
```

may be supported by Electron if desired, but approval action still requires valid backend state.

---

# 301. APPROVAL + WINDOW FOCUS

When approval request arrives, Electron may bring attention to the app if product settings allow.

Do not steal focus aggressively by default.

---

# 302. APPROVAL + SYSTEM NOTIFICATION

Optional local notification:

```text
SyncNode needs your approval.
```

Click opens the approval run.

No approval from notification alone.

---

# 303. APPROVAL + SECURITY

The approval action is sensitive.

Ensure preload/IPC does not expose arbitrary HTTP actions.

Renderer calls the typed approval service.

---

# 304. IPC APPROVAL BRIDGE

The approval POST may be initiated by renderer through the standard frontend HTTP client.

No special unrestricted IPC API is necessary unless architecture requires it.

---

# 305. APPROVAL + CORS / LOOPBACK

Use the existing backend access mechanism.

Do not modify backend CORS merely for convenience.

---

# 306. APPROVAL + URL VALIDATION

If backend base URL is configurable:

validate/normalize frontend configuration.

Do not allow arbitrary untrusted URLs in renderer actions without product requirements.

---

# 307. APPROVAL + ERROR TELEMETRY

Development mode can record:

```text
approval decision request
status
duration
```

without exposing sensitive data.

---

# 308. APPROVAL + ANALYTICS

Do not send approval data to third-party analytics.

SyncNode is local/offline.

---

# 309. APPROVAL + LOCAL STORAGE

Do not store approval content in localStorage by default.

---

# 310. APPROVAL + SESSION STATE

Approval UI state such as:

```text
expanded evidence
```

may be local.

Authority state remains backend.

---

# 311. APPROVAL + UI RESTORE

When returning to run:

restore:
```text
selected tab
selected evidence
```

but rehydrate approval truth from backend.

---

# 312. APPROVAL + SPLASH

Startup health sequence must finish before displaying an active approval.

If backend becomes ready and waiting run exists:

```text
splash
→ workspace
→ waiting approval
```

---

# 313. APPROVAL + HOME

Home may show:

```text
1 approval waiting
```

if recent run state provides it.

---

# 314. APPROVAL + RUNS LIST

Waiting rows should be visually elevated enough to find quickly.

---

# 315. APPROVAL + ACTIVE RUN PRIORITY

If user starts a new task while another run has a pending approval:

the frontend may allow it if backend supports multiple runs, but the waiting approval remains visible in sidebar.

Do not approve the wrong run.

---

# 316. APPROVAL + ONE ACTIVE RUN UX

If product chooses one active workspace at a time:

switching runs should preserve approval states in store.

---

# 317. APPROVAL + ARTIFACT CROSS-CHECK

Before displaying a critical attachment as verified:

use artifact identity + verified state.

Do not mark based solely on filename.

---

# 318. APPROVAL + STALE ARTIFACT

If backend marks artifact stale/unverified:

show that.

Do not turn it green because it exists locally.

---

# 319. APPROVAL + VERIFICATION FAIL

If a critical verification failed:

the approval should not be presented as ready unless backend explicitly says the approval remains valid.

Frontend should follow backend status.

---

# 320. APPROVAL + PARTIAL VERIFICATION

Show:

```text
Some checks are pending
```

only if backend state shows that.

---

# 321. APPROVAL + BLOCKED

If run/step is blocked:

show backend state.

Do not provide approval buttons unless backend says actionable.

---

# 322. APPROVAL + RECOVERY EXHAUSTED

If:

```text
recovery.exhausted
```

and run fails:

approval surface closes after reconciliation.

---

# 323. APPROVAL + CANCELLED DURING REVIEW

If user/device causes cancellation elsewhere:

frontend receives terminal state.

Close buttons.

Show cancelled state.

---

# 324. APPROVAL + DECISION AFTER CANCELLATION

If user tries to approve stale cancelled request:

backend rejects.

Frontend shows stale state.

---

# 325. APPROVAL + DECISION AFTER COMPLETION

Same.

---

# 326. APPROVAL + DECISION AFTER REJECTION

Same.

---

# 327. APPROVAL + DECISION AFTER APPROVAL

Same.

---

# 328. APPROVAL + BUTTON STATE FROM BACKEND

Actionable when:

```text
approval exists
and backend run is waiting_approval
and approval is not decided
```

Use actual backend fields/status.

---

# 329. APPROVAL + LOCAL OPTIMISTIC UI

Only optimize harmless visuals:

```text
submitting spinner
```

Do NOT optimistically mutate:

```text
approved
rejected
sent
completed
```

---

# 330. APPROVAL + EVENTUAL CONSISTENCY

The frontend may temporarily show:

```text
Decision submitted
```

before:

```text
Approved
```

This is acceptable and accurate.

---

# 331. APPROVAL + FINAL DECISION

Backend truth:

```text
approval.decided
```

and run snapshot.

---

# 332. APPROVAL + FINAL RUN

After decision:

```text
final run state
```

comes from:

```text
GET /runs/{id}
```

and events.

---

# 333. APPROVAL + FINAL EVIDENCE

Refresh:

```text
artifacts
verifications
audit
```

after terminal state.

---

# 334. APPROVAL + TIMELINE FREEZE

When waiting:

```text
timeline remains visible
```

but does not invent events.

If no new events arrive, it simply stays waiting.

---

# 335. APPROVAL + CURRENT ACTION

Top status:

```text
WAITING FOR APPROVAL
```

not:

```text
RUNNING
```

unless backend says otherwise.

---

# 336. APPROVAL + GRAPH ACTIVE PATH

The graph should stop visually advancing at:

```text
Approval
```

while waiting.

---

# 337. APPROVAL + DESKTOP ACTION

Do not animate desktop action during approval unless backend provides a new observation.

---

# 338. APPROVAL + AGENT ANIMATION

Agents waiting should stop active pulses.

---

# 339. APPROVAL + TOOL ANIMATION

No tool spinner should continue after the step is complete.

---

# 340. APPROVAL + ARTIFACT ANIMATION

Artifact cards remain settled.

---

# 341. APPROVAL + RAG ANIMATION

Knowledge activity should be completed.

---

# 342. APPROVAL + MEMORY

Memory indicator may remain historical.

---

# 343. APPROVAL + AUDIT

Audit remains available.

---

# 344. APPROVAL + USER CONFIDENCE

The interface should make the approval boundary feel deliberate:

```text
The machine has paused.
You decide what happens next.
```

Do not phrase it as persuasion.

---

# 345. APPROVAL + NO PRESSURE

Both buttons should be clear.

Do not visually manipulate the user into approval.

---

# 346. APPROVAL + PRIMARY ACTION BALANCE

The Approve button may be primary because it is the positive continuation action, but Reject must remain clearly accessible.

---

# 347. APPROVAL + DECISION COPY

Use neutral:

```text
Approve
Reject
```

not:

```text
Proceed safely
Cancel danger
```

---

# 348. APPROVAL + REVIEW LANGUAGE

Recommended:

```text
Review required
Nothing has been sent
3 verified attachments
```

---

# 349. APPROVAL + EVIDENCE LANGUAGE

Use:

```text
Verified
Observed
Prepared
Ready
```

only where backend evidence supports it.

---

# 350. APPROVAL + TRANSPARENCY

If evidence is incomplete:

```text
Some evidence is unavailable.
```

Do not hide the gap.

---

# 351. APPROVAL + BACKEND CONTRACT STABILITY

Use only:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

for contract definitions.

Do not alter them from the frontend.

---

# 352. APPROVAL + FRONTEND CONTRACT MAPPER

A single mapper should convert backend approval data into:

```text
ApprovalView
```

to keep UI stable.

---

# 353. APPROVAL + FRONTEND DOMAIN TYPES

Keep separate:

```text
ApiApproval
ApprovalView
ApprovalActionState
```

---

# 354. APPROVAL + EVENT MAPPER

Map backend events to domain actions:

```text
approval.requested
→ approvalRequested()

approval.decided
→ approvalDecided()
```

---

# 355. APPROVAL + REST MAPPER

Map backend snapshots to:

```text
approval state
```

without creating unsupported values.

---

# 356. APPROVAL + TEST DATA

Use contract-accurate fixtures.

Do not simplify fields if it changes semantics.

---

# 357. APPROVAL + FINAL TEST MATRIX

Run:

```text
[ ] request appears
[ ] card renders
[ ] evidence loads
[ ] artifacts load
[ ] verification loads
[ ] approve works
[ ] reject works
[ ] duplicate click prevented
[ ] stale approval handled
[ ] SSE reconnect
[ ] app reload
[ ] terminal reconciliation
[ ] multi-run isolation
[ ] unknown event tolerance
[ ] no backend modification
```

---

# 358. APPROVAL + REAL BACKEND TEST

At least one real Electron-to-backend test must use the real local backend.

Do not rely only on mocked SSE for final approval validation.

---

# 359. APPROVAL + REAL GOLDEN BACKEND

The final local golden run:

```text
Word
Excel
PowerPoint
Email
three artifacts
```

must reach:

```text
waiting_approval
```

and the Electron UI must reflect it.

---

# 360. APPROVAL + NO SEND

The frontend must not call any undocumented send endpoint.

For the golden workflow:

```text
send executions = 0
```

if backend reports that.

---

# 361. APPROVAL + BACKEND MODULE IMMUTABILITY

During frontend work:

```text
git diff
```

should show only frontend changes.

Before declaring done:

verify:

```text
no backend source modifications
```

---

# 362. FINAL FRONTEND GIT CHECK

Run:

```powershell
git status --short
git diff -- backend
git diff -- ai_ml
```

Expected:

```text
no changes to backend or ai_ml
```

unless those paths were already modified before the frontend task and the implementing editor carefully distinguishes pre-existing changes.

Do not revert unrelated user changes.

---

# 363. APPROVAL DOCUMENTATION

The frontend should include:

```text
docs/FRONTEND_APPROVAL_FLOW.md
```

This document is the source for:
- UI
- routes
- event mapping
- state machine
- testing
- safety behavior

---

# 364. IMPLEMENTATION HANDOFF

The implementing editor must read:

```text
docs/FRONTEND_MASTER.md
docs/ELECTRON_ARCHITECTURE.md
docs/FRONTEND_API_INTEGRATION.md
docs/FRONTEND_SSE_STATE_MODEL.md
docs/FRONTEND_AGENT_TIMELINE.md
docs/FRONTEND_SCREEN_SPEC.md
docs/FRONTEND_APPROVAL_FLOW.md

shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

before implementation.

Also read all other relevant architecture docs in:

```text
docs/
```

---

# 365. NO BACKEND TOUCHING DURING APPROVAL IMPLEMENTATION

If something fails:

```text
frontend mapping issue
→ fix frontend

event contract misunderstood
→ fix frontend

approval component bug
→ fix frontend

stale state bug
→ fix frontend

SSE reconnect bug
→ fix frontend

API client bug
→ fix frontend
```

Do not modify backend.

---

# 366. IF BACKEND CONTRACT IS MISSING DATA

Do:

```text
show "Not available"
```

or:

```text
hide field
```

and document the limitation.

Do not patch backend.

---

# 367. FINAL APPROVAL ARCHITECTURE

Canonical implementation:

```text
                 BACKEND
                    │
          approval.requested
                    │
                    ▼
               SSE CLIENT
                    │
                    ▼
             EVENT ROUTER
                    │
             ┌──────┴──────┐
             ▼             ▼
       APPROVAL STORE   RUN STORE
             │             │
             └──────┬──────┘
                    ▼
             REVIEW SURFACE
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
     REJECT                   APPROVE
        │                       │
        └───────────┬───────────┘
                    ▼
             TYPED API CLIENT
                    │
                    ▼
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
                    │
                    ▼
                 BACKEND
                    │
              ┌─────┴─────┐
              ▼           ▼
          APPROVED      REJECTED
              │           │
              ▼           ▼
         RUN RESUMES   RUN TERMINAL
              │
              ▼
           SSE / REST
              │
              ▼
         UI RECONCILES
```

---

# 368. FINAL APPROVAL UX PRINCIPLE

Approval is the point where the application clearly transitions from:

```text
AUTONOMOUS EXECUTION
```

to:

```text
HUMAN DECISION
```

The frontend should make that state unmistakable.

---

# 369. FINAL APPROVAL IMPLEMENTATION REQUIREMENT

Build the approval system completely.

It must:

```text
read all docs
↓
read OpenAPI
↓
read event contracts
↓
wire approval route
↓
wire approval events
↓
build approval state
↓
build evidence review
↓
build artifact review
↓
build approval UI
↓
build approve/reject action
↓
handle errors
↓
handle stale approvals
↓
handle reconnect
↓
handle reload
↓
handle terminal states
↓
handle multiple runs
↓
test real backend integration
```

---

# 370. FINAL ABSOLUTE RULE

**DO NOT TOUCH THE BACKEND.**

Do not:
- change backend approval routes
- change backend state machine
- change backend policy
- change backend SSE events
- change backend schemas
- change backend persistence
- add backend shortcuts
- add a send API
- bypass approval
- modify the execution engine

The frontend must wire to the backend that already exists.

---

# 371. FINAL DEFINITION OF DONE

Approval is complete when:

```text
[ ] approval.requested renders
[ ] run.waiting_approval renders
[ ] approval card works
[ ] action/risk/evidence render
[ ] artifacts render
[ ] verification renders
[ ] desktop evidence renders
[ ] timeline renders
[ ] graph renders
[ ] agent state renders
[ ] approve POST works
[ ] reject POST works
[ ] buttons cannot double-submit
[ ] backend confirmation drives state
[ ] stale approval handled
[ ] SSE reconnect handled
[ ] Electron reload handled
[ ] multiple runs isolated
[ ] terminal reconciliation works
[ ] no fake send state
[ ] no fake approval state
[ ] no backend modification
[ ] real local backend approval integration passes
```

---

# 372. FINAL GOLDEN STATE

The ideal final SyncNode desktop approval scene:

```text
SYNCNODE

MONTHLY OPERATIONS PACK

● WAITING FOR APPROVAL

LEFT
────────────────────────
TASK

✓ Word
✓ Excel
✓ PowerPoint
✓ Email Draft
🔒 Approval

CENTER
────────────────────────
LIVE DESKTOP

Email Draft

To:
demo@example.com

Attachments:
Word
Excel
PowerPoint

BOTTOM
────────────────────────
WORKFLOW

WORD ✓
EXCEL ✓
PPT ✓
EMAIL ✓
APPROVAL 🔒

TIMELINE

✓ Word created
✓ Excel verified
✓ PowerPoint verified
✓ Email draft prepared
✓ 3 attachments verified
🔒 Approval requested

RIGHT
────────────────────────
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

Verification
✓ PASS

Nothing has been sent.

[ Reject ]       [ Approve ]

BOTTOM STATUS
────────────────────────
🔒 WAITING FOR APPROVAL
● LOCAL
● BACKEND CONNECTED
```

This is the final human-control moment before the workflow can continue.

---

# 373. FINAL IMPLEMENTING-EDITOR INSTRUCTION

Read every relevant document in `docs/` and all shared frontend contract files.

Then implement this entire approval architecture using only the frontend.

Wire:

```text
REST
+
SSE
+
approval state
+
run state
+
agent state
+
timeline
+
workflow graph
+
desktop evidence
+
verification
+
artifacts
+
audit
```

into one coherent approval experience.

Use:

```text
POST /api/v1/runs/{run_id}/approvals/{approval_id}/decide
```

for user decisions.

Use:

```text
GET /api/v1/runs/{run_id}/...
```

for authoritative evidence.

Use:

```text
GET /api/v1/runs/{run_id}/events
```

for live state.

Never approve locally.
Never reject locally.
Never send locally.
Never execute locally.
Never bypass backend policy.

The backend remains the authority.

The Electron application is the review and decision interface.

---

# 374. FINAL SOURCE-OF-TRUTH STATEMENT

For this frontend implementation:

```text
BACKEND
= AUTHORITY

REST
= SNAPSHOT

SSE
= LIVE EVENTS

FRONTEND STORE
= SYNCHRONIZED VIEW

APPROVAL UI
= HUMAN DECISION SURFACE

ELECTRON
= VISUAL CLIENT
```

The user should always know:

```text
The workflow is paused.
The system is waiting.
Here is what is ready.
Here is the evidence.
Here is what the action means.
You decide.
```

That is the complete SyncNode approval architecture.

---

# 375. FINAL NON-NEGOTIABLE CONSTRAINT

**DO NOT MODIFY BACKEND CODE OR CONTRACTS.**

Build the complete approval experience entirely on the frontend and connect it to the existing SyncNode backend exactly as documented.
