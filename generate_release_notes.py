#!/usr/bin/env python3
"""
Simplified release notes generator script
Automatically handles authentication and paths
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Generate release notes with GitHub authentication')
    parser.add_argument('--version', required=True, help='Release version (e.g., v1.2.0)')
    parser.add_argument('--enhanced', action='store_true', help='Use enhanced generator with more features')
    parser.add_argument('--use-github', action='store_true', help='Fetch commits from GitHub API instead of local git')
    parser.add_argument('--audience', choices=['users', 'developers', 'managers'], default='users', help='Target audience')
    parser.add_argument('--publish-confluence', action='store_true', help='Publish to Confluence after generation')
    
    args = parser.parse_args()
    
    print(f"🚀 Generating release notes for {args.version}")
    print("📋 Configuration:")
    print(f"   - Generator: {'Enhanced' if args.enhanced else 'Standard'}")
    print(f"   - Source: {'GitHub API' if args.use_github else 'Local Git'}")
    print(f"   - Audience: {args.audience}")
    print(f"   - Publish to Confluence: {'Yes' if args.publish_confluence else 'No'}")
    print()
    
    try:
        if args.enhanced:
            # Use enhanced generator
            cmd = [
                sys.executable, '-m', 'src.enhanced_generate_notes',
                '--version', args.version,
                '--audience', args.audience,
                '--commit-source', 'github' if args.use_github else 'local'
            ]
            if args.publish_confluence:
                cmd.extend(['--publish', 'confluence'])
        else:
            # Use standard generator
            cmd = [
                sys.executable, '-m', 'src.generate_notes',
                '--version', args.version,
                '--audience', args.audience
            ]
            if args.use_github:
                cmd.append('--use-github')
            if args.publish_confluence:
                cmd.append('--publish-confluence')
        
        import subprocess
        result = subprocess.run(cmd, check=True)
        
        print("\n✅ Release notes generated successfully!")
        print(f"📄 Check the examples/release_{args.version}.md file")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error generating release notes: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()