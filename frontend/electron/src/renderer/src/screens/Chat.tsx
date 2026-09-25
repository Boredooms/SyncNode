import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Plus, Trash2, MessageSquare, Wrench, Cpu,
  ChevronDown, Zap, Loader2, AlertCircle, BookOpen, X,
  Paperclip, FileText, FileSpreadsheet, Presentation, File,
  CheckCircle2,
} from 'lucide-react'
import { cn } from '../lib/utils'
import {
  createChatSession, listChatSessions, getChatSession,
  deleteChatSession, clearChatSession, streamChatMessage,
  createRun,
} from '../lib/api/client'
import type { ChatSession, ChatMessage, ChatStreamEvent } from '../lib/api/types'
import { useHealthStore } from '../stores/healthStore'
import { Skeleton, EmptyState } from '../components/ui/primitives'
import { toast } from 'sonner'

const BASE_URL = 'http://127.0.0.1:8000'

// ── Supported attachment types ────────────────────────────────────────────────
const ATTACH_EXTS = ['.docx','.xlsx','.pptx','.pdf','.txt','.md','.csv','.json','.py','.ts','.js','.html']

// ── Attachment state ──────────────────────────────────────────────────────────
interface AttachedFile {
  id: string
  file: File
  status: 'parsing' | 'ready' | 'error'
  text?: string          // extracted text from the backend
  charCount?: number
  error?: string
}

function attachFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['docx','doc'].includes(ext))         return <FileText size={11} className="text-blue-400/70" />
  if (['xlsx','xls','csv'].includes(ext))   return <FileSpreadsheet size={11} className="text-emerald-400/70" />
  if (['pptx','ppt'].includes(ext))         return <Presentation size={11} className="text-orange-400/70" />
  if (ext === 'pdf')                         return <FileText size={11} className="text-red-400/70" />
  return <File size={11} className="text-white/40" />
}

// ── Types for local streaming state ──────────────────────────────────────────

interface ToolExecution {
  tool: string
  args: Record<string, unknown>
  result?: string
  success?: boolean
  done: boolean
}

interface LocalMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolExecutions?: ToolExecution[]
  streaming?: boolean
  error?: string
  usage?: { in: number; out: number }
}

// ── Tool execution card ───────────────────────────────────────────────────────

function ToolCard({ exec }: { exec: ToolExecution }) {
  const [open, setOpen] = useState(false)
  const color = exec.done
    ? exec.success ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'
    : 'border-white/[0.07] bg-white/[0.02]'
  const dot = exec.done
    ? exec.success ? 'bg-emerald-400' : 'bg-red-400'
    : 'bg-amber-400 animate-pulse'

  return (
    <div className={cn('rounded-xl border text-[11px] font-mono overflow-hidden mt-2', color)}>
      <button
        className="w-full flex items-center gap-2 px-3 py-2 text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', dot)} />
        <Wrench size={11} className="text-white/40 flex-shrink-0" />
        <span className="text-white/70 flex-1 truncate">{exec.tool}</span>
        {exec.done && (
          <span className={exec.success ? 'text-emerald-400/70' : 'text-red-400/60'}>
            {exec.success ? 'done' : 'failed'}
          </span>
        )}
        {!exec.done && <Loader2 size={10} className="animate-spin text-white/35" />}
        <ChevronDown size={10} className={cn('text-white/25 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-1.5 border-t border-white/[0.05] pt-2">
          {Object.keys(exec.args).length > 0 && (
            <div>
              <p className="text-white/25 mb-1">args</p>
              <pre className="text-white/55 text-[10px] leading-tight whitespace-pre-wrap break-all">
                {JSON.stringify(exec.args, null, 2).slice(0, 400)}
              </pre>
            </div>
          )}
          {exec.result && (
            <div>
              <p className="text-white/25 mb-1">result</p>
              <pre className="text-white/55 text-[10px] leading-tight whitespace-pre-wrap break-all">
                {exec.result.slice(0, 400)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Message bubble ────────────────────────────────────────────────────────────

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
      <div className={cn('max-w-[78%] space-y-1', isUser && 'items-end flex flex-col')}>
        <div
          className={cn(
            'px-4 py-3 rounded-2xl text-[13px] leading-relaxed',
            isUser
              ? 'bg-white/12 text-white/90 rounded-br-sm'
              : 'bg-white/[0.04] border border-white/[0.06] text-white/82 rounded-bl-sm',
            msg.streaming && 'animate-pulse-subtle',
            msg.error && 'border-red-500/25 bg-red-500/5 text-red-300/80',
          )}
        >
          {msg.error ? (
            <div className="flex items-center gap-2">
              <AlertCircle size={13} className="text-red-400 flex-shrink-0" />
              <span>{msg.error}</span>
            </div>
          ) : (
            <span className="whitespace-pre-wrap break-words">{msg.content}</span>
          )}
          {msg.streaming && !msg.content && (
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          )}
        </div>

        {/* Tool executions */}
        {msg.toolExecutions && msg.toolExecutions.length > 0 && (
          <div className="w-full space-y-1">
            {msg.toolExecutions.map((exec, i) => (
              <ToolCard key={i} exec={exec} />
            ))}
          </div>
        )}

        {/* Usage stats */}
        {msg.usage && (
          <p className="text-[10px] text-white/20 font-mono px-1">
            {msg.usage.in} in · {msg.usage.out} out tokens
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
      <button
        className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <BookOpen size={11} className="text-white/30" />
        <span className="text-white/35 flex-1">Context summary</span>
        <ChevronDown size={10} className={cn('text-white/20 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="px-3 pb-3 text-[11px] text-white/45 leading-relaxed border-t border-white/[0.04] pt-2">
          {text}
        </div>
      )}
    </div>
  )
}

// ── Main Chat screen ──────────────────────────────────────────────────────────

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

  const parseAttachment = useCallback(async (af: AttachedFile) => {
    const update = (patch: Partial<AttachedFile>) =>
      setAttachments(prev => prev.map(a => a.id === af.id ? { ...a, ...patch } : a))
    try {
      const form = new FormData()
      form.append('file', af.file)
      form.append('ingest', 'false')
      const r = await fetch(`${BASE_URL}/api/v1/documents/upload`, { method: 'POST', body: form })
      if (!r.ok) {
        const e = await r.json().catch(() => ({}))
        throw new Error(e.detail ?? `HTTP ${r.status}`)
      }
      const data = await r.json()
      update({ status: 'ready', text: data.text ?? '', charCount: data.char_count ?? 0 })
    } catch (e: any) {
      update({ status: 'error', error: e.message })
      toast.error(`Could not parse ${af.file.name}: ${e.message}`)
    }
  }, [])

  const handleAttachFiles = (files: File[]) => {
    const valid = files.filter(f => {
      const ext = '.' + (f.name.split('.').pop()?.toLowerCase() ?? '')
      return ATTACH_EXTS.includes(ext)
    })
    if (!valid.length) { toast.warning('No supported files selected'); return }
    const entries: AttachedFile[] = valid.map(f => ({
      id: `${f.name}-${Date.now()}`,
      file: f, status: 'parsing',
    }))
    setAttachments(prev => [...entries, ...prev])
    entries.forEach(af => parseAttachment(af))
  }

  const removeAttachment = (id: string) =>
    setAttachments(prev => prev.filter(a => a.id !== id))

  // ── Load sessions ──────────────────────────────────────────────────────────
  const loadSessions = useCallback(async () => {
    try {
      const list = await listChatSessions()
      setSessions(list)
    } catch { /* silent */ }
    finally { setSessionsLoading(false) }
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  // ── Scroll to bottom on new messages ──────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Open / create session ──────────────────────────────────────────────────
  const openSession = async (id: string) => {
    setActiveId(id)
    setMessages([])
    setSummary(null)
    try {
      const detail = await getChatSession(id)
      setSummary(detail.summary ?? null)
      setMessages(
        detail.messages
          .filter((m) => m.role !== 'tool')
          .map((m) => ({
            id: m.message_id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            toolExecutions: m.tool_calls?.map((tc, i) => ({
              tool: tc.tool,
              args: tc.args ?? {},
              result: m.tool_results?.[i]
                ? JSON.stringify((m.tool_results[i] as any).result ?? m.tool_results[i]).slice(0, 400)
                : undefined,
              success: (m.tool_results?.[i] as any)?.success ?? true,
              done: true,
            })),
          }))
      )
    } catch { /* silent */ }
  }

  const newSession = async () => {
    try {
      const sess = await createChatSession('New Chat')
      setSessions((prev) => [sess, ...prev])
      setActiveId(sess.session_id)
      setMessages([])
      setSummary(null)
    } catch (e: any) {
      toast.error(`Failed to create session: ${e?.message}`)
    }
  }

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await deleteChatSession(id)
      setSessions((prev) => prev.filter((s) => s.session_id !== id))
      if (activeId === id) { setActiveId(null); setMessages([]) }
    } catch (e: any) {
      toast.error(`Delete failed: ${e?.message}`)
    }
  }

  // ── Detect workflow intent — creates a real run instead of chatting ─────────
  const _WORKFLOW_RE = [
    /open\s+(word|excel|powerpoint|notepad|chrome|browser)/i,
    /create\s+a?\s*(word|excel|pptx?|spreadsheet|presentation|document|docx?)/i,
    /write\s+(a\s+)?(document|report|summary|email|letter)/i,
    /search\s+(windows|taskbar)\s+for\s+/i,
    /take\s+a\s+screenshot/i,
    /open\s+(microsoft|ms)\s+(word|excel|powerpoint)/i,
    /launch\s+(word|excel|powerpoint)/i,
    /send\s+an?\s+email|compose\s+an?\s+email/i,
    /attach\s+.*(file|doc|document)/i,
  ]
  const looksLikeWorkflow = (t: string) => _WORKFLOW_RE.some((r) => r.test(t))

  // ── Send message ───────────────────────────────────────────────────────────
  const send = async () => {
    const text = input.trim()
    if (!text || sending) return

    // If it looks like a workflow command, create a real run
    if (looksLikeWorkflow(text)) {
      setInput('')
      setSending(true)
      try {
        const newRun = await createRun({ goal: text })
        const asstId = `asst-${Date.now()}`
        const uid = `user-${Date.now()}`
        setMessages((prev) => [
          ...prev,
          { id: uid, role: 'user', content: text },
          {
            id: asstId, role: 'assistant',
            content: `✓ Workflow started — Run \`${newRun.run_id.slice(0, 12)}\`\n\n**Goal:** ${text}\n\nGo to the **Runs** tab to watch it execute in real time.`,
            streaming: false,
          },
        ])
        toast.success('Workflow created', { description: 'Running in background — check Runs tab.' })
      } catch (e: any) {
        toast.error(`Failed to start workflow: ${e?.message}`)
      } finally {
        setSending(false)
      }
      return
    }

    // Ensure we have a session
    let sid = activeId
    if (!sid) {
      try {
        const sess = await createChatSession(text.slice(0, 60))
        setSessions((prev) => [sess, ...prev])
        sid = sess.session_id
        setActiveId(sid)
      } catch (e: any) {
        toast.error(`Could not create session: ${e?.message}`)
        return
      }
    }

    setInput('')
    setSending(true)

    // Collect ready attachments for this message, then clear them
    const readyAttachments = attachments.filter(a => a.status === 'ready')
    setAttachments([])

    // Build user bubble content — show attached file names
    const attachmentLabel = readyAttachments.length > 0
      ? `\n\n📎 ${readyAttachments.map(a => a.file.name).join(', ')}`
      : ''

    // Optimistic user bubble
    const userMsgId = `user-${Date.now()}`
    setMessages((prev) => [...prev, { id: userMsgId, role: 'user', content: text + attachmentLabel }])

    // Assistant streaming bubble
    const asstMsgId = `asst-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      { id: asstMsgId, role: 'assistant', content: '', streaming: true },
    ])

    let accContent = ''
    const toolMap = new Map<string, ToolExecution>()

    // Merge all attachment text into one context block
    const docContext = readyAttachments.length > 0
      ? readyAttachments.map(a => `=== ${a.file.name} ===\n${a.text ?? ''}`.trim()).join('\n\n')
      : undefined
    const docName = readyAttachments.length === 1
      ? readyAttachments[0].file.name
      : readyAttachments.length > 1
        ? `${readyAttachments.length} files`
        : undefined

    try {
      for await (const event of streamChatMessage(sid, text, enableTools, undefined, docContext, docName)) {
        if (event.type === 'delta') {
          accContent += event.content
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId ? { ...m, content: accContent, streaming: true } : m
            )
          )
        } else if (event.type === 'tool_start') {
          const exec: ToolExecution = { tool: event.tool, args: event.args, done: false }
          toolMap.set(event.tool, exec)
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, toolExecutions: [...Array.from(toolMap.values())] }
                : m
            )
          )
        } else if (event.type === 'tool_result') {
          const exec = toolMap.get(event.tool)
          if (exec) {
            exec.result = event.result
            exec.success = event.success
            exec.done = true
          }
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, toolExecutions: [...Array.from(toolMap.values())] }
                : m
            )
          )
        } else if (event.type === 'summary') {
          setSummary(event.text)
        } else if (event.type === 'done') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, streaming: false, usage: event.usage }
                : m
            )
          )
          // Update session title optimistically
          if (event.message_id) {
            setSessions((prev) =>
              prev.map((s) =>
                s.session_id === sid
                  ? { ...s, message_count: (s.message_count ?? 0) + 2 }
                  : s
              )
            )
          }
        } else if (event.type === 'error') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, streaming: false, error: event.message }
                : m
            )
          )
        }
      }
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? { ...m, streaming: false, error: e?.message ?? 'Stream failed' }
            : m
        )
      )
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex-1 flex min-h-0 overflow-hidden">

      {/* ── Session sidebar ── */}
      <div className="w-56 flex-shrink-0 border-r border-white/[0.05] flex flex-col bg-[#0c0c0c]">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-3 border-b border-white/[0.05]">
          <span className="text-[12px] font-medium text-white/60">Chats</span>
          <button
            onClick={newSession}
            className="p-1.5 rounded text-white/30 hover:text-white/70 hover:bg-white/6 transition-colors"
            title="New chat"
          >
            <Plus size={13} />
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-1">
          {sessionsLoading ? (
            <div className="p-3 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-9 rounded-lg" />)}
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center">
              <p className="text-[11px] text-white/25">No chats yet</p>
              <button
                onClick={newSession}
                className="mt-2 text-[11px] text-white/40 hover:text-white/70 transition-colors"
              >
                Start one →
              </button>
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => openSession(s.session_id)}
                className={cn(
                  'group flex items-center gap-2 px-3 py-2.5 mx-1 rounded-lg cursor-pointer transition-colors',
                  activeId === s.session_id
                    ? 'bg-white/8 text-white/85'
                    : 'text-white/45 hover:bg-white/4 hover:text-white/70'
                )}
              >
                <MessageSquare size={12} className="flex-shrink-0 opacity-60" />
                <span className="flex-1 text-[11px] truncate leading-snug">{s.title}</span>
                <button
                  onClick={(e) => deleteSession(s.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-white/25 hover:text-red-400 transition-all flex-shrink-0"
                >
                  <Trash2 size={10} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Model status footer */}
        <div className="px-3 py-2.5 border-t border-white/[0.05] space-y-1.5">
          <div className="flex items-center gap-2">
            <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0',
              modelOnline ? 'bg-emerald-400' : 'bg-white/20')} />
            <span className="text-[10px] text-white/35 font-mono truncate">
              {health.model?.model_id ?? 'gemma4:e4b'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Zap size={9} className="text-emerald-400/60" />
            <span className="text-[10px] text-white/25 font-mono">RTX 2050 · CUDA</span>
          </div>
          {/* Tools toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <div
              className={cn(
                'w-7 h-4 rounded-full transition-colors relative',
                enableTools ? 'bg-emerald-500/40' : 'bg-white/10'
              )}
              onClick={() => setEnableTools((t) => !t)}
            >
              <span className={cn(
                'absolute top-0.5 w-3 h-3 rounded-full bg-white/70 transition-all',
                enableTools ? 'left-3.5' : 'left-0.5'
              )} />
            </div>
            <span className="text-[10px] text-white/30">Tools</span>
          </label>
        </div>
      </div>

      {/* ── Main chat area ── */}
      <div className="flex-1 flex flex-col min-h-0">

        {!activeId ? (
          /* ── Empty state ── */
          <div className="flex-1 flex flex-col items-center justify-center p-8 select-none">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center max-w-sm"
            >
              <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/[0.07] flex items-center justify-center mx-auto mb-5">
                <Cpu size={22} className="text-white/35" />
              </div>
              <h2 className="text-[18px] font-light text-white/75 mb-2">SyncNode Chat</h2>
              <p className="text-[12px] text-white/35 leading-relaxed mb-6">
                Chat with your local Gemma model. Ask it to create documents, open apps, write reports — it uses real tools to get things done.
              </p>
              <button
                onClick={newSession}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] text-white/70 border border-white/[0.1] hover:bg-white/5 hover:text-white/90 transition-all mx-auto"
              >
                <Plus size={14} />
                New conversation
              </button>
            </motion.div>
          </div>
        ) : (
          <>
            {/* ── Message list ── */}
            <div className="flex-1 overflow-y-auto py-4 px-4 space-y-4">
              {/* Context summary banner */}
              {summary && <SummaryBanner text={summary} />}

              {messages.length === 0 && !sending && (
                <div className="flex items-center justify-center h-32">
                  <p className="text-[12px] text-white/25">Send a message to start the conversation</p>
                </div>
              )}

              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              <div ref={bottomRef} />
            </div>

            {/* ── Input bar ── */}
            <div className="px-4 pb-4 flex-shrink-0">

              {/* Hidden file input */}
              <input
                ref={attachInputRef}
                type="file"
                multiple
                accept={ATTACH_EXTS.join(',')}
                className="hidden"
                onChange={(e) => {
                  handleAttachFiles(Array.from(e.target.files ?? []))
                  e.target.value = ''
                }}
              />

              {/* Attachment chips — shown above the text box */}
              <AnimatePresence>
                {attachments.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex flex-wrap gap-1.5 mb-2 overflow-hidden"
                  >
                    {attachments.map(af => (
                      <motion.div
                        key={af.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className={cn(
                          'flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-mono',
                          af.status === 'ready'   && 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400/80',
                          af.status === 'parsing' && 'border-white/[0.08] bg-white/[0.03] text-white/40',
                          af.status === 'error'   && 'border-red-500/20 bg-red-500/5 text-red-400/70',
                        )}
                      >
                        {attachFileIcon(af.file.name)}
                        <span className="max-w-[120px] truncate">{af.file.name}</span>
                        {af.status === 'parsing' && <Loader2 size={9} className="animate-spin opacity-60" />}
                        {af.status === 'ready'   && <CheckCircle2 size={9} className="text-emerald-400/70" />}
                        {af.status === 'error'   && <AlertCircle size={9} className="text-red-400/70" aria-label={af.error} />}
                        {af.charCount != null && af.status === 'ready' && (
                          <span className="text-white/25 ml-0.5">{(af.charCount / 1000).toFixed(1)}k</span>
                        )}
                        <button
                          onClick={() => removeAttachment(af.id)}
                          className="ml-0.5 text-white/30 hover:text-white/70 transition-colors"
                        >
                          <X size={9} />
                        </button>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Text input + buttons */}
              <div
                className="flex items-end gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-3 py-3 focus-within:border-white/[0.12] transition-colors"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  handleAttachFiles(Array.from(e.dataTransfer.files))
                }}
              >
                {/* Attach button */}
                <button
                  onClick={() => attachInputRef.current?.click()}
                  disabled={sending}
                  className={cn(
                    'flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-colors',
                    attachments.length > 0
                      ? 'text-emerald-400/70 hover:bg-white/[0.06]'
                      : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]',
                    sending && 'opacity-40 pointer-events-none',
                  )}
                  title="Attach a document"
                >
                  <Paperclip size={13} />
                </button>

                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    attachments.some(a => a.status === 'ready')
                      ? 'Ask about the attached file, summarise it, or start a workflow…'
                      : enableTools
                        ? "Ask me anything or say 'create a report', 'open Word'…"
                        : 'Ask me anything…'
                  }
                  rows={1}
                  disabled={sending}
                  className="flex-1 bg-transparent text-[13px] text-white/80 placeholder:text-white/22 outline-none resize-none leading-relaxed max-h-40 overflow-y-auto disabled:opacity-50"
                  style={{ scrollbarWidth: 'none' }}
                  onInput={(e) => {
                    const el = e.currentTarget
                    el.style.height = 'auto'
                    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
                  }}
                />
                <button
                  onClick={send}
                  disabled={(!input.trim() && !attachments.some(a => a.status === 'ready')) || sending}
                  className={cn(
                    'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all',
                    (input.trim() || attachments.some(a => a.status === 'ready')) && !sending
                      ? 'bg-white/15 text-white/80 hover:bg-white/22'
                      : 'bg-white/5 text-white/20 cursor-not-allowed'
                  )}
                >
                  {sending
                    ? <Loader2 size={14} className="animate-spin" />
                    : <Send size={14} />
                  }
                </button>
              </div>
              <p className="text-[10px] text-white/18 mt-1.5 px-1">
                Enter to send · Shift+Enter for newline · {enableTools ? 'Tools on' : 'Tools off'} · Drop files to attach
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
