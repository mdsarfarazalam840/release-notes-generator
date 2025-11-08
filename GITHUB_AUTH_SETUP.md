# GitHub Authentication Setup Guide

## Issue Fixed ✅

The **401 Unauthorized error** when accessing GitHub API has been resolved. The release notes generator now properly loads GitHub authentication from environment variables.

## What Was Fixed

1. **Import Path Issues**: Fixed module import paths to work from any directory
2. **Environment Variable Loading**: Enhanced `.env` file discovery to work from any working directory
3. **Template Path Resolution**: Fixed template file path resolution for cross-directory execution
4. **Configuration Loading**: Made `config.yaml` loading work from any directory

## Authentication Setup

### 1. Environment Variables

Your GitHub token should be stored in `.env.local` (which is already configured):

```bash
# .env.local (DO NOT COMMIT THIS FILE)
GITHUB_TOKEN=Your Github Token
OPENROUTER_API_KEY=Your OpenRouter API Key
CONFLUENCE_BASE=Your Confluence URL contains like this -> https://testing.atlassian.net
CONFLUENCE_USER=Your Confluence EMAIL ID
CONFLUENCE_SPACE=Your Confluence SPACE name
CONFLUENCE_API_TOKEN=Your confluence API token
```

### 2. GitHub Token Permissions

Your GitHub token needs these permissions:
- `repo` (for private repositories)
- `public_repo` (for public repositories)
- `read:org` (if accessing organization repositories)

## Usage Examples

### Standard Generator

```bash
# Using module approach (recommended)
python -m src.generate_notes --version v1.2.0 --use-github

# Using direct script execution
cd src && python generate_notes.py --version v1.2.0 --use-github
```

### Enhanced Generator

```bash
# Enhanced version with GitHub source
python -m src.enhanced_generate_notes --version v1.2.0 --commit-source github

# With Confluence publishing
python -m src.enhanced_generate_notes --version v1.2.0 --commit-source github --publish confluence
```

### Simplified Wrapper Script

```bash
# Use the new simplified script
python generate_release_notes.py --version v1.2.0 --use-github
python generate_release_notes.py --version v1.2.0 --enhanced --use-github --publish-confluence
```

## Verification

Test your GitHub authentication:

```bash
python -c "
import requests
from src.utils import env
token = env('GITHUB_TOKEN')
headers = {'Authorization': f'token {token}'}
r = requests.get('https://api.github.com/repos/mdsarfarazalam840/release-notes-generator/commits?per_page=1', headers=headers)
print(f'Status: {r.status_code}')
print(f'Success: {r.status_code == 200}')
"
```

## Troubleshooting

1. **401 Unauthorized**: Check that `GITHUB_TOKEN` is set in `.env.local`
2. **403 Forbidden**: Your token may have insufficient permissions
3. **Module not found**: Use `python -m src.generate_notes` instead of direct execution
4. **File not found**: Make sure you're running from the project root directory

## Security Notes

- Never commit `.env.local` to version control
- The `.env.local` file is already in `.gitignore`
- Use environment-specific tokens for different environments
- Rotate tokens periodically for security