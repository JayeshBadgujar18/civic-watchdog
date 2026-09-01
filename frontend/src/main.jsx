import { StrictMode, useRef, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowUp, ChevronDown, FileAudio, FileText, FolderOpen, LoaderCircle, Plus, Search, Shield, Sparkles, Upload, X } from 'lucide-react'
import './styles.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const MAX_UPLOAD_BYTES = 500 * 1024 * 1024
const ACCEPTED_EXTENSIONS = new Set(['.txt', '.md', '.mp3', '.mp4', '.wav', '.m4a', '.webm', '.mov'])
const mono = 'font-[DM_Mono] uppercase tracking-[0.07em]'

if (!import.meta.env.VITE_API_URL) {
  console.warn('VITE_API_URL is not set; the frontend is using http://localhost:8000.')
}

const SESSION_KEY = 'civic_watchdog_session_id'
function getOrCreateSessionId() {
  let sessionId = localStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    sessionId = crypto.randomUUID()
    localStorage.setItem(SESSION_KEY, sessionId)
  }
  return sessionId
}
const SESSION_ID = getOrCreateSessionId()

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remaining = Math.floor(seconds % 60).toString().padStart(2, '0')
  return `${minutes.toString().padStart(2, '0')}:${remaining}`
}

function isMediaSource(source) {
  return /\.(mp3|mp4|wav|m4a|webm|mov)$/i.test(source || '')
}

function formatFileSize(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(0)} MB`
}

function formatAnswerText(text, citations, onCitationClick) {
  if (!text) return null;
  const regex = /\[?(?:Source:\s*([^|\]]+?)\s*\|\s*)?Timestamp:\s*(\d+(?:\.\d+)?)s?\]?/gi;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const source = match[1] ? match[1].trim() : (citations[0]?.source || 'Unknown source');
    const start = parseFloat(match[2]);
    
    parts.push(
      <button 
        key={match.index}
        type="button"
        onClick={() => onCitationClick({ source, start })}
        className="mx-[3px] inline-flex items-center gap-[3px] rounded-[4px] bg-[#39765d] px-[6px] py-[2px] font-[DM_Mono] text-[13px] font-medium tracking-wide text-[#e9f0e8] hover:bg-[#4d876c] transition-colors align-baseline"
        title={`Jump to ${formatTime(start)}`}
        aria-label={`Jump to ${formatTime(start)}`}
      >
        {isMediaSource(source) ? <FileAudio size={12} /> : <FileText size={12} />}
        {formatTime(start)}
      </button>
    );
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts.length > 0 ? parts : text;
}

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [citations, setCitations] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [notice, setNotice] = useState('')
  const [sources, setSources] = useState(() => {
    const saved = localStorage.getItem('civic_watchdog_sources')
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    localStorage.setItem('civic_watchdog_sources', JSON.stringify(sources))
  }, [sources])
  const fileInput = useRef(null)
  const askInFlight = useRef(false)

  async function askQuestion(event) {
    event.preventDefault()
    if (!question.trim() || loading || askInFlight.current) return
    askInFlight.current = true
    setLoading(true); setNotice('')
    try {
      const response = await fetch(`${API_URL}/api/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Session-Id': SESSION_ID }, body: JSON.stringify({ query: question }) })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'The watchdog could not answer.')
      setAnswer(data.answer); setCitations(data.citations || [])
    } catch (error) { setNotice(error.message) } finally { askInFlight.current = false; setLoading(false) }
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!ACCEPTED_EXTENSIONS.has(extension)) {
      setNotice('Use a transcript, audio, or video file in a supported format.')
      event.target.value = ''
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setNotice(`${file.name} is ${formatFileSize(file.size)}. Files must be smaller than ${formatFileSize(MAX_UPLOAD_BYTES)}.`)
      event.target.value = ''
      return
    }
    setUploading(true); setNotice('')
    const form = new FormData(); form.append('file', file)
    try {
      const response = await fetch(`${API_URL}/api/ingest`, { method: 'POST', headers: { 'X-Session-Id': SESSION_ID }, body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not index this file.')
      setSources((current) => [{ name: data.source, chunks: data.chunks }, ...current])
      setNotice(`${data.source} is ready to search.`)
    } catch (error) { setNotice(error.message) } finally { setUploading(false); event.target.value = '' }
  }

  function handleCitationClick(citation) {
    const mediaEvent = new CustomEvent('civic-watchdog:seek', {
      detail: { source: citation.source, start: citation.start, end: citation.end },
    })
    window.dispatchEvent(mediaEvent)
    setNotice(`Timestamp ${formatTime(citation.start)} selected. Connect a player to open this recording.`)
  }

  return (
    <div className="min-h-screen bg-[#f5f3ed] text-[#18221e] [background-image:radial-gradient(circle_at_80%_10%,#e6eee7_0,transparent_32%)]">
      <header className="mx-auto flex h-[76px] max-w-[1240px] items-center gap-6 border-b border-[#dce0d8] px-5 sm:px-8">
        <a className="flex flex-1 items-center gap-2.5 font-medium tracking-[-0.02em] no-underline" href="/"><span className="grid size-[34px] place-items-center rounded-lg bg-[#183d35] text-[#e9f0e8]"><Shield size={19} /></span><span>Civic <b>Watchdog</b></span></a>
        <div className={`${mono} hidden text-[11px] text-[#627168] sm:block`}><span className="mr-2 inline-block size-[7px] rounded-full bg-[#37a26c] shadow-[0_0_0_4px_#dcece0]" />Knowledge base live</div>
        <button className="grid size-9 place-items-center rounded-full border border-[#d1d9d1] bg-transparent text-[#456057]" title="Open sources" onClick={() => document.querySelector('.source-panel')?.scrollIntoView({ behavior: 'smooth' })}><FolderOpen size={18} /></button>
      </header>

      <main className="mx-auto max-w-[1240px] px-5 pb-[70px] pt-[54px] sm:px-8 sm:pt-[82px]">
        <section className="max-w-[670px]">
          <p className={`${mono} mb-5 flex items-center gap-2 text-[11px] text-[#39765d]`}><Sparkles size={14} /> PUBLIC RECORDS, MADE SEARCHABLE</p>
          <h1 className="max-w-[760px] font-[Fraunces] text-[55px] font-medium leading-[0.96] tracking-[-0.055em] sm:text-[clamp(48px,7vw,88px)]">Ask what happened<br /><em className="text-[#4d876c] not-italic">in the room.</em></h1>
          <p className="mt-[26px] max-w-[530px] text-[17px] leading-[1.55] text-[#65716a]">Search your council meeting videos and transcripts for the detail that matters. Every answer stays tied to its source.</p>
        </section>

        <section className="mt-10 max-w-[860px] border border-[#d9ded7] bg-[#fffefa] p-[18px_14px_15px] shadow-[0_14px_40px_#263b3210] sm:mt-[54px] sm:p-[22px_24px_18px]">
          <div className={`${mono} mb-3.5 flex justify-between text-[11px] text-[#718078]`}><span>Ask the record</span><kbd className="font-inherit text-[10px] text-[#8a948d]">⌘ K</kbd></div>
          <form onSubmit={askQuestion}><div className="flex items-center gap-3 border border-[#ccd5cd] p-1.5 pl-3.5 text-[#7b8b82] focus-within:border-[#39765d]"><Search size={22} /><input className="min-w-0 flex-1 bg-transparent py-2.5 text-base text-[#18221e] outline-none placeholder:text-[#99a39c]" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What did the committee decide about..." aria-label="Ask a question" /><button className="grid size-[42px] place-items-center rounded bg-[#183d35] text-white transition-opacity disabled:cursor-default disabled:opacity-35" type="submit" disabled={loading || !question.trim()}>{loading ? <LoaderCircle className="animate-spin" size={19} /> : <ArrowUp size={19} />}</button></div></form>
          <div className="mt-[15px] flex flex-wrap items-center gap-2 text-xs text-[#8c9790]"><span>Try asking</span><button className="rounded-full border border-[#d6e3d7] bg-[#edf3ed] px-2.5 py-1 text-xs text-[#4e6d5d]" onClick={() => setQuestion('What was the man protesting during his public comment?')}>public comment topics</button><button className="rounded-full border border-[#d6e3d7] bg-[#edf3ed] px-2.5 py-1 text-xs text-[#4e6d5d]" onClick={() => setQuestion('What was the final decision?')}>final decisions</button></div>
        </section>

        {notice && <div className="mt-3.5 flex max-w-[860px] justify-between gap-4 border border-[#ecd9bd] bg-[#fff5e7] px-4 py-3 text-[13px] text-[#855d38]"><span>{notice}</span><button title="Dismiss notice" aria-label="Dismiss notice" onClick={() => setNotice('')}><X size={16} /></button></div>}

        <section className="mt-[52px] grid gap-[54px] lg:mt-[67px] lg:grid-cols-[minmax(0,1fr)_310px] lg:gap-[62px]">
          <div className="min-w-0">
            {loading ? <div className="animate-pulse border-y border-[#d5ddd5] py-[46px]" aria-live="polite" aria-label="Searching the indexed record"><div className="mb-5 h-11 w-11 rounded-full bg-[#dce9dd]" /><div className="mb-3 h-7 max-w-[330px] rounded bg-[#dfe5df]" /><div className="h-4 max-w-[460px] rounded bg-[#e4e8e3]" /><div className="mt-3 h-4 max-w-[390px] rounded bg-[#e4e8e3]" /></div> : answer ? <article className="bg-[#183d35] p-[26px_22px] text-[#edf4ec] sm:p-[26px_28px]"><div className={`${mono} flex items-center gap-2 text-[11px] text-[#9ac7a8]`}><span className="grid size-[25px] place-items-center rounded-full bg-[#a9d4ad] text-[#183d35]"><Sparkles size={16} /></span>Watchdog answer</div><p className="my-[25px] font-[Fraunces] text-[23px] leading-[1.3] tracking-[-0.02em] sm:text-[27px] whitespace-pre-wrap">{formatAnswerText(answer, citations, handleCitationClick)}</p><div className={`${mono} border-t border-[#416257] pt-[15px] text-[10px] text-[#91b2a0]`}>Generated from {citations.length} transcript {citations.length === 1 ? 'source' : 'sources'}</div></article> : <div className="border-y border-[#d5ddd5] py-[46px]"><div className="mb-5 grid size-11 place-items-center rounded-full bg-[#e3eee4] text-[#39765d]"><Search size={22} /></div><h2 className="mb-2 font-[Fraunces] text-[27px] font-medium">Your answer will appear here</h2><p className="text-[#7a867e]">Ask a question to search across every indexed meeting.</p></div>}
            {!loading && answer && citations.length === 0 && <div className="mt-4 flex items-start gap-3 border border-[#ecd9bd] bg-[#fff8ed] p-4 text-sm text-[#855d38]" role="status"><Search className="mt-0.5 shrink-0" size={17} /><span><strong className="font-semibold">No supporting evidence found.</strong> This answer was returned without matching transcript excerpts. Treat it as unverified.</span></div>}
            {citations.length > 0 && <div className="mt-11"><div className={`${mono} flex justify-between border-b border-[#cfd8d0] pb-[13px] text-[11px] text-[#51635a]`}><span>Evidence</span><span className="text-[#9ba59e]">{citations.length} excerpts</span></div>{citations.map((citation, index) => <details className="border-b border-[#d8ded8]" key={`${citation.source}-${citation.start}-${index}`} open={index === 0}><summary className="flex cursor-pointer items-center gap-3.5 px-1 py-[17px]"><button type="button" className="flex shrink-0 items-center gap-1.5 rounded-[3px] bg-[#e3eee4] px-2 py-1 font-[DM_Mono] text-[11px] text-[#39765d] hover:bg-[#d5e7d5]" onClick={(event) => { event.preventDefault(); handleCitationClick(citation) }} aria-label={`Jump to ${citation.source} at ${formatTime(citation.start)}`}>{isMediaSource(citation.source) ? <FileAudio size={12} /> : <FileText size={12} />}{formatTime(citation.start)}</button><span className="truncate text-sm text-[#4a5c53]">{isMediaSource(citation.source) ? <FileAudio className="mr-1 inline text-[#39765d]" size={14} aria-label="Audio or video source" /> : <FileText className="mr-1 inline text-[#39765d]" size={14} aria-label="Text source" />}{citation.source}</span><ChevronDown className="citation-chevron ml-auto shrink-0 text-[#8b978e] transition-transform" size={17} /></summary><p className="pb-5 pl-[45px] pr-2 text-sm leading-[1.55] text-[#68766e]">{citation.text}</p></details>)}</div>}
          </div>
          <aside className="source-panel self-start lg:pt-0"><div className={`${mono} flex justify-between border-b border-[#cfd8d0] pb-[13px] text-[11px] text-[#51635a]`}><span>Sources</span><span className="text-[#9ba59e]">{sources.length || '—'}</span></div><label aria-label="Upload a meeting video, audio file, or transcript" className="mt-[19px] flex cursor-pointer flex-col items-center border border-dashed border-[#aebfaf] bg-[#e8f0e7] px-[15px] py-7 text-center text-[#4d6659]"><input className="hidden" ref={fileInput} type="file" accept=".txt,.md,.mp3,.mp4,.wav,.m4a,.webm,.mov" onChange={uploadFile} /><span className="mb-3 grid size-10 place-items-center rounded-full bg-[#d5e7d5] text-[#39765d]">{uploading ? <LoaderCircle className="animate-spin" size={20} /> : <Upload size={20} />}</span><strong className="text-sm font-semibold">{uploading ? 'Indexing file...' : 'Add a meeting'}</strong><small className="mt-1 text-xs text-[#829188]">Drop a video or transcript here</small></label><div className="mt-[18px] min-h-[60px]">{sources.length ? sources.map((source) => <div className="flex gap-2.5 border-b border-[#d8ded8] py-3" key={`${source.name}-${source.chunks}`}><span className="text-[#39765d]">{isMediaSource(source.name) ? <FileAudio size={17} /> : <FileText size={17} />}</span><span className="min-w-0"><b className="block truncate text-[13px] font-medium text-[#45584e]">{source.name}</b><small className="mt-1 block text-[11px] text-[#909a93]">{source.chunks} indexed chunks</small></span></div>) : <p className="mt-1 text-[11px] text-[#909a93]">Your indexed meetings will show up here.</p>}</div><button className="mt-4 flex w-full items-center justify-center gap-1.5 border border-[#b7c8b9] bg-transparent p-2.5 text-[13px] text-[#39765d]" onClick={() => fileInput.current?.click()}><Plus size={16} /> Add source</button></aside>
        </section>
      </main>
      <footer className={`${mono} mx-auto flex max-w-[1240px] flex-col gap-2.5 px-5 pb-[30px] pt-5 text-[10px] text-[#9aa49d] sm:flex-row sm:justify-between sm:px-8`}><span>Built for clearer local government.</span><span>Private by default <span className="px-2 text-[#4d876c]">•</span> Source-linked answers</span></footer>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
