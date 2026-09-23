# PROMPT: Generate `12_COMPUTER_CONTROL.md` Technical Specification

You are a **Principal Windows Systems Software Engineer and Robotic Desktop Automation Architect** specializing in:

- Windows 10/11 internals
- Win32 process/window APIs
- Windows UI Automation (UIA)
- COM / STA automation
- display and multi-monitor geometry
- DPI-aware coordinate systems
- deterministic mouse/keyboard synthesis
- clipboard automation
- desktop-session isolation
- human-interference detection
- fail-closed safety interlocks
- local-first computer-use runtimes

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, production-grade, implementation-ready technical specification** titled:

> `12_COMPUTER_CONTROL.md`

This specification governs the **SyncNode Computer Control Subsystem**: the deterministic execution layer responsible for controlling real Windows desktop applications, resolving accessibility elements, managing process/window state, synthesizing keyboard and mouse input only when required, enforcing exclusive desktop control, freezing automation during user interference, detecting secure-desktop/UAC conditions, capturing post-action observations, and exposing verifiable state transitions to the Agent Runtime and recovery system.

The subsystem operates on the **actual Windows 10/11 desktop**.

It must integrate cleanly with:

- Agent Runtime
- Planner
- Tool Registry
- Context Engine
- Token Management
- Vision / Multimodal subsystem
- Browser Runtime
- Document Runtime
- Verification / Recovery
- Policy / Approval
- Audit / Telemetry
- `computer_observations`
- `audit_events`

The system must prioritize semantic UI Automation over coordinates.

> **UIA / semantic controls are canonical interaction mechanisms. Vision and coordinate-based input are fallbacks, never authoritative state.**

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architectural source of truth.

Before writing the final specification:

1. Read the complete `idea.md`.
2. Extract its:
   - Computer Control responsibilities
   - Windows automation constraints
   - UIA requirements
   - process/window requirements
   - desktop mutex requirements
   - user-interference behavior
   - secure-desktop/UAC policy
   - observation persistence
   - browser/document integration
   - approval constraints
   - cancellation/recovery semantics
   - phase-1 scope
3. Preserve SyncNode terminology wherever possible.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud services.
6. Do not require administrator privileges.
7. Do not design UAC bypass or credential harvesting.
8. Do not design CAPTCHA bypass or other security-control evasion.
9. Where implementation details are missing, make a concrete engineering choice and explicitly label it:
   > **Implementation Decision**
10. Clearly distinguish:
   - verified Windows state
   - semantic UIA targets
   - model/vision proposals
   - coordinate-derived fallback targets
   - synthetic input
   - user input
   - approval state
   - post-action observation
   - verification evidence
   - persisted audit state

The final document must be directly implementable by another engineer.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & OPERATING PHILOSOPHY

Position the subsystem inside SyncNode:

```text
Planner / Agent Runtime
          ↓
   Tool Registry
          ↓
┌─────────────────────────────────────────┐
│         COMPUTER CONTROL                │
│                                         │
│ Process Lifecycle                       │
│ Window Discovery / Focus                │
│ UI Automation                           │
│ Semantic Locator                        │
│ Desktop Mutex                           │
│ Human Interference Detector             │
│ Keyboard / Mouse Input                  │
│ Clipboard Bridge                        │
│ Secure Desktop Detector                 │
│ Observation Capture                     │
└──────────────────┬──────────────────────┘
                   ↓
              Windows OS
```

The Computer Control subsystem SHALL own:

- process launch/tracking
- PID/HWND correlation
- window enumeration
- active-window verification
- focus stabilization
- UIA initialization
- UIA tree traversal
- semantic target resolution
- UIA pattern execution
- controlled coordinate fallback
- keyboard input
- clipboard bridge
- desktop mutex
- user-interference freezing
- secure-desktop detection
- emergency abort
- observation capture
- action lifecycle state
- cleanup and resource release

It SHALL NOT own:

- intent interpretation
- graph planning
- model routing
- token accounting
- human approval decisions
- arbitrary tool authorization
- unrestricted shell execution
- privilege escalation

---

# 1.1 Core invariants

### Semantic-first control

Required resolution order:

```text
UIA semantic target
    ↓
application-specific adapter
    ↓
vision-assisted target proposal
    ↓
verified coordinate fallback
    ↓
SendInput
```

Do not use blind coordinates when a deterministic UIA control can be resolved.

### Deterministic action state

Every action follows:

```text
PROPOSED
→ SCHEMA_VALIDATED
→ TARGET_RESOLVED
→ POLICY_ALLOWED
→ EXECUTING
→ OBSERVING
→ VERIFYING
→ PASSED / FAILED
```

Alternative terminal:

```text
ABORTED
```

### Exclusive physical desktop control

Only one agent may synthesize physical input on one desktop session at a time.

### User safety

Any unexpected human input must freeze automated input.

### Secure desktop safety

Encountering:

- UAC consent
- Winlogon
- credential prompts
- secure desktop

must fail closed.

---

# 1.2 Required end-to-end control topology

Include detailed Mermaid and ASCII diagrams:

```text
Action Proposal
      ↓
Schema Validation
      ↓
Target Window Resolution
      ↓
UIA Target Resolution
      ↓
Policy Check
      ↓
Desktop Mutex
      ↓
Foreground Focus Stabilization
      ↓
Pattern Selection
   /           \
 UIA           Fallback
  │              │
  ▼              ▼
Invoke/Value    Vision / verified coordinates
  │              │
  └──────┬───────┘
         ▼
    Input / Action
         ↓
   Post-Action Observation
         ↓
      Verification
         ↓
   Observation Persistence
         ↓
     Mutex Release
         ↓
         Result
```

---

# 2. PROCESS LIFECYCLE & WINDOW MANAGEMENT ENGINE

Provide implementation-ready process/window management.

---

## 2.1 Process spawning

Support safe non-elevated execution through:

```text
CreateProcessW
subprocess.Popen
```

Define exact contracts for:

```text
executable
arguments
working_directory
environment_overrides
expected_process_name
expected_window_class
expected_window_title
timeout
```

Rules:

- do not invoke a shell by default
- do not accept arbitrary model-generated executable paths
- validate approved application identity
- validate working directory
- reject unexpected privilege requirements
- capture PID/process handle
- associate process with `run_step_id`

---

## 2.2 Process tracking

Track:

```text
PID
process handle
parent PID
process name
executable identity
start time
exit time
associated run
associated step
```

Handle:

- early process exit
- crash
- access denied
- duplicate process instances
- child process discovery

Define safe `CloseHandle` lifecycle.

---

## 2.3 HWND resolution

Implement:

```text
EnumWindows
EnumChildWindows
GetWindowThreadProcessId
IsWindowVisible
IsWindow
```

Filtering dimensions:

```text
PID
process identity
window title
window class
visibility
enabled state
foreground status
ownership/transient relationship
```

---

## 2.4 Deterministic multi-window selection

Selection priority may be:

```text
exact process identity
→ visible
→ expected class
→ expected title
→ foreground
→ stable HWND ordering
```

Use explicit tie-breaking.

Handle:

- splash screens
- dialogs
- MDI child windows
- browser windows
- modal windows
- hidden helper windows

---

## 2.5 Focus stabilization

Implement:

```text
observe current foreground
→ validate target HWND
→ BringWindowToTop
→ ShowWindow if policy permits
→ SetForegroundWindow
→ re-observe
→ verify exact foreground HWND
→ continue or fail
```

Where `AttachThreadInput` is used, document:

- why
- thread identity requirements
- attach/detach symmetry
- risks
- cleanup

Never assume `SetForegroundWindow` is guaranteed to succeed.

---

## 2.6 Graceful teardown

Use:

```text
WM_CLOSE
→ bounded wait
→ re-observe
→ forceful termination only if policy explicitly permits
```

Do not use `WM_DESTROY` as if it were a general external shutdown request; explain the distinction between requesting application shutdown and directly destroying window objects.

---

# 3. SEMANTIC CONTROL ENGINE — WINDOWS UI AUTOMATION

Define a complete UIA subsystem.

---

## 3.1 COM / STA architecture

Every UIA worker must initialize COM correctly:

```text
CoInitializeEx(..., COINIT_APARTMENTTHREADED)
```

Specify:

- STA thread lifecycle
- one initialization per worker thread
- matching `CoUninitialize`
- thread affinity
- COM exception handling
- marshaling constraints

Do not move COM-bound UIA objects between threads unsafely.

---

## 3.2 UIA client creation

Provide concrete reference implementation for acquiring:

```text
IUIAutomation
```

through the selected COM binding.

Include:

- HRESULT handling
- initialization errors
- cleanup
- stale-reference normalization

---

## 3.3 Tree scopes

Support:

```text
TreeScope_Element
TreeScope_Children
TreeScope_Descendants
```

Define traversal limits:

```text
max_depth
max_nodes
max_duration_ms
```

Check cancellation during traversal.

---

## 3.4 Compound locator conditions

Implement matching for:

```text
AutomationId
Name
ClassName
ControlType
ProcessId
enabled state
```

Support deterministic condition composition equivalent to:

```text
CreateAndCondition
```

and where useful:

```text
CreateOrCondition
```

Do not permit unbounded arbitrary condition graphs from model output.

---

## 3.5 UIA cache requests

Define `IUIAutomationCacheRequest` usage.

Cache:

```text
Name
AutomationId
ControlType
ClassName
IsEnabled
IsOffscreen
BoundingRectangle
ProcessId
supported patterns
```

Explain how batched COM retrieval reduces repeated cross-process calls.

Define:

- cache lifecycle
- stale cache detection
- refresh behavior

---

## 3.6 UIA node model

Retain:

```text
runtime_id
automation_id
name
control_type
class_name
bounding_rectangle
enabled
offscreen
focused
supported_patterns
parent
```

Suppress non-interactive layout containers when safe.

---

## 3.7 UIA pattern execution

Provide concrete wrappers for:

### InvokePattern

```text
IUIAutomationInvokePattern::Invoke
```

### ValuePattern

```text
IUIAutomationValuePattern::SetValue
```

### SelectionItemPattern

Support:

```text
Select
AddToSelection
RemoveFromSelection
```

where available.

### TogglePattern

```text
IUIAutomationTogglePattern::Toggle
```

### ExpandCollapsePattern

```text
Expand
Collapse
```

### ScrollItemPattern

```text
ScrollIntoView
```

For every pattern define:

- preconditions
- execution
- HRESULT/error handling
- post-observation
- verification
- stale-reference recovery

---

# 3.8 Semantic locator hierarchy

Use:

```text
AutomationId
→ AutomationId + ControlType
→ Name + ControlType
→ ClassName + ControlType
→ ancestry/path
→ application adapter
→ vision fallback
```

Never allow coordinate clicking to be the first fallback.

If multiple semantic matches remain, fail with:

```text
UIA_ELEMENT_AMBIGUOUS
```

rather than selecting arbitrarily.

---

# 3.9 Stale UIA reference recovery

Required sequence:

```text
stale element / COM exception
→ invalidate reference
→ reacquire active HWND
→ rebuild UIA root
→ refresh cache
→ resolve semantic locator again
→ retry once
→ fail
```

No repeated retries against the same stale object.

---

# 4. VIRTUAL DESKTOP GEOMETRY & COORDINATE MAPPING

Coordinate input is secondary and must be derived from fresh verified observations.

---

## 4.1 Virtual screen metrics

Use:

```text
SM_XVIRTUALSCREEN
SM_YVIRTUALSCREEN
SM_CXVIRTUALSCREEN
SM_CYVIRTUALSCREEN
```

Support:

- multiple monitors
- negative monitor coordinates
- mixed orientations
- different resolutions
- per-monitor DPI

---

## 4.2 DPI normalization

Use:

```text
GetDpiForWindow(HWND)
```

with:

```text
ScaleFactor = DPI / 96.0
```

Clearly distinguish:

- logical coordinates
- device pixels
- physical screen coordinates
- UIA bounding rectangles

Do not assume one global DPI factor.

---

## 4.3 Coordinate transform

Implement a verified transformation from target rectangle to physical screen point.

Where the architecture uses the safe-central-region policy, define:

```text
inner_target =
verified bounding rectangle
intersected with a central safe region
```

Use a configurable safe-region fraction rather than an unexplained hardcoded constant.

All target coordinates must pass:

```text
fresh observation
+
foreground verification
+
window-bound check
+
monitor geometry check
+
target-bound check
```

before input.

---

## 4.4 Boundary protection

Reject:

- negative/invalid rectangle dimensions
- stale bounds
- off-screen target
- target outside expected window
- taskbar/system-tray regions where prohibited
- coordinates belonging to a different foreground application

Never click outside the verified target.

---

# 5. SYNTHETIC INPUT SYNTHESIS & LOW-LEVEL WIN32 DRIVERS

Define real Win32 input structures.

---

## 5.1 `SendInput`

Provide `ctypes` structures for:

```text
INPUT
MOUSEINPUT
KEYBDINPUT
HARDWAREINPUT
```

and the correct function signature for:

```text
SendInput
```

Explain:

- mouse movement
- left/right/middle buttons
- wheel
- key down/up
- scan codes
- Unicode events
- extra information

---

## 5.2 Mouse action pipeline

Before mouse input:

```text
desktop mutex
→ user interference check
→ secure desktop check
→ foreground verification
→ fresh target observation
→ coordinate calculation
→ coordinate bounds validation
→ SendInput
→ input completion check
→ post-action observation
```

Never dispatch stale coordinates.

---

## 5.3 Cursor trajectories

Do not design randomization to evade anti-automation/security systems.

When a cursor path is needed for ordinary stability, define a deterministic bounded interpolation method, such as a fixed Bézier curve.

Use reproducible control points derived from:

```text
start
end
target bounds
```

No arbitrary random jitter.

---

## 5.4 Keyboard input

Support:

```text
VkKeyScanExW
KEYEVENTF_UNICODE
KEYEVENTF_SCANCODE
```

Define:

- modifier handling
- key down/up symmetry
- Unicode characters
- function keys
- Ctrl/Alt/Shift/Win combinations
- cancellation

If an exception occurs:

```text
release any known-down modifiers
```

before returning failure.

---

# 6. TEXT ENTRY, KEYSTROKE INJECTION & CLIPBOARD BRIDGE

---

## 6.1 Text-entry selection policy

Choose among:

```text
UIA ValuePattern
→ application-native editor API
→ KEYEVENTF_UNICODE
→ clipboard paste
```

depending on target/application capabilities.

Prefer semantic APIs.

---

## 6.2 Atomic keyboard transaction

Model:

```text
focus verified
→ begin input transaction
→ modifier down
→ keys/text
→ modifier up
→ verify modifier release
→ re-observe
```

Protect against:

- partial sequence
- cancellation
- focus loss
- user interference

---

## 6.3 Clipboard bridge

Required:

```text
capture metadata
→ OpenClipboard with bounded retries
→ write CF_UNICODETEXT
→ focus target
→ Ctrl+V
→ verify
→ restore original clipboard if possible
```

Define retry:

```text
delay_n = min(base_delay × 2^n, max_delay)
```

with cancellation and retry count.

Never persist raw clipboard contents in logs.

---

## 6.4 Clipboard restoration

Cleanup must attempt restoration even when paste/verification fails.

If restoration fails:

```text
CLIPBOARD_RESTORE_FAILED
```

must be auditable.

Do not silently overwrite the user's clipboard.

---

# 7. ACTION STATE MACHINE & EXECUTION LIFECYCLE

Define exact states:

```text
PROPOSED
SCHEMA_VALIDATED
TARGET_RESOLVED
POLICY_ALLOWED
EXECUTING
OBSERVING
VERIFYING
PASSED
FAILED
ABORTED
```

---

## 7.1 Legal transitions

Define a static transition map.

Example:

```text
PROPOSED
→ SCHEMA_VALIDATED

SCHEMA_VALIDATED
→ TARGET_RESOLVED
→ FAILED

TARGET_RESOLVED
→ POLICY_ALLOWED
→ FAILED

POLICY_ALLOWED
→ EXECUTING
→ ABORTED

EXECUTING
→ OBSERVING
→ FAILED
→ ABORTED

OBSERVING
→ VERIFYING
→ FAILED

VERIFYING
→ PASSED
→ FAILED
```

Reject illegal transitions.

---

## 7.2 State timeout policy

Every state must have:

- entry timestamp
- deadline
- cancellation support
- timeout error

Use monotonic time for duration measurement.

---

## 7.3 Cleanup invariant

For every terminal action:

```text
release input state
→ release clipboard
→ release COM/UIA temporary references
→ release desktop mutex
→ capture final observation
→ persist telemetry
```

Cleanup must be idempotent.

---

# 8. CONCURRENCY CONTROL, DESKTOP FOCUS MUTEX & INTERFERENCE ENGINE

---

## 8.1 Desktop mutex

Use a system-wide named mutex or equivalent exclusive resource.

Example:

```text
Global\SyncNode_Desktop_Focus_Lock
```

Define:

- acquisition timeout
- ownership identity
- fencing token/lease
- crash recovery
- safe release
- stale-owner handling

---

## 8.2 Physical user interference

Use local Windows observation mechanisms such as:

```text
WH_MOUSE_LL
WH_KEYBOARD_LL
```

where appropriate.

Detect:

- physical mouse movement
- physical keyboard events
- foreground window changes

Define a configurable movement threshold based on the architecture default where applicable.

---

## 8.3 Synthetic vs human event distinction

Design an explicit mechanism to distinguish runtime-generated input from observed physical input where technically reliable.

Do not assume that a user-mode hook can perfectly identify every input source.

Where ambiguity remains:

```text
treat as user interference
→ freeze automation
```

Fail-safe behavior wins.

---

## 8.4 Freeze protocol

On interference:

```text
automation active
→ immediately stop new input
→ cancel pending input transaction
→ capture current foreground/UI state
→ invalidate target
→ persist `computer.user_interrupted`
→ transition to ABORTED or paused reconciliation state
```

Do not fight the human for control.

---

# 8.5 Emergency kill switch

Define a configurable emergency sequence.

On trigger:

```text
stop input
→ abort current action
→ release desktop mutex
→ clean up modifiers
→ persist audit
→ terminate/disable computer-control execution path
```

The emergency path must remain available even if the active application is hung.

---

# 9. SECURITY BOUNDARIES, PROTECTED DESKTOPS & UAC INTERLOCKS

This section must be precise and must not make unsupported claims about what ordinary user-mode code can intercept.

---

## 9.1 Secure desktop detection

Use local Win32 APIs such as:

```text
OpenInputDesktop
GetUserObjectInformationW
```

Detect transitions away from the supported interactive desktop.

Recognize known contexts such as:

```text
Winlogon
ConsentUI
```

where identifiable.

---

## 9.2 UAC behavior

Required invariant:

```text
secure desktop / UAC detected
→ freeze automation
→ capture safe metadata
→ emit SEC_UAC_RESTRICTED
→ release desktop lock
→ fail closed
```

Never:

- click UAC approval
- manipulate credential dialogs
- bypass elevation
- capture passwords

---

## 9.3 Secure-attention sequences

Do not claim that normal user-mode hooks can universally block kernel-protected sequences such as the Secure Attention Sequence.

The specification must distinguish:

```text
what can be detected
```

from:

```text
what can actually be intercepted or blocked in user mode
```

If an input is outside the runtime's safe control boundary:

```text
reject the automation request
```

rather than pretending the subsystem can enforce an impossible guarantee.

---

## 9.4 Process/application security boundary

Define approved application identities.

Before launching or manipulating a process verify:

- executable identity
- expected application
- PID/window relationship
- current foreground process

Unexpected application state must trigger re-observation and potentially halt execution.

---

# 10. OBSERVATION CAPTURE & MULTIMODAL HANDOFF

---

## 10.1 Post-action observation

Every state-changing action should trigger:

```text
active window snapshot
+
UIA state
+
focus state
+
action result
+
optional bounded visual frame
```

The visual frame must be local-only.

---

## 10.2 Observation hashing

Canonicalize:

```text
observation object
→ stable JSON serialization
→ UTF-8
→ SHA-256
```

Use:

- stable key order
- deterministic list order
- normalized strings
- explicit null-handling

---

## 10.3 `computer_observations`

Map persisted observations to the existing schema from `idea.md`.

Capture where supported:

```text
run_step_id
machine/session
application
process
HWND
window title/class
UI tree
focused element
action metadata
timestamp
observation hash
parent observation hash
```

---

## 10.4 Vision bridge

When UIA fails:

```text
UIA target resolution
→ bounded screenshot
→ local vision model
→ proposed bounding region
→ deterministic bounds/foreground validation
→ coordinate fallback
```

Vision output is advisory.

It must never overwrite the canonical UIA/OS observation.

---

# 11. COMPLETE DATA CONTRACTS & INTERFACE DEFINITIONS

Provide fully syntactically valid Pydantic v2 models.

Required:

## `WindowHandleContext`

```text
hwnd
pid
process_name
window_title
class_name
bounding_box
dpi_scale
visible
enabled
is_foreground
captured_at
observation_hash
```

## `UIAElementDescriptor`

```text
runtime_id
automation_id
name
control_type
class_name
bounding_rectangle
supported_patterns
is_enabled
is_offscreen
is_focused
process_id
parent_runtime_id
```

## `SyntheticInputAction`

```text
action_type
coordinates
modifiers
text_payload
key_sequence
delay_parameters
target_observation_hash
```

Supported action types:

```text
click
double_click
right_click
move
type_text
send_hotkey
drag_drop
scroll
```

## `ComputerObservationRecord`

Include the fields required to persist to `computer_observations`.

---

# 11.1 `ComputerControlProtocol`

Provide:

```python
class ComputerControlProtocol(Protocol):
    async def launch_app(...) -> ProcessContext:
        ...

    async def find_window(...) -> WindowHandleContext:
        ...

    async def focus_window(...) -> FocusResult:
        ...

    async def resolve_uia_element(...) -> UIAElementDescriptor:
        ...

    async def invoke_uia_pattern(...) -> ActionResult:
        ...

    async def send_synthetic_input(...) -> ActionResult:
        ...

    async def acquire_desktop_mutex(...) -> DesktopLockLease:
        ...

    async def release_desktop_mutex(...) -> None:
        ...

    async def is_user_interfering(...) -> bool:
        ...
```

Improve signatures where needed, but keep responsibilities separated.

---

# 12. REQUIRED SUPPORTING SCHEMAS

Also define complete models for:

- `ProcessContext`
- `ProcessIdentity`
- `LaunchAppRequest`
- `WindowQuery`
- `FocusRequest`
- `FocusResult`
- `DesktopSession`
- `DesktopLockRequest`
- `DesktopLockLease`
- `LocatorQuery`
- `UIAAction`
- `UIAPattern`
- `UIATreeSnapshot`
- `SyntheticInputAction`
- `MouseCoordinates`
- `KeyboardSequence`
- `ClipboardMetadata`
- `ClipboardWriteRequest`
- `UserInterferenceState`
- `FocusState`
- `SecureDesktopState`
- `VerificationEvidence`
- `ActionResult`
- `ComputerObservationRecord`
- `ComputerAuditEvent`
- `ComputerControlError`

No undefined types may appear in code examples.

---

# 13. COMPLETE WIN32 / COM / UIA API CONTRACTS

Provide actual `ctypes`/`comtypes` declarations or safe wrappers for the relevant APIs.

At minimum cover:

### Process

```text
CreateProcessW
OpenProcess
GetExitCodeProcess
CloseHandle
TerminateProcess
```

### Window

```text
EnumWindows
EnumChildWindows
GetWindowThreadProcessId
IsWindow
IsWindowVisible
GetForegroundWindow
SetForegroundWindow
BringWindowToTop
ShowWindow
SendMessageW
PostMessageW
```

### Input/desktop

```text
OpenInputDesktop
GetUserObjectInformationW
SendInput
VkKeyScanExW
```

### Geometry

```text
GetSystemMetrics
GetDpiForWindow
```

### COM

```text
CoInitializeEx
CoUninitialize
```

### UIA

Provide concrete interface usage for:

```text
IUIAutomation
IUIAutomationElement
IUIAutomationCondition
IUIAutomationCacheRequest
IUIAutomationInvokePattern
IUIAutomationValuePattern
IUIAutomationSelectionItemPattern
IUIAutomationTogglePattern
IUIAutomationExpandCollapsePattern
IUIAutomationScrollItemPattern
```

Do not just list API names.

Show safe signatures/wrappers and normalize failure HRESULTs into typed runtime errors.

---

# 14. SECURITY & ERROR TAXONOMY

Define complete errors:

```text
PROCESS_LAUNCH_FAILED
PROCESS_NOT_FOUND
PROCESS_EXITED_EARLY
WINDOW_NOT_FOUND
WINDOW_AMBIGUOUS
WINDOW_STALE
FOCUS_STABILIZATION_FAILED
UIA_INITIALIZATION_FAILED
UIA_ELEMENT_NOT_FOUND
UIA_ELEMENT_AMBIGUOUS
UIA_STALE_ELEMENT
UIA_PATTERN_UNSUPPORTED
UIA_COM_ERROR
DESKTOP_MUTEX_TIMEOUT
DESKTOP_LOCK_LOST
USER_INTERRUPT_DETECTED
INPUT_FROZEN
INPUT_DISPATCH_FAILED
COORDINATE_TARGET_INVALID
TARGET_OBSERVATION_STALE
CLIPBOARD_BUSY
CLIPBOARD_WRITE_FAILED
CLIPBOARD_RESTORE_FAILED
SEC_UAC_RESTRICTED
SECURE_DESKTOP_DETECTED
VISION_TARGET_UNVERIFIED
APPLICATION_POLICY_VIOLATION
PROCESS_POLICY_VIOLATION
ACTION_VERIFICATION_FAILED
COMPUTER_CONTROL_TIMEOUT
EMERGENCY_ABORT
RESOURCE_UNAVAILABLE
```

Every error must include:

- stable code
- severity
- retryability
- run ID
- step ID
- machine/session
- trace ID
- sanitized reason
- recovery action

Never include secrets.

---

# 15. RESILIENCE & RECOVERY

Define deterministic recovery paths.

### Stale UIA node

```text
reobserve
→ reacquire UIA
→ resolve again
→ retry once
→ fail
```

### Window lost

```text
verify process
→ enumerate windows
→ select replacement only with deterministic identity
→ otherwise fail
```

### Process crash

```text
observe process exit
→ persist observation
→ fail step
→ notify Planner/Recovery
```

Restart only if the plan explicitly authorizes it.

### Focus drift

```text
foreground mismatch
→ stop input
→ re-stabilize
→ verify
→ continue or fail
```

### User intervention

```text
freeze
→ capture state
→ invalidate target
→ reconcile
→ require safe resume condition
```

---

# 16. HANDLE, COM & RESOURCE OWNERSHIP

Provide an ownership model.

For every resource specify:

```text
resource
creator
owner
lifetime
cleanup
```

Resources include:

- process handles
- thread handles
- mutex handles
- desktop handles
- hook handles
- COM/UIA objects
- clipboard ownership

Use context-manager/RAII-style wrappers where possible.

All terminal paths must release owned resources exactly once.

---

# 17. PERFORMANCE & CONCURRENCY

Provide measurable engineering targets for:

- process launch tracking
- window enumeration
- UIA initialization
- UIA lookup
- cached property retrieval
- focus stabilization
- input dispatch
- observation capture
- desktop lock acquisition
- clipboard operation

Define upper bounds:

```text
max_ui_tree_depth
max_ui_tree_nodes
max_action_duration_ms
max_focus_retries
max_uia_retry_count
max_clipboard_retries
max_window_search_ms
max_process_launch_wait_ms
```

All values must be configuration-backed.

---

# 17.1 Concurrency model

Define:

```text
read-only observation
→ potentially concurrent

physical desktop control
→ exclusive

same browser desktop session
→ serialized through desktop mutex

unrelated document parsing
→ concurrent
```

Explain which UIA operations can safely execute concurrently and which must remain on an STA thread.

---

# 18. REFERENCE PACKAGE STRUCTURE

Provide a concrete package tree:

```text
syncnode/
└── computer_control/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── runtime.py
    ├── processes.py
    ├── windows.py
    ├── focus.py
    ├── desktop_mutex.py
    ├── interference.py
    ├── security.py
    ├── observations.py
    ├── verification.py
    ├── vision_bridge.py
    ├── input/
    │   ├── __init__.py
    │   ├── send_input.py
    │   ├── mouse.py
    │   ├── keyboard.py
    │   └── clipboard.py
    ├── uia/
    │   ├── __init__.py
    │   ├── com.py
    │   ├── client.py
    │   ├── traversal.py
    │   ├── cache.py
    │   ├── locator.py
    │   └── patterns.py
    ├── persistence.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_processes.py
        ├── test_windows.py
        ├── test_focus.py
        ├── test_mutex.py
        ├── test_interference.py
        ├── test_security.py
        ├── test_uia.py
        ├── test_locator.py
        ├── test_patterns.py
        ├── test_input.py
        ├── test_clipboard.py
        ├── test_observations.py
        ├── test_verification.py
        ├── test_persistence.py
        └── test_determinism.py
```

Adapt to the actual `idea.md` repository structure.

---

# 19. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The generated `12_COMPUTER_CONTROL.md` MUST contain real Python 3.12+ implementations for at least:

1. `CreateProcessW` wrapper
2. safe non-elevated application launch
3. process handle wrapper
4. `EnumWindows` wrapper
5. deterministic HWND selection
6. foreground detection
7. focus stabilization
8. `AttachThreadInput` safe wrapper where justified
9. desktop mutex acquisition/release
10. COM STA worker setup
11. UIA client creation
12. UIA cache request
13. UIA tree traversal
14. compound locator creation
15. deterministic element selection
16. InvokePattern
17. ValuePattern
18. SelectionItemPattern
19. TogglePattern
20. ExpandCollapsePattern
21. ScrollItemPattern
22. stale UIA recovery
23. virtual-screen geometry retrieval
24. DPI-aware coordinate transformation
25. coordinate clamping
26. `SendInput` ctypes structures
27. mouse click implementation
28. Unicode keyboard implementation
29. modifier-safe hotkey sequence
30. clipboard backup/write/paste/restore
31. user-interference detection architecture
32. secure-desktop detection
33. emergency abort handling
34. observation canonicalization + SHA-256
35. complete action state machine
36. Computer Control orchestration
37. teardown/cleanup logic
38. database observation persistence
39. audit event generation
40. `ComputerControlProtocol`

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- Windows 10/11-compatible
- type annotated
- async-compatible where appropriate
- syntactically complete
- executable with documented dependencies
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder implementations
- free of unexplained magic constants

Where a native API is hazardous, wrap it behind a checked interface with explicit preconditions.

---

# 20. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- Win32 integration tests
- UIA tests
- desktop-session tests
- concurrency tests
- security tests
- interference tests
- clipboard tests
- failure-recovery tests
- persistence tests
- deterministic replay tests

Mandatory tests:

### UIA-first

If a supported semantic control exists, coordinate fallback is not selected.

### Ambiguity

Multiple matching UIA elements fail deterministically rather than selecting randomly.

### Stale reference

A stale UIA object is never invoked.

### Focus

Keyboard input is never dispatched unless the expected foreground window is verified.

### Desktop mutex

Two agents cannot simultaneously acquire the same physical desktop control resource.

### User interference

Human mouse/keyboard activity freezes automated input.

### Secure desktop

UAC/Winlogon/secure-desktop detection blocks execution.

### Coordinate fallback

Coordinates require fresh observation, bounds validation, and foreground verification.

### Keyboard cleanup

Every interrupted key sequence releases known-down modifiers.

### Clipboard safety

Clipboard restoration is attempted on every terminal path.

### Process safety

Unknown applications cannot be launched.

### Observation safety

Every state-changing action yields post-action observation evidence.

### Determinism

Identical:

- current UI state
- locator
- application
- runtime configuration

produce identical semantic target resolution.

---

# 21. DATABASE INTEROPERABILITY

Align with:

```text
computer_observations
audit_events
```

using the exact architecture from `idea.md`.

Define mapping for:

### `computer_observations`

- run
- step
- machine/session
- process
- window
- UI tree
- focused control
- action
- timestamp
- observation hash
- parent hash

### `audit_events`

- event ID
- run/step
- action
- result
- trace
- timestamp
- security classification
- observation reference

If a field must be added beyond `idea.md`, introduce it explicitly under:

> **Implementation Decision — Computer Control Persistence Extensions**

---

# 22. INTEGRATION WITH TOOL REGISTRY

Expected flow:

```text
Tool Registry
    ↓
Validated computer tool call
    ↓
Computer Control
    ↓
Desktop mutex
    ↓
Observe
    ↓
Resolve target
    ↓
Act
    ↓
Observe
    ↓
Verify
    ↓
ToolCallResult
```

The Tool Registry owns:

- authorization
- schema validation
- risk
- approval
- idempotency

Computer Control owns:

- actual Windows interaction
- focus
- UIA
- input
- desktop safety
- observation

Do not duplicate authorization logic inside low-level API wrappers, but always revalidate critical safety preconditions at the execution boundary.

---

# 23. INTEGRATION WITH CONTEXT ENGINE & VERIFICATION

After state changes:

```text
Computer action
     ↓
Observation
     ↓
Context Engine delta
     ↓
Verifier
```

Expose:

- window identity
- focus
- UIA target
- action result
- observation hash
- UI delta
- timestamps

The verifier may determine semantic success, but canonical OS state remains the observation source.

---

# 24. REFERENCE END-TO-END WORKFLOWS

Use real Windows workflows.

---

## Example A — Word Save

```text
Request:
click Save
```

Pipeline:

```text
Tool Registry validation
→ desktop mutex
→ Word HWND resolution
→ foreground stabilization
→ UIA locator
  Name = Save
  ControlType = Button
→ InvokePattern
→ observation
→ verifier
→ persistence
→ mutex release
```

---

## Example B — UIA fallback

```text
Save is unavailable through UIA
```

Pipeline:

```text
reobserve
→ application adapter
→ bounded local vision
→ target proposal
→ coordinate validation
→ SendInput
→ observation
→ verification
```

---

## Example C — Text entry

```text
Enter story into Word
```

Preferred sequence:

```text
UIA ValuePattern
→ verify
```

Fallback:

```text
Unicode input / clipboard
→ verify
```

---

## Example D — Human interference

```text
User moves mouse while agent is typing
```

Expected:

```text
freeze input
→ release pending input transaction
→ capture state
→ invalidate target
→ audit
→ pause/abort
```

---

## Example E — UAC

```text
UAC consent desktop appears
```

Expected:

```text
detect
→ stop all automation
→ SEC_UAC_RESTRICTED
→ audit
→ release mutex
→ fail
```

---

# 25. SECURITY MODEL

Explicitly address:

- stale HWNDs
- stale UIA references
- focus hijacking
- foreground-window changes
- user interference
- secure desktops
- UAC
- credential prompts
- unexpected process identity
- coordinate injection
- DPI miscalculation
- off-screen clicks
- clipboard leakage
- stuck modifiers
- desktop lock theft
- orphaned handles
- malicious application names
- unsafe process launch
- model-generated target spoofing
- vision target spoofing
- cross-user desktop control

Required guarantees:

1. UIA is primary.
2. Coordinates are fallback only.
3. Every coordinate target comes from fresh verified observation.
4. Desktop control is exclusive.
5. User interaction freezes automation.
6. Secure desktop blocks execution.
7. UAC cannot be bypassed.
8. Credentials cannot be collected.
9. Unknown applications cannot be launched.
10. Foreground window is verified before physical input.
11. Post-action state is always re-observed.
12. All resources have deterministic cleanup.
13. Every physical action is auditable.
14. Unknown or ambiguous state fails closed.

---

# 26. FINAL ENGINE CONTRACT

The Computer Control subsystem SHALL:

- control real Windows applications
- use UIA semantic interactions first
- manage Win32 process/window lifecycle
- resolve HWNDs deterministically
- stabilize foreground focus
- use an exclusive desktop mutex
- detect and freeze on user interference
- provide controlled keyboard/mouse fallback
- manage clipboard safely
- detect secure desktop/UAC states
- refuse privilege escalation
- integrate with vision only as a fallback proposal path
- re-observe after actions
- expose verification evidence
- persist observations and audit events
- clean up Win32/COM resources
- support bounded cancellation/timeouts
- remain independently testable

The subsystem SHALL NOT:

- bypass UAC
- manipulate credential prompts
- harvest passwords
- bypass CAPTCHA
- pretend user-mode hooks can block unsupported kernel-secure input sequences
- fight human users for focus
- blindly click coordinates
- invoke stale UIA elements
- launch arbitrary executables from model output
- bypass the desktop mutex
- leak clipboard contents
- silently continue through secure-desktop boundaries
- treat a vision prediction as verified OS state

---

# 27. OUTPUT QUALITY BAR

The generated `12_COMPUTER_CONTROL.md` must be:

- exhaustive
- production-grade
- Windows-specific
- implementation-ready
- deterministic
- security-focused
- concurrency-safe
- resource-safe
- audit-ready
- compatible with SyncNode

Do not produce:

- generic RPA tutorials
- generic computer-use explanations
- marketing language
- vague recommendations
- unsafe automation tricks
- pseudo-code presented as implementation
- undefined classes
- placeholder methods
- `TODO`
- `TBD`
- `pass`
- unexplained magic constants
- cloud-dependent architecture
- unsupported claims about Windows interception capabilities

Use throughout:

- Pydantic v2
- Python Protocols
- ctypes/comtypes
- Win32 API signatures
- UIA pattern wrappers
- deterministic state machines
- Mermaid diagrams
- coordinate equations
- resource locking
- security interlocks
- observation hashing
- SQL persistence examples
- failure taxonomies
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
12_COMPUTER_CONTROL.md
```
