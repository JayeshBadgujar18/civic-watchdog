import { StrictMode, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowUp, ChevronDown, FileAudio, FileText, FolderOpen, LoaderCircle, Plus, Search, Shield, Sparkles, Upload, X } from 'lucide-react'
import './styles.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remaining = Math.floor(seconds % 60).toString().padStart(2, '0')
  return `${minutes.toString().padStart(2, '0')}:${remaining}`
}

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [citations, setCitations] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [notice, setNotice] = useState('')
  const [sources, setSources] = useState([])
  const fileInput = useRef(null)

  async function askQuestion(event) {
    event.preventDefault()
    if (!question.trim() || loading) return
    setLoading(true)
    setNotice('')
    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: question }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'The watchdog could not answer.')
      setAnswer(data.answer)
      setCitations(data.citations || [])
    } catch (error) { setNotice(error.message) } finally { setLoading(false) }
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true); setNotice('')
    const form = new FormData(); form.append('file', file)
    try {
      const response = await fetch(`${API_URL}/api/ingest`, { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not index this file.')
      setSources((current) => [{ name: data.source, chunks: data.chunks }, ...current])
      setNotice(`${data.source} is ready to search.`)
    } catch (error) { setNotice(error.message) } finally { setUploading(false); event.target.value = '' }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/"><span className="brand-mark"><Shield size={19} /></span><span>Civic <b>Watchdog</b></span></a>
        <div className="status"><span className="status-dot" /> Knowledge base live</div>
        <button className="icon-button" title="Open sources" onClick={() => document.querySelector('.source-panel')?.scrollIntoView({ behavior: 'smooth' })}><FolderOpen size={18} /></button>
      </header>

      <main className="workspace">
        <section className="intro">
          <p className="eyebrow"><Sparkles size={14} /> PUBLIC RECORDS, MADE SEARCHABLE</p>
          <h1>Ask what happened<br /><em>in the room.</em></h1>
          <p className="lede">Search your council meeting videos and transcripts for the detail that matters. Every answer stays tied to its source.</p>
        </section>

        <section className="ask-panel">
          <div className="panel-label"><span>Ask the record</span><kbd>⌘ K</kbd></div>
          <form onSubmit={askQuestion}>
            <div className="question-row"><Search size={22} /><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What did the committee decide about..." aria-label="Ask a question" /><button className="submit-button" type="submit" disabled={loading || !question.trim()}>{loading ? <LoaderCircle className="spin" size={19} /> : <ArrowUp size={19} />}</button></div>
          </form>
          <div className="suggestions"><span>Try asking</span><button onClick={() => setQuestion('What was the man protesting during his public comment?')}>public comment topics</button><button onClick={() => setQuestion('What was the final decision?')}>final decisions</button></div>
        </section>

        {notice && <div className="notice"><span>{notice}</span><button title="Dismiss" onClick={() => setNotice('')}><X size={16} /></button></div>}

        <section className="results-grid">
          <div className="answer-column">
            {answer ? <article className="answer-card"><div className="answer-heading"><span className="answer-icon"><Sparkles size={16} /></span><span>Watchdog answer</span></div><p className="answer-text">{answer}</p><div className="answer-foot">Generated from {citations.length} transcript {citations.length === 1 ? 'source' : 'sources'}</div></article> : <div className="empty-answer"><div className="empty-icon"><Search size={22} /></div><h2>Your answer will appear here</h2><p>Ask a question to search across every indexed meeting.</p></div>}
            {citations.length > 0 && <div className="citations"><div className="section-heading"><span>Evidence</span><span className="count">{citations.length} excerpts</span></div>{citations.map((citation, index) => <details className="citation" key={`${citation.source}-${citation.start}-${index}`} open={index === 0}><summary><span className="citation-time">{formatTime(citation.start)}</span><span className="citation-source">{citation.source}</span><ChevronDown size={17} /></summary><p>{citation.text}</p></details>)}</div>}
          </div>
          <aside className="source-panel"><div className="section-heading"><span>Sources</span><span className="count">{sources.length || '—'}</span></div><label className="upload-box"><input ref={fileInput} type="file" accept=".txt,.md,.mp3,.mp4,.wav,.m4a,.webm,.mov" onChange={uploadFile} /><span className="upload-icon">{uploading ? <LoaderCircle className="spin" size={20} /> : <Upload size={20} />}</span><strong>{uploading ? 'Indexing file...' : 'Add a meeting'}</strong><small>Drop a video or transcript here</small></label><div className="source-list">{sources.length ? sources.map((source) => <div className="source-item" key={`${source.name}-${source.chunks}`}><span className="file-icon">{source.name.match(/\.(mp3|mp4|wav|m4a|webm|mov)$/i) ? <FileAudio size={17} /> : <FileText size={17} />}</span><span><b>{source.name}</b><small>{source.chunks} indexed chunks</small></span></div>) : <p className="source-empty">Your indexed meetings will show up here.</p>}</div><button className="add-button" onClick={() => fileInput.current?.click()}><Plus size={16} /> Add source</button></aside>
        </section>
      </main>
      <footer><span>Built for clearer local government.</span><span>Private by default <span className="footer-dot">•</span> Source-linked answers</span></footer>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
