# Quick Start Guide - Release Notes Generator

## ✅ Current Status

**Frontend Server**: ✅ Running on http://localhost:5173
**Backend Server**: ⚠️ Needs to be started manually

## 🚀 Starting the Application

### Option 1: Use Batch Files (Easiest)

1. **Start Backend**: Double-click `run_backend.bat`
   - This opens a console window with the backend server
   - Server runs on http://localhost:5000

2. **Start Frontend**: Double-click `run_frontend.bat` (in a new window)
   - This opens a console with the frontend dev server
   - Frontend runs on http://localhost:5173

### Option 2: Manual Start

**Backend:**
```powershell
cd c:\Users\kekeb\Downloads\Compressed\release-notes-generator
python src/server.py
```

**Frontend** (in a new terminal):
```powershell
cd c:\Users\kekeb\Downloads\Compressed\release-notes-generator\frontend
npm run dev
```

## 🌐 Accessing the Application

Once both servers are running:

1. **Open your browser** and go to: **http://localhost:5173**
2. The frontend will automatically connect to the backend at http://localhost:5000

## 📝 Using the Application

1. **Repository Field**: Enter your GitHub repo (e.g., `owner/repo`)
   - Default from config: `mdsarfarazalam840/release-notes-generator`

2. **Fetch Releases**: Click "Fetch Releases" to load releases from GitHub
   - Requires `GITHUB_TOKEN` environment variable

3. **Select Previous Release** (optional): Choose a tag from the dropdown to use as starting point

4. **Generate Release Notes**: 
   - Enter version (e.g., `v1.2.5`)
   - Select audience (users/developers/managers)
   - Click "Generate Release Notes"

5. **View Results**: Generated notes appear in the editor/preview panel

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:
```
GITHUB_TOKEN=your_github_token_here
OPENROUTER_API_KEY=your_key_here  # Optional, for LLM
```

### Config File

Edit `config.yaml`:
```yaml
repo: "your-username/your-repo"
llm:
  model: "minimax/minimax-m2:free"
  temperature: 0.0
```

## 📁 Generated Files

Release notes are saved in:
- `examples/release_<version>.md`

Example files already present:
- `release_v1.2.0.md`
- `release_v1.2.3.md`
- `release_v1.2.4.md`

## 🐛 Troubleshooting

### Backend not starting?
- Check if port 5000 is already in use
- Verify Python dependencies: `pip install -r requirements.txt`
- Check for error messages in the console

### Frontend not connecting?
- Ensure backend is running on port 5000
- Check browser console for CORS errors
- Verify `VITE_API_BASE` in frontend (defaults to `http://localhost:5000`)

### Can't fetch releases?
- Verify `GITHUB_TOKEN` is set
- Check repository name format: `owner/repo`
- Ensure repository has releases

## ✨ Features

- ✅ Fetch GitHub releases
- ✅ Select previous release tags
- ✅ Generate release notes with LLM
- ✅ Real-time preview
- ✅ Edit and save release notes
- ✅ View generated files

---

**Status**: Frontend is running! Start the backend to begin using the application.

