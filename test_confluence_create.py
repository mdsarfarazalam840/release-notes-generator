import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

base_url = os.getenv('CONFLUENCE_BASE', 'https://yourcompany.atlassian.net')
username = os.getenv('CONFLUENCE_USER', 'you@example.com')
api_token = os.getenv('CONFLUENCE_API_TOKEN', 'your_confluence_api_token_here')

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Create a simple test page
test_page = {
    'type': 'page',
    'title': 'Release Notes - TEST PAGE v2.8.0',
    'space': {'key': 'MFS'},
    'body': {
        'storage': {
            'value': '<h1>Test Release Notes</h1><p>This is a test page created via API.</p><ul><li>Feature 1</li><li>Feature 2</li></ul>',
            'representation': 'storage'
        }
    }
}

print("Testing page creation...")
print(f"Space: MFS (My first space)")
print(f"Title: {test_page['title']}")

try:
    url = base_url + "/wiki/rest/api/content"
    print(f"POST URL: {url}")
    
    response = requests.post(url, auth=(username, api_token), headers=headers, json=test_page, timeout=15)
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print("✅ SUCCESS! Page created!")
        print(f"Page ID: {result.get('id')}")
        print(f"Title: {result.get('title')}")
        if '_links' in result and 'webui' in result['_links']:
            full_url = base_url + result['_links']['webui']
            print(f"🔗 View at: {full_url}")
        else:
            print(f"Page created but no URL in response")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Response: {response.text}")
        
        # Try to parse error details
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print("Could not parse error response as JSON")
            
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "="*50)
print("Checking current permissions and space access...")

try:
    # Check what permissions we have
    user_url = base_url + "/wiki/rest/api/user/current"
    user_response = requests.get(user_url, auth=(username, api_token), headers=headers)
    print(f"User API Status: {user_response.status_code}")
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"Current user: {user_data.get('displayName')} ({user_data.get('email')})")
        
    # Check space permissions
    space_url = base_url + "/wiki/rest/api/space/MFS"
    space_response = requests.get(space_url, auth=(username, api_token), headers=headers)
    print(f"Space API Status: {space_response.status_code}")
    
    if space_response.status_code == 200:
        space_data = space_response.json()
        print(f"Space: {space_data.get('name')} (Key: {space_data.get('key')})")
        print(f"Space type: {space_data.get('type')}")
        
except Exception as e:
    print(f"Permission check failed: {e}")
