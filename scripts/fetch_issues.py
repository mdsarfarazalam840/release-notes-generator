"""Fetch issues from GitHub or Jira. This example shows GitHub issues via REST API."""
import os
import requests
import yaml
import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

# Add src to path and inject GitHub token
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.github_token_fix import inject_github_token
    inject_github_token()
except ImportError:
    pass

def fetch_github_issues(
    repo: str, 
    token: str, 
    state: str = 'closed',
    milestone: Optional[str] = None,
    labels: Optional[List[str]] = None,
    since: Optional[str] = None,
    assignee: Optional[str] = None
) -> List[dict]:
    """Fetch issues from GitHub with filtering options."""
    # Reload environment variables to ensure we have latest token
    try:
        from src.utils import reload_env, env
        reload_env()
        # Use provided token, or fall back to environment variable
        if not token:
            token = env('GITHUB_TOKEN')
    except ImportError:
        # Fallback to os.getenv if utils not available
        from dotenv import load_dotenv
        from pathlib import Path
        current_dir = Path.cwd()
        env_file = current_dir / '.env'
        env_local_file = current_dir / '.env.local'
        if env_file.exists():
            load_dotenv(env_file)
        if env_local_file.exists():
            load_dotenv(env_local_file, override=True)
        if not token:
            token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        raise ValueError("GITHUB_TOKEN not provided and not found in environment variables (.env.local)")
    
    print(f"DEBUG fetch_github_issues: Token loaded successfully")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    params = {
        'state': state,
        'per_page': 100,
        'sort': 'updated',
        'direction': 'desc'
    }
    
    if milestone:
        # Get milestone number
        milestones = fetch_milestones(repo, token)
        for m in milestones:
            if m['title'] == milestone or m['number'] == int(milestone) if milestone.isdigit() else None:
                params['milestone'] = m['number']
                break
    
    if labels:
        params['labels'] = ','.join(labels)
    
    if assignee:
        params['assignee'] = assignee
    
    issues = []
    url = f'https://api.github.com/repos/{repo}/issues'
    
    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        
        # Filter by date if provided
        if since:
            since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
            filtered = []
            for issue in data:
                closed_at = issue.get('closed_at')
                if closed_at:
                    closed_date = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
                    if closed_date >= since_date:
                        filtered.append(issue)
            issues.extend(filtered)
        else:
            issues.extend(data)
        
        # Pagination
        if 'next' in r.links:
            url = r.links['next']['url']
            params = {}  # Params already in URL
        else:
            url = None
    
    return issues

load_dotenv('.env.local')
def fetch_milestones(repo: str, token: str, state: str = 'all') -> List[dict]:
    """Fetch milestones from GitHub."""
    # CRITICAL FIX: Force working token for milestones
    token = os.getenv('GITHUB_TOKEN', token)  # Fallback to function argument if not found
    print(f"🚨 CRITICAL FIX: Forcing token {WORKING_TOKEN[:10]}... in fetch_milestones")
    
    headers = {'Authorization': f'token {token}'}
    url = f'https://api.github.com/repos/{repo}/milestones?state={state}&per_page=100'
    milestones = []
    
    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        milestones.extend(r.json())
        
        if 'next' in r.links:
            url = r.links['next']['url']
        else:
            url = None
    
    return milestones

def fetch_issues_by_milestone(repo: str, token: str, milestone: str) -> List[dict]:
    """Fetch issues for a specific milestone."""
    return fetch_github_issues(repo, token, milestone=milestone)

def fetch_issues_by_label(repo: str, token: str, labels: List[str], state: str = 'closed') -> List[dict]:
    """Fetch issues with specific labels."""
    return fetch_github_issues(repo, token, labels=labels, state=state)

if __name__ == '__main__':
    import json, os, sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Load config from config.yaml
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    repo = config.get('repo', 'owner/repo')
    token = os.getenv('GITHUB_TOKEN')
    data = fetch_github_issues(repo, token)
    print(json.dumps(data[:20], indent=2))
