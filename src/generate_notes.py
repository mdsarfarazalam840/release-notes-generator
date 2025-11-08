"""Main orchestrator: collects data, prepares prompt, calls LLM, writes markdown."""
import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, env
from scripts.extract_commits import extract_commits_local, extract_commits_github, extract_commits_between_tags
from scripts.fetch_issues import fetch_github_issues
from scripts.fetch_releases import fetch_github_releases, get_previous_release_notes, fetch_changelog_from_repo
from scripts.classify_change import classify_commit
from src.publish_to_confluence import publish as publish_to_confluence

# LLM client placeholder - adapt to your provider
import openai

def build_prompt(version, commits, issues, audience, previous_releases=None):
    from pathlib import Path
    
    # Find templates directory relative to project root
    template_path = Path('templates/prompt.md')
    if not template_path.exists():
        # Look for templates in parent directories
        current = Path(__file__).parent
        while current != current.parent:
            template_candidate = current / 'templates' / 'prompt.md'
            if template_candidate.exists():
                template_path = template_candidate
                break
            current = current.parent
    
    with open(template_path) as f:
        tpl = f.read()
    
    prev_releases_text = ''
    if previous_releases:
        prev_releases_text = json.dumps(previous_releases[:3])  # Last 3 releases
    
    data = tpl.format(
        version=version,
        date=str(date.today()),
        commits=json.dumps(commits[:200]),
        issues=json.dumps(issues[:200]),
        previous_releases=prev_releases_text or 'None',
        audience=audience
    )
    return data

def call_llm(prompt, model='gpt-5', temperature=0.0):
    # Allow OpenRouter API key and endpoint
    import os
    import openai
    from src.utils import reload_env
    
    # Reload environment variables to ensure we have latest API keys
    reload_env()
    
    api_key = env('OPENROUTER_API_KEY') or env('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set in .env.local")
    
    # If using OpenRouter, must point base_url to their endpoint
    if env('OPENROUTER_API_KEY'):
        client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    else:
        client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=temperature,
        max_tokens=1500
    )
    return resp.choices[0].message.content

def assemble_sections(llm_output: str) -> str:
    # If the LLM already returns markdown, use it directly. Optionally post-process.
    return llm_output

if __name__ == '__main__':
    # Force reload environment variables from .env.local when executed
    from src.utils import reload_env
    reload_env()
    
    p = argparse.ArgumentParser(description='Generate release notes from git commits and GitHub issues')
    p.add_argument('--version', required=True, help='Release version (e.g., v1.2.0)')
    p.add_argument('--repo', default=None, help='GitHub repository in format owner/repo')
    p.add_argument('--audience', choices=['users', 'developers', 'managers'], default='users', help='Target audience')
    p.add_argument('--from-tag', default=None, help='Previous tag to compare from (for commit range)')
    p.add_argument('--since', default=None, help='Date since (ISO format or relative like "30 days ago")')
    p.add_argument('--milestone', default=None, help='GitHub milestone to filter issues')
    p.add_argument('--labels', default=None, help='Comma-separated issue labels to filter')
    p.add_argument('--use-github', action='store_true', help='Fetch commits from GitHub API instead of local git')
    p.add_argument('--publish-confluence', action='store_true', help='Publish to Confluence after generation')
    p.add_argument('--skip-previous-releases', action='store_true', help='Skip fetching previous release notes')
    args = p.parse_args()

    cfg = load_config()
    repo = args.repo or cfg.get('repo')
    
    # Reload env again to ensure we have latest values
    reload_env()
    github_token = env('GITHUB_TOKEN')
    
    # Debug output
    print(f'DEBUG: GITHUB_TOKEN: {"SET" if github_token else "NOT SET"}')
    print(f'DEBUG: OPENROUTER_API_KEY: {"SET" if env("OPENROUTER_API_KEY") else "NOT SET"}')
    print(f'DEBUG: OPENAI_API_KEY: {"SET" if env("OPENAI_API_KEY") else "NOT SET"}')
    
    if not repo:
        print('Error: Repository not specified. Use --repo or set in config.yaml')
        exit(1)

    print(f'Generating release notes for {args.version}...')
    print(f'Repository: {repo}')
    
    # Fetch commits
    print('\n[1/5] Fetching commits...')
    if args.use_github and github_token:
        if args.from_tag:
            # Extract commits between tags
            print(f'  Fetching commits between tags...')
            commits = extract_commits_between_tags(repo, github_token, args.from_tag, args.version)
        else:
            commits = extract_commits_github(repo, github_token, since=args.since)
        print(f'  Found {len(commits)} commits from GitHub')
    else:
        commits = extract_commits_local('.', since=args.since)
        print(f'  Found {len(commits)} commits from local repository')
    
    if not commits:
        print('  Warning: No commits found!')

    # Fetch issues
    print('\n[2/5] Fetching issues...')
    issues = fetch_github_issues(
        repo, 
        github_token, 
        milestone=args.milestone,
        labels=args.labels.split(',') if args.labels else None,
        since=args.since
    )
    print(f'  Found {len(issues)} issues')
    
    # Fetch previous release notes
    previous_releases = []
    if not args.skip_previous_releases and github_token:
        print('\n[3/5] Fetching previous release notes...')
        try:
            previous_releases = get_previous_release_notes(repo, github_token, args.version, count=3)
            print(f'  Found {len(previous_releases)} previous releases')
        except Exception as e:
            print(f'  Warning: Could not fetch previous releases: {e}')
    
    # Classify commits
    print('\n[4/5] Classifying commits...')
    for c in commits:
        c['type'] = classify_commit(c['subject'])

    # Build prompt and call LLM
    print('\n[5/5] Generating release notes with LLM...')
    prompt = build_prompt(args.version, commits, issues, args.audience, previous_releases)
    llm_out = call_llm(prompt, model=cfg['llm']['model'], temperature=cfg['llm'].get('temperature',0.0))

    # Assemble and write
    md = assemble_sections(llm_out)
    out_file = Path('examples') / f'release_{args.version}.md'
    out_file.parent.mkdir(exist_ok=True)
    out_file.write_text(md, encoding='utf-8')
    print(f'\nWrote {out_file}')
    
    # Publish to Confluence if requested
    confluence_url = None
    if args.publish_confluence:
        print('\n[6/6] Publishing to Confluence...')
        try:
            result = publish_to_confluence(args.version, str(out_file))
            if result and result.get('_links', {}).get('webui'):
                confluence_url = result['_links']['webui']
                print(f'Published to Confluence: {confluence_url}')
            else:
                print('Published to Confluence (URL not available)')
        except Exception as e:
            print(f'  Error publishing to Confluence: {e}')
            print('  Make sure CONFLUENCE_BASE, CONFLUENCE_USER, and CONFLUENCE_API_TOKEN are set in .env.local')
    
    print(f'\nRelease notes generation complete!')
