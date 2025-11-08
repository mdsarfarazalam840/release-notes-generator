# End-to-end test script for release notes generator

Write-Host "=== Testing Release Notes Generator ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if backend is running
Write-Host "[1/5] Testing backend server..." -ForegroundColor Yellow
try {
    $config = Invoke-RestMethod -Uri "http://localhost:5000/api/config" -Method Get -TimeoutSec 5
    Write-Host "[OK] Backend is running!" -ForegroundColor Green
    Write-Host "  - Repo: $($config.repo)" -ForegroundColor Gray
    Write-Host "  - GitHub Token: $(if($config.has_github_token){'SET'}else{'NOT SET'})" -ForegroundColor Gray
    Write-Host "  - LLM Model: $($config.llm_model)" -ForegroundColor Gray
} catch {
    Write-Host "[FAIL] Backend is not running or not accessible" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check releases endpoint
Write-Host ""
Write-Host "[2/5] Testing releases endpoint..." -ForegroundColor Yellow
try {
    $releases = Invoke-RestMethod -Uri "http://localhost:5000/api/releases" -Method Get -TimeoutSec 5
    Write-Host "[OK] Releases endpoint working!" -ForegroundColor Green
    Write-Host "  - Found $($releases.releases.Count) releases" -ForegroundColor Gray
    if ($releases.releases.Count -gt 0) {
        Write-Host "  - Latest: $($releases.releases[0].tag_name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "[FAIL] Releases endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

# Test 3: Generate a new release note
Write-Host ""
Write-Host "[3/5] Testing generation endpoint..." -ForegroundColor Yellow
$version = "v1.2.7"
$generateBody = @{
    version = $version
    audience = "users"
    use_github = $true
    repo = $config.repo
} | ConvertTo-Json

try {
    $generateResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/generate" -Method Post -Body $generateBody -ContentType "application/json" -TimeoutSec 120
    if ($generateResponse.status -eq "ok") {
        Write-Host "[OK] Generation successful!" -ForegroundColor Green
        Write-Host "  - Version: $($generateResponse.version)" -ForegroundColor Gray
        Write-Host "  - New releases count: $($generateResponse.releases.Count)" -ForegroundColor Gray
        Write-Host "  - Output file created in examples/" -ForegroundColor Gray
    } else {
        Write-Host "[FAIL] Generation failed: $($generateResponse.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Generation endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

# Test 4: Verify new release file exists
Write-Host ""
Write-Host "[4/5] Verifying generated file..." -ForegroundColor Yellow
$releaseFile = "examples/release_$version.md"
if (Test-Path $releaseFile) {
    Write-Host "[OK] Release file created: $releaseFile" -ForegroundColor Green
    $content = Get-Content $releaseFile -Raw
    Write-Host "  - File size: $($content.Length) characters" -ForegroundColor Gray
    Write-Host "  - Contains content: $(if($content.Length -gt 100){'Yes'}else{'No'})" -ForegroundColor Gray
} else {
    Write-Host "[FAIL] Release file not found: $releaseFile" -ForegroundColor Red
}

# Test 5: Check if releases list updated
Write-Host ""
Write-Host "[5/5] Verifying releases list updated..." -ForegroundColor Yellow
try {
    $releasesAfter = Invoke-RestMethod -Uri "http://localhost:5000/api/releases" -Method Get -TimeoutSec 5
    $foundNew = $releasesAfter.releases | Where-Object { $_.tag_name -eq $version }
    if ($foundNew) {
        Write-Host "[OK] New release found in list!" -ForegroundColor Green
        Write-Host "  - Tag: $($foundNew.tag_name)" -ForegroundColor Gray
        Write-Host "  - Name: $($foundNew.name)" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] New release not yet in list (may need refresh)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Could not verify releases list" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
