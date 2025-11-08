import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, send_file, make_response

# Ensure the project root is on Python path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils import load_config
from src.api_endpoints import create_enhanced_app

# Create enhanced app with all new endpoints
app = create_enhanced_app()

EXAMPLES_DIR = Path('examples')


# Legacy endpoints for backward compatibility
@app.route('/api/list', methods=['GET'])  
def list_notes():
    EXAMPLES_DIR.mkdir(exist_ok=True)
    files = sorted(EXAMPLES_DIR.glob('release_*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
    data = [
        {
            'name': f.name,
            'path': str(f),
            'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        }
        for f in files
    ]
    return jsonify({'files': data})


@app.route('/api/latest', methods=['GET'])
def latest_note():
    EXAMPLES_DIR.mkdir(exist_ok=True)
    files = sorted(EXAMPLES_DIR.glob('release_*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return jsonify({'error': 'no files found'}), 404
    latest = files[0]
    content = latest.read_text(encoding='utf-8')
    return jsonify({'name': latest.name, 'content': content})


def _read_release_file(path: Path):
    content = path.read_text(encoding='utf-8')
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    title = lines[0] if lines else path.stem
    if title.startswith('#'):
        title = title.lstrip('#').strip()
    snippet = '\n'.join(content.splitlines()[:30]).strip()
    tag = path.stem.replace('release_', '')
    return {
        'tag_name': tag,
        'name': title or tag,
        'body': snippet,
        'path': str(path),
        'published_at': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        'prerelease': False,
        'draft': False,
        'url': '',
    }


@app.route('/api/releases', methods=['GET'])
def list_releases():
    """List local release notes stored in the examples folder."""
    cfg = load_config()
    repo = request.args.get('repo') or cfg.get('repo', 'local/examples')

    EXAMPLES_DIR.mkdir(exist_ok=True)
    files = sorted(
        EXAMPLES_DIR.glob('release_*.md'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    releases = [_read_release_file(path) for path in files]
    return jsonify({'releases': releases, 'repo': repo, 'source': 'local'})


def _get_release_list():
    EXAMPLES_DIR.mkdir(exist_ok=True)
    files = sorted(
        EXAMPLES_DIR.glob('release_*.md'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return [_read_release_file(path) for path in files]


@app.route('/api/releases/<tag>', methods=['GET'])
def get_release(tag):
    """Return a specific release based on local files."""
    EXAMPLES_DIR.mkdir(exist_ok=True)
    candidates = list(EXAMPLES_DIR.glob(f'release_{tag}.md'))
    if not candidates:
        # try without exact match (case-insensitive)
        candidates = [p for p in EXAMPLES_DIR.glob('release_*.md') if p.stem.endswith(tag)]

    if not candidates:
        return jsonify({'error': 'Release not found'}), 404

    release_data = _read_release_file(candidates[0])
    release_data['content'] = candidates[0].read_text(encoding='utf-8')
    return jsonify({'release': release_data})


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate release notes endpoint - always returns JSON"""
    # Ensure we always return JSON even on errors
    try:
        # Force reload environment variables before generation
        from dotenv import load_dotenv
        from pathlib import Path
        current_dir = Path.cwd()
        env_file = current_dir / '.env'
        env_local_file = current_dir / '.env.local'
        
        if env_file.exists():
            load_dotenv(env_file)
        if env_local_file.exists():
            load_dotenv(env_local_file, override=True)
        
        body = request.get_json(force=True, silent=True) or {}
        version = body.get('version') or datetime.now().strftime('v%Y.%m.%d-%H%M')
        audience = body.get('audience', 'users')
        use_github = body.get('use_github', True)
        repo = body.get('repo')
        from_tag = body.get('from_tag')
        labels = body.get('labels')
        milestone = body.get('milestone')
        since = body.get('since')

        cfg = load_config()
        repo = repo or cfg.get('repo')
        
        if not repo:
            return jsonify({'error': 'Repository not specified. Use --repo or set in config.yaml'}), 400

        # Use sys.executable to ensure we use the same Python interpreter
        cmd = [
            sys.executable, '-m', 'src.generate_notes',
            '--version', version,
            '--audience', audience,
            '--repo', repo
        ]
        if use_github:
            cmd.append('--use-github')
        if from_tag:
            cmd.extend(['--from-tag', from_tag])
        if labels:
            cmd.extend(['--labels', labels])
        if milestone:
            cmd.extend(['--milestone', milestone])
        if since:
            cmd.extend(['--since', since])

        # Check if Confluence publishing is requested
        publish_confluence = body.get('publish_confluence', False)
        if publish_confluence:
            cmd.append('--publish-confluence')
        
        # Pass current environment variables to subprocess (including .env.local)
        env_vars = os.environ.copy()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env_vars,  # Explicitly pass environment variables
            timeout=300,  # 5 minute timeout
            cwd=str(current_dir)  # Ensure working directory is correct
        )
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'code': result.returncode,
                'message': result.stderr or 'Generation failed'
            }), 500
        
        # Check for Confluence link in output
        confluence_result = None
        if publish_confluence:
            # Try to extract Confluence link from output
            output_lines = result.stdout.split('\n')
            import re
            for line in output_lines:
                # Pattern: Published to Confluence: https://...
                url_match = re.search(r'Published to Confluence:\s*(https?://[^\s]+)', line)
                if url_match:
                    confluence_result = {
                        '_links': {
                            'webui': url_match.group(1)
                        }
                    }
                    break
                # Pattern: Confluence page: https://...
                url_match = re.search(r'Confluence page:\s*(https?://[^\s]+)', line)
                if url_match:
                    confluence_result = {
                        '_links': {
                            'webui': url_match.group(1)
                        }
                    }
                    break
                # Pattern: Just a URL on a line with Confluence
                if 'Confluence' in line:
                    url_match = re.search(r'(https?://[^\s]+)', line)
                    if url_match:
                        confluence_result = {
                            '_links': {
                                'webui': url_match.group(1)
                            }
                        }
                        break
        
        # refresh release list after generation
        releases = _get_release_list()
        response_data = {
            'status': 'ok',
            'version': version,
            'output': result.stdout,
            'releases': releases
        }
        
        if confluence_result:
            response_data['confluence'] = confluence_result
        
        return jsonify(response_data)
    except subprocess.TimeoutExpired:
        response = jsonify({'status': 'error', 'message': 'Generation timed out'})
        response.status_code = 500
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in generate endpoint: {e}")
        print(f"Traceback: {error_trace}")
        response = jsonify({
            'status': 'error',
            'message': str(e),
            'error': 'Generation failed'
        })
        response.status_code = 500
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    # Force inject environment variables before starting server
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        from fix_flask_env import inject_env_vars
        env_status = inject_env_vars()
        print("🚀 Starting Flask server with injected environment...")
    except Exception as e:
        print(f"⚠️ Environment injection failed: {e}")
    
    app.run(host='0.0.0.0', port=5000)


