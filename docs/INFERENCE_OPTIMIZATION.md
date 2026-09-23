# SyncNode Inference Optimization — Decision Record

This records the measured optimization of local `gemma4:e4b` inference on the
NVIDIA RTX 2050 (4 GB). Every claim here is backed by a measurement in
`docs/INFERENCE_BENCHMARK.md` / `data/benchmarks/`.

## Baseline

- Model was running **100 % on CPU** at the model's default **131072** context.
- Tiny-prompt round trip ~25 s (load 22 s); realistic 430-token generation at
  ~8 tok/s (53 s).
- `.env` had `SYNCNODE_MODEL_TIMEOUT=3600` — a 1-hour timeout, itself a symptom
  of how slow inference had become.

## Measured bottleneck

Diagnosed from `%LOCALAPPDATA%\Ollama\server.log` and controlled probes, in
priority order:

1. **NVIDIA GPU not bound.** `llama-server` logged
   `warning: no usable GPU found, --gpu-layers option will be ignored`. Startup
   GPU discovery found only the Intel iGPU (Vulkan, dropped as integrated) and
   fell back to `library=cpu` with `total_vram="0 B"`. The discrete RTX 2050 was
   never enumerated by the CUDA runner on that server instance.
2. **System RAM pressure.** `available="1.7 GiB"` of ~12 GB at load; repeated
   `common_fit_params: failed to fit params to free device memory … abort`.
   This inflated `load_duration` (11–22 s).
3. **Oversized default context.** 131072 KV allocation wasted memory and pushed
   Ollama toward CPU-only.

## Root cause and fix for GPU detection

The CUDA runner libraries (`cuda_v12`, `cuda_v13`, `ggml-cuda.dll`,
`cudart64_*.dll`) and `nvcuda.dll` are all present — GPU support ships with
Ollama. The CPU-only state came from a **stale server** that had started during
the model download under memory pressure and failed CUDA bootstrap.

**Fix:** restart Ollama. After a clean restart the log shows
`inference compute … library=CUDA compute=8.6 name=CUDA0
description="NVIDIA GeForce RTX 2050" … total="4.0 GiB"`. Detection persists
across restarts of the desktop app.

> Operational note: on this laptop (Optimus with an active Intel iGPU), if Ollama
> ever falls back to CPU again, restart the Ollama service so CUDA discovery
> re-runs.

## Experiments (one variable at a time)

Realistic ~430-token generation, warm/cold as noted:

| Config | tok/s | Load | GPU % | VRAM |
|--------|------:|-----:|------:|-----:|
| ctx 131072, no num_gpu | ~7.6 | 22.3 s | 0 % | 0 GB |
| ctx 4096, auto-offload | 8.1 | 19 s | 15 % | 1.46 GB |
| **ctx 4096, num_gpu=99** | **30.8** | 11.2 s | 100 % | 3.23 GB |
| ctx 4096, num_gpu=99 (warm) | 31.0 | 0.01 s | 100 % | 3.23 GB |

`num_gpu` alone had **no effect while the GPU was undetected**; once CUDA was
bound, forcing `num_gpu=99` packed all layers into VRAM (Ollama's auto-estimate
was too conservative at ~15 %).

## Final configuration

Applied via settings and sent per-request by `OllamaAdapter` (SyncNode owns the
runtime options; `num_gpu` cannot be set by env var):

| Knob | Value | Rationale |
|------|-------|-----------|
| `num_gpu` (`SYNCNODE_GPU_LAYERS`) | 99 | Full offload; fits in 4 GB at bounded ctx; ~3.8× faster |
| `num_ctx` (`SYNCNODE_NUM_CTX`) | 8192 default (profiles 4096–8192) | GPU-resident with headroom; measured stable to 32768 |
| `keep_alive` (`SYNCNODE_KEEP_ALIVE`) | 30m | Warm reload 0.01 s vs 11–19 s cold |
| `SYNCNODE_MODEL_TIMEOUT` | 300 (was 3600) | Fast inference no longer needs an hour |
| repair attempts | 2 (was 3) | Invariant MG-03: ≤ 2 repairs after initial gen |

### Inference profiles

`ai_ml/src/syncnode_ai/routing/profiles.py` defines typed profiles selected by
task class (`fast_simple`, `fast_structured`, `normal_reasoning`, `planner`,
`vision`), each binding num_ctx / num_gpu / max_output / temperature / top_p /
keep_alive / thinking / timeout. Intent uses `fast_structured`, the planner uses
`planner`, the writer uses `fast_simple`. Model parameters are no longer
scattered across call sites.

## Result

- Realistic generation **~8 → ~31 tok/s** (~3.8×); a 427-token generation
  **53 s → 14 s**.
- Warm model load **11–19 s → 0.01 s**.
- Gate B capability suite **182 s → ~31 s** wall clock, still **10/10 pass**.
- Golden E2E reaches `waiting_approval` with all steps verified.

## Quality impact (no regression)

- Structured intent and plan generation still validate (`structured_valid=True`).
- Failure-injection test still catches false success → run fails.
- No verification, schema validation, policy, audit, or local-only guarantee was
  weakened. `temperature=0.0` retained for machine-to-machine steps.

## Remaining opportunities (not yet done)

- **Structured-output payload:** intent/plan prompts embed the full JSON schema
  (~1.2–1.4k prompt tokens). A compact schema or native provider grammar could
  cut prompt-eval further. Deferred — current path is valid and fast enough.
- **Dynamic tool-schema reduction / per-step tool subsets** (handoff §17–18):
  the planner currently gets the fixed golden tool set; step-scoped tool
  exposure would reduce prompt size and hallucination.
- **Vision preprocessing:** crop/downscale screenshots before send (image
  tokenization dominates vision latency).
- **Concurrency:** left at 1 (Ollama `OLLAMA_NUM_PARALLEL=1`); a 4 GB card
  should not run concurrent generations. Not increased.
