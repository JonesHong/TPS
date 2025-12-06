$root = Resolve-Path "$PSScriptRoot/.."
$frontend = Join-Path $root "frontend"

Write-Host "Starting TPS Development Environment..." -ForegroundColor Cyan

# Start Backend
Write-Host "Launching Backend (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; Write-Host 'Starting Backend...'; uv run uvicorn tps.app:app --reload"

# Start Frontend
Write-Host "Launching Frontend (SvelteKit)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontend'; Write-Host 'Starting Frontend...'; pnpm dev"

Write-Host "Done! Check the new windows." -ForegroundColor Cyan
