import os
import yaml
from dotenv import load_dotenv

# Load .env first (for defaults), then .env.local (for actual credentials) - this way .env.local overrides .env
from pathlib import Path

def find_env_file(filename):
    """Find .env file in current directory or parent directories"""
    current = Path.cwd()
    while current != current.parent:
        env_file = current / filename
        if env_file.exists():
            return str(env_file)
        current = current.parent
    return filename  # fallback to original

def reload_env():
    """Force reload environment variables"""
    env_file = find_env_file('.env')
    env_local_file = find_env_file('.env.local')
    load_dotenv(env_file)
    load_dotenv(env_local_file, override=True)

# Try to find .env files in project root
env_file = find_env_file('.env')
env_local_file = find_env_file('.env.local')

load_dotenv(env_file)
load_dotenv(env_local_file, override=True)

def load_config(path='config.yaml'):
    from pathlib import Path
    
    # If path is relative, look for it in the project root
    config_path = Path(path)
    if not config_path.is_absolute() and not config_path.exists():
        # Try to find config.yaml in parent directories
        current = Path(__file__).parent
        while current != current.parent:
            config_candidate = current / path
            if config_candidate.exists():
                config_path = config_candidate
                break
            current = current.parent
    
    with open(config_path) as f:
        return yaml.safe_load(f)

def env(key, default=None):
    return os.getenv(key, default)
