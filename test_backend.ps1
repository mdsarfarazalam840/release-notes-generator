Start-Sleep -Seconds 10
try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/api/config" -TimeoutSec 5
    Write-Host "Backend is running!"
    Write-Host "Repo: $($r.repo)"
    Write-Host "GitHub Token: $($r.has_github_token)"
    Write-Host "LLM Model: $($r.llm_model)"
} catch {
    Write-Host "Backend check failed: $_"
}

