#!/usr/bin/env python3
"""Test the nuclear GitHub fix"""

import requests
import json
import time

def test_nuclear():
    print("☢️  TESTING NUCLEAR GITHUB FIX")
    print("=" * 50)
    
    time.sleep(2)
    
    url = 'http://localhost:5000/api/generate/enhanced'
    data = {
        'version': 'v1.0.0-nuclear-test',
        'model': 'template-basic',
        'commit_source': 'github'
    }
    
    print("🚨 Making request with nuclear fix active...")
    print("   Watch for 'NUCLEAR INTERCEPT' messages above")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"\n📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 NUCLEAR FIX SUCCESS!")
            print("✅ Frontend should now work without 401 errors")
            return True
        else:
            print(f"💥 Nuclear fix failed: {response.text}")
            return False
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

if __name__ == '__main__':
    test_nuclear()