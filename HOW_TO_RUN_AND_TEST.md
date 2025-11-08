# How to Run and Test the Release Notes Generator

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm installed
3. **Environment variables** configured in `.env.local`:
   - `GITHUB_TOKEN` - Your GitHub personal access token
   - `OPENROUTER_API_KEY` or `OPENAI_API_KEY` - LLM API key
   - `CONFLUENCE_BASE`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` (optional, for Confluence publishing)

## Quick Start

### Option 1: Run Both Servers Manually (Recommended)

#### Terminal 1 - Backend Server:
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator"
python src/server.py
```

You should see:
```
Starting Flask server...
 * Running on http://0.0.0.0:5000
```

#### Terminal 2 - Frontend Server:
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator\frontend"
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Option 2: Run in Background (PowerShell)

```powershell
# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\kekeb\Downloads\Compressed\release-notes-generator'; python src/server.py"

# Start frontend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\kekeb\Downloads\Compressed\release-notes-generator\frontend'; npm run dev"
```

## Access the Application

1. **Frontend UI**: Open your browser and go to `http://localhost:5173`
2. **Backend API**: Available at `http://localhost:5000`

## Testing the Application

### 1. Manual Testing via Web UI

1. Open `http://localhost:5173` in your browser
2. Enter your repository (e.g., `owner/repo`)
3. Enter a version (e.g., `v1.0.0`)
4. Select an audience (users, developers, or managers)
5. Click "Generate Release Notes"
6. Wait for generation to complete
7. View the generated release notes below
8. Click on any tag in the releases list to view that release

### 2. API Testing via PowerShell

#### Test Backend Health:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/config" -Method GET
```

#### Test List Releases:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/releases" -Method GET
```

#### Test Generate Release Notes (Standard):
```powershell
$payload = @{
    version = "v1.0.0"
    repo = "mdsarfarazalam840/release-notes-generator"
    audience = "users"
    use_github = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/generate" -Method POST -Body $payload -ContentType "application/json"
```

#### Test Generate Release Notes (Enhanced):
```powershell
$payload = @{
    version = "v1.0.0"
    repo = "mdsarfarazalam840/release-notes-generator"
    audience = "users"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/generate/enhanced" -Method POST -Body $payload -ContentType "application/json"
```

### 3. Comprehensive Test Script

Run the complete test suite:

```powershell
Write-Host "=== Testing All Endpoints ===" -ForegroundColor Cyan

# Test 1: Config
Write-Host "`n[1] Testing /api/config..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/api/config" -Method GET -TimeoutSec 5
    Write-Host "   [OK] Backend is running - Repo: $($r.repo)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] $_" -ForegroundColor Red
}

# Test 2: List Releases
Write-Host "`n[2] Testing /api/releases..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/api/releases" -Method GET -TimeoutSec 5
    Write-Host "   [OK] Found $($r.releases.Count) releases" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] $_" -ForegroundColor Red
}

# Test 3: Generate Enhanced
Write-Host "`n[3] Testing /api/generate/enhanced..." -ForegroundColor Yellow
$payload = @{
    version = "v1.0.0-test"
    repo = "mdsarfarazalam840/release-notes-generator"
    audience = "users"
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/api/generate/enhanced" -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 60
    Write-Host "   [OK] Generation successful!" -ForegroundColor Green
    Write-Host "   Status: $($r.status)" -ForegroundColor White
    Write-Host "   Version: $($r.version)" -ForegroundColor White
} catch {
    Write-Host "   [FAIL] Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# Test 4: Generate Standard
Write-Host "`n[4] Testing /api/generate..." -ForegroundColor Yellow
$payload2 = @{
    version = "v1.0.1-test"
    repo = "mdsarfarazalam840/release-notes-generator"
    audience = "users"
    use_github = $true
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/api/generate" -Method POST -Body $payload2 -ContentType "application/json" -TimeoutSec 60
    Write-Host "   [OK] Generation successful! Status: $($r.status)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] $_" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
```

## Troubleshooting

### Backend Not Starting

1. Check if port 5000 is already in use:
   ```powershell
   Get-NetTCPConnection -LocalPort 5000
   ```

2. Kill any process using port 5000:
   ```powershell
   Get-NetTCPConnection -LocalPort 5000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
   ```

3. Check Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Frontend Not Starting

1. Check if port 5173 is already in use:
   ```powershell
   Get-NetTCPConnection -LocalPort 5173
   ```

2. Install frontend dependencies:
   ```powershell
   cd frontend
   npm install
   ```

### API Returns 500 Error

1. Check backend logs for error messages
2. Verify `.env.local` file has all required environment variables
3. Ensure GitHub token is valid and has proper permissions
4. Check that LLM API key is set correctly

### Frontend Shows "Failed to Fetch"

1. Verify backend is running on `http://localhost:5000`
2. Check browser console for CORS errors
3. Verify backend CORS headers are set correctly

## Stopping the Servers

### Manual Stop:
- Press `Ctrl+C` in each terminal window

### Stop All Processes:
```powershell
# Stop Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Stop Node processes
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force

# Or stop by port
Get-NetTCPConnection -LocalPort 5000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 5173 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Expected Behavior

### Successful Generation:
- Backend returns JSON with `status: "ok"` or `status: "success"`
- Release notes file is created in `examples/` folder
- Frontend displays the generated content
- If Confluence publishing is enabled, a link is displayed

### Error Handling:
- All errors return JSON (never HTML)
- Error messages are descriptive
- Frontend displays errors clearly

## Next Steps

1. **Generate Release Notes**: Use the UI or API to generate release notes
2. **View Releases**: Browse generated releases in the UI
3. **Publish to Confluence**: Enable Confluence publishing in the UI
4. **Customize**: Modify templates, audiences, or add custom sections

## Support

If you encounter issues:
1. Check the backend terminal for error messages
2. Check the browser console (F12) for frontend errors
3. Verify all environment variables are set correctly
4. Ensure all dependencies are installed


