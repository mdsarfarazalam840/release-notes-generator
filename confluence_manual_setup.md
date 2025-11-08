# 📄 Confluence Manual Setup Guide

## 🔑 Step 1: Create Atlassian API Token

1. **Go to**: https://id.atlassian.com/manage-profile/security/api-tokens
2. **Click**: "Create API token"
3. **Label**: "Release Notes Generator"
4. **Copy the token** - Save it somewhere safe!

## 📝 Step 2: Add to .env File

Open your `.env` file in the project directory and add these lines:

```bash
# Confluence Configuration
CONFLUENCE_BASE=https://yourcompany.atlassian.net
CONFLUENCE_USER=your-email@company.com
CONFLUENCE_API_TOKEN=your_api_token_here
```

**Replace**:
- `yourcompany` with your actual Atlassian domain
- `your-email@company.com` with your Atlassian email
- `your_api_token_here` with the token you created

## 🧪 Step 3: Test Connection

Run this command to test your setup:
```bash
python setup_confluence.py status
```

## 🚀 Step 4: Use in Release Notes Generator

1. Start the server: `python run_enhanced_server.py`
2. Open: http://localhost:5173
3. Check the "📄 Confluence" checkbox
4. Generate release notes - they'll be auto-published!

## 📁 Step 5: Optional - Choose Confluence Space

You can also specify which space to publish to by adding:
```bash
CONFLUENCE_SPACE_KEY=DOCS
```

## 🔍 Example .env Configuration

```bash
GITHUB_TOKEN=your_github_token
OPENROUTER_API_KEY=your_openrouter_key

# Confluence Configuration
CONFLUENCE_BASE=https://mycompany.atlassian.net
CONFLUENCE_USER=john.doe@mycompany.com
CONFLUENCE_API_TOKEN=ATATTxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CONFLUENCE_SPACE_KEY=DOCS
```