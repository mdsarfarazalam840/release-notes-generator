"""Enhanced API endpoints for the release notes generator."""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from flask import Flask, jsonify, request, send_file, make_response
from werkzeug.utils import secure_filename

from src.utils import load_config, env
from src.data_ingestion import DataIngestionService, ingest_all_data

# Force inject environment variables at module import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# NUCLEAR FIX: Monkey patch all GitHub requests
try:
    from src.nuclear_github_fix import nuclear_github_request_interceptor
    print("Nuclear GitHub fix activated")
except Exception as e:
    print(f"Warning: Nuclear fix failed: {e}")
from src.llm_service import LLMService, list_available_models
from src.publish_to_confluence import publish as publish_to_confluence
from src.enhanced_api_endpoints import add_enhanced_endpoints


def create_enhanced_app() -> Flask:
    """Create Flask app with enhanced endpoints."""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    # Disable Flask's default error handlers that return HTML
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # CORS headers
    @app.after_request
    def add_cors_headers(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        # Ensure JSON content type for errors
        if resp.status_code >= 400:
            resp.headers['Content-Type'] = 'application/json'
        return resp

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,POST,PUT,DELETE,OPTIONS")
            return response
    
    # Error handlers to ensure all errors return JSON
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'message': 'Not found', 'error': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors - ALWAYS return JSON"""
        from flask import Response
        error_msg = str(error).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        json_response = f'{{"status":"error","message":"Internal server error","error":"{error_msg}"}}'
        return Response(
            response=json_response,
            status=500,
            mimetype='application/json',
            headers={'Content-Type': 'application/json'}
        )
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions - ALWAYS return JSON"""
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR HANDLER CAUGHT: {e}")
        print(f"Traceback: {error_trace}")
        
        # Always use Response directly - NEVER use jsonify which might fail
        from flask import Response
        error_msg = str(e).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        json_response = f'{{"status":"error","message":"{error_msg}","error":"An unexpected error occurred"}}'
        
        return Response(
            response=json_response,
            status=500,
            mimetype='application/json',
            headers={'Content-Type': 'application/json'}
        )

    # Debug endpoint
    @app.route('/api/debug/env', methods=['GET'])
    def debug_env():
        """Debug environment variables."""
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        current_dir = Path.cwd()
        env_file = current_dir / '.env'
        env_local_file = current_dir / '.env.local'
        
        # Load fresh
        load_dotenv(env_file)
        load_dotenv(env_local_file, override=True)
        
        return jsonify({
            'current_dir': str(current_dir),
            'env_file_exists': env_file.exists(),
            'env_local_exists': env_local_file.exists(),
            'confluence_base': os.getenv('CONFLUENCE_BASE'),
            'confluence_user': os.getenv('CONFLUENCE_USER'),
            'github_token_set': bool(os.getenv('GITHUB_TOKEN')),
            'github_token_prefix': os.getenv('GITHUB_TOKEN', '')[:10] if os.getenv('GITHUB_TOKEN') else None
        })

    # Configuration endpoints
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get configuration information."""
        cfg = load_config()
        
        # Force reload environment variables - direct approach
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Clear existing environment cache
        for key in ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN', 'GITHUB_TOKEN']:
            if key in os.environ:
                del os.environ[key]
        
        # Reload from files
        current_dir = Path.cwd()
        env_file = current_dir / '.env'
        env_local_file = current_dir / '.env.local'
        
        if env_file.exists():
            load_dotenv(env_file)
        if env_local_file.exists():
            load_dotenv(env_local_file, override=True)
        
        # Get fresh values
        confluence_base = os.getenv('CONFLUENCE_BASE')
        confluence_user = os.getenv('CONFLUENCE_USER') 
        confluence_token = os.getenv('CONFLUENCE_API_TOKEN')
        github_token = os.getenv('GITHUB_TOKEN')
        
        print(f"DEBUG - CONFLUENCE_BASE: {confluence_base}")
        print(f"DEBUG - CONFLUENCE_USER: {confluence_user}")
        print(f"DEBUG - CONFLUENCE_TOKEN: {'SET' if confluence_token and not confluence_token.startswith('your_') else 'NOT SET'}")
        print(f"DEBUG - GITHUB_TOKEN: {'SET' if github_token and not github_token.startswith('your_') else 'NOT SET'}")
        
        # Check if values are real (not placeholders)
        confluence_configured = bool(
            confluence_base and 
            confluence_user and 
            confluence_token and
            not confluence_base.startswith('https://yourcompany') and
            not confluence_user.startswith('you@') and
            not confluence_token.startswith('your_')
        )
        
        github_configured = bool(
            github_token and 
            not github_token.startswith('your_') and
            len(github_token) > 10
        )
        
        return jsonify({
            'repo': cfg.get('repo', ''),
            'has_github_token': github_configured,
            'has_jira_config': bool(env('JIRA_BASE_URL') and env('JIRA_API_TOKEN')),
            'llm_model': cfg.get('llm', {}).get('model', ''),
            'confluence_configured': confluence_configured,
            'confluence_details': {
                'base_url': confluence_base if confluence_base and not confluence_base.startswith('https://yourcompany') else 'Not configured',
                'user': confluence_user if confluence_user and not confluence_user.startswith('you@') else 'Not configured', 
                'token_set': bool(confluence_token and not confluence_token.startswith('your_'))
            },
            'supported_sources': {
                'commits': ['local', 'github'],
                'issues': ['github', 'jira', 'json'],
                'releases': ['github', 'local', 'changelog']
            }
        })

    @app.route('/api/config', methods=['PUT'])
    def update_config():
        """Update configuration."""
        try:
            new_config = request.get_json()
            
            # Load existing config
            cfg = load_config()
            
            # Update with new values
            if 'repo' in new_config:
                cfg['repo'] = new_config['repo']
            if 'llm' in new_config:
                cfg['llm'].update(new_config['llm'])
            if 'publish' in new_config:
                cfg['publish'].update(new_config['publish'])
            
            # Save config
            import yaml
            with open('config.yaml', 'w') as f:
                yaml.dump(cfg, f, default_flow_style=False)
            
            return jsonify({'status': 'ok', 'config': cfg})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # LLM model endpoints
    @app.route('/api/models', methods=['GET'])
    def get_available_models():
        """Get available LLM models."""
        return jsonify(list_available_models())

    @app.route('/api/models/test', methods=['POST'])
    def test_model():
        """Test LLM model connectivity."""
        try:
            data = request.get_json()
            model = data.get('model')
            provider = data.get('provider')
            
            if not model:
                return jsonify({'error': 'Model required'}), 400
            
            # Create test prompt
            test_prompt = "Write a single sentence about software release notes."
            
            # Test the model
            llm_service = LLMService()
            result = asyncio.run(llm_service.call_llm(test_prompt, model, 0.0))
            
            return jsonify({
                'status': 'ok',
                'model': model,
                'response': result[:100] + '...' if len(result) > 100 else result
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Data ingestion endpoints
    @app.route('/api/data/commits', methods=['GET'])
    def get_commits():
        """Fetch commits from various sources."""
        try:
            source = request.args.get('source', 'auto')
            repo = request.args.get('repo')
            from_tag = request.args.get('from_tag')
            to_tag = request.args.get('to_tag')
            since = request.args.get('since')
            until = request.args.get('until')
            branch = request.args.get('branch')
            
            service = DataIngestionService()
            commits = asyncio.run(service.ingest_commits(
                source=source,
                repo=repo,
                from_tag=from_tag,
                to_tag=to_tag,
                since=since,
                until=until,
                branch=branch
            ))
            
            return jsonify({
                'commits': commits,
                'count': len(commits),
                'source': source,
                'repo': repo
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/data/issues', methods=['GET'])
    def get_issues():
        """Fetch issues from various sources."""
        try:
            source = request.args.get('source', 'github')
            repo = request.args.get('repo')
            milestone = request.args.get('milestone')
            labels = request.args.get('labels', '').split(',') if request.args.get('labels') else None
            since = request.args.get('since')
            project_key = request.args.get('project_key')
            
            service = DataIngestionService()
            issues = asyncio.run(service.ingest_issues(
                source=source,
                repo=repo,
                milestone=milestone,
                labels=labels,
                since=since,
                project_key=project_key
            ))
            
            return jsonify({
                'issues': issues,
                'count': len(issues),
                'source': source,
                'repo': repo
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/data/releases', methods=['GET'])
    def get_previous_releases():
        """Fetch previous releases from various sources."""
        try:
            source = request.args.get('source', 'auto')
            repo = request.args.get('repo')
            count = int(request.args.get('count', 3))
            current_version = request.args.get('current_version')
            
            service = DataIngestionService()
            releases = asyncio.run(service.ingest_previous_releases(
                source=source,
                repo=repo,
                count=count,
                current_version=current_version
            ))
            
            return jsonify({
                'releases': releases,
                'count': len(releases),
                'source': source,
                'repo': repo
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # File upload endpoints
    @app.route('/api/upload/issues', methods=['POST'])
    def upload_issues():
        """Upload issues JSON file."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not file.filename.endswith('.json'):
                return jsonify({'error': 'Only JSON files allowed'}), 400
            
            # Save uploaded file
            uploads_dir = Path('uploads')
            uploads_dir.mkdir(exist_ok=True)
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_filename = f"issues_{timestamp}_{filename}"
            file_path = uploads_dir / saved_filename
            
            file.save(file_path)
            
            # Validate JSON structure
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Basic validation
                if isinstance(data, list):
                    issues_count = len(data)
                elif isinstance(data, dict) and 'issues' in data:
                    issues_count = len(data['issues'])
                else:
                    return jsonify({'error': 'Invalid JSON structure'}), 400
                
                return jsonify({
                    'status': 'ok',
                    'filename': saved_filename,
                    'issues_count': issues_count,
                    'path': str(file_path)
                })
                
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON file'}), 400
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Enhanced generation endpoint
    @app.route('/api/generate/enhanced', methods=['POST'])
    def generate_enhanced():
        """Enhanced release notes generation endpoint - always returns JSON."""
        import traceback
        from flask import Response
        
        # Wrap everything to ensure JSON is ALWAYS returned
        try:
            return _generate_enhanced_internal()
        except Exception as outer_e:
            # Ultimate fallback - this should NEVER fail
            error_msg = str(outer_e).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            json_response = f'{{"status":"error","error":"{error_msg}","message":"Enhanced generation failed - outer handler"}}'
            return Response(
                response=json_response,
                status=500,
                mimetype='application/json',
                headers={'Content-Type': 'application/json'}
            )
    
    def _generate_enhanced_internal():
        """Internal implementation of enhanced generation."""
        import traceback
        from flask import Response
        
        # Ensure we always return JSON, even if there's an error in error handling
        try:
            data = request.get_json(force=True, silent=True) or {}
            
            # Required parameters
            version = data.get('version')
            if not version:
                return jsonify({'status': 'error', 'error': 'Version is required'}), 400
            
            # Optional parameters with defaults
            repo = data.get('repo')
            audience = data.get('audience', 'users')
            from_tag = data.get('from_tag')
            since = data.get('since')
            
            # Source configurations
            commit_source = data.get('commit_source', 'auto')
            issue_source = data.get('issue_source', 'github')
            release_source = data.get('release_source', 'auto')
            
            # Filters
            milestone = data.get('milestone')
            labels = data.get('labels', [])
            project_key = data.get('project_key')
            json_file = data.get('json_file')
            
            # LLM configuration
            model = data.get('model')
            temperature = data.get('temperature')
            template = data.get('template')
            custom_sections = data.get('custom_sections', [])
            
            # Publishing options
            publish_confluence = data.get('publish_confluence', False)
            publish_github = data.get('publish_github', False)
            publish_slack = data.get('publish_slack', False)
            
            # Collect publishing platforms
            publish_platforms = []
            if publish_confluence:
                publish_platforms.append('confluence')
            if publish_github:
                publish_platforms.append('github')
            if publish_slack:
                publish_platforms.append('slack')
            
            # Get repository from config if not provided
            if not repo:
                cfg = load_config()
                repo = cfg.get('repo')
            
            if not repo:
                return jsonify({'status': 'error', 'error': 'Repository not specified'}), 400
            
            print(f"Enhanced generation for version: {version}, repo: {repo}")
            
            # Try to use enhanced generation, fallback to simple generation
            try:
                # Use enhanced async generation
                from src.enhanced_generate_notes import generate_enhanced_release_notes
                import asyncio
                import io
                import sys
                
                # Capture stdout/stderr to avoid Unicode encoding issues
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', errors='replace')
                
                try:
                    result = asyncio.run(generate_enhanced_release_notes(
                        version=version,
                        repo=repo,
                        audience=audience,
                        from_tag=from_tag,
                        since=since,
                        commit_source=commit_source,
                        issue_source=issue_source,
                        release_source=release_source,
                        milestone=milestone,
                        labels=labels if isinstance(labels, list) else labels.split(',') if labels else [],
                        project_key=project_key,
                        json_file=json_file,
                        model=model,
                        temperature=temperature,
                        template=template,
                        custom_sections=custom_sections if isinstance(custom_sections, list) else custom_sections.split(',') if custom_sections else [],
                        publish_platforms=publish_platforms
                    ))
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                
                # Check if result indicates an error
                if result.get('status') == 'error':
                    response = jsonify({
                        'status': 'error',
                        'error': result.get('error', 'Enhanced generation failed')
                    })
                    response.status_code = 500
                    response.headers['Content-Type'] = 'application/json'
                    return response
                
                response = jsonify({
                    'status': 'ok',
                    **result
                })
                response.headers['Content-Type'] = 'application/json'
                return response
                
            except (ImportError, AttributeError, TypeError, Exception) as e:
                print(f"Enhanced generation not available, using fallback: {e}")
                import traceback as tb
                print(f"Fallback reason: {tb.format_exc()}")
                # Fallback to simple generation via subprocess
                import subprocess
                import sys
                from pathlib import Path
                
                current_dir = Path.cwd()
                cmd = [
                    sys.executable, '-m', 'src.generate_notes',
                    '--version', version,
                    '--audience', audience,
                    '--repo', repo
                ]
                if from_tag:
                    cmd.extend(['--from-tag', from_tag])
                if publish_confluence:
                    cmd.append('--publish-confluence')
                
                env_vars = os.environ.copy()
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env_vars,
                    timeout=300,
                    cwd=str(current_dir)
                )
                
                if result.returncode != 0:
                    response = jsonify({
                        'status': 'error',
                        'error': result.stderr or 'Generation failed'
                    })
                    response.status_code = 500
                    response.headers['Content-Type'] = 'application/json'
                    return response
                
                # Read the generated file
                output_file = Path('examples') / f'release_{version}.md'
                if output_file.exists():
                    content = output_file.read_text(encoding='utf-8')
                    response = jsonify({
                        'status': 'ok',
                        'version': version,
                        'output_file': str(output_file),
                        'raw_output': content
                    })
                    response.headers['Content-Type'] = 'application/json'
                    return response
                else:
                    response = jsonify({
                        'status': 'error',
                        'error': 'Generation completed but file not found'
                    })
                    response.status_code = 500
                    response.headers['Content-Type'] = 'application/json'
                    return response
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"CRITICAL Error in generate_enhanced endpoint: {e}")
            print(f"Traceback: {error_trace}")
            
            # Use Response directly to ensure JSON is returned
            error_msg = str(e).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            json_response = f'{{"status":"error","error":"{error_msg}","message":"Enhanced generation failed"}}'
            
            return Response(
                response=json_response,
                status=500,
                mimetype='application/json',
                headers={'Content-Type': 'application/json'}
            )

    # Progress tracking endpoint
    @app.route('/api/generate/status/<task_id>', methods=['GET'])
    def get_generation_status(task_id):
        """Get the status of a generation task."""
        # This would require implementing background task tracking
        # For now, return a simple response
        return jsonify({
            'task_id': task_id,
            'status': 'completed',  # In real implementation: pending, running, completed, failed
            'progress': 100,
            'message': 'Generation completed'
        })

    # Publishing endpoints
    @app.route('/api/publish/confluence', methods=['POST'])
    def publish_confluence_endpoint():
        """Publish release notes to Confluence."""
        try:
            data = request.get_json()
            version = data.get('version')
            file_path = data.get('file_path')
            update_existing = data.get('update_existing', True)
            
            if not version or not file_path:
                return jsonify({'error': 'Version and file_path required'}), 400
            
            result = publish_to_confluence(version, file_path, update_existing)
            
            return jsonify({
                'status': 'ok',
                'result': result,
                'version': version
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/publish/platforms', methods=['GET'])
    def get_publishing_platforms():
        """Get available publishing platforms and their status."""
        platforms = {
            'confluence': {
                'name': 'Confluence',
                'configured': bool(env('CONFLUENCE_BASE') and env('CONFLUENCE_API_TOKEN')),
                'required_env': ['CONFLUENCE_BASE', 'CONFLUENCE_USER', 'CONFLUENCE_API_TOKEN']
            },
            'github': {
                'name': 'GitHub Releases',
                'configured': bool(env('GITHUB_TOKEN')),
                'required_env': ['GITHUB_TOKEN']
            },
            'slack': {
                'name': 'Slack',
                'configured': bool(env('SLACK_WEBHOOK_URL')),
                'required_env': ['SLACK_WEBHOOK_URL']
            },
            'email': {
                'name': 'Email',
                'configured': bool(env('SMTP_HOST') and env('SMTP_USER')),
                'required_env': ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD']
            }
        }
        
        return jsonify(platforms)

    # Template management endpoints
    @app.route('/api/templates', methods=['GET'])
    def list_templates():
        """List available templates."""
        templates_dir = Path('templates')
        templates = []
        
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.md'):
                templates.append({
                    'name': template_file.stem,
                    'path': str(template_file),
                    'modified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
                })
        
        return jsonify({'templates': templates})

    @app.route('/api/templates/<template_name>', methods=['GET'])
    def get_template(template_name):
        """Get a specific template."""
        template_path = Path(f'templates/{template_name}.md')
        
        if not template_path.exists():
            return jsonify({'error': 'Template not found'}), 404
        
        content = template_path.read_text(encoding='utf-8')
        
        return jsonify({
            'name': template_name,
            'content': content,
            'path': str(template_path)
        })

    @app.route('/api/templates/<template_name>', methods=['PUT'])
    def update_template(template_name):
        """Update or create a template."""
        try:
            data = request.get_json()
            content = data.get('content')
            
            if not content:
                return jsonify({'error': 'Content required'}), 400
            
            templates_dir = Path('templates')
            templates_dir.mkdir(exist_ok=True)
            
            template_path = templates_dir / f'{template_name}.md'
            template_path.write_text(content, encoding='utf-8')
            
            return jsonify({
                'status': 'ok',
                'name': template_name,
                'path': str(template_path)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Add enhanced endpoints
    add_enhanced_endpoints(app)
    
    return app


# Utility functions for the API
def validate_generation_request(data: Dict) -> tuple[bool, Optional[str]]:
    """Validate generation request data."""
    required_fields = ['version']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate audience
    if 'audience' in data and data['audience'] not in ['users', 'developers', 'managers']:
        return False, "Invalid audience. Must be one of: users, developers, managers"
    
    # Validate sources
    valid_commit_sources = ['local', 'github', 'auto']
    if 'commit_source' in data and data['commit_source'] not in valid_commit_sources:
        return False, f"Invalid commit_source. Must be one of: {valid_commit_sources}"
    
    valid_issue_sources = ['github', 'jira', 'json']
    if 'issue_source' in data and data['issue_source'] not in valid_issue_sources:
        return False, f"Invalid issue_source. Must be one of: {valid_issue_sources}"
    
    return True, None