import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'
import rehypeRaw from 'rehype-raw'

interface QueryResponse {
  question: string
  sql_query: string
  answer: string
  steps: string[]
  raw_result?: string
  suggestions?: string[]
  anomalies?: {
    count: number
    message: string
    details: any[]
  }
  context_used?: boolean
  decomposition_plan?: string
  error?: string
  llm_mode?: string
  llm_fallback_reason?: string
}

interface TableData {
  headers: string[]
  rows: string[][]
}

interface ToastMessage {
  id: number
  message: string
  type: 'warning' | 'error' | 'success'
}

interface ChatSession {
  id: string
  title: string
  timestamp: number
  messages: Array<{role: string, content: any}>
}

function App() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState<Array<{role: string, content: any}>>([])
  const [loading, setLoading] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme')
    return (savedTheme === 'dark' || savedTheme === 'light') ? savedTheme : 'dark'
  })
  const [showNewChatButton, setShowNewChatButton] = useState(false)
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const chatEndRef = useRef<HTMLDivElement>(null)

  // API URL from environment variable (for deployment)
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  
  // Toast notification function
  const showToast = (message: string, type: 'warning' | 'error' | 'success' = 'warning') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 5000)
  }
  
  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  // Load chat sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('chat_sessions')
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions)
        setChatSessions(parsed)
        // Load the most recent session
        if (parsed.length > 0) {
          const recent = parsed[0]
          setHistory(recent.messages)
          setCurrentSessionId(recent.id)
          setShowNewChatButton(true)
        }
      } catch (e) {
        console.error('Error loading chat sessions:', e)
      }
    }
  }, [])

  // Save current session whenever history changes
  useEffect(() => {
    if (history.length > 0) {
      const title = history[0]?.role === 'user' 
        ? history[0].content.substring(0, 50) 
        : 'New Conversation'
      
      const session: ChatSession = {
        id: currentSessionId || Date.now().toString(),
        title,
        timestamp: Date.now(),
        messages: history
      }
      
      // Update or add session
      setChatSessions(prev => {
        const existing = prev.findIndex(s => s.id === session.id)
        let updated
        if (existing >= 0) {
          updated = [...prev]
          updated[existing] = session
        } else {
          updated = [session, ...prev]
          setCurrentSessionId(session.id)
        }
        // Keep only last 20 sessions
        const limited = updated.slice(0, 20)
        localStorage.setItem('chat_sessions', JSON.stringify(limited))
        return limited
      })
    }
  }, [history, currentSessionId])

  // Save theme to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('theme', theme)
  }, [theme])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, loading])

  // Parse SQL results into table format
  const parseTableData = (rawResult: string): TableData | null => {
    if (!rawResult) return null
    
    try {
      // Handle list of tuples: [(val1, val2), (val3, val4)]
      if (rawResult.includes('[(') || rawResult.includes('), (')) {
        const cleaned = rawResult.replace(/[\[\]]/g, '').trim()
        const rows = cleaned.split('), (').map(row => 
          row.replace(/[()]/g, '').split(',').map(cell => cell.trim().replace(/['"]/g, ''))
        )
        
        if (rows.length > 0) {
          // First row might be headers or data - we'll treat as data
          const headers = rows[0].map((_, i) => `Column ${i + 1}`)
          return { headers, rows }
        }
      }
      
      // Handle simple list: [val1, val2, val3]
      if (rawResult.startsWith('[') && rawResult.includes(',')) {
        const values = rawResult.replace(/[\[\]]/g, '').split(',').map(v => v.trim())
        return {
          headers: ['Value'],
          rows: values.map(v => [v])
        }
      }
    } catch (e) {
      console.error('Error parsing table data:', e)
    }
    
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setHistory(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)
    setShowNewChatButton(true)
    
    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      
      const data: QueryResponse = await response.json()
      setHistory(prev => [...prev, { role: 'assistant', content: data }])
      setQuestion('')
      
      // Show toast notification if fallback to mock mode occurred
      if (data.llm_mode === 'mock' && data.llm_fallback_reason) {
        showToast(`⚠️ Using Mock Mode: ${data.llm_fallback_reason}`, 'warning')
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      setHistory(prev => [...prev, { 
        role: 'assistant', 
        content: { 
          answer: `❌ **Connection Error**\n\n${errorMsg}\n\n**Troubleshooting:**\n• Ensure backend is running\n• Check your network connection\n• Try refreshing the page\n• Restart the backend server if needed`,
          error: errorMsg
        } 
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = async () => {
    // Clear conversation context on backend
    try {
      await fetch(`${API_URL}/api/context/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    } catch (error) {
      console.error('Error clearing context:', error)
    }
    
    // Clear local history
    setHistory([])
    setShowNewChatButton(false)
    setQuestion('')
    setCurrentSessionId('')
    showToast('✨ New conversation started', 'success')
  }

  const loadChatSession = (session: ChatSession) => {
    setHistory(session.messages)
    setCurrentSessionId(session.id)
    setShowNewChatButton(true)
    setSidebarOpen(false)
  }

  const deleteSession = (sessionId: string) => {
    setChatSessions(prev => {
      const updated = prev.filter(s => s.id !== sessionId)
      localStorage.setItem('chat_sessions', JSON.stringify(updated))
      return updated
    })
    if (currentSessionId === sessionId) {
      handleNewChat()
    }
    showToast('🗑️ Session deleted', 'success')
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      showToast('✅ Copied to clipboard!', 'success')
    }).catch(err => {
      console.error('Failed to copy:', err)
      showToast('❌ Failed to copy', 'error')
    })
  }

  const exportChatHistory = () => {
    const dataStr = JSON.stringify(history, null, 2)
    const dataBlob = new Blob([dataStr], {type: 'application/json'})
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ledger-detective-chat-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
    showToast('💾 Chat history exported!', 'success')
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion)
  }

  const runAnomalyScan = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/anomalies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      const data = await response.json()
      setHistory(prev => [...prev, { 
        role: 'system', 
        content: { 
          answer: data.message,
          anomalies: data.anomalies,
          suggestions: data.suggestions
        } 
      }])
    } catch (error) {
      console.error('Error scanning anomalies:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  // Modern AI chat colors (similar to ChatGPT/Claude)
  const colors = {
    teal: '#2A9D8F',
    light: {
      bg: '#FFFFFF',
      userBubble: '#2A9D8F',
      assistantBg: '#F7F7F8',
      text: '#0D0D0D',
      textSecondary: '#6B6B6B',
      border: '#ECECEC',
      inputBg: '#FFFFFF',
      inputBorder: '#D1D1D1',
      codeBg: '#F3F4F6',
      tableBorder: '#E5E7EB',
      tableHeader: '#F9FAFB'
    },
    dark: {
      bg: '#212121',
      userBubble: '#2A9D8F',
      assistantBg: '#2F2F2F',
      text: '#ECECEC',
      textSecondary: '#B4B4B4',
      border: '#3F3F3F',
      inputBg: '#2F2F2F',
      inputBorder: '#4B4B4B',
      codeBg: '#1A1A1A',
      tableBorder: '#3F3F3F',
      tableHeader: '#2A2A2A'
    }
  }

  const currentColors = theme === 'dark' ? colors.dark : colors.light

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: currentColors.bg,
      color: currentColors.text,
      transition: 'background-color 0.3s ease, color 0.3s ease',
      display: 'flex',
      flexDirection: 'row',
      overflow: 'hidden'
    }}>
      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? '280px' : '0',
        backgroundColor: theme === 'dark' ? '#1A1A1A' : '#F5F5F5',
        borderRight: sidebarOpen ? `1px solid ${currentColors.border}` : 'none',
        transition: 'width 0.3s ease',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh'
      }}>
        <div style={{ padding: '1rem', borderBottom: `1px solid ${currentColors.border}` }}>
          <button
            onClick={handleNewChat}
            style={{
              width: '100%',
              padding: '0.75rem 1rem',
              backgroundColor: colors.teal,
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 600,
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#238d82'
              e.currentTarget.style.transform = 'translateY(-1px)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = colors.teal
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            <span style={{ fontSize: '1.2rem' }}>+</span>
            New Chat
          </button>
        </div>
        <div style={{ 
          flex: 1, 
          overflow: 'auto',
          padding: '0.5rem'
        }}>
          <div style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: currentColors.textSecondary,
            padding: '0.5rem 0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Recent Chats
          </div>
          {chatSessions.map((session) => (
            <div
              key={session.id}
              style={{
                padding: '0.75rem',
                margin: '0.25rem 0',
                backgroundColor: currentSessionId === session.id ? currentColors.assistantBg : 'transparent',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'start',
                gap: '0.5rem'
              }}
              onClick={() => loadChatSession(session)}
              onMouseEnter={(e) => {
                if (currentSessionId !== session.id) {
                  e.currentTarget.style.backgroundColor = currentColors.assistantBg
                }
              }}
              onMouseLeave={(e) => {
                if (currentSessionId !== session.id) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: '0.875rem',
                  color: currentColors.text,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  marginBottom: '0.25rem'
                }}>
                  {session.title}
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: currentColors.textSecondary
                }}>
                  {new Date(session.timestamp).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteSession(session.id)
                }}
                style={{
                  padding: '0.25rem',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: currentColors.textSecondary,
                  cursor: 'pointer',
                  fontSize: '1rem',
                  opacity: 0.6,
                  transition: 'opacity 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        minWidth: 0
      }}>
      {/* Header */}
      <div style={{ 
        backgroundColor: currentColors.bg,
        borderBottom: `1px solid ${currentColors.border}`,
        padding: '1rem 1.5rem',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                padding: '0.5rem',
                backgroundColor: 'transparent',
                color: currentColors.text,
                border: `1px solid ${currentColors.border}`,
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                fontSize: '1.2rem'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = currentColors.assistantBg
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              {sidebarOpen ? '✕' : '☰'}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <img 
                src="/ledger-detective-logo.png" 
                alt="Ledger Detective Logo" 
                style={{ width: '36px', height: '36px' }}
              />
              <div>
                <h1 style={{ 
                  color: currentColors.text, 
                  margin: 0, 
                  fontSize: '1.15rem', 
                  fontWeight: 600
                }}>
                  Ledger Detective
                </h1>
                <div style={{
                  margin: 0,
                  fontSize: '0.7rem',
                  color: currentColors.textSecondary,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{
                    padding: '0.125rem 0.375rem',
                    backgroundColor: theme === 'dark' ? '#1a3a1a' : '#e8f5e9',
                    color: colors.teal,
                    borderRadius: '4px',
                    fontSize: '0.65rem',
                    fontWeight: 600
                  }}>
                    916 RECORDS
                  </span>
                  <span>SAP Procurement</span>
                </div>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {history.length > 0 && (
              <button
                onClick={exportChatHistory}
                title="Export chat history"
                style={{
                  padding: '0.5rem 0.75rem',
                  fontSize: '1.1rem',
                  backgroundColor: 'transparent',
                  color: currentColors.textSecondary,
                  border: `1px solid ${currentColors.border}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = currentColors.assistantBg
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
              >
                💾
              </button>
            )}
            {showNewChatButton && (
              <button
                onClick={handleNewChat}
                style={{
                  padding: '0.5rem 1rem',
                  fontSize: '0.875rem',
                  backgroundColor: 'transparent',
                  color: currentColors.textSecondary,
                  border: `1px solid ${currentColors.border}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = currentColors.assistantBg
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
              >
                New Chat
              </button>
            )}
            <button
              onClick={runAnomalyScan}
              title="Scan for data issues"
              style={{
                padding: '0.5rem 0.75rem',
                fontSize: '1.1rem',
                backgroundColor: 'transparent',
                color: currentColors.textSecondary,
                border: `1px solid ${currentColors.border}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = currentColors.assistantBg
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              🔍
            </button>
            <button
              onClick={toggleTheme}
              style={{
                padding: '0.5rem 0.75rem',
                fontSize: '1.25rem',
                backgroundColor: 'transparent',
                color: currentColors.textSecondary,
                border: `1px solid ${currentColors.border}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = currentColors.assistantBg
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ 
        flex: 1,
        maxWidth: '900px', 
        width: '100%',
        margin: '0 auto', 
        padding: '2rem 1.5rem',
        paddingBottom: '160px'
      }}>
        {/* Chat History */}
        <div style={{ flex: 1 }}>
          {history.length === 0 && (
            <div style={{ 
              textAlign: 'center', 
              padding: '3rem 2rem',
              maxWidth: '900px',
              margin: '0 auto'
            }}>
              {/* Hero Section */}
              <div style={{ marginBottom: '3rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1.5rem', animation: 'fadeIn 0.6s ease-out' }}>🔍</div>
                <h2 style={{ 
                  fontSize: '2.25rem', 
                  marginBottom: '0.75rem',
                  fontWeight: 700,
                  color: currentColors.text,
                  animation: 'fadeIn 0.6s ease-out 0.1s backwards'
                }}>
                  Welcome to Ledger Detective
                </h2>
                <p style={{ 
                  fontSize: '1.1rem', 
                  marginBottom: '2.5rem',
                  color: currentColors.textSecondary,
                  lineHeight: '1.6',
                  animation: 'fadeIn 0.6s ease-out 0.2s backwards'
                }}>
                  Your AI-powered assistant for SAP procurement data analysis
                  <br/>
                  Ask questions in natural language and get instant insights
                </p>

                {/* Features Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '1rem',
                  marginBottom: '3rem',
                  animation: 'fadeIn 0.6s ease-out 0.3s backwards'
                }}>
                  {[
                    { icon: '⚡', title: 'Instant Analysis', desc: 'Query 916 records across 5 tables' },
                    { icon: '🤖', title: 'AI-Powered', desc: 'Gemini LLM with smart fallback' },
                    { icon: '🔒', title: 'Secure Queries', desc: 'SQL injection protection' },
                    { icon: '💡', title: 'Smart Insights', desc: 'Anomaly detection & suggestions' }
                  ].map((feature, i) => (
                    <div key={i} style={{
                      padding: '1.5rem 1rem',
                      backgroundColor: currentColors.assistantBg,
                      border: `1px solid ${currentColors.border}`,
                      borderRadius: '12px',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-4px)'
                      e.currentTarget.style.borderColor = colors.teal
                      e.currentTarget.style.boxShadow = `0 8px 16px ${theme === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.1)'}`
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)'
                      e.currentTarget.style.borderColor = currentColors.border
                      e.currentTarget.style.boxShadow = 'none'
                    }}>
                      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{feature.icon}</div>
                      <div style={{ 
                        fontWeight: 600, 
                        marginBottom: '0.25rem',
                        color: currentColors.text,
                        fontSize: '0.9rem'
                      }}>
                        {feature.title}
                      </div>
                      <div style={{ 
                        fontSize: '0.75rem', 
                        color: currentColors.textSecondary,
                        lineHeight: '1.4'
                      }}>
                        {feature.desc}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Example Questions */}
                <div style={{ marginBottom: '1rem' }}>
                  <h3 style={{
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: currentColors.text,
                    marginBottom: '1rem',
                    animation: 'fadeIn 0.6s ease-out 0.4s backwards'
                  }}>
                    Try asking me:
                  </h3>
                </div>
                <div style={{ 
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '0.75rem',
                  animation: 'fadeIn 0.6s ease-out 0.5s backwards'
                }}>
                  {[
                    { q: 'How many purchase orders?', icon: '📊' },
                    { q: 'Which vendors have most POs?', icon: '🏢' },
                    { q: 'Show unmatched receipts > 100k', icon: '⚠️' },
                    { q: 'What percentage of POs are fully matched?', icon: '✓' },
                    { q: 'Scan for data anomalies', icon: '🔍' },
                    { q: 'Show me vendor performance summary', icon: '📈' }
                  ].map((example, i) => (
                    <button
                      key={i}
                      onClick={() => setQuestion(example.q)}
                      style={{
                        padding: '1rem 1.25rem',
                        backgroundColor: currentColors.assistantBg,
                        border: `1px solid ${currentColors.border}`,
                        borderRadius: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.25s ease',
                        fontSize: '0.9rem',
                        color: currentColors.text,
                        textAlign: 'left',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        fontWeight: 500
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = colors.teal
                        e.currentTarget.style.transform = 'translateX(4px)'
                        e.currentTarget.style.backgroundColor = theme === 'dark' ? '#2A2A2A' : '#FAFAFA'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = currentColors.border
                        e.currentTarget.style.transform = 'translateX(0)'
                        e.currentTarget.style.backgroundColor = currentColors.assistantBg
                      }}
                    >
                      <span style={{ fontSize: '1.25rem' }}>{example.icon}</span>
                      <span>{example.q}</span>
                    </button>
                  ))}
                </div>

                {/* Pro Tips */}
                <div style={{ 
                  marginTop: '3rem',
                  padding: '1.5rem',
                  backgroundColor: currentColors.assistantBg,
                  borderRadius: '12px',
                  border: `1px solid ${currentColors.border}`,
                  animation: 'fadeIn 0.6s ease-out 0.6s backwards'
                }}>
                  <div style={{
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    marginBottom: '0.75rem',
                    color: currentColors.text,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <span style={{ fontSize: '1.2rem' }}>💡</span>
                    Pro Tips
                  </div>
                  <div style={{
                    fontSize: '0.85rem',
                    color: currentColors.textSecondary,
                    lineHeight: '1.8',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                    gap: '0.75rem'
                  }}>
                    <div>• Click <b>☰</b> to open chat history sidebar</div>
                    <div>• Press <b>🔍</b> to scan for data anomalies</div>
                    <div>• Toggle <b>🌙/☀️</b> to switch themes</div>
                    <div>• Click <b>💾</b> to export conversations</div>
                    <div>• All queries show SQL for transparency</div>
                    <div>• Up to 20 conversations auto-saved</div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {history.map((msg, idx) => (
            <div key={idx} style={{ marginBottom: '1.5rem' }}>
              {msg.role === 'user' ? (
                <div style={{ 
                  display: 'flex',
                  gap: '0.75rem',
                  justifyContent: 'flex-end'
                }}>
                  <div style={{ 
                    backgroundColor: colors.teal,
                    color: 'white',
                    padding: '0.875rem 1.125rem',
                    borderRadius: '18px',
                    maxWidth: '75%',
                    fontSize: '0.95rem',
                    lineHeight: '1.5'
                  }}>
                    {msg.content}
                  </div>
                </div>
              ) : msg.role === 'system' ? (
                <div style={{ 
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'flex-start'
                }}>
                  <div style={{
                    minWidth: '32px',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: currentColors.assistantBg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.1rem',
                    flexShrink: 0,
                    marginTop: '0.25rem'
                  }}>
                    🔍
                  </div>
                  <div style={{ 
                    backgroundColor: currentColors.assistantBg,
                    padding: '1.125rem 1.25rem',
                    borderRadius: '18px',
                    maxWidth: 'calc(100% - 48px)',
                    fontSize: '0.95rem',
                    lineHeight: '1.6',
                    color: currentColors.text
                  }}>
                    <div style={{ whiteSpace: 'pre-line' }}>{msg.content.answer}</div>
                    {msg.content.suggestions && msg.content.suggestions.length > 0 && (
                      <div style={{ marginTop: '1rem' }}>
                        <div style={{ 
                          fontSize: '0.875rem',
                          color: currentColors.textSecondary,
                          marginBottom: '0.5rem',
                          fontWeight: 500
                        }}>
                          💡 Suggested actions:
                        </div>
                        <div style={{ 
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.5rem'
                        }}>
                          {msg.content.suggestions.map((suggestion, i) => (
                            <button
                              key={i}
                              onClick={() => handleSuggestionClick(suggestion)}
                              style={{
                                padding: '0.625rem 0.875rem',
                                backgroundColor: currentColors.bg,
                                border: `1px solid ${currentColors.border}`,
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                color: currentColors.text,
                                textAlign: 'left',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = colors.teal
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = currentColors.border
                              }}
                            >
                              → {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ 
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'flex-start'
                }}>
                  <div style={{
                    minWidth: '28px',
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #2A9D8F 0%, #238d82 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.9rem',
                    flexShrink: 0,
                    marginTop: '0.25rem',
                    boxShadow: '0 2px 4px rgba(42, 157, 143, 0.2)'
                  }}>
                    🔍
                  </div>
                  <div style={{ 
                    flex: 1,
                    maxWidth: 'calc(100% - 48px)',
                    fontSize: '0.95rem',
                    lineHeight: '1.6',
                    color: currentColors.text
                  }}>
                    {/* Context Indicator */}
                    {msg.content.context_used && (
                      <div style={{ 
                        marginBottom: '0.75rem',
                        padding: '0.5rem 0.75rem',
                        backgroundColor: theme === 'dark' ? '#1a3a1a' : '#e8f5e9',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        color: colors.teal
                      }}>
                        🔗 Used conversation context to understand your question
                      </div>
                    )}

                    {/* Decomposition Plan */}
                    {msg.content.decomposition_plan && (
                      <div style={{ 
                        marginBottom: '0.75rem',
                        padding: '0.75rem',
                        backgroundColor: currentColors.codeBg,
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        color: currentColors.text,
                        borderLeft: `3px solid ${colors.teal}`,
                        whiteSpace: 'pre-line'
                      }}>
                        {msg.content.decomposition_plan}
                      </div>
                    )}

                    {/* Main Answer - Markdown Rendered */}
                    <div style={{ 
                      marginBottom: msg.content.sql_query || (msg.content.steps && msg.content.steps.length > 0) || msg.content.suggestions ? '1rem' : 0,
                      padding: '0.75rem 1rem',
                      backgroundColor: currentColors.assistantBg,
                      borderRadius: '12px',
                      border: `1px solid ${currentColors.border}`
                    }}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          code({node, inline, className, children, ...props}) {
                            const match = /language-(\w+)/.exec(className || '')
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={theme === 'dark' ? vscDarkPlus : vs}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} style={{
                                backgroundColor: currentColors.codeBg,
                                padding: '0.2rem 0.4rem',
                                borderRadius: '4px',
                                fontFamily: "'SF Mono', 'Monaco', monospace",
                                fontSize: '0.9em'
                              }} {...props}>
                                {children}
                              </code>
                            )
                          },
                          table({node, ...props}) {
                            return (
                              <div style={{ overflowX: 'auto', margin: '1rem 0' }}>
                                <table style={{
                                  width: '100%',
                                  borderCollapse: 'collapse',
                                  border: `1px solid ${currentColors.tableBorder}`
                                }} {...props} />
                              </div>
                            )
                          },
                          thead({node, ...props}) {
                            return <thead style={{ backgroundColor: currentColors.tableHeader }} {...props} />
                          },
                          th({node, ...props}) {
                            return (
                              <th style={{
                                padding: '0.75rem',
                                textAlign: 'left',
                                borderBottom: `2px solid ${currentColors.tableBorder}`,
                                fontWeight: 600,
                                color: currentColors.text
                              }} {...props} />
                            )
                          },
                          td({node, ...props}) {
                            return (
                              <td style={{
                                padding: '0.75rem',
                                borderBottom: `1px solid ${currentColors.tableBorder}`,
                                color: currentColors.text
                              }} {...props} />
                            )
                          },
                          p({node, ...props}) {
                            return <p style={{ margin: '0.5rem 0', lineHeight: '1.6' }} {...props} />
                          },
                          ul({node, ...props}) {
                            return <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }} {...props} />
                          },
                          ol({node, ...props}) {
                            return <ol style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }} {...props} />
                          },
                          li({node, ...props}) {
                            return <li style={{ margin: '0.25rem 0' }} {...props} />
                          },
                          blockquote({node, ...props}) {
                            return (
                              <blockquote style={{
                                margin: '1rem 0',
                                padding: '0.5rem 1rem',
                                borderLeft: `4px solid ${colors.teal}`,
                                backgroundColor: currentColors.codeBg,
                                fontStyle: 'italic'
                              }} {...props} />
                            )
                          },
                          h1({node, ...props}) {
                            return <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '1rem 0 0.5rem' }} {...props} />
                          },
                          h2({node, ...props}) {
                            return <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: '1rem 0 0.5rem' }} {...props} />
                          },
                          h3({node, ...props}) {
                            return <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0.75rem 0 0.5rem' }} {...props} />
                          },
                          a({node, ...props}) {
                            return <a style={{ color: colors.teal, textDecoration: 'underline' }} {...props} target="_blank" rel="noopener noreferrer" />
                          },
                          strong({node, ...props}) {
                            return <strong style={{ fontWeight: 700 }} {...props} />
                          },
                          em({node, ...props}) {
                            return <em style={{ fontStyle: 'italic' }} {...props} />
                          }
                        }}
                      >
                        {msg.content.answer}
                      </ReactMarkdown>
                    </div>

                    {/* Anomaly Alert */}
                    {msg.content.anomalies && (
                      <div style={{ 
                        marginTop: '1rem',
                        padding: '1rem',
                        backgroundColor: theme === 'dark' ? '#3a1a1a' : '#fff4e6',
                        borderRadius: '10px',
                        borderLeft: `4px solid #ff9800`,
                        marginBottom: '1rem'
                      }}>
                        <div style={{ 
                          fontWeight: 600,
                          marginBottom: '0.5rem',
                          color: '#ff9800',
                          fontSize: '0.95rem'
                        }}>
                          ⚠️ {msg.content.anomalies.count} Issue{msg.content.anomalies.count > 1 ? 's' : ''} Detected
                        </div>
                        <div style={{ 
                          fontSize: '0.875rem',
                          color: currentColors.text,
                          whiteSpace: 'pre-line'
                        }}>
                          {msg.content.anomalies.message}
                        </div>
                      </div>
                    )}
                    
                    {/* Table Results */}
                    {msg.content.raw_result && (() => {
                      const tableData = parseTableData(msg.content.raw_result)
                      return tableData && tableData.rows.length > 0 ? (
                        <div style={{ 
                          marginTop: '1rem',
                          overflowX: 'auto',
                          borderRadius: '10px',
                          backgroundColor: currentColors.bg,
                          border: `1px solid ${currentColors.border}`,
                          boxShadow: theme === 'dark' ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
                        }}>
                          <table style={{ 
                            width: '100%',
                            borderCollapse: 'collapse',
                            fontSize: '0.85rem'
                          }}>
                            <thead>
                              <tr style={{ 
                                background: theme === 'dark' 
                                  ? 'linear-gradient(to right, #1a3a3a, #1a4a4a)' 
                                  : 'linear-gradient(to right, #e8f5f3, #d4f1ec)'
                              }}>
                                {tableData.headers.map((header, i) => (
                                  <th key={i} style={{ 
                                    padding: '0.875rem 1rem',
                                    textAlign: 'left',
                                    fontWeight: 600,
                                    borderBottom: `2px solid ${colors.teal}`,
                                    color: theme === 'dark' ? colors.teal : '#1a5a54',
                                    fontSize: '0.8rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px'
                                  }}>
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {tableData.rows.slice(0, 10).map((row, i) => (
                                <tr key={i} style={{ 
                                  borderBottom: `1px solid ${currentColors.border}`,
                                  transition: 'background-color 0.15s ease',
                                  cursor: 'default'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor = currentColors.assistantBg
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = 'transparent'
                                }}>
                                  {row.map((cell, j) => (
                                    <td key={j} style={{ 
                                      padding: '0.75rem 1rem',
                                      color: currentColors.text
                                    }}>
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {tableData.rows.length > 10 && (
                            <div style={{ 
                              padding: '0.625rem 1rem',
                              backgroundColor: currentColors.assistantBg,
                              fontSize: '0.75rem',
                              color: currentColors.textSecondary,
                              textAlign: 'center',
                              borderTop: `1px solid ${currentColors.border}`,
                              fontStyle: 'italic'
                            }}>
                              Showing first 10 of {tableData.rows.length} total rows
                            </div>
                          )}
                        </div>
                      ) : null
                    })()}
                    
                    {/* SQL Query & Processing Steps - Footer */}
                    {(msg.content.sql_query || (msg.content.steps && msg.content.steps.length > 0)) && (
                      <div style={{ 
                        marginTop: '1.5rem',
                        paddingTop: '1rem',
                        borderTop: `1px solid ${currentColors.border}`
                      }}>
                        {msg.content.sql_query && (
                          <details style={{ marginBottom: msg.content.steps ? '0.75rem' : 0 }}>
                            <summary style={{ 
                              cursor: 'pointer',
                              fontSize: '0.8rem',
                              color: currentColors.textSecondary,
                              marginBottom: '0.5rem',
                              userSelect: 'none',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                              fontWeight: 500
                            }}>
                              <span>📊 SQL Query</span>
                              <button
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  copyToClipboard(msg.content.sql_query)
                                }}
                                style={{
                                  padding: '0.2rem 0.4rem',
                                  fontSize: '0.7rem',
                                  backgroundColor: currentColors.bg,
                                  color: currentColors.textSecondary,
                                  border: `1px solid ${currentColors.border}`,
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  transition: 'all 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor = colors.teal
                                  e.currentTarget.style.color = 'white'
                                  e.currentTarget.style.borderColor = colors.teal
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = currentColors.bg
                                  e.currentTarget.style.color = currentColors.textSecondary
                                  e.currentTarget.style.borderColor = currentColors.border
                                }}
                                title="Copy SQL"
                              >
                                📋 Copy
                              </button>
                            </summary>
                            <pre style={{ 
                              backgroundColor: currentColors.codeBg,
                              padding: '0.75rem',
                              borderRadius: '6px',
                              overflow: 'auto',
                              fontSize: '0.75rem',
                              margin: '0.5rem 0 0 0',
                              fontFamily: "'SF Mono', 'Monaco', monospace",
                              lineHeight: '1.6',
                              color: currentColors.text,
                              border: `1px solid ${currentColors.border}`
                            }}>
{msg.content.sql_query}
                            </pre>
                          </details>
                        )}
                        
                        {msg.content.steps && msg.content.steps.length > 0 && (
                          <details>
                            <summary style={{ 
                              cursor: 'pointer',
                              fontSize: '0.8rem',
                              color: currentColors.textSecondary,
                              userSelect: 'none',
                              fontWeight: 500
                            }}>
                              ⚙️ Processing Steps ({msg.content.steps.length})
                            </summary>
                            <ul style={{ 
                              paddingLeft: '1.25rem', 
                              margin: '0.5rem 0 0 0',
                              fontSize: '0.75rem',
                              color: currentColors.textSecondary,
                              lineHeight: '1.8'
                            }}>
                              {msg.content.steps.map((step, i) => (
                                <li key={i} style={{ marginBottom: '0.25rem' }}>{step}</li>
                              ))}
                            </ul>
                          </details>
                        )}
                      </div>
                    )}

                    {/* Smart Suggestions */}
                    {msg.content.suggestions && msg.content.suggestions.length > 0 && (
                      <div style={{ marginTop: '1rem' }}>
                        <div style={{ 
                          fontSize: '0.875rem',
                          color: currentColors.textSecondary,
                          marginBottom: '0.5rem',
                          fontWeight: 500
                        }}>
                          💡 You might also want to know:
                        </div>
                        <div style={{ 
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.5rem'
                        }}>
                          {msg.content.suggestions.map((suggestion, i) => (
                            <button
                              key={i}
                              onClick={() => handleSuggestionClick(suggestion)}
                              style={{
                                padding: '0.625rem 0.875rem',
                                backgroundColor: currentColors.bg,
                                border: `1px solid ${currentColors.border}`,
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                color: currentColors.text,
                                textAlign: 'left',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = colors.teal
                                e.currentTarget.style.backgroundColor = currentColors.assistantBg
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = currentColors.border
                                e.currentTarget.style.backgroundColor = currentColors.bg
                              }}
                            >
                              → {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div style={{ 
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'flex-start'
            }}>
              <div style={{
                minWidth: '32px',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: currentColors.assistantBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.1rem',
                flexShrink: 0,
                marginTop: '0.25rem'
              }}>
                🔍
              </div>
              <div style={{ 
                backgroundColor: currentColors.assistantBg,
                padding: '1.125rem 1.25rem',
                borderRadius: '18px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <div style={{ 
                  width: '16px',
                  height: '16px',
                  border: `2px solid ${currentColors.border}`,
                  borderTop: `2px solid ${colors.teal}`,
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }} />
                <span style={{ 
                  fontSize: '0.95rem',
                  color: currentColors.textSecondary
                }}>
                  Thinking...
                </span>
              </div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Form - Fixed at bottom */}
      <div style={{ 
        position: 'fixed',
        bottom: '0',
        left: '0',
        right: '0',
        backgroundColor: currentColors.bg,
        borderTop: `1px solid ${currentColors.border}`,
        padding: '1.25rem 1.5rem',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Message Ledger Detective..."
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.875rem 3.5rem 0.875rem 1.125rem',
                fontSize: '0.95rem',
                border: `1px solid ${currentColors.inputBorder}`,
                borderRadius: '12px',
                backgroundColor: currentColors.inputBg,
                color: currentColors.text,
                outline: 'none',
                transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                fontFamily: 'inherit',
                boxShadow: theme === 'dark' ? 'none' : '0 1px 2px rgba(0,0,0,0.05)'
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = colors.teal
                e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.teal}20`
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = currentColors.inputBorder
                e.currentTarget.style.boxShadow = theme === 'dark' ? 'none' : '0 1px 2px rgba(0,0,0,0.05)'
              }}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                padding: '0.5rem',
                width: '32px',
                height: '32px',
                fontSize: '1.1rem',
                backgroundColor: loading || !question.trim() ? 'transparent' : colors.teal,
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: loading || !question.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: loading || !question.trim() ? 0.3 : 1
              }}
              onMouseEnter={(e) => {
                if (!loading && question.trim()) {
                  e.currentTarget.style.backgroundColor = '#238d82'
                }
              }}
              onMouseLeave={(e) => {
                if (!loading && question.trim()) {
                  e.currentTarget.style.backgroundColor = colors.teal
                }
              }}
            >
              ↑
            </button>
          </form>
        </div>
      </div>

      {/* Toast Notifications */}
      <div style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        maxWidth: '400px'
      }}>
        {toasts.map(toast => (
          <div
            key={toast.id}
            style={{
              backgroundColor: toast.type === 'error' ? '#ef4444' : 
                             toast.type === 'success' ? '#10b981' : '#f59e0b',
              color: 'white',
              padding: '1rem',
              borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              display: 'flex',
              alignItems: 'start',
              justifyContent: 'space-between',
              gap: '0.75rem',
              animation: 'slideInRight 0.3s ease-out',
              fontSize: '0.875rem',
              lineHeight: '1.4'
            }}
          >
            <div style={{ flex: 1 }}>{toast.message}</div>
            <button
              onClick={() => removeToast(toast.id)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '1.25rem',
                lineHeight: '1',
                padding: '0',
                opacity: 0.8
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        * {
          box-sizing: border-box;
        }
        
        body {
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
            'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
            sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
        
        code, pre {
          font-family: 'SF Mono', 'Monaco', 'Consolas', 'Courier New', monospace;
        }
        
        input::placeholder {
          opacity: 0.5;
        }
        
        details summary {
          list-style: none;
        }
        
        details summary::-webkit-details-marker {
          display: none;
        }
        
        details summary::marker {
          display: none;
        }
        
        details summary:hover {
          opacity: 0.7;
        }
        
        details[open] summary {
          margin-bottom: 0.5rem;
        }
        
        /* Smooth scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
          background: ${currentColors.border};
          border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: ${currentColors.textSecondary};
        }
      `}</style>
    </div>
    </div>
  )
}

export default App
