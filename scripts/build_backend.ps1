# SyncNode — Build standalone Python backend executable
#
# Produces: dist/syncnode-backend/syncnode-backend.exe
# Self-contained: no Python installation required on the target machine.
#
# Usage: .\scripts\build_backend.ps1
# Requires: pip install pyinstaller (in the backend venv)

param(
    [switch]$Clean,
    [string]$OutDir = "dist/syncnode-backend"
)

$ROOT = Split-Path $PSScriptRoot -Parent

Write-Host "▶  Building SyncNode backend executable..." -ForegroundColor Cyan

if ($Clean) {
    Remove-Item -Recurse -Force "$ROOT\build\backend" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$ROOT\$OutDir"        -ErrorAction SilentlyContinue
}

# Install deps + PyInstaller
Write-Host "   Installing dependencies..."
pip install -e "$ROOT\backend[dev]" -e "$ROOT\ai_ml" pyinstaller --quiet

# Run PyInstaller
pyinstaller `
    --onedir `
    --name "syncnode-backend" `
    --distpath "$ROOT\dist" `
    --workpath "$ROOT\build\backend" `
    --specpath "$ROOT\build\backend" `
    --noconfirm `
    --paths "$ROOT\backend\src" `
    --paths "$ROOT\ai_ml\src" `
    --hidden-import "syncnode_backend.main" `
    --hidden-import "syncnode_backend.api.v1.runs" `
    --hidden-import "syncnode_backend.api.v1.health" `
    --hidden-import "syncnode_backend.api.v1.chat" `
    --hidden-import "syncnode_backend.api.v1.knowledge" `
    --hidden-import "syncnode_backend.api.v1.tools" `
    --hidden-import "syncnode_backend.api.v1.learning" `
    --hidden-import "syncnode_backend.api.v1.events" `
    --hidden-import "syncnode_backend.persistence.models" `
    --hidden-import "syncnode_backend.persistence.database" `
    --hidden-import "syncnode_backend.system.tools" `
    --hidden-import "syncnode_backend.office.tools" `
    --hidden-import "syncnode_backend.computer.tools" `
    --hidden-import "syncnode_backend.browser.tools" `
    --hidden-import "syncnode_backend.documents.tools" `
    --hidden-import "syncnode_ai.gateway.gateway" `
    --hidden-import "syncnode_ai.gateway.ollama_adapter" `
    --hidden-import "syncnode_ai.intent.engine" `
    --hidden-import "syncnode_ai.planner.engine" `
    --hidden-import "syncnode_ai.agents.registry" `
    --hidden-import "uvicorn.main" `
    --hidden-import "uvicorn.lifespan.on" `
    --hidden-import "uvicorn.protocols.http.h11_impl" `
    --hidden-import "aiosqlite" `
    --hidden-import "chromadb" `
    --hidden-import "sentence_transformers" `
    --collect-all "chromadb" `
    --collect-all "sentence_transformers" `
    --collect-all "docx" `
    --collect-all "openpyxl" `
    --collect-all "pptx" `
    --add-data "$ROOT\knowledge;knowledge" `
    --add-data "$ROOT\tests\fixtures;tests/fixtures" `
    "$ROOT\scripts\backend_entry.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓  Backend executable built → $ROOT\$OutDir\syncnode-backend.exe" -ForegroundColor Green
} else {
    Write-Host "✗  Build failed" -ForegroundColor Red
    exit 1
}
