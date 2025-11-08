"""Direct Confluence publishing fix with environment variables."""
import requests
import re
import os
from dotenv import load_dotenv

def publish_to_confluence_fixed(version: str, md_path: str, update_existing: bool = False):
    """Fixed Confluence publishing function using environment variables."""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    BASE = os.getenv('CONFLUENCE_BASE', 'https://yourcompany.atlassian.net')
    USER = os.getenv('CONFLUENCE_USER', 'you@example.com')
    TOKEN = os.getenv('CONFLUENCE_API_TOKEN', 'your_confluence_api_token_here')
    SPACE = os.getenv('CONFLUENCE_SPACE', 'MFS')
    
    print(f"Publishing to Confluence: {version}")
    print(f"Base URL: {BASE}")
    print(f"Space: {SPACE}")
    print(f"User: {USER}")
    
    # Read markdown file
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()
    
    title = f'Release Notes - {version}'
    
    # Convert markdown to Confluence storage format
    def md_to_storage_format(md_content: str, page_title: str) -> dict:
        """Convert markdown to Confluence storage format."""
        html = md_content
        
        # This will be handled by the calling function - don't add it here
        # The AI model info will be added before this function is called
        
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
        
        # Convert code blocks
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        return {
            'type': 'page',
            'title': page_title,
            'space': {'key': SPACE},
            'body': {
                'storage': {
                    'value': html,
                    'representation': 'storage'
                }
            }
        }
    
    # Check if page already exists
    def find_existing_page(space: str, page_title: str):
        """Find existing page by title."""
        url = f'{BASE}/wiki/rest/api/content'
        params = {
            'spaceKey': space,
            'title': page_title,
            'expand': 'version'
        }
        
        try:
            r = requests.get(url, auth=(USER, TOKEN), params=params)
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    return results[0].get('id')
        except Exception as e:
            print(f"Error checking existing page: {e}")
        
        return None
    
    # Always create new page - never update existing ones
    # Each version should get its own page
    print(f"Creating new page for version: {version}")
    
    # Check if a page with this exact title already exists
    existing_id = find_existing_page(SPACE, title)
    
    if existing_id and not update_existing:
        # If page exists and we don't want to update, create with unique title
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        title = f'Release Notes - {version} ({timestamp})'
        print(f"Page exists, creating with unique title: {title}")
    
    # Create new page
    payload = md_to_storage_format(md, title)
    
    url = f'{BASE}/wiki/rest/api/content'
    r = requests.post(url, auth=(USER, TOKEN), json=payload)
    r.raise_for_status()
    result = r.json()
    
    full_url = BASE + result.get('_links', {}).get('webui', '')
    print(f'Published new page to Confluence: {full_url}')
    return result


if __name__ == '__main__':
    # Test the fixed function
    import sys
    if len(sys.argv) > 2:
        version = sys.argv[1]
        md_path = sys.argv[2]
        result = publish_to_confluence_fixed(version, md_path)
        print(f"Success! Page ID: {result.get('id')}")
    else:
        print("Usage: python confluence_fix.py <version> <md_file>")