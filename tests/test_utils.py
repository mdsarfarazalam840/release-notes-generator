from src.utils import load_config

def test_load_config():
    cfg = load_config('config.yaml')
    assert 'repo' in cfg
    assert 'llm' in cfg
