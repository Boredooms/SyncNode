Yep. I’d make `website/MASTER_DESIGN.md` the **single source of truth for the public SyncNode website**, and I’d base it on the actual repository structure plus the visual references you attached.

One important correction before the design gets implemented: the GitHub `website/` directory currently contains content files such as `README.md`, `idea.md`, `features.md`, `use_cases.md`, `roadmap.md` and `faq.md`; it is **not yet the final React/Vite site structure**. So the new website should be built as a proper Vite React application inside `website/`, while preserving those documents as content/reference material rather than treating them as the application itself. [SyncNode repository](https://github.com/Boredooms/SyncNode?utm_source=chatgpt.com)

Also, the uploaded visual references establish a very specific aesthetic direction: **black-first, restrained grayscale, cinematic, editorial, minimal, premium**, rather than a colorful SaaS landing page.

Below is the master file I would put at:

```text
C:\syncnode\website\MASTER_DESIGN.md
```

````md
# SyncNode Website — Master Design System & Implementation Blueprint

> **Project:** SyncNode
> 
> **Purpose:** Public product website for SyncNode — a sovereign local AI workbench for confidential industrial work.
>
> **Repository:** https://github.com/Boredooms/SyncNode
>
> **Application location:** `website/`
>
> **Deployment target:** Vercel
>
> **Primary runtime:** React + Vite + TypeScript
>
> **Primary visual language:** Black / graphite / cool grayscale / restrained white
>
> **Product positioning:** Sovereign industrial AI + real agentic execution + verification + governance

---

# 1. WEBSITE PURPOSE

The website is not a generic AI landing page.

It is the public-facing explanation of SyncNode.

Its job is to communicate, in order:

1. What SyncNode is.
2. Why confidential organizations need it.
3. Why ordinary cloud AI does not fit this environment.
4. How SyncNode works.
5. What SyncNode can actually automate.
6. What the real desktop product looks like.
7. Why the execution model is trustworthy.
8. How the system is different from a normal chatbot.
9. How to download the Windows application.
10. How the project can evolve into a deployable enterprise system.

The website must feel like a **serious developer/industrial product**, not a hackathon microsite.

---

# 2. PRIMARY WEBSITE MESSAGE

## Main statement

# THINK LOCALLY.
# ACT INTELLIGENTLY.

Secondary statement:

> SyncNode turns confidential work into locally executed, verified and auditable workflows — without requiring your data to leave the environment you control.

Supporting line:

> Local models. Local knowledge. Real automation. Human control.

---

# 3. WEBSITE EXPERIENCE

The visitor should feel this progression:

```text
CURIOUS
   ↓
WHAT IS THIS?
   ↓
WHY DOES IT MATTER?
   ↓
HOW DOES IT WORK?
   ↓
SHOW ME
   ↓
I SEE THE AUTOMATION
   ↓
I UNDERSTAND THE TRUST MODEL
   ↓
I WANT THE APP
````

The website should therefore behave almost like a product walkthrough rather than a conventional marketing page.

---

# 4. INFORMATION ARCHITECTURE

The website MUST be multi-page.

Do NOT implement the entire site as one huge scroll.

Required pages:

```text
/
├── /
├── /about
├── /features
├── /workflow
├── /demo
├── /security
├── /architecture
├── /use-cases
├── /download
├── /faq
└── /roadmap
```

Optional future pages:

```text
/agents
/knowledge
/integrations
/docs
/changelog
```

---

# 5. PRIMARY NAVIGATION

Desktop header:

```text
SYNCNODE

Product
  About
  Features
  Workflow
  Architecture

Explore
  Demo
  Use Cases
  Security
  Roadmap

Resources
  FAQ
  GitHub

[ Download for Windows ]
```

The header must remain visually light.

No huge mega-menu.

No heavy shadows.

No excessive badges.

---

# 6. HEADER BEHAVIOR

Initial state:

* transparent
* black background
* logo left
* navigation center
* download action right

On scroll:

* subtle dark surface
* slight blur
* thin border
* compact height
* no exaggerated glass effect

Header transition:

```text
transparent
↓
soft graphite surface
↓
border appears
↓
slight compression
```

Use GSAP or Framer Motion for the transition.

---

# 7. GLOBAL VISUAL LANGUAGE

## Background

Primary:

```text
#080808
```

Secondary:

```text
#0D0D0D
```

Panels:

```text
#111111
```

Elevated:

```text
#151515
```

Borders:

```text
#222222
#292929
```

Text:

```text
#F2F2F2
#D4D4D4
#A4A4A4
#737373
```

Muted:

```text
#555555
```

Optional tiny positive signal:

```text
#8BE3B0
```

Optional warning:

```text
#D6A85B
```

The website must remain predominantly monochrome.

Do not create:

* purple AI gradients
* neon cyan
* rainbow cards
* blue SaaS blobs
* excessive green
* giant glowing orbs

---

# 8. VISUAL REFERENCE DIRECTION

The attached references establish:

* cinematic grayscale
* large negative space
* soft photographic textures
* fog / smoke / mineral / graphite surfaces
* large editorial typography
* extremely restrained color
* premium product-film feeling
* minimal UI chrome
* dark black-first composition

Use these references as the design language.

Do NOT reproduce their exact compositions.

The visual system should feel original to SyncNode.

---

# 9. TYPOGRAPHY

Primary:

```text
Inter
```

Alternative:

```text
Geist
```

Use one family consistently.

Optional technical monospace:

```text
JetBrains Mono
```

Use monospace ONLY for:

* model names
* technical labels
* system states
* logs
* architecture annotations
* code
* event traces

Do not turn the whole website into a developer terminal.

---

# 10. TYPOGRAPHIC SCALE

Hero:

```text
clamp(4rem, 10vw, 10rem)
```

Section heading:

```text
clamp(2.5rem, 5vw, 5rem)
```

Large statement:

```text
clamp(2rem, 4vw, 4rem)
```

Body:

```text
16–20px
```

Small:

```text
12–14px
```

Technical labels:

```text
10–12px
letter-spacing: 0.14em
text-transform: uppercase
```

The typography should feel editorial.

---

# 11. MOTION SYSTEM

Motion is important, but must never become decorative noise.

The animation philosophy is:

```text
slow
precise
weighted
physical
intentional
```

Primary motion libraries:

* GSAP
* Framer Motion

Secondary:

* Anime.js
* ReactBits
* Lottie
* Lenis

Use each for a specific reason.

Do NOT make five libraries control the same animation.

---

# 12. MOTION LANGUAGE

## Text entrance

Preferred:

```text
opacity
+
translateY
+
small blur reduction
```

Example:

```text
heading
starts:
y = 50
opacity = 0
filter = blur(10px)

ends:
y = 0
opacity = 1
filter = blur(0)
```

---

## Card entrance

Use:

```text
scale .96 → 1
opacity 0 → 1
y 32 → 0
```

---

## Image/video reveal

Use masked reveal:

```text
clip-path
or
scale + overflow-hidden
```

---

# 13. TEXT ANIMATION MODES

The site should use multiple text styles.

### Fall In

Characters descend lightly and settle into place.

Use for:

* hero statements
* section headings

### Rise In

Words/cards travel upward from below the viewport.

Use for:

* feature grids
* workflow cards

### Chroma

Subtle light-to-dark shift over text.

Use for:

* key labels
* transition sections

### Tracking Reveal

Letters begin slightly expanded and tighten into place.

Use for:

* technical labels
* section metadata

### Blur Resolve

Text appears through a soft blur reduction.

Use sparingly.

---

# 14. SMOOTH SCROLL

Use:

```text
Lenis
```

for page-level smooth scrolling.

GSAP ScrollTrigger should consume the same scroll source.

Never create multiple competing smooth-scroll implementations.

---

# 15. GLOBAL COMPONENT SYSTEM

Create:

```text
components/
├── Header.tsx
├── Footer.tsx
├── PageTransition.tsx
├── Cursor.tsx
├── MagneticButton.tsx
├── TextReveal.tsx
├── SplitText.tsx
├── Reveal.tsx
├── ChromaText.tsx
├── BlurText.tsx
├── SectionLabel.tsx
├── NoiseOverlay.tsx
├── GridBackground.tsx
├── VideoFrame.tsx
├── DeviceFrame.tsx
├── BrowserFrame.tsx
├── TerminalFrame.tsx
├── FeatureCard.tsx
├── FeatureGrid.tsx
├── WorkflowNode.tsx
├── WorkflowGraph.tsx
├── AgentCard.tsx
├── StatBlock.tsx
├── QuoteBlock.tsx
├── Timeline.tsx
├── LogoMark.tsx
├── DownloadButton.tsx
└── Icon.tsx
```

---

# 16. COMPONENT LIBRARIES

Use libraries as supporting infrastructure rather than blindly importing everything.

Preferred:

### Base UI

* shadcn/ui
* Radix UI

### Icons

* Lucide React

### Rich interaction

* GSAP
* Framer Motion

### Motion / decorative

* ReactBits
* Anime.js
* Lottie

### Optional inspiration/component sources

* Aceternity UI
* Magic UI
* Vercel UI patterns
* DaisyUI patterns where appropriate
* Motion Primitives
* Cult UI
* Origin UI
* Hover.dev patterns
* React Aria where accessibility requires it

IMPORTANT:

Do not create a visual mashup of every library.

The visitor should never be able to tell which component came from which library.

Everything must look like one SyncNode design system.

---

# 17. ICON RULE

Primary icon system:

```text
Lucide React
```

Icons must be:

* monochrome
* thin
* geometric
* small
* aligned to text

Animated icons may use:

* Lottie
* SVG path animation
* GSAP

No emoji icons in production UI.

---

# 18. LOTTIE RULES

Use Lottie only for:

* loading
* sovereignty/security visual
* model routing visual
* system initialization
* subtle empty-state visuals

Do not place animated Lottie illustrations everywhere.

---

# 19. WEBSITE ROUTES

Each page should have its own React route.

Use:

```text
react-router-dom
```

Structure:

```text
src/
├── app/
│   ├── router.tsx
│   └── providers.tsx
│
├── pages/
│   ├── Home/
│   ├── About/
│   ├── Features/
│   ├── Workflow/
│   ├── Demo/
│   ├── Security/
│   ├── Architecture/
│   ├── UseCases/
│   ├── Download/
│   ├── FAQ/
│   └── Roadmap/
│
├── components/
├── animations/
├── data/
├── lib/
├── styles/
└── assets/
```

---

# 20. HOME PAGE

Route:

```text
/
```

The home page is the strongest visual experience.

---

## HOME — HERO

Large black canvas.

Minimal logo.

Large statement:

# Think locally.

# Act intelligently.

Subheadline:

> A sovereign AI workbench for confidential work — designed to reason locally, act through controlled tools, verify the result, and keep your data inside the environment you control.

Actions:

```text
[ Download for Windows ]
[ Explore SyncNode ]
```

Secondary:

```text
LOCAL AI
NO CLOUD REQUIRED
VERIFIED EXECUTION
```

---

# 21. HERO VISUAL

Use a cinematic background constructed from:

* dark fog
* graphite texture
* soft grayscale gradients
* subtle noise
* slow-moving particles
* sparse geometric system lines

Do NOT use:

* floating AI brain
* robots
* neon neural networks
* cliché cyberpunk imagery

The product is sophisticated because it is quiet.

---

# 22. HERO PRODUCT MARK

Use the SyncNode wordmark extremely large but very low contrast.

Example:

```text
SYNCNODE
```

at:

```text
opacity: 0.06–0.10
```

behind the primary hero statement.

The logo should almost disappear into the environment.

---

# 23. HERO LOADER / SYSTEM BOOT

Before the home content appears, use a short system initialization sequence.

Example:

```text
SYNCNODE

INITIALIZING LOCAL RUNTIME
✓ MODEL GATEWAY
✓ LOCAL KNOWLEDGE
✓ EXECUTION ENGINE
✓ VERIFICATION

WORKSPACE READY
```

Then reveal the hero.

Duration:

```text
1.5–3 seconds
```

Must be skippable after first visit.

Store completion in localStorage.

---

# 24. HOME — THE PROBLEM

Transition section:

Large statement:

> Confidential work should not have to leave the place where it matters.

Then show:

```text
CONFIDENTIAL DOCUMENT
       ↓
PUBLIC AI
       ↓
LOSS OF CONTROL
```

versus:

```text
CONFIDENTIAL DOCUMENT
       ↓
SYNCNODE
       ↓
LOCAL EXECUTION
```

Use a slow horizontal transition.

---

# 25. HOME — THE CORE IDEA

Headline:

> AI should not be the final authority.

Then animated chain:

```text
UNDERSTAND
↓
PLAN
↓
AUTHORIZE
↓
ACT
↓
OBSERVE
↓
VERIFY
```

Each word should appear sequentially.

Then:

> The model proposes. The system validates.

This is the most important conceptual statement on the website.

---

# 26. HOME — PRODUCT DIFFERENCE

Three large vertical cards:

```text
THINK
Local AI reasoning

ACT
Real local execution

PROVE
Verification + audit
```

Cards rise in from below.

Hover:

* subtle lift
* border brightens
* icon animates
* internal line moves

---

# 27. HOME — PRODUCT PREVIEW

Use a large cinematic Electron application frame.

Include the actual SyncNode UI.

Tabs:

```text
Overview
Agents
Automation
Desktop
Artifacts
Evidence
Audit
```

Do not fake UI screenshots with random HTML if actual product screenshots exist.

Use the real screenshots/video from `website/videos/` or generated product captures.

---

# 28. HOME — LIVE WORKFLOW

Headline:

> From a sentence to real work.

Animation:

```text
User goal
 ↓
Intent
 ↓
Plan
 ↓
Agents
 ↓
Tools
 ↓
Execution
 ↓
Observation
 ↓
Verification
 ↓
Deliverable
```

Each node should activate as the user scrolls.

---

# 29. HOME — SOVEREIGNTY

Large statement:

# Your AI.

# Your machine.

# Your data.

Below:

```text
LOCAL INFERENCE
LOCAL KNOWLEDGE
LOCAL FILES
LOCAL TOOLS
LOCAL AUDIT
```

Add a tiny network activity visualization.

It should show:

```text
SYNCNODE
   │
   ├── Ollama
   ├── Local DB
   ├── Local Files
   └── Local Apps

EXTERNAL AI
   X
```

Do not claim "air-gapped" unless the deployment actually enforces and demonstrates it.

---

# 30. HOME — MRPL / INDUSTRIAL CONTEXT

Introduce the real problem class.

Headline:

> Built for work where "just upload it" is not an option.

Explain examples:

* engineering documents
* inspection reports
* project packages
* procurement documentation
* calculations
* internal manuals
* confidential correspondence

Avoid claiming access to confidential MRPL data.

Use public/project-derived context only.

---

# 31. HOME — FEATURE PREVIEW

Six cards:

```text
MULTI-MODEL
Choose the right local model

MULTIMODAL
Read documents, scans and images

AGENTIC
Plan and coordinate specialist work

AUTOMATION
Operate local tools and applications

VERIFICATION
Check what actually happened

AUDIT
Keep the complete execution trail
```

---

# 32. HOME — DEMO CTA

Large statement:

> See the system work.

Buttons:

```text
[ Watch the workflow ]
[ Explore the demo ]
```

Video poster should use the best frame from:

```text
website/videos/
```

---

# 33. HOME — DOWNLOAD

Final CTA:

# Bring sovereign AI to your desktop.

Buttons:

```text
[ Download for Windows ]
[ View on GitHub ]
```

Download target:

```text
GitHub repository
↓
Windows release
↓
EXE
```

The download button must never point to a fake file.

Use the actual GitHub release asset URL once published.

Repository:

```text
https://github.com/Boredooms/SyncNode
```

---

# 34. ABOUT PAGE

Route:

```text
/about
```

Hero:

> SyncNode is not a chatbot.

Then:

> It is a local execution environment for confidential work.

Sections:

1. Why this exists
2. The trust problem
3. Local intelligence
4. Agentic execution
5. Verification
6. Human control
7. The philosophy behind SyncNode

Use large typography and sparse layouts.

---

# 35. ABOUT — ORIGIN

Show:

```text
CHAT
↓
RAG
↓
AGENT
↓
EXECUTION
↓
VERIFIED EXECUTION
```

Explain why each stage was insufficient alone.

---

# 36. ABOUT — DESIGN PRINCIPLE

Large quote:

> The model proposes.
> Deterministic infrastructure validates, authorizes, executes and verifies.

Make this an iconic visual statement.

---

# 37. FEATURES PAGE

Route:

```text
/features
```

Feature sections:

### Local Model Runtime

### Dynamic Model Routing

### Local Knowledge

### Multimodal Understanding

### Specialist Agents

### Controlled Tools

### Sandbox

### Desktop Automation

### Office Automation

### Browser Automation

### Verification

### Recovery

### Human Approval

### Audit

### Workflow Memory

Each section gets:

* explanation
* icon
* animated visual
* product screenshot
* small technical detail

---

# 38. WORKFLOW PAGE

Route:

```text
/workflow
```

This should be one of the most impressive pages.

Use a full-screen vertical execution sequence.

```text
01
UNDERSTAND

02
GROUND

03
PLAN

04
DELEGATE

05
AUTHORIZE

06
EXECUTE

07
OBSERVE

08
VERIFY

09
RECOVER

10
APPROVE

11
DELIVER

12
REMEMBER
```

Each phase changes the center visual.

---

# 39. WORKFLOW VISUAL

At the center:

```text
┌───────────────────────────────┐
│        CURRENT STEP            │
│                               │
│     ENGINEERING ANALYSIS      │
│                               │
│  Local model selected         │
│  4 sources retrieved          │
│  Calculation running          │
└───────────────────────────────┘
```

Around it:

```text
MODEL
KNOWLEDGE
AGENT
TOOL
OBSERVATION
VERIFIER
```

Animate connections dynamically.

---

# 40. DEMO PAGE

Route:

```text
/demo
```

This should be a true visual product story.

Use the videos already stored in:

```text
website/videos/
```

Create a reusable video manifest:

```ts
const videos = {
  intro: "...",
  about: "...",
  features: "...",
  workflow: "...",
  prototype: "...",
  system: "..."
}
```

Do not hard-code filenames throughout the application.

---

# 41. VIDEO PRESENTATION

Every video should be displayed inside a product-film frame:

```text
┌────────────────────────────────────┐
│                                    │
│         VIDEO                      │
│                                    │
│                                    │
└────────────────────────────────────┘
```

Controls:

* play/pause
* sound toggle
* progress
* fullscreen

Use custom controls styled in SyncNode language.

No default browser UI where avoidable.

---

# 42. DEMO STORYLINE

The demo page should guide the visitor:

```text
01
USER GOAL

02
SYSTEM UNDERSTANDS

03
LOCAL KNOWLEDGE

04
PLAN

05
AGENTS

06
AUTOMATION

07
VERIFICATION

08
APPROVAL

09
REAL ARTIFACT
```

---

# 43. SECURITY PAGE

Route:

```text
/security
```

Headline:

# Sovereignty is not a badge.

# It is an execution property.

Show:

```text
LOCAL MODEL
↓
LOCAL DATA
↓
LOCAL TOOL
↓
LOCAL EXECUTION
↓
OBSERVATION
↓
AUDIT
```

Then:

```text
EXTERNAL AI API
DISABLED

LOCAL INFERENCE
ACTIVE

NETWORK
MONITORED

AUDIT
SHA-256
```

Never present decorative security language as proof.

---

# 44. SECURITY EVIDENCE

Create an animated evidence view:

```text
INPUT HASH
↓
MODEL SELECTED
↓
SOURCE RETRIEVED
↓
TOOL AUTHORIZED
↓
ACTION EXECUTED
↓
OUTPUT HASH
↓
VERIFIED
↓
AUDIT EVENT
```

This communicates the real SyncNode advantage.

---

# 45. ARCHITECTURE PAGE

Route:

```text
/architecture
```

Show the full architecture.

Top-level:

```text
USER
↓
ELECTRON
↓
FASTAPI
↓
ORCHESTRATOR
↓
MODEL ROUTER
↓
KNOWLEDGE
↓
AGENTS
↓
TOOLS
↓
EXECUTION
↓
OBSERVATION
↓
VERIFICATION
↓
RECOVERY
↓
APPROVAL
↓
AUDIT
```

Use interactive architecture nodes.

Hover:

```text
NAME
ROLE
INPUT
OUTPUT
TECHNOLOGY
```

---

# 46. ARCHITECTURE VISUAL LANGUAGE

Technical diagram should resemble:

```text
industrial control schematic
+
editorial typography
+
developer IDE
```

Not:

* generic AWS architecture
* colorful cloud architecture
* giant database cylinders
* rainbow microservices

---

# 47. USE CASES PAGE

Route:

```text
/use-cases
```

Main groups:

```text
ENGINEERING
MAINTENANCE
PROJECTS
PROCUREMENT
R&D
DOCUMENT WORK
COMPLIANCE
DESKTOP AUTOMATION
```

Each use case gets one complete mini workflow.

---

# 48. ENGINEERING USE CASE

```text
Inspection Report
+
Drawing
+
Historical Data

↓
Multimodal Understanding

↓
Local Knowledge

↓
Engineering Analysis

↓
Calculation

↓
Verification

↓
Approval Note
```

This should be the hero industrial use case.

---

# 49. PROJECT USE CASE

```text
Project package
↓
Document understanding
↓
Project structure
↓
Open actions
↓
Dependencies
↓
Summary
↓
Report / PPT
↓
Approval
```

---

# 50. PROCUREMENT USE CASE

```text
Vendor submission
↓
Specification
↓
Rule retrieval
↓
Technical comparison
↓
Deviation identification
↓
NFA
↓
Human approval
```

Never publish synthetic authority thresholds as real MRPL policy.

---

# 51. R&D USE CASE

```text
Engineering data
↓
Model routing
↓
Local analysis
↓
Sandboxed computation
↓
Plot
↓
Verification
↓
Technical report
```

---

# 52. DOWNLOAD PAGE

Route:

```text
/download
```

Headline:

# Run SyncNode locally.

Show:

```text
Windows
x64
Desktop application
Local AI
```

Primary CTA:

```text
DOWNLOAD FOR WINDOWS
```

Secondary:

```text
VIEW SOURCE ON GITHUB
```

GitHub:

```text
https://github.com/Boredooms/SyncNode
```

---

# 53. DOWNLOAD CARD

```text
SYNCNODE FOR WINDOWS

Desktop Workbench
Local-first
Electron

[ DOWNLOAD .EXE ]

Version
1.x.x

Requirements
Windows
Local model runtime
Compatible hardware
```

Version information should eventually come from the actual release metadata.

Do not hard-code false version numbers.

---

# 54. FAQ PAGE

Route:

```text
/faq
```

Topics:

### Does SyncNode require the cloud?

### Which models can it use?

### Can administrators add new models?

### How does verification work?

### Can it operate Windows applications?

### Can it work with PDFs and images?

### What happens when an action fails?

### How is approval handled?

### What gets stored?

### Can it run offline?

### Does SyncNode send data externally?

### Can it create Word, Excel and PowerPoint files?

Use accordion interaction from shadcn/Radix.

---

# 55. ROADMAP PAGE

Route:

```text
/roadmap
```

Timeline:

```text
LOCAL CORE
↓
AGENTIC WORKBENCH
↓
MULTIMODAL
↓
SEMANTIC KNOWLEDGE
↓
SANDBOXED COMPUTATION
↓
INDUSTRIAL DEPLOYMENT
```

Use labels:

```text
BUILT
INTEGRATING
PLANNED
```

Never use misleading "100% complete" language.

---

# 56. FOOTER

Footer should be minimal.

Left:

```text
SYNCNODE
Think locally. Act intelligently.
```

Links:

```text
Product
Architecture
Security
Demo
GitHub
Download
FAQ
```

Bottom:

```text
© SyncNode
Built for local-first AI execution.
```

---

# 57. PAGE TRANSITIONS

Every route change should have a small transition.

Preferred:

```text
black
↓
content fades
↓
new page rises
```

Do not use large spinning loaders for normal navigation.

Use the cinematic loader only for:

* first boot
* long media loading
* model/product film loading

---

# 58. CUSTOM LOADING SEQUENCE

Create:

```text
components/system/BootLoader.tsx
```

Sequence:

```text
SYNCNODE

LOCAL RUNTIME
..............

MODEL GATEWAY
READY

KNOWLEDGE
READY

EXECUTION
READY

WORKSPACE
READY
```

Then:

```text
fade out
↓
hero reveal
```

---

# 59. CURSOR SYSTEM

Desktop-only enhancement:

* custom circular cursor
* magnetic interactions
* text hover mode
* link hover mode

But:

* automatically disabled for touch devices
* disabled for reduced-motion users
* never interfere with accessibility

---

# 60. MAGNETIC BUTTONS

Download / primary CTA can use small magnetic motion.

Movement should be subtle:

```text
max 8–12px
```

Never extreme.

---

# 61. NOISE TEXTURE

Use one global noise overlay.

Properties:

```text
opacity: 0.025–0.05
mix-blend-mode: soft-light
pointer-events: none
```

This gives the monochrome design physical texture.

---

# 62. GRID / SCHEMATIC BACKGROUND

Use subtle background grids:

```text
1px lines
low opacity
large spacing
```

Animate only where needed.

No glowing neon grid.

---

# 63. VIDEO BACKGROUND

Video backgrounds should:

* autoplay muted
* loop
* preload appropriately
* respect reduced motion
* use poster fallback
* never dominate the page

Recommended visual treatment:

```text
video
+
black overlay
+
grain
+
slow scale
```

---

# 64. CARD LANGUAGE

Cards are:

* flat
* dark
* thin border
* low radius
* high typography quality

Avoid:

```text
huge rounded cards
floating colorful SaaS blocks
gradient blobs
```

Suggested radius:

```text
10–16px
```

for application-like components.

Large editorial modules may use:

```text
20–28px
```

---

# 65. SHADCN USAGE

Use shadcn components for:

* Button
* Dialog
* Accordion
* Tabs
* Tooltip
* Sheet
* Dropdown
* Scroll Area

Modify their styling heavily to fit SyncNode.

Do not ship untouched default shadcn styling.

---

# 66. REACTBITS USAGE

Use ReactBits-inspired interaction patterns for:

* split text
* magnetic buttons
* animated borders
* scroll reveals
* hover transitions

Again:

Do not visually mix unrelated styles.

---

# 67. ACETERNITY / MAGIC UI

Use only patterns that fit the monochrome design:

Good:

* text reveals
* spotlight
* subtle borders
* tracing effects
* smooth transitions

Avoid:

* giant glowing gradients
* colorful blobs
* cosmic backgrounds

---

# 68. VERSEL UI INFLUENCE

Use Vercel-like principles:

* strong typography
* high contrast
* excellent spacing
* technical clarity
* restrained decoration
* fast interaction

Do NOT clone the Vercel website.

---

# 69. DAISY UI INFLUENCE

Only use:

* spacing ideas
* accessible component patterns
* responsive primitives

Never allow DaisyUI's default color system to dominate.

---

# 70. ANIME.JS

Anime.js can be used for:

* SVG path motion
* system graph transitions
* tiny icon sequences

GSAP remains the main orchestration engine.

---

# 71. GSAP

GSAP handles:

* ScrollTrigger
* master page timelines
* text reveals
* horizontal scroll
* pinned sections
* workflow graph activation
* image/video parallax

All GSAP timelines must be cleaned up properly in React.

---

# 72. FRAMER MOTION

Use Framer Motion for:

* React component lifecycle animations
* dialogs
* drawers
* card interactions
* page transitions
* state transitions

Avoid using GSAP and Framer Motion to animate the exact same element simultaneously.

---

# 73. LOTTIE

Create one reusable:

```text
LottiePlayer.tsx
```

It must support:

```ts
autoplay
loop
speed
lazyLoad
fallback
```

---

# 74. RESPONSIVE DESIGN

Mobile is not an afterthought.

Breakpoints:

```text
mobile
tablet
desktop
wide
```

Mobile navigation:

```text
SYNCNODE
        [menu]
```

Full-screen menu:

```text
Product
Explore
Resources

DOWNLOAD
```

---

# 75. MOBILE HERO

On mobile:

* no enormous 10vw typography that destroys layout
* preserve cinematic negative space
* reduce video complexity
* disable custom cursor
* keep CTA accessible

---

# 76. ACCESSIBILITY

Required:

* keyboard navigation
* visible focus state
* semantic headings
* alt text
* ARIA labels
* reduced-motion mode
* video captions where applicable
* contrast compliance
* accessible dialogs

---

# 77. REDUCED MOTION

Respect:

```css
prefers-reduced-motion
```

When enabled:

* disable parallax
* disable cursor animations
* reduce page transitions
* reduce text split animation
* keep content immediately visible

---

# 78. PERFORMANCE

This site must remain fast despite rich animation.

Rules:

* lazy-load videos
* lazy-load Lottie
* lazy-load heavy components
* use poster images
* avoid huge uncompressed assets
* use modern image formats
* prefetch route chunks sensibly
* don't mount all page animations globally

---

# 79. ASSET STRUCTURE

Create:

```text
website/
├── public/
│   ├── favicon.svg
│   ├── og-image.png
│   ├── screenshots/
│   ├── posters/
│   ├── lottie/
│   └── videos/
│
└── src/
    └── assets/
```

If videos already exist in:

```text
website/videos/
```

either serve them through `public/videos/` or establish one consistent asset pipeline.

Do not duplicate large media unnecessarily.

---

# 80. VIDEO DIRECTORY

Assuming current source files correspond roughly to:

```text
About the project 2.0
About the Project
Features
Features 2.0
Prototype
Prototype 2.0
Website main intro
```

Create metadata such as:

```ts
export const videoCatalog = {
  aboutProject: {
    title: "About the Project",
    section: "about",
    src: "/videos/..."
  },

  features: {
    title: "Features",
    section: "features",
    src: "/videos/..."
  },

  prototype: {
    title: "Prototype Walkthrough",
    section: "demo",
    src: "/videos/..."
  },

  intro: {
    title: "SyncNode",
    section: "hero",
    src: "/videos/..."
  }
}
```

The actual filenames must be discovered from the repository rather than guessed.

---

# 81. DATA-DRIVEN CONTENT

Do not hard-code repeated content in JSX.

Create:

```text
src/data/
├── navigation.ts
├── features.ts
├── workflows.ts
├── useCases.ts
├── faq.ts
├── roadmap.ts
└── videos.ts
```

This makes the site easy to maintain.

---

# 82. DOWNLOAD BEHAVIOR

The download button should:

1. Open the official GitHub release asset.
2. Never pretend to host a nonexistent EXE.
3. Show fallback instructions if no release exists.
4. Include source-code link.

Preferred future behavior:

```text
Download
↓
Latest Windows release
↓
SyncNode-Setup.exe
```

---

# 83. GITHUB LINK

Official source:

```text
https://github.com/Boredooms/SyncNode
```

Open externally.

Use Lucide GitBranch/Github icon.

---

# 84. SEO

Set:

```text
title:
SyncNode — Sovereign Local AI Workbench

description:
A sovereign local AI workbench for confidential work. Run open-weight AI locally, execute controlled workflows, verify results and keep sensitive data inside your environment.

keywords:
local AI
sovereign AI
on-premise AI
agentic AI
industrial AI
offline AI
private AI
AI workbench
```

Do not keyword-stuff.

---

# 85. OPEN GRAPH

Create:

```text
og-image.png
```

Design:

```text
black
+
SYNCNODE
+
THINK LOCALLY. ACT INTELLIGENTLY.
```

Minimal.

No giant feature collage.

---

# 86. FAVICON

Use:

```text
SyncNode N / node symbol
```

Minimal monochrome SVG.

---

# 87. ERROR PAGE

Create:

```text
/404
```

Visual:

```text
NODE NOT FOUND
```

Then:

```text
[ Return Home ]
```

Subtle animated node graph.

---

# 88. SCROLL STORYTELLING

The site should use three scales of motion.

### Micro

buttons
icons
hover

### Meso

cards
sections
images

### Macro

page transitions
workflow graph
hero reveal
horizontal storytelling

This hierarchy prevents animation overload.

---

# 89. HERO STORY

Hero timeline:

```text
BOOT
↓
WORDMARK
↓
HEADLINE
↓
SUBHEAD
↓
CTA
↓
SYSTEM STATUS
↓
SCROLL
```

---

# 90. PRODUCT FILM LANGUAGE

Whenever a video appears:

```text
media
↓
caption
↓
one sentence insight
```

Example:

> SyncNode does not stop at reasoning. It moves from plan to controlled local execution.

---

# 91. FEATURE STORYTELLING

Never show:

```text
Feature name
+
two-line description
+
icon
```

over and over.

Instead:

```text
FEATURE
↓
WHY IT MATTERS
↓
HOW IT WORKS
↓
WHAT THE USER SEES
```

Every major feature should answer all four.

---

# 92. INDUSTRIAL STORYTELLING

The most important public use-case should be:

```text
Inspection
↓
Local evidence
↓
Analysis
↓
Calculation
↓
Approval
↓
Verified result
```

Then secondary workflows:

```text
Project engineering
Procurement
R&D
Document automation
Desktop automation
```

This makes the site specific without pretending to expose confidential MRPL systems.

---

# 93. TRUST STORY

The website should make this visual:

```text
MODEL
does not directly control the machine

↓

POLICY
decides what is permitted

↓

TOOL
provides controlled interface

↓

EXECUTOR
performs action

↓

OBSERVER
records reality

↓

VERIFIER
checks reality

↓

AUDIT
records proof
```

This is the central SyncNode differentiator.

---

# 94. FINAL WEBSITE EXPERIENCE

The visitor should leave understanding:

```text
SYNCNODE

LOCAL AI
+
LOCAL KNOWLEDGE
+
SPECIALIST AGENTS
+
REAL AUTOMATION
+
VERIFICATION
+
HUMAN CONTROL
+
AUDIT
```

---

# 95. IMPLEMENTATION ORDER

Build in this order.

## Phase 1

Project bootstrap:

* React
* Vite
* TypeScript
* React Router
* Tailwind
* shadcn
* Lucide
* GSAP
* Framer Motion
* Lenis

---

## Phase 2

Core shell:

* header
* footer
* route system
* page transitions
* theme tokens
* typography
* global noise
* responsive system

---

## Phase 3

Home page.

Do not move forward until Home feels premium.

---

## Phase 4

About + Features.

---

## Phase 5

Workflow + Architecture.

---

## Phase 6

Demo + video system.

---

## Phase 7

Security + Use Cases.

---

## Phase 8

Download + FAQ + Roadmap.

---

## Phase 9

Performance / SEO / accessibility.

---

## Phase 10

Final visual QA.

---

# 96. REQUIRED FINAL QA

Before deployment, verify every route.

```text
/
 /about
 /features
 /workflow
 /demo
 /security
 /architecture
 /use-cases
 /download
 /faq
 /roadmap
```

Verify:

* no broken routes
* no console errors
* no missing media
* no broken animations
* no layout shifts
* no mobile overflow
* keyboard navigation works
* reduced motion works
* videos load correctly
* GitHub links work
* download links are real
* no fake statistics
* no fake enterprise claims
* no placeholder text
* no default browser buttons
* no inaccessible dark-on-dark text

---

# 97. VISUAL QA CHECKLIST

The site should feel:

```text
MINIMAL
EDITORIAL
TECHNICAL
INDUSTRIAL
PREMIUM
QUIET
FAST
CONFIDENT
```

It should NOT feel:

```text
GENERIC AI
HACKATHON TEMPLATE
SAAS LANDING PAGE
CYBERPUNK
GAMING
NEON
GLASSMORPHISM
AI SLOP
```

---

# 98. FINAL DESIGN RULE

When choosing between:

A. more features on screen

B. more visual clarity

Always choose:

```text
B
```

When choosing between:

A. more animation

B. stronger hierarchy

Choose:

```text
B
```

When choosing between:

A. a flashy unsupported claim

B. a smaller technically defensible claim

Choose:

```text
B
```

The credibility of SyncNode matters more than visual noise.

---

# 99. FINAL WEBSITE TAGLINE SYSTEM

Primary:

# THINK LOCALLY.

# ACT INTELLIGENTLY.

Secondary:

> Sovereign AI for confidential work.

Supporting:

> Understand locally. Execute safely. Verify everything.

Optional technical:

> Local intelligence. Controlled action. Proven outcomes.

---

# 100. FINAL DEVELOPMENT PRINCIPLE

Do not treat this website as a collection of sections.

Treat it as one continuous product narrative:

```text
WHY
↓
WHAT
↓
HOW
↓
SHOW
↓
TRUST
↓
USE
↓
DOWNLOAD
```

Every page should reinforce the same idea:

# SyncNode gives local AI a controlled way to actually do useful work.

---

# 101. NON-NEGOTIABLE IMPLEMENTATION RULES

1. Build inside `website/`.
2. Use React + Vite + TypeScript.
3. Make the site multi-page through React Router.
4. Do not modify the Electron application for website work.
5. Do not modify the backend.
6. Do not invent unsupported product metrics.
7. Do not invent confidential MRPL information.
8. Use actual videos from the website video directory.
9. Use real GitHub release links once published.
10. Keep the visual language monochrome.
11. Use Lucide for icons.
12. Use GSAP / Framer Motion intentionally.
13. Use Lottie sparingly.
14. Keep animations performant.
15. Respect reduced motion.
16. Make the design responsive.
17. Make every page feel like the same product.
18. Do not use stock AI illustrations.
19. Do not copy other products.
20. Make the website feel like the public-facing sibling of the SyncNode Electron workbench.

---

# 102. END STATE

The completed website should feel like:

```text
EDITORIAL WEBSITE
        +
PRODUCT FILM
        +
DEVELOPER TOOL
        +
INDUSTRIAL SYSTEM
        +
SECURITY PRODUCT
```

It should communicate the same personality as the Electron workbench:

```text
quiet
precise
dark
technical
confident
observable
controlled
```

---

# 103. FINAL IMPLEMENTATION COMMAND

After creating the website:

```bash
cd C:\syncnode\website

npm install

npm run dev
```

Production:

```bash
npm run build
```

Preview:

```bash
npm run preview
```

Deploy the `website/` Vite application to Vercel.

---

# 104. FINAL SUCCESS CONDITION

The visitor reaches the end of the site and can answer all of these without opening another document:

```text
What is SyncNode?
Why does it exist?
Why must it be local?
How does it work?
What are the agents?
What can it actually automate?
How is the system controlled?
How is success verified?
How does human approval work?
What does the product look like?
What does the architecture look like?
What industrial workflows does it support?
Where is the source?
Where can I download it?
```

If any of those questions remain unclear, the website is not finished.

```

And one practical change I would make immediately: **do not literally call it a “single-page website” anywhere in the implementation**. Your screenshots/videos should be treated as **visual chapters distributed across real routes**, with a common motion system and common shell. That gives you the premium editorial feel you're after while keeping the site maintainable.

I also verified the GitHub repository exists and the `website/` directory currently contains the existing Markdown content files, so the implementation agent should inspect those before replacing or reorganizing anything. :contentReference[oaicite:1]{index=1}
```
