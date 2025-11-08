#!/usr/bin/env python3
"""
Enhanced server runner with configuration validation and setup assistance.
"""

import os
import sys
import subprocess
from pathlib import Path

# Load environment variables first (.env for defaults, then .env.local overrides)
from dotenv import load_dotenv
load_dotenv()                      # Load defaults
load_dotenv('.env.local', override=True)  # Override with actual credentials

from src.utils import load_config, env
from src.publishing_service import PublishingService
from src.llm_service import list_available_models


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'requests', 'openai', 'yaml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ {package}")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + ' '.join(missing))
        return False
    
    return True


def check_configuration():
    """Check configuration and environment variables."""
    print("\n⚙️ Checking configuration...")
    
    # Load config
    try:
        config = load_config()
        print(f"  ✓ Config file loaded")
        print(f"    Repository: {config.get('repo', 'Not set')}")
        print(f"    LLM model: {config.get('llm', {}).get('model', 'Not set')}")
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False
    
    # Check environment variables
    env_status = {
        'GITHUB_TOKEN': bool(env('GITHUB_TOKEN')),
        'OPENROUTER_API_KEY': bool(env('OPENROUTER_API_KEY')),
        'OPENAI_API_KEY': bool(env('OPENAI_API_KEY')),
        'JIRA_BASE_URL': bool(env('JIRA_BASE_URL')),
        'CONFLUENCE_BASE': bool(env('CONFLUENCE_BASE'))
    }
    
    print("\n🔑 Environment variables:")
    for var, status in env_status.items():
        print(f"  {'✓' if status else '✗'} {var}")
    
    # Check publishing platforms
    service = PublishingService()
    platforms = service.get_platform_status()
    
    print("\n📤 Publishing platforms:")
    for name, info in platforms.items():
        print(f"  {'✓' if info['configured'] else '✗'} {info['name']}")
    
    return True


def check_frontend():
    """Check if frontend is properly set up."""
    print("\n🌐 Checking frontend...")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print("  ✗ Frontend directory not found")
        return False
    
    package_json = frontend_dir / 'package.json'
    if not package_json.exists():
        print("  ✗ package.json not found")
        return False
    
    node_modules = frontend_dir / 'node_modules'
    if not node_modules.exists():
        print("  ⚠️ node_modules not found - run 'npm install' in frontend directory")
        return False
    
    print("  ✓ Frontend appears to be set up")
    return True


def show_startup_info():
    """Show startup information and URLs."""
    print("\n🚀 Enhanced Release Notes Generator")
    print("=" * 50)
    print("Backend API: http://localhost:5000")
    print("Frontend UI: http://localhost:5173")
    print("API Documentation: http://localhost:5000/api/config")
    print("=" * 50)
    
    print("\n📋 Available API Endpoints:")
    endpoints = [
        "GET  /api/config - Get configuration",
        "GET  /api/models - List available LLM models", 
        "GET  /api/data/commits - Fetch commits",
        "GET  /api/data/issues - Fetch issues",
        "GET  /api/data/releases - Fetch previous releases",
        "POST /api/generate/enhanced - Generate release notes",
        "POST /api/upload/issues - Upload JSON issues",
        "GET  /api/publish/platforms - Get publishing platforms",
        "POST /api/publish/confluence - Publish to Confluence"
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")
    
    print("\n🔧 Configuration Tips:")
    print("1. Set GITHUB_TOKEN for GitHub integration")
    print("2. Set OPENROUTER_API_KEY or OPENAI_API_KEY for LLM")
    print("3. Set JIRA_* variables for JIRA integration")
    print("4. Set CONFLUENCE_* variables for publishing")
    print("5. See .env.example for full configuration")


def main():
    """Main function to run enhanced server with checks."""
    print("🔧 Enhanced Release Notes Generator - Server Startup")
    print("=" * 55)
    
    # Run checks
    if not check_dependencies():
        sys.exit(1)
    
    check_configuration()
    check_frontend()
    
    show_startup_info()
    
    print("\n🚀 Starting enhanced server...")
    print("Press Ctrl+C to stop")
    print("-" * 30)
    
    try:
        # Start the server
        from src.server import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()