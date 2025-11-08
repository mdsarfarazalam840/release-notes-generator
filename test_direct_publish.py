import sys
sys.path.append('src')
from publish_to_confluence import publish

try:
    result = publish('v2.6.0-debug', 'test_confluence_debug.md', True)
    if result:
        print('SUCCESS: Published to Confluence!')
        print(f'Page ID: {result.get("id", "Unknown")}')
        print(f'Title: {result.get("title", "Unknown")}')
        if '_links' in result and 'webui' in result['_links']:
            print(f'URL: {result["_links"]["webui"]}')
        else:
            print('URL: Not available in response')
    else:
        print('FAILED: No result returned from publish function')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
