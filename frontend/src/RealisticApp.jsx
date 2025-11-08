import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000'

function RealisticApp() {
  // State management
  const [config, setConfig] = useState({})
  const [availableModels, setAvailableModels] = useState([])
  const [availableVersions, setAvailableVersions] = useState([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState('')
  const [currentModel, setCurrentModel] = useState('')
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState(null)
  
  // Form state - simplified
  const [formData, setFormData] = useState({
    version: '',
    repo: '',
    audience: 'users',
    model: '',
    publish_confluence: false,
    publish_github: false,
    publish_slack: false
  })

  // Load initial data
  useEffect(() => {
    loadConfig()
    loadAvailableModels()
    loadAvailableVersions()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/config`)
      const data = await response.json()
      setConfig(data)
      
      // Set default values
      if (data.llm_model && !formData.model) {
        setFormData(prev => ({ ...prev, model: data.llm_model }))
      }
      if (data.repo && !formData.repo) {
        setFormData(prev => ({ ...prev, repo: data.repo }))
      }
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/models/openrouter`)
      const data = await response.json()
      setAvailableModels(data.models || [])
      
      // Set first available model as default
      if (data.models && data.models.length > 0 && !formData.model) {
        setFormData(prev => ({ ...prev, model: data.models[0].id }))
      }
    } catch (error) {
      console.error('Error loading models:', error)
      // Fallback to free options
      setAvailableModels([
        { id: 'template-basic', name: 'Template-Based (No AI)', pricing: 'FREE' },
        { id: 'ollama/llama3.1', name: 'Local Ollama (if installed)', pricing: 'FREE' },
        { id: 'meta-llama/llama-3.1-8b-instruct:free', name: 'LLaMA 3.1 8B', pricing: 'OpenRouter Free' }
      ])
    }
  }

  const loadAvailableVersions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/versions`)
      const data = await response.json()
      setAvailableVersions(data.versions || [])
      
      // Set suggested next version as default
      if (data.suggested_next && !formData.version) {
        setFormData(prev => ({ ...prev, version: data.suggested_next }))
      }
    } catch (error) {
      console.error('Error loading versions:', error)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const generateReleaseNotes = async () => {
    if (!formData.version) {
      alert('Please select or enter a version')
      return
    }

    if (!formData.model) {
      alert('Please select an LLM model')
      return
    }

    setIsGenerating(true)
    setResults(null)
    setProgress(0)
    setCurrentModel(formData.model)

    // Simulate realistic progress steps
    const steps = [
      { step: 'Initializing...', percent: 10 },
      { step: 'Fetching commits from repository...', percent: 25 },
      { step: 'Loading issues and pull requests...', percent: 40 },
      { step: 'Analyzing previous releases...', percent: 55 },
      { step: `Generating with ${getModelDisplayName(formData.model)}...`, percent: 70 },
      { step: 'Structuring content...', percent: 85 },
      { step: 'Finalizing release notes...', percent: 95 }
    ]

    try {
      // Animate through steps
      for (let i = 0; i < steps.length; i++) {
        setCurrentStep(steps[i].step)
        setProgress(steps[i].percent)
        await new Promise(resolve => setTimeout(resolve, 800))
      }

      // Make actual API call
      const response = await fetch(`${API_BASE}/api/generate/enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version: formData.version,
          audience: formData.audience,
          model: formData.model,
          commit_source: 'auto',
          issue_source: 'github',
          publish_confluence: formData.publish_confluence
        })
      })

      const data = await response.json()

      if (response.ok) {
        setResults(data)
        setCurrentStep('✅ Generation completed successfully!')
        setProgress(100)
        
        // Auto-scroll to results section with visual highlight
        setTimeout(() => {
          const resultsElement = document.getElementById('results-section')
          if (resultsElement) {
            // Add a subtle animation to draw attention
            resultsElement.style.animation = 'slideInUp 0.5s ease-out'
            
            // Scroll to results
            resultsElement.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center' 
            })
            
            // Add a brief highlight effect
            setTimeout(() => {
              resultsElement.style.boxShadow = '0 4px 20px rgba(16, 185, 129, 0.3)'
              setTimeout(() => {
                resultsElement.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'
              }, 2000)
            }, 600)
          }
        }, 500)
        
        // Clear progress after delay
        setTimeout(() => {
          setCurrentStep('')
          setProgress(0)
        }, 3000)
      } else {
        throw new Error(data.error || 'Generation failed')
      }
    } catch (error) {
      setCurrentStep(`❌ Error: ${error.message}`)
      setTimeout(() => {
        setCurrentStep('')
        setProgress(0)
      }, 5000)
    } finally {
      setIsGenerating(false)
    }
  }

  const getModelDisplayName = (modelId) => {
    const model = availableModels.find(m => m.id === modelId)
    return model ? model.name : modelId
  }

  const testConfluenceConnection = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/confluence/test`, { method: 'POST' })
      const data = await response.json()
      
      if (response.ok) {
        alert('✅ Confluence connection successful!')
      } else {
        alert(`❌ Confluence connection failed: ${data.error}`)
      }
    } catch (error) {
      alert(`❌ Confluence connection failed: ${error.message}`)
    }
  }

  return (
    <div style={{ 
      fontFamily: 'system-ui, -apple-system, sans-serif', 
      maxWidth: '900px', 
      margin: '0 auto', 
      padding: '20px',
      backgroundColor: '#f8fafc',
      minHeight: '100vh'
    }}>
      {/* Add CSS animations */}
      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.02); }
          100% { transform: scale(1); }
        }
        
        .results-highlight {
          animation: pulse 0.6s ease-in-out;
        }
      `}</style>
      {/* Header */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '40px',
        padding: '30px',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ 
          color: '#1e40af', 
          margin: '0 0 10px 0',
          fontSize: '2.5rem',
          fontWeight: '700'
        }}>
          🚀 Release Notes Generator
        </h1>
        <p style={{ 
          color: '#64748b', 
          margin: 0,
          fontSize: '1.1rem'
        }}>
          AI-powered release notes for {config.repo || 'your repository'}
        </p>
      </div>

      {/* Main Form */}
      <div style={{ 
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '30px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        {/* Repository Selection */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontWeight: '600',
            color: '#374151',
            fontSize: '1rem'
          }}>
            📁 Repository
          </label>
          <input
            type="text"
            value={formData.repo}
            onChange={(e) => handleInputChange('repo', e.target.value)}
            placeholder="e.g., username/repository-name"
            style={{ 
              width: '100%',
              padding: '12px', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '1rem',
              backgroundColor: '#f9fafb'
            }}
          />
        </div>

        {/* Version Selection */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontWeight: '600',
            color: '#374151',
            fontSize: '1rem'
          }}>
            📦 Release Version
          </label>
          
          {availableVersions.length > 0 ? (
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <select
                value={formData.version}
                onChange={(e) => handleInputChange('version', e.target.value)}
                style={{ 
                  flex: 1,
                  padding: '12px', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '8px',
                  fontSize: '1rem',
                  backgroundColor: '#f9fafb'
                }}
              >
                <option value="">Select or enter version...</option>
                {availableVersions.map(version => (
                  <option key={version.tag} value={version.tag}>
                    {version.tag} (Next: {version.suggested})
                  </option>
                ))}
              </select>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => handleInputChange('version', e.target.value)}
                placeholder="or type custom version"
                style={{ 
                  flex: 1,
                  padding: '12px', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '8px',
                  fontSize: '1rem'
                }}
              />
            </div>
          ) : (
            <input
              type="text"
              value={formData.version}
              onChange={(e) => handleInputChange('version', e.target.value)}
              placeholder="e.g., v1.2.3"
              style={{ 
                width: '100%',
                padding: '12px', 
                border: '2px solid #e5e7eb', 
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            />
          )}
        </div>

        {/* Audience Selection */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontWeight: '600',
            color: '#374151',
            fontSize: '1rem'
          }}>
            👥 Target Audience
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            {[
              { value: 'users', label: '👤 End Users', desc: 'User-friendly, benefit-focused' },
              { value: 'developers', label: '💻 Developers', desc: 'Technical details, code examples' },
              { value: 'managers', label: '📊 Stakeholders', desc: 'Business value, strategic impact' }
            ].map(option => (
              <label
                key={option.value}
                style={{
                  flex: 1,
                  padding: '15px',
                  border: formData.audience === option.value ? '2px solid #3b82f6' : '2px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: formData.audience === option.value ? '#eff6ff' : '#f9fafb',
                  textAlign: 'center',
                  transition: 'all 0.2s'
                }}
              >
                <input
                  type="radio"
                  name="audience"
                  value={option.value}
                  checked={formData.audience === option.value}
                  onChange={(e) => handleInputChange('audience', e.target.value)}
                  style={{ display: 'none' }}
                />
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>{option.label}</div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{option.desc}</div>
              </label>
            ))}
          </div>
        </div>

        {/* LLM Model Selection */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontWeight: '600',
            color: '#374151',
            fontSize: '1rem'
          }}>
            🤖 AI Model
          </label>
          <select
            value={formData.model}
            onChange={(e) => handleInputChange('model', e.target.value)}
            style={{ 
              width: '100%',
              padding: '12px', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '1rem',
              backgroundColor: '#f9fafb'
            }}
          >
            <option value="">Select AI model...</option>
            {availableModels.map(model => (
              <option key={model.id} value={model.id}>
                {model.name} {model.pricing && `(${model.pricing})`}
              </option>
            ))}
          </select>
        </div>

        {/* Publishing Options */}
        <div style={{ marginBottom: '25px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '12px', 
            fontWeight: '600',
            color: '#374151',
            fontSize: '1rem'
          }}>
            📤 Publishing Options
          </label>
          
          <div style={{ display: 'grid', gap: '12px' }}>
            {/* Confluence */}
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '12px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#f9fafb',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={formData.publish_confluence}
                onChange={(e) => handleInputChange('publish_confluence', e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '600', color: '#374151' }}>
                  📄 Confluence
                </div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  {config.confluence_configured ? 'Ready to publish' : 'Setup required'}
                </div>
              </div>
              {config.confluence_configured && (
                <button
                  type="button"
                  onClick={testConfluenceConnection}
                  style={{
                    padding: '4px 8px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    backgroundColor: 'white',
                    cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  Test
                </button>
              )}
            </label>

            {/* GitHub Releases */}
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '12px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#f9fafb',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={formData.publish_github}
                onChange={(e) => handleInputChange('publish_github', e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '600', color: '#374151' }}>
                  🐙 GitHub Releases
                </div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  {config.has_github_token ? 'Ready to publish' : 'GitHub token required'}
                </div>
              </div>
            </label>

            {/* Slack */}
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '12px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#f9fafb',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={formData.publish_slack}
                onChange={(e) => handleInputChange('publish_slack', e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '600', color: '#374151' }}>
                  💬 Slack
                </div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  Webhook URL required
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={generateReleaseNotes}
          disabled={isGenerating || !formData.version || !formData.model}
          style={{
            width: '100%',
            padding: '16px',
            backgroundColor: isGenerating ? '#9ca3af' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1.1rem',
            fontWeight: '600',
            cursor: isGenerating ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {isGenerating ? '⏳ Generating...' : '🚀 Generate Release Notes'}
        </button>
      </div>

      {/* Progress Display */}
      {(isGenerating || currentStep) && (
        <div style={{ 
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '25px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginBottom: '20px'
        }}>
          <div style={{ marginBottom: '15px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <span style={{ fontWeight: '600', color: '#374151' }}>{currentStep}</span>
              <span style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                {currentModel && `Using ${getModelDisplayName(currentModel)}`}
              </span>
            </div>
            <div style={{ 
              width: '100%', 
              height: '8px', 
              backgroundColor: '#e5e7eb', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: `${progress}%`, 
                height: '100%', 
                backgroundColor: '#3b82f6',
                transition: 'width 0.5s ease',
                borderRadius: '4px'
              }} />
            </div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div 
          id="results-section"
          style={{ 
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '25px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginTop: '20px',
            border: '2px solid #10b981',
            position: 'relative'
          }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: 0, color: '#374151' }}>
              ✅ Release Notes - {results.version}
            </h3>
            <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
              Generated with {getModelDisplayName(results.metadata.model)}
            </div>
          </div>
          
          <div style={{ 
            marginBottom: '15px', 
            padding: '12px', 
            backgroundColor: '#f0f9ff', 
            borderRadius: '6px',
            fontSize: '0.9rem'
          }}>
            <strong>Summary:</strong> {results.data_summary.commits_count} commits, {results.data_summary.issues_count} issues analyzed
            {results.confluence && !results.confluence.error && (
              <span style={{ marginLeft: '15px', color: '#059669' }}>
                📄 Published to Confluence
              </span>
            )}
          </div>

          <div style={{
            backgroundColor: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '8px',
            padding: '20px',
            maxHeight: '600px',
            overflow: 'auto',
            fontFamily: 'ui-monospace, monospace',
            fontSize: '0.9rem',
            lineHeight: '1.6',
            whiteSpace: 'pre-wrap'
          }}>
            {results.raw_output}
          </div>

          {/* Enhanced Publishing Results Display */}
          {results.publishing && results.publishing.published_to && results.publishing.published_to.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#059669', display: 'flex', alignItems: 'center', gap: '8px' }}>
                ✅ Publishing Results
              </h4>
              
              {results.publishing.published_to.map(platform => (
                <div key={platform} style={{ 
                  marginBottom: '10px', 
                  padding: '15px', 
                  backgroundColor: '#ecfdf5', 
                  border: '2px solid #10b981', 
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: '0 2px 4px rgba(16, 185, 129, 0.1)'
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '1.2rem' }}>
                        {platform === 'confluence' && '📄'}
                        {platform === 'github' && '🐙'}
                        {platform === 'slack' && '💬'}
                      </span>
                      <strong style={{ color: '#059669', fontSize: '1rem' }}>
                        {platform === 'confluence' && 'Confluence'}
                        {platform === 'github' && 'GitHub'}
                        {platform === 'slack' && 'Slack'}
                      </strong>
                    </div>
                    
                    <div style={{ fontSize: '0.9rem', color: '#047857', marginBottom: '8px' }}>
                      ✅ Successfully published to {platform}
                    </div>
                    
                    {/* Confluence specific details */}
                    {platform === 'confluence' && results.publishing.success?.confluence && (
                      <div style={{ fontSize: '0.85rem', color: '#065f46', lineHeight: '1.4' }}>
                        <div style={{ marginBottom: '3px' }}>
                          <strong>📄 Page:</strong> {results.publishing.success.confluence.title}
                        </div>
                        <div style={{ marginBottom: '3px' }}>
                          <strong>🆔 Page ID:</strong> {results.publishing.success.confluence.page_id}
                        </div>
                        <div style={{ marginBottom: '3px' }}>
                          <strong>📁 Space:</strong> {results.publishing.success.confluence.space} (My first space)
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* View button */}
                  {platform === 'confluence' && results.publishing.success?.confluence?.url && (
                    <a 
                      href={results.publishing.success.confluence.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        padding: '10px 20px',
                        backgroundColor: '#059669',
                        color: 'white',
                        textDecoration: 'none',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontWeight: 'bold',
                        transition: 'background-color 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      🔗 View in Confluence
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Publishing Errors */}
          {results.publishing && results.publishing.failed_to && results.publishing.failed_to.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#dc2626' }}>❌ Publishing Errors</h4>
              
              {results.publishing.failed_to.map(platform => (
                <div key={platform} style={{ 
                  marginBottom: '10px', 
                  padding: '12px', 
                  backgroundColor: '#fef2f2', 
                  border: '1px solid #fecaca', 
                  borderRadius: '6px',
                  color: '#dc2626'
                }}>
                  <strong>{platform}:</strong> {results.publishing.errors?.[platform] || 'Publishing failed'}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Status Footer */}
      <div style={{ 
        marginTop: '30px',
        textAlign: 'center',
        fontSize: '0.85rem',
        color: '#6b7280'
      }}>
        <div>
          Repository: {config.repo || 'Not configured'} • 
          GitHub: {config.has_github_token ? ' ✅' : ' ❌'} • 
          Confluence: {config.confluence_configured ? ' ✅' : ' ❌'}
        </div>
      </div>
    </div>
  )
}

export default RealisticApp