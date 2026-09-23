# SyncNode — FRONTEND_UI_DESIGN_SYSTEM.md

## Sovereign AI Workbench — Premium Monochrome Electron Design System

> **Design directive:** Build SyncNode like a serious professional developer workstation, not like a generic AI SaaS dashboard.
>
> **Primary aesthetic:** black-first, monochrome, dense-but-breathable, quiet, precise, technical, editor-like.
>
> **North-star interaction:** the interface should feel at home beside tools such as OpenCode, VS Code, Zed, Cursor, Antigravity-style AI IDEs, Raycast, terminal workspaces, and professional desktop applications—while remaining distinctly SyncNode.
>
> **Core principle:** **less decoration, more information architecture; less dashboard, more workstation.**

---

## 0. READ THIS FIRST — NON-NEGOTIABLE IMPLEMENTATION CONTRACT

This document is the **visual and interaction authority for the Electron frontend** after the functional/frontend API documents.

The frontend must be implemented as a coherent design system, not as a collection of individually designed pages.

### Hard rules

1. **Frontend only.** Do not modify backend Python, backend schemas, backend routes, LangGraph logic, model routing, execution, tools, database, SSE event names, or backend contracts.
2. **REST + SSE only.** Treat the backend as the authoritative source of run state, agent state, tool state, verification state, artifacts, approvals, knowledge, and audit data.
3. **No fake AI activity.** Do not invent streamed reasoning, tool calls, verification, files, statuses, percentages, token counts, or success states for visual effect.
4. **No frontend-side mutation of backend truth.** UI optimistic state is allowed only for purely local presentation interactions. Run/task execution truth comes from API/SSE.
5. **Do not turn the app into a conventional SaaS dashboard.** The primary mental model is an **AI-native IDE/workbench**.
6. **No giant cards everywhere.** Use panes, rows, tabs, split views, compact surfaces, dividers, breadcrumbs, inline metadata, and contextual panels.
7. **No excessive gradients.** Subtle atmospheric lighting is allowed only where it reinforces hierarchy. The default interface is flat/low-chroma/monochrome.
8. **No rainbow AI effects.** Agent activity must not automatically become purple-blue-pink neon noise.
9. **No gratuitous glassmorphism.** Use opacity only when it improves depth or preserves a desktop/editor aesthetic.
10. **No oversized marketing typography inside the workbench.** Large type belongs primarily to splash/onboarding/empty states.
11. **Keyboard-first.** Every high-frequency workstation action needs a keyboard-accessible path.
12. **Desktop-first, Electron-native.** Window controls, command palette, split panes, drag handles, context menus, quick actions, and persistent workspace behavior matter.
13. **Motion is functional.** Animation should explain state changes, hierarchy, focus, progress, or navigation—not show off.
14. **Use the component ecosystem intelligently.** shadcn/ui + Base UI/Radix + Tailwind are the foundation; other open-source ecosystems are sources for specialized patterns, not permission to mix visual languages randomly.
15. **One visual grammar.** Components from different libraries must be normalized through SyncNode tokens before reaching product screens.
16. **Do not copy branded interfaces.** Reference developer-tool ergonomics and density, but keep SyncNode's own identity.
17. **Every screen needs loading, empty, active, success, failure, cancelled, disconnected, and permission/approval states where applicable.**
18. **Accessibility is part of the visual system, not a later retrofit.** Focus visibility, reduced motion, keyboard navigation, semantics, contrast, and readable hit targets are required.

---

# 1. PRODUCT VISUAL IDENTITY

## 1.1 Brand idea

**SyncNode** is a local intelligence workstation.

The product should communicate:

- local intelligence
- controlled automation
- engineering precision
- observable agents
- verified actions
- secure enterprise execution
- calm confidence
- technical depth without visual clutter

The visual language should therefore feel closer to:

```text
Professional IDE
+ terminal/workbench
+ AI operations console
+ document workspace
+ subtle cinematic launch experience
```

and much less like:

```text
Generic SaaS dashboard
+ marketing cards
+ neon AI gradients
+ floating blobs
+ decorative robot icons
```

---

## 1.2 Visual reference direction from the supplied screenshots

The supplied references establish the target mood:

- almost-black full-window background
- extremely restrained chrome
- compact top bars
- thin separators
- muted text hierarchy
- compact controls
- editor/terminal-like density
- generous negative space when the app is idle
- centered command/input composition on the splash/home experience
- workspace chrome around an active working surface
- minimal iconography
- very little visual noise
- emphasis on the content/state currently being worked on

Use the references as a **density and restraint reference**, not as a pixel-for-pixel imitation.

---

# 2. DESIGN SYSTEM ARCHITECTURE

## 2.1 Layer model

The frontend visual system should be built in this exact layered manner:

```text
Layer 0 — Platform
Electron window, titlebar, window controls, DPI, safe areas

Layer 1 — Design Tokens
Color, typography, spacing, radii, borders, shadows, motion, elevation

Layer 2 — Primitive Interaction
Base UI / Radix / shadcn primitives, keyboard behavior, focus handling

Layer 3 — Core SyncNode Components
Pane, rail, split view, command bar, activity row, timeline node, status chip, evidence row, artifact tile

Layer 4 — Workbench Patterns
Run header, agent timeline, tool execution row, verification row, approval sheet, artifact preview, desktop mirror, graph canvas

Layer 5 — Screens
Splash, Home, Intent, Active Run, Agents, Desktop, Timeline, Knowledge, Learning, Audit, Settings

Layer 6 — Experience Orchestration
Transitions, cross-pane synchronization, panel expansion, command palette, shortcuts, deep links, persisted workspace layout
```

Do not skip directly from a component library to screens.

---

# 3. COMPONENT ECOSYSTEM — USE IT AS A TOOLBOX, NOT A VISUAL JUNK DRAWER

The following ecosystem is intentionally broad. The implementation must **converge on one SyncNode design language** even when source components come from different projects.

## 3.1 Foundation — shadcn/ui

**Role:** primary application component source and copy/edit model.

Use for:

- Button
- Input
- Textarea
- Command
- Dialog
- Sheet
- Drawer
- Popover
- Dropdown Menu
- Context Menu
- Select
- Tabs
- Accordion
- Collapsible
- Tooltip
- Toast/Sonner integration
- Table
- Data Table
- Sidebar
- Resizable panes
- Scroll Area
- Breadcrumb
- Badge
- Skeleton
- Progress
- Toggle
- Checkbox
- Radio Group
- Switch
- Calendar/date controls where needed

shadcn/ui is particularly useful here because the component source can be owned and customized rather than treated as an untouchable black-box package. Official documentation currently describes it as open source/open code with copy-and-customize distribution, and its current ecosystem supports both Base UI and Radix foundations. citeturn203963search3turn203963search19

**Rule:** SyncNode's final components belong under the product's component layer. Do not scatter third-party imports through feature screens.

---

## 3.2 Base UI — preferred headless foundation for new custom primitives

**Role:** accessible, unstyled interaction primitives when shadcn does not cover a specialized workstation interaction cleanly.

Good candidates:

- complex menus
- comboboxes
- autocomplete
- nested dialogs
- context surfaces
- selection patterns
- advanced keyboard interactions
- custom command surfaces

Base UI is an open-source React component library focused on accessibility, performance, composability, and headless control. Its documentation also explicitly positions it as compatible with Tailwind and other styling systems. citeturn334311search0turn334311search4

**Design rule:** Base UI supplies behavior; SyncNode supplies appearance.

---

## 3.3 Radix UI — accessibility/behavior fallback and existing shadcn-compatible primitives

**Role:** use for existing Radix-based shadcn components already present or for cases where Radix offers the desired primitive and migrating would create unnecessary churn.

Excellent for:

- Dialog
- Alert Dialog
- Dropdown Menu
- Context Menu
- Popover
- Tabs
- Tooltip
- Scroll Area
- Collapsible
- Checkbox
- Select
- Slider
- Hover Card

Radix describes its primitives as open-source, accessible, low-level, and customizable, which makes them appropriate as a behavior foundation rather than a finished visual skin. citeturn203963search2turn203963search6

**Do not run Radix and Base UI side-by-side for identical primitives in the same visual subsystem without a reason.**

---

## 3.4 Ark UI — advanced headless/state-machine patterns

Use when a complex interaction is easier to model as a stateful primitive:

- multi-step selectors
- complex comboboxes
- advanced tree controls
- status/interaction widgets
- future cross-framework design-system experiments

Ark UI currently provides accessible headless components across React, Solid, Vue, and Svelte and uses state-machine-oriented interaction design. citeturn334311search9turn334311search11

For SyncNode Electron today, use it selectively—not as a second general component library.

---

## 3.5 Park UI — pattern/reference source

Use Park UI as a reference for how to turn headless primitives into coherent design-system recipes, especially:

- compact controls
- sophisticated form layouts
- dense utility surfaces
- tokens
- component recipes
- subtle states

Park UI documents an open-code approach built on Ark UI and Panda CSS and is MIT licensed. citeturn334311search5turn334311search7

**Do not import Park UI's full aesthetic into SyncNode. Extract patterns and translate them into SyncNode tokens.**

---

## 3.6 Flexible shadcn Blocks

Use shadcn Blocks for:

- sidebar/workspace shells
- dashboard-like analytical subviews
- settings layouts
- data-heavy screens
- command-center compositions
- table + filter + side panel patterns

Current shadcn Blocks are positioned as copy-and-paste building blocks that work with React frameworks. citeturn203963search17

**Important:** Blocks are structural references, not finished SyncNode screens.

Recompose them into the workstation shell.

---

## 3.7 React Bits — motion and microinteraction source

React Bits is useful for carefully chosen:

- text reveals
- subtle entrance choreography
- loaders
- microinteractions
- background motion
- hover states
- state transitions
- elegant empty-state motion

Its current repository describes a large collection of customizable animated React components and copy-paste integration, including shadcn-compatible installation paths. citeturn903647search3

**Hard rule:** never install an animated React Bits component just because it looks impressive. Use it only when the movement carries meaning.

---

## 3.8 Aceternity UI — selective premium visual effects

Use Aceternity sparingly for:

- launch/splash atmosphere
- subtle hero typography
- one high-value empty state
- limited background treatment
- focused visual moments
- cinematic transition moments

Aceternity currently offers React/Next.js copy-paste components built with Tailwind and Motion and labels itself shadcn-compatible. citeturn203963search4turn203963search13

**Forbidden:** bringing the typical high-gradient Aceternity landing-page aesthetic into the core workbench.

Core workbench stays monochrome and quiet.

---

## 3.9 Magic UI — selective animation/component source

Use for:

- subtle launch animations
- fine-grained decorative motion
- product intro moments
- microinteractions
- animated status treatments

Magic UI describes its main repository as an open-source UI library with animated components/effects that can be copied and pasted. citeturn903647search8

Again: source patterns, then normalize them.

---

## 3.10 daisyUI — utility vocabulary, not primary visual language

Use daisyUI selectively for:

- quick prototypes
- low-level utility patterns
- state naming inspiration
- compact form controls when useful

daisyUI is a Tailwind plugin with high-level component classes and a large set of utility-oriented components. citeturn203963search9turn203963search5

Do **not** mix daisyUI's default theme look with SyncNode's visual identity.

---

## 3.11 Kibo UI — specialized app/AI primitives

Kibo UI is valuable for:

- AI chat surfaces
- richer data tables
- file dropzones
- AI interaction primitives
- shadcn-compatible higher-level app components

Its documentation describes it as an open-source extension built on top of shadcn/ui. citeturn334311search1

Potential SyncNode uses:

- agent conversation/history panel
- file attachment area
- artifact upload/drop surface
- structured assistant response blocks

Normalize the visuals before use.

---

## 3.12 Tremor / Tremor Raw — telemetry and analytical visualization

Use for:

- token/latency telemetry
- run duration
- throughput
- agent utilization
- tool success/failure trends
- verification metrics
- audit summaries
- knowledge statistics

Tremor provides open-source React/Tailwind components for dashboards and charts, while Tremor Raw emphasizes copy/paste customization. citeturn334311search2turn334311search14

Use analytical components only where data genuinely exists.

**Do not create fake dashboards with empty graphs.**

---

## 3.13 Origin UI / ReUI / Coss UI / related modern open component ecosystems

These can be used as additional inspiration/source material for:

- dense form layouts
- advanced inputs
- polished command surfaces
- data-heavy cards
- settings rows
- table interactions
- modern shadcn-compatible patterns

Base UI's current community ecosystem explicitly lists projects such as ReUI and coss ui among open-source styled libraries built around the Base UI ecosystem. citeturn334311search8

**Rule:** do not create a dependency pile. Inspect the source, extract the useful pattern, then adapt it into the SyncNode system.

---

# 4. ICON SYSTEM

## 4.1 Primary icon set

Default: **Lucide**.

Use 16–18px icons for standard UI controls.

Recommended icon vocabulary:

```text
play / pause / square
arrow-up / arrow-down
chevron-left / chevron-right
terminal
folder / file / file-text
brain / sparkles only when semantically justified
bot / network / workflow
shield-check
check / x / triangle-alert / circle-alert
clock
search
command
settings
git-branch
monitor
mouse-pointer
keyboard
layers
panel-left / panel-right
maximize / minimize
external-link
download
refresh-cw
rotate-ccw
history
link / unlink
lock / unlock
eye / eye-off
activity
cpu
memory-stick
zap
```

## 4.2 Alternative icon sources

Use when Lucide does not have the right visual metaphor:

- Tabler Icons — large open-source set with a consistent outline language. citeturn203963search15
- Phosphor Icons — multiple weights and a broad semantic set; its core assets are MIT licensed. citeturn903647search0turn903647search4
- Heroicons — use selectively for familiar UI affordances.
- Iconoir — use only where its shape language clearly fits.
- AnimatedIcons / similar open animated icon sources — only for intentional state transitions.

### Icon rule

Never mix five icon families inside one toolbar.

The user should perceive **one icon language**.

---

# 5. MOTION SYSTEM

## 5.1 Motion stack

Preferred:

1. **CSS transitions** for simple state changes.
2. **Motion for React** for layout, presence, gestures, and orchestrated UI transitions.
3. **GSAP** for advanced timeline sequences where CSS/Motion becomes awkward.
4. **Anime.js** for lightweight specialty sequences when justified.
5. **Lenis** only when a long-form/splash/marketing-like scrolling surface exists; the core Electron workbench should not require smooth-scroll gimmicks.

Motion for React currently provides production-grade React animation primitives including layout/gesture/scroll animation and browser-native animation paths where possible. citeturn203963search16

Anime.js currently provides lightweight JavaScript animation APIs for CSS, SVG, DOM attributes, and JS objects. citeturn777108search9turn777108search12

### GSAP note

GSAP is excellent for timeline choreography, but treat its licensing model separately from the strictly open-source packages in the rest of the component stack. Do not label GSAP as an OSI/open-source dependency merely because it is free for many use cases.

---

## 5.2 Motion principles

### Instant feedback

Button press:

```text
hover: 80–120ms
pressed: 50–90ms
state change: 120–180ms
```

### Pane transitions

```text
enter: 180–240ms
exit: 140–200ms
```

### Major workspace transitions

```text
250–400ms
```

### Splash choreography

```text
brand reveal: ~600–1200ms
input reveal: ~450–700ms
workspace metadata: ~250–450ms
```

These are target ranges—not mandatory constants. Respect `prefers-reduced-motion` and Electron accessibility settings.

---

# 6. THE ANTI-AI-SLOP RULEBOOK

This section is mandatory.

## 6.1 Never do this

```text
❌ purple/blue/pink gradient blobs
❌ random glowing borders
❌ every card with a shadow
❌ every section as a rounded rectangle
❌ huge “AI” headline in the workbench
❌ robot face illustrations
❌ floating sparkles around normal UI
❌ meaningless waveform animation
❌ 3D rotating cubes
❌ moving starfields in an enterprise control interface
❌ fake live token counters
❌ fake agent thinking dots with no event
❌ massive dashboard KPI tiles
❌ “magic” buttons that do not correspond to a real action
❌ hover animations on every element
❌ rainbow status indicators
❌ excessive corner radii
❌ nested cards inside cards inside cards
```

## 6.2 Prefer this

```text
✓ thin borders
✓ subtle inset separation
✓ compact rows
✓ terminal/editor density
✓ precise typography
✓ visible hierarchy
✓ monochrome statuses + one semantic accent when necessary
✓ meaningful motion
✓ contextual right panels
✓ command palette
✓ keyboard shortcuts
✓ workspace persistence
✓ split panes
✓ inline metadata
✓ evidence-first verification views
✓ unobtrusive tool traces
✓ explicit approvals
✓ artifact previews
✓ restrained empty states
```

---

# 7. COLOR SYSTEM

The default visual theme is **SyncNode Black**.

## 7.1 Core palette

Use CSS variables; do not hard-code color values in feature components.

```css
:root {
  --background: 0 0% 4%;
  --foreground: 0 0% 95%;

  --surface-0: 0 0% 5%;
  --surface-1: 0 0% 7%;
  --surface-2: 0 0% 9%;
  --surface-3: 0 0% 11%;
  --surface-4: 0 0% 14%;

  --border-subtle: 0 0% 13%;
  --border: 0 0% 18%;
  --border-strong: 0 0% 25%;

  --text-primary: 0 0% 95%;
  --text-secondary: 0 0% 70%;
  --text-tertiary: 0 0% 48%;
  --text-disabled: 0 0% 34%;

  --accent: 0 0% 92%;
  --accent-foreground: 0 0% 7%;

  --success: 142 55% 50%;
  --warning: 38 90% 58%;
  --danger: 0 68% 58%;
  --info: 210 90% 62%;

  --focus: 0 0% 92%;
  --selection: 0 0% 16%;
}
```

These are starting tokens, not a license to hard-code them everywhere.

## 7.2 Color behavior

Normal product surfaces should be grayscale.

Semantic colors are reserved for:

- errors
- warnings
- approval requests
- active/success states where text alone is insufficient
- health indicators
- verification status

The semantic accent should occupy a very small fraction of the visual field.

---

# 8. TYPOGRAPHY

## 8.1 Primary UI font

Use a highly legible neutral sans-serif.

Preferred hierarchy:

```text
UI / body       Inter / Geist Sans / system sans
Code / logs     Geist Mono / JetBrains Mono / system mono
Numbers         tabular-nums
```

Geist's current design-system documentation explicitly provides a developer-oriented sans + mono family and a high-contrast component/grid language that is relevant to this product's visual direction. citeturn777108search0turn777108search1

Do not distribute or embed a font file without verifying project/license requirements.

## 8.2 Scale

```text
10px  — micro metadata only
11px  — dense timestamps/status metadata
12px  — default compact UI
13px  — primary dense body
14px  — comfortable body / command text
16px  — section titles
18px  — major panel title
20–24px — screen title
28–36px — splash/hero only
```

Do not use 32–48px titles throughout every page.

---

# 9. SPACING + DENSITY

Use a 4px base rhythm.

```text
4   micro gap
6   compact icon/text gap
8   standard inline gap
12  row/panel padding
16  default section padding
20  major section spacing
24  panel spacing
32  screen-level spacing
40+ splash/hero spacing
```

Recommended density modes:

```text
Compact   — default workstation
Comfort   — preference for users with more breathing room
Focus     — larger central work surface / minimized side chrome
```

Do not make every screen visually spacious. A professional IDE has controlled density.

---

# 10. BORDERS, RADIUS, MATERIALS

## 10.1 Radius

```text
2px   micro/terminal-like
4px   compact controls
6px   default buttons/inputs
8px   dialogs/panels
10px  prominent floating surfaces
12px  splash/search shell
16px  rare large media surface
```

Avoid 24–32px pill-shaped everything.

## 10.2 Borders

Prefer:

```text
1px solid var(--border-subtle)
1px solid var(--border)
```

Use stronger borders only for:

- selected panes
- focused controls
- destructive/approval actions
- modal boundaries

## 10.3 Shadows

The workbench should rely more on:

- borders
- layering
- tonal differences
- backdrop dimming

than on heavy shadows.

Use shallow shadows only for:

- dropdowns
- command palette
- floating menus
- dialogs
- drag previews

---

# 11. ELECTRON WINDOW / CHROME

The application should feel like a native workstation.

## 11.1 Window composition

```text
┌───────────────────────────────────────────────────────────────┐
│ custom titlebar / workspace identity / window controls      │
├───────┬───────────────────────────────────────────────┬──────┤
│       │                                               │      │
│ left  │             main workbench                    │ right│
│ rail  │                                               │ panel│
│       │                                               │      │
└───────┴───────────────────────────────────────────────┴──────┘
```

Use Electron draggable regions carefully:

```css
-webkit-app-region: drag;
```

Interactive controls inside draggable regions must explicitly use:

```css
-webkit-app-region: no-drag;
```

## 11.2 Native-feeling behavior

Support:

- remember window bounds
- restore workspace layout
- panel resizing
- fullscreen/maximize
- keyboard shortcuts
- context menus
- command palette
- drag-and-drop where meaningful
- system-level focus behavior
- accessible window title
- reduced motion

---

# 12. GLOBAL APP SHELL

## 12.1 Four-zone workstation shell

Primary layout:

```text
┌─ window/titlebar ─────────────────────────────────────────────┐
│                                                              │
│ ┌ rail ┐ ┌──────────── main workbench ───────────┐ ┌ panel ┐│
│ │      │ │ top context / run header               │ │       ││
│ │ nav  │ ├───────────────────────────────────────┤ │ agent ││
│ │      │ │                                       │ │ /tool ││
│ │ task │ │ primary content                       │ │ /data ││
│ │      │ │                                       │ │       ││
│ │      │ ├───────────────────────────────────────┤ │       ││
│ │      │ │ timeline / graph / terminal / files   │ │       ││
│ └──────┘ └───────────────────────────────────────┘ └───────┘│
│                         status bar                           │
└──────────────────────────────────────────────────────────────┘
```

## 12.2 Left rail

Compact, icon-forward navigation.

Suggested areas:

```text
Workspace
Runs
Agents
Knowledge
Artifacts
Learning
Audit
Settings
```

The rail should support:

- collapsed 48–56px mode
- expanded 220–260px mode
- tooltips in collapsed mode
- active indicator
- keyboard navigation
- badge count only where meaningful

## 12.3 Center pane

This is the visual center of gravity.

Possible center modes:

```text
Intent
Plan
Desktop
Workflow graph
Timeline
Artifact
Knowledge document
Audit event stream
```

## 12.4 Right inspector

The right side should be contextual, not a permanent dashboard.

It can host:

```text
Agent details
Tool details
Step details
Observation evidence
Verification evidence
Approval review
Artifact details
Model information
Context / retrieval evidence
```

It should be closable and resizable.

---

# 13. SPLASH EXPERIENCE — BEFORE LOGIN / BEFORE WORKSPACE

The splash must feel premium and intentional.

## 13.1 Concept

The splash is not a generic loading spinner screen.

It is a minimal black canvas that establishes:

```text
SyncNode
Think locally. Act intelligently.

local model / workspace status

[ Continue ]
```

The screen may transition into login/setup or directly into the workspace depending on the application's auth/bootstrap state.

## 13.2 Visual composition

```text
                     syncnode

               Think locally.
              Act intelligently.

          ┌───────────────────────────┐
          │  Continue to workspace  ↑ │
          └───────────────────────────┘

             localhost • ready
```

The logo should not be huge.

The reference splash image demonstrates the intended restraint: black canvas, low-contrast wordmark, centered input/action surface, tiny workspace metadata, and almost no decorative chrome.

## 13.3 Bootstrap sequence

```text
0ms      black canvas
150ms    wordmark fade-in
400ms    subtitle enters
650ms    readiness state appears
850ms    primary action/input appears
1100ms   keyboard hint appears
```

Actual timing should adapt to real Electron/backend bootstrap status.

## 13.4 Splash states

```text
BOOTING
CHECKING LOCAL RUNTIME
MODEL AVAILABLE
MODEL UNAVAILABLE
BACKEND STARTING
BACKEND READY
DATABASE READY
BROWSER RUNTIME READY
COMPUTER RUNTIME READY
CONTINUE
RECOVERY / DIAGNOSTICS
```

Never show “ready” unless the corresponding backend health data says ready.

---

# 14. HOME / NEW SESSION SCREEN

The Home experience should be a quiet launchpad, not a dashboard.

## Layout

```text
                New session

        What would you like SyncNode to do?

 ┌──────────────────────────────────────────────┐
 │ Type a task, objective, or workflow...     ↑ │
 └──────────────────────────────────────────────┘

 [ local ] [ safe ] [ explain ] [ files ]

 Recent
 ───────────────────────────────────────────────
 run: Create a report from plant documents
 run: Prepare weekly audit package
 run: Draft operational summary
```

Quick actions should be compact text/icon controls rather than colorful cards.

---

# 15. INTENT SCREEN

The Intent screen should look like an engineer reviewing a task specification.

## 15.1 Structure

```text
Intent

USER GOAL
────────────────────────────────────────────
Create a compliance summary from the supplied files.

UNDERSTANDING
────────────────────────────────────────────
Task type      Document synthesis
Risk level     Medium
External effect None
Primary output Report

CONTEXT
────────────────────────────────────────────
5 files • 3 relevant knowledge records • 1 prior workflow

CAPABILITIES
────────────────────────────────────────────
Document runtime
Knowledge retrieval
Verification

[ Edit intent ]            [ Continue to plan ]
```

## 15.2 Visual treatment

No giant “AI understanding” card.

Use:

- section labels
- thin separators
- inline metadata
- mono values for identifiers
- subtle highlighted selections

## 15.3 Intent uncertainty

When confidence/uncertainty is actually available from backend state, expose it as a factual status.

Do not convert model internals into fake confidence percentages.

---

# 16. PLAN SCREEN

The Plan screen is an operational specification.

## Visual hierarchy

```text
PLAN
Goal

Step 01  Retrieve relevant knowledge
Step 02  Draft Word document
Step 03  Generate spreadsheet
Step 04  Generate presentation
Step 05  Verify artifacts
Step 06  Prepare email draft
Step 07  Request send approval
```

Each row should show:

```text
step number
agent
capability/tool
input/output
dependency
risk
status
```

Use compact timeline/graph affordances instead of oversized cards.

---

# 17. ACTIVE RUN SCREEN

This is the primary SyncNode experience.

## 17.1 Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Run title                      RUNNING    00:02:31          │
├───────────────┬────────────────────────────┬───────────────┤
│ Run steps     │ Active work surface        │ Intelligence  │
│               │                            │               │
│ ✓ Intent      │    desktop / graph /       │ Agent         │
│ ✓ Plan        │    artifact / terminal     │ details       │
│ ● Execute     │                            │               │
│   ├ writer    │                            │ Tool call     │
│   ├ office    │                            │ verification  │
│   └ browser   │                            │ context       │
│ ○ Verify      │                            │               │
│ ○ Approve     │                            │               │
└───────────────┴────────────────────────────┴───────────────┘
```

## 17.2 Run header

Compact:

```text
RUNNING  ·  c0574206  ·  6 steps  ·  local
```

Actions:

```text
Pause/terminate where supported
Open timeline
Open audit
Open artifacts
Open command palette
```

Do not crowd the header.

---

# 18. AGENT SCREEN

Agent screens should feel like internal worker processes inside an IDE.

## 18.1 Agent list

```text
Agents

Supervisor        idle
Writer            working
Document          complete
Office            working
Computer          observing
Browser           waiting
Verifier          checking
Recovery          idle
```

## 18.2 Agent row anatomy

```text
[status] Agent Name         capability      task      runtime
```

Hover/selection reveals:

- agent key
- assigned task
- current phase
- latest tool
- last observation
- verification state
- duration
- model/profile if available from API

## 18.3 Agent detail

```text
WRITER
────────────────────────────────────────
Current step
Drafting report content

MODEL
local/gemma4:e4b

INPUTS
context/knowledge

OUTPUT
artifact candidate

LATEST EVENT
agent.plan_summary

[ View timeline ]   [ View evidence ]
```

Do not expose raw chain-of-thought.

Use safe summaries or backend-provided activity fields only.

---

# 19. TOOL EXECUTION SCREEN / TOOL ROWS

The tool timeline must visually distinguish:

```text
proposed
validated
authorized
started
invoked
completed
failed
```

Tool rows should be compact.

Example:

```text
┌─────────────────────────────────────────────────────────────┐
│ ✓  document.create_docx                      1.82s          │
│    Create verified Word artifact                            │
│    output: SyncNode_Word_c0574206.docx                     │
└─────────────────────────────────────────────────────────────┘
```

Expanded:

```text
tool key
input summary
validation result
authorization result
runtime duration
output references
verification references
audit event id
```

Never show raw secrets, credentials, or unsafe internal payloads.

---

# 20. DESKTOP MIRROR / COMPUTER CONTROL VIEW

This is one of the strongest differentiators and therefore must look excellent.

## 20.1 Visual direction

The desktop mirror should feel like a professional remote-control viewport embedded in an IDE.

```text
┌───────────────────────────────────────────────────────────┐
│ Desktop  •  Windows  •  observed  1280×720               │
├───────────────────────────────────────────────────────────┤
│                                                           │
│                 [ observed desktop ]                      │
│                                                           │
│    cursor overlay                                         │
│                                                           │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ observation  #82   •   click   •   verify                 │
└───────────────────────────────────────────────────────────┘
```

## 20.2 Controls

Compact toolbar:

```text
observe
fit
zoom
focus app
pause
step mode
open evidence
```

Do not render fake cursor motion. Render only backend-provided observations/tool state.

## 20.3 Observation card

```text
OBSERVATION
Window: Microsoft Word
State: document open
Source: computer.observe
Captured: 18:42:17

[ View screenshot ]
```

---

# 21. WORKFLOW GRAPH

Use React Flow / XYFlow as the graph substrate where the existing frontend architecture calls for graph visualization.

React Flow provides node-based React interfaces and is well suited to a workflow graph view.

## Graph design

Nodes should be narrow, dense, and technical.

```text
┌───────────────┐
│ RAG           │
│ ✓ complete    │
│ 320ms         │
└──────┬────────┘
       │
       ▼
┌───────────────┐
│ Intent        │
│ ✓ complete    │
└──────┬────────┘
       │
       ▼
┌───────────────┐
│ Plan          │
│ ● running     │
└───────────────┘
```

Use:

- thin edges
- restrained node fills
- status rails
- small timestamps
- compact icons
- optional minimap only when graph size warrants it

Avoid huge colorful flowchart cards.

---

# 22. TIMELINE

The timeline is the canonical visual history of a run.

## Event families

```text
run
rag
intent
plan
agent
tool
observation
verification
recovery
approval
artifact
workflow memory
audit
```

## Timeline visual encoding

Use one consistent vertical spine.

```text
18:42:01  ● run.started
          │
18:42:02  ● rag.query
          │
18:42:03  ● rag.retrieval.completed
          │
18:42:04  ● intent.completed
          │
18:42:06  ● plan.created
          │
18:42:08  ● agent.spawned
          │
18:42:09  ● tool.started
          │
18:42:10  ● observation.captured
          │
18:42:12  ● verification.passed
```

Filters:

```text
All
Agents
Tools
Evidence
Approvals
Artifacts
Errors
```

Use virtualization for long timelines.

---

# 23. VERIFICATION UI

Verification must be visually distinct from execution.

## Verification row

```text
✓ VERIFIED
Artifact exists
Exact expected path matched
SHA recorded
Content checks passed
```

Failure:

```text
× VERIFICATION FAILED
Expected artifact was not found
Recovery available
```

Never treat:

```text
tool completed
```

as visually equivalent to:

```text
verification passed
```

This distinction is central to SyncNode's product identity.

---

# 24. APPROVAL UI

The approval surface must be calm, explicit, and difficult to misunderstand.

## Example

```text
REVIEW REQUIRED
────────────────────────────────────────────────
SyncNode is ready to perform an external action.

Action
Prepare and send email

Recipients
operations@example.local

Attachments
3 verified artifacts

Evidence
✓ files created
✓ files verified
✓ draft prepared

[ Reject ]                    [ Approve ]
```

Use a focused dialog/sheet.

Do not use red as a generic warning background.

The action itself determines semantic styling.

Approval requests should never disappear into a toast.

---

# 25. ARTIFACT EXPERIENCE

Artifacts are first-class product objects.

## 25.1 Artifact list

```text
Artifacts

▣ SyncNode_Word_c0574206.docx       verified
▤ SyncNode_Excel_c0574206.xlsx      verified
▥ SyncNode_Presentation_c0574206.pptx verified
✉ draft.eml                         prepared
```

## 25.2 Artifact tile

```text
┌─────────────────────────────────────────┐
│ DOCX                                    │
│ SyncNode_Word_c0574206.docx             │
│ 84 KB  •  verified  •  created 18:42    │
│                                         │
│ SHA  601adaa1...                        │
│                                         │
│ [ Open ] [ Reveal ] [ Evidence ]        │
└─────────────────────────────────────────┘
```

## 25.3 Artifact evidence panel

Use a side panel rather than another page whenever possible.

```text
ARTIFACT EVIDENCE

Identity
path
run id
artifact type
size
hash

Creation
creating tool
agent
step

Verification
checks
status
timestamp

Lineage
inputs → tool → artifact → verifier
```

---

# 26. KNOWLEDGE SCREEN

Knowledge should look like an engineering knowledge workspace.

## Layout

```text
┌──────────── knowledge sources ───────────┬──────── document ─────┐
│ search                                   │ title                │
│ filters                                  │ content              │
│ source/type                              │ metadata             │
│                                          │ provenance           │
└──────────────────────────────────────────┴───────────────────────┘
```

Use dense rows and split panes.

Search surface should support:

- query
- type
- source
- date
- tags
- relevance
- selected result

Do not turn knowledge into an image-heavy card grid.

---

# 27. LEARNING SCREEN

Workflow memory should look measurable and controlled.

```text
Task type
──────────────────────────────────────────
Create weekly operational package

Successful workflows        17
Average duration             4m 32s
Last successful run          today

Candidates awaiting review
──────────────────────────────────────────
3 workflow candidates

[ Inspect ] [ Review ] [ Ignore ]
```

No fake “AI learns 97% better” metrics.

Only API-backed measurements.

---

# 28. AUDIT SCREEN

Audit should be highly legible and forensic.

Use a compact event table/timeline.

Columns:

```text
Time | Run | Actor | Event | Resource | Result
```

Expandable row:

```text
event id
correlation id
run id
agent id
tool id
status
safe payload summary
related artifact
related verification
```

Use monospace for IDs.

---

# 29. SETTINGS SCREEN

Settings should feel like an IDE settings surface.

Categories:

```text
Appearance
Workbench
Keyboard
Model
Runtime
Computer Control
Browser
Knowledge
Notifications
Privacy
Diagnostics
About
```

Each setting should be a compact row:

```text
Theme                                    SyncNode Black
High contrast                            Off
Motion                                   Full
Panel density                            Compact
Show telemetry                            On
```

Use standard form patterns and inline descriptions.

---

# 30. COMMAND PALETTE

A command palette is mandatory for the editor feeling.

Shortcut:

```text
Ctrl/Cmd + K
```

Possible commands:

```text
New session
Open recent run
Focus run timeline
Show agents
Show artifacts
Show knowledge
Open audit
Toggle left rail
Toggle right inspector
Toggle desktop
Fit workflow graph
Focus intent
Focus plan
Open settings
Toggle compact mode
Toggle focus mode
```

## Visual design

```text
┌───────────────────────────────────────────────┐
│ > Type a command                              │
├───────────────────────────────────────────────┤
│ Run                                            │
│   New session                                  │
│   Open recent run                              │
│ Workspace                                      │
│   Toggle right panel                           │
│   Focus timeline                               │
└───────────────────────────────────────────────┘
```

Use `cmdk` or a shadcn Command surface where it fits; cmdk is a focused command-menu package for React ecosystems.

---

# 31. TOOLTIP / POPOVER / MENU SYSTEM

Floating UI can be used as the positioning substrate for custom floating interactions, including anchored tooltips, menus, popovers, and collision-aware surfaces. citeturn777108search2turn777108search8

Preferred hierarchy:

```text
Tooltip       minimal label
Popover       lightweight contextual content
Dropdown      action list
Context menu  right-click/secondary actions
Dialog        blocking decision
Sheet         larger review surface
```

Never use a modal dialog for a non-blocking tooltip-sized interaction.

---

# 32. DRAWERS / SHEETS

Use Vaul or the chosen shadcn/base primitive when a mobile-like drawer interaction is also useful on desktop.

Desktop behavior:

- side sheet for inspectors
- bottom sheet for execution details when center canvas should remain visible
- full dialog for approval

Never stack more than two modal layers.

---

# 33. TABLES / DENSE DATA

The app will eventually display substantial telemetry, audit, artifact, knowledge, and workflow data.

Table rules:

- 32–40px default row height
- 28–32px compact mode
- sticky header for long datasets
- sortable only where sorting is meaningful
- monospace IDs
- truncation with tooltip/detail view
- keyboard row navigation where practical
- no unnecessary borders on every cell

Use a restrained zebra/hover treatment, not bright striping.

---

# 34. EMPTY STATES

Empty states should be quiet and useful.

Example:

```text
No runs yet

Start a new local workflow to see execution history here.

[ New session ]
```

No huge cartoon illustration.

Allowed:

- tiny line illustration
- one subtle motion accent
- very low-contrast icon

---

# 35. LOADING STATES

Loading should show **where** work is happening.

Bad:

```text
Loading...
```

Better:

```text
Loading run
Fetching execution state
Restoring event stream
```

For lists:

- skeleton rows
- shimmer only when useful
- stable geometry to avoid layout jumps

For real-time run state:

```text
CONNECTING
RECONNECTING
LIVE
STALE
DISCONNECTED
```

Use actual SSE state.

---

# 36. ERROR STATES

Errors should feel like engineering diagnostics.

```text
Run failed
────────────────────────────────────────
Verification failed for the Word artifact.

Expected
SyncNode_Word_....docx

Observed
artifact path mismatch

Recovery
1 bounded recovery attempt available

[ Open evidence ] [ Open timeline ]
```

Avoid:

```text
Oops!
Something magical went wrong!
```

---

# 37. STATUS LANGUAGE

Standardize statuses across the entire frontend.

```text
queued
running
waiting_approval
completed
failed
cancelled

pending
proposed
validated
authorized
started
invoked
completed
failed

verified
verification_failed
recovery_running
recovered
```

Do not invent alternate synonyms such as:

```text
working
busy
processing
active-ish
almost done
```

unless the status is a purely visual local substate.

---

# 38. STATUS VISUAL LANGUAGE

Use the same geometry everywhere.

```text
queued             ○ muted
running            ● subtle active ring
waiting approval   ◇ outlined
completed          ✓ restrained semantic success
failed             × semantic danger
cancelled          — muted
```

Do not use colored status badges everywhere. In many places an icon + text is sufficient.

---

# 39. MICROINTERACTIONS

## Button

```text
rest → hover → pressed → disabled → success/error
```

## Sidebar item

```text
rest → hover → active
```

Active state should use a left or inset indicator rather than a glowing filled pill.

## Timeline item

```text
pending → entering → active → complete
```

Animation should travel along the timeline spine only when useful.

## Artifact

```text
created → verifying → verified
```

The visual should tell this story without pulsing endlessly.

---

# 40. AGENT ACTIVITY MOTION

Agents may be active for long periods.

Do not leave 8 animated spinners permanently running.

Instead:

- one subtle active marker
- elapsed time
- current task line
- latest tool row
- optional compact progress indicator when backend provides progress

Example:

```text
● Writer      drafting report       00:14
  └─ document.create_docx           running
```

This looks much more like an IDE process view than an AI dashboard.

---

# 41. SPLIT-PANE ENGINEERING

Use a robust resizable panel system such as `react-resizable-panels` or an equivalent implementation.

Requirements:

- drag handle hit target >= 8px
- keyboard-accessible resize where supported
- min/max pane constraints
- persisted sizes
- snap-to-common widths
- double-click reset
- collapse/expand

Possible presets:

```text
40 / 60
50 / 50
60 / 40
main / inspector
main / timeline
```

---

# 42. DESKTOP RESPONSIVE RULES

Electron is desktop-first, but the UI must survive window resizing.

## >= 1440px

Full four-zone workbench.

## 1200–1439px

Compact left rail + collapsible right inspector.

## 900–1199px

One side panel open at a time; center prioritizes content.

## <900px

Treat as constrained workstation mode:

- left rail collapses
- inspector becomes sheet
- timeline becomes drawer/bottom panel
- avoid horizontal clipping

This is not mobile UI; it is compact desktop adaptation.

---

# 43. ACCESSIBILITY

Minimum expectations:

- keyboard navigation
- visible focus
- `aria-label` for icon-only controls
- semantic headings
- accessible dialogs
- accessible command palette
- accessible tab navigation
- sensible screen reader labels
- reduced-motion support
- sufficient text contrast
- no color-only status meaning
- focus restoration after dialogs/menus
- ESC closes transient surfaces
- TAB/SHIFT+TAB moves predictably

Use Radix/Base UI/Ark behavior patterns rather than hand-rolling accessibility-heavy primitives.

---

# 44. FOCUS SYSTEM

Focus should be visually clear but quiet.

Preferred:

```css
outline: 1px solid hsl(var(--focus));
outline-offset: 1px;
```

or a subtle inset ring.

Avoid thick glowing neon rings.

---

# 45. SCROLLBARS

Scrollbar styling should be extremely restrained.

- thin width
- low-contrast track
- slightly brighter thumb on hover
- no rounded giant scroll thumbs

Keep native behavior understandable.

---

# 46. TERMINAL / LOG SURFACES

Terminal/log surfaces should have:

- monospace
- 11–13px text
- line numbers only if useful
- timestamp column optional
- subtle row highlighting
- copy button
- search
- auto-scroll toggle
- “follow live” indicator

Example:

```text
18:42:07  agent.started          writer
18:42:08  tool.proposed          document.create_docx
18:42:08  tool.validated         document.create_docx
18:42:09  tool.started           document.create_docx
18:42:10  artifact.created       SyncNode_Word_...
18:42:11  verification.passed    artifact.identity
```

---

# 47. CODE / JSON / STRUCTURED DATA

Structured data should use a mono font and syntax-aware highlighting.

Even with a monochrome palette, hierarchy can be expressed through:

- weight
- opacity
- spacing
- indentation
- tiny semantic accents

Do not color every JSON key blue/green/purple just because it is possible.

---

# 48. ARTIFACT PREVIEWS

Artifact preview should adapt to type.

```text
DOCX       document preview / metadata
XLSX       sheet preview / table
PPTX       slide thumbnails + preview
PDF        page preview
IMAGE      image viewer
TEXT       code/text viewer
JSON       formatted viewer
EMAIL      draft preview
```

The actual file content is authoritative; the frontend must never fabricate a preview unrelated to the artifact.

---

# 49. IMAGE / SCREENSHOT PRESENTATION

For computer observations and artifact images:

- use a dark frame
- preserve native aspect ratio
- allow fit/contain/fill controls
- show timestamp/source metadata
- support zoom
- allow open-in-new-view
- never crop important evidence by default

A screenshot is evidence, not decoration.

---

# 50. FOCUS MODE

Add an IDE-style focus mode.

Shortcut:

```text
Ctrl/Cmd + Shift + F
```

Behavior:

```text
hide left rail
hide inspector
maximize center canvas
keep run status visible
keep command palette available
```

Useful during:

- desktop observation
- workflow graph
- artifact review
- knowledge reading

---

# 51. WORKSPACE PERSISTENCE

The UI should remember local frontend presentation settings.

Persist:

- panel widths
- selected navigation item
- expanded/collapsed rail
- inspector width
- density mode
- theme
- last active center mode
- focus mode preference if appropriate
- open run selection

Do not persist backend truth as if it were authoritative.

---

# 52. KEYBOARD SHORTCUT SYSTEM

Suggested baseline:

```text
Ctrl/Cmd + K          Command palette
Ctrl/Cmd + N          New session
Ctrl/Cmd + P          Quick open
Ctrl/Cmd + Shift + P  Command palette alias if useful
Ctrl/Cmd + B          Toggle left rail
Ctrl/Cmd + J          Toggle bottom timeline/log
Ctrl/Cmd + Shift + ]  Next pane
Ctrl/Cmd + Shift + [  Previous pane
Ctrl/Cmd + Shift + F  Focus mode
Esc                   Close transient surface
```

Run-level actions must show dangerous shortcuts clearly before activation.

---

# 53. CONTEXTUAL ACTION PHILOSOPHY

The UI should reveal relevant actions where the user is looking.

Example artifact:

```text
[ Open ] [ Evidence ] [ Reveal ]
```

Example tool:

```text
[ Details ] [ Evidence ]
```

Example failed verification:

```text
[ Inspect ] [ Recovery details ]
```

Do not put 12 buttons into a toolbar “just in case.”

---

# 54. TOASTS / NOTIFICATIONS

Use toasts only for non-blocking state updates.

Good:

```text
Layout saved
```

```text
Connection restored
```

```text
Artifact opened
```

Bad:

```text
Approval required
```

Approval belongs in the actual approval surface and active-run state.

---

# 55. LIVE CONNECTION INDICATOR

The application should expose SSE health subtly.

Top/status bar:

```text
● LIVE
● RECONNECTING
○ DISCONNECTED
```

Hover/detail:

```text
Run stream
connected 18:42:18
last event 180ms ago
```

Never hide connection failure while the UI continues pretending the run is live.

---

# 56. MODEL / LOCAL RUNTIME INDICATOR

The product is local-first, so runtime state can be useful in a quiet status area.

Example:

```text
LOCAL
Gemma
GPU
Ready
```

Clicking can open runtime diagnostics.

Do not display speculative GPU values. Only show backend-provided health/telemetry.

---

# 57. DESIGNING THE “AI” FEEL WITHOUT GIMMICKS

SyncNode can feel intelligent through information choreography instead of visual clichés.

Use:

- live event stream
- clear run progression
- agent spawning
- contextual summaries
- retrieval evidence
- tool activity
- verification transitions
- artifact lineage
- workflow graph movement
- precise state labels
- contextual recommendations from real backend state

The intelligence is visible because the system is observable.

---

# 58. THE WORKFLOW STORY SHOULD ALWAYS BE READABLE

At any moment, a user should be able to answer:

```text
What did I ask?
What did SyncNode understand?
What plan did it create?
Which agent is acting?
What tool is being used?
What did the system observe?
Did the result verify?
Was recovery needed?
Is approval required?
What artifact was created?
What is the exact current state?
```

The UI design is successful when these answers can be found without navigating through five screens.

---

# 59. INFORMATION HIERARCHY FOR EVERY SCREEN

Every major screen should have exactly one dominant focal point.

### Level 1 — primary task/state

Example:

```text
Create weekly operations report
RUNNING
```

### Level 2 — current work

Example:

```text
Office agent → creating Excel workbook
```

### Level 3 — evidence and metadata

Example:

```text
tool
path
hash
time
agent
```

### Level 4 — optional diagnostics

Example:

```text
event id
model profile
raw metadata
```

Do not make all levels equally bright.

---

# 60. DESIGN TOKENS FOR COMPONENT STATES

Every interactive component should support at least:

```text
rest
hover
focus-visible
pressed
selected
disabled
loading
success
warning
danger
```

Only use the states that make semantic sense.

---

# 61. SHADOW / ELEVATION SCALE

Keep it tiny.

```text
0   flat surface
1   dropdown
2   popover
3   dialog
4   critical modal / approval
```

Use opacity + border before increasing shadow strength.

---

# 62. BACKDROP / OVERLAY SYSTEM

Dialogs should dim the workspace subtly.

Use:

```text
rgba(0,0,0,0.45–0.68)
```

Avoid opaque modal backdrops that make the user lose all context.

The approval surface should leave enough of the underlying run visible to reinforce why approval is being requested.

---

# 63. HERO SPLASH vs WORKBENCH RULE

These are deliberately different modes.

## Splash / onboarding

Can use:

- cinematic typography
- subtle animated wordmark
- very restrained background texture
- one premium effect
- larger negative space

## Workbench

Must use:

- density
- utility
- split panels
- compact labels
- tool traces
- command surface
- evidence
- clear status

Never let the hero style leak into the core workstation.

---

# 64. PREMIUM VISUAL RECIPE

For a truly polished screen, use this composition formula:

```text
1. strong black base
2. subtle surface hierarchy
3. precise typography
4. one focal action
5. tiny semantic accents
6. clean alignment
7. consistent 4px spacing grid
8. thin separators
9. one motion story
10. no unnecessary decoration
```

That is enough.

Do not add another 15 effects after this formula is working.

---

# 65. SPECIALIZED OPEN-SOURCE LIBRARIES / UTILITIES

These are additional sources that may be used selectively after the primary design layer exists.

| Ecosystem | Role in SyncNode | Recommended usage |
|---|---|---|
| shadcn/ui | Foundation + copy/edit components | **Primary** |
| Base UI | Headless behaviors | **Primary for new primitives where appropriate** |
| Radix UI | Headless/accessibility primitives | **Existing + selective** |
| Ark UI | Complex stateful/headless controls | Selective |
| Park UI | Recipe/pattern inspiration | Selective |
| React Aria | Accessibility-heavy custom controls | Selective |
| Headless UI | Simple headless patterns | Selective |
| Aceternity UI | Hero/visual accents | Very limited |
| React Bits | Motion + microinteractions | Limited |
| Magic UI | Motion + premium accents | Limited |
| shadcn Blocks | Layout patterns | Frequent reference |
| Kibo UI | AI/chat/file/data primitives | Selective |
| Tremor | Charts/telemetry | Data screens only |
| daisyUI | Tailwind utility patterns | Prototype/reference |
| Floating UI | Popover/tooltip positioning | Infrastructure |
| cmdk | Command palette | Strong candidate |
| Vaul | Drawer/sheet patterns | Selective |
| React Flow / XYFlow | Workflow graph | Strong candidate |
| Motion | UI motion | Strong candidate |
| GSAP | Complex sequences | Specialty only |
| Anime.js | Lightweight specialty motion | Specialty only |
| Lenis | Long-form smooth scroll | Splash/marketing only |
| Lucide | Default icons | **Primary** |
| Tabler | Supplemental icons | Selective |
| Phosphor | Supplemental icons/weight options | Selective |
| Heroicons | Familiar supplemental icons | Selective |
| Embla | Carousel/media strips | Artifact previews only if required |
| react-resizable-panels | Resizable workbench | Strong candidate |
| Sonner | Toasts | Strong candidate |
| Recharts | Analytical charts | Only when backend data exists |
| TanStack Table | Dense tables | Strong candidate where needed |
| TanStack Virtual | Long timeline/list virtualization | Strong candidate |
```

---

# 66. CURRENT ECOSYSTEM NOTES / SOURCE REFERENCES

This section records the major sources used when defining the design-system toolbox. Verify licenses and compatibility against the exact package version before adding a dependency to the Electron application.

### Core / primitives

- shadcn/ui — https://ui.shadcn.com/ citeturn203963search3turn203963search8
- shadcn Components — https://ui.shadcn.com/docs/components citeturn203963search1
- shadcn Blocks — https://ui.shadcn.com/blocks citeturn203963search17
- Base UI — https://base-ui.com/ citeturn334311search0turn334311search4
- Radix UI — https://www.radix-ui.com/primitives citeturn203963search2turn203963search6
- Ark UI — https://ark-ui.com/ citeturn334311search9
- Park UI — https://park-ui.com/ citeturn334311search7
- Kibo UI — https://www.kibo-ui.com/docs citeturn334311search1
- Tremor — https://www.tremor.so/ citeturn334311search3turn334311search14
- daisyUI — https://daisyui.com/ citeturn203963search9

### Motion / effects

- Motion for React — https://motion.dev/docs/react citeturn203963search16
- React Bits — https://github.com/DavidHDev/react-bits citeturn903647search3
- Aceternity UI — https://ui.aceternity.com/ citeturn203963search4
- Magic UI — https://github.com/magicuidesign/magicui citeturn903647search8
- Anime.js — https://animejs.com/ citeturn777108search9
- GSAP — https://gsap.com/
- Lenis — https://lenis.darkroom.engineering/

### Workbench / positioning / graph

- Floating UI — https://floating-ui.com/ citeturn777108search2turn777108search8
- React Flow / XYFlow — https://reactflow.dev/
- Vaul — https://github.com/emilkowalski/vaul
- cmdk — https://github.com/pacocoursey/cmdk
- react-resizable-panels — https://github.com/bvaughn/react-resizable-panels
- Sonner — https://github.com/emilkowalski/sonner
- Embla — https://www.embla-carousel.com/ citeturn777108search4

### Iconography

- Lucide — https://lucide.dev/
- Tabler Icons — https://tabler.io/icons citeturn203963search15
- Phosphor — https://phosphoricons.com/ citeturn903647search0turn903647search4
- Heroicons — https://heroicons.com/

### Vercel / Geist reference

Geist provides a useful reference for developer-tool typography, high-contrast color, grid, materials, and compact component design. Vercel currently documents it as its design system for consistent web experiences. citeturn777108search0turn777108search16

Use Geist as **design-language inspiration**, not as a command to clone Vercel.

---

# 67. LICENSE / DEPENDENCY DISCIPLINE

The phrase “open source” must not be used casually.

Before adopting any component/effect package:

1. verify its current repository/license
2. verify commercial-use terms if relevant
3. verify whether its visual assets have separate terms
4. verify Electron/Vite/React compatibility
5. verify bundle impact
6. verify accessibility
7. verify maintenance status
8. verify whether source copying has attribution requirements
9. prefer copy/edit ownership for critical UI primitives
10. avoid adding a dependency for a single 30-line component

The design system is intentionally broad, but the production dependency graph should remain disciplined.

---

# 68. COMPONENT OWNERSHIP MAP

Create a single source of truth for product components.

```text
frontend/
  src/
    components/
      ui/
        button
        dialog
        command
        dropdown-menu
        tooltip
        tabs
        input
        select
        badge
        sheet
        drawer
        scroll-area

      shell/
        AppShell
        TitleBar
        LeftRail
        StatusBar
        PaneFrame
        ResizeHandle
        InspectorPanel

      run/
        RunHeader
        RunStatus
        RunStepList
        RunSummary
        RunTimeline
        RunConnectionIndicator

      agents/
        AgentList
        AgentRow
        AgentDetail
        AgentStatus
        AgentActivity

      tools/
        ToolRow
        ToolDetails
        ToolStatus
        ToolInputSummary
        ToolOutputSummary

      evidence/
        EvidencePanel
        ObservationCard
        VerificationCard
        RecoveryCard
        AuditReference

      artifacts/
        ArtifactList
        ArtifactRow
        ArtifactTile
        ArtifactPreview
        ArtifactEvidence
        ArtifactLineage

      graph/
        WorkflowGraph
        GraphNode
        GraphEdge
        GraphToolbar
        GraphMiniMap

      computer/
        DesktopMirror
        ObservationToolbar
        ScreenFrame
        CursorOverlay

      knowledge/
        KnowledgeList
        KnowledgeSearch
        KnowledgePreview
        ProvenancePanel

      approval/
        ApprovalDialog
        ApprovalEvidence
        ApprovalActionBar

      command/
        CommandPalette
        CommandGroup
        CommandItem

      settings/
        SettingsNav
        SettingsSection
        SettingsRow
```

Feature pages must compose these components instead of recreating variants.

---

# 69. CSS / TOKEN ARCHITECTURE

Create a token layer such as:

```text
src/styles/
  tokens.css
  theme.css
  motion.css
  globals.css
```

And semantic utility classes/components for:

```text
surface-0
surface-1
surface-2
surface-raised
border-subtle
border-default
text-primary
text-secondary
text-tertiary
status-success
status-warning
status-danger
status-info
focus-ring
```

Avoid arbitrary Tailwind values repeated through the product.

---

# 70. DESIGN REVIEW CHECKLIST

Every new screen must pass this review before being considered complete.

## Visual

```text
[ ] Looks correct at 100% scale
[ ] Looks correct at 125% scale
[ ] No random gradients
[ ] No excessive cards
[ ] No unexplained shadows
[ ] Typography hierarchy is obvious
[ ] Borders are consistent
[ ] Icons use the same family
[ ] Spacing follows the grid
```

## Interaction

```text
[ ] Keyboard works
[ ] Focus state is visible
[ ] Tooltips exist for icon-only controls
[ ] Escape behavior works
[ ] Resize behavior works
[ ] Loading state works
[ ] Error state works
[ ] Empty state works
[ ] Reconnect state works
```

## Backend truth

```text
[ ] No fake event
[ ] No fake progress
[ ] No fake artifact
[ ] No fake verification
[ ] No fake approval state
[ ] No frontend mutation of backend contract
```

## Premium quality

```text
[ ] Alignments are intentional
[ ] No text feels cramped
[ ] No dead controls
[ ] Hover states are subtle
[ ] Motion has meaning
[ ] Dense screens remain readable
[ ] Primary focal point is obvious
```

---

# 71. VISUAL QA / PLAYWRIGHT CHECKLIST

Run visual QA at these sizes:

```text
1280×720
1440×900
1600×1000
1920×1080
2560×1440
```

At minimum capture:

```text
splash
home
intent
plan
active run
agent inspector
desktop mirror
workflow graph
timeline
approval dialog
artifact evidence
knowledge
learning
audit
settings
```

Review for:

- clipping
- overflow
- panel collapse
- typography jumps
- broken focus rings
- inconsistent icon sizing
- incorrect z-index
- modal layering
- status legibility
- long run names
- long artifact paths
- long agent names
- error content wrapping
- empty states
- reconnect states

---

# 72. PERFORMANCE RULES

A premium interface that stutters is not premium.

## Avoid

- continuously animated backgrounds inside the workbench
- expensive blur across huge areas
- large DOM trees for timeline events
- unnecessary rerenders on every SSE event
- re-rendering the entire graph for one node state
- rendering all hidden inspectors
- unbounded log DOM

## Prefer

- virtualization
- memoized rows
- derived selectors
- event normalization before rendering
- stable keys
- CSS transforms
- browser-native animations where possible
- lazy preview loading
- deferred heavy artifact previews

---

# 73. SSE UI UPDATE RULE

The design system must support rapid backend state changes without visual chaos.

When events arrive:

```text
event
  ↓
normalize
  ↓
dedupe
  ↓
update normalized store
  ↓
derive affected entities
  ↓
animate only affected visual nodes
```

Do not rebuild the entire UI tree for each incoming event.

---

# 74. ANIMATION CONTRACT FOR LIVE EVENTS

Different event classes should produce different visual responses.

```text
run.started
  → header status transition

agent.spawned
  → add agent row with subtle entrance

agent.started
  → active marker

tool.started
  → tool row activates

observation.captured
  → evidence badge/timeline marker

verification.passed
  → compact success transition

verification.failed
  → clear failure state

recovery.started
  → recovery section expands

approval.requested
  → approval surface enters focus

run.completed
  → calm final state; no fireworks

run.failed
  → persistent failure explanation
```

Do not animate everything the same way.

---

# 75. SUCCESS / COMPLETION EXPERIENCE

Completion should be satisfying but understated.

Example:

```text
COMPLETED

Weekly operational package

7 steps completed
9 verifications passed
3 artifacts created
1 draft prepared

[ Review artifacts ]
[ Open timeline ]
[ New session ]
```

A tiny checkmark transition is sufficient.

No confetti.

---

# 76. CANCELLATION EXPERIENCE

Cancellation is a first-class state.

```text
CANCELLED

The run was stopped by the user.

Completed steps remain available for inspection.

[ View evidence ]
[ Start new run ]
```

Preserve evidence; do not visually erase the work.

---

# 77. RECOVERY EXPERIENCE

Recovery should feel like a controlled engineering process.

```text
VERIFICATION FAILED
        ↓
RECOVERY 1/2
        ↓
RETRY
        ↓
VERIFY
        ↓
✓ RECOVERED
```

If recovery fails:

```text
RECOVERY EXHAUSTED

No further automated action taken.

[ Inspect failure ]
```

---

# 78. AGENT PARALLELISM VISUALIZATION

When multiple agents work in parallel, show concurrency through lanes.

```text
RUN
│
├── Writer      ●────────────✓
│
├── Office      ●───────●────✓
│
├── Computer    ●──●─────────✓
│
└── Verifier                 ●──✓
```

The UI should not imply parallel execution unless backend events show it.

A compact lane layout is better than a wall of simultaneous cards.

---

# 79. AGENT/TOOL/VERIFICATION COLOR DISCIPLINE

Use color by meaning, not by entity type.

Do not do:

```text
writer = purple
computer = blue
browser = orange
verifier = green
```

That becomes a circus.

Instead:

```text
all entities → monochrome
semantic state → small accent
```

This creates the restrained editor feel.

---

# 80. DESIGNING FOR TRUST

The product's key trust signals are visual clarity and evidence.

The interface must visually distinguish:

```text
PROPOSED
AUTHORIZED
EXECUTED
OBSERVED
VERIFIED
APPROVED
```

Do not collapse them into one green “done” badge.

This is particularly important for:

- computer actions
- email/send actions
- artifact creation
- browser actions
- external effects

---

# 81. SECURITY-AWARE UI

Never display:

- credentials
- API secrets
- tokens
- passwords
- raw private keys
- hidden environment values

When backend events include sensitive payloads, render a safe summary.

Example:

```text
Credential used
[redacted by runtime]
```

The frontend is not a secrets inspector.

---

# 82. NO RAW CHAIN-OF-THOUGHT PANEL

A high-quality AI workstation does not need to expose hidden reasoning.

Instead show:

```text
PLAN SUMMARY
CONTEXT USED
TOOLS SELECTED
CURRENT STEP
DECISION SUMMARY
VERIFICATION RESULT
```

These make the agent observable without presenting hidden internal reasoning.

---

# 83. “MODEL” UX

Model selection should be secondary to the task.

Use compact metadata:

```text
local · Gemma · vision
```

A model inspector can reveal:

```text
provider
model
capabilities
profile
temperature if exposed
context limit if exposed
telemetry if available
```

Do not make model selection look like shopping for consumer AI characters.

---

# 84. THE VISUAL VOCABULARY OF SYNCNODE

Use these words as design metaphors:

```text
node
link
edge
flow
observe
verify
evidence
trace
workspace
runtime
local
context
artifact
agent
policy
approval
recovery
```

A node motif can be reflected subtly in:

- graph nodes
- timeline markers
- status indicators
- small connector lines

Do not cover the UI with literal circles everywhere.

---

# 85. BRAND MARK / LOGOTYPE

The SyncNode wordmark should be:

- lowercase or restrained title casing
- compact
- geometric
- highly legible
- monochrome
- subtle enough to sit in the top chrome

On splash, it can be larger.

In the workbench, it should become tiny product chrome.

Suggested lockup:

```text
syncnode
```

with optional tiny descriptor:

```text
local agentic workbench
```

---

# 86. SPLASH SCREEN PREMIUM EFFECT OPTIONS

Choose **at most one** of these at a time:

### Option A — Light sweep

A nearly invisible horizontal light sweep crosses behind the wordmark once.

### Option B — Grid reveal

A microscopic technical grid fades in and out.

### Option C — Text mask reveal

The wordmark resolves from a low-opacity mask.

### Option D — Node line draw

One or two thin node connections draw under the wordmark.

### Option E — Noise texture

Barely visible monochrome film/noise texture.

Never combine all five.

---

# 87. HOME SCREEN MICRO-EXPERIENCE

The home screen may include:

```text
recent runs
pinned workflows
local runtime status
knowledge shortcuts
new task input
```

All are secondary to the main “start a local task” interaction.

---

# 88. FIRST-RUN EXPERIENCE

First launch should gracefully introduce the system without becoming a tutorial-heavy SaaS flow.

Suggested:

```text
SyncNode

Local runtime is ready.

Model        ready
Workspace    ready
Computer     ready
Knowledge    empty

[ Start your first local workflow ]
```

Use real health information.

---

# 89. DESIGN SYSTEM DOCUMENTATION INSIDE THE REPO

Create a developer-facing visual reference page, for example:

```text
/dev/design-system
```

It should contain:

- colors
- typography
- spacing
- radius
- shadows
- buttons
- inputs
- menus
- dialogs
- badges
- timeline rows
- tool rows
- verification rows
- artifacts
- graph nodes
- approval dialog
- empty states
- error states
- loading states
- motion examples

This page should be the frontend's visual regression reference.

---

# 90. RECOMMENDED IMPLEMENTATION ORDER

Do not build screens in arbitrary order.

## Phase 1 — token foundation

```text
colors
spacing
type
borders
radius
shadows
motion
icons
```

## Phase 2 — shell

```text
Electron chrome
AppShell
left rail
center pane
right inspector
status bar
resizable panels
```

## Phase 3 — core interaction

```text
command palette
buttons
inputs
dialogs
sheets
tabs
menus
toasts
tooltips
```

## Phase 4 — run primitives

```text
RunHeader
RunStepList
AgentRow
ToolRow
Timeline
Status
Evidence
```

## Phase 5 — primary screens

```text
Splash
Home
Intent
Plan
Active Run
```

## Phase 6 — specialized screens

```text
Desktop
Graph
Artifacts
Knowledge
Learning
Audit
Settings
```

## Phase 7 — motion/polish

Only after functional layout is stable.

---

# 91. SCREEN-SPECIFIC DESIGN PRIORITIES

| Screen | Primary visual priority |
|---|---|
| Splash | premium identity + readiness |
| Home | immediate task creation |
| Intent | clarity of understood objective |
| Plan | operational structure |
| Active Run | current work + trace |
| Agents | parallel worker visibility |
| Desktop | real computer observation |
| Graph | dependencies + flow |
| Timeline | trustworthy history |
| Artifacts | evidence + file identity |
| Approval | decision safety |
| Knowledge | source/context relevance |
| Learning | measurable workflow memory |
| Audit | forensic clarity |
| Settings | predictable control |

---

# 92. “OPENCODE / IDE FEEL” CHECKLIST

The frontend should feel like an editor because it has:

```text
✓ command palette
✓ keyboard shortcuts
✓ compact persistent chrome
✓ split panes
✓ resizable panels
✓ contextual inspector
✓ tabs
✓ dense rows
✓ terminal/log views
✓ mono metadata
✓ run/workspace identity
✓ stateful navigation
✓ persistent workspace layout
✓ focus mode
✓ contextual actions
✓ subtle status indicators
✓ strong information hierarchy
```

It should **not** feel like an editor because it has a fake code editor everywhere.

The goal is the interaction grammar, not literal imitation.

---

# 93. “PREMIUM” CHECKLIST

Premium quality should come from:

```text
alignment
spacing
hierarchy
consistency
motion timing
responsive behavior
accessibility
state completeness
performance
content clarity
```

Not from:

```text
more gradients
more glow
more particles
more blur
more 3D
more cards
more animation
```

---

# 94. DESIGN SYSTEM FAILURE MODES TO WATCH FOR

## Failure 1 — Library soup

Symptoms:

```text
Radix button
daisyUI input
Aceternity card
Magic UI hover
React Bits loader
Tabler icon
Lucide icon
```

all on one screen.

Fix: normalize at the component layer.

## Failure 2 — Every page looks like a dashboard

Fix: use editor/workbench structures.

## Failure 3 — Too much black with no hierarchy

Fix: use surface steps and borders.

## Failure 4 — Too much gray text

Fix: keep primary text bright and secondary text legible.

## Failure 5 — Motion everywhere

Fix: animate only meaningful state transitions.

## Failure 6 — Fake “AI” personality

Fix: let actual execution evidence communicate intelligence.

## Failure 7 — Huge empty screen with tiny content

Fix: add useful contextual metadata/panels, not decoration.

---

# 95. FINAL DESIGN NORTH STAR

At any point, the product should be describable visually as:

> **A quiet black developer workstation where a local multi-agent system is doing visible, verifiable work.**

The user should feel:

```text
I know where I am.
I know what the system is doing.
I can inspect the evidence.
I can intervene.
I can approve sensitive actions.
I can see the artifacts.
I can trace what happened.
```

That is the premium experience.

---

# 96. FINAL HANDOFF TO THE FRONTEND IMPLEMENTER

Implement this document as the visual foundation for the **Electron frontend only**.

Before writing UI code:

1. Read `01_idea.md` through the current architecture docs.
2. Read `FRONTEND_MASTER.md`.
3. Read `ELECTRON_ARCHITECTURE.md`.
4. Read `FRONTEND_API_INTEGRATION.md`.
5. Read `FRONTEND_SSE_STATE_MODEL.md`.
6. Read `FRONTEND_AGENT_TIMELINE.md`.
7. Read `FRONTEND_SCREEN_SPEC.md`.
8. Read `FRONTEND_APPROVAL_FLOW.md`.
9. Read `FRONTEND_ARTIFACT_EVIDENCE.md`.
10. Use this file as the **visual/UI-system authority**.

Then implement in this order:

```text
TOKENS
  ↓
COMPONENT FOUNDATION
  ↓
ELECTRON SHELL
  ↓
WORKSPACE LAYOUT
  ↓
RUN/AGENT/TOOL/EVIDENCE PRIMITIVES
  ↓
SPLASH
  ↓
HOME
  ↓
INTENT
  ↓
PLAN
  ↓
ACTIVE RUN
  ↓
DESKTOP
  ↓
GRAPH
  ↓
TIMELINE
  ↓
ARTIFACTS
  ↓
APPROVAL
  ↓
KNOWLEDGE
  ↓
LEARNING
  ↓
AUDIT
  ↓
SETTINGS
  ↓
MOTION + ACCESSIBILITY + RESPONSIVENESS
  ↓
VISUAL QA
```

### Backend boundary — final reminder

```text
DO NOT MODIFY:
- backend Python
- FastAPI routes
- LangGraph graph
- model gateway
- model router
- agents
- tool registry
- execution engine
- computer runtime
- document runtime
- browser runtime
- verification/recovery logic
- database schema
- SSE event names
- API response schemas
- backend tests
```

The frontend may:

```text
- consume REST
- consume SSE
- render backend state
- maintain frontend UI state
- persist local visual preferences
- transform backend data into presentation models
- animate real state transitions
- provide keyboard/workspace behavior
```

### Final principle

**Do not chase “cool UI.” Build a coherent workstation.**

The result should be visually minimal, technically dense, calm, premium, observable, accessible, performant, and unmistakably an AI-native developer/operations environment.

---

## Appendix A — Quick design recipe for any new component

Before creating a component, answer:

```text
1. What information does it communicate?
2. What action does it enable?
3. What states can it have?
4. Which existing SyncNode component is closest?
5. Can shadcn/Base UI/Radix provide the behavior?
6. Does it need custom visuals?
7. Does it need motion?
8. Does it need keyboard support?
9. Does it need a responsive mode?
10. Is it actually necessary?
```

Then implement.

---

## Appendix B — Quick “Is this AI slop?” test

Ask:

```text
Would this still look good if the word “AI” disappeared?
Would this look natural inside a professional IDE?
Does every animated element communicate real state?
Can I scan the screen in 2 seconds and know what matters?
Can I find evidence without opening five modals?
Does the UI look good at midnight on a developer's monitor?
```

If the answer is no, simplify.

---

## Appendix C — Quick visual acceptance standard

A screen is ready when:

```text
[✓] coherent with the SyncNode shell
[✓] monochrome first
[✓] uses shared tokens
[✓] uses shared components
[✓] has complete states
[✓] has keyboard/focus behavior
[✓] has responsive behavior
[✓] has meaningful motion only
[✓] displays only backend-backed truth
[✓] feels like a workstation, not a marketing page
[✓] visually matches the supplied OpenCode/editor references in restraint and density
```

**End of `FRONTEND_UI_DESIGN_SYSTEM.md`**
