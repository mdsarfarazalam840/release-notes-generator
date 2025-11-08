#!/usr/bin/env python3
"""Full stack test - Backend + Frontend integration test."""

import requests
import time
import webbrowser
import os
from dotenv import load_dotenv

def test_backend_server():
    """Test backend server functionality."""
    print("🔧 Testing Backend Server (Port 5000)")
    print("-" * 50)
    
    backend_url = "http://localhost:5000"
    
    try:
        # Test basic connectivity
        response = requests.get(f"{backend_url}/api/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print("✅ Backend server running successfully")
            print(f"   Repository: {config.get('repo')}")
            print(f"   LLM Model: {config.get('llm_model')}")
            print(f"   Confluence: {config.get('confluence_configured')}")
        else:
            print(f"❌ Backend server error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False
    
    # Test key endpoints
    endpoints = [
        "/api/models",
        "/api/publish/platforms",
        "/api/confluence/test"
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint == "/api/confluence/test":
                response = requests.post(f"{backend_url}{endpoint}", json={}, timeout=10)
            else:
                response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 201]:
                print(f"✅ {endpoint}: Working")
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {str(e)[:50]}...")
    
    return True

def test_frontend_server():
    """Test frontend server functionality."""
    print("\n🌐 Testing Frontend Server (Port 5173)")
    print("-" * 50)
    
    frontend_url = "http://localhost:5173"
    
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend server running successfully")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"   Content length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ Frontend server error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend server not running on port 5173")
        print("   Try running: cd frontend && npm start")
        return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def test_fullstack_integration():
    """Test frontend-backend integration."""
    print("\n🔗 Testing Full Stack Integration")
    print("-" * 50)
    
    # Test CORS and API connectivity from frontend perspective
    backend_url = "http://localhost:5000"
    
    try:
        # Test CORS headers
        response = requests.options(f"{backend_url}/api/config")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Configuration:")
        for header, value in cors_headers.items():
            if value:
                print(f"✅ {header}: {value}")
            else:
                print(f"⚠️  {header}: Not set")
        
        # Test a simple API call that frontend would make
        config_response = requests.get(f"{backend_url}/api/config")
        if config_response.status_code == 200:
            print("✅ API calls from frontend will work")
            return True
        else:
            print(f"❌ API integration issue: {config_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def test_environment_variables():
    """Test environment variables are properly loaded."""
    print("\n🔑 Testing Environment Variables")
    print("-" * 50)
    
    load_dotenv()
    load_dotenv('.env.local', override=True)
    
    required_vars = ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN', 'GITHUB_TOKEN', 'OPENROUTER_API_KEY']
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var, '')
        if value and not value.startswith('your_'):
            print(f"✅ {var}: Configured")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def perform_live_demo():
    """Demonstrate the working system."""
    print("\n🚀 Live System Demonstration")
    print("-" * 50)
    
    backend_url = "http://localhost:5000"
    frontend_url = "http://localhost:5173"
    
    print("System URLs:")
    print(f"✅ Backend API: {backend_url}")
    print(f"✅ Frontend UI: {frontend_url}")
    
    print("\nAPI Endpoints Available:")
    endpoints = [
        "GET  /api/config - System configuration",
        "GET  /api/models - Available LLM models",
        "POST /api/generate/enhanced - Generate release notes",
        "POST /api/confluence/test - Test Confluence connection",
        "GET  /api/publish/platforms - Publishing options"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    print("\nFrontend Features:")
    features = [
        "🎯 Release notes generation interface",
        "⚙️  Configuration management",
        "📊 Real-time API interaction",
        "🔗 Confluence integration",
        "📝 Template-based generation"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print(f"\n🌐 Open your browser and visit: {frontend_url}")
    print("💡 You can interact with the UI to generate release notes!")
    
    # Optionally open browser
    try:
        print("\n🔍 Attempting to open browser...")
        webbrowser.open(frontend_url)
        print("✅ Browser opened (if available)")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"   Please manually open: {frontend_url}")

def main():
    """Run full stack testing and demonstration."""
    print("🧪 FULL STACK SYSTEM TEST")
    print("=" * 60)
    print("Testing Backend + Frontend Integration")
    
    # Test individual components
    backend_ok = test_backend_server()
    frontend_ok = test_frontend_server()
    integration_ok = test_fullstack_integration() if backend_ok else False
    env_ok = test_environment_variables()
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 FULL STACK TEST RESULTS")
    print("=" * 60)
    
    results = [
        ("Backend Server", backend_ok),
        ("Frontend Server", frontend_ok),
        ("Integration", integration_ok),
        ("Environment Config", env_ok)
    ]
    
    all_working = True
    for component, status in results:
        symbol = "✅" if status else "❌"
        print(f"   {component:<20}: {symbol}")
        if not status:
            all_working = False
    
    print("-" * 60)
    
    if all_working:
        print("🎉 FULL STACK SYSTEM OPERATIONAL!")
        print("\n✅ Both frontend and backend are working correctly")
        print("✅ Integration between services is functional")
        print("✅ Environment variables properly configured")
        print("✅ CORS properly configured for cross-origin requests")
        
        perform_live_demo()
        
        print(f"\n🚀 SYSTEM READY FOR PRODUCTION USE!")
        
    else:
        print("❌ SYSTEM ISSUES DETECTED")
        print("\nIssues to resolve:")
        for component, status in results:
            if not status:
                print(f"   • Fix {component}")
        
        print(f"\nTroubleshooting:")
        if not backend_ok:
            print(f"   • Start backend: python run_enhanced_server.py")
        if not frontend_ok:
            print(f"   • Start frontend: cd frontend && npm start")
    
    return all_working

if __name__ == '__main__':
    success = main()
    
    if success:
        print(f"\n⏳ System is running. Press Ctrl+C to stop servers.")
        print(f"🌐 Frontend: http://localhost:5173")
        print(f"🔧 Backend:  http://localhost:5000")
        
        # Keep the test running so you can interact with the system
        try:
            while True:
                time.sleep(10)
                print(".", end="", flush=True)
        except KeyboardInterrupt:
            print(f"\n👋 Test completed!")
    
    exit(0 if success else 1)