# SyncNode Local Inference Benchmark

All numbers below are **measured** on the actual machine via
`scripts/benchmark_inference.py` (which runs through the real SyncNode
`ModelGateway` → `OllamaAdapter` path with the production inference profiles) and
direct `/api/chat` probes. Raw JSON is persisted under `data/benchmarks/`.

## Hardware / runtime (verified)

| Item | Value |
|------|-------|
| GPU | NVIDIA GeForce RTX 2050, 4096 MiB (4 GB) VRAM, compute 8.6 |
| GPU driver / CUDA UMD | 616.56 / 13.4 (Ollama uses bundled `cuda_v13` runner) |
| CPU RAM | ~12 GB total (observed heavy pressure: ~1 GB free at times) |
| iGPU | Intel UHD 770 (dropped by Ollama as integrated) |
| PyTorch | 2.10.0+cpu (`torch.cuda.is_available()==False`; irrelevant to Ollama) |
| Ollama | 0.34.2, endpoint `http://127.0.0.1:11434` |
| Model | `gemma4:e4b` — gemma4, 8.0B params, Q4_K_M, ctx 131072, embed 2560 |
| Capabilities | completion, vision, audio, tools, thinking |

## Baseline (before optimization)

Measured with a tiny prompt via direct `/api/chat`, and with a realistic
~430-token generation. The pre-existing adapter sent **no** `num_ctx`, `num_gpu`
or `keep_alive`, so Ollama used the model default context (131072) and its
conservative auto-offload.

| Condition | tok/s (gen) | Load | GPU % | VRAM |
|-----------|-------------|------|-------|------|
| Default (ctx 131072, no num_gpu) — before GPU was even detected | ~7.6 | 22.3 s | 0 % (CPU only) | 0.00 GB |
| Auto-offload, ctx 4096 (num_gpu unset) | ~8.1 | 19 s cold | 15 % | 1.46 GB |

Root cause of the CPU-only state: a stale Ollama server (started during the
model download under memory pressure) failed CUDA bootstrap. A clean restart
made Ollama detect the RTX 2050 (`inference compute … library=CUDA compute=8.6
… total="4.0 GiB"`).

## Optimized (num_gpu=99, bounded num_ctx, keep_alive)

Realistic ~430–445 token generations:

| Condition | tok/s (gen) | Load (cold) | Load (warm) | GPU % | VRAM |
|-----------|-------------|-------------|-------------|-------|------|
| **num_gpu=99, ctx 4096** | **~31** | 11.2 s | **0.01 s** | 100 % | 3.23 GB |

A 427-token generation dropped from **53 s → 14 s**. Same-prompt A/B through the
SyncNode gateway: auto-offload **11.5 tok/s** vs full-offload **29.3 tok/s**.

### Context ceiling (num_gpu=99)

The gemma4 sliding-window / shared-KV cache (`shared_kv_layers=18`; KV = a small
4-layer full-attention cache + a 20-layer local cache) is compact, so full GPU
residency holds across a wide context range:

| num_ctx | tok/s | VRAM | GPU % |
|---------|-------|------|-------|
| 2048 | 30.7 | 3.22 GB | 100 % |
| 4096 | 30.8 | 3.23 GB | 100 % |
| 8192 | 30.6 | 3.23 GB | 100 % |
| 16384 | 30.7 | 3.24 GB | 100 % |
| 32768 | 30.6 | 3.26 GB | 100 % |

Context is **not** the offload constraint on this model/GPU. Profiles stay at
4096–8192 for RAM/VRAM headroom.

## Per-workload (through the SyncNode gateway + profiles)

Latest run (`data/benchmarks/inference_20260919_023245.json`), model warm:

| Workload | Profile | Prompt tok | Out tok | ~tok/s | Total (s) | Structured valid |
|----------|---------|-----------:|--------:|-------:|----------:|------------------|
| A tiny | fast_simple | 23 | 3 | n/a* | 14.5 | — |
| B normal reasoning | normal_reasoning | 61 | 1024 | 21.5 | 47.7 | — |
| C structured intent | fast_structured | 1366 | 935 | 20.5 | 45.7 | **True** |
| D structured plan | planner | 1233 | 1444 | 23.0 | 62.7 | **True** |
| E vision (64px img) | vision | 110 | 259 | 28.0 | 9.3 | — |
| F multi-turn | normal_reasoning | 83 | 314 | 29.9 | 10.5 | — |

\* A_tiny generates only ~3 tokens; tok/s over total latency is not meaningful
at that size.

### Vision note

For a 64×64 image, prompt-eval was ~13 s for ~108 image tokens — **image
tokenization dominates vision latency**, not generation (which runs at ~30
tok/s). Screenshots should be cropped/downscaled before being sent (see
`docs/INFERENCE_OPTIMIZATION.md`, §Vision).

### Structured-output payload note

C/D show large prompt-token counts (1366 / 1233) because `generate_structured`
embeds the JSON schema in the prompt. Both still validate. Reducing schema
payload is a further, non-urgent optimization (tracked in the optimization doc).

## Reproduce

```powershell
python scripts/benchmark_inference.py --profile-compare
```

Requires Ollama running with `gemma4:e4b` present. Fails loudly if the model is
unavailable (no fabricated numbers).
