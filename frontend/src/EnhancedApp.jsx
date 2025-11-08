import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000'

function EnhancedApp() {
  // Configuration state
  const [config, setConfig] = useState({})
  const [availableModels, setAvailableModels] = useState({})
  const [publishingPlatforms, setPublishingPlatforms] = useState({})
  
  // Form state
  const [formData, setFormData] = useState({
    version: '',
    repo: '',
    audience: 'users',
    commit_source: 'auto',
    issue_source: 'github',
    release_source: 'auto',
    from_tag: '',
    since: '',
    milestone: '',
    labels: '',
    project_key: '',
    model: '',
    temperature: 0.0,
    template: '',
    custom_sections: '',
    publish_confluence: false
  })
  
  // UI state
  const [activeTab, setActiveTab] = useState('generate')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState({ step: '', percent: 0 })
  const [results, setResults] = useState(null)
  const [releases, setReleases] = useState([])
  const [uploadedFile, setUploadedFile] = useState(null)
  
  // Load initial configuration
  useEffect(() => {
    loadConfig()
    loadAvailableModels()
    loadPublishingPlatforms()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/config`)
      const data = await response.json()
      setConfig(data)
      setFormData(prev => ({
        ...prev,
        repo: data.repo || '',
        model: data.llm_model || ''
      }))
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/models`)
      const data = await response.json()
      setAvailableModels(data)
    } catch (error) {
      console.error('Error loading models:', error)
    }
  }

  const loadPublishingPlatforms = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/publish/platforms`)
      const data = await response.json()
      setPublishingPlatforms(data)
    } catch (error) {
      console.error('Error loading publishing platforms:', error)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const testDataSource = async (sourceType) => {
    setIsLoading(true)
    setProgress({ step: `Testing ${sourceType} connection...`, percent: 50 })
    
    try {
      let endpoint = ''
      let params = new URLSearchParams({
        repo: formData.repo,
        since: formData.since || undefined
      })

      if (sourceType === 'commits') {
        endpoint = '/api/data/commits'
        params.append('source', formData.commit_source)
        params.append('from_tag', formData.from_tag || '')
      } else if (sourceType === 'issues') {
        endpoint = '/api/data/issues'
        params.append('source', formData.issue_source)
        params.append('milestone', formData.milestone || '')
        params.append('labels', formData.labels || '')
        params.append('project_key', formData.project_key || '')
      } else if (sourceType === 'releases') {
        endpoint = '/api/data/releases'
        params.append('source', formData.release_source)
        params.append('current_version', formData.version || '')
      }

      const response = await fetch(`${API_BASE}${endpoint}?${params}`)
      const data = await response.json()
      
      if (response.ok) {
        setProgress({ step: `✓ Found ${data.count} ${sourceType}`, percent: 100 })
        setTimeout(() => setProgress({ step: '', percent: 0 }), 2000)
        
        // Store data for preview
        if (sourceType === 'releases') {
          setReleases(data.releases || [])
        }
      } else {
        throw new Error(data.error || 'Test failed')
      }
    } catch (error) {
      setProgress({ step: `✗ Error: ${error.message}`, percent: 0 })
      setTimeout(() => setProgress({ step: '', percent: 0 }), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formDataUpload = new FormData()
    formDataUpload.append('file', file)

    setIsLoading(true)
    setProgress({ step: 'Uploading file...', percent: 50 })

    try {
      const response = await fetch(`${API_BASE}/api/upload/issues`, {
        method: 'POST',
        body: formDataUpload
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setUploadedFile(data)
        setFormData(prev => ({ ...prev, json_file: data.path }))
        setProgress({ step: `✓ Uploaded ${data.issues_count} issues`, percent: 100 })
        setTimeout(() => setProgress({ step: '', percent: 0 }), 2000)
      } else {
        throw new Error(data.error || 'Upload failed')
      }
    } catch (error) {
      setProgress({ step: `✗ Upload error: ${error.message}`, percent: 0 })
      setTimeout(() => setProgress({ step: '', percent: 0 }), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  const generateReleaseNotes = async () => {
    if (!formData.version) {
      alert('Please enter a version number')
      return
    }

    setIsLoading(true)
    setResults(null)

    // Simulate progress steps
    const steps = [
      'Validating configuration...',
      'Fetching commits...',
      'Fetching issues...',
      'Loading previous releases...',
      'Generating with LLM...',
      'Saving results...'
    ]

    try {
      for (let i = 0; i < steps.length - 1; i++) {
        setProgress({ step: steps[i], percent: (i + 1) * 16 })
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      setProgress({ step: steps[steps.length - 1], percent: 90 })

      const response = await fetch(`${API_BASE}/api/generate/enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          labels: formData.labels ? formData.labels.split(',').map(l => l.trim()) : [],
          custom_sections: formData.custom_sections ? formData.custom_sections.split(',').map(s => s.trim()) : []
        })
      })

      const data = await response.json()

      if (response.ok) {
        setResults(data)
        setProgress({ step: '✓ Generation completed!', percent: 100 })
        setTimeout(() => setProgress({ step: '', percent: 0 }), 2000)
      } else {
        throw new Error(data.error || 'Generation failed')
      }
    } catch (error) {
      setProgress({ step: `✗ Error: ${error.message}`, percent: 0 })
      setTimeout(() => setProgress({ step: '', percent: 0 }), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  const testModel = async () => {
    if (!formData.model) {
      alert('Please select a model first')
      return
    }

    setIsLoading(true)
    setProgress({ step: 'Testing model connection...', percent: 50 })

    try {
      const response = await fetch(`${API_BASE}/api/models/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: formData.model })
      })

      const data = await response.json()

      if (response.ok) {
        setProgress({ step: `✓ Model working: "${data.response}"`, percent: 100 })
        setTimeout(() => setProgress({ step: '', percent: 0 }), 3000)
      } else {
        throw new Error(data.error || 'Model test failed')
      }
    } catch (error) {
      setProgress({ step: `✗ Model error: ${error.message}`, percent: 0 })
      setTimeout(() => setProgress({ step: '', percent: 0 }), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', margin: '20px', maxWidth: '1200px' }}>
      <h1 style={{ color: '#2563eb', marginBottom: '30px' }}>
        🚀 Enhanced Release Notes Generator
      </h1>

      {/* Tab Navigation */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #e5e7eb' }}>
        {['generate', 'configure', 'templates'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              marginRight: '10px',
              border: 'none',
              background: activeTab === tab ? '#2563eb' : 'transparent',
              color: activeTab === tab ? 'white' : '#374151',
              borderRadius: '8px 8px 0 0',
              cursor: 'pointer',
              textTransform: 'capitalize',
              fontWeight: activeTab === tab ? 'bold' : 'normal'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Progress Bar */}
      {progress.step && (
        <div style={{ 
          marginBottom: '20px', 
          padding: '15px', 
          background: '#f3f4f6', 
          borderRadius: '8px',
          border: '1px solid #d1d5db'
        }}>
          <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>{progress.step}</div>
          <div style={{ 
            width: '100%', 
            height: '6px', 
            background: '#e5e7eb', 
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{ 
              width: `${progress.percent}%`, 
              height: '100%', 
              background: '#10b981',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      )}

      {/* Generate Tab */}
      {activeTab === 'generate' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            {/* Basic Configuration */}
            <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
              <h3 style={{ marginTop: 0, color: '#374151' }}>📋 Basic Configuration</h3>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Version *
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => handleInputChange('version', e.target.value)}
                  placeholder="e.g., v1.2.3"
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Repository
                </label>
                <input
                  type="text"
                  value={formData.repo}
                  onChange={(e) => handleInputChange('repo', e.target.value)}
                  placeholder="owner/repository"
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Audience
                </label>
                <select
                  value={formData.audience}
                  onChange={(e) => handleInputChange('audience', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value="users">👥 End Users</option>
                  <option value="developers">💻 Developers</option>
                  <option value="managers">📊 Managers</option>
                </select>
              </div>
            </div>

            {/* Data Sources */}
            <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
              <h3 style={{ marginTop: 0, color: '#374151' }}>📊 Data Sources</h3>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Commits Source
                  <button
                    onClick={() => testDataSource('commits')}
                    disabled={isLoading}
                    style={{
                      marginLeft: '10px',
                      padding: '2px 8px',
                      fontSize: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      background: '#f9fafb',
                      cursor: 'pointer'
                    }}
                  >
                    Test
                  </button>
                </label>
                <select
                  value={formData.commit_source}
                  onChange={(e) => handleInputChange('commit_source', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value="auto">🤖 Auto-detect</option>
                  <option value="local">📂 Local Git</option>
                  <option value="github">🐙 GitHub API</option>
                </select>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Issues Source
                  <button
                    onClick={() => testDataSource('issues')}
                    disabled={isLoading}
                    style={{
                      marginLeft: '10px',
                      padding: '2px 8px',
                      fontSize: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      background: '#f9fafb',
                      cursor: 'pointer'
                    }}
                  >
                    Test
                  </button>
                </label>
                <select
                  value={formData.issue_source}
                  onChange={(e) => handleInputChange('issue_source', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value="github">🐙 GitHub Issues</option>
                  <option value="jira">🎫 JIRA</option>
                  <option value="json">📄 JSON Upload</option>
                </select>
              </div>

              {formData.issue_source === 'json' && (
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    Upload Issues JSON
                  </label>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                  {uploadedFile && (
                    <div style={{ marginTop: '5px', fontSize: '12px', color: '#10b981' }}>
                      ✓ Uploaded: {uploadedFile.issues_count} issues
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Filters and LLM Configuration */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            {/* Filters */}
            <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
              <h3 style={{ marginTop: 0, color: '#374151' }}>🔍 Filters</h3>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  From Tag
                </label>
                <input
                  type="text"
                  value={formData.from_tag}
                  onChange={(e) => handleInputChange('from_tag', e.target.value)}
                  placeholder="v1.2.0"
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Since Date
                </label>
                <input
                  type="date"
                  value={formData.since}
                  onChange={(e) => handleInputChange('since', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Labels (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.labels}
                  onChange={(e) => handleInputChange('labels', e.target.value)}
                  placeholder="bug, feature, enhancement"
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>

              {formData.issue_source === 'jira' && (
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    JIRA Project Key
                  </label>
                  <input
                    type="text"
                    value={formData.project_key}
                    onChange={(e) => handleInputChange('project_key', e.target.value)}
                    placeholder="PROJ"
                    style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </div>
              )}
            </div>

            {/* LLM Configuration */}
            <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
              <h3 style={{ marginTop: 0, color: '#374151' }}>🤖 LLM Configuration</h3>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Model
                  <button
                    onClick={testModel}
                    disabled={isLoading || !formData.model}
                    style={{
                      marginLeft: '10px',
                      padding: '2px 8px',
                      fontSize: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      background: '#f9fafb',
                      cursor: 'pointer'
                    }}
                  >
                    Test
                  </button>
                </label>
                <select
                  value={formData.model}
                  onChange={(e) => handleInputChange('model', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value="">Select a model...</option>
                  {Object.entries(availableModels).map(([provider, models]) => (
                    <optgroup key={provider} label={provider.toUpperCase()}>
                      {models.map(model => (
                        <option key={model} value={model}>{model}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Temperature: {formData.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                  style={{ width: '100%' }}
                />
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  0 = Deterministic, 1 = Creative
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Custom Sections (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.custom_sections}
                  onChange={(e) => handleInputChange('custom_sections', e.target.value)}
                  placeholder="Security Updates, Performance"
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
              </div>
            </div>
          </div>

          {/* Publishing Options */}
          <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px', marginBottom: '20px' }}>
            <h3 style={{ marginTop: 0, color: '#374151' }}>📤 Publishing Options</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              {Object.entries(publishingPlatforms).map(([key, platform]) => (
                <label key={key} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    checked={formData[`publish_${key}`] || false}
                    onChange={(e) => handleInputChange(`publish_${key}`, e.target.checked)}
                    disabled={!platform.configured}
                  />
                  <span style={{ 
                    color: platform.configured ? '#374151' : '#9ca3af',
                    textDecoration: platform.configured ? 'none' : 'line-through'
                  }}>
                    {platform.name} {platform.configured ? '✓' : '✗'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={generateReleaseNotes}
            disabled={isLoading || !formData.version}
            style={{
              width: '100%',
              padding: '15px',
              background: isLoading ? '#9ca3af' : '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? '⏳ Generating...' : '🚀 Generate Release Notes'}
          </button>
        </div>
      )}

      {/* Configure Tab */}
      {activeTab === 'configure' && (
        <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, color: '#374151' }}>⚙️ Configuration</h3>
          
          <div style={{ marginBottom: '20px', padding: '15px', background: '#f3f4f6', borderRadius: '8px' }}>
            <h4>Current Status</h4>
            <ul style={{ margin: 0 }}>
              <li>GitHub Token: {config.has_github_token ? '✅ Configured' : '❌ Missing'}</li>
              <li>JIRA Config: {config.has_jira_config ? '✅ Configured' : '❌ Missing'}</li>
              <li>Confluence: {config.confluence_configured ? '✅ Configured' : '❌ Missing'}</li>
              <li>Default Model: {config.llm_model || 'Not set'}</li>
            </ul>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <h4>Environment Variables Required:</h4>
            <div style={{ fontFamily: 'monospace', fontSize: '14px', background: '#f8f9fa', padding: '10px', borderRadius: '4px' }}>
              <div>GITHUB_TOKEN=your_github_token</div>
              <div>OPENROUTER_API_KEY=your_openrouter_key</div>
              <div>JIRA_BASE_URL=https://yourcompany.atlassian.net</div>
              <div>JIRA_USERNAME=your_email@company.com</div>
              <div>JIRA_API_TOKEN=your_jira_token</div>
              <div>CONFLUENCE_BASE=https://yourcompany.atlassian.net</div>
              <div>CONFLUENCE_USER=your_email@company.com</div>
              <div>CONFLUENCE_API_TOKEN=your_confluence_token</div>
            </div>
          </div>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div style={{ padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, color: '#374151' }}>📝 Templates</h3>
          
          <div style={{ marginBottom: '20px' }}>
            <h4>Available Templates:</h4>
            <ul>
              <li><strong>Users Template:</strong> User-friendly language, focused on benefits</li>
              <li><strong>Developers Template:</strong> Technical details, API changes, code examples</li>
              <li><strong>Managers Template:</strong> Business value, strategic impact</li>
            </ul>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Select Template for Preview:
            </label>
            <select style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}>
              <option value="users">Users Template</option>
              <option value="developers">Developers Template</option>
              <option value="managers">Managers Template</option>
            </select>
          </div>

          <p style={{ color: '#6b7280', fontStyle: 'italic' }}>
            Template editing and preview functionality can be expanded here.
          </p>
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div style={{ marginTop: '30px', padding: '20px', border: '1px solid #d1d5db', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, color: '#374151' }}>
            ✅ Generated Release Notes - {results.version}
          </h3>
          
          <div style={{ marginBottom: '15px', padding: '10px', background: '#f0f9ff', borderRadius: '4px' }}>
            <strong>Summary:</strong> Generated {results.data_summary.commits_count} commits, 
            {results.data_summary.issues_count} issues, {results.data_summary.previous_releases_count} previous releases
          </div>

          <div style={{
            background: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '4px',
            padding: '15px',
            maxHeight: '500px',
            overflow: 'auto',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap'
          }}>
            {results.raw_output}
          </div>

          {results.confluence && results.confluence.error && (
            <div style={{ marginTop: '10px', padding: '10px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '4px', color: '#dc2626' }}>
              <strong>Confluence Error:</strong> {results.confluence.error}
            </div>
          )}

          {results.confluence && !results.confluence.error && (
            <div style={{ marginTop: '10px', padding: '10px', background: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '4px', color: '#1d4ed8' }}>
              <strong>Published to Confluence:</strong> <a href={results.confluence._links?.webui} target="_blank" rel="noopener noreferrer">View Page</a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EnhancedApp