import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

base_url = os.getenv('CONFLUENCE_BASE', 'https://yourcompany.atlassian.net')
username = os.getenv('CONFLUENCE_USER', 'you@example.com')
api_token = os.getenv('CONFLUENCE_API_TOKEN', 'your_confluence_api_token_here')

# Test different endpoint variations to find what works
test_endpoints = [
    "/wiki/rest/api/content",      # What we're currently using (fails)
    "/rest/api/content",           # Alternative
    "/wiki/api/v2/pages",          # V2 API
    "/api/v2/pages"                # V2 without wiki prefix
]

headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

print("Testing which endpoint works for POST (content creation)...")
for endpoint in test_endpoints:
    test_url = base_url + endpoint
    print(f"\nTesting: {test_url}")
    
    # Simple test payload
    test_page = {
        'type': 'page',
        'title': f'API Test - {endpoint.replace("/", "-")}',
        'space': {'key': 'MFS'},
        'body': {
            'storage': {
                'value': f'<p>Testing endpoint: {endpoint}</p>',
                'representation': 'storage'
            }
        }
    }
    
    try:
        response = requests.post(test_url, auth=(username, api_token), headers=headers, json=test_page, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"✅ SUCCESS! This endpoint works: {endpoint}")
            result = response.json()
            print(f"Created page ID: {result.get('id')}")
            print(f"Page URL: {base_url + result.get('_links', {}).get('webui', '')}")
            break
        elif response.status_code == 404:
            print("❌ 404 - Not found")
        else:
            print(f"❌ Failed with {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\nDone testing endpoints")
