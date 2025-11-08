from scripts.classify_change import classify_commit

def test_feature():
    assert classify_commit('feat: add new API') == 'feature'
    assert classify_commit('Add support for X') == 'feature'

def test_bug():
    assert classify_commit('fix: resolved crash') == 'bug'
    assert classify_commit('bugfix: handle null') == 'bug'

def test_docs():
    assert classify_commit('docs: update README') == 'docs'

def test_refactor():
    assert classify_commit('refactor: cleanup code') == 'refactor'

def test_unknown():
    assert classify_commit('chore: bump deps') == 'unknown'
