# SyncNode — Start Ollama with GPU stability settings
# Fixes "llama-server GPU discovery watchdog timed out" on Windows RTX systems.
#
# Usage: .\scripts\start_ollama.ps1
# Or with a specific model: .\scripts\start_ollama.ps1 -Model gemma4:e4b

param(
    [string]$Model = "gemma4:e4b",
    [switch]$PullModel
)

Write-Host "▶  Starting Ollama (CUDA-stable mode)..." -ForegroundColor Cyan

# ── CUDA / GPU stability environment variables ─────────────────────────────
# Force device 0 — prevents multi-GPU probe loop on systems with iGPU + dGPU
$env:CUDA_VISIBLE_DEVICES     = "0"
# Disable Intel iGPU Vulkan probing — we only want CUDA (RTX 2050)
$env:OLLAMA_IGPU_ENABLE       = "0"
# Give llama-server more time to init CUDA on cold start (default is 15s — too short)
$env:OLLAMA_LOAD_TIMEOUT      = "300s"
# Prevent parallel CUDA init deadlock
$env:OLLAMA_MAX_LOADED_MODELS = "1"
# Keep model warm between requests
$env:OLLAMA_KEEP_ALIVE        = "30m"
# Use CUDA v13 library path explicitly
$env:OLLAMA_LLM_LIBRARY       = ""   # let Ollama auto-detect from CUDA path

Write-Host "   CUDA_VISIBLE_DEVICES     = $env:CUDA_VISIBLE_DEVICES" -ForegroundColor Gray
Write-Host "   OLLAMA_IGPU_ENABLE       = $env:OLLAMA_IGPU_ENABLE"   -ForegroundColor Gray
Write-Host "   OLLAMA_LOAD_TIMEOUT      = $env:OLLAMA_LOAD_TIMEOUT"  -ForegroundColor Gray
Write-Host "   OLLAMA_MAX_LOADED_MODELS = $env:OLLAMA_MAX_LOADED_MODELS" -ForegroundColor Gray

# ── Pull model if requested ─────────────────────────────────────────────────
if ($PullModel) {
    Write-Host "▶  Pulling model $Model..." -ForegroundColor Cyan
    ollama pull $Model
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗  Failed to pull model $Model" -ForegroundColor Red
        exit 1
    }
}

# ── Start Ollama serve ──────────────────────────────────────────────────────
Write-Host "▶  ollama serve" -ForegroundColor Cyan
ollama serve
