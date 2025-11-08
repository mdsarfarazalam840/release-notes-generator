# 🚀 START HERE - Complete Setup Instructions

## How to Run

Start the backend and frontend in two terminals.

**Terminal 1 – Backend:**
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator"
python src/server.py
```
Wait until you see: `* Running on http://0.0.0.0:5000`

**Terminal 2 – Frontend:**
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator\frontend"
npm run dev
```
Wait until you see: `Local: http://localhost:5173/`

---

## ✅ Verification Steps

### 1. Check Backend:
Open browser: http://localhost:5000/api/config

**Expected:** JSON with repository info (GitHub token no longer required)
```json
{
  "repo": "mdsarfarazalam840/release-notes-generator",
  "has_github_token": false,
  "llm_model": "minimax/minimax-m2:free"
}
```

### 2. Check Frontend:
Open browser: http://localhost:5173

**Expected:** Release Notes Generator UI

### 3. Test Local Releases:
1. Repository field should be pre-filled
2. Click "Fetch Releases" button
3. **You should see:**
   - Releases from the `examples/` directory
   - Helpful message if no releases are found

---

## 🔧 If Frontend Not Working

### Check Frontend Status:
```powershell
# Check if frontend port is listening
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
```

### Restart Frontend:
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator\frontend"
npm run dev
```

### Check for Errors:
- Open browser console (F12)
- Look for errors in red
- Check Network tab for failed requests

---

## 🔧 If Backend Not Working

### Check Backend Status:
```powershell
# Check if backend port is listening
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
```

### Test Backend Directly:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/config"
```

### Restart Backend:
```powershell
cd "c:\Users\kekeb\Downloads\Compressed\release-notes-generator"
python src/server.py
```

---

## 📝 What Was Fixed

1. ✅ **Frontend Code**: Fixed syntax errors
2. ✅ **Release Display**: Improved UI with better formatting
3. ✅ **Error Handling**: Better error messages
4. ✅ **Debug Logging**: Added console.log for troubleshooting
5. ✅ **Local releases**: Backend now serves markdown files from `examples/`

---

## 🎯 Expected Behavior

### When Everything Works:
1. Open http://localhost:5173
2. Repository field auto-filled from config
3. Click "Fetch Releases"
4. Releases appear in blue box below
5. Each release shows:
   - Tag name (blue, clickable)
   - Release name/title
   - Published date
   - Preview of notes
   - "View on GitHub" link
6. Select a release from dropdown
7. Generate release notes works

---

## ⚠️ Important Notes

- **Both servers must be running** for the app to work
- **Backend must start before frontend** for best results
- **Keep terminal windows open** while using the app
- **Check browser console (F12)** for detailed error messages

---

## 🆘 Still Having Issues?

1. **Check browser console** (F12 → Console) for errors
2. **Check backend terminal** for error messages
3. **Verify GITHUB_TOKEN** is set in `.env` file
4. **Test API directly**: http://localhost:5000/api/config

---

**Use `run_servers.ps1` script for the easiest startup experience!**

