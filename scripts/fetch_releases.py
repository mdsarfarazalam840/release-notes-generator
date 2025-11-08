"""Fetch previous release notes and changelogs from GitHub."""
import requests
import yaml
from typing import List, Dict, Optional
from datetime import datetime

def fetch_github_releases(repo: str, token: str, limit: int = 10) -> List[Dict]:
    """Fetch GitHub releases."""
    # Reload environment variables to ensure we have latest token
    import os
    from pathlib import Path
    try:
        from src.utils import reload_env, env
        reload_env()
        if not token:
            token = env('GITHUB_TOKEN')
    except ImportError:
        from dotenv import load_dotenv
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
    
    print(f"DEBUG fetch_github_releases: Using token: {token[:10]}...")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{repo}/releases'
    params = {'per_page': limit}
    
    releases = []
    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        
        for release in data:
            releases.append({
                'tag_name': release.get('tag_name', ''),
                'name': release.get('name', ''),
                'body': release.get('body', ''),
                'published_at': release.get('published_at', ''),
                'created_at': release.get('created_at', ''),
                'author': release.get('author', {}).get('login', '') if release.get('author') else '',
                'prerelease': release.get('prerelease', False),
                'draft': release.get('draft', False),
                'url': release.get('html_url', '')
            })
        
        if 'next' in r.links:
            url = r.links['next']['url']
            params = {}
        else:
            url = None
        
        if len(releases) >= limit:
            break
    
    return releases[:limit]

def fetch_release_by_tag(repo: str, token: str, tag: str) -> Optional[Dict]:
    """Fetch a specific release by tag."""
    # Reload environment variables to ensure we have latest token
    import os
    from pathlib import Path
    try:
        from src.utils import reload_env, env
        reload_env()
        if not token:
            token = env('GITHUB_TOKEN')
    except ImportError:
        from dotenv import load_dotenv
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
    
    print(f"DEBUG fetch_release_by_tag: Using token: {token[:10]}...")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{repo}/releases/tags/{tag}'
    r = requests.get(url, headers=headers)
    
    if r.status_code == 404:
        return None
    
    r.raise_for_status()
    release = r.json()
    
    return {
        'tag_name': release.get('tag_name', ''),
        'name': release.get('name', ''),
        'body': release.get('body', ''),
        'published_at': release.get('published_at', ''),
        'created_at': release.get('created_at', ''),
        'author': release.get('author', {}).get('login', '') if release.get('author') else '',
        'prerelease': release.get('prerelease', False),
        'draft': release.get('draft', False),
        'url': release.get('html_url', '')
    }

def fetch_changelog_from_repo(repo: str, token: str) -> Optional[str]:
    """Fetch CHANGELOG.md or similar file from repository."""
    # Reload environment variables to ensure we have latest token
    import os
    from pathlib import Path
    try:
        from src.utils import reload_env, env
        reload_env()
        if not token:
            token = env('GITHUB_TOKEN')
    except ImportError:
        from dotenv import load_dotenv
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
    
    print(f"DEBUG fetch_changelog_from_repo: Using token: {token[:10]}...")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    
    # Try common changelog file names
    changelog_files = ['CHANGELOG.md', 'CHANGELOG', 'Changelog.md', 'changelog.md', 'HISTORY.md']
    
    for filename in changelog_files:
        try:
            url = f'https://api.github.com/repos/{repo}/contents/{filename}'
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = r.json().get('content', '')
                # Base64 decode if needed
                import base64
                if content:
                    return base64.b64decode(content).decode('utf-8')
        except:
            continue
    
    return None

def get_previous_release_notes(repo: str, token: str, current_version: str, count: int = 3) -> List[Dict]:
    """Get previous release notes before the current version."""
    releases = fetch_github_releases(repo, token, limit=50)
    
    # Filter out current version and get previous ones
    previous = []
    for release in releases:
        if release['tag_name'] != current_version and not release['draft']:
            previous.append(release)
        if len(previous) >= count:
            break
    
    return previous

if __name__ == '__main__':
    import json, os
     # Load config from config.yaml
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    repo = config.get('repo', 'owner/repo')
    token = os.getenv('GITHUB_TOKEN')
    
    if token:
        releases = fetch_github_releases(repo, token, limit=5)
        print(json.dumps(releases, indent=2))
        
        changelog = fetch_changelog_from_repo(repo, token)
        if changelog:
            print("\n=== CHANGELOG ===")
            print(changelog[:500])  # First 500 chars

