#!/usr/bin/env python3
"""Debug environment variable loading."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

def check_env_file():
    """Check if .env file exists and what's in it."""
    env_file = Path('.env')
    print(f"🔍 Checking .env file: {env_file.absolute()}")
    
    if env_file.exists():
        print("✅ .env file exists")
        print("📄 Contents:")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'CONFLUENCE' in line:
                    print(f"  {i:2d}: {line.strip()}")
                else:
                    print(f"  {i:2d}: {line.strip()}")
    else:
        print("❌ .env file not found")

def check_python_dotenv():
    """Check if python-dotenv is working."""
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        # Try loading .env
        result = load_dotenv()
        print(f"✅ load_dotenv() result: {result}")
        
        # Check specific variables
        confluence_vars = ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN']
        for var in confluence_vars:
            value = os.getenv(var)
            print(f"   {var}: {'SET' if value else 'NOT SET'}")
            if value:
                # Show first/last few chars for security
                if len(value) > 10:
                    masked = value[:5] + "..." + value[-5:]
                else:
                    masked = "***"
                print(f"     Value: {masked}")
                
    except ImportError:
        print("❌ python-dotenv not available")

def check_utils_import():
    """Check if our utils module loads env correctly."""
    try:
        from src.utils import env
        print("✅ utils.env imported successfully")
        
        confluence_vars = ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN']
        for var in confluence_vars:
            value = env(var)
            print(f"   utils.env('{var}'): {'SET' if value else 'NOT SET'}")
            
    except Exception as e:
        print(f"❌ utils import failed: {e}")

if __name__ == '__main__':
    print("🔧 ENVIRONMENT DEBUG REPORT")
    print("=" * 40)
    
    check_env_file()
    print()
    check_python_dotenv()
    print()
    check_utils_import()