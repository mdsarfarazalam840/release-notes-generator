#!/usr/bin/env python3
"""
Setup script for Confluence integration.
"""

import os
from pathlib import Path


def setup_confluence():
    """Guide user through Confluence setup."""
    print("🔧 Confluence Integration Setup")
    print("=" * 40)
    
    print("\n📋 What you'll need:")
    print("1. Your Atlassian site URL (e.g., https://yourcompany.atlassian.net)")
    print("2. Your Atlassian email address")
    print("3. An API token (we'll help you create this)")
    
    print("\n🔑 Step 1: Create API Token")
    print("1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Click 'Create API token'")
    print("3. Give it a label like 'Release Notes Generator'")
    print("4. Copy the token (you won't see it again!)")
    
    print("\n📝 Step 2: Configure Environment")
    
    # Get inputs
    base_url = input("\nEnter your Confluence base URL: ").strip()
    if not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    if not base_url.endswith('.atlassian.net') and 'atlassian' not in base_url:
        base_url = f"{base_url}.atlassian.net"
    
    email = input("Enter your Atlassian email: ").strip()
    api_token = input("Enter your API token: ").strip()
    
    # Update .env file
    env_file = Path('.env')
    env_content = ""
    
    if env_file.exists():
        env_content = env_file.read_text()
    
    # Remove existing Confluence config if any
    lines = env_content.split('\n')
    filtered_lines = [
        line for line in lines 
        if not any(line.startswith(prefix) for prefix in [
            'CONFLUENCE_BASE=', 'CONFLUENCE_USER=', 'CONFLUENCE_API_TOKEN='
        ])
    ]
    
    # Add new config
    confluence_config = f"""
# Confluence Configuration
CONFLUENCE_BASE={base_url}
CONFLUENCE_USER={email}
CONFLUENCE_API_TOKEN={api_token}
"""
    
    new_content = '\n'.join(filtered_lines) + confluence_config
    env_file.write_text(new_content)
    
    print(f"\n✅ Configuration saved to {env_file}")
    
    # Test connection
    print("\n🧪 Testing connection...")
    
    try:
        import requests
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (email, api_token)
        test_url = f"{base_url}/rest/api/space"
        
        response = requests.get(test_url, headers=headers, auth=auth, timeout=10)
        
        if response.status_code == 200:
            spaces = response.json()
            space_count = len(spaces.get('results', []))
            print(f"✅ Connection successful! Found {space_count} spaces.")
            
            if space_count > 0:
                print("\n📁 Available spaces:")
                for space in spaces.get('results', [])[:5]:
                    print(f"  • {space.get('name')} ({space.get('key')})")
            
        elif response.status_code == 401:
            print("❌ Authentication failed. Please check your email and API token.")
        elif response.status_code == 403:
            print("❌ Access denied. Make sure you have permission to access Confluence.")
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    print("\n🚀 Setup complete!")
    print("You can now use Confluence publishing in the Release Notes Generator.")
    print("\nTo test the integration:")
    print("1. Start the server: python run_enhanced_server.py")
    print("2. Open http://localhost:5173")
    print("3. Enable 'Publish to Confluence' option")


def show_confluence_info():
    """Show current Confluence configuration status."""
    print("📄 Current Confluence Configuration")
    print("=" * 40)
    
    base_url = os.getenv('CONFLUENCE_BASE')
    user = os.getenv('CONFLUENCE_USER') 
    token = os.getenv('CONFLUENCE_API_TOKEN')
    
    print(f"Base URL: {base_url or 'Not set'}")
    print(f"User: {user or 'Not set'}")
    print(f"API Token: {'Set' if token else 'Not set'}")
    
    if all([base_url, user, token]):
        print("✅ Confluence is configured")
    else:
        print("❌ Confluence is not fully configured")
        print("\nRun: python setup_confluence.py")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        show_confluence_info()
    else:
        setup_confluence()