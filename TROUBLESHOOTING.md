# Troubleshooting Guide

## Error: "Failed to fetch" when clicking "Fetch Releases"

### Solution 1: Backend Server Not Running ⚠️ MOST COMMON

**Problem**: The backend server isn't running on port 5000.

**Fix**: 
1. Open a terminal/command prompt
2. Navigate to the project directory
3. Run: `python src/server.py`
4. You should see: `Running on http://0.0.0.0:5000`
5. Keep this terminal open
6. Refresh your browser (F5)

**Or use the batch file**:
- Double-click `run_backend.bat`

---

### Solution 2: GITHUB_TOKEN Not Set

**Problem**: Backend is running but GitHub token is missing.

**Error Message**: "GITHUB_TOKEN not set"

**Fix**:
1. Create a `.env` file in the project root
2. Add: `GITHUB_TOKEN=your_token_here`
3. Restart the backend server

**How to get a GitHub token**:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` permissions
3. Copy the token to your `.env` file

---

### Solution 3: Invalid Repository Name

**Problem**: Repository name format is incorrect.

**Error Message**: "Repository not specified" or "Not Found"

**Fix**:
- Use format: `owner/repo` (e.g., `mdsarfarazalam840/release-notes-generator`)
- Don't include `https://github.com/`
- Make sure the repository exists and is accessible

---

### Solution 4: CORS Error

**Problem**: Browser blocking requests due to CORS.

**Error Message**: "CORS policy" or "Access-Control-Allow-Origin"

**Fix**:
- Backend already has CORS enabled
- Make sure backend is running on `http://localhost:5000`
- Frontend should be on `http://localhost:5173` (or similar Vite port)

---

### Solution 5: Port Already in Use

**Problem**: Another application is using port 5000.

**Error Message**: "Address already in use" or "Port 5000 is already in use"

**Fix**:
1. Find what's using port 5000:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Kill the process or change the port in `src/server.py`:
   ```python
   app.run(host='0.0.0.0', port=5001)  # Change to different port
   ```
3. Update frontend `VITE_API_BASE` if needed

---

## Quick Diagnosis Steps

1. **Check if backend is running**:
   - Open browser to: http://localhost:5000/api/config
   - Should see JSON response with repo info

2. **Check browser console** (F12):
   - Look for network errors
   - Check if requests are reaching the backend

3. **Check backend logs**:
   - Look at the terminal where backend is running
   - Check for error messages

4. **Verify environment**:
   ```powershell
   python -c "import os; print('GITHUB_TOKEN:', 'SET' if os.getenv('GITHUB_TOKEN') else 'NOT SET')"
   ```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Failed to fetch" | Backend not running | Start backend server |
| "GITHUB_TOKEN not set" | Missing token | Set GITHUB_TOKEN in .env |
| "Repository not specified" | Invalid repo format | Use `owner/repo` format |
| "Not Found" | Repository doesn't exist | Check repository name |
| "NetworkError" | Connection refused | Check backend is running |
| "CORS policy" | CORS issue | Ensure backend CORS is enabled |

---

## Still Having Issues?

1. **Check backend logs** in the terminal window
2. **Check browser console** (F12 → Console tab)
3. **Verify both servers are running**:
   - Backend: http://localhost:5000/api/config
   - Frontend: http://localhost:5173
4. **Restart both servers** if needed

