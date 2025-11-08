"""Fallback LLM options when OpenRouter fails."""

from typing import Dict, List
import json
import subprocess
import requests


def get_fallback_models() -> List[Dict]:
    """Get fallback LLM options when OpenRouter is not available."""
    fallback_models = []
    
    # Check for local Ollama
    if check_ollama_available():
        ollama_models = get_ollama_models()
        fallback_models.extend(ollama_models)
    
    # Add basic template-based option
    fallback_models.append({
        'id': 'template-basic',
        'name': 'Template-Based (No AI)',
        'pricing': 'Free',
        'description': 'Generate release notes using templates without AI'
    })
    
    return fallback_models


def check_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False


def get_ollama_models() -> List[Dict]:
    """Get available Ollama models."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model in data.get('models', []):
                models.append({
                    'id': f"ollama/{model['name']}",
                    'name': f"Ollama: {model['name'].title()}",
                    'pricing': 'Local/Free',
                    'description': 'Local Ollama model'
                })
            
            return models
    except:
        pass
    
    return []


def generate_with_template(version: str, commits: List[Dict], issues: List[Dict], audience: str) -> str:
    """Generate release notes using templates when no AI is available."""
    
    template = f"""# Release {version}

## Highlights
- {len(commits)} commits included in this release
- {len(issues)} issues addressed
- Focused on {audience} experience

## What's New
"""
    
    # Add commit summaries
    for i, commit in enumerate(commits[:5]):  # Top 5 commits
        subject = commit.get('subject', 'Update')
        template += f"- {subject}\n"
    
    template += "\n## Bug Fixes\n"
    
    # Add issue summaries
    for i, issue in enumerate(issues[:5]):  # Top 5 issues
        title = issue.get('title', 'Bug fix')
        number = issue.get('number', '')
        if number:
            template += f"- {title} (#{number})\n"
        else:
            template += f"- {title}\n"
    
    template += f"""
## Technical Details
- Total commits: {len(commits)}
- Issues resolved: {len(issues)}
- Target audience: {audience.title()}

## Installation
Please refer to the installation documentation for upgrade instructions.

---
*Generated with Release Notes Generator*
"""
    
    return template


def generate_with_ollama(model: str, prompt: str) -> str:
    """Generate with local Ollama model."""
    try:
        model_name = model.replace('ollama/', '')
        
        payload = {
            'model': model_name,
            'prompt': prompt,
            'stream': False
        }
        
        response = requests.post('http://localhost:11434/api/generate', 
                               json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json().get('response', 'Generation failed')
        else:
            return f"Ollama error: {response.status_code}"
            
    except Exception as e:
        return f"Ollama generation failed: {e}"