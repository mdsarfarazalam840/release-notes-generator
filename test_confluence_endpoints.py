import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

base_url = os.getenv('CONFLUENCE_BASE', 'https://yourcompany.atlassian.net')
username = os.getenv('CONFLUENCE_USER', 'you@example.com')
api_token = os.getenv('CONFLUENCE_API_TOKEN', 'your_confluence_api_token_here')

# Test various Confluence Cloud API endpoints
test_endpoints = [
    "/wiki/rest/api/content",
    "/wiki/api/v2/pages", 
    "/rest/api/content",
    "/api/v2/pages"
]

headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

print("Testing Confluence Cloud API endpoints...")
for endpoint in test_endpoints:
    try:
        url = base_url + endpoint
        print(f"\nTesting: {url}")
        
        # Test GET first
        response = requests.get(url, auth=(username, api_token), headers=headers, timeout=10)
        print(f"GET Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ This endpoint works for GET!")
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Test with space parameter
            params = {'spaceKey': 'MFS', 'limit': 1}
            space_response = requests.get(url, auth=(username, api_token), headers=headers, params=params, timeout=10)
            print(f"With space MFS: {space_response.status_code}")
            
            if space_response.status_code == 200:
                space_data = space_response.json()
                print(f"Space data keys: {list(space_data.keys())}")
                if 'results' in space_data:
                    print(f"Found {len(space_data['results'])} items in MFS space")
                    for item in space_data['results'][:2]:
                        print(f"  - {item.get('title', 'No title')}")
            break
        elif response.status_code == 404:
            print("❌ 404 - Endpoint not found")
        else:
            print(f"❌ {response.status_code} - {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*50)
print("Testing Confluence Cloud v2 API specifically...")

# Test the new v2 API which might be the correct one for Confluence Cloud
try:
    v2_url = base_url + "/wiki/api/v2/pages"
    print(f"Testing v2 API: {v2_url}")
    
    response = requests.get(v2_url, auth=(username, api_token), headers=headers, timeout=10)
    print(f"V2 API Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ V2 API works!")
        data = response.json()
        print(f"V2 Response: {list(data.keys())}")
    else:
        print(f"V2 API failed: {response.status_code}")
        print(response.text[:200])
        
except Exception as e:
    print(f"V2 API Error: {e}")
