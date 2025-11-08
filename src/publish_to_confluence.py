"""Publish a markdown file to Confluence via REST API."""
import os
import requests
import re
from src.utils import env, load_config
from typing import Optional

CFG = load_config()

# Force environment variable loading with fallbacks
def get_confluence_config():
    from dotenv import load_dotenv
    load_dotenv(override=True)
    load_dotenv('.env.local', override=True)
    
    # Use os.getenv directly to ensure fresh values
    base = os.getenv('CONFLUENCE_BASE')
    user = os.getenv('CONFLUENCE_USER') 
    token = os.getenv('CONFLUENCE_API_TOKEN')
    
    print(f"DEBUG - Confluence config:")
    print(f"  Base: {base}")
    print(f"  User: {user}")
    print(f"  Token: {'SET' if token and not token.startswith('your_') else 'NOT SET'}")
    
    return base, user, token

# Don't set module-level variables - get them fresh each time
SPACE = CFG['publish'].get('confluence_space', 'MFS')  # Use existing space "My first space"
PARENT_ID = CFG['publish'].get('confluence_parent_page_id', None)

def md_to_storage_format(md: str, title: str = 'Release Notes') -> dict:
    """Convert markdown to Confluence storage format."""
    # Basic markdown to Confluence wiki format conversion
    # Confluence uses storage format which is similar to HTML
    
    # Escape HTML
    html = md
    
    # Convert headers
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Convert bullet lists
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            result.append(f'<li>{content}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if line.strip():
                result.append(f'<p>{line}</p>')
            else:
                result.append('<p></p>')
    if in_list:
        result.append('</ul>')
    
    html = '\n'.join(result)
    
    # Convert code blocks (basic)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    return {
        'type': 'page',
        'title': title,
        'space': {'key': SPACE},
        'body': {
            'storage': {
                'value': html,
                'representation': 'storage'
            }
        }
    }

def find_existing_page(space: str, title: str) -> Optional[str]:
    """Find existing page by title."""
    BASE, USER, TOKEN = get_confluence_config()
    
    if not BASE or not USER or not TOKEN:
        return None
    
    url = f'{BASE}/wiki/rest/api/content'
    params = {
        'spaceKey': space,
        'title': title,
        'expand': 'version'
    }
    
    try:
        r = requests.get(url, auth=(USER, TOKEN), params=params)
        if r.status_code == 200:
            results = r.json().get('results', [])
            if results:
                return results[0].get('id')
    except:
        pass
    
    return None

def publish(version: str, md_path: str, update_existing: bool = True):
    """Publish or update release notes in Confluence."""
    BASE, USER, TOKEN = get_confluence_config()
    
    if not BASE or not USER or not TOKEN:
        print('Confluence credentials not configured. Skipping publish.')
        return None
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()
    
    title = f'Release Notes - {version}'
    
    # Check if page exists
    existing_id = find_existing_page(SPACE, title) if update_existing else None
    
    if existing_id:
        # Update existing page
        url = f'{BASE}/wiki/rest/api/content/{existing_id}'
        
        # Get current version
        r = requests.get(url, auth=(USER, TOKEN), params={'expand': 'version'})
        current_version = r.json().get('version', {}).get('number', 1)
        
        payload = md_to_storage_format(md, title)
        payload['version'] = {'number': current_version + 1}
        payload['id'] = existing_id
        
        # Set parent if configured
        if PARENT_ID:
            payload['ancestors'] = [{'id': PARENT_ID}]
        
        r = requests.put(url, auth=(USER, TOKEN), json=payload)
        r.raise_for_status()
        result = r.json()
        print(f'Updated Confluence page: {result.get("_links", {}).get("webui", "")}')
        return result
    else:
        # Create new page
        payload = md_to_storage_format(md, title)
        
        # Set parent if configured
        if PARENT_ID:
            payload['ancestors'] = [{'id': PARENT_ID}]
        
        # Try different API endpoints for creating content
        possible_urls = [
            f'{BASE}/wiki/rest/api/content',
            f'{BASE}/rest/api/content'
        ]
        
        success = False
        for url in possible_urls:
            try:
                r = requests.post(url, auth=(USER, TOKEN), json=payload)
                if r.status_code in [200, 201]:
                    success = True
                    break
                elif r.status_code == 404:
                    continue  # Try next URL
                else:
                    print(f"Error {r.status_code} for {url}: {r.text[:100]}")
            except Exception as e:
                print(f"Error posting to {url}: {e}")
                continue
        
        if not success:
            raise Exception(f"All API endpoints failed. Last status: {r.status_code if 'r' in locals() else 'Unknown'}")
        r.raise_for_status()
        result = r.json()
        print(f'Published to Confluence: {result.get("_links", {}).get("webui", "")}')
        return result

if __name__ == '__main__':
    import sys
    ver = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    path = sys.argv[2] if len(sys.argv) > 2 else 'examples/release_dev.md'
    update = sys.argv[3] if len(sys.argv) > 3 else 'true'
    publish(ver, path, update_existing=(update.lower() == 'true'))
