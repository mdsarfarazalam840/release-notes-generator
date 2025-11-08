"""Enhanced API endpoints for realistic UI features."""
import requests
import subprocess
import re
import os
from pathlib import Path
from typing import List, Dict, Optional
from flask import jsonify, request
import json

from src.utils import env, load_config
from src.fallback_llm import get_fallback_models


def add_enhanced_endpoints(app):
    """Add enhanced endpoints to the Flask app."""
    
    @app.route('/api/models/openrouter', methods=['GET'])
    def get_openrouter_models():
        """Fetch available models from OpenRouter API based on user's access."""
        api_key = env('OPENROUTER_API_KEY')
        
        if not api_key:
            fallback_models = get_fallback_models()
            # Always include template-based as first option
            all_models = [
                {'id': 'template-basic', 'name': 'Template-Based (No AI)', 'pricing': 'FREE'},
            ] + fallback_models
            return jsonify({
                'models': all_models,
                'source': 'fallback',
                'message': 'OpenRouter not configured. Using fallback options.'
            })
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
            response.raise_for_status()
            
            models_data = response.json()
            
            # Filter and format models - prioritize free and commonly used models
            available_models = []
            
            # Actually free models (no credits required) - updated list
            free_models = [
                'meta-llama/llama-3.1-8b-instruct:free',
                'google/gemma-2-9b-it:free', 
                'microsoft/phi-3-mini-128k-instruct:free',
                'huggingfaceh4/zephyr-7b-beta:free',
                'qwen/qwen-2-7b-instruct:free',
                'minimax/minimax-m2:free',
                'nousresearch/nous-capybara-7b:free',
                'openchat/openchat-7b:free'
            ]
            
            # Premium models
            premium_models = [
                'openai/gpt-4o',
                'anthropic/claude-3.5-sonnet',
                'google/gemini-pro-1.5',
                'meta-llama/llama-3.1-70b-instruct',
                'microsoft/wizardlm-2-8x22b'
            ]
            
            all_models = models_data.get('data', [])
            
            # Add free models - check both by ID and pricing
            for model_info in all_models:
                model_id = model_info.get('id', '')
                model_name = model_info.get('name', model_id)
                
                # Check if it's a free model by ID pattern or pricing
                is_free = (
                    model_id in free_models or 
                    ':free' in model_id or
                    model_info.get('pricing', {}).get('prompt', 0) == 0 or
                    'free' in model_name.lower()
                )
                
                if is_free:
                    available_models.append({
                        'id': model_id,
                        'name': format_model_name(model_name),
                        'pricing': 'Free',
                        'context_length': model_info.get('context_length', 'Unknown')
                    })
            
            # Add premium models
            for model_id in premium_models:
                model_info = next((m for m in all_models if m.get('id') == model_id), None)
                if model_info:
                    available_models.append({
                        'id': model_id,
                        'name': format_model_name(model_info.get('name', model_id)),
                        'pricing': 'Premium',
                        'context_length': model_info.get('context_length', 'Unknown')
                    })
            
            # Always include template-based first, then found models
            all_models = [
                {'id': 'template-basic', 'name': 'Template-Based (No AI)', 'pricing': 'FREE'},
            ]
            
            # Add found models or fallbacks  
            if available_models:
                all_models.extend(available_models)
            else:
                # Add working fallback models if OpenRouter fails
                all_models.extend([
                    {'id': 'meta-llama/llama-3.1-8b-instruct:free', 'name': 'LLaMA 3.1 8B', 'pricing': 'Free'},
                    {'id': 'minimax/minimax-m2:free', 'name': 'MiniMax M2', 'pricing': 'Free'},
                    {'id': 'google/gemma-2-9b-it:free', 'name': 'Gemma 2 9B', 'pricing': 'Free'}
                ])
                fallback_models = get_fallback_models()
                all_models.extend(fallback_models)
            
            available_models = all_models
            
            return jsonify({
                'models': available_models,
                'total_available': len(all_models)
            })
            
        except requests.RequestException as e:
            fallback_models = get_fallback_models()
            all_models = [
                {'id': 'template-basic', 'name': 'Template-Based (No AI)', 'pricing': 'FREE'},
            ] + fallback_models
            return jsonify({
                'models': all_models,
                'source': 'fallback',
                'error': f'OpenRouter failed: {str(e)}. Using fallback options.'
            })

    @app.route('/api/versions', methods=['GET'])
    def get_available_versions():
        """Get available versions from GitHub or local git."""
        config = load_config()
        repo = config.get('repo', '')
        github_token = env('GITHUB_TOKEN')
        
        versions = []
        suggested_next = None
        
        try:
            if github_token and repo:
                # Try GitHub API first
                print(f"Trying GitHub API for repo: {repo}")
                versions, suggested_next = get_github_versions(repo, github_token)
                print(f"GitHub API returned {len(versions)} versions")
            
            if not versions:
                # Fallback to local git
                print("Falling back to local git")
                versions, suggested_next = get_local_versions()
                print(f"Local git returned {len(versions)} versions")
            
            # If still no versions, create some default suggestions
            if not versions:
                print("No versions found, creating defaults")
                versions = [
                    {'tag': 'v1.0.0', 'name': 'v1.0.0', 'type': 'suggested'},
                    {'tag': 'v0.1.0', 'name': 'v0.1.0', 'type': 'suggested'}
                ]
                suggested_next = "v1.0.0"
                
        except Exception as e:
            print(f"Error fetching versions: {e}")
            # Return default suggestions
            versions = [
                {'tag': 'v1.0.0', 'name': 'v1.0.0', 'type': 'suggested'},
                {'tag': 'v0.1.0', 'name': 'v0.1.0', 'type': 'suggested'}
            ]
            suggested_next = "v1.0.0"
        
        return jsonify({
            'versions': versions,
            'suggested_next': suggested_next,
            'source': 'github' if github_token and repo else 'local'
        })

    @app.route('/api/confluence/test', methods=['POST'])
    def test_confluence_connection():
        """Test Confluence connection."""
        # Force reload environment variables (.env first, then .env.local overrides)
        from dotenv import load_dotenv
        load_dotenv(override=True)
        load_dotenv('.env.local', override=True)
        
        # Use os.getenv directly to ensure fresh values
        base_url = os.getenv('CONFLUENCE_BASE')
        username = os.getenv('CONFLUENCE_USER')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        print(f"CONFLUENCE TEST - Raw values:")
        print(f"  Base URL: {base_url}")
        print(f"  Username: {username}")
        print(f"  Token: {'SET' if api_token and not api_token.startswith('your_') else 'NOT SET'}")
        
        # Don't fall back to placeholders - use actual values or fail
        if not all([base_url, username, api_token]) or any(val.startswith('your_') for val in [base_url, username, api_token] if val):
            return jsonify({
                'error': 'Confluence configuration incomplete. Please set CONFLUENCE_BASE, CONFLUENCE_USER, and CONFLUENCE_API_TOKEN in .env.local file'
            }), 400
        
        print(f"CONFLUENCE TEST - Using:")
        print(f"  Base URL: {base_url}")
        print(f"  Username: {username}")
        print(f"  Token: {'SET' if api_token else 'NOT SET'}")
        
        if not all([base_url, username, api_token]):
            return jsonify({
                'error': 'Confluence configuration incomplete. Please set CONFLUENCE_BASE, CONFLUENCE_USER, and CONFLUENCE_API_TOKEN'
            }), 400
        
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            auth = (username, api_token)
            
            # Try multiple API endpoints to find the working one
            test_urls = [
                f"{base_url}/wiki/rest/api/space",  # Confluence Cloud API
                f"{base_url}/rest/api/space",       # Alternative path
                f"{base_url}/wiki/api/v2/spaces"    # V2 API
            ]
            
            response = None
            working_url = None
            
            for test_url in test_urls:
                try:
                    print(f"Testing Confluence URL: {test_url}")
                    response = requests.get(test_url, headers=headers, auth=auth, timeout=10)
                    if response.status_code == 200:
                        working_url = test_url
                        break
                    elif response.status_code == 404:
                        print(f"404 for {test_url}")
                        continue
                    else:
                        print(f"Status {response.status_code} for {test_url}")
                except requests.RequestException as e:
                    print(f"Request failed for {test_url}: {e}")
                    continue
            
            if not response or response.status_code != 200:
                # If all space endpoints fail, try a basic auth test
                auth_test_url = f"{base_url}/wiki/rest/api/user/current"
                print(f"Trying auth test: {auth_test_url}")
                response = requests.get(auth_test_url, headers=headers, auth=auth, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle different API response formats
                if working_url and 'space' in working_url:
                    # Space API response
                    spaces = response_data.get('results', [])
                    space_count = len(spaces)
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Connected successfully! Found {space_count} spaces.',
                        'spaces': space_count,
                        'api_url': working_url
                    })
                else:
                    # User API response (auth test)
                    user_info = response_data
                    return jsonify({
                        'status': 'success', 
                        'message': f'Authentication successful! Connected as {user_info.get("displayName", "User")}',
                        'user': user_info.get('displayName', 'Unknown'),
                        'api_url': auth_test_url
                    })
            else:
                response.raise_for_status()
            
        except requests.RequestException as e:
            return jsonify({
                'error': f'Connection failed: {str(e)}'
            }), 500

    @app.route('/api/confluence/setup', methods=['GET'])
    def get_confluence_setup_info():
        """Get Confluence setup information and instructions."""
        base_url = env('CONFLUENCE_BASE')
        username = env('CONFLUENCE_USER')
        api_token = env('CONFLUENCE_API_TOKEN')
        
        return jsonify({
            'configured': bool(base_url and username and api_token),
            'base_url': base_url or '',
            'username': username or '',
            'has_token': bool(api_token),
            'setup_instructions': {
                'step1': 'Go to your Atlassian account settings',
                'step2': 'Create an API token in Security > API tokens',
                'step3': 'Set environment variables: CONFLUENCE_BASE, CONFLUENCE_USER, CONFLUENCE_API_TOKEN',
                'example_base_url': 'https://yourcompany.atlassian.net'
            }
        })


def format_model_name(name: str) -> str:
    """Format model name for better display."""
    # Remove common prefixes and make more readable
    name = name.replace('openai/', '').replace('meta-llama/', '').replace('google/', '')
    name = name.replace('anthropic/', '').replace('microsoft/', '')
    
    # Capitalize and clean up
    name = re.sub(r'[-_]', ' ', name)
    name = re.sub(r'\b\w+\b', lambda m: m.group(0).title(), name)
    
    # Fix common names
    replacements = {
        'Gpt': 'GPT',
        'Llama': 'LLaMA',
        'Phi': 'Phi',
        'Wizardlm': 'WizardLM',
        'Gemma': 'Gemma',
        'Claude': 'Claude'
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    return name


def get_github_versions(repo: str, token: str) -> tuple[List[Dict], Optional[str]]:
    """Get versions from GitHub releases and tags."""
    # Use provided token; do not override with any hardcoded token
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    versions = []
    
    try:
        # Get releases
        releases_url = f'https://api.github.com/repos/{repo}/releases'
        response = requests.get(releases_url, headers=headers, params={'per_page': 20})
        response.raise_for_status()
        
        releases = response.json()
        
        for release in releases[:10]:  # Last 10 releases
            versions.append({
                'tag': release['tag_name'],
                'name': release['name'] or release['tag_name'],
                'published_at': release['published_at'],
                'type': 'release'
            })
        
        # Also get tags for more options
        tags_url = f'https://api.github.com/repos/{repo}/tags'
        tags_response = requests.get(tags_url, headers=headers, params={'per_page': 20})
        
        if tags_response.status_code == 200:
            tags = tags_response.json()
            
            # Add tags that aren't already in releases
            existing_tags = {v['tag'] for v in versions}
            
            for tag in tags[:15]:  # More tags
                if tag['name'] not in existing_tags:
                    versions.append({
                        'tag': tag['name'],
                        'name': tag['name'],
                        'type': 'tag'
                    })
        
        # Suggest next version
        suggested_next = suggest_next_version([v['tag'] for v in versions])
        
        return versions, suggested_next
        
    except Exception as e:
        print(f"GitHub API error: {e}")
        return [], "v1.0.0"


def get_local_versions() -> tuple[List[Dict], Optional[str]]:
    """Get versions from local git tags."""
    versions = []
    
    try:
        # Get git tags
        print("🔍 Running git command for versions...")
        result = subprocess.run(
            ['git', 'tag', '--sort=-version:refname'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            tags = result.stdout.strip().split('\n')
            tags = [tag for tag in tags if tag.strip()]  # Remove empty lines
            
            for tag in tags[:10]:  # Last 10 tags
                # Get tag date
                date_result = subprocess.run(
                    ['git', 'log', '-1', '--format=%ai', tag],
                    capture_output=True,
                    text=True,
                    cwd='.'
                )
                
                date = date_result.stdout.strip() if date_result.returncode == 0 else ''
                
                versions.append({
                    'tag': tag,
                    'name': tag,
                    'created_at': date,
                    'type': 'tag'
                })
        
        # Suggest next version
        suggested_next = suggest_next_version([v['tag'] for v in versions])
        
        return versions, suggested_next
        
    except Exception as e:
        print(f"Local git error: {e}")
        return [], "v1.0.0"


def suggest_next_version(existing_versions: List[str]) -> str:
    """Suggest the next version based on existing versions."""
    if not existing_versions:
        return "v1.0.0"
    
    # Parse semantic versions
    version_numbers = []
    
    for version in existing_versions:
        # Remove 'v' prefix if present
        clean_version = version.lstrip('v')
        
        # Try to parse semantic version
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)', clean_version)
        if match:
            major, minor, patch = map(int, match.groups())
            version_numbers.append((major, minor, patch))
    
    if not version_numbers:
        return "v1.0.0"
    
    # Get latest version
    latest = max(version_numbers)
    major, minor, patch = latest
    
    # Suggest patch increment
    return f"v{major}.{minor}.{patch + 1}"