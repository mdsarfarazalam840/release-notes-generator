# Release Notes Generator

Generates audience-specific release notes from git commits and issue trackers using an LLM.

## Quick Start

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env.local` and fill in your API keys (see [GITHUB_AUTH_SETUP.md](GITHUB_AUTH_SETUP.md))
4. Run: `python generate_release_notes.py --version v1.0.0 --use-github`

### Alternative Usage Methods

```bash
# Standard generator
python -m src.generate_notes --version v1.0.0 --use-github

# Enhanced generator  
python -m src.enhanced_generate_notes --version v1.0.0 --commit-source github

# Simplified wrapper script (recommended)
python generate_release_notes.py --version v1.0.0 --use-github
```

## Prerequisites

- Python 3.11+ installed
- Git installed (for commit extraction)
- Node.js 18+ (optional, for frontend)
- Docker Desktop (optional, for containerized deployment)

## Features

✅ **GitHub Integration**
- Fetch commit history directly from GitHub API
- Extract commits between git tags/releases
- Filter commits by date range
- Access commits even without local git clone

✅ **Issue Tracker Integration**
- Fetch issues from GitHub with advanced filtering
- Filter by milestone, labels, assignee
- Filter by date range
- Automatic pagination support

✅ **Previous Release Notes**
- Automatically fetch previous release notes from GitHub releases
- Learn from historical context
- Maintain consistency across releases
- Reference CHANGELOG.md from repository

✅ **Automated Publishing**
- Publish release notes directly to Confluence
- Auto-update existing pages or create new ones
- Proper markdown to Confluence storage format conversion
- Configurable parent pages and spaces

✅ **Smart Commit Classification**
- Automatic classification (feature, bug, docs, refactor, etc.)
- Context-aware categorization

✅ **Multiple Audience Support**
- Generate notes for different audiences (users, developers, managers)
- Tailored content based on target audience

✅ **LLM Integration**
- Support for OpenRouter API (cost-effective)
- Support for OpenAI API
- Configurable models and temperature

## Local Setup - Step by Step

### Step 1: Clone or Extract the Repository

```bash
# If using git
git clone <repository-url>
cd release-notes-generator

# Or extract the zip file to your desired location
```

### Step 2: Create Environment File

Create a `.env` file in the project root with your credentials:

```bash
# Use OpenRouter or OpenAI (OpenRouter preferred)
OPENROUTER_API_KEY=your_openrouter_key   # if set, OpenRouter is used
# OPENAI_API_KEY=your_openai_key         # fallback if OPENROUTER_API_KEY not set

# Required for fetching GitHub issues
GITHUB_TOKEN=your_github_pat

# Optional: Slack notifications
SLACK_WEBHOOK=your_slack_webhook_url

# Optional: Confluence publishing (for --publish-confluence flag)
CONFLUENCE_BASE=https://your-domain.atlassian.net
CONFLUENCE_USER=your_email@example.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
# Note: Also configure confluence_space and confluence_parent_page_id in config.yaml
```

### Step 3: Set Up Python Virtual Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt
```

### Step 5: Configure Repository Settings

Edit `config.yaml` and set your GitHub repository:

```yaml
repo: "your-org/your-repo"  # Change this to your repository
batch_size: 200
llm:
  model: "meta-llama/llama-3-70b-instruct"  # Or any OpenRouter model
  temperature: 0.0
publish:
  confluence_space: "DOCS"
  confluence_parent_page_id: 123456
```

### Step 6: Verify Setup (Run Tests)

**Windows (CMD):**
```cmd
set PYTHONPATH=.
pytest -q
```

**Linux/Mac:**
```bash
PYTHONPATH=. pytest -q
```

You should see: `6 passed` if everything is set up correctly.

### Step 7: Generate Release Notes

**Windows (CMD):**
```cmd
set PYTHONPATH=.
python src/generate_notes.py --version v1.2.0 --audience users
```

**Linux/Mac:**
```bash
PYTHONPATH=. python src/generate_notes.py --version v1.2.0 --audience users
```

**Available audiences:**
- `users` - User-facing release notes
- `developers` - Technical release notes
- `managers` - High-level summary

Output will be written to: `examples/release_v1.2.0.md`

### Step 7 Advanced: Advanced Options

The generator supports many advanced options:

**Fetch commits from GitHub API:**
```bash
# Windows (CMD)
set PYTHONPATH=.
python src/generate_notes.py --version v1.2.0 --audience users --use-github

# Linux/Mac
PYTHONPATH=. python src/generate_notes.py --version v1.2.0 --audience users --use-github
```

**Fetch commits between tags:**
```bash
python src/generate_notes.py --version v1.2.0 --from-tag v1.1.0 --use-github
```

**Filter issues by milestone:**
```bash
python src/generate_notes.py --version v1.2.0 --milestone "v1.2.0"
```

**Filter issues by labels:**
```bash
python src/generate_notes.py --version v1.2.0 --labels "bug,enhancement"
```

**Filter by date range:**
```bash
python src/generate_notes.py --version v1.2.0 --since "2024-01-01T00:00:00Z"
```

**Publish to Confluence:**
```bash
python src/generate_notes.py --version v1.2.0 --publish-confluence
```

**Complete example with all features:**
```bash
python src/generate_notes.py \
  --version v1.2.0 \
  --audience developers \
  --use-github \
  --from-tag v1.1.0 \
  --milestone "v1.2.0" \
  --labels "bug,enhancement" \
  --publish-confluence
```

### Step 8 (Optional): Run Frontend Preview

```bash
cd frontend
npm install
npm run dev
```

Open your browser to `http://localhost:5173` to preview the frontend.

## Components
- `scripts/extract_commits.py` — extract commits from local git or GitHub API
- `scripts/fetch_issues.py` — fetch and filter issues from GitHub
- `scripts/fetch_releases.py` — fetch previous release notes and changelogs
- `scripts/classify_change.py` — classify commits by type (feature, bug, etc.)
- `src/generate_notes.py` — main orchestration, LLM call, and workflow
- `src/publish_to_confluence.py` — automated publishing to Confluence
- `src/utils.py` — configuration and environment utilities
- `templates/prompt.md` — LLM prompt template
- `config.yaml` — project configuration

## Confluence Publishing Configuration

To enable automated publishing to Confluence:

1. **Set environment variables in `.env`:**
   ```bash
   CONFLUENCE_BASE=https://your-domain.atlassian.net
   CONFLUENCE_USER=your_email@example.com
   CONFLUENCE_API_TOKEN=your_confluence_api_token
   ```

2. **Configure in `config.yaml`:**
   ```yaml
   publish:
     confluence_space: "DOCS"  # Your Confluence space key
     confluence_parent_page_id: 123456  # Optional: Parent page ID
   ```

3. **Generate and publish:**
   ```bash
   python src/generate_notes.py --version v1.2.0 --publish-confluence
   ```

The system will automatically:
- Check if a page with the same title exists
- Update existing page or create new one
- Convert markdown to Confluence storage format
- Link to parent page if configured

## Docker Deployment

### Option 1: Using Docker Run (Backend Only)

**Step 1: Build the Backend Image**
```bash
docker build -t release-notes-generator:latest -f docker/Dockerfile .
```

**Step 2: Run the Container**
```bash
# Windows (PowerShell)
docker run --rm --env-file .env -v ${PWD}:/app release-notes-generator:latest

# Linux/Mac
docker run --rm --env-file .env -v $(pwd):/app release-notes-generator:latest
```

**Step 3: Run with Custom Version**
```bash
docker run --rm --env-file .env -v ${PWD}:/app release-notes-generator:latest python src/generate_notes.py --version v1.2.0 --audience users
```

### Option 2: Using Docker Compose (Backend + Frontend)

**Step 1: Ensure .env file exists in project root**

**Step 2: Run Production Build (Backend + Frontend)**
```bash
# Build and run both services
docker compose -f docker/docker-compose.yml up --build

# Access:
# - Backend: Runs release notes generation
# - Frontend: http://localhost:3000 (or custom port via FRONTEND_PORT env var)
```

**Step 3: Run with Custom Version**
```bash
# Windows (PowerShell)
$env:RELEASE_VERSION="v1.2.0"
$env:AUDIENCE="users"
$env:FRONTEND_PORT="3000"
docker compose -f docker/docker-compose.yml up --build

# Linux/Mac
RELEASE_VERSION=v1.2.0 AUDIENCE=users FRONTEND_PORT=3000 docker compose -f docker/docker-compose.yml up --build
```

**Step 4: Run in Development Mode (Hot Reload)**
```bash
# Frontend with hot reload, Backend stays running
docker compose -f docker/docker-compose.dev.yml up --build

# Access:
# - Backend: Running and waiting for commands (can exec into container)
# - Frontend: http://localhost:5173 (Vite dev server with hot reload)
```

**Step 5: Execute Commands in Development Backend**
```bash
# After starting dev mode, run release notes generation
docker exec -it release-notes-backend-dev python src/generate_notes.py --version v1.2.0 --audience users
```

The output will be written to `examples/release_{VERSION}.md` in your project directory.

### Push to Docker Hub

**Step 1: Build Both Images**
```bash
# Build backend
docker build -t release-notes-generator:latest -f docker/Dockerfile .

# Build frontend
docker build -t release-notes-generator-frontend:latest -f docker/Dockerfile.frontend .
```

**Step 2: Login to Docker Hub**
```bash
docker login
```

**Step 3: Tag Both Images**
```bash
# Tag backend
docker tag release-notes-generator:latest YOUR_DOCKERHUB_USERNAME/release-notes-generator:latest

# Tag frontend
docker tag release-notes-generator-frontend:latest YOUR_DOCKERHUB_USERNAME/release-notes-generator-frontend:latest
```

**Step 4: Push Both Images**
```bash
# Push backend
docker push YOUR_DOCKERHUB_USERNAME/release-notes-generator:latest

# Push frontend
docker push YOUR_DOCKERHUB_USERNAME/release-notes-generator-frontend:latest
```

**Step 5: Pull and Run from Docker Hub**
```bash
# Pull backend
docker pull YOUR_DOCKERHUB_USERNAME/release-notes-generator:latest

# Pull frontend
docker pull YOUR_DOCKERHUB_USERNAME/release-notes-generator-frontend:latest

# Run backend
docker run --rm --env-file .env -v $(pwd):/app YOUR_DOCKERHUB_USERNAME/release-notes-generator:latest

# Run frontend
docker run --rm -p 3000:80 YOUR_DOCKERHUB_USERNAME/release-notes-generator-frontend:latest
```

## License
MIT

## Tests & Linting

Run tests locally with `pytest` and lint with `flake8`.

## Frontend

A minimal Vite + React preview app is included in `frontend/`.

## Packaging

A zip archive of the project is created at `/mnt/data/release-notes-generator.zip` in this environment.
