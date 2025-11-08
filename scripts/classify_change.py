"""Simple rule-based classifier for commit messages."""
import re
from typing import Literal

def classify_commit(subject: str) -> Literal['feature','bug','docs','chore','refactor','unknown']:
    s = subject.lower()
    if re.search(r'\bfeat\b|feature|add ', s):
        return 'feature'
    if re.search(r'\bfix\b|bugfix|patch', s):
        return 'bug'
    if re.search(r'doc|readme|changelog', s):
        return 'docs'
    if re.search(r'refactor|cleanup', s):
        return 'refactor'
    return 'unknown'
