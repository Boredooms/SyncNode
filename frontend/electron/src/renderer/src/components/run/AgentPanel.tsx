import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRunStore } from '../../stores/runStore'
import { useHealthStore } from '../../stores/healthStore'
import { useUIStore } from '../../stores/uiStore'
import { StatusDot } from '../ui/primitives'
import {
  PanelRight, Cpu, Bot, MessageSquare, Activity,
  Send, Loader2, Wrench, ChevronDown, AlertCircle,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import {
  createChatSession, streamChatMessage, createRun,
} from '../../lib/api/client'
import { toast } from 'sonner'
import type { ChatStreamEvent } from '../../lib/api/types'

interface AgentPanelProps {
  runId: string
}

// ── Inline tool execution card ────────────────────────────────────────────────
function MiniToolCard({
  tool, success, done,
}: { tool: string; success?: boolean; done: boolean }) {
  const dot = done
    ? (success ? 'bg-emerald-400' : 'bg-red-400')
    : 'bg-amber-400 animate-pulse'
  return (
    <div className="flex items-center gap-1.5 text-[10px] font-mono py-1 px-2 rounded bg-white/[0.03] border border-white/[0.05]">
      <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', dot)} />
      <Wrench size={9} className="text-white/30 flex-shrink-0" />
      <span className="text-white/55 truncate">{tool}</span>
      {done && (
        <span className={cn('ml-auto flex-shrink-0', success ? 'text-emerald-400/60' : 'text-red-400/50')}>
          {success ? '✓' : '✗'}
        </span>
      )}
      {!done && <Loader2 size={9} className="ml-auto animate-spin text-white/25 flex-shrink-0" />}
    </div>
  )
}

// ── Inline chat message ───────────────────────────────────────────────────────
interface ChatMsg {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  error?: string
  tools?: Array<{ tool: string; success?: boolean; done: boolean }>
}

function InlineChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={cn('flex gap-2', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="w-5 h-5 rounded-full bg-white/8 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Cpu size={10} className="text-white/45" />
        </div>
      )}
      <div className="max-w-[85%] space-y-1">
        <div
          className={cn(
            'px-3 py-2 rounded-xl text-[12px] leading-relaxed',
            isUser
              ? 'bg-white/10 text-white/85 rounded-br-sm'
              : 'bg-white/[0.04] border border-white/[0.06] text-white/78 rounded-bl-sm',
            msg.error && 'border-red-500/20 bg-red-500/5 text-red-300/80',
          )}
        >
          {msg.error ? (
            <div className="flex items-center gap-1.5">
              <AlertCircle size={11} className="text-red-400 flex-shrink-0" />
              <span className="text-[11px]">{msg.error}</span>
            </div>
          ) : msg.streaming && !msg.content ? (
            <span className="inline-flex gap-1">
              {[0, 150, 300].map((d) => (
                <span
                  key={d}
                  className="w-1 h-1 rounded-full bg-white/35 animate-bounce"
                  style={{ animationDelay: `${d}ms` }}
                />
              ))}
            </span>
          ) : (
            <span className="whitespace-pre-wrap">{msg.content}</span>
          )}
        </div>
        {msg.tools && msg.tools.length > 0 && (
          <div className="space-y-0.5">
            {msg.tools.map((t, i) => (
              <MiniToolCard key={i} tool={t.tool} success={t.success} done={t.done} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main AgentPanel ───────────────────────────────────────────────────────────
export function AgentPanel({ runId }: AgentPanelProps) {
  const runState = useRunStore((s) => s.runs[runId])
  const health = useHealthStore()
  const { setRightPanelCollapsed } = useUIStore()

  const [tab, setTab] = useState<'intelligence' | 'chat'>('intelligence')
  const [chatSessionId, setChatSessionId] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatSending, setChatSending] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const activeAgents = Object.values(runState?.activeAgents ?? {})
  const run = runState?.run
  const pendingApprovals = runState?.approvals.filter((a) => a.status === 'pending') ?? []
  const summaries = (runState?.sseEvents ?? [])
    .filter((e) => e.event_type === 'agent.plan_summary' || (e.event_type && e.event_type.includes('plan_summary')))
    .slice(-3)
    .reverse()

  // ── Auto-scroll chat ──────────────────────────────────────────────────────
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // ── Ensure a chat session exists ──────────────────────────────────────────
  const ensureSession = useCallback(async (): Promise<string | null> => {
    if (chatSessionId) return chatSessionId
    try {
      const title = run?.goal ? run.goal.slice(0, 55) + '…' : `Run ${runId.slice(0, 8)}`
      const sess = await createChatSession(`[Run] ${title}`, runId)
      setChatSessionId(sess.session_id)
      return sess.session_id
    } catch (e: any) {
      toast.error(`Could not start chat: ${e?.message}`)
      return null
    }
  }, [chatSessionId, run, runId])

  // ── Detect if the user is asking to DO something (agentic trigger) ──────────
  // If the message looks like a workflow command, create a real run instead of
  // (or in addition to) chatting. This is what makes the side panel "agentic".
  const _WORKFLOW_TRIGGERS = [
    /open\s+(word|excel|powerpoint|notepad|chrome|browser)/i,
    /create\s+a?\s*(word|excel|pptx?|spreadsheet|presentation|document|docx?)/i,
    /write\s+(a\s+)?(document|report|summary|email|letter)/i,
    /search\s+(windows|taskbar|for)\s+/i,
    /take\s+a\s+screenshot/i,
    /open\s+(microsoft|ms)\s+(word|excel|powerpoint)/i,
    /launch\s+(word|excel|powerpoint|notepad)/i,
    /attach\s+.*(file|doc|document)/i,
    /send\s+an?\s+email/i,
    /compose\s+an?\s+email/i,
  ]

  const _looksLikeWorkflow = (t: string) =>
    _WORKFLOW_TRIGGERS.some((re) => re.test(t))

  // ── Send message ──────────────────────────────────────────────────────────
  const sendChat = async () => {
    const text = chatInput.trim()
    if (!text || chatSending) return

    // If it looks like a workflow command AND no run is currently active,
    // create a real run so the full orchestrator pipeline handles it.
    if (_looksLikeWorkflow(text) && (!run || ['completed', 'failed', 'cancelled'].includes(run.status))) {
      try {
        const newRun = await createRun({ goal: text })
        toast(`Workflow started: ${newRun.run_id.slice(0, 8)}…`, { description: 'Check the Runs tab for progress.' })
        setChatMessages((prev) => [
          ...prev,
          { id: `u-${Date.now()}`, role: 'user', content: text },
          {
            id: `a-${Date.now()}`, role: 'assistant',
            content: `✓ Workflow created (${newRun.run_id.slice(0, 8)}). Running: ${text.slice(0, 80)}…\n\nWatch it execute in the Automation tab.`,
            streaming: false,
          },
        ])
        setChatInput('')
        return
      } catch (e: any) {
        // Fall through to normal chat if run creation fails
      }
    }

    const sid = await ensureSession()
    if (!sid) return

    setChatInput('')
    setChatSending(true)

    const userMsgId = `u-${Date.now()}`
    const asstMsgId = `a-${Date.now()}`

    setChatMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: text },
      { id: asstMsgId, role: 'assistant', content: '', streaming: true },
    ])

    let accContent = ''
    const toolMap = new Map<string, { tool: string; success?: boolean; done: boolean }>()

    // Build a context-enriched message that tells the model about the current run
    // The server loads full run context (steps/artifacts/memory) via run_id — no
    // need to duplicate it here. Just send the raw user text.
    const messageToSend = text

    try {
      for await (const event of streamChatMessage(sid, messageToSend, true, runId)) {
        if (event.type === 'delta') {
          accContent += event.content
          setChatMessages((prev) =>
            prev.map((m) => m.id === asstMsgId ? { ...m, content: accContent } : m)
          )
        } else if (event.type === 'tool_start') {
          toolMap.set(event.tool, { tool: event.tool, done: false })
          setChatMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, tools: Array.from(toolMap.values()) }
                : m
            )
          )
        } else if (event.type === 'tool_result') {
          const t = toolMap.get(event.tool)
          if (t) { t.done = true; t.success = event.success }
          setChatMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, tools: Array.from(toolMap.values()) }
                : m
            )
          )
        } else if (event.type === 'done') {
          setChatMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId ? { ...m, streaming: false } : m
            )
          )
        } else if (event.type === 'error') {
          setChatMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, streaming: false, error: event.message }
                : m
            )
          )
        }
      }
    } catch (e: any) {
      setChatMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? { ...m, streaming: false, error: e?.message ?? 'Failed' }
            : m
        )
      )
    } finally {
      setChatSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendChat()
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#0d0d0d] text-[12px]">

      {/* ── Header with tab switcher ── */}
      <div className="flex items-center border-b border-white/[0.05] min-h-[36px] flex-shrink-0">
        {/* Tab buttons */}
        <button
          onClick={() => setTab('intelligence')}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors border-b-2',
            tab === 'intelligence'
              ? 'text-white/70 border-white/30'
              : 'text-white/25 border-transparent hover:text-white/45'
          )}
        >
          <Activity size={11} />
          Intel
        </button>
        <button
          onClick={() => setTab('chat')}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors border-b-2',
            tab === 'chat'
              ? 'text-white/70 border-white/30'
              : 'text-white/25 border-transparent hover:text-white/45'
          )}
        >
          <MessageSquare size={11} />
          Chat
          {chatMessages.filter((m) => m.role === 'assistant').length > 0 && (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/70 ml-0.5" />
          )}
        </button>
        <div className="flex-1" />
        <button
          onClick={() => setRightPanelCollapsed(true)}
          className="text-white/20 hover:text-white/50 transition-colors p-2"
          title="Collapse panel"
        >
          <PanelRight size={13} />
        </button>
      </div>

      {/* ── Intelligence tab ── */}
      {tab === 'intelligence' && (
        <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
          {/* Current task */}
          {run && (
            <div className="px-3 py-3">
              <p className="text-[9px] uppercase tracking-widest text-white/25 mb-1.5 font-mono">Task Objective</p>
              <p className="text-[11px] text-white/70 leading-relaxed select-text break-words line-clamp-4">{run.goal}</p>
            </div>
          )}

          {/* Model */}
          <div className="px-3 py-3">
            <p className="text-[9px] uppercase tracking-widest text-white/25 mb-2 font-mono">Inference Engine</p>
            <div className="flex items-center gap-2 mb-1">
              <Cpu size={11} className="text-white/30" />
              <span className="text-[11px] text-white/70 font-mono font-medium">
                {health.model?.model_id ?? run?.model_id ?? 'gemma4:e4b'}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className={cn(
                'w-1.5 h-1.5 rounded-full',
                health.overall?.status === 'healthy' || health.overall?.status === 'ok'
                  ? 'bg-emerald-400' : 'bg-amber-400'
              )} />
              <span className="text-[10px] text-white/35 font-mono">
                {health.overall?.status === 'healthy' || health.overall?.status === 'ok'
                  ? 'OLLAMA / GPU ACCELERATED' : 'LOCAL ENGINE'}
              </span>
            </div>
          </div>

          {/* Active Agents */}
          {activeAgents.length > 0 && (
            <div className="px-3 py-3">
              <p className="text-[9px] uppercase tracking-widest text-white/25 mb-2 font-mono">
                Agents ({activeAgents.length})
              </p>
              <div className="space-y-1.5">
                {activeAgents.map((agent) => (
                  <div key={agent.agent_id} className="p-2 rounded bg-white/2 border border-white/[0.05] space-y-1">
                    <div className="flex items-center gap-2">
                      <StatusDot status={agent.status} />
                      <span className="flex-1 text-[11px] text-white/80 font-mono font-medium truncate">
                        {agent.agent_id}
                      </span>
                      <span className={cn(
                        'text-[9px] uppercase font-mono px-1 py-0.2 rounded',
                        agent.status === 'running' ? 'text-blue-400 bg-blue-500/10' :
                        agent.status === 'completed' ? 'text-emerald-400 bg-emerald-500/10' :
                        agent.status === 'failed' ? 'text-red-400 bg-red-500/10' :
                        'text-white/30 bg-white/5'
                      )}>
                        {agent.status}
                      </span>
                    </div>
                    {agent.action && (
                      <p className="text-[10px] text-white/40 truncate">{agent.action}</p>
                    )}
                    {agent.lastSummary && (
                      <p className="text-[10px] text-white/30 italic">{agent.lastSummary}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Plan summaries */}
          {summaries.length > 0 && (
            <div className="px-3 py-3">
              <p className="text-[9px] uppercase tracking-widest text-white/25 mb-2 font-mono">Plan Summaries</p>
              <div className="space-y-2">
                {summaries.map((e, i) => {
                  const text = (e.summary as string) || (e.payload?.summary as string) || e.event_type
                  return (
                    <div key={i} className="text-[11px] text-white/55 leading-relaxed bg-black/40 p-2 rounded border border-white/[0.05]">
                      {text}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Pending approval */}
          {pendingApprovals.length > 0 && (
            <div className="px-3 py-3">
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/8 px-3 py-2.5">
                <p className="text-[10px] font-semibold text-amber-400 mb-1 font-mono uppercase">Gate Blocked</p>
                {pendingApprovals.map((a) => (
                  <p key={a.approval_id} className="text-[11px] text-amber-300/80 leading-tight">{a.action}</p>
                ))}
              </div>
            </div>
          )}

          {activeAgents.length === 0 && summaries.length === 0 && pendingApprovals.length === 0 && (
            <div className="px-3 py-8 text-center">
              <Bot size={18} className="mx-auto mb-2 text-white/15" />
              <p className="text-[11px] text-white/30">
                {run?.status === 'running' ? 'Agents orchestrating…' : 'No agents active'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Chat tab ── */}
      {tab === 'chat' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Run context strip */}
          {run && (
            <div className="px-3 py-2 border-b border-white/[0.04] flex-shrink-0">
              <div className="flex items-center gap-1.5">
                <StatusDot status={run.status} />
                <span className="text-[10px] text-white/35 truncate font-mono">{run.goal.slice(0, 45)}…</span>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {chatMessages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <MessageSquare size={20} className="text-white/12 mb-3" />
                <p className="text-[11px] text-white/28 leading-relaxed">
                  Chat with Gemma while the run executes.
                </p>
                <p className="text-[10px] text-white/18 mt-1">
                  Ask what it's doing, give context, or trigger actions.
                </p>
              </div>
            )}
            {chatMessages.map((msg) => (
              <InlineChatMessage key={msg.id} msg={msg} />
            ))}
            <div ref={chatBottomRef} />
          </div>

          {/* Input */}
          <div className="p-2.5 border-t border-white/[0.05] flex-shrink-0">
            <div className="flex items-end gap-2 rounded-xl border border-white/[0.07] bg-white/[0.03] px-3 py-2 focus-within:border-white/[0.11] transition-colors">
              <textarea
                ref={inputRef}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Gemma anything…"
                rows={1}
                disabled={chatSending}
                className="flex-1 bg-transparent text-[12px] text-white/75 placeholder:text-white/20 outline-none resize-none leading-relaxed max-h-28 overflow-y-auto disabled:opacity-50"
                style={{ scrollbarWidth: 'none' }}
                onInput={(e) => {
                  const el = e.currentTarget
                  el.style.height = 'auto'
                  el.style.height = Math.min(el.scrollHeight, 112) + 'px'
                }}
              />
              <button
                onClick={sendChat}
                disabled={!chatInput.trim() || chatSending}
                className={cn(
                  'flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-all',
                  chatInput.trim() && !chatSending
                    ? 'bg-white/14 text-white/70 hover:bg-white/20'
                    : 'bg-white/4 text-white/18 cursor-not-allowed'
                )}
              >
                {chatSending
                  ? <Loader2 size={12} className="animate-spin" />
                  : <Send size={12} />
                }
              </button>
            </div>
            <p className="text-[9px] text-white/15 mt-1 px-0.5">Enter to send · Shift+Enter newline</p>
          </div>
        </div>
      )}
    </div>
  )
}
