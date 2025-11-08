"""Test backend API endpoints"""
import time
import requests
import json

print("=== Testing Backend API ===\n")

# Wait for server to start
print("Waiting for backend to start...")
time.sleep(5)

base_url = "http://localhost:5000"

# Test 1: Config endpoint
print("\n[1/4] Testing /api/config...")
try:
    response = requests.get(f"{base_url}/api/config", timeout=5)
    if response.status_code == 200:
        config = response.json()
        print(f"[OK] Config endpoint working!")
        print(f"  - Repo: {config.get('repo')}")
        print(f"  - GitHub Token: {'SET' if config.get('has_github_token') else 'NOT SET'}")
        print(f"  - LLM Model: {config.get('llm_model')}")
    else:
        print(f"[FAIL] Config endpoint returned status {response.status_code}")
except Exception as e:
    print(f"[FAIL] Config endpoint failed: {e}")
    exit(1)

# Test 2: Releases endpoint
print("\n[2/4] Testing /api/releases...")
try:
    response = requests.get(f"{base_url}/api/releases", timeout=5)
    if response.status_code == 200:
        releases = response.json()
        count = len(releases.get('releases', []))
        print(f"[OK] Releases endpoint working!")
        print(f"  - Found {count} releases")
        if count > 0:
            print(f"  - Latest: {releases['releases'][0].get('tag_name')}")
    else:
        print(f"[FAIL] Releases endpoint returned status {response.status_code}")
except Exception as e:
    print(f"[FAIL] Releases endpoint failed: {e}")

# Test 3: Generate endpoint
print("\n[3/4] Testing /api/generate...")
version = "v1.2.8"
generate_data = {
    "version": version,
    "audience": "users",
    "use_github": True,
    "repo": config.get('repo')
}

try:
    response = requests.post(
        f"{base_url}/api/generate",
        json=generate_data,
        timeout=120
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'ok':
            print(f"[OK] Generation successful!")
            print(f"  - Version: {result.get('version')}")
            print(f"  - New releases count: {len(result.get('releases', []))}")
        else:
            print(f"[FAIL] Generation failed: {result.get('message')}")
    else:
        print(f"[FAIL] Generate endpoint returned status {response.status_code}")
        try:
            error = response.json()
            print(f"  Error: {error.get('error', error.get('message', 'Unknown error'))}")
        except:
            print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ Generate endpoint failed: {e}")

# Test 4: Verify file exists
print("\n[4/4] Verifying generated file...")
import os
release_file = f"examples/release_{version}.md"
if os.path.exists(release_file):
    with open(release_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"[OK] Release file created: {release_file}")
    print(f"  - Size: {len(content)} characters")
    print(f"  - Preview: {content[:100]}...")
else:
    print(f"[FAIL] Release file not found: {release_file}")

print("\n=== Test Complete ===")

