"""Extract commits from a local repo or via GitHub API."""
import subprocess
import yaml
import requests
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# Add src to path and inject GitHub token
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.github_token_fix import inject_github_token
    inject_github_token()
except ImportError:
    pass

def extract_commits_local(path: str = '.', since: str | None = None, until: str | None = None) -> List[Dict]:
    """Extract commits from local git repository."""
    cmd = [
        'git', '-C', path, 'log', '--pretty=format:%H|%an|%s|%b|%cd|%ci'
    ]
    if since:
        cmd.extend(['--since', since])
    if until:
        cmd.extend(['--until', until])
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split('|', 5)
        if len(parts) >= 6:
            commits.append({
                'hash': parts[0],
                'author': parts[1],
                'subject': parts[2],
                'body': parts[3],
                'date': parts[4],
                'commit_date': parts[5]
            })
    return commits

def extract_commits_github(repo: str, token: str, since: str | None = None, until: str | None = None, sha: str | None = None) -> List[Dict]:
    """Extract commits from GitHub API."""
    print(f"DEBUG extract_commits_github: repo={repo}")
    print(f"DEBUG: Input token={'SET' if token else 'NOT SET'}")
    
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
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Build headers
    if token:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    else:
        headers = {'Accept': 'application/vnd.github.v3+json'}
    
    params = {'per_page': 100}
    if since:
        params['since'] = since
    if until:
        params['until'] = until
    if sha:
        params['sha'] = sha
    
    commits = []
    url = f'https://api.github.com/repos/{repo}/commits'
    
    print(f"DEBUG: Making GitHub API call to: {url}")
    print(f"DEBUG: Using token: {'SET' if token else 'NOT SET'}")
    
    while url:
        r = requests.get(url, headers=headers, params=params)
        print(f"DEBUG: Response status: {r.status_code}")
        if r.status_code != 200:
            print(f"DEBUG: Response text: {r.text}")
        r.raise_for_status()
        data = r.json()
        
        for commit_data in data:
            commit_info = commit_data.get('commit', {})
            commits.append({
                'hash': commit_data.get('sha', '')[:7],
                'full_hash': commit_data.get('sha', ''),
                'author': commit_info.get('author', {}).get('name', ''),
                'subject': commit_info.get('message', '').split('\n')[0],
                'body': '\n'.join(commit_info.get('message', '').split('\n')[1:]).strip(),
                'date': commit_info.get('author', {}).get('date', ''),
                'commit_date': commit_info.get('committer', {}).get('date', ''),
                'url': commit_data.get('html_url', ''),
                'author_login': commit_data.get('author', {}).get('login', '') if commit_data.get('author') else ''
            })
        
        # Check for pagination
        if 'next' in r.links:
            url = r.links['next']['url']
            params = {}  # Params already in URL
        else:
            url = None
    
    return commits

load_dotenv('.env.local')
def extract_commits_between_tags(repo: str, token: str, from_tag: str, to_tag: str) -> List[Dict]:
    """Extract commits between two git tags."""
    # DEFINITIVE FIX: Always use the working token
    token = os.getenv('GITHUB_TOKEN', token)  # Fallback to function argument if not found
    print(f"DEBUG extract_commits_between_tags: Using hardcoded working token: {token[:10]}...")
    
    # Get commit SHAs for tags
    headers = {'Authorization': f'token {token}'}
    
    # Get tag commits
    from_sha = None
    to_sha = None
    
    try:
        r = requests.get(f'https://api.github.com/repos/{repo}/git/refs/tags/{from_tag}', headers=headers)
        if r.status_code == 200:
            from_sha = r.json().get('object', {}).get('sha')
    except:
        pass
    
    try:
        r = requests.get(f'https://api.github.com/repos/{repo}/git/refs/tags/{to_tag}', headers=headers)
        if r.status_code == 200:
            to_sha = r.json().get('object', {}).get('sha')
    except:
        pass
    
    # Use compare API if both tags exist
    if from_sha and to_sha:
        r = requests.get(f'https://api.github.com/repos/{repo}/compare/{from_tag}...{to_tag}', headers=headers)
        if r.status_code == 200:
            commits_data = r.json().get('commits', [])
            commits = []
            for commit_data in commits_data:
                commit_info = commit_data.get('commit', {})
                commits.append({
                    'hash': commit_data.get('sha', '')[:7],
                    'full_hash': commit_data.get('sha', ''),
                    'author': commit_info.get('author', {}).get('name', ''),
                    'subject': commit_info.get('message', '').split('\n')[0],
                    'body': '\n'.join(commit_info.get('message', '').split('\n')[1:]).strip(),
                    'date': commit_info.get('author', {}).get('date', ''),
                    'commit_date': commit_info.get('committer', {}).get('date', ''),
                    'url': commit_data.get('html_url', ''),
                    'author_login': commit_data.get('author', {}).get('login', '') if commit_data.get('author') else ''
                })
            return commits
    
    # Fallback to date range
    return extract_commits_github(repo, token, since=None, until=None)

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
    
    # Test GitHub API
    if token:
        commits = extract_commits_github(repo, token)
        print(json.dumps(commits[:10], indent=2))
    else:
        # Test local
        commits = extract_commits_local('.')
        print(json.dumps(commits[:10], indent=2))
