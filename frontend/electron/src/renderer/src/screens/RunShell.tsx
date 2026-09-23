import { useEffect, useState, useCallback } from 'react'
import { useParams, Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Brain, Map, Users, Clock, Monitor,
  Wrench, FileText, Shield, Vote, BookOpen, XCircle,
  ChevronLeft, Wifi, Loader2, Terminal, Activity, RefreshCw,
  PanelLeft,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { useRunStore } from '../stores/runStore'
import { useUIStore } from '../stores/uiStore'
import { openRunStream, closeRunStream } from '../lib/sse/stream'
import * as api from '../lib/api/client'
import { StatusDot, StatusBadge } from '../components/ui/primitives'
import { AgentPanel } from '../components/run/AgentPanel'
import { LiveEventInspector } from '../components/run/LiveEventInspector'
import {
  RunErrorBoundary,
  AgentPanelErrorBoundary,
} from '../components/ui/ErrorBoundary'
import { syncLogger } from '../lib/logger'

const RUN_TABS = [
  { label: 'Overview', path: 'overview', icon: LayoutDashboard },
  { label: 'Automation', path: 'automation', icon: Activity },
  { label: 'Intent', path: 'intent', icon: Brain },
  { label: 'Plan', path: 'plan', icon: Map },
  { label: 'Agents', path: 'agents', icon: Users },
  { label: 'Timeline', path: 'timeline', icon: Clock },
  { label: 'Desktop', path: 'desktop', icon: Monitor },
  { label: 'Tools', path: 'tools', icon: Wrench },
  { label: 'Artifacts', path: 'artifacts', icon: FileText },
  { label: 'Evidence', path: 'evidence', icon: Shield },
  { label: 'Approvals', path: 'approvals', icon: Vote },
  { label: 'Audit', path: 'audit', icon: BookOpen },
]

export function RunShell() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const { runs, initRun, hydrateRunState, appendEvent, setStreamState, setActiveRunId } = useRunStore()
  const { rightPanelCollapsed } = useUIStore()
  const [showEventInspector, setShowEventInspector] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const runState = runId ? runs[runId] : undefined
  const run = runState?.run

  const loadRun = useCallback(async (id: string) => {
    setIsRefreshing(true)
    syncLogger.debug('RUN', `Hydrating run data from REST for run=${id}`)
    try {
      const r = await api.getRun(id)
      if (!runs[id]) initRun(id, r)
      else hydrateRunState(id, { run: r })

      // Parallel hydration across all entity endpoints
      const [steps, artifacts, tools, observations, verifications, audit, context, approvals] = await Promise.allSettled([
        api.getRunSteps(id),
        api.getRunArtifacts(id),
        api.getRunTools(id),
        api.getRunObservations(id),
        api.getRunVerifications(id),
        api.getRunAudit(id),
        api.getRunContext(id),
        api.getRunApprovals(id),
      ])

      const partial: Parameters<typeof hydrateRunState>[1] = {}
      if (steps.status === 'fulfilled') partial.steps = steps.value
      if (artifacts.status === 'fulfilled') partial.artifacts = artifacts.value
      if (tools.status === 'fulfilled') partial.tools = tools.value
      if (observations.status === 'fulfilled') partial.observations = observations.value
      if (verifications.status === 'fulfilled') partial.verifications = verifications.value
      if (audit.status === 'fulfilled') partial.auditEvents = audit.value
      if (context.status === 'fulfilled') partial.context = context.value
      if (approvals.status === 'fulfilled') partial.approvals = approvals.value

      hydrateRunState(id, partial)
      syncLogger.info('RUN', `Run=${id} fully hydrated. Status=${r.status}, steps=${partial.steps?.length ?? 0}, artifacts=${partial.artifacts?.length ?? 0}`)
    } catch (err: any) {
      syncLogger.error('RUN', `Failed to load run=${id}: ${err?.message}`, err)
    } finally {
      setIsRefreshing(false)
    }
  }, [runId])

  useEffect(() => {
    if (!runId) return
    setActiveRunId(runId)

    loadRun(runId)

    // Open SSE stream for events replay or active updates.
    // When the stream goes terminal (run.completed/failed after approval),
    // do a REST refresh so the store has the final authoritative DB state.
    const stream = openRunStream(runId, {
      onEvent: (event) => {
        appendEvent(runId, event)
        // After approval leads to completion, immediately refresh from REST
        // so artifacts/verifications/approvals all reflect the final state.
        if (
          event.event_type === 'run.completed' ||
          event.event_type === 'approval.decided' ||
          event.event_type === 'run.failed'
        ) {
          setTimeout(() => loadRun(runId), 600)
        }
      },
      onStateChange: (state) => setStreamState(runId, state),
    })

    return () => {
      closeRunStream(runId)
      setActiveRunId(null)
    }
  }, [runId])

  if (!runId) return null

  if (!run) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[#0a0a0a] text-white">
        <div className="flex items-center gap-2 text-white/40 mb-3">
          <Loader2 size={16} className="animate-spin text-white/50" />
          <span className="text-[12px] font-mono">Connecting & hydrating run {runId.slice(0, 8)}…</span>
        </div>
        <button
          onClick={() => loadRun(runId)}
          className="px-3 py-1.5 rounded text-[11px] bg-white/5 hover:bg-white/10 text-white/60 border border-white/[0.07] transition-colors"
        >
          Retry connection
        </button>
      </div>
    )
  }

  const streamState = runState?.streamState
  const eventsCount = runState?.sseEvents.length ?? 0

  return (
    <RunErrorBoundary onRefresh={() => loadRun(runId)}>
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-[#0a0a0a]">
        {/* Run header */}
        <div className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.05] bg-[#0d0d0d] flex-shrink-0">
          <button
            onClick={() => navigate('/runs')}
            className="text-white/30 hover:text-white/70 transition-colors"
            title="Back to runs list"
          >
            <ChevronLeft size={15} />
          </button>
          <StatusDot status={run.status} />
          <div className="flex-1 min-w-0">
            <p className="text-[12px] text-white/85 truncate font-medium">{run.goal}</p>
            <p className="text-[10px] text-white/30 font-mono">{run.run_id}</p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <StatusBadge status={run.status} />

            {/* Refresh button */}
            <button
              onClick={() => loadRun(runId)}
              disabled={isRefreshing}
              className="p-1.5 rounded text-white/30 hover:text-white/70 hover:bg-white/5 transition-colors disabled:opacity-30"
              title="Refresh run snapshot"
            >
              <RefreshCw size={12} className={isRefreshing ? 'animate-spin' : ''} />
            </button>

            {/* Stream indicator */}
            {streamState === 'connected' && (
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20" title="Live stream connected">
                <Wifi size={10} className="text-emerald-400" />
                <span className="text-[9px] text-emerald-400 font-mono font-semibold">LIVE</span>
              </div>
            )}
            {streamState === 'reconnecting' && (
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20" title="Reconnecting">
                <Loader2 size={10} className="text-amber-400 animate-spin" />
                <span className="text-[9px] text-amber-400 font-mono">reconnecting</span>
              </div>
            )}

            {/* Live Events Diagnostic Button */}
            <button
              onClick={() => setShowEventInspector(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono bg-white/5 hover:bg-white/10 text-white/70 border border-white/[0.07] transition-colors"
              title="Open Live SSE Event Inspector"
            >
              <Terminal size={11} className="text-white/50" />
              <span>&lt;/&gt; Events</span>
              {eventsCount > 0 && (
                <span className="px-1 py-0.2 rounded bg-white/10 text-[9px] text-white/60">
                  {eventsCount}
                </span>
              )}
            </button>

            {(run.status === 'running' || run.status === 'waiting_approval') && (
              <button
                onClick={() => api.terminateRun(run.run_id)}
                className="flex items-center gap-1 px-2.5 py-1 rounded text-[11px] text-red-400/80 hover:text-red-400 hover:bg-red-500/10 border border-red-500/20 transition-all"
              >
                <XCircle size={11} />
                Terminate
              </button>
            )}
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-0.5 px-4 py-1.5 border-b border-white/[0.05] bg-[#0d0d0d] overflow-x-auto flex-shrink-0 scrollbar-none">
          {RUN_TABS.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={`/runs/${runId}/${path}`}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] whitespace-nowrap transition-colors font-medium',
                  isActive
                    ? 'bg-white/12 text-white/90 shadow-xs'
                    : 'text-white/35 hover:text-white/65 hover:bg-white/5'
                )
              }
            >
              <Icon size={11} />
              {label}
              {path === 'approvals' && runState?.approvals.some((a) => a.status === 'pending') && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 ml-0.5" />
              )}
            </NavLink>
          ))}
        </div>

        {/* Content area + right agent panel */}
        <div className="flex-1 flex min-h-0 overflow-hidden relative">
          {/* Main content */}
          <div className="flex-1 min-w-0 overflow-y-auto">
            <Outlet context={{ runId, runState }} />
          </div>

          {/* Re-open toggle — always visible on the right edge when panel is collapsed */}
          {rightPanelCollapsed && (
            <div className="absolute right-0 top-1/2 -translate-y-1/2 z-20">
              <button
                onClick={() => useUIStore.getState().setRightPanelCollapsed(false)}
                title="Open intelligence panel"
                className="flex flex-col items-center justify-center gap-1 w-5 h-14 rounded-l-lg bg-[#1a1a1a] border border-r-0 border-white/[0.08] text-white/25 hover:text-white/65 hover:bg-white/8 transition-all"
              >
                <PanelLeft size={11} />
              </button>
            </div>
          )}

          {/* Right agent panel */}
          <AnimatePresence>
            {!rightPanelCollapsed && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 310, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.18 }}
                className="border-l border-white/[0.05] overflow-hidden flex-shrink-0 bg-[#0c0c0c]"
              >
                <AgentPanelErrorBoundary>
                  <AgentPanel runId={runId} />
                </AgentPanelErrorBoundary>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Live SSE Event Inspector Modal */}
        <LiveEventInspector
          runId={runId}
          events={runState?.sseEvents ?? []}
          isOpen={showEventInspector}
          onClose={() => setShowEventInspector(false)}
        />
      </div>
    </RunErrorBoundary>
  )
}
