# Launch both Backend and Frontend for Report Intelligence Assistant
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Report Intelligence Assistant (Dev Server)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend
$backend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Write-Host 'Starting Backend API on http://localhost:8000...' -ForegroundColor Green; .\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --port 8000" -PassThru

# 2. Start Vite Frontend
$frontend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Write-Host 'Starting Frontend UI on http://localhost:5173...' -ForegroundColor Cyan; cd frontend; npm run dev" -PassThru

Write-Host "`nBackend process ID: $($backend.Id) -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend process ID: $($frontend.Id) -> http://localhost:5173" -ForegroundColor Cyan
Write-Host "`nApp is launching! Press Ctrl+C in their respective windows to stop." -ForegroundColor Yellow

