"""Enhanced LLM integration service with multiple providers and prompt customization."""
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import openai
import requests
from src.utils import env, load_config
from src.fallback_llm import generate_with_template, generate_with_ollama


class LLMService:
    """Unified service for LLM integration with multiple providers."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.llm_config = self.config.get('llm', {})
        self.providers = {
            'openai': self._call_openai,
            'openrouter': self._call_openrouter,
            'anthropic': self._call_anthropic,
            'local': self._call_local_llm,
            'ollama': self._call_ollama,
            'template': self._call_template
        }
    
    def detect_provider(self, model: str) -> str:
        """Detect provider based on model name."""
        if model.startswith(('gpt-', 'o1-')):
            return 'openai'
        elif model.startswith('ollama/'):
            return 'ollama'
        elif model.startswith('template-'):
            return 'template'
        elif '/' in model:  # OpenRouter format like "anthropic/claude-3"
            return 'openrouter'
        elif model.startswith('claude-'):
            return 'anthropic'
        else:
            return 'local'
    
    async def generate_release_notes(
        self,
        version: str,
        commits: List[Dict],
        issues: List[Dict],
        audience: str = 'users',
        previous_releases: Optional[List[Dict]] = None,
        template: Optional[str] = None,
        custom_sections: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate structured release notes using LLM."""
        
        # Build the prompt
        prompt = self.build_prompt(
            version=version,
            commits=commits,
            issues=issues,
            audience=audience,
            previous_releases=previous_releases,
            template=template,
            custom_sections=custom_sections
        )
        
        # Call LLM
        model = model or self.llm_config.get('model', 'gpt-4')
        temperature = temperature if temperature is not None else self.llm_config.get('temperature', 0.0)
        
        raw_output = await self.call_llm(prompt, model, temperature)
        
        # Parse and structure the output
        structured_output = self.parse_llm_output(raw_output)
        
        return {
            'raw_output': raw_output,
            'structured': structured_output,
            'metadata': {
                'model': model,
                'temperature': temperature,
                'audience': audience,
                'prompt_length': len(prompt),
                'version': version
            }
        }
    
    def build_prompt(
        self,
        version: str,
        commits: List[Dict],
        issues: List[Dict],
        audience: str = 'users',
        previous_releases: Optional[List[Dict]] = None,
        template: Optional[str] = None,
        custom_sections: Optional[List[str]] = None
    ) -> str:
        """Build customized prompt based on audience and template."""
        
        # Load base template
        if template:
            template_path = Path(f'templates/{template}')
            if template_path.exists():
                base_template = template_path.read_text(encoding='utf-8')
            else:
                base_template = template  # Treat as direct template content
        else:
            # Load audience-specific template
            audience_template = Path(f'templates/prompt_{audience}.md')
            if audience_template.exists():
                base_template = audience_template.read_text(encoding='utf-8')
            else:
                # Fallback to default
                base_template = Path('templates/prompt.md').read_text(encoding='utf-8')
        
        # Prepare data for template
        template_data = {
            'version': version,
            'date': str(datetime.now().date()),
            'commits': self._format_commits_for_prompt(commits, audience),
            'issues': self._format_issues_for_prompt(issues, audience),
            'previous_releases': self._format_previous_releases(previous_releases) if previous_releases else 'None',
            'audience': audience,
            'custom_sections': ', '.join(custom_sections) if custom_sections else ''
        }
        
        # Add audience-specific instructions
        audience_instructions = self._get_audience_instructions(audience)
        if audience_instructions:
            template_data['audience_instructions'] = audience_instructions
        
        # Add section customization
        if custom_sections:
            template_data['sections_instruction'] = f"Include these specific sections: {', '.join(custom_sections)}"
        else:
            template_data['sections_instruction'] = self._get_default_sections(audience)
        
        # Format template
        try:
            return base_template.format(**template_data)
        except KeyError as e:
            # Handle missing template variables gracefully
            print(f"Warning: Template variable {e} not found, using fallback")
            return self._build_fallback_prompt(version, commits, issues, audience, previous_releases)
    
    def _format_commits_for_prompt(self, commits: List[Dict], audience: str) -> str:
        """Format commits for inclusion in prompt based on audience."""
        if not commits:
            return "No commits provided"
        
        if audience == 'developers':
            # Include more technical details
            formatted = []
            for commit in commits[:50]:  # Limit for prompt size
                formatted.append({
                    'hash': commit.get('hash', ''),
                    'author': commit.get('author', ''),
                    'subject': commit.get('subject', ''),
                    'body': commit.get('body', '')[:200],  # Truncate body
                    'type': commit.get('type', 'other'),
                    'url': commit.get('url', '')
                })
        else:
            # Simplified for users/managers
            formatted = []
            for commit in commits[:30]:
                formatted.append({
                    'subject': commit.get('subject', ''),
                    'type': commit.get('type', 'other'),
                    'author': commit.get('author', '')
                })
        
        return json.dumps(formatted, indent=2)
    
    def _format_issues_for_prompt(self, issues: List[Dict], audience: str) -> str:
        """Format issues for inclusion in prompt based on audience."""
        if not issues:
            return "No issues provided"
        
        formatted = []
        for issue in issues[:30]:  # Limit for prompt size
            item = {
                'title': issue.get('title', ''),
                'number': issue.get('number', ''),
                'labels': issue.get('labels', []),
                'state': issue.get('state', '')
            }
            
            if audience == 'developers':
                item['body'] = issue.get('body', '')[:300]  # Truncate
                item['url'] = issue.get('url', '')
            
            formatted.append(item)
        
        return json.dumps(formatted, indent=2)
    
    def _format_previous_releases(self, releases: List[Dict]) -> str:
        """Format previous releases for context."""
        if not releases:
            return "None"
        
        formatted = []
        for release in releases[:3]:  # Last 3 releases
            formatted.append({
                'version': release.get('version', ''),
                'name': release.get('name', ''),
                'summary': release.get('body', '')[:500]  # First 500 chars
            })
        
        return json.dumps(formatted, indent=2)
    
    def _get_audience_instructions(self, audience: str) -> str:
        """Get audience-specific instructions."""
        instructions = {
            'users': """
Focus on user-facing changes and benefits. Use simple language and explain the impact.
Avoid technical jargon and implementation details.
""",
            'developers': """
Include technical details, API changes, breaking changes, and implementation notes.
Reference commit hashes, PR numbers, and provide code examples where relevant.
""",
            'managers': """
Focus on business value, feature completeness, and high-level improvements.
Emphasize outcomes and benefits rather than technical implementation.
"""
        }
        return instructions.get(audience, '')
    
    def _get_default_sections(self, audience: str) -> str:
        """Get default sections based on audience."""
        if audience == 'developers':
            return "Use sections: Highlights, New Features, API Changes, Bug Fixes, Breaking Changes, Technical Improvements, Dependencies"
        elif audience == 'managers':
            return "Use sections: Executive Summary, Key Features, Business Impact, Improvements, Known Issues"
        else:  # users
            return "Use sections: Highlights, New Features, Improvements, Bug Fixes, Known Issues"
    
    def _build_fallback_prompt(
        self,
        version: str,
        commits: List[Dict],
        issues: List[Dict],
        audience: str,
        previous_releases: Optional[List[Dict]]
    ) -> str:
        """Build a simple fallback prompt if template formatting fails."""
        from datetime import datetime
        
        return f"""You are an assistant that writes professional release notes.

Version: {version}
Date: {datetime.now().date()}
Audience: {audience}

Commits:
{json.dumps(commits[:20], indent=2)}

Issues:
{json.dumps(issues[:20], indent=2)}

Previous Releases:
{json.dumps(previous_releases[:3] if previous_releases else [], indent=2)}

Generate professional release notes in markdown format with appropriate sections.
"""
    
    async def call_llm(self, prompt: str, model: str, temperature: float = 0.0) -> str:
        """Call the appropriate LLM provider."""
        provider = self.detect_provider(model)
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return await self.providers[provider](prompt, model, temperature)
    
    async def _call_openai(self, prompt: str, model: str, temperature: float) -> str:
        """Call OpenAI API."""
        api_key = env('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    async def _call_openrouter(self, prompt: str, model: str, temperature: float) -> str:
        """Call OpenRouter API."""
        api_key = env('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str, model: str, temperature: float) -> str:
        """Call Anthropic API."""
        api_key = env('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except ImportError:
            raise ValueError("anthropic package not installed. Run: pip install anthropic")
    
    async def _call_local_llm(self, prompt: str, model: str, temperature: float) -> str:
        """Call local LLM (e.g., Ollama)."""
        base_url = env('LOCAL_LLM_BASE_URL', 'http://localhost:11434')
        
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }
        
        try:
            response = requests.post(f'{base_url}/api/generate', json=payload)
            response.raise_for_status()
            return response.json().get('response', '')
            
        except requests.RequestException as e:
            raise ValueError(f"Error calling local LLM: {e}")
    
    async def _call_ollama(self, prompt: str, model: str, temperature: float) -> str:
        """Call local Ollama model."""
        return generate_with_ollama(model, prompt)
    
    async def _call_template(self, prompt: str, model: str, temperature: float) -> str:
        """Generate using template-based method."""
        # Extract data from prompt for template generation
        # This is a simplified approach - in practice, you'd parse the prompt better
        return "# Release Notes\n\nGenerated using template-based approach.\n\nPlease configure an AI model for better results."
    
    def parse_llm_output(self, output: str) -> Dict[str, Any]:
        """Parse LLM output into structured sections."""
        sections = {}
        current_section = None
        current_content = []
        
        lines = output.split('\n')
        
        for line in lines:
            # Check if line is a header (starts with #)
            if line.strip().startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip('#').strip().lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If no sections found, treat entire output as content
        if not sections:
            sections['content'] = output
        
        return sections


# Template management functions
def create_audience_template(audience: str, content: str) -> bool:
    """Create a custom template for specific audience."""
    try:
        template_path = Path(f'templates/prompt_{audience}.md')
        template_path.parent.mkdir(exist_ok=True)
        template_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error creating template: {e}")
        return False


def list_available_models() -> Dict[str, List[str]]:
    """List available models by provider."""
    return {
        'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
        'openrouter': [
            'anthropic/claude-3-opus',
            'anthropic/claude-3-sonnet', 
            'anthropic/claude-3-haiku',
            'openai/gpt-4',
            'meta-llama/llama-3-70b-instruct',
            'mistralai/mixtral-8x7b-instruct'
        ],
        'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
        'local': ['llama2', 'codellama', 'mistral', 'neural-chat']
    }