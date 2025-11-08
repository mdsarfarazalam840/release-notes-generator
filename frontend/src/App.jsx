import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000';

export default function App(){
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [version, setVersion] = useState('v' + new Date().toISOString().slice(0,10));
  const [audience, setAudience] = useState('users');
  const [repo, setRepo] = useState('');
  const [fromTag, setFromTag] = useState('');
  const [releases, setReleases] = useState([]);
  const [loadingReleases, setLoadingReleases] = useState(false);
  const [info, setInfo] = useState('');
  const [configLoaded, setConfigLoaded] = useState(false);
  const [selectedTag, setSelectedTag] = useState('');
  const [publishConfluence, setPublishConfluence] = useState(false);
  const [confluenceLink, setConfluenceLink] = useState('');

  const fetchLatest = async () => {
    setLoading(true); setError(''); setInfo('');
    try {
      const res = await fetch(`${API_BASE}/api/latest`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });
      if (!res.ok) {
        if (res.status === 404) {
          setMarkdown('');
          return;
        }
        throw new Error('No notes found');
      }
      const data = await res.json();
      setMarkdown(data.content || '');
      setInfo('');
    } catch (e) {
      if (e.name === 'AbortError' || e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
        setError(`Cannot connect to backend at ${API_BASE}. Make sure the backend server is running.`);
      } else {
        setError(e.message);
      }
      setMarkdown('');
    } finally {
      setLoading(false);
    }
  };

  const fetchReleases = async () => {
    if (!repo) return;
    setLoadingReleases(true);
    setError(''); // Clear previous errors
    setInfo('Fetching releases...');
    try {
      const res = await fetch(`${API_BASE}/api/releases?repo=${encodeURIComponent(repo)}&limit=20`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(15000) // 15 second timeout
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 401) {
          throw new Error('GITHUB_TOKEN not set. Please set it in your environment or .env file');
        } else if (res.status === 400) {
          throw new Error(data?.error || 'Repository not specified');
        } else if (res.status === 500) {
          throw new Error(data?.error || 'Server error while fetching releases');
        }
        throw new Error(data?.error || `Failed to fetch releases (Status: ${res.status})`);
      }
      const data = await res.json();
      const releasesList = data.releases || [];
      setReleases(releasesList);
      setError('');
      if (releasesList.length === 0) {
        setInfo('No releases found for this repository yet.');
      } else {
        setInfo(`Fetched ${releasesList.length} releases from ${repo}.`);
      }
    } catch (e) {
      setInfo('');
      if (e.name === 'AbortError' || e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
        setError(`Cannot connect to backend at ${API_BASE}. Make sure the backend server is running on port 5000.`);
      } else {
        setError(`Failed to fetch releases: ${e.message}`);
      }
      setReleases([]); // Clear releases on error
    } finally {
      setLoadingReleases(false);
    }
  };

  const fetchReleaseByTag = async (tag) => {
    if (!tag) return;
    try {
      setLoading(true); setError('');
      const res = await fetch(`${API_BASE}/api/releases/${encodeURIComponent(tag)}`);
      if (!res.ok) {
        throw new Error('Unable to load release content');
      }
      const data = await res.json();
      setMarkdown(data.release?.content || '');
      setSelectedTag(tag);
      setInfo(`Loaded release ${tag}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const generate = async () => {
    if (!repo) {
      setError('Please enter a repository (e.g., owner/repo)');
      return;
    }
    setLoading(true); setError(''); setInfo(''); setConfluenceLink('');
    try {
      const payload = {
        version,
        audience,
        use_github: true,
        repo: repo,
        publish_confluence: publishConfluence
      };
      if (fromTag) {
        payload.from_tag = fromTag;
      }
      
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(300000) // 5 minute timeout for generation
      });
      
      // Check if response is JSON before parsing
      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(`Server returned non-JSON response: ${text.substring(0, 200)}`);
      }
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.message || data?.error || 'Generation failed');
      }
      
      if (data.status === 'ok') {
        // Update releases list
        if (Array.isArray(data.releases)) {
          setReleases(data.releases);
        } else {
          await fetchReleases();
        }
        
        // Fetch and display the newly generated release
        try {
          const releaseRes = await fetch(`${API_BASE}/api/releases/${encodeURIComponent(version)}?repo=${encodeURIComponent(repo)}`);
          if (releaseRes.ok) {
            const releaseData = await releaseRes.json();
            if (releaseData.release?.content) {
              setMarkdown(releaseData.release.content);
              setSelectedTag(version);
            }
          }
        } catch (e) {
          console.warn('Could not fetch generated release:', e);
          // Fallback to latest
          await fetchLatest();
        }
        
        // Check for Confluence link
        if (data.confluence && data.confluence._links && data.confluence._links.webui) {
          setConfluenceLink(data.confluence._links.webui);
          setInfo(`Generated release notes for ${version}. Published to Confluence.`);
        } else {
          setInfo(`Generated release notes for ${version}.`);
        }
      } else {
        throw new Error(data?.message || 'Generation failed');
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        setError('Request timed out. The generation is taking too long. Please try again.');
      } else if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
        setError(`Cannot connect to backend at ${API_BASE}. Make sure the backend server is running on port 5000.`);
      } else {
        setError(e.message);
      }
      setMarkdown('');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    // Test backend connection first
    fetch(`${API_BASE}/api/config`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000)
    })
      .then(res => {
        if (!res.ok) {
          throw new Error(`Backend returned status ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.repo && !repo) {
          setRepo(data.repo);
        }
        setConfigLoaded(true);
        fetchLatest();
      })
      .catch((e) => {
        setError(`Cannot connect to backend at ${API_BASE}. Make sure the backend server is running on port 5000.`);
        setConfigLoaded(true);
      });
  }, []);

  useEffect(() => {
    if (repo && configLoaded) {
      fetchReleases();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repo, configLoaded]);

  return (
    <div style={{padding:20,fontFamily:'Arial, sans-serif',maxWidth:1200,margin:'auto'}}>
      <h1>Release Notes Generator</h1>

      <div style={{display:'flex', flexDirection:'column', gap:12, marginBottom:20, padding:15, backgroundColor:'#f5f5f5', borderRadius:8}}>
        <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap'}}>
          <input 
            value={repo} 
            onChange={e=>setRepo(e.target.value)} 
            placeholder="Repository (e.g., owner/repo)" 
            style={{flex:1, minWidth:200, padding:8}}
          />
          <input 
            value={version} 
            onChange={e=>setVersion(e.target.value)} 
            placeholder="Version (e.g., v1.2.0)" 
            style={{width:150, padding:8}}
          />
          <select 
            value={audience} 
            onChange={e=>setAudience(e.target.value)}
            style={{padding:8}}
          >
            <option value="users">Users</option>
            <option value="developers">Developers</option>
            <option value="managers">Managers</option>
          </select>
          <button 
            onClick={fetchReleases} 
            disabled={loadingReleases || !repo}
            style={{padding:8, cursor: loadingReleases || !repo ? 'not-allowed' : 'pointer'}}
          >
            {loadingReleases ? 'Loading...' : 'Fetch Releases'}
          </button>
        </div>

        {releases.length > 0 && (
          <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap'}}>
            <label style={{fontWeight:'bold'}}>From Tag (optional):</label>
            <select 
              value={fromTag} 
              onChange={e=>setFromTag(e.target.value)}
              style={{flex:1, minWidth:200, padding:8}}
            >
              <option value="">-- Select previous release --</option>
              {releases.map(r => (
                <option key={r.tag_name} value={r.tag_name}>
                  {r.tag_name} {r.prerelease ? '(pre-release)' : ''} {r.draft ? '(draft)' : ''}
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap'}}>
          <label style={{display:'flex', alignItems:'center', gap:5, cursor:'pointer'}}>
            <input 
              type="checkbox" 
              checked={publishConfluence}
              onChange={e => setPublishConfluence(e.target.checked)}
              style={{cursor:'pointer'}}
            />
            <span style={{fontSize:'0.9em'}}>Publish to Confluence</span>
          </label>
          <button 
            onClick={generate} 
            disabled={loading || !repo}
            style={{padding:10, backgroundColor:'#007bff', color:'white', border:'none', borderRadius:4, cursor: loading || !repo ? 'not-allowed' : 'pointer'}}
          >
            {loading ? 'Generating...' : 'Generate Release Notes'}
          </button>
          <button 
            onClick={fetchLatest} 
            disabled={loading}
            style={{padding:10, backgroundColor:'#6c757d', color:'white', border:'none', borderRadius:4, cursor: loading ? 'not-allowed' : 'pointer'}}
          >
            Refresh Latest
          </button>
          {loading && <span>Loading...</span>}
          {error && <span style={{color:'red', flex:1}}>{error}</span>}
          {!error && info && <span style={{color:'#0d6efd', flex:1}}>{info}</span>}
        </div>
      </div>

      {releases.length > 0 ? (
        <div style={{marginBottom:20, padding:15, backgroundColor:'#f0f8ff', borderRadius:8}}>
          <h3 style={{marginTop:0}}>Available Releases ({releases.length})</h3>
          <div style={{maxHeight:200, overflowY:'auto'}}>
            {releases.map((r, idx) => (
              <div
                key={r.tag_name || idx}
                onClick={() => fetchReleaseByTag(r.tag_name)}
                style={{
                  padding:8,
                  marginBottom:8,
                  backgroundColor: (selectedTag === r.tag_name ? '#e1f0ff' : 'white'),
                  borderRadius:4,
                  border:'1px solid #ddd',
                  cursor:'pointer'
                }}
              >
                <div style={{display:'flex', alignItems:'center', gap:10}}>
                  <strong style={{color:'#007bff'}}>{r.tag_name || 'No tag'}</strong>
                  {r.name && <span>{r.name}</span>}
                  {r.prerelease && <span style={{color:'orange', fontSize:'0.85em'}}>(pre-release)</span>}
                  {r.draft && <span style={{color:'gray', fontSize:'0.85em'}}>(draft)</span>}
                </div>
                {r.published_at && (
                  <div style={{color:'#666', fontSize:'0.9em', marginTop:4}}>
                    Published: {new Date(r.published_at).toLocaleDateString()}
                  </div>
                )}
                {r.body && (
                  <div style={{marginTop:8, color:'#333', fontSize:'0.9em', maxHeight:60, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'pre-wrap'}}>
                    {r.body.substring(0, 150)}{r.body.length > 150 ? '...' : ''}
                  </div>
                )}
                {r.url && (
                  <a href={r.url} target="_blank" rel="noopener noreferrer" style={{color:'#007bff', fontSize:'0.85em', textDecoration:'none'}}>
                    View on GitHub →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : loadingReleases ? (
        <div style={{marginBottom:20, padding:15, backgroundColor:'#fff3cd', borderRadius:8}}>
          <div>Loading releases...</div>
        </div>
      ) : (!error && info ? (
        <div style={{marginBottom:20, padding:15, backgroundColor:'#e7f1ff', borderRadius:8}}>
          <div>{info}</div>
        </div>
      ) : null)}

      {confluenceLink && (
        <div style={{padding:15, backgroundColor:'#e7f3ff', border:'1px solid #4a90e2', borderRadius:8, marginBottom:20}}>
          <strong>Published to Confluence:</strong>{' '}
          <a href={confluenceLink} target="_blank" rel="noopener noreferrer" style={{color:'#007bff', textDecoration:'underline'}}>
            View Release Notes on Confluence
          </a>
        </div>
      )}

      <div style={{display:'flex',gap:20}}>
        <div style={{flex:1}}>
          <h3>Editor</h3>
          <textarea 
            value={markdown} 
            onChange={(e)=>setMarkdown(e.target.value)} 
            style={{width:'100%', height:500, padding:10, fontFamily:'monospace', fontSize:14, border:'1px solid #ddd', borderRadius:4}}
            placeholder="Release notes will appear here..."
          />
        </div>
        <div style={{flex:1, borderLeft:'1px solid #ddd', paddingLeft:20}}>
          <h3>Preview</h3>
          <div style={{height:500, overflowY:'auto', padding:10, backgroundColor:'#f9f9f9', borderRadius:4, whiteSpace:'pre-wrap', fontFamily:'monospace', fontSize:14}}>
            {markdown || <em style={{color:'#999'}}>No content to preview</em>}
          </div>
        </div>
      </div>
    </div>
  )
}
