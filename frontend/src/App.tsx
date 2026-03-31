import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Debate {
  id: string
  user_id: string
  username: string
  avatar_url: string
  title: string
  body: string
  tags: string[]
  status: string
  created_at: string
}

interface Suggestion {
  user_id: string
  display_name: string
  github_username: string
  avatar_url: string
  similarity: number
  reasons: string[]
}

interface User {
  id: string
  github_username: string
  display_name: string
  avatar_url: string
  email: string
  is_active: boolean
  affiliation: string
  languages: string[]
  topics: string[]
  created_at: string
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [debates, setDebates] = useState<Debate[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewDebate, setShowNewDebate] = useState(false)
  const [newDebate, setNewDebate] = useState({ title: '', body: '', tags: '' })
  const [authChecked, setAuthChecked] = useState(false)

  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        credentials: 'include'
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        fetchDebates()
        fetchSuggestions()
      }
    } catch (error) {
      console.error('Error checking auth:', error)
    } finally {
      setLoading(false)
      setAuthChecked(true)
    }
  }

  const fetchDebates = async () => {
    try {
      const response = await fetch(`${API_URL}/debates`)
      const data = await response.json()
      setDebates(data)
    } catch (error) {
      console.error('Error fetching debates:', error)
    }
  }

  const fetchSuggestions = async () => {
    try {
      const response = await fetch(`${API_URL}/suggestions`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setSuggestions(data)
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error)
    }
  }

  const handleLogin = () => {
    window.location.href = `${API_URL}/auth/github`
  }

  const handleCreateDebate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch(`${API_URL}/debates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          title: newDebate.title,
          body: newDebate.body,
          tags: newDebate.tags.split(',').map(t => t.trim()).filter(t => t)
        })
      })
      if (response.ok) {
        setShowNewDebate(false)
        setNewDebate({ title: '', body: '', tags: '' })
        fetchDebates()
        fetchSuggestions()
        if (user && !user.is_active) {
          checkAuth()
        }
      }
    } catch (error) {
      console.error('Error creating debate:', error)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <p>Cargando...</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <h1>GitHub-Mini</h1>
        <p style={{ marginTop: '1rem', marginBottom: '2rem', color: '#8b949e' }}>
          GitHub es donde subís código. GitHub-Mini es donde encontrás a quienes debatirlo.
        </p>
        <button className="btn" onClick={handleLogin}>
          Entrar con GitHub
        </button>
      </div>
    )
  }

  if (!user.is_active) {
    return (
      <div className="container" style={{ maxWidth: '800px', paddingTop: '2rem' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>Bienvenido a GitHub-Mini</h2>
          <p style={{ marginTop: '1rem', color: '#8b949e' }}>
            Para activar tu cuenta, publicá tu primer debate.
          </p>
          <button className="btn" style={{ marginTop: '1rem' }} onClick={() => setShowNewDebate(true)}>
            Publicar mi primer debate
          </button>
        </div>

        {showNewDebate && (
          <div className="card" style={{ marginTop: '1rem' }}>
            <h3>Nuevo debate</h3>
            <form onSubmit={handleCreateDebate}>
              <input
                type="text"
                placeholder="Título"
                value={newDebate.title}
                onChange={(e) => setNewDebate({ ...newDebate, title: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  marginBottom: '1rem',
                  backgroundColor: '#0d1117',
                  border: '1px solid #30363d',
                  borderRadius: '6px',
                  color: '#e6edf3'
                }}
                required
              />
              <textarea
                placeholder="Escribí tu debate..."
                value={newDebate.body}
                onChange={(e) => setNewDebate({ ...newDebate, body: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  marginBottom: '1rem',
                  backgroundColor: '#0d1117',
                  border: '1px solid #30363d',
                  borderRadius: '6px',
                  color: '#e6edf3',
                  minHeight: '150px'
                }}
                required
              />
              <input
                type="text"
                placeholder="Etiquetas (separadas por coma)"
                value={newDebate.tags}
                onChange={(e) => setNewDebate({ ...newDebate, tags: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  marginBottom: '1rem',
                  backgroundColor: '#0d1117',
                  border: '1px solid #30363d',
                  borderRadius: '6px',
                  color: '#e6edf3'
                }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button type="submit" className="btn">Publicar</button>
                <button type="button" className="btn btn-outline" onClick={() => setShowNewDebate(false)}>
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="container" style={{ paddingTop: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <img src={user.avatar_url} alt={user.github_username} className="avatar" style={{ width: '48px', height: '48px' }} />
          <div>
            <h2>{user.display_name || user.github_username}</h2>
            <p style={{ fontSize: '0.875rem', color: '#8b949e' }}>@{user.github_username}</p>
          </div>
        </div>
        <button className="btn" onClick={() => setShowNewDebate(true)}>Nuevo debate</button>
      </div>

      {showNewDebate && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3>Nuevo debate</h3>
          <form onSubmit={handleCreateDebate}>
            <input
              type="text"
              placeholder="Título"
              value={newDebate.title}
              onChange={(e) => setNewDebate({ ...newDebate, title: e.target.value })}
              style={{
                width: '100%',
                padding: '0.5rem',
                marginBottom: '1rem',
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                color: '#e6edf3'
              }}
              required
            />
            <textarea
              placeholder="Escribí tu debate..."
              value={newDebate.body}
              onChange={(e) => setNewDebate({ ...newDebate, body: e.target.value })}
              style={{
                width: '100%',
                padding: '0.5rem',
                marginBottom: '1rem',
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                color: '#e6edf3',
                minHeight: '150px'
              }}
              required
            />
            <input
              type="text"
              placeholder="Etiquetas (separadas por coma)"
              value={newDebate.tags}
              onChange={(e) => setNewDebate({ ...newDebate, tags: e.target.value })}
              style={{
                width: '100%',
                padding: '0.5rem',
                marginBottom: '1rem',
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                color: '#e6edf3'
              }}
            />
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="submit" className="btn">Publicar</button>
              <button type="button" className="btn btn-outline" onClick={() => setShowNewDebate(false)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem' }}>
        <div>
          <h3 style={{ marginBottom: '1rem' }}>Debates recientes</h3>
          {debates.length === 0 ? (
            <p style={{ color: '#8b949e' }}>No hay debates aún. ¡Sé el primero en publicar!</p>
          ) : (
            debates.map((debate) => (
              <div key={debate.id} className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <img src={debate.avatar_url} alt={debate.username} className="avatar" style={{ width: '32px', height: '32px' }} />
                  <span style={{ fontWeight: 'bold' }}>{debate.username}</span>
                  <span style={{ fontSize: '0.75rem', color: '#8b949e' }}>
                    {new Date(debate.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h4 style={{ marginBottom: '0.5rem' }}>{debate.title}</h4>
                <p style={{ color: '#e6edf3', marginBottom: '0.5rem' }}>{debate.body}</p>
                {debate.tags.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {debate.tags.map((tag) => (
                      <span key={tag} style={{ fontSize: '0.75rem', color: '#2f81f7' }}>#{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div>
          <h3 style={{ marginBottom: '1rem' }}>Personas para conectar</h3>
          {suggestions.length === 0 ? (
            <p style={{ color: '#8b949e' }}>Aún no hay sugerencias. Publicá debates para mejorar tu perfil.</p>
          ) : (
            suggestions.map((suggestion) => (
              <div key={suggestion.user_id} className="card" style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <img src={suggestion.avatar_url} alt={suggestion.github_username} className="avatar" style={{ width: '32px', height: '32px' }} />
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{suggestion.display_name || suggestion.github_username}</div>
                    <div style={{ fontSize: '0.75rem', color: '#8b949e' }}>@{suggestion.github_username}</div>
                  </div>
                </div>
                {suggestion.reasons.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: '#8b949e', marginTop: '0.5rem' }}>
                    {suggestion.reasons.map((reason, i) => (
                      <div key={i}>• {reason}</div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default App
