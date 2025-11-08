"""End-to-end test for release notes generator"""
import requests
import json
import time

print("=" * 60)
print("END-TO-END TEST - Release Notes Generator")
print("=" * 60)

BASE_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:5173"

# Test 1: Backend Config
print("\n[1/6] Testing Backend Config Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/config", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type, f"Expected JSON, got {content_type}"
    data = response.json()
    print(f"  [OK] Status: {response.status_code}")
    print(f"  [OK] Content-Type: {content_type}")
    print(f"  [OK] Repo: {data.get('repo')}")
    print(f"  [OK] GitHub Token: {'SET' if data.get('has_github_token') else 'NOT SET'}")
    print(f"  [OK] LLM Model: {data.get('llm_model')}")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    exit(1)

# Test 2: Releases Endpoint
print("\n[2/6] Testing Releases Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/releases", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type, f"Expected JSON, got {content_type}"
    data = response.json()
    print(f"  [OK] Status: {response.status_code}")
    print(f"  [OK] Content-Type: {content_type}")
    print(f"  [OK] Releases count: {len(data.get('releases', []))}")
    if len(data.get('releases', [])) > 0:
        print(f"  [OK] Latest release: {data['releases'][0].get('tag_name')}")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    exit(1)

# Test 3: Generate Endpoint (JSON format)
print("\n[3/6] Testing Generate Endpoint (JSON Response)...")
version = f"v1.2.9-{int(time.time())}"
payload = {
    "version": version,
    "audience": "users",
    "use_github": True,
    "repo": data.get('repo'),
    "publish_confluence": False
}
try:
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=payload,
        timeout=120,
        headers={'Content-Type': 'application/json'}
    )
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type, f"Expected JSON, got {content_type}"
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    result = response.json()
    print(f"  [OK] Status: {response.status_code}")
    print(f"  [OK] Content-Type: {content_type}")
    print(f"  [OK] Response status: {result.get('status')}")
    print(f"  [OK] Version: {result.get('version')}")
    print(f"  [OK] Releases in response: {len(result.get('releases', []))}")
    print(f"  [OK] Has confluence field: {'confluence' in result}")
    if 'confluence' in result and result['confluence']:
        print(f"  [OK] Confluence link: {result['confluence'].get('_links', {}).get('webui', 'N/A')}")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_data = e.response.json()
            print(f"  Error details: {error_data}")
        except:
            print(f"  Response text: {e.response.text[:200]}")
    exit(1)

# Test 4: Verify Generated File
print("\n[4/6] Verifying Generated File...")
import os
release_file = f"examples/release_{version}.md"
try:
    assert os.path.exists(release_file), f"File not found: {release_file}"
    with open(release_file, 'r', encoding='utf-8') as f:
        content = f.read()
    assert len(content) > 0, "File is empty"
    print(f"  [OK] File exists: {release_file}")
    print(f"  [OK] File size: {len(content)} characters")
    print(f"  [OK] Preview: {content[:80]}...")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    exit(1)

# Test 5: Fetch Generated Release
print("\n[5/6] Testing Fetch Generated Release...")
try:
    response = requests.get(f"{BASE_URL}/api/releases/{version}", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type, f"Expected JSON, got {content_type}"
    release_data = response.json()
    assert 'release' in release_data, "Response missing 'release' key"
    assert 'content' in release_data['release'], "Release missing 'content'"
    print(f"  [OK] Status: {response.status_code}")
    print(f"  [OK] Content-Type: {content_type}")
    print(f"  [OK] Release content length: {len(release_data['release']['content'])}")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    exit(1)

# Test 6: Frontend Accessibility
print("\n[6/6] Testing Frontend Accessibility...")
try:
    response = requests.get(FRONTEND_URL, timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert 'Release Notes Generator' in response.text, "Frontend page not loaded correctly"
    print(f"  [OK] Status: {response.status_code}")
    print(f"  [OK] Frontend page loaded correctly")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")
    exit(1)

print("\n" + "=" * 60)
print("[SUCCESS] ALL TESTS PASSED!")
print("=" * 60)
print("\nSummary:")
print(f"  - Backend: Running on {BASE_URL}")
print(f"  - Frontend: Running on {FRONTEND_URL}")
print(f"  - Generated version: {version}")
print(f"  - All endpoints return valid JSON")
print(f"  - Generated file created and accessible")
print("\nYou can now:")
print(f"  1. Open {FRONTEND_URL} in your browser")
print(f"  2. Click 'Generate Release Notes' to test the UI")
print(f"  3. Verify the generated release appears in the editor")
print(f"  4. Check that no JSON parsing errors occur")

