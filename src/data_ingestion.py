"""Enhanced data ingestion layer supporting multiple sources and formats."""
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timedelta
import requests
from src.utils import env, load_config
from scripts.extract_commits import extract_commits_local, extract_commits_github, extract_commits_between_tags
from scripts.fetch_issues import fetch_github_issues

# Force import GitHub token fix
try:
    from src.github_token_fix import inject_github_token
    inject_github_token()
except ImportError:
    pass


class DataIngestionService:
    """Unified service for ingesting data from multiple sources."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.jira_config = self._load_jira_config()
    
    def _get_github_token(self):
        """Get GitHub token with fresh environment reload."""
        # Force reload environment variables
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        current_dir = Path.cwd()
        env_file = current_dir / '.env'
        env_local_file = current_dir / '.env.local'
        
        if env_file.exists():
            load_dotenv(env_file)
        if env_local_file.exists():
            load_dotenv(env_local_file, override=True)
        
        token = os.getenv('GITHUB_TOKEN')
        print(f"DEBUG: Retrieved GitHub token: {'SET' if token else 'NOT SET'}")
        return token
    
    def _load_jira_config(self) -> Dict:
        """Load JIRA configuration from environment/config."""
        return {
            'base_url': env('JIRA_BASE_URL'),
            'username': env('JIRA_USERNAME'),
            'api_token': env('JIRA_API_TOKEN'),
            'project_key': env('JIRA_PROJECT_KEY')
        }
    
    async def ingest_commits(
        self,
        source: str = 'auto',  # 'local', 'github', 'auto'
        repo: Optional[str] = None,
        from_tag: Optional[str] = None,
        to_tag: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        branch: Optional[str] = None
    ) -> List[Dict]:
        """Ingest commits from various sources."""
        repo = repo or self.config.get('repo')
        
        github_token = self._get_github_token()
        
        if source == 'auto':
            # Use GitHub if token available, otherwise local
            source = 'github' if github_token else 'local'
        
        if source == 'github':
            # PERMANENT FIX: Use bulletproof GitHub API
            print("🔒 Using BulletproofGitHub API (permanent fix)")
            try:
                from src.bulletproof_github import bulletproof_github
                return bulletproof_github.get_commits(repo)
            except Exception as e:
                print(f"🚨 BulletproofGitHub failed: {e}")
                # Fallback to local if everything fails
                print("📁 Falling back to local git")
                return extract_commits_local('.', since=since, until=until)
        elif source == 'local':
            return extract_commits_local('.', since=since, until=until)
        else:
            raise ValueError(f"Unsupported commit source: {source}")
    
    async def ingest_issues(
        self,
        source: str = 'github',  # 'github', 'jira', 'json'
        repo: Optional[str] = None,
        milestone: Optional[str] = None,
        labels: Optional[List[str]] = None,
        since: Optional[str] = None,
        project_key: Optional[str] = None,
        json_file: Optional[str] = None
    ) -> List[Dict]:
        """Ingest issues from various sources."""
        
        if source == 'github':
            repo = repo or self.config.get('repo')
            # PERMANENT FIX: Use bulletproof GitHub API
            print("🔒 Using BulletproofGitHub for issues (permanent fix)")
            try:
                from src.bulletproof_github import bulletproof_github
                return bulletproof_github.get_issues(repo)
            except Exception as e:
                print(f"🚨 BulletproofGitHub issues failed: {e}")
                return []
        
        elif source == 'jira':
            return await self._fetch_jira_issues(
                project_key=project_key or self.jira_config.get('project_key'),
                since=since
            )
        
        elif source == 'json':
            return self._load_json_issues(json_file)
        
        else:
            raise ValueError(f"Unsupported issue source: {source}")
    
    async def _fetch_jira_issues(
        self,
        project_key: str,
        since: Optional[str] = None,
        status: str = 'Done'
    ) -> List[Dict]:
        """Fetch issues from JIRA."""
        if not all([
            self.jira_config['base_url'],
            self.jira_config['username'], 
            self.jira_config['api_token']
        ]):
            return []
        
        # Build JQL query
        jql_parts = [f'project = "{project_key}"']
        if status:
            jql_parts.append(f'status = "{status}"')
        if since:
            jql_parts.append(f'updated >= "{since}"')
        
        jql = ' AND '.join(jql_parts)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (self.jira_config['username'], self.jira_config['api_token'])
        
        url = f"{self.jira_config['base_url']}/rest/api/3/search"
        params = {
            'jql': jql,
            'maxResults': 1000,
            'fields': 'summary,description,status,priority,assignee,created,updated,fixVersions,labels'
        }
        
        try:
            response = requests.get(url, headers=headers, auth=auth, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert JIRA issues to standard format
            issues = []
            for item in data.get('issues', []):
                fields = item.get('fields', {})
                issues.append({
                    'id': item.get('key'),
                    'number': item.get('key'),
                    'title': fields.get('summary', ''),
                    'body': fields.get('description', ''),
                    'state': fields.get('status', {}).get('name', ''),
                    'labels': [label for label in fields.get('labels', [])],
                    'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                    'created_at': fields.get('created'),
                    'updated_at': fields.get('updated'),
                    'closed_at': fields.get('updated'),  # Use updated as closed for Done items
                    'url': f"{self.jira_config['base_url']}/browse/{item.get('key')}",
                    'source': 'jira'
                })
            
            return issues
            
        except Exception as e:
            print(f"Error fetching JIRA issues: {e}")
            return []
    
    def _load_json_issues(self, json_file: Optional[str]) -> List[Dict]:
        """Load issues from JSON file."""
        if not json_file:
            return []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize format if needed
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'issues' in data:
                return data['issues']
            else:
                return []
                
        except Exception as e:
            print(f"Error loading JSON issues: {e}")
            return []
    
    async def ingest_previous_releases(
        self,
        source: str = 'auto',  # 'github', 'local', 'changelog', 'auto'
        repo: Optional[str] = None,
        count: int = 3,
        current_version: Optional[str] = None
    ) -> List[Dict]:
        """Ingest previous release notes from various sources."""
        
        if source == 'auto':
            # Try GitHub first, then local files
            github_token = self._get_github_token()
            if github_token:
                try:
                    return await self._fetch_github_releases(repo, count, current_version)
                except:
                    pass
            return self._load_local_releases(count, current_version)
        
        elif source == 'github':
            return await self._fetch_github_releases(repo, count, current_version)
        
        elif source == 'local':
            return self._load_local_releases(count, current_version)
        
        elif source == 'changelog':
            return self._parse_changelog_file(count, current_version)
        
        else:
            raise ValueError(f"Unsupported release source: {source}")
    
    async def _fetch_github_releases(
        self,
        repo: Optional[str],
        count: int,
        current_version: Optional[str]
    ) -> List[Dict]:
        """Fetch releases from GitHub API."""
        repo = repo or self.config.get('repo')
        github_token = self._get_github_token()
        if not github_token or not repo:
            return []
        
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        url = f'https://api.github.com/repos/{repo}/releases'
        params = {'per_page': count * 2}  # Get extra in case current version is included
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            releases = response.json()
            
            # Filter out current version and drafts
            filtered = []
            for release in releases:
                if (release.get('tag_name') != current_version and 
                    not release.get('draft', False) and
                    len(filtered) < count):
                    filtered.append({
                        'version': release.get('tag_name'),
                        'name': release.get('name'),
                        'body': release.get('body', ''),
                        'published_at': release.get('published_at'),
                        'url': release.get('html_url'),
                        'source': 'github'
                    })
            
            return filtered
            
        except Exception as e:
            print(f"Error fetching GitHub releases: {e}")
            return []
    
    def _load_local_releases(self, count: int, current_version: Optional[str]) -> List[Dict]:
        """Load releases from local examples directory."""
        examples_dir = Path('examples')
        if not examples_dir.exists():
            return []
        
        release_files = sorted(
            examples_dir.glob('release_*.md'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        releases = []
        for file_path in release_files:
            if len(releases) >= count:
                break
            
            # Extract version from filename
            version = file_path.stem.replace('release_', '')
            if version == current_version:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                # Extract title from first line
                lines = content.strip().split('\n')
                title = lines[0].strip('# ') if lines else version
                
                releases.append({
                    'version': version,
                    'name': title,
                    'body': content,
                    'published_at': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'url': str(file_path),
                    'source': 'local'
                })
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        return releases
    
    def _parse_changelog_file(self, count: int, current_version: Optional[str]) -> List[Dict]:
        """Parse releases from CHANGELOG.md file."""
        changelog_path = Path('CHANGELOG.md')
        if not changelog_path.exists():
            return []
        
        try:
            content = changelog_path.read_text(encoding='utf-8')
            # Basic changelog parsing - can be enhanced based on format
            # This is a simple implementation
            releases = []
            current_release = None
            
            for line in content.split('\n'):
                # Look for version headers (## [1.2.3] or # v1.2.3)
                if line.startswith('##') and '[' in line and ']' in line:
                    if current_release and len(releases) < count:
                        releases.append(current_release)
                    
                    version = line.split('[')[1].split(']')[0]
                    if version != current_version:
                        current_release = {
                            'version': version,
                            'name': line.strip('# '),
                            'body': '',
                            'source': 'changelog'
                        }
                elif current_release:
                    current_release['body'] += line + '\n'
            
            # Add last release
            if current_release and len(releases) < count:
                releases.append(current_release)
            
            return releases[:count]
            
        except Exception as e:
            print(f"Error parsing CHANGELOG.md: {e}")
            return []

    def upload_json_data(self, file_path: str, data_type: str = 'issues') -> bool:
        """Save uploaded JSON data for processing."""
        try:
            upload_dir = Path('uploads')
            upload_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_path = upload_dir / f"{data_type}_{timestamp}.json"
            
            # Copy uploaded file
            import shutil
            shutil.copy2(file_path, saved_path)
            
            return True
            
        except Exception as e:
            print(f"Error saving uploaded data: {e}")
            return False


# Convenience functions for backward compatibility
async def ingest_all_data(
    version: str,
    repo: Optional[str] = None,
    from_tag: Optional[str] = None,
    since: Optional[str] = None,
    commit_source: str = 'auto',
    issue_source: str = 'github',
    include_previous: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """Ingest all data sources and return combined dataset."""
    
    service = DataIngestionService()
    
    # Ingest commits
    commits = await service.ingest_commits(
        source=commit_source,
        repo=repo,
        from_tag=from_tag,
        since=since,
        **{k: v for k, v in kwargs.items() if k in ['to_tag', 'until', 'branch']}
    )
    
    # Ingest issues
    issues = await service.ingest_issues(
        source=issue_source,
        repo=repo,
        since=since,
        **{k: v for k, v in kwargs.items() if k in ['milestone', 'labels', 'project_key', 'json_file']}
    )
    
    # Ingest previous releases
    previous_releases = []
    if include_previous:
        previous_releases = await service.ingest_previous_releases(
            source=kwargs.get('release_source', 'auto'),
            repo=repo,
            current_version=version,
            count=kwargs.get('count', 3)
        )
    
    return {
        'commits': commits,
        'issues': issues,
        'previous_releases': previous_releases,
        'metadata': {
            'version': version,
            'repo': repo,
            'sources': {
                'commits': commit_source,
                'issues': issue_source,
                'releases': 'auto' if include_previous else 'none'
            },
            'ingested_at': datetime.now().isoformat()
        }
    }