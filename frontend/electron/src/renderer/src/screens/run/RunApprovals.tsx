import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Vote, Check, X, AlertTriangle, BookOpen, Monitor, Code, CheckCircle2, Sparkles } from 'lucide-react'
import { cn, formatTimestamp } from '../../lib/utils'
import { decideApproval } from '../../lib/api/client'
import { useRunStore } from '../../stores/runStore'
import { EmptyState } from '../../components/ui/primitives'
import type { RunState } from '../../stores/runStore'
import { RawDataDrawer } from '../../components/run/RawDataDrawer'

interface RunTabContext {
  runId: string
  runState: RunState
}

export function RunApprovals() {
  const { runId, runState } = useOutletContext<RunTabContext>()
  const { approvals = [] } = runState
  const { hydrateRunState } = useRunStore()
  const [deciding, setDeciding] = useState<string | null>(null)
  // Per-approval reason map so typing a note on one card doesn't affect others.
  const [reasons, setReasons] = useState<Record<string, string>>({})
  const [inspectApproval, setInspectApproval] = useState<any>(null)

  const pending = approvals.filter((a) => a.status === 'pending')
  const decided = approvals.filter((a) => a.status !== 'pending')

  const handleDecide = async (approvalId: string, decision: 'approved' | 'rejected') => {
    setDeciding(approvalId)
    const reason = reasons[approvalId] || ''
    try {
      await decideApproval(runId, approvalId, { decision, reason: reason || undefined })
      hydrateRunState(runId, {
        approvals: approvals.map((a) =>
          a.approval_id === approvalId
            ? { ...a, status: decision, decision, reason, decided_at: Date.now() / 1000 }
            : a
        ),
      })
      // Clear the reason for this approval after decision.
      setReasons((prev) => { const next = { ...prev }; delete next[approvalId]; return next })
    } catch (e: any) {
      console.error('Failed to decide approval:', e)
    } finally {
      setDeciding(null)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">

      {/* ── Workflow completed success banner (shown after approval leads to completion) ── */}
      <AnimatePresence>
        {runState?.run?.status === 'completed' && decided.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-emerald-500/30 bg-emerald-950/15 p-5 flex items-start gap-4"
          >
            <Sparkles size={20} className="text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-[14px] font-semibold text-emerald-300 mb-1">Workflow Complete</p>
              <p className="text-[12px] text-white/60 leading-relaxed">
                All steps verified and the approval gate was authorized. The workflow finished successfully.
              </p>
            </div>
            <CheckCircle2 size={22} className="text-emerald-400 flex-shrink-0" />
          </motion.div>
        )}
        {runState?.run?.status === 'failed' && decided.some(a => a.status === 'rejected') && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-red-500/30 bg-red-950/10 p-5 flex items-start gap-4"
          >
            <X size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-[14px] font-semibold text-red-300 mb-1">Workflow Rejected</p>
              <p className="text-[12px] text-white/50">The action was rejected. No external communication was sent.</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state — no approvals at all */}
      {pending.length === 0 && decided.length === 0 && (
        <EmptyState
          icon={<Vote size={22} />}
          title="No approval boundaries triggered"
          description="Actions involving external tools, email dispatch, or file deletion will pause here for human authorization."
        />
      )}

      {pending.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-amber-400 font-semibold font-mono mb-3">
            Pending Authorization Required ({pending.length})
          </p>
          <div className="space-y-3">
            {pending.map((approval) => (
              <motion.div
                key={approval.approval_id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-amber-500/30 bg-amber-950/10 overflow-hidden shadow-lg"
              >
                <div className="px-5 py-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={14} className="text-amber-400" />
                      <span className="text-[12px] font-semibold text-amber-300 font-mono">
                        SOVEREIGN GATE // HUMAN APPROVAL REQUIRED
                      </span>
                    </div>
                    <button
                      onClick={() => setInspectApproval(approval)}
                      className="text-white/30 hover:text-white/70"
                    >
                      <Code size={12} />
                    </button>
                  </div>

                  <p className="text-[14px] text-white/90 font-medium mb-3 select-text">
                    {approval.action || approval.action_summary}
                  </p>

                  <div className="flex items-center gap-4 text-[11px] font-mono mb-3">
                    <span className="text-white/40">Risk Class:</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold uppercase text-[10px]">
                      {approval.risk || approval.risk_class || 'high'}
                    </span>
                    {approval.step_key && (
                      <span className="text-white/30">Step: {approval.step_key}</span>
                    )}
                  </div>

                  {approval.context && Object.keys(approval.context).length > 0 && (
                    <div className="rounded-lg bg-black/50 border border-white/[0.05] p-3 mb-3 space-y-1 text-[11px]">
                      {Object.entries(approval.context).map(([k, v]) => (
                        <div key={k} className="flex gap-2">
                          <span className="text-white/35 w-24 flex-shrink-0 font-mono">{k}:</span>
                          <span className="text-white/70 select-text font-mono truncate">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <textarea
                    placeholder="Optional rationale or justification notes…"
                    value={reasons[approval.approval_id] || ''}
                    onChange={(e) => setReasons((prev) => ({ ...prev, [approval.approval_id]: e.target.value }))}
                    rows={2}
                    className="w-full bg-black/40 border border-white/[0.07] rounded-lg px-3 py-2 mb-3 text-[11px] text-white/80 placeholder:text-white/25 outline-none resize-none select-text focus:border-amber-500/40"
                  />

                  <div className="flex gap-2.5">
                    <button
                      onClick={() => handleDecide(approval.approval_id, 'rejected')}
                      disabled={deciding === approval.approval_id}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[12px] border border-white/[0.08] text-white/60 hover:text-white/90 hover:bg-white/5 transition-all font-medium disabled:opacity-40"
                    >
                      <X size={13} />
                      Reject Action
                    </button>
                    <button
                      onClick={() => handleDecide(approval.approval_id, 'approved')}
                      disabled={deciding === approval.approval_id}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[12px] bg-white text-black font-semibold hover:bg-white/90 transition-all disabled:opacity-40"
                    >
                      <Check size={13} />
                      Authorize Action
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {decided.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono mb-2.5">
            Decided Boundary Records
          </p>
          <div className="space-y-2">
            {decided.map((approval) => (
              <div
                key={approval.approval_id}
                className={cn(
                  'px-4 py-3 rounded-xl border text-[11px] flex items-center justify-between',
                  approval.status === 'approved'
                    ? 'border-emerald-500/20 bg-emerald-500/5'
                    : 'border-red-500/20 bg-red-500/5'
                )}
              >
                <div className="flex items-center gap-2.5">
                  {approval.status === 'approved' ? (
                    <Check size={12} className="text-emerald-400" />
                  ) : (
                    <X size={12} className="text-red-400" />
                  )}
                  <span className="text-white/80 font-medium">{approval.action || approval.action_summary}</span>
                </div>

                <div className="flex items-center gap-3 font-mono text-[10px]">
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded font-semibold uppercase',
                      approval.status === 'approved' ? 'text-emerald-400 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'
                    )}
                  >
                    {approval.status}
                  </span>
                  {approval.decided_at && (
                    <span className="text-white/30">{formatTimestamp(approval.decided_at)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {inspectApproval && (
        <RawDataDrawer
          title={`Approval: ${inspectApproval.approval_id}`}
          data={inspectApproval}
          isOpen={true}
          onClose={() => setInspectApproval(null)}
        />
      )}
    </div>
  )
}

export function RunAudit() {
  const { runState } = useOutletContext<RunTabContext>()
  const { auditEvents = [], sseEvents = [] } = runState
  const [inspectAudit, setInspectAudit] = useState<any>(null)

  // Use auditEvents from REST if populated, otherwise fallback to sseEvents
  const events = auditEvents.length > 0 ? auditEvents : sseEvents

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
          Cryptographic Audit Trail ({events.length} records)
        </p>
      </div>

      {events.length === 0 ? (
        <div className="flex items-center justify-center p-8">
          <EmptyState icon={<BookOpen size={22} />} title="No audit records yet" />
        </div>
      ) : (
        <div className="rounded-xl border border-white/[0.06] bg-[#0d0d0d] overflow-hidden divide-y divide-white/5 font-mono text-[11px]">
          {events.map((event: any, i) => {
            const eventType = String(event.event_type ?? event.type ?? 'audit.event')
            const agent = (event.agent as string) ?? (eventType.includes('.') ? eventType.split('.')[0] : 'system')
            const seq = event.seq ?? i + 1
            const hash = event.hash

            return (
              <div
                key={`audit-${i}`}
                onClick={() => setInspectAudit(event)}
                className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/3 transition-colors cursor-pointer select-none"
              >
                <span className="text-white/20 w-8 flex-shrink-0 text-[10px]">#{seq}</span>
                <span className="text-white/25 w-16 flex-shrink-0 text-[10px]">{formatTimestamp(event.ts)}</span>
                <span className="text-white/40 w-24 flex-shrink-0 truncate text-[10px]">{agent}</span>
                <span className="text-white/80 flex-1 truncate">{eventType}</span>
                {hash && (
                  <span className="text-white/20 text-[10px] hidden sm:inline">{hash}</span>
                )}
                {event.step_key && (
                  <span className="text-white/30 text-[10px] truncate max-w-[120px]">
                    {event.step_key as string}
                  </span>
                )}
                <Code size={11} className="text-white/20 hover:text-white/60 flex-shrink-0 ml-1" />
              </div>
            )
          })}
        </div>
      )}

      {inspectAudit && (
        <RawDataDrawer
          title={`Audit Record: ${inspectAudit.event_type || inspectAudit.type}`}
          data={inspectAudit}
          isOpen={true}
          onClose={() => setInspectAudit(null)}
        />
      )}
    </div>
  )
}

export function RunDesktop() {
  const { runState } = useOutletContext<RunTabContext>()
  const { observations = [] } = runState

  const screenshots = observations.filter(
    (o) => o.observation_type === 'screenshot' || o.kind === 'screenshot' || o.screenshot_path
  )

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
        Desktop Mirror & Visual Observations ({screenshots.length})
      </p>

      {screenshots.length === 0 ? (
        <div className="flex items-center justify-center rounded-xl border border-white/[0.06] bg-white/2 p-12 min-h-[360px]">
          <EmptyState
            icon={<Monitor size={24} />}
            title="No visual desktop observations"
            description="Live desktop captures and screen state will be mirrored here during computer control workflows."
          />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Show all screenshots, most-recent first */}
          {[...screenshots].reverse().map((obs, i) => (
            <div
              key={obs.observation_id ?? i}
              className="rounded-xl border border-white/[0.07] bg-[#0e0e0e] overflow-hidden"
            >
              {/* Caption bar */}
              <div className="px-4 py-2.5 bg-white/4 border-b border-white/[0.05] flex items-center gap-2 font-mono text-[11px]">
                <span className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0" />
                <span className="text-white/70 font-medium">
                  {i === 0 ? 'Latest Capture' : 'Capture'}
                </span>
                {obs.application && (
                  <span className="text-white/40">[{obs.application}]</span>
                )}
                {obs.window_title && (
                  <span className="text-white/30 truncate max-w-[220px]">
                    - {obs.window_title}
                  </span>
                )}
                {obs.step_key && (
                  <span className="text-white/25 font-mono text-[10px] ml-1">
                    ({obs.step_key})
                  </span>
                )}
                <span className="text-white/20 ml-auto text-[10px]">
                  {formatTimestamp(obs.captured_at || obs.ts)}
                </span>
              </div>

              {/* Screenshot image — served via the backend screenshots endpoint */}
              {obs.observation_id ? (
                <div className="bg-black/80 p-2 flex items-center justify-center min-h-[120px]">
                  <img
                    src={`http://127.0.0.1:8000/api/v1/screenshots/${obs.observation_id}`}
                    alt={`Desktop capture — ${obs.window_title ?? obs.step_key ?? 'observation'}`}
                    className="max-h-[500px] w-auto max-w-full object-contain rounded border border-white/[0.07]"
                    onError={(e) => {
                      // Hide broken image; show fallback text
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      const parent = target.parentElement
                      if (parent && !parent.querySelector('.img-fallback')) {
                        const fb = document.createElement('p')
                        fb.className = 'img-fallback text-[11px] text-white/30 font-mono py-4'
                        fb.textContent = `Screenshot: ${obs.screenshot_hash?.slice(0, 16) ?? 'captured'}`
                        parent.appendChild(fb)
                      }
                    }}
                  />
                </div>
              ) : (
                <div className="p-4 text-[11px] text-white/30 font-mono">
                  Screenshot captured — path: {obs.screenshot_path ?? '(no path)'}
                </div>
              )}

              {/* Window title fallback when no image */}
              {obs.content && (
                <div className="p-3 text-[11px] font-mono text-white/55 bg-black/40 border-t border-white/5 select-text">
                  {obs.content}
                </div>
              )}
              {!obs.observation_id && obs.window_title && (
                <div className="p-3 text-[11px] font-mono text-white/45 bg-black/40 border-t border-white/5">
                  Window: {obs.window_title}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
