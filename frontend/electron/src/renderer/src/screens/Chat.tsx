import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Plus, Trash2, MessageSquare, Wrench, Cpu,
  ChevronDown, Zap, Loader2, AlertCircle, BookOpen, X,
  Paperclip, FileText, FileSpreadsheet, Presentation, File,
  CheckCircle2, Terminal, Code2, Check, Image, FileCode,
} from 'lucide-react'
import { cn } from '../lib/utils'
import {
  createChatSession, listChatSessions, getChatSession,
  deleteChatSession, clearChatSession, streamChatMessage,
  createRun, listModels, getActiveModel, setActiveModel,
} from '../lib/api/client'
import type { ChatSession, ChatMessage, ChatStreamEvent, ModelProfile } from '../lib/api/types'
import { useHealthStore } from '../stores/healthStore'
import { Skeleton } from '../components/ui/primitives'
import { toast } from 'sonner'

const BASE_URL = 'http://127.0.0.1:8000'

// ── Supported attachment types ────────────────────────────────────────────────
const ATTACH_EXTS = [
  '.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.md', '.csv', '.json',
  '.py', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.yaml', '.yml',
  '.sh', '.ps1', '.bat', '.toml', '.xml', '.ini', '.cfg',
  '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff',
  '.c', '.cpp', '.h', '.cs', '.java', '.rs', '.go', '.rb', '.php',
  '.sql', '.r', '.swift', '.kt',
]

// ── Attachment state ──────────────────────────────────────────────────────────
interface AttachedFile {
  id: string
  file: File
  status: 'parsing' | 'ready' | 'error'
  text?: string
  charCount?: number
  error?: string
}

function attachFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['docx', 'doc'].includes(ext))          return <FileText size={11} className="text-blue-400/70" />
  if (['xlsx', 'xls', 'csv'].includes(ext))   return <FileSpreadsheet size={11} className="text-emerald-400/70" />
  if (['pptx', 'ppt'].includes(ext))           return <Presentation size={11} className="text-orange-400/70" />
  if (ext === 'pdf')                            return <FileText size={11} className="text-red-400/70" />
  if (['png','jpg','jpeg','webp','gif','bmp','tiff'].includes(ext))
    return <Image size={11} className="text-purple-400/70" />
  if (['py','js','ts','tsx','jsx','c','cpp','cs','java','rs','go','rb','php','swift','kt','sh','ps1'].includes(ext))
    return <FileCode size={11} className="text-yellow-400/70" />
  return <File size={11} className="text-white/40" />
}

// ── Tool card ─────────────────────────────────────────────────────────────────
interface ToolExecution {
  tool: string
  args: Record<string, unknown>
  result?: string
  success?: boolean
  done: boolean
}

// Detect if a tool is code/terminal related
function isCodeTool(tool: string) {
  return ['system_run_code', 'system_terminal', 'system_shell'].includes(tool)
}
function isDocTool(tool: string) {
  return tool.startsWith('document_read') || tool.startsWith('document_inspect')
}

function ToolCard({ exec }: { exec: ToolExecution }) {
  const [open, setOpen] = useState(false)
  const color = exec.done
    ? exec.success ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'
    : 'border-white/[0.07] bg-white/[0.02]'
  const dot = exec.done
    ? exec.success ? 'bg-emerald-400' : 'bg-red-400'
    : 'bg-amber-400 animate-pulse'

  const icon = isCodeTool(exec.tool) ? <Terminal size={11} className="text-yellow-400/60" />
             : isDocTool(exec.tool)  ? <FileText size={11} className="text-blue-400/60" />
             : <Wrench size={11} className="text-white/40" />

  // Format tool name nicely
  const displayName = exec.tool.replace(/_/g, '.')

  return (
    <div className={cn('rounded-xl border text-[11px] font-mono overflow-hidden mt-2', color)}>
      <button className="w-full flex items-center gap-2 px-3 py-2 text-left" onClick={() => setOpen(o => !o)}>
        <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', dot)} />
        {icon}
        <span className="text-white/70 flex-1 truncate">{displayName}</span>
        {exec.done && (
          <span className={exec.success ? 'text-emerald-400/70' : 'text-red-400/60'}>
            {exec.success ? 'done' : 'failed'}
          </span>
        )}
        {!exec.done && <Loader2 size={10} className="animate-spin text-white/35" />}
        <ChevronDown size={10} className={cn('text-white/25 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-white/[0.05] pt-2">
          {Object.keys(exec.args).length > 0 && (
            <div>
              <p className="text-white/25 text-[9px] uppercase tracking-wider mb-1">args</p>
              <pre className="text-white/55 text-[10px] leading-snug whitespace-pre-wrap break-all bg-white/[0.02] rounded p-2">
                {JSON.stringify(exec.args, null, 2).slice(0, 600)}
              </pre>
            </div>
          )}
          {exec.result && (
            <div>
              <p className="text-white/25 text-[9px] uppercase tracking-wider mb-1">output</p>
              <pre className={cn(
                'text-[10px] leading-snug whitespace-pre-wrap break-all rounded p-2',
                exec.success ? 'text-emerald-300/70 bg-emerald-500/5' : 'text-red-300/70 bg-red-500/5'
              )}>
                {exec.result.slice(0, 800)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Message bubble with code block rendering ──────────────────────────────────
interface LocalMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolExecutions?: ToolExecution[]
  streaming?: boolean
  error?: string
  usage?: { in: number; out: number }
}

function renderContent(text: string) {
  // Render ```lang\n...\n``` code blocks inline
  const parts: React.ReactNode[] = []
  const codeRe = /```(\w*)\n?([\s\S]*?)```/g
  let last = 0, m: RegExpExecArray | null
  let key = 0
  while ((m = codeRe.exec(text)) !== null) {
    if (m.index > last) {
      parts.push(<span key={key++} className="whitespace-pre-wrap break-words">{text.slice(last, m.index)}</span>)
    }
    const lang = m[1] || 'code'
    const code = m[2].trimEnd()
    parts.push(
      <div key={key++} className="my-2 rounded-xl overflow-hidden border border-white/[0.08]">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.04] border-b border-white/[0.06]">
          <Code2 size={11} className="text-white/35" />
          <span className="text-[9px] font-mono text-white/40 uppercase tracking-wider">{lang}</span>
        </div>
        <pre className="px-3 py-2.5 text-[11px] font-mono text-white/75 leading-relaxed whitespace-pre overflow-x-auto bg-[#0d0d0d]">
          {code}
        </pre>
      </div>
    )
    last = m.index + m[0].length
  }
  if (last < text.length) {
    parts.push(<span key={key++} className="whitespace-pre-wrap break-words">{text.slice(last)}</span>)
  }
  return parts
}

function MessageBubble({ msg }: { msg: LocalMessage }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}
    >
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-white/8 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Cpu size={13} className="text-white/55" />
        </div>
      )}
      <div className={cn('max-w-[82%] space-y-1', isUser && 'items-end flex flex-col')}>
        <div className={cn(
          'px-4 py-3 rounded-2xl text-[13px] leading-relaxed',
          isUser
            ? 'bg-white/12 text-white/90 rounded-br-sm'
            : 'bg-white/[0.04] border border-white/[0.06] text-white/82 rounded-bl-sm',
          msg.error && 'border-red-500/25 bg-red-500/5 text-red-300/80',
        )}>
          {msg.error ? (
            <div className="flex items-center gap-2">
              <AlertCircle size={13} className="text-red-400 flex-shrink-0" />
              <span>{msg.error}</span>
            </div>
          ) : msg.streaming && !msg.content ? (
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          ) : (
            <div>{renderContent(msg.content)}</div>
          )}
        </div>
        {msg.toolExecutions && msg.toolExecutions.length > 0 && (
          <div className="w-full space-y-1">
            {msg.toolExecutions.map((exec, i) => <ToolCard key={i} exec={exec} />)}
          </div>
        )}
        {msg.usage && (
          <p className="text-[10px] text-white/20 font-mono px-1">
            {msg.usage.in}↑ {msg.usage.out}↓ tokens
          </p>
        )}
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-[11px] text-white/60 font-medium">U</span>
        </div>
      )}
    </motion.div>
  )
}

// ── Summary banner ────────────────────────────────────────────────────────────
function SummaryBanner({ text }: { text: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mx-4 my-3 rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
      <button className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-left" onClick={() => setOpen(o => !o)}>
        <BookOpen size={11} className="text-white/30" />
        <span className="text-white/35 flex-1">Context summary</span>
        <ChevronDown size={10} className={cn('text-white/20 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="px-3 pb-3 text-[11px] text-white/45 leading-relaxed border-t border-white/[0.04] pt-2">{text}</div>
      )}
    </div>
  )
}

// ── Main Chat ─────────────────────────────────────────────────────────────────
export function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [messages, setMessages] = useState<LocalMessage[]>([])
  const [summary, setSummary] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [enableTools, setEnableTools] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const health = useHealthStore()
  const modelOnline = health.overall?.status === 'ok' || health.overall?.status === 'healthy'

  // ── Attachment state ───────────────────────────────────────────────────────
  const [attachments, setAttachments] = useState<AttachedFile[]>([])
  const attachInputRef = useRef<HTMLInputElement>(null)

  // ── Model switcher ─────────────────────────────────────────────────────────
  const [models, setModels] = useState<ModelProfile[]>([])
  const [activeModelId, setActiveModelId] = useState<string>('')
  const [modelDropOpen, setModelDropOpen] = useState(false)
  const [modelSwitching, setModelSwitching] = useState(false)
  const modelDropRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listModels().then(ms => setModels(ms.filter(m => !m.model_id.endsWith(':cloud')))).catch(() => {})
    getActiveModel().then(m => setActiveModelId(m.model_id)).catch(() => {})
  }, [])

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (modelDropRef.current && !modelDropRef.current.contains(e.target as Node))
        setModelDropOpen(false)
    }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  const handleSwitchModel = async (modelId: string) => {
    if (modelId === activeModelId) { setModelDropOpen(false); return }
    setModelSwitching(true)
    try {
      await setActiveModel(modelId)
      setActiveModelId(modelId)
      setModels(prev => prev.map(m => ({ ...m, is_active: m.model_id === modelId })))
      toast.success(`Model → ${modelId}`)
    } catch (e: any) {
      toast.error(`Switch failed: ${e?.message}`)
    } finally { setModelSwitching(false); setModelDropOpen(false) }
  }

  // ── Attachment parsing ─────────────────────────────────────────────────────
  const parseAttachment = useCallback(async (af: AttachedFile) => {
    const update = (patch: Partial<AttachedFile>) =>
      setAttachments(prev => prev.map(a => a.id === af.id ? { ...a, ...patch } : a))
    try {
      const form = new FormData()
      form.append('file', af.file)
      form.append('ingest', 'false')
      const r = await fetch(`${BASE_URL}/api/v1/documents/upload`, { method: 'POST', body: form })
      if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail ?? `HTTP ${r.status}`) }
      const data = await r.json()
      update({ status: 'ready', text: data.text ?? '', charCount: data.char_count ?? 0 })
    } catch (e: any) {
      update({ status: 'error', error: e.message })
      toast.error(`Parse failed: ${af.file.name}`)
    }
  }, [])

  const handleAttachFiles = (files: File[]) => {
    const valid = files.filter(f => {
      const ext = '.' + (f.name.split('.').pop()?.toLowerCase() ?? '')
      return ATTACH_EXTS.includes(ext)
    })
    if (!valid.length) { toast.warning('File type not supported'); return }
    const entries: AttachedFile[] = valid.map(f => ({ id: `${f.name}-${Date.now()}`, file: f, status: 'parsing' }))
    setAttachments(prev => [...entries, ...prev])
    entries.forEach(af => parseAttachment(af))
  }

  // ── Sessions ───────────────────────────────────────────────────────────────
  const loadSessions = useCallback(async () => {
    try { const list = await listChatSessions(); setSessions(list) }
    catch {} finally { setSessionsLoading(false) }
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const openSession = async (id: string) => {
    setActiveId(id); setMessages([]); setSummary(null)
    try {
      const detail = await getChatSession(id)
      setSummary(detail.summary ?? null)
      setMessages(detail.messages.filter(m => m.role !== 'tool').map(m => ({
        id: m.message_id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        toolExecutions: m.tool_calls?.map((tc, i) => ({
          tool: tc.tool, args: tc.args ?? {},
          result: m.tool_results?.[i] ? JSON.stringify((m.tool_results[i] as any).result ?? m.tool_results[i]).slice(0, 400) : undefined,
          success: (m.tool_results?.[i] as any)?.success ?? true,
          done: true,
        })),
      })))
    } catch {}
  }

  const newSession = async () => {
    try {
      const sess = await createChatSession('New Chat')
      setSessions(prev => [sess, ...prev]); setActiveId(sess.session_id); setMessages([]); setSummary(null)
    } catch (e: any) { toast.error(`Session failed: ${e?.message}`) }
  }

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await deleteChatSession(id)
      setSessions(prev => prev.filter(s => s.session_id !== id))
      if (activeId === id) { setActiveId(null); setMessages([]) }
    } catch (e: any) { toast.error(`Delete failed: ${e?.message}`) }
  }

  // ── Workflow detection ─────────────────────────────────────────────────────
  const _WORKFLOW_RE = [
    /open\s+(word|excel|powerpoint|notepad|chrome|browser)/i,
    /create\s+a?\s*(word|excel|pptx?|spreadsheet|presentation|document|docx?)/i,
    /write\s+(a\s+)?(document|report|summary|email|letter)/i,
    /search\s+(windows|taskbar)\s+for\s+/i,
    /open\s+(microsoft|ms)\s+(word|excel|powerpoint)/i,
    /send\s+an?\s+email|compose\s+an?\s+email/i,
  ]
  const looksLikeWorkflow = (t: string) => _WORKFLOW_RE.some(r => r.test(t))

  // ── Send ───────────────────────────────────────────────────────────────────
  const send = async () => {
    const text = input.trim()
    if ((!text && !attachments.some(a => a.status === 'ready')) || sending) return

    if (text && looksLikeWorkflow(text) && attachments.length === 0) {
      setInput(''); setSending(true)
      try {
        const newRun = await createRun({ goal: text })
        const uid = `user-${Date.now()}`, aid = `asst-${Date.now()}`
        setMessages(prev => [...prev,
          { id: uid, role: 'user', content: text },
          { id: aid, role: 'assistant', content: `✓ Workflow started — \`${newRun.run_id.slice(0, 12)}\`\n\nGo to **Runs** tab to watch it execute.`, streaming: false },
        ])
        toast.success('Workflow started')
      } catch (e: any) { toast.error(`Failed: ${e?.message}`) }
      finally { setSending(false) }
      return
    }

    let sid = activeId
    if (!sid) {
      try {
        const sess = await createChatSession((text || 'File chat').slice(0, 60))
        setSessions(prev => [sess, ...prev]); sid = sess.session_id; setActiveId(sid)
      } catch (e: any) { toast.error(`Session error: ${e?.message}`); return }
    }

    setInput(''); setSending(true)
    const readyAttachments = attachments.filter(a => a.status === 'ready')
    setAttachments([])

    const attachLabel = readyAttachments.length > 0
      ? `\n\n📎 ${readyAttachments.map(a => a.file.name).join(', ')}` : ''

    const uid = `user-${Date.now()}`, aid = `asst-${Date.now()}`
    setMessages(prev => [...prev,
      { id: uid, role: 'user', content: (text || '(files attached)') + attachLabel },
      { id: aid, role: 'assistant', content: '', streaming: true },
    ])

    const docContext = readyAttachments.length > 0
      ? readyAttachments.map(a => `=== ${a.file.name} ===\n${a.text ?? ''}`.trim()).join('\n\n') : undefined
    const docName = readyAttachments.length === 1 ? readyAttachments[0].file.name
      : readyAttachments.length > 1 ? `${readyAttachments.length} files` : undefined

    let accContent = ''
    const toolMap = new Map<string, ToolExecution>()

    try {
      for await (const event of streamChatMessage(sid, text || 'Summarize and analyze the attached file(s).', enableTools, undefined, docContext, docName)) {
        if (event.type === 'delta') {
          accContent += event.content
          setMessages(prev => prev.map(m => m.id === aid ? { ...m, content: accContent, streaming: true } : m))
        } else if (event.type === 'tool_start') {
          toolMap.set(event.tool, { tool: event.tool, args: event.args, done: false })
          setMessages(prev => prev.map(m => m.id === aid ? { ...m, toolExecutions: [...toolMap.values()] } : m))
        } else if (event.type === 'tool_result') {
          const exec = toolMap.get(event.tool)
          if (exec) { exec.result = event.result; exec.success = event.success; exec.done = true }
          setMessages(prev => prev.map(m => m.id === aid ? { ...m, toolExecutions: [...toolMap.values()] } : m))
        } else if (event.type === 'summary') {
          setSummary(event.text)
        } else if (event.type === 'done') {
          setMessages(prev => prev.map(m => m.id === aid ? { ...m, streaming: false, usage: event.usage } : m))
          if (event.message_id) setSessions(prev => prev.map(s => s.session_id === sid ? { ...s, message_count: (s.message_count ?? 0) + 2 } : s))
        } else if (event.type === 'error') {
          setMessages(prev => prev.map(m => m.id === aid ? { ...m, streaming: false, error: event.message } : m))
        }
      }
    } catch (e: any) {
      setMessages(prev => prev.map(m => m.id === aid ? { ...m, streaming: false, error: e?.message ?? 'Stream failed' } : m))
    } finally { setSending(false); inputRef.current?.focus() }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  // ── Detect if input looks like code ────────────────────────────────────────
  const looksLikeCode = input.trimStart().startsWith('```') || input.includes('\n') && /[{}();]/.test(input)

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex-1 flex min-h-0 overflow-hidden">

      {/* ── Session sidebar ─────────────────────────────────────────────── */}
      <div className="w-56 flex-shrink-0 border-r border-white/[0.05] flex flex-col bg-[#0c0c0c]">
        <div className="flex items-center justify-between px-3 py-3 border-b border-white/[0.05]">
          <span className="text-[12px] font-medium text-white/60">Chats</span>
          <button onClick={newSession} className="p-1.5 rounded text-white/30 hover:text-white/70 hover:bg-white/6 transition-colors" title="New chat">
            <Plus size={13} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {sessionsLoading ? (
            <div className="p-3 space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-9 rounded-lg" />)}</div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center">
              <p className="text-[11px] text-white/25">No chats yet</p>
              <button onClick={newSession} className="mt-2 text-[11px] text-white/40 hover:text-white/70 transition-colors">Start one →</button>
            </div>
          ) : sessions.map(s => (
            <div key={s.session_id} onClick={() => openSession(s.session_id)}
              className={cn('group flex items-center gap-2 px-3 py-2.5 mx-1 rounded-lg cursor-pointer transition-colors',
                activeId === s.session_id ? 'bg-white/8 text-white/85' : 'text-white/45 hover:bg-white/4 hover:text-white/70')}>
              <MessageSquare size={12} className="flex-shrink-0 opacity-60" />
              <span className="flex-1 text-[11px] truncate leading-snug">{s.title}</span>
              <button onClick={e => deleteSession(s.session_id, e)} className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-white/25 hover:text-red-400 transition-all">
                <Trash2 size={10} />
              </button>
            </div>
          ))}
        </div>

        {/* ── Footer: model switcher + tools toggle ── */}
        <div className="px-3 py-2.5 border-t border-white/[0.05] space-y-2" ref={modelDropRef}>
          {/* Model button */}
          <button onClick={() => setModelDropOpen(v => !v)}
            className={cn('w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-colors group',
              modelDropOpen ? 'bg-white/[0.06]' : 'hover:bg-white/[0.04]')}>
            {modelSwitching
              ? <Loader2 size={9} className="animate-spin text-white/40 flex-shrink-0" />
              : <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', modelOnline ? 'bg-emerald-400' : 'bg-white/20')} />}
            <span className="text-[10px] text-white/55 font-mono truncate flex-1">
              {activeModelId || health.model?.model_id || 'gemma4:e4b'}
            </span>
            <ChevronDown size={9} className={cn('text-white/25 transition-transform flex-shrink-0', modelDropOpen && 'rotate-180')} />
          </button>

          <AnimatePresence>
            {modelDropOpen && models.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                transition={{ duration: 0.1 }}
                className="rounded-lg border border-white/[0.09] bg-[#111] shadow-xl overflow-hidden mb-1">
                <p className="text-[8px] uppercase tracking-widest text-white/25 px-2.5 pt-2 pb-1 font-semibold">Switch model</p>
                <div className="max-h-[160px] overflow-y-auto">
                  {models.map(m => (
                    <button key={m.model_id} onClick={() => handleSwitchModel(m.model_id)}
                      className={cn('w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-[10px] transition-colors hover:bg-white/[0.05]',
                        m.model_id === activeModelId && 'bg-white/[0.04]')}>
                      <span className="font-mono truncate flex-1 text-white/60">{m.model_id}</span>
                      {m.capabilities?.vision && <span className="text-[8px] text-blue-400/60">👁</span>}
                      {m.model_id === activeModelId && <Check size={9} className="text-emerald-400 flex-shrink-0" />}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Zap size={9} className="text-emerald-400/60" />
              <span className="text-[9px] text-white/25 font-mono">CUDA · GPU</span>
            </div>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <div className={cn('w-7 h-4 rounded-full transition-colors relative', enableTools ? 'bg-emerald-500/40' : 'bg-white/10')}
                onClick={() => setEnableTools(t => !t)}>
                <span className={cn('absolute top-0.5 w-3 h-3 rounded-full bg-white/70 transition-all', enableTools ? 'left-3.5' : 'left-0.5')} />
              </div>
              <span className="text-[9px] text-white/30">Tools</span>
            </label>
          </div>
        </div>
      </div>

      {/* ── Main chat area ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0">
        {!activeId ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 select-none">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="text-center max-w-sm">
              <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/[0.07] flex items-center justify-center mx-auto mb-5">
                <Cpu size={22} className="text-white/35" />
              </div>
              <h2 className="text-[18px] font-light text-white/75 mb-2">SyncNode Chat</h2>
              <p className="text-[12px] text-white/35 leading-relaxed mb-4">
                A full coding agent with terminal access, code execution, document parsing (PDF, images, Word, Excel), and local AI.
              </p>
              <div className="flex flex-wrap gap-1.5 justify-center mb-6">
                {['Python', 'JS', 'C++', 'PowerShell', 'PDF', 'OCR', 'Excel', 'Terminal'].map(cap => (
                  <span key={cap} className="text-[9px] font-mono px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-white/35">{cap}</span>
                ))}
              </div>
              <button onClick={newSession}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] text-white/70 border border-white/[0.1] hover:bg-white/5 hover:text-white/90 transition-all mx-auto">
                <Plus size={14} /> New conversation
              </button>
            </motion.div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto py-4 px-4 space-y-4">
              {summary && <SummaryBanner text={summary} />}
              {messages.length === 0 && !sending && (
                <div className="flex items-center justify-center h-32">
                  <p className="text-[12px] text-white/25">Send a message to start</p>
                </div>
              )}
              {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
              <div ref={bottomRef} />
            </div>

            {/* ── Input bar ── */}
            <div className="px-4 pb-4 flex-shrink-0">
              <input ref={attachInputRef} type="file" multiple accept={ATTACH_EXTS.join(',')} className="hidden"
                onChange={e => { handleAttachFiles(Array.from(e.target.files ?? [])); e.target.value = '' }} />

              {/* Attachment chips */}
              <AnimatePresence>
                {attachments.length > 0 && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="flex flex-wrap gap-1.5 mb-2 overflow-hidden">
                    {attachments.map(af => (
                      <motion.div key={af.id} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}
                        className={cn('flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-mono',
                          af.status === 'ready'   && 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400/80',
                          af.status === 'parsing' && 'border-white/[0.08] bg-white/[0.03] text-white/40',
                          af.status === 'error'   && 'border-red-500/20 bg-red-500/5 text-red-400/70')}>
                        {attachFileIcon(af.file.name)}
                        <span className="max-w-[120px] truncate">{af.file.name}</span>
                        {af.status === 'parsing' && <Loader2 size={9} className="animate-spin opacity-60" />}
                        {af.status === 'ready'   && <CheckCircle2 size={9} className="text-emerald-400/70" />}
                        {af.status === 'error'   && <AlertCircle size={9} className="text-red-400/70" />}
                        {af.charCount != null && af.status === 'ready' && (
                          <span className="text-white/25 ml-0.5">{(af.charCount / 1000).toFixed(1)}k</span>
                        )}
                        <button onClick={() => setAttachments(prev => prev.filter(a => a.id !== af.id))}
                          className="ml-0.5 text-white/30 hover:text-white/70">
                          <X size={9} />
                        </button>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Text box */}
              <div className={cn(
                'flex items-end gap-2 rounded-2xl border bg-white/[0.03] px-3 py-3 transition-colors',
                looksLikeCode ? 'border-yellow-500/20 focus-within:border-yellow-500/30' : 'border-white/[0.08] focus-within:border-white/[0.12]'
              )}
                onDragOver={e => e.preventDefault()}
                onDrop={e => { e.preventDefault(); handleAttachFiles(Array.from(e.dataTransfer.files)) }}>

                {/* Attach */}
                <button onClick={() => attachInputRef.current?.click()} disabled={sending}
                  className={cn('flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-colors',
                    attachments.length > 0 ? 'text-emerald-400/70' : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]',
                    sending && 'opacity-40 pointer-events-none')}
                  title="Attach file (PDF, image, code, document…)">
                  <Paperclip size={13} />
                </button>

                {/* Terminal hint icon when code detected */}
                {looksLikeCode && (
                  <div className="flex-shrink-0 w-7 h-7 flex items-center justify-center" title="Code detected — will be executed">
                    <Terminal size={12} className="text-yellow-400/60" />
                  </div>
                )}

                <textarea ref={inputRef} value={input}
                  onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                  placeholder={
                    attachments.some(a => a.status === 'ready')
                      ? 'Ask about the file, summarise it, run analysis…'
                      : enableTools
                        ? "Ask anything · run code · open files · read PDFs · terminal…"
                        : 'Ask me anything…'
                  }
                  rows={1} disabled={sending}
                  className={cn('flex-1 bg-transparent text-[13px] placeholder:text-white/22 outline-none resize-none leading-relaxed max-h-48 overflow-y-auto disabled:opacity-50',
                    looksLikeCode ? 'text-yellow-100/80 font-mono text-[12px]' : 'text-white/80')}
                  style={{ scrollbarWidth: 'none' }}
                  onInput={e => {
                    const el = e.currentTarget; el.style.height = 'auto'
                    el.style.height = Math.min(el.scrollHeight, 192) + 'px'
                  }} />

                <button onClick={send}
                  disabled={(!input.trim() && !attachments.some(a => a.status === 'ready')) || sending}
                  className={cn('flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all',
                    (input.trim() || attachments.some(a => a.status === 'ready')) && !sending
                      ? 'bg-white/15 text-white/80 hover:bg-white/22' : 'bg-white/5 text-white/20 cursor-not-allowed')}>
                  {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                </button>
              </div>

              <p className="text-[10px] text-white/18 mt-1.5 px-1">
                Enter · Shift+Enter newline · {enableTools ? 'Tools on' : 'Tools off'} · Drop files · PDF/OCR/Code/Terminal supported
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
