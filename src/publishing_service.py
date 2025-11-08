"""Enhanced publishing service supporting multiple platforms."""
import json
import os
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from src.utils import env, load_config
try:
    from src.confluence_fix import publish_to_confluence_fixed as publish_to_confluence
except ImportError:
    from src.publish_to_confluence import publish as publish_to_confluence


class PublishingService:
    """Unified service for publishing to multiple platforms."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.platforms = {
            'confluence': self._publish_confluence,
            'github': self._publish_github_release,
            'slack': self._publish_slack,
            'email': self._publish_email,
            'webhook': self._publish_webhook
        }
    
    async def publish_release_notes(
        self,
        version: str,
        content: str,
        file_path: str,
        platforms: List[str],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Publish release notes to multiple platforms."""
        
        results = {}
        errors = {}
        
        for platform in platforms:
            if platform not in self.platforms:
                errors[platform] = f"Unsupported platform: {platform}"
                continue
            
            try:
                result = await self.platforms[platform](version, content, file_path, metadata)
                results[platform] = result
            except Exception as e:
                errors[platform] = str(e)
        
        return {
            'success': results,
            'errors': errors,
            'published_to': list(results.keys()),
            'failed_to': list(errors.keys())
        }
    
    async def _publish_confluence(
        self,
        version: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Publish to Confluence."""
        try:
            result = publish_to_confluence(version, file_path, update_existing=False)
            if result:
                # Get the full URL - fix the URL construction
                base_url = os.getenv('CONFLUENCE_BASE', 'https://yourcompany.atlassian.net')
                webui_path = result.get('_links', {}).get('webui', '')
                
                # Ensure webui_path starts with /wiki if it doesn't already
                if webui_path and not webui_path.startswith('/wiki'):
                    webui_path = '/wiki' + webui_path
                
                full_url = base_url + webui_path if webui_path else ''
                
                return {
                    'platform': 'confluence',
                    'status': 'published',
                    'url': full_url,
                    'page_id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'space': 'MFS'
                }
            else:
                raise Exception("No result returned from publish_to_confluence")
        except Exception as e:
            raise Exception(f"Confluence publishing failed: {str(e)}")
    
    async def _publish_github_release(
        self,
        version: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Publish as GitHub release."""
        token = env('GITHUB_TOKEN')
        repo = metadata.get('repo') if metadata else self.config.get('repo')
        
        if not token or not repo:
            raise ValueError("GitHub token and repository required")
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Check if release already exists
        existing_url = f'https://api.github.com/repos/{repo}/releases/tags/{version}'
        existing_response = requests.get(existing_url, headers=headers)
        
        payload = {
            'tag_name': version,
            'name': f'Release {version}',
            'body': content,
            'draft': False,
            'prerelease': version.count('-') > 0 or 'alpha' in version.lower() or 'beta' in version.lower()
        }
        
        if existing_response.status_code == 200:
            # Update existing release
            release_id = existing_response.json()['id']
            url = f'https://api.github.com/repos/{repo}/releases/{release_id}'
            response = requests.patch(url, headers=headers, json=payload)
        else:
            # Create new release
            url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.post(url, headers=headers, json=payload)
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'platform': 'github',
            'status': 'published',
            'url': result.get('html_url', ''),
            'release_id': result.get('id', '')
        }
    
    async def _publish_slack(
        self,
        version: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Publish to Slack via webhook."""
        webhook_url = env('SLACK_WEBHOOK_URL')
        
        if not webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL not configured")
        
        # Extract highlights from content for Slack message
        highlights = self._extract_highlights(content)
        repo = metadata.get('repo') if metadata else self.config.get('repo', 'Unknown')
        
        # Create Slack message
        slack_message = {
            "text": f"🚀 New Release: {version}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 {repo} - Release {version}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Highlights:*\n{highlights}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Full Release Notes"
                            },
                            "url": f"https://github.com/{repo}/releases/tag/{version}",
                            "action_id": "view_release"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(webhook_url, json=slack_message)
        response.raise_for_status()
        
        return {
            'platform': 'slack',
            'status': 'published',
            'message': 'Posted to Slack channel'
        }
    
    async def _publish_email(
        self,
        version: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send release notes via email."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = env('SMTP_HOST')
        smtp_port = int(env('SMTP_PORT', '587'))
        smtp_user = env('SMTP_USER')
        smtp_password = env('SMTP_PASSWORD')
        recipients = env('EMAIL_RECIPIENTS', '').split(',')
        
        if not all([smtp_host, smtp_user, smtp_password]) or not recipients:
            raise ValueError("Email configuration incomplete")
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Release Notes - {version}'
        msg['From'] = smtp_user
        msg['To'] = ', '.join(recipients)
        
        # Create HTML version
        html_content = self._markdown_to_html(content)
        html_part = MIMEText(html_content, 'html')
        
        # Create plain text version
        text_part = MIMEText(content, 'plain')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {
            'platform': 'email',
            'status': 'sent',
            'recipients': len(recipients),
            'message': f'Sent to {len(recipients)} recipients'
        }
    
    async def _publish_webhook(
        self,
        version: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Publish to custom webhook."""
        webhook_url = env('CUSTOM_WEBHOOK_URL')
        
        if not webhook_url:
            raise ValueError("CUSTOM_WEBHOOK_URL not configured")
        
        payload = {
            'version': version,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'repo': metadata.get('repo') if metadata else self.config.get('repo')
        }
        
        headers = {'Content-Type': 'application/json'}
        auth_token = env('WEBHOOK_AUTH_TOKEN')
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        
        return {
            'platform': 'webhook',
            'status': 'posted',
            'url': webhook_url,
            'response': response.status_code
        }
    
    def _extract_highlights(self, content: str, max_items: int = 3) -> str:
        """Extract highlights from release notes content."""
        lines = content.split('\n')
        highlights = []
        in_highlights = False
        
        for line in lines:
            line = line.strip()
            if 'highlight' in line.lower() and line.startswith('#'):
                in_highlights = True
                continue
            elif line.startswith('#') and in_highlights:
                break
            elif in_highlights and line.startswith('-') or line.startswith('*'):
                highlights.append(line[1:].strip())
                if len(highlights) >= max_items:
                    break
        
        if not highlights:
            # Fallback: extract first few bullet points
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    highlights.append(line[1:].strip())
                    if len(highlights) >= max_items:
                        break
        
        return '\n'.join(f"• {item}" for item in highlights[:max_items])
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to basic HTML for email."""
        try:
            import markdown
            return markdown.markdown(markdown)
        except ImportError:
            # Fallback: basic conversion
            html = markdown.replace('\n', '<br>')
            html = html.replace('**', '</strong>').replace('**', '<strong>')
            html = html.replace('*', '</em>').replace('*', '<em>')
            return f'<html><body>{html}</body></html>'
    
    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the configuration status of all platforms."""
        status = {}
        
        # Confluence
        status['confluence'] = {
            'name': 'Confluence',
            'configured': bool(env('CONFLUENCE_BASE') and env('CONFLUENCE_API_TOKEN')),
            'required_env': ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN'],
            'description': 'Publish to Confluence wiki pages'
        }
        
        # GitHub
        status['github'] = {
            'name': 'GitHub Releases',
            'configured': bool(env('GITHUB_TOKEN')),
            'required_env': ['GITHUB_TOKEN'],
            'description': 'Create GitHub releases'
        }
        
        # Slack
        status['slack'] = {
            'name': 'Slack',
            'configured': bool(env('SLACK_WEBHOOK_URL')),
            'required_env': ['SLACK_WEBHOOK_URL'],
            'description': 'Post notifications to Slack'
        }
        
        # Email
        status['email'] = {
            'name': 'Email',
            'configured': bool(env('SMTP_HOST') and env('SMTP_USER') and env('EMAIL_RECIPIENTS')),
            'required_env': ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'EMAIL_RECIPIENTS'],
            'description': 'Send release notes via email'
        }
        
        # Custom Webhook
        status['webhook'] = {
            'name': 'Custom Webhook',
            'configured': bool(env('CUSTOM_WEBHOOK_URL')),
            'required_env': ['CUSTOM_WEBHOOK_URL'],
            'optional_env': ['WEBHOOK_AUTH_TOKEN'],
            'description': 'Post to custom webhook endpoint'
        }
        
        return status


# Convenience function for automated publishing
async def auto_publish(
    version: str,
    file_path: str,
    platforms: Optional[List[str]] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Automatically publish to configured platforms."""
    
    if platforms is None:
        # Auto-detect configured platforms
        service = PublishingService()
        platform_status = service.get_platform_status()
        platforms = [name for name, status in platform_status.items() if status['configured']]
    
    if not platforms:
        return {
            'success': {},
            'errors': {'general': 'No platforms configured for publishing'},
            'published_to': [],
            'failed_to': []
        }
    
    # Read content from file
    content = Path(file_path).read_text(encoding='utf-8')
    
    service = PublishingService()
    return await service.publish_release_notes(version, content, file_path, platforms, metadata)


# CLI interface for manual publishing
if __name__ == '__main__':
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description='Publish release notes to multiple platforms')
    parser.add_argument('version', help='Release version')
    parser.add_argument('file_path', help='Path to release notes file')
    parser.add_argument('--platforms', nargs='+', 
                       choices=['confluence', 'github', 'slack', 'email', 'webhook'],
                       help='Platforms to publish to')
    parser.add_argument('--repo', help='Repository name (owner/repo)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be published without actually publishing')
    
    args = parser.parse_args()
    
    metadata = {'repo': args.repo} if args.repo else None
    
    if args.dry_run:
        service = PublishingService()
        status = service.get_platform_status()
        print("Platform Status:")
        for name, info in status.items():
            print(f"  {name}: {'✓' if info['configured'] else '✗'} {info['description']}")
    else:
        result = asyncio.run(auto_publish(args.version, args.file_path, args.platforms, metadata))
        print(f"Published to: {result['published_to']}")
        if result['failed_to']:
            print(f"Failed to publish to: {result['failed_to']}")
            for platform, error in result['errors'].items():
                print(f"  {platform}: {error}")