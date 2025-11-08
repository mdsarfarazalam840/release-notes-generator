#!/usr/bin/env python3
"""
Test the frontend fix - run this to verify it's working
"""
import requests
import json
import time

def test_frontend_fix():
    print("🧪 Testing Frontend GitHub Fix")
    print("=" * 50)
    
    # Wait for server
    time.sleep(2)
    
    # Test the exact API call the frontend makes
    url = 'http://localhost:5000/api/generate/enhanced'
    payload = {
        'version': 'v1.0.0-frontend-working',
        'model': 'template-basic',  # Use template to avoid LLM issues
        'commit_source': 'github',
        'audience': 'users'
    }
    
    print(f"📡 Testing: POST {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print("\n⏳ Making request...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n🎉 SUCCESS! Frontend GitHub API is now working!")
            print("=" * 50)
            print(f"✅ Version: {result.get('version')}")
            print(f"✅ Commits Count: {result.get('data_summary', {}).get('commits_count', 0)}")
            print(f"✅ Output File: {result.get('output_file')}")
            print("\n🚀 Go to http://localhost:5174 and test the UI!")
            return True
        else:
            print(f"\n❌ Still failing with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', response.text)}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = test_frontend_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ FRONTEND IS FIXED!")
        print("🎯 Your UI at http://localhost:5174 should now work")
        print("📝 Try generating release notes in the web interface")
    else:
        print("❌ Frontend still has issues")
        print("🔄 Use the working command line: python generate_release_notes.py --version v1.0.0 --use-github")
    print("=" * 50)