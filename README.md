# SyncNode

**Think locally. Act intelligently.**

SyncNode is a fully offline, sovereign AI automation workbench that runs entirely on your local machine. No cloud. No subscriptions. No data leaving your device.

---

## What it does

SyncNode gives you an AI agent (powered by Google Gemma 4) that can:

- **Create documents** — Word (.docx), Excel (.xlsx), PowerPoint (.pptx) with real content
- **Control your desktop** — search the taskbar, open apps, type into them via UIA
- **Browse the web** — navigate, fill forms, attach files in Chromium
- **Compose emails** — fill recipient, subject, body, attach files — then stop for your approval
- **Access your entire PC** — read/write any file, run shell commands, list processes
- **Chat intelligently** — ask questions, get answers, trigger actions from natural language
- **Learn over time** — workflow memory records successful patterns for future runs

Everything runs on your GPU. No API keys. No internet required after setup.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Electron Frontend                      │
│  React + Tailwind + Framer Motion + Vite                │
│  • Home / Runs / Chat / Files / Knowledge / Settings    │
│  • Live SSE stream from backend                         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP/SSE  localhost:8000
┌───────────────────▼─────────────────────────────────────┐
│                 FastAPI Backend                         │
│  • Orchestrator: intent → plan → agents → tools        │
│  • Tool registry: 44 tools (document, system, browser) │
│  • Verification engine: post-condition assertions       │
│  • Audit chain: SHA-256 per event                       │
│  • SQLite database (aiosqlite)                          │
│  • ChromaDB RAG index (offline embeddings)              │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP  localhost:11434
┌───────────────────▼─────────────────────────────────────┐
│                  Ollama (local)                         │
│  • gemma4:e4b  — primary model (GPU, Q4_K_M)           │
│  • gemma3:1b   — enricher + summarizer (CPU)            │
└─────────────────────────────────────────────────────────┘
```

---

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 x64 | Windows 11 x64 |
| RAM | 8 GB | 16 GB |
| GPU | Any (CPU fallback) | NVIDIA RTX (4 GB+ VRAM) |
| Storage | 10 GB | 20 GB |
| Python | 3.12 | 3.12 |
| Node.js | 20 | 20 |

---

## Quick Start

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) and install.

Pull the required models:
```powershell
ollama pull gemma4:e4b    # Primary model (~3.8 GB)
ollama pull gemma3:1b     # Enricher/summarizer (~800 MB, optional)
```

### 2. Clone & install

```powershell
git clone https://github.com/Boredooms/SyncNode.git
cd SyncNode

# Backend
pip install -e backend -e ai_ml

# Frontend
cd frontend/electron
npm install
cd ../..
```

### 3. Configure

```powershell
Copy-Item .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 4. Start everything

```powershell
# Option A: All-in-one script
.\scripts\start_all.ps1 --dev

# Option B: Manual (3 terminals)
.\scripts\start_ollama.ps1          # Terminal 1
python scripts\start_server.py      # Terminal 2
cd frontend/electron && npm run dev # Terminal 3
```

Open Electron — it will auto-connect to the backend.

---

## Building the distributable

### Windows installer (NSIS + portable .exe)

```powershell
# Build backend executable
.\scripts\build_backend.ps1

# Build Electron installer
cd frontend/electron
npm run dist
```

Output: `frontend/electron/dist/SyncNode-Setup-1.0.0.exe`

### CI/CD

Every push to `main` and every `v*.*.*` tag triggers the GitHub Actions workflow (`.github/workflows/build.yml`) which:
1. Runs backend linting and frontend TypeScript checks
2. Builds the Python backend into a standalone `.exe` via PyInstaller
3. Bundles it into the Electron NSIS installer
4. On version tags: publishes a GitHub Release with the installer attached

---

## Project structure

```
SyncNode/
├── backend/          # FastAPI backend (Python)
│   └── src/syncnode_backend/
│       ├── api/v1/   # REST + SSE endpoints
│       ├── workflow/ # Orchestrator + LangGraph
│       ├── tools/    # Tool registry
│       ├── system/   # Full PC access tools
│       ├── computer/ # UIA desktop control
│       ├── browser/  # Playwright browser
│       ├── office/   # Excel/PowerPoint
│       ├── documents/# Word/filesystem
│       └── verification/ # Post-condition engine
│
├── ai_ml/            # AI substrate (Python)
│   └── src/syncnode_ai/
│       ├── gateway/  # Ollama adapter
│       ├── intent/   # Intent extraction
│       ├── planner/  # Execution plan DAG
│       ├── agents/   # Agent registry
│       └── routing/  # Inference profiles
│
├── frontend/electron/ # Electron + React
│   └── src/
│       ├── main/     # Electron main process
│       ├── preload/  # IPC bridge
│       └── renderer/ # React UI
│           ├── screens/  # Pages
│           └── components/
│
├── data/             # SQLite DB + ChromaDB (gitignored)
├── workspace/        # Run artifacts (gitignored)
├── knowledge/        # Markdown knowledge base
├── scripts/          # Startup + build scripts
└── tests/            # Integration + golden tests
```

---

## GPU troubleshooting (NVIDIA)

If you see `llama-server GPU discovery watchdog timed out`:

```powershell
# These are already set by start_server.py / start_ollama.ps1:
$env:CUDA_VISIBLE_DEVICES = "0"       # Force GPU 0
$env:OLLAMA_IGPU_ENABLE   = "0"       # Disable iGPU Vulkan probe
$env:OLLAMA_LOAD_TIMEOUT  = "300s"    # More time for CUDA init
```

The `start_ollama.ps1` script sets these automatically.

---

## License

Proprietary. All rights reserved. © 2026 Boredooms.

---

*Think locally. Act intelligently.*
