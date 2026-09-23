# SyncNode — Start all services (Ollama + Backend + Frontend)
#
# Opens 3 terminal windows:
#   1. Ollama (GPU-stable, CUDA env set)
#   2. Python backend (FastAPI on :8000)
#   3. Electron dev server (Vite on :5173)
#
# Usage: .\scripts\start_all.ps1 [--dev] [--no-frontend]

param(
    [switch]$Dev,
    [switch]$NoFrontend,
    [switch]$NoOllama,
    [int]$Port = 8000
)

$ROOT = Split-Path $PSScriptRoot -Parent
$SCRIPTS = $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   SyncNode — Starting All Services    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Ollama ───────────────────────────────────────────────────────────────
if (-not $NoOllama) {
    $ollamaRunning = $null
    try { $ollamaRunning = Invoke-RestMethod "http://127.0.0.1:11434/api/version" -TimeoutSec 2 -ErrorAction Stop } catch {}

    if ($ollamaRunning) {
        Write-Host "✓  Ollama already running (v$($ollamaRunning.version))" -ForegroundColor Green
    } else {
        Write-Host "▶  Starting Ollama..." -ForegroundColor Cyan
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "& '$SCRIPTS\start_ollama.ps1'"
        ) -WindowStyle Normal

        # Wait for Ollama to be ready (up to 30s)
        $attempts = 0
        do {
            Start-Sleep 2; $attempts++
            try { $ollamaRunning = Invoke-RestMethod "http://127.0.0.1:11434/api/version" -TimeoutSec 1 -ErrorAction Stop } catch {}
        } while (-not $ollamaRunning -and $attempts -lt 15)

        if ($ollamaRunning) {
            Write-Host "✓  Ollama ready" -ForegroundColor Green
        } else {
            Write-Host "⚠  Ollama not responding — check the Ollama window" -ForegroundColor Yellow
        }
    }
}

# ── 2. Backend ──────────────────────────────────────────────────────────────
$backendRunning = $null
try { $backendRunning = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2 -ErrorAction Stop } catch {}

if ($backendRunning -and $backendRunning.status -eq "ok") {
    Write-Host "✓  Backend already running on :$Port" -ForegroundColor Green
} else {
    Write-Host "▶  Starting backend on :$Port..." -ForegroundColor Cyan
    $reloadFlag = if ($Dev) { "--reload" } else { "" }
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$ROOT'; python scripts\start_server.py --port $Port $reloadFlag"
    ) -WindowStyle Normal

    # Wait for backend
    $attempts = 0
    do {
        Start-Sleep 2; $attempts++
        try { $backendRunning = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 1 -ErrorAction Stop } catch {}
    } while ((-not $backendRunning -or $backendRunning.status -ne "ok") -and $attempts -lt 20)

    if ($backendRunning -and $backendRunning.status -eq "ok") {
        Write-Host "✓  Backend ready → http://127.0.0.1:$Port" -ForegroundColor Green
    } else {
        Write-Host "⚠  Backend not responding — check backend window" -ForegroundColor Yellow
    }
}

# ── 3. Frontend ─────────────────────────────────────────────────────────────
if (-not $NoFrontend) {
    if ($Dev) {
        Write-Host "▶  Starting Electron dev server..." -ForegroundColor Cyan
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "Set-Location '$ROOT\frontend\electron'; npm run dev"
        ) -WindowStyle Normal
        Write-Host "✓  Frontend dev server starting (Vite on :5173)" -ForegroundColor Green
    } else {
        Write-Host "ℹ  Production mode: launch SyncNode.exe from dist/" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SyncNode is running!" -ForegroundColor Green
Write-Host "  Backend  → http://127.0.0.1:$Port" -ForegroundColor White
Write-Host "  Docs     → http://127.0.0.1:$Port/docs" -ForegroundColor White
if (-not $NoFrontend -and $Dev) {
Write-Host "  Frontend → http://localhost:5173" -ForegroundColor White
}
Write-Host "══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
