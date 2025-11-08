"""Enhanced main orchestrator with new data ingestion and publishing capabilities."""
import argparse
import asyncio
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, env
from src.data_ingestion import ingest_all_data
from src.llm_service import LLMService
from src.publishing_service import auto_publish


async def generate_enhanced_release_notes(
    version: str,
    repo: Optional[str] = None,
    audience: str = 'users',
    from_tag: Optional[str] = None,
    since: Optional[str] = None,
    commit_source: str = 'auto',
    issue_source: str = 'github',
    release_source: str = 'auto',
    milestone: Optional[str] = None,
    labels: Optional[List[str]] = None,
    project_key: Optional[str] = None,
    json_file: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    template: Optional[str] = None,
    custom_sections: Optional[List[str]] = None,
    publish_platforms: Optional[List[str]] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced release notes generation with full configuration options.
    
    Args:
        version: Release version (required)
        repo: Repository name (owner/repo format)
        audience: Target audience (users, developers, managers)
        from_tag: Previous tag to compare from
        since: Date since (ISO format)
        commit_source: Source for commits (auto, local, github)
        issue_source: Source for issues (github, jira, json)
        release_source: Source for previous releases (auto, github, local, changelog)
        milestone: GitHub milestone filter
        labels: Issue labels filter
        project_key: JIRA project key
        json_file: Path to uploaded JSON issues file
        model: LLM model to use
        temperature: LLM temperature setting
        template: Custom template name
        custom_sections: Custom sections for output
        publish_platforms: Platforms to publish to
        output_file: Custom output file path
    
    Returns:
        Dictionary with generation results and metadata
    """
    
    print(f'Enhanced Release Notes Generation for {version}')
    print(f'Repository: {repo}')
    print(f'Audience: {audience}')
    print(f'Sources: commits={commit_source}, issues={issue_source}, releases={release_source}')
    
    try:
        # Step 1: Ingest all data
        print('\n[1/4] Ingesting data from all sources...')
        
        ingestion_data = await ingest_all_data(
            version=version,
            repo=repo,
            from_tag=from_tag,
            since=since,
            commit_source=commit_source,
            issue_source=issue_source,
            include_previous=True,
            milestone=milestone,
            labels=labels,
            project_key=project_key,
            json_file=json_file,
            release_source=release_source
        )
        
        print(f'  [OK] Commits: {len(ingestion_data["commits"])}')
        print(f'  [OK] Issues: {len(ingestion_data["issues"])}')
        print(f'  [OK] Previous releases: {len(ingestion_data["previous_releases"])}')
        
        # Step 2: Generate with LLM
        print('\n[2/4] Generating release notes with LLM...')
        
        llm_service = LLMService()
        llm_result = await llm_service.generate_release_notes(
            version=version,
            commits=ingestion_data['commits'],
            issues=ingestion_data['issues'],
            audience=audience,
            previous_releases=ingestion_data['previous_releases'],
            template=template,
            custom_sections=custom_sections,
            model=model,
            temperature=temperature
        )
        
        # Add AI model information to the generated content
        model_name = llm_result["metadata"]["model"]
        model_footer = f"\n\n---\n*Generated with AI model: {model_name}*\n"
        llm_result['raw_output'] += model_footer
        
        print(f'  [OK] Generated with model: {llm_result["metadata"]["model"]}')
        print(f'  [OK] Structured sections: {len(llm_result["structured"])}')
        
        # Step 3: Save to file
        print('\n[3/4] Saving release notes...')
        
        if output_file:
            output_path = Path(output_file)
        else:
            output_dir = Path('examples')
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f'release_{version}.md'
        
        output_path.write_text(llm_result['raw_output'], encoding='utf-8')
        print(f'  [OK] Saved to: {output_path}')
        
        # Step 4: Publish to platforms
        publishing_results = {}
        if publish_platforms:
            print(f'\n[4/4] Publishing to platforms: {", ".join(publish_platforms)}...')
            
            metadata = {
                'repo': repo,
                'audience': audience,
                'model': llm_result['metadata']['model'],
                'data_summary': {
                    'commits_count': len(ingestion_data['commits']),
                    'issues_count': len(ingestion_data['issues']),
                    'previous_releases_count': len(ingestion_data['previous_releases'])
                }
            }
            
            publishing_results = await auto_publish(
                version=version,
                file_path=str(output_path),
                platforms=publish_platforms,
                metadata=metadata
            )
            
            print(f'  [OK] Published to: {publishing_results["published_to"]}')
            if publishing_results['failed_to']:
                print(f'  [FAIL] Failed to publish to: {publishing_results["failed_to"]}')
        else:
            print('\n[4/4] Skipping publishing (no platforms specified)')
        
        # Return comprehensive results
        return {
            'status': 'success',
            'version': version,
            'output_file': str(output_path),
            'raw_output': llm_result['raw_output'],
            'structured_output': llm_result['structured'],
            'metadata': {
                **llm_result['metadata'],
                **ingestion_data['metadata']
            },
            'publishing': publishing_results,
            'data_summary': {
                'commits_count': len(ingestion_data['commits']),
                'issues_count': len(ingestion_data['issues']),
                'previous_releases_count': len(ingestion_data['previous_releases'])
            }
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f'\n[ERROR] Error: {e}')
        print(f'Traceback: {error_trace}')
        return {
            'status': 'error',
            'error': str(e),
            'version': version
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Enhanced Release Notes Generator with multi-source data ingestion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic generation
  python -m src.enhanced_generate_notes --version v1.2.3
  
  # With specific sources and filters
  python -m src.enhanced_generate_notes --version v1.2.3 \\
    --commit-source github --issue-source jira \\
    --project-key PROJ --labels bug,feature \\
    --audience developers
  
  # With publishing
  python -m src.enhanced_generate_notes --version v1.2.3 \\
    --publish confluence github slack
  
  # Upload JSON issues
  python -m src.enhanced_generate_notes --version v1.2.3 \\
    --issue-source json --json-file issues.json
        """
    )
    
    # Required arguments
    parser.add_argument('--version', required=True, 
                       help='Release version (e.g., v1.2.3)')
    
    # Basic configuration
    parser.add_argument('--repo', 
                       help='Repository in format owner/repo')
    parser.add_argument('--audience', 
                       choices=['users', 'developers', 'managers'], 
                       default='users',
                       help='Target audience for release notes')
    
    # Data source configuration
    parser.add_argument('--commit-source', 
                       choices=['auto', 'local', 'github'], 
                       default='auto',
                       help='Source for commit data')
    parser.add_argument('--issue-source', 
                       choices=['github', 'jira', 'json'], 
                       default='github',
                       help='Source for issue data')
    parser.add_argument('--release-source', 
                       choices=['auto', 'github', 'local', 'changelog'], 
                       default='auto',
                       help='Source for previous release notes')
    
    # Filters and ranges
    parser.add_argument('--from-tag', 
                       help='Previous tag to compare from (for commit range)')
    parser.add_argument('--since', 
                       help='Date since (ISO format or relative like "30 days ago")')
    parser.add_argument('--milestone', 
                       help='GitHub milestone to filter issues')
    parser.add_argument('--labels', 
                       help='Comma-separated issue labels to filter')
    parser.add_argument('--project-key', 
                       help='JIRA project key')
    parser.add_argument('--json-file', 
                       help='Path to JSON file with issues data')
    
    # LLM configuration
    parser.add_argument('--model', 
                       help='LLM model to use (overrides config)')
    parser.add_argument('--temperature', 
                       type=float,
                       help='LLM temperature (0.0-1.0)')
    parser.add_argument('--template', 
                       help='Custom template name or path')
    parser.add_argument('--custom-sections', 
                       help='Comma-separated custom sections to include')
    
    # Output and publishing
    parser.add_argument('--output', 
                       help='Custom output file path')
    parser.add_argument('--publish', 
                       nargs='+',
                       choices=['confluence', 'github', 'slack', 'email', 'webhook'],
                       help='Platforms to publish to after generation')
    
    # Flags
    parser.add_argument('--skip-previous-releases', 
                       action='store_true',
                       help='Skip fetching previous release notes for context')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what would be done without actually generating')
    
    args = parser.parse_args()
    
    # Convert comma-separated strings to lists
    labels = args.labels.split(',') if args.labels else None
    custom_sections = args.custom_sections.split(',') if args.custom_sections else None
    
    if args.dry_run:
        print("Dry run mode - showing configuration:")
        print(f"  Version: {args.version}")
        print(f"  Repository: {args.repo or 'from config'}")
        print(f"  Audience: {args.audience}")
        print(f"  Commit source: {args.commit_source}")
        print(f"  Issue source: {args.issue_source}")
        print(f"  Release source: {args.release_source}")
        if args.from_tag:
            print(f"  From tag: {args.from_tag}")
        if args.since:
            print(f"  Since: {args.since}")
        if labels:
            print(f"  Labels: {labels}")
        if args.project_key:
            print(f"  JIRA project: {args.project_key}")
        if args.model:
            print(f"  LLM model: {args.model}")
        if args.publish:
            print(f"  Publishing to: {args.publish}")
        exit(0)
    
    # Run the enhanced generation
    result = asyncio.run(generate_enhanced_release_notes(
        version=args.version,
        repo=args.repo,
        audience=args.audience,
        from_tag=args.from_tag,
        since=args.since,
        commit_source=args.commit_source,
        issue_source=args.issue_source,
        release_source=args.release_source if not args.skip_previous_releases else 'none',
        milestone=args.milestone,
        labels=labels,
        project_key=args.project_key,
        json_file=args.json_file,
        model=args.model,
        temperature=args.temperature,
        template=args.template,
        custom_sections=custom_sections,
        publish_platforms=args.publish,
        output_file=args.output
    ))
    
    if result['status'] == 'success':
        print(f'\n[SUCCESS] Release notes generation completed successfully!')
        print(f'Output file: {result["output_file"]}')
        
        if result.get('publishing', {}).get('published_to'):
            print(f'Published to: {", ".join(result["publishing"]["published_to"])}')
        
    else:
        print(f'\n[ERROR] Generation failed: {result["error"]}')
        exit(1)