# PROMPT: Generate `COMPUTER_RUNTIME.md` Technical Specification

You are a **Principal Systems Engineer and Windows Internals Specialist** specializing in:

- Windows 10/11 internals
- Win32 process and window management
- Windows UI Automation (UIA)
- COM / STA automation
- accessibility-tree driven computer control
- deterministic desktop automation
- safe keyboard/mouse fallback mechanisms
- desktop/session isolation
- fail-closed operating-system safety boundaries
- local-first / on-premise agentic runtime infrastructure

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, production-grade, implementation-ready technical specification** titled:

> `COMPUTER_RUNTIME.md`

This document governs the **SyncNode Windows Computer Runtime Subsystem**: the deterministic execution layer that translates approved semantic computer-action requests into real Windows application operations, using Windows UI Automation as the primary interaction mechanism and tightly controlled physical input simulation as a secondary fallback.

The Computer Runtime must operate against the **actual Windows desktop**, not a simulated environment.

It integrates with:

- Agent Runtime / Computer Agent
- Planner
- Tool Registry
- Context Engine
- Token Management
- Vision / Multimodal subsystem
- Browser Runtime
- Document Runtime
- Policy / Approval
- Verification / Recovery
- Audit / Telemetry
- `computer_observations`
- `audit_events`

The subsystem must be designed for **real-world desktop execution** where the system can visibly:

- launch applications
- focus windows
- inspect accessibility trees
- invoke buttons
- type text
- save documents
- navigate application UI
- recover from UI changes
- verify resulting state

At the same time, it must be safety-bounded and must never silently escalate privileges or continue automated input while a human is actively interfering with the desktop.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary architectural source of truth.

Before writing the final specification:

1. Read the complete `idea.md`.
2. Extract:
   - Computer Runtime responsibilities
   - Windows UI Automation requirements
   - browser/document interaction boundaries
   - desktop locking requirements
   - approval requirements
   - security restrictions
   - observation persistence
   - run/step integration
   - phase-1 scope
   - cancellation/recovery semantics
3. Preserve existing SyncNode terminology.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud dependencies.
6. Do not assume administrator privileges.
7. Do not design unrestricted shell access.
8. Do not design UAC bypass, CAPTCHA bypass, credential harvesting, or privileged desktop control.
9. Where a low-level Windows detail is not specified, make a concrete engineering decision and mark it:
   > **Implementation Decision**
10. Clearly distinguish:
   - canonical OS observation
   - semantic target resolution
   - UIA action
   - visual fallback
   - low-level input fallback
   - user interference
   - approval state
   - verification evidence
   - persisted telemetry

The final document must be detailed enough for another engineer to implement the subsystem without needing another architecture document.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & OPERATING PHILOSOPHY

Define the exact boundary:

```text
Computer Agent
      ↓
Tool Registry
      ↓
Computer Runtime
      │
      ├── Process Manager
      ├── Window Manager
      ├── UIA Engine
      ├── Focus Stabilizer
      ├── Desktop Mutex
      ├── Input Engine
      ├── Clipboard Bridge
      ├── Security Interlocks
      ├── Observation Capture
      └── Verification Hooks
      │
      ▼
Windows 10/11 Desktop
```

The Computer Runtime SHALL own:

- process launching/tracking
- window discovery
- focus management
- UIA tree inspection
- semantic element resolution
- supported-pattern invocation
- bounded keyboard/mouse fallback
- clipboard bridge
- user-interference detection
- desktop mutex
- secure-desktop detection
- observation capture
- physical-action telemetry
- deterministic post-action re-observation hooks

The Computer Runtime SHALL NOT own:

- task planning
- intent extraction
- model routing
- token accounting
- final policy approval
- arbitrary tool authorization
- autonomous privilege escalation
- verification semantics beyond collecting deterministic evidence

---

# 1.1 Core safety invariants

### Semantic-first control

Interaction priority:

```text
1. UI Automation semantic control
2. Application-specific adapter
3. Browser/Document specialized runtime
4. Vision-assisted semantic localization
5. Low-level coordinate/input simulation
```

Coordinates are never the canonical representation of a target.

---

### Desktop mutex

Only one agent may control the same physical desktop session at a time.

Use a system-wide mutex/resource lock such as:

```text
syncnode_desktop_control_mutex
```

or a scoped equivalent:

```text
syncnode:desktop:{machine_id}:{session_id}
```

---

### User interference freeze

If the human physically changes:

- mouse position
- keyboard state
- active window
- desktop focus

during autonomous interaction, the runtime must immediately enter:

```text
USER_INTERRUPTED
```

or:

```text
INPUT_FROZEN
```

according to the state machine.

Automated input must stop.

The runtime must:

```text
freeze input
→ capture current state
→ invalidate stale target handles
→ re-observe
→ require deterministic resume conditions
```

---

### Secure desktop boundary

If the active desktop switches to:

- Winlogon
- credential UI
- UAC consent
- secure desktop

the runtime must stop.

Required terminal security event:

```text
SEC_UAC_RESTRICTED
```

The runtime must never attempt to manipulate secure-desktop prompts.

---

# 1.2 Required subsystem topology

Include a detailed Mermaid and/or ASCII sequence diagram:

```text
Step Request
    ↓
Validate Request
    ↓
Acquire Desktop Mutex
    ↓
Resolve Target Window
    ↓
Stabilize Foreground Focus
    ↓
Refresh UIA Tree
    ↓
Find Semantic Element
    ↓
[UIA Pattern Available?]
     /         \
   YES          NO
    │            │
    ▼            ▼
Invoke Pattern  Application Adapter /
                Vision Bridge
                     ↓
              [Target Resolved?]
                  /       \
                YES        NO
                 │          │
                 ▼          ▼
              Input     Fail Closed
              Fallback
                 │
                 ▼
          Re-observe Window/UI
                 ↓
         Verify Immediate State
                 ↓
        Persist Observation
                 ↓
        Release Desktop Mutex
                 ↓
              Result
```

---

# 2. WINDOWS PROCESS & APPLICATION LIFECYCLE MANAGER

Define a process/application lifecycle manager based on non-elevated Windows process execution.

---

## 2.1 Process launch

Support:

- `CreateProcessW`
- Python `subprocess`
- existing application adapters

Processes must launch without elevation unless the source architecture explicitly permits otherwise.

Define a typed launch contract containing:

```text
executable
arguments
working_directory
environment_overrides
timeout
expected_window_title
expected_window_class
expected_process_name
```

Validate:

- executable path
- working directory
- allowed roots / approved application identities
- argument size
- environment injection policy

Do not blindly pass model-generated shell strings to a shell.

Prefer direct argument vectors or Win32 process creation.

---

# 2.2 Win32 process handles

Define safe handle lifecycle:

```text
CreateProcessW
→ retain process/thread handles
→ capture PID
→ monitor lifetime
→ close owned handles
```

Use `CloseHandle` exactly once per owned handle.

Define behavior for:

- process exits early
- process crashes
- access denied
- already-running application
- multiple matching processes
- process tree discovery

---

# 2.3 HWND resolution

Implement top-level window enumeration through:

```text
EnumWindows
```

Filter using:

- process ID
- visibility
- title
- class name
- owned/transient windows
- window styles
- active/foreground state

Provide typed models for:

```text
HWND
PID
window title
class name
rectangle
visibility
enabled state
process identity
```

---

# 2.4 Multi-window applications

Handle applications such as Word/Excel/browser families that may have:

- multiple top-level windows
- splash screens
- modal dialogs
- child windows
- hidden helper windows

Define deterministic window selection:

```text
exact PID
→ visible
→ expected class
→ title match
→ foreground
→ stable HWND
```

Use stable tie-breaking if multiple windows remain.

---

# 2.5 Application teardown

Required sequence:

```text
request graceful close
→ WM_CLOSE
→ wait bounded timeout
→ observe process/window state
→ terminate only if explicitly policy-permitted
```

Forceful termination must require an explicit policy flag.

Never terminate arbitrary unrelated processes.

---

# 3. WINDOWS UI AUTOMATION ENGINE

Define a full Windows UIA subsystem.

The implementation may use:

- `comtypes`
- Windows COM interfaces
- another explicit local UIA binding

but the specification must provide concrete signatures and data handling.

---

# 3.1 COM / STA initialization

Define:

```text
CoInitializeEx(..., COINIT_APARTMENTTHREADED)
```

for threads performing UIA COM operations.

Specify:

- one COM initialization lifecycle per thread
- matching `CoUninitialize`
- thread affinity
- apartment violations
- cleanup on worker termination

Do not move COM-bound UIA objects across threads without an explicitly supported marshaling strategy.

---

# 3.2 `IUIAutomation` acquisition

Provide a complete reference implementation for creating the UI Automation client.

Include:

- COM initialization
- automation object creation
- error handling
- COM exception normalization
- teardown

No pseudo-code-only examples.

---

# 3.3 Tree traversal

Support:

```text
TreeScope_Element
TreeScope_Children
TreeScope_Descendants
```

Define:

- maximum depth
- maximum node count
- cancellation check
- time budget
- lazy traversal
- visibility filtering
- interactive-control preference

Suppress non-semantic layout containers where safe.

Retain relevant metadata:

```text
AutomationId
Name
ControlType
ClassName
IsEnabled
IsOffscreen
BoundingRectangle
ProcessId
RuntimeId
supported patterns
```

---

# 3.4 UIA cache requests

Define how `IUIAutomationCacheRequest` is used to fetch common properties and patterns efficiently.

Include:

- cache request construction
- requested properties
- requested patterns
- traversal mode
- stale-cache behavior
- cache refresh

The final specification should quantify why cache requests reduce repeated cross-process COM calls.

---

# 3.5 Semantic locator resolution

Define a resolver hierarchy:

```text
AutomationId
→ Name + ControlType
→ AutomationId + ControlType
→ ClassName + ControlType
→ ancestry/path hints
→ application adapter
→ visual fallback
```

Do not use raw coordinates as the primary canonical target.

Define `LocatorQuery` with bounded fields.

Example:

```python
class LocatorQuery(BaseModel):
    automation_id: str | None
    name: str | None
    control_type: str | None
    class_name: str | None
    parent_automation_id: str | None
    required_enabled: bool
```

---

# 3.6 Control pattern execution

Provide concrete behavior for:

### Invoke

Buttons/links:

```text
IUIAutomationInvokePattern::Invoke
```

### Value

Text entry:

```text
IUIAutomationValuePattern::SetValue
```

### Toggle

Checkboxes:

```text
IUIAutomationTogglePattern::Toggle
```

### Selection

Radio/list items:

```text
IUIAutomationSelectionItemPattern::Select
```

### Expand/Collapse

Dropdowns:

```text
IUIAutomationExpandCollapsePattern
```

### Scroll

Scrollable content:

```text
IUIAutomationScrollItemPattern
```

Also define fallback handling when a pattern is unsupported.

---

# 3.7 Stale element handling

UIA references can become invalid.

Required sequence:

```text
COM/UIA failure
→ classify stale reference
→ discard object
→ refresh active window
→ reacquire UIA root
→ re-resolve semantic target
→ retry once
→ fail if still unavailable
```

Never repeatedly invoke a stale COM object.

---

# 4. ACTIVE WINDOW MANAGEMENT & DESKTOP MUTEX

Define a strict focus-control subsystem.

---

# 4.1 Foreground window detection

Use:

```text
GetForegroundWindow
```

and verify:

- expected HWND
- expected process
- expected application
- expected title/class identity

before every keyboard input sequence.

---

# 4.2 Focus stabilization

Define a deterministic sequence:

```text
candidate window
→ verify visible/enabled
→ BringWindowToTop
→ SetForegroundWindow
→ observe foreground
→ optionally AttachThreadInput when explicitly required
→ re-observe
→ timeout/fail
```

Do not rely on a single `SetForegroundWindow` call.

Document Windows foreground restrictions and the limits of thread-input attachment.

---

# 4.3 Desktop mutex

Implement a system-level lock.

Requirements:

- exclusive ownership
- lease/timeout
- owner run ID
- owner step ID
- machine/session identity
- safe release
- recovery after worker death

The lock must prevent:

- competing keystrokes
- focus thrashing
- simultaneous mouse control
- cross-agent race conditions

---

# 4.4 Human interference detection

Implement a detection subsystem based on local Windows input observation.

Detect:

- physical mouse movement
- physical keyboard activity
- foreground window changes

The exact low-level hook mechanism may use:

```text
WH_MOUSE_LL
WH_KEYBOARD_LL
```

where appropriate.

Define a configurable movement threshold such as:

```text
50 px
```

but make it configuration-driven.

Required state:

```text
AUTOMATION_ACTIVE
→ USER_INTERFERENCE_DETECTED
→ INPUT_FROZEN
→ STATE_REOBSERVED
→ RESUME_ALLOWED
```

Resume must require explicit deterministic conditions.

---

# 4.5 Emergency abort

Define a global emergency stop mechanism.

Example configuration:

```text
Ctrl+Shift+Escape
```

or another configured sequence.

On trigger:

```text
stop input generation immediately
→ cancel active step
→ release safe resources
→ preserve observation
→ persist audit event
→ transition to ABORTED
```

The emergency mechanism itself must not depend on the active application remaining responsive.

---

# 5. COORDINATE MAPPING & INPUT SIMULATION FALLBACK

Coordinate input is secondary.

The specification must define strict admission rules.

---

# 5.1 `SendInput`

Provide concrete Win32 ctypes structures for:

```text
INPUT
MOUSEINPUT
KEYBDINPUT
HARDWAREINPUT
```

and the signature for:

```text
SendInput
```

Explain:

- keyboard input
- mouse movement
- mouse button events
- Unicode input
- scan codes
- extra-info field

---

# 5.2 Coordinate normalization

Use the required formula:

```text
dx = round(X × 65535 / W_virtual)
dy = round(Y × 65535 / H_virtual)
```

Define exact handling for:

- negative virtual-screen coordinates
- multi-monitor layouts
- virtual screen origin
- zero-sized rectangles
- clamping
- off-screen targets

Never click a coordinate unless it was freshly derived from a verified target observation.

---

# 5.3 DPI awareness

Define interaction with:

```text
GetDpiForWindow
```

and/or process/thread DPI-awareness APIs.

Handle:

- 100%
- 125%
- 150%
- mixed-DPI multi-monitor systems

The coordinate transform must be derived from the current observed window/monitor configuration, not a hardcoded scale.

---

# 5.4 Obscured-target checks

Before coordinate fallback:

1. re-observe target bounds
2. verify window is foreground
3. verify enabled/visible
4. verify bounding rectangle intersects intended click point
5. verify target is not stale
6. verify no conflicting modal dialog is active
7. verify user has not interfered

Then inject input.

---

# 5.5 Humanized trajectories

Do **not** design randomized movement to bypass anti-automation systems or evade security controls.

For ordinary UX simulation where needed, use deterministic, bounded trajectories for stability and reproducibility.

Example:

```text
Bezier interpolation
with fixed control points derived from start/end
```

No random micro-jitter unless explicitly needed for legitimate hardware stabilization and documented as deterministic/configurable.

---

# 6. TEXT ENTRY, KEYSTROKE INJECTION & CLIPBOARD BRIDGE

Define safe text-entry methods.

---

# 6.1 Virtual-key translation

Support:

```text
VkKeyScanExW
```

and/or explicit `KEYEVENTF_UNICODE` injection.

Define:

- modifiers
- Ctrl
- Shift
- Alt
- Win
- function keys
- Unicode text
- key-down/key-up symmetry

Never leave a modifier key held across an exception.

---

# 6.2 Atomic keystroke transaction

A keyboard operation must behave as:

```text
precondition focus verified
→ acquire input transaction
→ key down
→ key sequence
→ key up
→ verify modifier release
→ re-observe
```

If an exception occurs midway, execute deterministic cleanup.

---

# 6.3 Clipboard bridge

For large text:

```text
capture existing clipboard
→ acquire clipboard lock
→ write CF_UNICODETEXT
→ focus target
→ Ctrl+V
→ verify resulting text/state
→ restore original clipboard if possible
```

Handle `OpenClipboard` contention with bounded retries.

Define:

```text
retry_n = min(base_delay × 2^n, max_delay)
```

with cancellation checks.

Never permanently destroy user clipboard contents when restoration is possible.

---

# 6.4 Clipboard privacy

Do not persist raw clipboard data to logs or database.

Telemetry should contain:

```text
payload_hash
payload_size
operation_status
target_application
```

unless explicit policy authorizes content persistence.

---

# 7. SECURITY INTERLOCKS, UAC & OPERATING BOUNDARIES

This section must be extremely concrete.

---

# 7.1 Secure desktop detection

Define local probing using:

```text
OpenInputDesktop
GetUserObjectInformation
```

or equivalent supported Win32 mechanisms.

Detect:

- default interactive desktop
- Winlogon desktop
- secure credential UI
- UAC consent desktop

Any transition away from the supported interactive desktop requires immediate input suspension.

---

# 7.2 UAC / privileged boundary

Required sequence:

```text
privileged/secure desktop detected
→ freeze input
→ capture observation metadata
→ emit SEC_UAC_RESTRICTED
→ abort/stop step
```

Never:

- bypass UAC
- press administrator approval buttons
- manipulate credential prompts
- capture credentials
- attempt to switch secure desktops

---

# 7.3 Restricted key combinations

Explicitly define policy for blocking/suppressing automation attempts involving:

```text
Ctrl+Alt+Del
Win+L
secure attention sequence
privilege escalation shortcuts
```

Clarify which inputs can actually be blocked from user mode on Windows.

Do not falsely claim that an ordinary user-mode hook can universally intercept kernel-reserved secure attention sequences.

The implementation must fail closed rather than pretending to control unsupported key combinations.

---

# 7.4 Application boundaries

Define approved target policies for:

- applications
- process identities
- window classes
- executable paths

Unknown or unexpected foreground applications must cause re-observation and, where required, suspension.

---

# 8. INTEGRATION WITH VISION & BROWSER SUBSYSTEMS

Define the exact bridge.

---

## 8.1 Vision fallback

When UIA cannot resolve a target:

```text
UIA lookup failure
→ capture bounded screenshot
→ VISION_MULTIMODAL resolver
→ semantic target hypothesis
→ deterministic coordinate verification
→ input fallback only if policy permits
```

The vision model may propose a target.

The Computer Runtime must still verify:

- target bounds
- foreground window
- application identity
- visibility
- current state

before executing input.

Vision coordinates are never canonical state.

---

# 8.2 Browser coexistence

Define interaction with browser runtime:

```text
Word foreground
→ Word interaction
→ Word verification
→ browser target requested
→ desktop focus transfer
→ browser verification
→ Playwright owns web interaction where possible
→ desktop input only for browser-level controls when required
```

Prefer Playwright/DOM/accessibility interactions over physical browser clicks.

The Computer Runtime should act as the desktop-level adapter around the browser runtime, not replace it.

---

# 9. TELEMETRY, OBSERVATION PERSISTENCE & AUDIT

Every physical interaction must generate auditable observation/action records.

---

# 9.1 `computer_observations`

Align with `idea.md`.

Capture as appropriate:

```text
run_step_id
machine/session identity
timestamp
active window
process identity
HWND
UI tree snapshot
focused control
action metadata
observation hash
parent observation hash
```

Store UI tree as structured JSON/JSONB where defined by the source architecture.

---

# 9.2 Observation hashing

Provide deterministic SHA-256 hashing:

```text
canonical_json(observation)
→ UTF-8
→ SHA-256
```

Use stable:

- key ordering
- list ordering
- normalized strings
- omitted-null policy

The observation hash must identify the exact logical observation representation stored.

---

# 9.3 `audit_events`

Define events:

```text
computer.window_launched
computer.window_focused
computer.uia_lookup
computer.uia_invoked
computer.uia_value_set
computer.clipboard_used
computer.input_simulated
computer.user_interrupted
computer.secure_desktop_detected
computer.uac_restricted
computer.emergency_abort
computer.window_closed
computer.observation_captured
```

Each event must include:

- event ID
- run ID
- run_step_id
- trace ID
- machine/session identity
- timestamp
- action/result
- observation hash where applicable
- sanitized metadata

Never log raw credentials or unrestricted clipboard contents.

---

# 10. COMPLETE DATA CONTRACTS & INTERFACE DEFINITIONS

Provide complete Pydantic v2 models and Python Protocol interfaces.

---

## 10.1 `WindowContext`

Required fields:

```text
machine_id
session_id
process_id
hwnd
window_title
class_name
executable
visible
enabled
foreground
bounding_rect
dpi_scale
captured_at
observation_hash
```

---

## 10.2 `UIANode`

Required fields:

```text
runtime_id
automation_id
name
control_type
class_name
bounding_box
supported_patterns
is_enabled
is_offscreen
is_visible
is_focused
process_id
parent_runtime_id
```

---

## 10.3 `InputPayload`

Required fields:

```text
action_type
coordinates
text_buffer
key_sequence
button
duration_ms
inter_key_delay_ms
source
target_observation_hash
```

Action types:

```text
click
double_click
right_click
move
type_text
key_combination
drag_and_drop
scroll
```

---

## 10.4 `ComputerRuntimeProtocol`

Define:

```python
class ComputerRuntimeProtocol(Protocol):
    async def launch_application(
        self,
        request: LaunchApplicationRequest,
        cancellation: CancellationToken,
    ) -> ProcessContext:
        ...

    async def find_window(
        self,
        query: WindowQuery,
        cancellation: CancellationToken,
    ) -> WindowContext:
        ...

    async def find_element(
        self,
        window: WindowContext,
        query: LocatorQuery,
        cancellation: CancellationToken,
    ) -> UIANode:
        ...

    async def invoke_element(
        self,
        target: UIANode,
        action: UIAAction,
        cancellation: CancellationToken,
    ) -> ActionResult:
        ...

    async def simulate_input(
        self,
        payload: InputPayload,
        cancellation: CancellationToken,
    ) -> ActionResult:
        ...

    async def acquire_desktop_mutex(
        self,
        request: DesktopLockRequest,
        cancellation: CancellationToken,
    ) -> DesktopLockLease:
        ...

    async def detect_user_interference(
        self,
        session: DesktopSession,
        cancellation: CancellationToken,
    ) -> UserInterferenceState:
        ...
```

Improve signatures where required, but preserve clear separation between observation, control, locking, and safety checks.

---

# 11. REQUIRED SUPPORTING SCHEMAS

Also define complete models for:

- `ProcessContext`
- `LaunchApplicationRequest`
- `WindowQuery`
- `DesktopSession`
- `DesktopLockRequest`
- `DesktopLockLease`
- `LocatorQuery`
- `UIAAction`
- `UIAPattern`
- `UIAObservation`
- `InputPayload`
- `ClipboardSnapshotMetadata`
- `ClipboardWriteRequest`
- `UserInterferenceState`
- `FocusState`
- `SecureDesktopState`
- `VerificationEvidence`
- `ActionResult`
- `ComputerObservation`
- `AuditEvent`
- `ComputerRuntimeError`

No undefined types may appear in code examples.

---

# 12. STATE MACHINES

Define explicit state machines.

---

## 12.1 Computer action state machine

```text
REQUESTED
   ↓
LOCK_ACQUIRED
   ↓
TARGET_RESOLVED
   ↓
FOCUS_STABILIZED
   ↓
ACTION_READY
   ↓
INPUT_DISPATCHED
   ↓
REOBSERVING
   ↓
VERIFIED
```

Alternative states:

```text
WAITING_RESOURCE
USER_INTERRUPTED
SECURE_DESKTOP_BLOCKED
FAILED
ABORTED
```

---

## 12.2 Desktop lock state machine

```text
UNLOCKED
→ ACQUIRING
→ LOCKED
→ RELEASING
→ UNLOCKED
```

Failure:

```text
ACQUIRING → TIMEOUT
LOCKED → OWNER_CRASHED → RECOVERY
```

Define owner identity and fencing semantics to prevent stale workers from releasing/reusing another worker's lock.

---

## 12.3 Window lifecycle

```text
UNKNOWN
→ DISCOVERED
→ VALIDATED
→ FOREGROUNDED
→ ACTIVE
→ CLOSING
→ CLOSED
```

Failure state:

```text
STALE
```

Stale windows must be re-resolved.

---

# 13. FAILURE MODES & ERROR TAXONOMY

Define a complete error catalog:

```text
WINDOW_NOT_FOUND
MULTIPLE_WINDOWS_AMBIGUOUS
PROCESS_LAUNCH_FAILED
PROCESS_EXITED_EARLY
WINDOW_ACTIVATION_FAILED
FOCUS_STABILIZATION_FAILED
UIA_INITIALIZATION_FAILED
UIA_ELEMENT_NOT_FOUND
UIA_ELEMENT_AMBIGUOUS
UIA_PATTERN_UNSUPPORTED
UIA_STALE_ELEMENT
UIA_COM_ERROR
DESKTOP_MUTEX_TIMEOUT
USER_INTERFERENCE_DETECTED
INPUT_FROZEN
INPUT_DISPATCH_FAILED
CLIPBOARD_BUSY
CLIPBOARD_WRITE_FAILED
SEC_UAC_RESTRICTED
SECURE_DESKTOP_DETECTED
UNSUPPORTED_INPUT
TARGET_OBSERVATION_STALE
VISION_TARGET_UNVERIFIED
APPLICATION_POLICY_VIOLATION
PROCESS_POLICY_VIOLATION
ACTION_VERIFICATION_FAILED
EMERGENCY_ABORT
COMPUTER_RUNTIME_TIMEOUT
```

Each error must include:

- stable code
- severity
- retryability
- run ID
- step ID
- machine/session
- trace ID
- sanitized reason
- recovery action

Never expose secrets.

---

# 14. RESILIENCE & RECOVERY

Define deterministic recovery paths.

---

## 14.1 Stale UI state

```text
stale target
→ invalidate target
→ reobserve
→ refocus
→ reacquire UIA
→ resolve target again
→ retry once
→ fail
```

---

## 14.2 Window disappeared

```text
expected HWND gone
→ check process state
→ enumerate replacement windows
→ compare trusted identity
→ select replacement only if deterministic
→ otherwise fail
```

---

## 14.3 Application crashed

```text
detect process exit
→ capture observation
→ mark application unavailable
→ persist failure
→ notify Planner/Recovery
```

Restart only if the plan/policy explicitly permits application relaunch.

---

## 14.4 User interference

```text
human input
→ freeze automation
→ preserve state
→ release immediate input transaction
→ reobserve
→ await deterministic resume condition
```

Do not fight the user for focus.

---

# 15. PROCESS / WINDOW SAFETY & HANDLE MANAGEMENT

Define handle ownership tables.

Every handle must have:

```text
creator
owner
lifetime
cleanup action
```

Provide concrete wrappers for Win32 handles.

Use context-manager style ownership where possible.

No leaked:

- process handles
- thread handles
- HWND references
- COM objects
- hook handles
- mutex handles

---

# 16. PERFORMANCE & CONCURRENCY

Define measurable engineering targets for:

- process launch tracking
- window enumeration
- UIA initialization
- UIA lookup
- cached UIA retrieval
- focus stabilization
- input dispatch
- observation capture
- desktop lock acquisition

Define limits:

```text
max_ui_tree_depth
max_ui_tree_nodes
max_action_duration_ms
max_focus_retries
max_stale_element_retries
max_clipboard_retries
max_process_launch_wait_ms
max_window_search_ms
```

All constants must be exposed through typed configuration.

---

# 16.1 Concurrency rules

The subsystem must support concurrent non-desktop work but serialize physical desktop control.

Examples:

```text
Document extraction ─┐
RAG search ──────────┼→ concurrent
Browser DOM parsing ─┘

Computer UI control → exclusive desktop mutex
```

UIA observation may be parallelized where thread/apartment rules safely permit it, but control of one desktop session remains exclusive.

---

# 17. REFERENCE PACKAGE STRUCTURE

Provide a concrete package structure:

```text
syncnode/
└── computer_runtime/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── runtime.py
    ├── processes.py
    ├── windows.py
    ├── uia/
    │   ├── __init__.py
    │   ├── com.py
    │   ├── automation.py
    │   ├── traversal.py
    │   ├── locator.py
    │   ├── cache.py
    │   └── patterns.py
    ├── focus.py
    ├── mutex.py
    ├── interference.py
    ├── input/
    │   ├── __init__.py
    │   ├── send_input.py
    │   ├── keyboard.py
    │   ├── mouse.py
    │   └── clipboard.py
    ├── security.py
    ├── vision_bridge.py
    ├── browser_bridge.py
    ├── observations.py
    ├── verification.py
    ├── telemetry.py
    ├── persistence.py
    ├── errors.py
    └── tests/
        ├── test_processes.py
        ├── test_windows.py
        ├── test_uia.py
        ├── test_locator.py
        ├── test_focus.py
        ├── test_mutex.py
        ├── test_interference.py
        ├── test_send_input.py
        ├── test_keyboard.py
        ├── test_clipboard.py
        ├── test_security.py
        ├── test_observations.py
        ├── test_persistence.py
        └── test_determinism.py
```

Adapt to the architecture in `idea.md`.

---

# 18. REQUIRED COMPLETE IMPLEMENTATION EXAMPLES

The generated `COMPUTER_RUNTIME.md` MUST contain actual Python 3.12+ implementations for at least:

1. Win32 `CreateProcessW` signature
2. safe application launch
3. process-handle wrapper
4. `EnumWindows` signature and enumeration
5. HWND filtering
6. `GetForegroundWindow` usage
7. focus stabilization
8. desktop mutex acquisition
9. COM STA initialization
10. UIA client creation
11. UIA tree traversal
12. UIA locator matching
13. UIA cache-request construction
14. InvokePattern execution
15. ValuePattern execution
16. TogglePattern execution
17. SelectionItemPattern execution
18. stale UIA reference recovery
19. `SendInput` ctypes structures
20. normalized mouse input calculation
21. Unicode keyboard input
22. modifier-safe key sequences
23. clipboard capture/write/restore
24. user-interference detection architecture
25. secure-desktop detection
26. emergency abort handling
27. observation canonicalization + SHA-256
28. audit event generation
29. complete ComputerRuntime orchestration
30. bounded teardown and cleanup

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- fully type annotated
- compatible with Windows 10/11
- explicit about optional Windows-specific dependencies
- syntactically complete
- executable with the documented dependencies
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder methods
- free of unexplained magic constants

Where a Windows API is unsafe to demonstrate directly, provide a safe wrapper and explicit precondition checks rather than a raw unsafe call.

---

# 19. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- Win32 integration tests
- UIA integration tests
- desktop-session tests
- process lifecycle tests
- focus tests
- mutex/concurrency tests
- interference tests
- clipboard tests
- security tests
- deterministic replay tests
- failure-recovery tests
- observation persistence tests

Mandatory security tests:

### UIA-first enforcement

A semantic target with a supported UIA pattern must never immediately fall back to coordinate clicking.

### Stale-target safety

A stale UIA object must never be invoked.

### Desktop isolation

Two computer agents cannot simultaneously own the same desktop mutex.

### Human-interference safety

Detected physical user interaction immediately freezes automated input.

### Secure-desktop safety

UAC/Winlogon/secure desktop detection always prevents automated control.

### Coordinate safety

Coordinate input requires a fresh verified observation and current foreground-window validation.

### Clipboard safety

Clipboard restoration is attempted after every successful temporary write.

### Handle safety

Owned Win32 handles are closed exactly once.

### Determinism

Identical:

- target observation
- locator
- application state
- runtime configuration

must produce identical target resolution and control-selection results.

### Auditability

Every physical action creates the required observation/audit records.

---

# 20. DATABASE INTEROPERABILITY

Align explicitly with:

```text
computer_observations
audit_events
```

and any related schema from `idea.md`.

For `computer_observations`, define mapping for:

```text
run_step_id
application/process identity
window identity
UI tree
action metadata
observation timestamp
observation hash
parent observation hash
```

For `audit_events`, define event-to-column mapping.

If additional columns are required but not specified by `idea.md`, introduce them under:

> Implementation Decision — Computer Runtime Persistence Extensions

Do not silently invent incompatible schema.

---

# 21. INTEGRATION WITH COMPUTER AGENT

Define the exact interaction:

```text
Planner
  ↓
Computer Step
  ↓
Agent Runtime
  ↓
Computer Runtime Tool
  ↓
Desktop Mutex
  ↓
Observe
  ↓
Resolve
  ↓
Act
  ↓
Re-observe
  ↓
Return ActionResult + Observation
```

The Computer Runtime executes approved semantic operations.

It does not decide whether the overall task is allowed.

---

# 22. INTEGRATION WITH CONTEXT ENGINE & VERIFICATION

After each state-changing action:

```text
Action
  ↓
Immediate Observation
  ↓
Context Engine delta
  ↓
Verifier
```

The runtime must expose:

- current window state
- focused control
- UI delta
- observation hash
- action result
- timestamps

The model may interpret the observation, but verified OS state remains authoritative.

---

# 23. REFERENCE END-TO-END EXAMPLES

Use concrete real-desktop workflows.

---

## Example A — Click Save in Word

```text
Computer step:
"Click Save"
```

Show:

```text
desktop mutex
→ locate Word HWND
→ focus stabilization
→ UIA lookup:
   Name = Save
   ControlType = Button
→ InvokePattern
→ reobserve
→ verify document state
→ persist observation/audit
→ release mutex
```

Do not use coordinates when UIA succeeds.

---

## Example B — UIA failure

```text
Save button unavailable through UIA
```

Show:

```text
refresh UIA
→ application adapter
→ bounded vision fallback
→ verified coordinate
→ SendInput
→ reobserve
→ verify
```

The vision result remains a proposal until runtime verification succeeds.

---

## Example C — Human interruption

```text
Agent is about to type
→ user moves mouse
```

Required:

```text
input frozen
→ observation captured
→ stale target invalidated
→ focus rechecked
→ execution paused
```

---

## Example D — UAC prompt

```text
Foreground transitions to secure desktop
```

Required:

```text
stop
→ SEC_UAC_RESTRICTED
→ persist audit
→ release mutex
→ fail step
```

---

## Example E — Hybrid Word → Browser workflow

```text
Word document creation
→ Word verification
→ release desktop lock
→ browser step
→ acquire desktop lock
→ browser window focus
→ Playwright handles DOM interaction
→ desktop runtime handles only browser-level window state
→ release
```

---

# 24. SECURITY MODEL

Explicitly address:

- desktop control races
- stale HWNDs
- stale UIA objects
- focus hijacking
- human interference
- UAC
- Winlogon
- secure desktop
- credential prompts
- coordinate injection
- malicious target descriptions
- process impersonation
- unexpected foreground applications
- clipboard leakage
- keyboard modifier leakage
- orphaned mutexes
- leaked Win32 handles
- unauthorized application launches
- window targeting ambiguity

Required guarantees:

1. UIA semantic control is preferred.
2. Raw coordinates are fallback only.
3. Every coordinate action is based on a fresh observation.
4. Desktop control is mutually exclusive.
5. Human interaction freezes automation.
6. Secure desktop blocks execution.
7. No UAC bypass is attempted.
8. No credentials are captured.
9. No arbitrary process is launched.
10. HWND/UIA identity is revalidated before sensitive input.
11. Every state-changing action is observed afterward.
12. All physical actions are auditable.
13. Resources are released during every terminal path.
14. Unknown/ambiguous target states fail closed.

---

# 25. PERFORMANCE & OPERATIONS

Define measurable targets for:

- UIA initialization latency
- UIA lookup latency
- cached traversal latency
- focus stabilization latency
- action dispatch latency
- observation capture latency
- desktop lock acquisition latency
- clipboard write latency
- process launch detection latency

Provide complexity analysis for:

```text
window enumeration      O(W)
tree traversal           O(N)
locator filtering        O(N)
stable target selection  O(N)
```

where:

- `W` = top-level windows
- `N` = observed UI nodes

Define configurable upper bounds for `W` and `N`.

---

# 26. FINAL ENGINE CONTRACT

The Computer Runtime SHALL:

- operate on the real Windows desktop
- use UIA as the primary control mechanism
- resolve semantic targets deterministically
- manage process/application lifecycles
- stabilize foreground focus
- enforce exclusive desktop control
- detect human interference
- freeze automation on user input
- provide bounded input simulation fallback
- manage clipboard safely
- detect secure desktop/UAC boundaries
- never perform privilege escalation
- integrate with vision only as a fallback proposal mechanism
- integrate with browser runtime without duplicating browser automation
- re-observe after state-changing actions
- hash and persist observations
- emit audit events
- manage Win32/COM resources safely
- support cooperative cancellation
- remain independently testable

The subsystem SHALL NOT:

- bypass UAC
- manipulate credential prompts
- harvest credentials
- bypass CAPTCHA
- simulate unsupported privileged secure-attention operations
- fight human users for focus
- blindly click arbitrary coordinates
- reuse stale UIA references
- launch arbitrary model-generated executables
- bypass the desktop mutex
- leak clipboard contents
- silently suppress security boundaries
- treat vision coordinates as verified state
- execute without observation/verification hooks

---

# 27. OUTPUT QUALITY BAR

The generated `COMPUTER_RUNTIME.md` must be:

- exhaustive
- production-grade
- Windows-specific
- implementation-ready
- safety-focused
- deterministic
- concurrency-safe
- resource-safe
- audit-friendly
- directly usable by another engineer

Do not produce:

- generic desktop automation tutorials
- generic RPA explanations
- marketing copy
- vague recommendations
- pseudo-code presented as production code
- undefined classes
- placeholder functions
- `TODO`
- `TBD`
- `pass`
- unexplained magic constants
- cloud-dependent architecture

Use throughout:

- Pydantic v2 schemas
- Python Protocols
- ctypes/comtypes signatures
- Win32 API examples
- UIA patterns
- Mermaid diagrams
- deterministic state machines
- resource-lock semantics
- security interlocks
- observation hashing
- audit schemas
- failure taxonomies
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
COMPUTER_RUNTIME.md
```
