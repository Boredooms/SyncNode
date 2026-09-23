import { useState } from 'react'
import { useOutletContext, useNavigate } from 'react-router-dom'
import { FileText, Shield, Users, Clock, Activity, Code, ChevronRight, CheckCircle2, Sparkles, XCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn, formatTimestamp } from '../../lib/utils'
import type { RunState } from '../../stores/runStore'
import { StatusDot, StatusBadge } from '../../components/ui/primitives'
import { RawDataDrawer } from '../../components/run/RawDataDrawer'

interface RunTabContext {
  runId: string
  runState: RunState
}

export function RunOverview() {
  const { runId, runState } = useOutletContext<RunTabContext>()
  const navigate = useNavigate()
  const [inspectData, setInspectData] = useState<{ title: string; data: any } | null>(null)

  const { run, steps = [], artifacts = [], verifications = [], approvals = [], sseEvents = [], activeAgents = {} } = runState

  if (!run) return null

  const passedVerifications = verifications.filter(
    (v) => v.result === 'PASS' || v.status === 'passed'
  ).length

  const stats = [
    { label: 'Steps', value: steps.length, icon: Activity, path: 'automation' },
    { label: 'Artifacts', value: artifacts.length, icon: FileText, path: 'artifacts' },
    { label: 'Verifications', value: passedVerifications, icon: Shield, path: 'evidence' },
    { label: 'Agents', value: Object.keys(activeAgents).length, icon: Users, path: 'agents' },
  ]

  const recentEvents = [...sseEvents].reverse().slice(0, 10)

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">

      {/* ── Terminal state banners ── */}
      <AnimatePresence>
        {run.status === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-emerald-500/30 bg-emerald-950/15 px-5 py-4 flex items-center gap-4"
          >
            <Sparkles size={18} className="text-emerald-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-[13px] font-semibold text-emerald-300">Workflow Completed Successfully</p>
              <p className="text-[11px] text-white/50 mt-0.5">
                All {steps.length} steps executed, {passedVerifications} verifications passed
                {artifacts.length > 0 ? `, ${artifacts.length} artifact${artifacts.length > 1 ? 's' : ''} produced.` : '.'}
              </p>
            </div>
            <CheckCircle2 size={20} className="text-emerald-400 flex-shrink-0" />
          </motion.div>
        )}
        {run.status === 'failed' && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-red-500/30 bg-red-950/10 px-5 py-4 flex items-center gap-4"
          >
            <XCircle size={18} className="text-red-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-[13px] font-semibold text-red-300">Workflow Failed</p>
              {run.error && <p className="text-[11px] text-red-400/70 font-mono mt-0.5">{run.error}</p>}
            </div>
          </motion.div>
        )}
        {run.status === 'waiting_approval' && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-amber-500/30 bg-amber-950/10 px-5 py-4 flex items-center gap-4"
          >
            <Shield size={18} className="text-amber-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-[13px] font-semibold text-amber-300">Waiting for Human Authorization</p>
              <p className="text-[11px] text-white/50 mt-0.5">
                All steps complete. Review the action in the Approvals tab before it proceeds.
              </p>
            </div>
            <button
              onClick={() => navigate(`/runs/${runId}/approvals`)}
              className="px-3 py-1.5 rounded-lg text-[11px] bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 font-medium transition-colors flex-shrink-0"
            >
              Review →
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Goal Banner */}
      <div className="p-5 rounded-xl border border-white/[0.07] bg-[#0e0e0e] shadow-sm flex items-start justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <p className="text-[10px] text-white/30 uppercase tracking-widest font-mono font-semibold">Goal</p>
          <p className="text-[14px] text-white/90 font-medium leading-relaxed select-text">{run.goal}</p>
          {run.model_id && (
            <p className="text-[10px] text-white/40 font-mono mt-1">Model: {run.model_id}</p>
          )}
        </div>

        <button
          onClick={() => setInspectData({ title: 'Run Raw Snapshot', data: runState })}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-mono text-white/50 hover:text-white/90 hover:bg-white/5 border border-white/[0.06] transition-colors flex-shrink-0"
          title="Inspect raw run JSON"
        >
          <Code size={12} />
          <span>Raw Data</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map(({ label, value, icon: Icon, path }) => (
          <button
            key={label}
            onClick={() => navigate(`/runs/${runId}/${path}`)}
            className="rounded-xl border border-white/[0.06] bg-white/2 hover:bg-white/4 hover:border-white/[0.09] p-4 text-left transition-all group"
          >
            <div className="flex items-center justify-between mb-2">
              <Icon size={16} className="text-white/30 group-hover:text-white/60 transition-colors" />
              <ChevronRight size={12} className="text-white/15 group-hover:text-white/40 transition-colors" />
            </div>
            <p className="text-[22px] font-light text-white/90 font-mono">{value}</p>
            <p className="text-[11px] text-white/40 mt-0.5">{label}</p>
          </button>
        ))}
      </div>

      {/* Verified Artifacts Preview */}
      {artifacts.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
              Output Artifacts
            </p>
            <button
              onClick={() => navigate(`/runs/${runId}/artifacts`)}
              className="text-[11px] text-white/40 hover:text-white/70 font-mono"
            >
              View all ({artifacts.length}) →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {artifacts.map((artifact, i) => (
              <div
                key={artifact.artifact_id || i}
                className="flex items-center gap-3 p-3 rounded-lg border border-white/[0.06] bg-white/2"
              >
                <FileText size={16} className="text-blue-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] text-white/80 font-medium truncate">{artifact.name}</p>
                  <p className="text-[10px] text-white/30 font-mono truncate">{artifact.path}</p>
                </div>
                {artifact.verified && (
                  <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex-shrink-0">
                    <CheckCircle2 size={10} /> verified
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Agents */}
      {Object.keys(activeAgents).length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono mb-2.5">
            Agents Involved
          </p>
          <div className="space-y-1.5">
            {Object.values(activeAgents).map((agent) => (
              <div
                key={agent.agent_id}
                className="flex items-center gap-3 py-2 px-3.5 rounded-lg bg-white/2 border border-white/[0.05]"
              >
                <StatusDot status={agent.status} />
                <span className="text-[12px] text-white/80 font-medium flex-1">{agent.agent_id}</span>
                {agent.action && (
                  <span className="text-[11px] text-white/40 truncate max-w-[200px]">{agent.action}</span>
                )}
                {agent.step_key && (
                  <span className="text-[10px] text-white/30 font-mono">{agent.step_key}</span>
                )}
                <StatusBadge status={agent.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity Feed */}
      {recentEvents.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
              Recent Events
            </p>
            <button
              onClick={() => navigate(`/runs/${runId}/timeline`)}
              className="text-[11px] text-white/40 hover:text-white/70 font-mono"
            >
              Full timeline ({sseEvents.length}) →
            </button>
          </div>

          <div className="rounded-xl border border-white/[0.06] bg-[#0d0d0d] overflow-hidden divide-y divide-white/5">
            {recentEvents.map((event, i) => {
              const eventType = event.event_type || event.type || 'event'
              const agent = (event.agent as string) || (event.agent_id as string)
              return (
                <div key={`${eventType}-${event.ts}-${i}`} className="flex items-center gap-3 px-4 py-2.5 text-[11px]">
                  <span className="text-white/25 font-mono w-16 flex-shrink-0 text-[10px]">
                    {formatTimestamp(event.ts)}
                  </span>
                  {agent && (
                    <span className="text-white/40 w-24 truncate flex-shrink-0 font-mono text-[10px]">
                      {agent}
                    </span>
                  )}
                  <span className="text-white/75 font-mono flex-1 truncate">{eventType}</span>
                  {event.step_key && (
                    <span className="text-white/25 font-mono text-[10px] truncate max-w-[140px]">
                      {event.step_key as string}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Inspect Raw Data Drawer */}
      {inspectData && (
        <RawDataDrawer
          title={inspectData.title}
          data={inspectData.data}
          isOpen={true}
          onClose={() => setInspectData(null)}
        />
      )}
    </div>
  )
}
