$ErrorActionPreference = "Continue"
Write-Host "Starting backend server..." -ForegroundColor Yellow

# Start backend in a new window so we can see errors
$backendJob = Start-Process python -ArgumentList "src/server.py" -PassThru -NoNewWindow

Start-Sleep -Seconds 10

# Check if process is running
if ($backendJob -and -not $backendJob.HasExited) {
    Write-Host "Backend process started (PID: $($backendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "Backend process may have exited" -ForegroundColor Red
}

# Test connection
Start-Sleep -Seconds 3
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/config" -Method Get -TimeoutSec 5
    Write-Host "Backend is responding!" -ForegroundColor Green
    Write-Host "Repo: $($response.repo)" -ForegroundColor Cyan
    Write-Host "GitHub Token: $($response.has_github_token)" -ForegroundColor Cyan
    Write-Host "LLM Model: $($response.llm_model)" -ForegroundColor Cyan
} catch {
    Write-Host "Backend not responding: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to stop the backend server..." -ForegroundColor Yellow
Read-Host

if ($backendJob -and -not $backendJob.HasExited) {
    Stop-Process -Id $backendJob.Id -Force
    Write-Host "Backend stopped" -ForegroundColor Green
}

