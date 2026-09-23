# SyncNode Runtime Context (verified)

Snapshot of the actual machine/runtime state and the selected inference
configuration. All values verified on-device (see `docs/INFERENCE_BENCHMARK.md`).
No secrets are stored here.

## Hardware

| Item | Value |
|------|-------|
| OS | Windows (win32), PowerShell |
| GPU | NVIDIA GeForce RTX 2050, 4096 MiB (4 GB) VRAM, compute capability 8.6 |
| GPU driver / CUDA UMD | 616.56 / 13.4 |
| Integrated GPU | Intel UHD 770 (dropped by Ollama as integrated) |
| System RAM | ~12 GB (observed under pressure; keep other apps light for headroom) |
| Python | 3.14.2 |
| PyTorch | 2.10.0+cpu (CPU-only build; not used by Ollama) |

## Model runtime

| Item | Value |
|------|-------|
| Provider | Ollama 0.34.2 (local, loopback only) |
| Endpoint | `http://127.0.0.1:11434` |
| GPU runner | bundled `cuda_v13` (CUDA0), full offload |
| Model (`SYNCNODE_MODEL_ID`) | `gemma4:e4b` |
| Architecture / params | gemma4 / 8.0B |
| Quantization | Q4_K_M |
| Max context | 131072 (we bound it — see below) |
| Capabilities | completion, vision, audio, tools, thinking |

## Selected inference configuration

| Knob | Value | Env |
|------|-------|-----|
| GPU layers (num_gpu) | 99 (all) | `SYNCNODE_GPU_LAYERS` |
| Default context (num_ctx) | 8192 | `SYNCNODE_NUM_CTX` |
| keep_alive | 30m | `SYNCNODE_KEEP_ALIVE` |
| Model timeout | 300 s | `SYNCNODE_MODEL_TIMEOUT` |
| Structured repair attempts | 2 | `SYNCNODE_MODEL_REPAIR_ATTEMPTS` |
| Concurrency | 1 generation at a time | Ollama `OLLAMA_NUM_PARALLEL=1` |

### Inference profiles (`ai_ml/.../routing/profiles.py`)

| Profile | num_ctx | num_gpu | max_out | temp | used by |
|---------|--------:|--------:|--------:|-----:|---------|
| fast_simple | 4096 | 99 | 512 | 0.4 | writer |
| fast_structured | 4096 | 99 | 768 | 0.0 | intent, tool selection |
| normal_reasoning | 8192 | 99 | 1024 | 0.2 | general reasoning |
| planner | 8192 | 99 | 4096 | 0.0 | ExecutionPlan / DAG |
| vision | 8192 | 99 | 512 | 0.0 | screenshot interpretation |

## Measured performance (warm)

| Metric | Value |
|--------|-------|
| Generation | ~31 tok/s (full GPU offload) vs ~8 tok/s CPU auto-offload |
| Warm model load | 0.01 s (cold ~11 s) |
| Resident VRAM | ~3.23 GB of 4.0 GB (100 % GPU) |
| Gate B capability suite | 10/10 pass, ~31 s |

## Dependencies for the golden demo

| Dependency | State |
|------------|-------|
| Microsoft Word | Installed at `C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE` (resolved via App Paths; not on PATH) |
| Playwright Chromium | Installed (`python -m playwright install chromium`) |
| Mail compose target | Local offline fixture `tests/fixtures/web/compose.html` (`SYNCNODE_MAIL_COMPOSE_URL`) — no external auth |
| Workspace root | `C:\syncnode\workspace\demo` (`SYNCNODE_WORKSPACE_ROOT`) |
| Database | SQLite (`data/syncnode.db`) |
| RAG | ChromaDB (`data/rag_index`) |

## Operational notes

- If Ollama falls back to CPU (`ollama ps` shows 100 % CPU / `total_vram=0`),
  restart the Ollama service so CUDA discovery re-runs.
- Between repeated golden runs, close Word and stray Playwright Chrome and delete
  the demo `.docx` (Word holds a file lock on the open document).
