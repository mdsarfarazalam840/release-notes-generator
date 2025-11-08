#!/usr/bin/env python3
"""
Setup script for enhanced release notes generator environment.
"""

import os
import sys
from pathlib import Path
import yaml


def create_env_file():
    """Create .env file with template values."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    # Read example file if it exists
    if env_example.exists():
        content = env_example.read_text()
    else:
        # Create basic template
        content = """# GitHub Integration
GITHUB_TOKEN=your_github_token_here

# LLM API Keys (choose one or more)
OPENROUTER_API_KEY=your_openrouter_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# JIRA Integration (optional)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PROJ

# Confluence Publishing (optional)
CONFLUENCE_BASE=https://yourcompany.atlassian.net
CONFLUENCE_USER=your_email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# Slack Publishing (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email Publishing (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENTS=user1@company.com,user2@company.com

# Custom Webhook (optional)
CUSTOM_WEBHOOK_URL=https://your-webhook-endpoint.com/release-notes
WEBHOOK_AUTH_TOKEN=your_webhook_auth_token

# Local LLM (optional)
LOCAL_LLM_BASE_URL=http://localhost:11434
"""
    
    env_file.write_text(content)
    print(f"✅ Created {env_file}")
    print("📝 Please edit .env with your actual API keys and configuration")


def create_config_file():
    """Create config.yaml file with enhanced settings."""
    config_file = Path('config.yaml')
    
    if config_file.exists():
        print("📄 config.yaml already exists")
        return
    
    config = {
        'repo': 'your-username/your-repository',
        'batch_size': 200,
        'llm': {
            'model': 'gpt-4',
            'temperature': 0.0
        },
        'publish': {
            'confluence_space': 'DOCS',
            'confluence_parent_page_id': None
        },
        'data_sources': {
            'commits': {
                'default_source': 'auto',
                'github_fallback_to_local': True
            },
            'issues': {
                'default_source': 'github',
                'include_pull_requests': True
            },
            'releases': {
                'default_source': 'auto',
                'max_previous': 3
            }
        },
        'audiences': {
            'users': {
                'template': 'prompt_users.md',
                'sections': ['highlights', 'new_features', 'improvements', 'bug_fixes', 'known_issues']
            },
            'developers': {
                'template': 'prompt_developers.md',
                'sections': ['highlights', 'new_features', 'api_changes', 'bug_fixes', 'breaking_changes', 'technical_improvements', 'dependencies']
            },
            'managers': {
                'template': 'prompt_managers.md', 
                'sections': ['executive_summary', 'key_features', 'business_impact', 'improvements', 'known_limitations']
            }
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Created {config_file}")
    print("📝 Please edit config.yaml with your repository and preferences")


def create_directories():
    """Create necessary directories."""
    directories = [
        'examples',
        'templates', 
        'uploads',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")


def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install Python dependencies."""
    requirements_file = Path('requirements.txt')
    
    if not requirements_file.exists():
        # Create basic requirements
        requirements = """flask>=2.0.0
requests>=2.25.0
openai>=1.0.0
pyyaml>=6.0.0
python-dotenv>=0.19.0
anthropic>=0.3.0
markdown>=3.4.0
jira>=3.4.0
"""
        requirements_file.write_text(requirements)
        print("📦 Created requirements.txt")
    
    print("📦 Installing Python dependencies...")
    import subprocess
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    return True


def setup_frontend():
    """Set up frontend dependencies."""
    frontend_dir = Path('frontend')
    
    if not frontend_dir.exists():
        print("⚠️ Frontend directory not found - skipping frontend setup")
        return
    
    package_json = frontend_dir / 'package.json'
    if not package_json.exists():
        print("⚠️ package.json not found - skipping frontend setup")
        return
    
    print("📦 Installing frontend dependencies...")
    import subprocess
    
    try:
        subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True, capture_output=True)
        print("✅ Frontend dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install frontend dependencies: {e}")
        print("💡 Make sure Node.js and npm are installed")
        return False
    except FileNotFoundError:
        print("❌ npm not found - please install Node.js")
        return False
    
    return True


def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Enhanced Release Notes Generator Setup Complete!")
    print("=" * 55)
    
    print("\n📝 Next Steps:")
    print("1. Edit .env file with your API keys:")
    print("   - GITHUB_TOKEN for GitHub integration")
    print("   - OPENROUTER_API_KEY or OPENAI_API_KEY for LLM")
    print("   - JIRA_* variables for JIRA integration (optional)")
    print("   - CONFLUENCE_* variables for publishing (optional)")
    
    print("\n2. Edit config.yaml with your repository and preferences")
    
    print("\n3. Start the application:")
    print("   python run_enhanced_server.py")
    
    print("\n4. Access the application:")
    print("   - Backend API: http://localhost:5000")
    print("   - Frontend UI: http://localhost:5173 (if frontend is set up)")
    
    print("\n🔧 Command Line Usage:")
    print("   python -m src.enhanced_generate_notes --version v1.2.3")
    print("   python -m src.enhanced_generate_notes --help")
    
    print("\n📚 Documentation:")
    print("   - README.md for detailed setup instructions")
    print("   - templates/ directory for customizing output")


def main():
    """Main setup function."""
    print("🔧 Enhanced Release Notes Generator - Setup")
    print("=" * 45)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create necessary files and directories
    create_directories()
    create_env_file()
    create_config_file()
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️ Some dependencies failed to install - you may need to install them manually")
    
    # Setup frontend (optional)
    setup_frontend()
    
    # Show next steps
    show_next_steps()


if __name__ == '__main__':
    main()