# FRONTEND_ARTIFACT_EVIDENCE.md

# SyncNode — Frontend Artifact Evidence, Provenance & Verification UX

## 0. Document Purpose

This document is the end-to-end frontend implementation specification for **artifact evidence** inside the SyncNode Electron + React workbench.

The frontend must make every generated or discovered artifact understandable, trustworthy, traceable, reviewable, and visibly tied to the run that produced it.

This document is **frontend-only**.

> **NON-NEGOTIABLE:** Do not modify backend modules, backend contracts, execution logic, database schemas, model logic, tool implementations, verification logic, or API behavior while implementing this document.

The frontend consumes the existing REST + SSE contract and renders the evidence already exposed by the backend.

---

# 1. Product Intent

SyncNode is a sovereign, local, agentic AI workbench. Artifact evidence is therefore not a decorative file list. It is part of the trust model.

For every artifact, the user should be able to answer:

- What was created or discovered?
- Which run produced it?
- Which step or agent produced it?
- What operation created it?
- Where is it located locally?
- What type of artifact is it?
- When was it created or observed?
- Was it verified?
- What evidence supports the verification?
- Was it attached to another action, such as an email draft?
- Is it still available?
- Can I preview it safely?
- Can I open it through the operating system?
- What happened to it across the execution timeline?

The UI should answer those questions without forcing the user to inspect raw logs.

---

# 2. Core Principle

The artifact UI must preserve a strict chain:

```text
Run
 ↓
Agent / Step
 ↓
Tool Invocation
 ↓
Observation
 ↓
Artifact
 ↓
Verification
 ↓
Approval / External Effect (when applicable)
 ↓
Audit Evidence
```

The frontend must never invent a relationship that is not represented by backend data.

If the backend does not provide a relationship, show the field as unavailable rather than fabricating one.

---

# 3. Scope

This specification covers:

- Run artifact inventory
- Artifact cards
- Artifact detail panel
- Artifact evidence drawer
- Provenance visualization
- Verification evidence
- Artifact previews
- Document / spreadsheet / presentation evidence
- Image and PDF evidence
- Text/code evidence where available
- Artifact hashes and identity
- Artifact lifecycle states
- Run-scoped filenames
- Attachment evidence
- Artifact-to-step linking
- Artifact-to-agent linking
- Timeline integration
- Approval evidence integration
- Evidence filtering and search
- Download/open/reveal actions
- Missing/corrupt/unavailable artifact states
- Reconnect/reload behavior
- Multi-run separation
- Accessibility
- Electron security behavior
- Frontend automated testing
- Visual QA

It does **not** include:

- Backend artifact generation
- Backend artifact storage redesign
- New backend endpoints
- Database migrations
- Backend hash algorithms
- New verification engines
- New file execution tools
- New model behavior
- Backend event changes
- Backend security policy changes

---

# 4. Existing Backend Contract Used by the Frontend

The frontend is a thin client over the documented REST + SSE API.

Relevant route:

```text
GET /api/v1/runs/{run_id}/artifacts
```

The frontend should also consume related run resources where needed:

```text
GET /api/v1/runs/{run_id}
GET /api/v1/runs/{run_id}/steps
GET /api/v1/runs/{run_id}/tools
GET /api/v1/runs/{run_id}/observations
GET /api/v1/runs/{run_id}/verifications
GET /api/v1/runs/{run_id}/audit
GET /api/v1/runs/{run_id}/context
GET /api/v1/runs/{run_id}/events
```

The frontend must use the existing OpenAPI/entity/event definitions as the runtime source of truth:

```text
shared/openapi/openapi.json
shared/events/events.json
shared/schemas/entities.json
```

Do not create a second incompatible artifact schema inside the UI.

A frontend-normalized view-model is allowed, but it must be a lossless presentation mapping from the backend contract.

---

# 5. Artifact Evidence Model

Conceptually, the frontend should normalize every artifact into the following view model.

```ts
export type ArtifactViewModel = {
  id: string;
  runId: string;

  name?: string;
  path?: string;
  mimeType?: string;
  extension?: string;
  sizeBytes?: number;
  createdAt?: string;
  updatedAt?: string;

  sha256?: string;

  status:
    | "created"
    | "verified"
    | "attached"
    | "missing"
    | "unavailable"
    | "failed"
    | "unknown";

  artifactType:
    | "document"
    | "spreadsheet"
    | "presentation"
    | "pdf"
    | "image"
    | "text"
    | "code"
    | "archive"
    | "other"
    | "unknown";

  sourceStepId?: string;
  sourceAgentId?: string;
  sourceToolKey?: string;

  verificationIds: string[];
  observationIds: string[];
  auditEventIds: string[];

  attachmentRefs: Array<{
    actionId?: string;
    target?: string;
    status?: string;
  }>;

  evidenceSummary?: string;

  preview:
    | { kind: "text"; content?: string }
    | { kind: "image"; url?: string }
    | { kind: "pdf"; url?: string; pageCount?: number }
    | { kind: "office"; available: boolean }
    | { kind: "unsupported" };
};
```

This type is a frontend view model, not a backend contract replacement.

Use the actual backend field names and values when implementing the real adapter.

Do not assume fields exist simply because this conceptual shape is convenient.

---

# 6. Artifact Evidence Is Different from a File Browser

The artifact area must not feel like a generic Windows Explorer clone.

The hierarchy should communicate:

```text
Artifact
 → Provenance
 → Verification
 → Evidence
 → Related execution
 → Available actions
```

A file name alone is insufficient.

Bad:

```text
SyncNode_Word_c0574206.docx
SyncNode_Excel_c0574206.xlsx
SyncNode_Presentation_c0574206.pptx
```

Good:

```text
SyncNode_Word_c0574206.docx
Document • Verified
Created by Writer / document.create_docx
Produced during Step 4
SHA-256: 601adaa1cfcb…
Verified after save
```

The UI should feel like a forensic evidence surface inside an AI IDE, while remaining clean and readable.

---

# 7. Where Artifact Evidence Appears

Artifact evidence must be available in multiple synchronized surfaces.

## 7.1 Active Run — Artifact Rail

Inside the active run screen, show a compact artifact rail in the lower/right portion of the IDE.

Each card should include:

- File icon/type icon
- Filename
- Artifact type
- Status badge
- Verification indicator
- Short provenance line
- File size when known
- Timestamp when known
- Quick preview button
- Evidence button
- Open/reveal action where supported

The rail must update live through SSE.

---

## 7.2 Dedicated Artifact Evidence View

Provide a larger evidence-focused panel/page accessible from:

- Active run
- Timeline
- Artifact card
- Approval review
- Final run summary

Recommended layout:

```text
┌──────────────────────────────────────────────────────────────────┐
│ Artifact Evidence                                               │
│ SyncNode_Word_c0574206.docx                  VERIFIED            │
├───────────────────────────────┬──────────────────────────────────┤
│ Preview                       │ Evidence                         │
│                               │ Type: Document                   │
│  [document preview]           │ Run: c057...                     │
│                               │ Agent: writer                    │
│                               │ Step: step-4                     │
│                               │ Tool: document.create_docx       │
│                               │ Size: ...                        │
│                               │ SHA-256: ...                     │
│                               │ Created: ...                     │
│                               │                                  │
│                               │ Verification                     │
│                               │ ✓ file exists                    │
│                               │ ✓ expected identity              │
│                               │ ✓ save completed                 │
│                               │                                  │
│                               │ [Open] [Reveal]                  │
└───────────────────────────────┴──────────────────────────────────┘
```

---

## 7.3 Timeline Artifact Evidence

When the user selects an artifact-related timeline event, the timeline should focus the artifact panel.

Example:

```text
14:32:11  artifact.created
           SyncNode_Word_c0574206.docx
           Writer agent
           document.create_docx
           [View evidence]
```

Clicking **View evidence** opens the artifact detail state without losing the active run context.

---

## 7.4 Approval Evidence

When an approval concerns an external action involving artifacts, such as attaching artifacts to an email draft or sending an email, the approval UI must surface the exact artifact set involved.

Example:

```text
Approval required

Email draft
To: operations@example.local

Attachments
✓ SyncNode_Word_c0574206.docx
✓ SyncNode_Excel_c0574206.xlsx
✓ SyncNode_Presentation_c0574206.pptx

[Inspect attachments]     [Reject] [Approve]
```

No approval card should say “3 files attached” without providing a way to inspect which three files they are.

---

# 8. Artifact Lifecycle UX

The UI should represent artifact lifecycle clearly.

Suggested conceptual state flow:

```text
DISCOVERED
   ↓
CREATED
   ↓
OBSERVED
   ↓
VERIFIED
   ↓
ATTACHED / REFERENCED
   ↓
EXTERNAL EFFECT (if any)
```

A failed path should be visually separate:

```text
CREATION FAILED
       ↓
   NO TRUSTED ARTIFACT
```

Do not display a generated-file card as “successful” merely because a tool invocation finished.

The frontend must use the backend's actual artifact and verification state.

---

# 9. Status Badges

Use a consistent compact status vocabulary.

### Verified

Displayed when backend verification supports the state.

```text
✓ VERIFIED
```

### Created / Unverified

Artifact exists but no successful verification evidence is currently known.

```text
○ CREATED
```

### Pending

Artifact generation or verification remains in progress.

```text
◌ VERIFYING
```

### Missing

The backend identifies that the expected artifact cannot currently be found.

```text
! MISSING
```

### Failed

Artifact creation or relevant processing failed.

```text
× FAILED
```

### Unavailable

Artifact metadata is known but preview/open access is currently unavailable.

```text
— UNAVAILABLE
```

### Unknown

Use only where the backend itself does not expose enough evidence to classify the state.

Do not reinterpret unknown as success.

---

# 10. Verification Evidence

Verification is a first-class part of the artifact experience.

The UI should show each verification separately.

Example:

```text
Verification

✓ Artifact exists
  Expected: SyncNode_Word_c0574206.docx
  Observed: SyncNode_Word_c0574206.docx

✓ Artifact identity matches
  Run-scoped artifact reference matched

✓ Save completed
  File remained available after save

✓ Content check
  Expected content was observed
```

The exact verification labels must come from backend verification records where available.

The frontend should not invent verification success criteria.

---

# 11. Verification Timeline

For each verification, show:

```text
Verification event
────────────────────────────
Status       PASSED
Time         14:32:16
Check        artifact identity
Target       SyncNode_Word_c0574206.docx
Evidence     expected artifact path matched observed artifact
Source       verifier
```

When verification fails:

```text
Verification event
────────────────────────────
Status       FAILED
Time         14:32:20
Check        artifact identity
Target       expected file
Evidence     observed target did not match expected artifact identity
Recovery     retry requested
```

A failed verification should remain visible even when recovery later succeeds. The history must not be erased.

---

# 12. Evidence Provenance Graph

Artifact evidence should support a compact provenance graph.

```text
Agent
  │
  ▼
Step
  │
  ▼
Tool
  │
  ▼
Artifact
  │
  ├──── Observation
  │
  ├──── Verification
  │
  ├──── Attachment
  │
  └──── Audit Events
```

In the UI, this can be represented as a horizontal or vertical chain.

Example:

```text
Writer Agent
    ↓
Step 4 — Generate Word document
    ↓
document.create_docx
    ↓
SyncNode_Word_c0574206.docx
    ↓
3 verification checks passed
```

Each node should be clickable.

Clicking a node should focus the corresponding existing frontend state rather than opening an unrelated page.

---

# 13. Agent Attribution

When backend data exposes the owning agent, show it prominently.

Example:

```text
Produced by
Writer Agent

Role
Document generation

Tool
 document.create_docx
```

For artifacts created by a generic execution stage rather than a separately spawned agent, render the actual source information available from backend data.

Never manufacture a named agent simply to make the UI look complete.

---

# 14. Step Attribution

Show the producing step where possible.

Example:

```text
Source step
Step 4 — Generate Word document

Status
Completed
```

Provide a “Jump to step” action.

The action should select the step in the workflow/timeline UI.

The artifact detail view should remain open or become an inline side panel so that context is not lost.

---

# 15. Tool Attribution

Where supported, show the exact tool key.

Example:

```text
Tool
`document.create_docx`
```

Use monospace typography for tool identifiers.

Provide a “View tool event” action that focuses the matching tool invocation in the timeline.

This is especially important when multiple tools can produce files.

---

# 16. Artifact Identity

Artifact identity is critical in multi-run systems.

The frontend must keep the following concepts separate:

```text
artifactId
runId
path
name
hash
```

Do not use filename alone as the internal identity.

A filename can be duplicated across runs.

A run-scoped artifact must remain associated with its owning run even when multiple runs use similar filenames.

Example:

```text
Run A
SyncNode_Report.docx

Run B
SyncNode_Report.docx
```

These are different artifacts unless the backend says otherwise.

---

# 17. Run-Scoped Filenames

When run-scoped filenames exist, display the actual backend-provided filename.

Do not transform it to a different name merely for aesthetics.

Example:

```text
SyncNode_Word_c0574206.docx
SyncNode_Excel_c0574206.xlsx
SyncNode_Presentation_c0574206.pptx
```

For long names, visually truncate only the rendered label while preserving the complete name in a tooltip and detail panel.

---

# 18. Cryptographic Hash Evidence

When a hash is available, expose it.

Example:

```text
SHA-256
601adaa1cfcb...

[Copy full hash]
```

The compact card can show a shortened value.

The detailed evidence panel should allow copying the full value.

Never alter the hash string.

Do not calculate a frontend hash and present it as the authoritative backend verification hash unless the contract explicitly defines that behavior.

---

# 19. Artifact Metadata

Display metadata only when supplied by the backend or derived safely from the artifact itself through an explicitly supported frontend capability.

Potential metadata:

```text
Name
Type
MIME type
Extension
Size
Created time
Modified time
Path
SHA-256
Run ID
Step ID
Agent
Tool
Verification state
Attachment state
```

Missing fields should be gracefully omitted or shown as `Not available` where useful.

---

# 20. Preview System

Artifacts should have a preview experience appropriate to their type.

The preview is evidence, not an editor.

The frontend should not silently mutate artifact contents.

---

# 21. DOCX Preview

For Word documents, provide a document-style preview when content is available through the existing frontend/backend contract.

Recommended structure:

```text
┌────────────────────────────────────┐
│ DOCX Preview                       │
├────────────────────────────────────┤
│                                    │
│       Document title               │
│                                    │
│  paragraph text...                 │
│                                    │
│  heading                           │
│                                    │
│  paragraph text...                 │
│                                    │
└────────────────────────────────────┘
```

Actions:

```text
Preview
Evidence
Open
Reveal
```

Do not create an editable fake-Word surface.

If no preview content exists through supported data, display:

```text
Preview unavailable
The artifact exists, but no renderable preview is available from the current evidence contract.
```

---

# 22. XLSX Preview

For spreadsheets, use a spreadsheet-oriented preview.

Show:

- Workbook name
- Relevant sheet names
- Selected sheet
- Tabular cells where supported
- Basic dimensions when known
- Verification information

Avoid implementing a full spreadsheet editor.

The preview must remain read-only.

For large sheets, virtualize rows/columns rather than rendering the entire workbook.

---

# 23. PPTX Preview

For presentations, show slide thumbnails or a slide-by-slide preview when available.

Recommended layout:

```text
┌────────────┬───────────────────────────────┐
│ Slides     │ Slide Preview                 │
│            │                               │
│ [01]       │      Slide 1                 │
│ [02]       │                               │
│ [03]       │                               │
└────────────┴───────────────────────────────┘
```

Clicking a slide should update the preview and evidence context.

---

# 24. PDF Preview

Provide paginated preview when supported.

Use a stable viewer container with:

- Page navigation
- Zoom
- Fit-to-width
- Page count when known
- Evidence panel remaining accessible

Do not silently upload a local PDF to a cloud viewer.

The product requirement is sovereign/local operation.

---

# 25. Image Preview

Show the image itself with:

- Fit to panel
- Zoom
- Actual dimensions when known
- Filename
- File type
- Verification state

For screenshots used as observations, distinguish the item visually from a generated artifact so users do not confuse observation imagery with output files.

---

# 26. Text / Code Preview

For text or source-code artifacts:

- Use a monospaced viewer
- Support line wrapping toggle
- Preserve whitespace
- Make copying easy
- Keep it read-only
- Show language/type when known

Never execute displayed code automatically.

---

# 27. Unsupported Artifact Preview

For unsupported formats, provide a deliberate fallback.

```text
Preview unavailable

This artifact type is not previewable in the current workbench.

Filename
example.zip

Type
Archive

[Reveal in folder]
[Open with system application]
```

The user should still be able to inspect metadata and provenance.

Unsupported preview must not imply unsupported artifact validity.

---

# 28. Safe Open / Reveal Actions

The frontend may expose local file actions already supported by the Electron application architecture.

Recommended actions:

```text
Open
Reveal in Explorer
Copy path
Copy hash
```

These actions should use secure Electron IPC/preload capabilities.

Do not expose arbitrary shell execution to renderer code.

Do not pass unchecked arbitrary commands from model text to Electron.

---

# 29. Attachment Evidence

Artifact attachments are particularly important for external side-effect review.

For each artifact, show whether it has been attached or referenced.

Example:

```text
Attachment usage

✓ Included in email draft
  draft action: attach artifacts

Target
  local mail sink / draft
```

The UI must distinguish:

```text
Artifact exists
```

from:

```text
Artifact attached to draft
```

and from:

```text
Email sent
```

These are different events and must never collapse into one status.

---

# 30. Send vs Draft Evidence

The artifact panel must accurately reflect the execution boundary.

For example:

```text
Artifacts created        ✓
Artifacts verified       ✓
Artifacts attached       ✓
Email draft created      ✓
Human approval           WAITING
Email sent               NOT EXECUTED
```

Never display “delivered” or “sent” merely because artifacts were attached to a draft.

The exact external action status must come from backend events/state.

---

# 31. Approval Review — Artifact Inspection

When approval is required, the approval surface should allow the reviewer to inspect each affected artifact.

Recommended layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ APPROVAL REQUIRED                                           │
│ Review outgoing action and attached evidence                │
├──────────────────────────────────────────────────────────────┤
│ ARTIFACTS                                                   │
│                                                              │
│ ✓ Word document        Verified                             │
│ ✓ Excel workbook       Verified                             │
│ ✓ PowerPoint           Verified                             │
│                                                              │
│ [Inspect evidence]                                         │
│                                                              │
│ OUTGOING EFFECT                                             │
│ Email draft / send                                         │
│                                                              │
│ [Reject]                                  [Approve]          │
└──────────────────────────────────────────────────────────────┘
```

The review surface should support opening evidence before making the approval decision.

---

# 32. Artifact Evidence in Run Summary

At completion, the run summary should include a compact artifact section.

Example:

```text
RUN COMPLETED

Artifacts

3 generated
3 verified
3 attached to draft
0 sent automatically

[View all artifacts]
```

A completed run with missing artifacts should not visually claim a clean artifact result.

Use the actual run terminal state and artifact data.

---

# 33. Failure States

Artifact evidence must make failure obvious and actionable.

## Missing artifact

```text
Artifact missing

Expected
SyncNode_Word_c0574206.docx

The execution trace references this artifact, but the artifact is not currently available.

[View recovery events]
[View audit]
```

## Verification failed

```text
Verification failed

The expected artifact was not confirmed by the verifier.

[View failed check]
[View recovery]
```

## Preview failed

```text
Artifact exists
Preview unavailable
```

Do not conflate preview failure with artifact creation failure.

---

# 34. Recovery Evidence

When an artifact failure triggers recovery, the evidence view should expose:

```text
Original attempt
      ↓
Verification failed
      ↓
Recovery started
      ↓
Retry / replan
      ↓
Artifact recreated
      ↓
Verification passed
```

The UI must preserve the original failure as historical evidence.

Do not replace the failed attempt with the successful one as though the failure never happened.

---

# 35. Audit Evidence

Artifact evidence should expose related audit events.

Example:

```text
Audit trail

14:32:11 artifact.created
14:32:13 observation.captured
14:32:16 verification.passed
14:32:18 artifact.attached
14:32:22 approval.requested
```

Use the actual event names provided by the backend event contract.

Do not generate synthetic audit entries merely for visual completeness.

---

# 36. SSE Integration

The artifact surface must be live.

The frontend should consume the existing run SSE stream.

Relevant event categories include artifact-adjacent events such as:

```text
artifact-related creation/update events, where exposed
observation.captured
verification.passed
verification.failed
recovery.started
recovery.attempted
recovery.completed
approval.requested
approval.decided
run.completed
run.failed
run.cancelled
```

Use the actual event names from `shared/events/events.json` as authoritative.

Do not invent new SSE event names.

---

# 37. Event-to-State Rules

When an event arrives:

1. Parse and validate the event envelope.
2. Resolve the owning run.
3. Resolve the artifact identity when the event contains one.
4. Merge the event into normalized frontend state.
5. Update timeline state.
6. Preserve prior events.
7. Reconcile with REST snapshots when needed.

Never assume event ordering is perfect.

An event can arrive before the artifact snapshot has loaded.

The reducer/store should therefore support temporary references and later reconciliation.

---

# 38. Initial REST Snapshot + SSE

Recommended sequence:

```text
Open run
  ↓
GET /runs/{run_id}
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/steps
GET /runs/{run_id}/verifications
GET /runs/{run_id}/observations
  ↓
Open /runs/{run_id}/events
  ↓
Apply live events
  ↓
Reconcile on reconnect / terminal state
```

If the SSE connection starts first and data races occur, the frontend must deduplicate and reconcile rather than rendering duplicates.

---

# 39. Reconnection Behavior

When SSE disconnects:

```text
LIVE
 ↓
RECONNECTING
 ↓
REST SNAPSHOT REFRESH
 ↓
SSE RECONNECTED
 ↓
STATE RECONCILED
```

The artifact panel should remain visible.

Do not clear existing artifacts because the stream temporarily disconnected.

A small banner is appropriate:

```text
Reconnecting to live run updates…
```

Once synchronized:

```text
Live updates restored
```

---

# 40. Reload Behavior

On browser/Electron renderer reload:

- Reconstruct the active run from URL/router state.
- Fetch the current artifact snapshot.
- Fetch associated verification/observation data as required.
- Reconnect the SSE stream.
- Reconcile events/state.
- Restore selected artifact where safe.

The UI must not depend on in-memory state surviving a renderer reload.

---

# 41. Multi-Run Isolation

Artifacts from separate runs must never visually merge.

State keys should be run-scoped.

Conceptual structure:

```ts
artifactsByRun[runId]
```

Do not maintain one flat global artifact collection and assume filename uniqueness.

The user must be able to switch runs without seeing stale artifacts from another run.

---

# 42. Artifact Selection State

Use a stable selected artifact ID where available.

Conceptual URL/state pattern:

```text
/run/{runId}?artifact={artifactId}
```

or an equivalent route/state supported by the application architecture.

The exact route may differ, but selection must be deep-linkable within the current run.

---

# 43. Filtering

The artifact evidence surface should support lightweight filters.

Recommended filters:

```text
All
Verified
Unverified
Failed
Missing
Attached
```

Artifact type filters:

```text
Documents
Spreadsheets
Presentations
PDFs
Images
Text
Other
```

Do not overbuild the filter system during Phase 1.

---

# 44. Search

A small artifact search field should match:

- Filename
- Extension
- Artifact ID
- Agent name where available
- Tool key where available
- Step title where available

Search must operate locally on already-fetched frontend state unless the documented backend knowledge/search route is explicitly appropriate.

Do not send arbitrary artifact search requests to undocumented backend endpoints.

---

# 45. Evidence Density

This is an AI IDE, not a consumer file browser.

Prefer information-rich compact rows.

Example:

```text
┌─────────────────────────────────────────────────────────────┐
│ DOCX  SyncNode_Word_c0574206.docx                ✓ VERIFIED │
│       Writer · Step 4 · document.create_docx               │
│       24 KB · SHA-256 601adaa1…                            │
│       Created 14:32:11                                      │
└─────────────────────────────────────────────────────────────┘
```

Hovering or opening details exposes the complete evidence.

---

# 46. Visual Language

Use the existing SyncNode visual language:

- Black-first interface
- Monochrome palette
- High information density
- Thin borders
- Subtle separators
- Compact typography
- Minimal visual noise
- Strong hierarchy
- Small status accents
- Smooth motion
- Electron/IDE feel

Artifact verification should feel important without looking like a marketing dashboard.

Avoid oversized green “success” banners.

A small precise `VERIFIED` state is preferable to a giant celebration panel.

---

# 47. Motion / Animation

Use restrained motion.

Artifact creation:

```text
card enters → metadata fades in → verification indicator resolves
```

Verification:

```text
pending ring → resolved status
```

New artifact:

```text
subtle insert highlight
```

Do not repeatedly animate an unchanged artifact.

Do not animate the entire artifact list whenever any single artifact updates.

Respect reduced-motion preferences.

---

# 48. Evidence Drawer

Recommended interaction:

```text
Artifact card
   ↓ click
Artifact evidence drawer
```

The drawer contains:

```text
Header
Preview
Metadata
Provenance
Verification
Attachment usage
Audit trail
Actions
```

The drawer should be wide enough for document previews and evidence metadata without covering the whole IDE unnecessarily.

On smaller widths, it can become a full-height modal/sheet.

---

# 49. Provenance Section UI

Suggested component:

```text
ArtifactProvenance
```

Layout:

```text
PRODUCED BY
Writer Agent

STEP
Generate Word document

TOOL
document.create_docx

RUN
c0574206-68ba-455b-bb67-b885dcc6fe36
```

Each row can include a navigation/focus action.

---

# 50. Verification Section UI

Suggested component:

```text
ArtifactVerificationPanel
```

Each verification row:

```text
[status]  Check name
          Evidence summary
          timestamp
          [View event]
```

Clicking a row should focus the corresponding event/verification context.

---

# 51. Evidence Strength

The UI should visually communicate that evidence has levels.

Conceptual hierarchy:

```text
Artifact metadata
      ↓
Observed artifact
      ↓
Verified artifact
      ↓
Verified + provenance
      ↓
Verified + provenance + external-action evidence
```

Do not turn this into an arbitrary score.

Use factual state indicators instead.

---

# 52. No Fake Evidence

This is one of the highest-priority rules.

Never fabricate:

- verification checks
- hashes
- timestamps
- agent ownership
- file paths
- successful attachment state
- preview availability
- send state
- observations
- audit events
- tool invocation details

If something is missing:

```text
Not available from current run evidence
```

is preferable to an invented placeholder that looks real.

---

# 53. Handling Partial Evidence

A run may expose an artifact but not all associated evidence.

For example:

```text
Artifact
✓ exists

Verification
No verification record available

Provenance
Step known
Agent unknown
```

The UI should preserve the partial evidence honestly.

Do not downgrade a known artifact to failed solely because optional metadata is absent.

Do not upgrade it to verified without an actual verification result.

---

# 54. Artifact vs Observation

An observation can contain a screenshot or visual state without being an output artifact.

The UI must visually distinguish them.

Artifact:

```text
FILE ARTIFACT
SyncNode_Word_c0574206.docx
```

Observation:

```text
SCREEN OBSERVATION
Word window after save
```

A screenshot used as verification evidence should appear inside the verification/evidence context, not as a generated file merely because it is an image.

---

# 55. Content Evidence

When the backend provides content-related verification evidence, show it near the artifact.

Example:

```text
Content verification

Expected content located
Observed in generated artifact

✓ PASS
```

For longer evidence, use expandable text.

Never render untrusted artifact content as executable HTML.

Treat text as text.

---

# 56. Path Handling

Paths are local-system-sensitive information.

The renderer should not receive unrestricted OS access.

Display paths safely:

```text
C:\SyncNode\runs\c057...\artifacts\SyncNode_Word_c0574206.docx
```

Long paths should be truncatable with a copy action.

Do not normalize a path by hand in a way that changes its meaning.

---

# 57. Artifact Action Menu

Recommended action menu:

```text
Preview
Inspect evidence
Copy filename
Copy path
Copy hash
Reveal in Explorer
Open with system app
```

Only show an action when the current environment and backend/frontend capability support it.

Never show a disabled-looking fake action that cannot work.

---

# 58. Open With System Application

For supported local files, use a secure Electron main-process/preload capability.

Renderer:

```ts
window.syncnode.files.open(path)
```

Main process validates and performs the allowed operation.

Do not allow arbitrary renderer shell APIs.

The frontend does not need a generic command executor for this feature.

---

# 59. Reveal in Explorer

Provide a dedicated secure capability such as:

```ts
window.syncnode.files.reveal(path)
```

The action should safely reveal the file in the system file manager.

Errors should be displayed as an artifact action failure, not as a run execution failure.

---

# 60. Copy Actions

Useful copy actions:

```text
Copy filename
Copy full path
Copy artifact ID
Copy run ID
Copy SHA-256
```

After copy:

```text
Copied
```

No disruptive toast stack is necessary.

---

# 61. Accessibility

Artifacts must be keyboard accessible.

Requirements:

- Cards are focusable.
- Enter/Space opens evidence.
- Action menus are keyboard navigable.
- Status is not conveyed by color alone.
- Verification icon has text/ARIA label.
- Preview has meaningful accessible labels.
- Copy/open/reveal actions have clear names.
- Focus remains predictable when drawer opens/closes.

Example accessible label:

```text
SyncNode_Word_c0574206.docx, verified document artifact, produced by Writer Agent
```

---

# 62. Error Presentation

Do not show raw stack traces by default.

Use a concise evidence-level message with a diagnostic disclosure.

Example:

```text
Could not preview artifact

The artifact metadata is available, but the preview could not be loaded.

[Retry]
[View diagnostic details]
```

Diagnostics may include request/event IDs when exposed by the existing API contract.

---

# 63. Loading States

Artifact loading should use skeletons shaped like the final content.

Example:

```text
████████████████████
██████████
██████████████
```

Avoid blank screens.

For large artifact sets, load progressively.

---

# 64. Empty States

No artifacts yet:

```text
No artifacts yet

Generated files and verified outputs will appear here as the run progresses.
```

No verified artifacts:

```text
No verified artifacts

Artifacts may exist, but no successful verification is currently recorded.
```

No artifacts after a failed run:

```text
No artifacts produced

See the execution timeline for failed steps and recovery attempts.
```

Do not make the empty state sound successful when the run failed.

---

# 65. Artifact Counts

Useful summary numbers:

```text
Artifacts        3
Verified         3
Failed           0
Attached         3
```

These numbers must be derived from actual frontend state based on backend data.

Do not show “100% verified” without meaningful denominator logic.

---

# 66. Artifact Relationships

Where backend evidence supports relationships, show:

```text
Artifact
 ├── generated by → step
 ├── generated by → agent
 ├── created by → tool
 ├── checked by → verification
 ├── observed by → observation
 ├── attached to → action
 └── recorded by → audit event
```

The relationship browser can be simple in Phase 1.

The requirement is traceability, not a complex graph database visualizer.

---

# 67. Timeline Synchronization

Selecting an artifact should highlight related events in the timeline.

Example:

```text
Artifact selected
       ↓
Timeline filters/highlights:
       ↓
artifact creation
observation
verification
recovery
attachment
approval
```

Selecting a timeline event should similarly focus the artifact when an artifact reference is present.

This bidirectional navigation is essential.

---

# 68. Workflow Graph Synchronization

Selecting an artifact should optionally highlight the step/node that produced it.

Example:

```text
[Generate Word]  ← highlighted
       ↓
[Verify]
       ↓
[Attach]
       ↓
[Approval]
```

Do not rewrite graph semantics in the artifact UI.

Only focus existing graph state.

---

# 69. Agent Panel Synchronization

If an artifact belongs to an agent, selecting it may focus the relevant agent panel.

Example:

```text
Artifact
SyncNode_Excel_c0574206.xlsx

Produced by
Office Agent
```

Selecting `Office Agent` should focus the existing agent details view.

---

# 70. Context / RAG Relationship

An artifact can be the output of a workflow that used RAG context.

The artifact detail may expose a compact relationship when backend evidence connects them.

Example:

```text
Knowledge used
3 local knowledge results

[View run context]
```

This should link to existing context state.

Do not imply that RAG directly authored a file unless the backend says so.

---

# 71. Evidence for the Three-Artifact Golden Flow

The canonical three-artifact desktop flow currently demonstrates the intended UX pattern.

The frontend should be able to render a run containing:

```text
Word
SyncNode_Word_<run>.docx

Excel
SyncNode_Excel_<run>.xlsx

PowerPoint
SyncNode_Presentation_<run>.pptx
```

The UI should surface:

```text
3 artifacts created
3 artifacts verified
3 artifacts attached to the draft
Send not executed
Approval required
```

Use the actual run state and artifacts returned by the backend at runtime.

---

# 72. No False Completion Masking

The frontend must not infer artifact success from only:

```text
run.status === waiting_approval
```

or:

```text
agent.completed
```

or:

```text
tool.completed
```

Artifact success should be represented by artifact data + verification data.

This prevents the UI from displaying a trustworthy-looking artifact result when the underlying artifact is missing.

---

# 73. Evidence Priority Rules

When rendering artifact truth, use this order conceptually:

```text
1. Explicit artifact record
2. Explicit verification record
3. Explicit observation/audit relationship
4. Step/agent/tool references
5. Derived UI metadata
```

Never let a lower-confidence derived presentation field override an explicit backend fact.

---

# 74. State Architecture

Recommended frontend stores:

```text
runStore
artifactStore
verificationStore
observationStore
agentStore
stepStore
executionEventStore
uiStore
```

Artifact selectors should combine state rather than duplicate backend data.

Example conceptual selectors:

```ts
selectArtifactsForRun(runId)
selectArtifactById(runId, artifactId)
selectArtifactVerifications(runId, artifactId)
selectArtifactObservations(runId, artifactId)
selectArtifactTimelineEvents(runId, artifactId)
selectArtifactAttachments(runId, artifactId)
```

---

# 75. Normalization

Do not store large duplicated artifact objects in many components.

Prefer normalized state:

```ts
artifactsById
artifactIdsByRun
```

Related records can be indexed separately.

This prevents expensive rerenders when one verification event arrives.

---

# 76. Event Deduplication

The same event can potentially be observed through reconnect/reconciliation paths.

Deduplicate with the stable event identity available from the backend event envelope.

Do not deduplicate merely on event type + timestamp because that can collapse legitimate repeated events.

For artifacts, avoid inserting duplicate artifact records merely because the REST refresh returned the same artifact already known through SSE.

---

# 77. Artifact Ordering

Use deterministic ordering.

Recommended default:

```text
latest relevant update first
```

Within equal timestamps, preserve backend-provided ordering or stable ID ordering.

Do not shuffle cards on every state update.

---

# 78. Large Artifact Sets

The golden flow is small, but production runs may produce many artifacts.

Design for:

- Virtualized lists where needed
- Collapsible evidence sections
- Lazy preview loading
- Deferred rendering of expensive previews
- Search/filter state
- Avoiding duplicate file decoding

Do not load every PDF/image/office preview automatically.

---

# 79. Preview Security

Artifact content must be treated as untrusted data.

Do not use unsafe HTML injection for arbitrary document content.

In Electron:

- Keep `contextIsolation` enabled.
- Keep `nodeIntegration` disabled in the renderer.
- Expose minimal preload APIs.
- Do not provide arbitrary filesystem access to renderer code.
- Do not execute artifact code/content.

Any preview technology must be compatible with the app's local/offline trust boundary.

---

# 80. Offline / Sovereign Behavior

Artifact evidence should continue to function without cloud services.

The frontend must not rely on:

- Cloud preview services
- Cloud storage
- External upload endpoints
- Remote OCR providers
- Remote document conversion

Use the existing local backend/API contract and local Electron capabilities.

---

# 81. API Error Handling

When the artifact endpoint fails:

```text
Artifacts unavailable

The run is still accessible. Artifact evidence could not be loaded.

[Retry]
```

Do not mark all artifacts as failed merely because one HTTP request failed.

Preserve previously valid state until a newer authoritative snapshot says otherwise.

---

# 82. Partial Endpoint Failure

For example:

```text
GET artifacts   ✓
GET verification data   ✗
```

The UI should show:

```text
Artifact metadata available
Verification evidence temporarily unavailable
```

Do not discard the artifact records.

---

# 83. Terminal Run Reconciliation

When the run reaches:

```text
completed
failed
cancelled
```

perform the existing final reconciliation strategy:

```text
fetch terminal run snapshot
fetch final artifacts
fetch final verifications where necessary
reconcile current frontend state
```

The goal is to ensure the final UI does not depend solely on a last-minute SSE event.

---

# 84. Artifact Evidence and Cancellation

If the run is cancelled, preserve artifacts that were already successfully created and verified.

Example:

```text
Run cancelled

Artifacts already produced
✓ report.docx
✓ report.xlsx

Later steps not executed
```

Cancellation is not equivalent to artifact invalidity.

---

# 85. Artifact Evidence and Run Failure

If a run fails after creating valid artifacts:

```text
Run failed

Artifacts produced before failure
✓ report.docx
✓ report.xlsx

Failed stage
Email attachment
```

Do not hide valid earlier artifacts simply because the overall run failed.

---

# 86. Artifact Evidence and Approval Waiting

If the run is waiting for approval:

```text
Run waiting for approval

Artifacts
✓ 3 verified

Pending external action
Email send
```

The UI must clearly separate completed artifact work from the pending sensitive action.

---

# 87. Evidence Detail Tabs

Recommended detail tabs:

```text
Preview
Evidence
Activity
```

### Preview
Human-readable content.

### Evidence
Metadata, provenance, verification, attachment state.

### Activity
Timeline events related to the artifact.

This keeps the panel manageable while preserving depth.

---

# 88. Evidence Activity Filter

Inside the artifact detail activity tab, show only events relevant to the selected artifact when such relationships are available.

Example:

```text
Artifact activity

14:32:11 Created
14:32:12 Observation captured
14:32:16 Verification passed
14:32:19 Attached to draft
```

Provide:

```text
[Show all run events]
```

which returns to the full timeline.

---

# 89. Copyable Evidence Summary

Provide an optional copy button for a concise factual evidence summary.

Example output:

```text
Artifact: SyncNode_Word_c0574206.docx
Run: c0574206-68ba-455b-bb67-b885dcc6fe36
Agent: Writer Agent
Tool: document.create_docx
Status: Verified
SHA-256: 601adaa1cfcb...
```

The generated summary must use actual data.

---

# 90. UX for Missing Relationships

When artifact relationships are incomplete:

```text
Source step
Not available

Source agent
Writer Agent

Verification
2 checks passed
```

Do not create “Unknown step” as though it were a backend entity.

Use “Not available” for absent data.

---

# 91. Artifact Card Component Contract

Recommended component:

```tsx
<ArtifactCard
  artifact={artifact}
  onOpenEvidence={() => ...}
  onPreview={() => ...}
  onReveal={() => ...}
  onOpen={() => ...}
/>
```

The card should not fetch its own unrelated global data directly.

Data should come through selectors/hooks at the feature boundary.

---

# 92. Artifact Evidence Feature Components

Recommended component tree:

```text
ArtifactWorkspace
├── ArtifactToolbar
├── ArtifactSummary
├── ArtifactList
│   └── ArtifactCard
├── ArtifactEvidenceDrawer
│   ├── ArtifactHeader
│   ├── ArtifactPreview
│   ├── ArtifactMetadata
│   ├── ArtifactProvenance
│   ├── ArtifactVerificationPanel
│   ├── ArtifactAttachmentPanel
│   └── ArtifactActivity
└── ArtifactEmptyState
```

Implementation naming can differ, but responsibilities should remain separated.

---

# 93. Hooks

Suggested hooks:

```ts
useRunArtifacts(runId)
useArtifact(runId, artifactId)
useArtifactEvidence(runId, artifactId)
useArtifactVerification(runId, artifactId)
useArtifactActivity(runId, artifactId)
useArtifactActions()
```

Hooks must use the central API/state layer.

Do not have every card independently open REST/SSE connections.

---

# 94. Backend Boundary Rule

The renderer may call only documented frontend service abstractions.

Do not allow components to directly perform arbitrary:

```text
fetch("http://...")
```

for every feature.

Centralize API access:

```text
api/client
api/runs
api/artifacts
api/verifications
```

This makes error handling, environment configuration, and test mocking consistent.

---

# 95. Electron Boundary Rule

Local file actions should flow through:

```text
React renderer
   ↓
preload bridge
   ↓
Electron main process
   ↓
OS
```

Never:

```text
React renderer
   ↓
Node fs / child_process
```

---

# 96. Artifact Preview Architecture

Use a preview adapter pattern.

Conceptual API:

```ts
interface ArtifactPreviewAdapter {
  canPreview(artifact: ArtifactViewModel): boolean;
  loadPreview(artifact: ArtifactViewModel): Promise<PreviewData>;
}
```

Adapters can exist for:

```text
text
image
pdf
office
```

But they should only use supported application data paths.

---

# 97. Do Not Build a Fake Office Environment

The artifact preview UI is not a replacement for actual Microsoft Word, Excel, or PowerPoint.

For real application behavior, the user can use:

```text
Open with system application
```

The preview exists to provide evidence review quickly inside the workbench.

---

# 98. Evidence and Desktop Mirror

When a run used real desktop interaction, the artifact evidence should connect to desktop observations where available.

Example:

```text
Artifact
SyncNode_Word_c0574206.docx

Related observation
Word after save

[View desktop observation]
```

This creates a factual bridge between:

```text
desktop action
→ observed result
→ file artifact
→ verification
```

Do not claim causal relationships that are not exposed by backend evidence.

---

# 99. Evidence and Computer Control

For computer-generated artifacts, the frontend can show:

```text
Computer action
Launch Word

Observation
Document visible

Artifact
SyncNode_Word_c0574206.docx

Verification
File exists and identity confirmed
```

The frontend is displaying execution evidence, not re-executing the computer action.

---

# 100. Evidence and Recovery

If recovery occurs, the artifact panel should show which attempt ultimately produced the trusted artifact when that relationship is available.

Example:

```text
Attempts

Attempt 1 — verification failed
Attempt 2 — verification passed

Current artifact
SyncNode_Word_c0574206.docx
```

Do not hide earlier failures.

---

# 101. Artifact Provenance Compact View

For cards, keep provenance compact:

```text
Writer · Step 4 · document.create_docx
```

For details, expand:

```text
Agent
Writer Agent

Step ID
...

Step title
Generate Word document

Tool
`document.create_docx`
```

---

# 102. Evidence Header

The evidence drawer header should include:

```text
[type icon]
filename
status badge
```

Secondary row:

```text
artifact type · size · created time
```

Action row:

```text
[Preview] [Copy] [Open] [Reveal] [⋯]
```

Avoid excessive chrome.

---

# 103. Metadata Formatting

Format file sizes consistently:

```text
24.1 KB
2.4 MB
1.1 GB
```

Preserve exact values in tooltip/details where important.

Format dates using the application’s global local timezone conventions.

Keep the raw ISO timestamp available in diagnostic details where useful.

---

# 104. Artifact Evidence and Internationalization

Do not hard-code date parsing assumptions.

Treat backend timestamps as timestamps.

Do not parse filenames to guess date, timezone, or ownership.

---

# 105. Evidence Integrity Warning

If artifact metadata and verification evidence appear inconsistent, show the inconsistency rather than silently resolving it.

Example:

```text
Evidence mismatch

Artifact name
SyncNode_Word_c0574206.docx

Verification target
SyncNode_Word_c0574205.docx

Review verification evidence before relying on this artifact.
```

This is preferable to silently selecting one value.

---

# 106. Artifact Duplicate Handling

If multiple artifact records have similar filenames:

```text
SyncNode_Report.docx
SyncNode_Report.docx
```

show enough metadata to disambiguate:

```text
Run
Source step
Created time
Artifact ID
Hash
```

Never silently merge them because filenames match.

---

# 107. Artifact Selection in Approval

When an approval references multiple artifacts, selecting one should open evidence without closing the approval context.

The reviewer must be able to move through:

```text
Artifact 1
Artifact 2
Artifact 3
```

without repeatedly reopening the approval modal.

---

# 108. Evidence and External Effects

The UI should make external-effect boundaries explicit.

Example:

```text
LOCAL ARTIFACTS
✓ created
✓ verified
✓ attached to draft

EXTERNAL ACTION
○ pending approval

SEND
Not executed
```

This preserves the distinction between local work and externally consequential operations.

---

# 109. Run Completion Screen

A good terminal summary should answer:

```text
What did the AI produce?
Was it verified?
What remains pending?
What external effects occurred?
```

Example:

```text
Run completed with approval required

Artifacts
3 created · 3 verified

Draft
Created with 3 attachments

External send
Not executed

[Inspect artifacts]
[Review approval]
```

The exact wording should follow actual run status.

---

# 110. No Backend Modifications

During implementation:

DO NOT:

- edit Python backend files
- edit FastAPI routes
- add artifact endpoints
- change schemas
- change event payloads
- change verification logic
- change hash generation
- change tool registry
- change document generators
- change browser/computer runtimes
- change LangGraph nodes
- change persistence
- change database schema
- modify backend tests except when explicitly instructed outside this frontend task

The frontend must adapt to the documented existing contract.

If the frontend discovers a contract gap, document it locally as a frontend integration note rather than modifying backend behavior.

---

# 111. If an API Field Is Missing

Use the following process:

```text
1. Inspect OpenAPI/entities/events.
2. Confirm whether the field exists under another documented name.
3. Reuse the documented representation if available.
4. Otherwise render the field as unavailable.
5. Do not invent a backend response field.
```

Do not “fix” the backend from the frontend branch.

---

# 112. If an Artifact Preview Is Missing

Do not create a fake server endpoint.

Instead:

```text
Artifact metadata → render
Preview unavailable → explain
Open/reveal → use existing Electron capability
```

A missing preview should not block artifact evidence metadata.

---

# 113. Performance Requirements

Artifact interactions should feel immediate.

Target behavior:

- Selecting a card: immediate state update
- Opening evidence drawer: immediate shell render
- Lazy preview loading: asynchronous
- Timeline filtering: client-side and responsive
- Verification updates: incremental, not full-page rerender
- Large artifact lists: virtualized where needed

Avoid parsing large office/PDF files in the main renderer thread when possible.

---

# 114. Testing Strategy

Artifact evidence requires unit, integration, component, and end-to-end coverage.

---

## 114.1 Unit Tests

Test:

```text
artifact normalization
artifact type detection
status mapping
artifact selection
run isolation
verification aggregation
attachment aggregation
event deduplication
reconciliation
filtering
sorting
```

---

## 114.2 Component Tests

Test:

```text
ArtifactCard
ArtifactEvidenceDrawer
ArtifactPreview
ArtifactProvenance
ArtifactVerificationPanel
ArtifactActivity
ArtifactToolbar
```

Verify loading, empty, success, missing, failed, unavailable states.

---

## 114.3 API Integration Tests

Mock the documented endpoints:

```text
GET /runs/{run_id}
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/steps
GET /runs/{run_id}/verifications
GET /runs/{run_id}/observations
GET /runs/{run_id}/events
```

Verify that:

- REST snapshot renders artifacts.
- SSE updates status.
- Verification events update evidence.
- Duplicate events do not duplicate artifacts.
- Reconnect preserves state.
- Terminal reconciliation produces final truth.

---

## 114.4 End-to-End Golden Test

Create a frontend E2E test around the existing three-artifact golden flow.

Expected UI sequence:

```text
Run starts
 ↓
Artifacts appear
 ↓
Word appears
 ↓
Excel appears
 ↓
PowerPoint appears
 ↓
Verification states resolve
 ↓
All three show verified
 ↓
Attachment evidence appears
 ↓
Approval request appears
 ↓
Approval screen lists all three artifacts
```

The E2E must verify that the UI is reading real backend state rather than mocked “success” placeholders.

---

# 115. Approval Golden Assertions

For the approval state, assert:

```text
approval card visible
artifact count = backend-supported count
all affected artifacts identifiable
verification states accurate
send state not shown as executed unless backend says so
```

The frontend must not infer send completion from attachment completion.

---

# 116. Failure-Injection E2E

Add a UI scenario for:

```text
artifact creation failure
verification failure
recovery attempt
artifact recreated
verification succeeds
```

The UI should show the complete history.

Expected:

```text
Attempt 1 failed
Recovery started
Attempt 2 completed
Final artifact verified
```

---

# 117. Missing Artifact E2E

Test a run where the backend reports a referenced artifact as missing.

Expected UI:

```text
MISSING
```

not:

```text
VERIFIED
```

and not a blank card.

---

# 118. Reconnect E2E

Simulate:

```text
SSE connected
Artifact A arrives
SSE disconnects
REST refresh
SSE reconnects
Artifact B arrives
```

Assert:

- Artifact A remains.
- Artifact B appears once.
- No duplicate records.
- Final verification state is reconciled.

---

# 119. Multi-Run E2E

Open two runs with similar filenames.

Assert:

```text
Run A → only A artifacts
Run B → only B artifacts
```

Switching runs must not leak state.

---

# 120. Electron File Action E2E

Where Electron integration tests are available, verify that:

```text
Reveal
Open
Copy path
Copy hash
```

route through the secure application bridge.

Do not test by exposing Node to the renderer.

---

# 121. Accessibility Test Cases

Verify:

```text
Tab navigation
Enter opens evidence
Escape closes drawer
Screen reader status labels
Keyboard-only artifact inspection
Focus restoration
```

---

# 122. Visual QA Checklist

The artifact evidence surface must visually confirm:

```text
[ ] Artifact cards are compact and readable
[ ] Verified state is obvious but not oversized
[ ] File type is clear
[ ] Filename is legible
[ ] Provenance is visible
[ ] Verification is distinct from creation
[ ] Drawer is wide enough
[ ] Preview does not dominate evidence
[ ] Approval can inspect every artifact
[ ] Failure states are visually distinct
[ ] Loading states look intentional
[ ] No layout jumping occurs on SSE updates
[ ] Long filenames do not break the UI
[ ] Long hashes do not overflow
[ ] Timeline focus is obvious
[ ] Dark monochrome SyncNode visual language is preserved
```

---

# 123. Responsive Layout

Primary target is desktop Electron.

Minimum practical states:

### Wide

```text
Artifacts rail + preview + evidence
```

### Medium

```text
Artifacts list + evidence drawer
```

### Narrow

```text
Artifact list
   ↓
full-screen evidence panel
```

Do not allow evidence metadata to become unreadably compressed.

---

# 124. Information Hierarchy

Every artifact detail view should prioritize:

```text
1. Artifact name + type
2. Artifact status
3. Preview / what the file contains
4. Verification
5. Provenance
6. Attachment/external-action state
7. Technical metadata
8. Audit details
```

Advanced details can be collapsed.

---

# 125. Technical Detail Disclosure

For technical users, allow an expandable diagnostic section:

```text
Technical details

Artifact ID
Run ID
Step ID
Agent ID
Tool key
Path
MIME type
Size bytes
Hash
Raw timestamps
```

This is especially useful for hackathon demos and debugging.

---

# 126. Artifact Evidence Demo Moment

The final SyncNode demo should be able to visibly demonstrate trust.

Example flow:

```text
User asks SyncNode to create three office artifacts and prepare an email.

Artifacts appear live.

Each artifact shows:
  filename
  originating agent
  tool
  verification status

User clicks Word artifact.

Evidence drawer opens.

Preview on left.

Provenance + verification on right.

Timeline highlights creation → observation → verification.

User opens approval.

All three exact artifacts are visible.

Send remains unexecuted until approval.
```

This is a central product demonstration, not an optional polish feature.

---

# 127. Implementation Order

Implement in this order.

## Phase A — Data Layer

1. Read existing frontend API integration docs.
2. Read existing SSE/state docs.
3. Read OpenAPI/events/entities.
4. Implement artifact REST integration.
5. Implement artifact normalization.
6. Wire artifact state into the existing run store.

## Phase B — Basic UI

7. Artifact rail/list.
8. Artifact card.
9. Status badges.
10. Counts/summary.

## Phase C — Evidence Drawer

11. Metadata.
12. Provenance.
13. Verification.
14. Activity.
15. Attachment state.

## Phase D — Preview

16. Text/image.
17. Office preview adapters where supported.
18. PDF preview where supported.
19. Unsupported fallback.

## Phase E — Deep Integration

20. Timeline focus.
21. Workflow graph focus.
22. Agent focus.
23. Approval artifact inspection.
24. Run completion summary.

## Phase F — Hardening

25. Reconnect handling.
26. Multi-run isolation.
27. Failure/recovery history.
28. Accessibility.
29. Electron security review.
30. E2E + visual QA.

---

# 128. Suggested Frontend File Structure

Adapt to the existing frontend project structure rather than creating an unnecessary parallel architecture.

Conceptual structure:

```text
frontend/
  src/
    features/
      artifacts/
        components/
          ArtifactWorkspace.tsx
          ArtifactToolbar.tsx
          ArtifactSummary.tsx
          ArtifactList.tsx
          ArtifactCard.tsx
          ArtifactEvidenceDrawer.tsx
          ArtifactPreview.tsx
          ArtifactMetadata.tsx
          ArtifactProvenance.tsx
          ArtifactVerificationPanel.tsx
          ArtifactAttachmentPanel.tsx
          ArtifactActivity.tsx
        hooks/
          useRunArtifacts.ts
          useArtifactEvidence.ts
        state/
          artifactSelectors.ts
          artifactReducers.ts
        services/
          artifactApi.ts
          artifactPreview.ts
        types/
          artifact.ts
        tests/
          ...
```

Use the repository’s actual conventions if they differ.

Do not force a refactor solely to match this example.

---

# 129. State Invariants

The frontend must maintain these invariants:

```text
I1. Artifact state is scoped to a run.
I2. Filename is not artifact identity.
I3. Verification is independent of artifact existence.
I4. Preview availability is independent of artifact validity.
I5. Attachment is independent of sending.
I6. Failure history is never erased by recovery.
I7. Unknown data is not fabricated.
I8. SSE is incremental; REST provides reconciliation truth.
I9. Renderer never receives arbitrary Node/process access.
I10. Backend behavior is never altered to satisfy a frontend display.
```

These are implementation invariants, not suggestions.

---

# 130. Acceptance Criteria

The frontend artifact evidence feature is complete only when all of the following are true:

### Core

```text
[ ] Artifacts load from documented run artifact API.
[ ] Artifacts are scoped to the correct run.
[ ] New artifact state updates live.
[ ] Artifact cards render correctly.
[ ] Artifact detail drawer works.
```

### Evidence

```text
[ ] Artifact provenance is visible where backend data exists.
[ ] Verification results are visible.
[ ] Related observations can be opened/focused where supported.
[ ] Related audit activity can be inspected.
[ ] Attachment state is explicit.
[ ] Approval state is explicit.
```

### Preview

```text
[ ] Supported previews work.
[ ] Unsupported formats have a clear fallback.
[ ] Previews are read-only.
[ ] Large artifacts do not freeze the renderer.
```

### Safety

```text
[ ] No arbitrary renderer filesystem access.
[ ] No arbitrary shell execution.
[ ] No cloud upload for local artifact preview.
[ ] No fabricated evidence.
[ ] No false send/success state.
```

### Resilience

```text
[ ] SSE reconnect works.
[ ] REST reconciliation works.
[ ] Duplicate events do not duplicate artifacts.
[ ] Multi-run isolation works.
[ ] Failed artifacts are visible.
[ ] Recovered artifacts preserve failure history.
```

### Demo

```text
[ ] Three-artifact golden flow renders correctly.
[ ] Word / Excel / PowerPoint artifacts are identifiable.
[ ] All three verification states are correctly represented.
[ ] Attachment evidence is inspectable.
[ ] Approval screen lists exact artifacts.
[ ] Send is not shown as executed when approval is still pending.
```

---

# 131. Final Editor Instruction

Build the artifact evidence experience as a **trust and provenance layer**, not as a generic file manager.

The user should be able to move from:

```text
“What did SyncNode make?”
```

to:

```text
“This exact artifact came from this run,
this step,
this agent/tool,
and these verification events confirm what happened.”
```

The UI must remain factual and backend-driven.

Do not fill gaps with invented data.

Do not add undocumented APIs.

Do not change backend behavior.

Do not bypass Electron security boundaries.

Do not collapse artifact creation, verification, attachment, approval, and external send into a single success state.

Make the evidence inspectable from the active run, timeline, workflow graph, and approval surfaces.

The final result should feel like a native part of the SyncNode AI IDE:

```text
LIVE EXECUTION
      ↓
ARTIFACTS
      ↓
EVIDENCE
      ↓
VERIFICATION
      ↓
HUMAN TRUST
```

**Frontend only. Backend untouched. Existing contract authoritative.**
