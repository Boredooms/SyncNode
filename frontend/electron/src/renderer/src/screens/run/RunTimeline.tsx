import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import {
  Clock, Check, AlertTriangle, Wrench, FileText, Shield, Copy, CheckCheck, Code
} from 'lucide-react'
import { cn, formatTimestamp, formatDuration, formatFileSize, getEventLabel } from '../../lib/utils'
import { EmptyState, StatusBadge } from '../../components/ui/primitives'
import type { RunState } from '../../stores/runStore'
import { RawDataDrawer } from '../../components/run/RawDataDrawer'

interface RunTabContext {
  runId: string
  runState: RunState
}

function eventIcon(type: string): string {
  if (type.includes('verification.passed')) return '✓'
  if (type.includes('verification.failed')) return '✗'
  if (type.includes('approval')) return '!'
  if (type.includes('recovery')) return '↻'
  if (type.includes('agent.completed')) return '●'
  if (type.includes('run.completed')) return '✓'
  if (type.includes('run.failed')) return '✗'
  return '·'
}

function eventColor(type: string): string {
  if (type.includes('verification.passed') || type.includes('completed')) return 'text-emerald-400'
  if (type.includes('failed') || type.includes('error')) return 'text-red-400'
  if (type.includes('approval') || type.includes('waiting')) return 'text-amber-400'
  if (type.includes('recovery')) return 'text-purple-400'
  return 'text-white/40'
}

export function RunTimeline() {
  const { runState } = useOutletContext<RunTabContext>()
  const { sseEvents = [] } = runState
  const [inspectEvent, setInspectEvent] = useState<any>(null)

  if (sseEvents.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <EmptyState
          icon={<Clock size={22} />}
          title="No timeline events"
          description="Live and replayed events will stream here."
        />
      </div>
    )
  }

  return (
    <div className="overflow-y-auto p-4 max-w-5xl mx-auto">
      <div className="rounded-xl border border-white/[0.06] bg-[#0d0d0d] overflow-hidden divide-y divide-white/5">
        {sseEvents.map((event, i) => {
          const eventType = String(event.event_type ?? event.type ?? 'event')
          const agent = (event.agent as string) ?? (event.agent_id as string) ?? 'system'
          return (
            <div
              key={`${eventType}-${event.ts}-${i}`}
              onClick={() => setInspectEvent(event)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-white/3 transition-colors cursor-pointer select-none"
            >
              <span className="text-[10px] text-white/25 font-mono w-16 flex-shrink-0">
                {formatTimestamp(event.ts)}
              </span>
              <span className={cn('text-[11px] text-white/45 truncate font-mono w-24 flex-shrink-0', eventColor(eventType))}>
                {agent}
              </span>
              <div className="flex-1 flex items-center gap-2 min-w-0">
                <span className={cn('text-[11px] font-mono', eventColor(eventType))}>
                  {eventIcon(eventType)}
                </span>
                <span className="text-[11px] text-white/70 font-mono truncate">{getEventLabel(eventType)}</span>
                {event.step_key && (
                  <span className="text-[10px] text-white/25 font-mono truncate">
                    ({event.step_key as string})
                  </span>
                )}
              </div>
              <Code size={11} className="text-white/20 hover:text-white/60 flex-shrink-0" />
            </div>
          )
        })}
      </div>

      {inspectEvent && (
        <RawDataDrawer
          title={`Event: ${inspectEvent.event_type || inspectEvent.type}`}
          data={inspectEvent}
          isOpen={true}
          onClose={() => setInspectEvent(null)}
        />
      )}
    </div>
  )
}

export function RunTools() {
  const { runState } = useOutletContext<RunTabContext>()
  const { tools = [] } = runState
  const [inspectTool, setInspectTool] = useState<any>(null)

  if (tools.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <EmptyState icon={<Wrench size={22} />} title="No tool calls recorded" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-3 max-w-5xl mx-auto">
      {tools.map((tool, idx) => (
        <div
          key={tool.tool_call_id || idx}
          className="px-4 py-3 rounded-xl border border-white/[0.06] bg-[#0e0e0e] hover:border-white/[0.09] transition-colors"
        >
          <div className="flex items-center gap-3 mb-1.5">
            <span className="text-[12px] text-white/85 font-mono font-medium">{tool.tool_key}</span>
            {tool.step_key && (
              <>
                <span className="text-white/20">·</span>
                <span className="text-[11px] text-white/40 font-mono">{tool.step_key}</span>
              </>
            )}
            <StatusBadge status={tool.status} className="ml-auto" />
            <button
              onClick={() => setInspectTool(tool)}
              className="p-1 rounded text-white/30 hover:text-white/70 hover:bg-white/5"
            >
              <Code size={12} />
            </button>
          </div>

          <div className="flex items-center gap-4 text-[10px] text-white/40 font-mono mt-2">
            {tool.agent && <span>Agent: {tool.agent}</span>}
            {tool.duration_ms && <span>Duration: {formatDuration(tool.duration_ms)}</span>}
            {tool.risk && <span className="text-amber-400/80">Risk: {tool.risk}</span>}
            {tool.side_effect_type && <span>Side Effect: {tool.side_effect_type}</span>}
          </div>

          {tool.error_message && (
            <div className="mt-2 p-2 rounded bg-red-950/20 border border-red-500/20 text-[10px] font-mono text-red-300">
              {tool.error_message}
            </div>
          )}
        </div>
      ))}

      {inspectTool && (
        <RawDataDrawer
          title={`Tool Call: ${inspectTool.tool_key}`}
          data={inspectTool}
          isOpen={true}
          onClose={() => setInspectTool(null)}
        />
      )}
    </div>
  )
}

export function RunArtifacts() {
  const { runState } = useOutletContext<RunTabContext>()
  const { artifacts = [] } = runState
  const [copiedPath, setCopiedPath] = useState<string | null>(null)
  const [inspectArt, setInspectArt] = useState<any>(null)

  const copyPath = (path: string) => {
    navigator.clipboard.writeText(path)
    setCopiedPath(path)
    setTimeout(() => setCopiedPath(null), 1500)
  }

  if (artifacts.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <EmptyState
          icon={<FileText size={22} />}
          title="No artifacts yet"
          description="Generated files and output documents will appear here once produced."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-3 max-w-5xl mx-auto">
      {artifacts.map((artifact, idx) => (
        <div
          key={artifact.artifact_id || idx}
          className="p-4 rounded-xl border border-white/[0.06] bg-[#0e0e0e] hover:border-white/[0.09] transition-colors"
        >
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-[10px] font-mono text-blue-400 flex-shrink-0">
              {(artifact.type || artifact.kind || 'DOC').toUpperCase().slice(0, 4)}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-[13px] text-white/90 font-medium truncate select-text">{artifact.name}</p>
                {artifact.verified && (
                  <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20 flex-shrink-0">
                    <Check size={10} /> verified
                  </span>
                )}
              </div>

              {artifact.path && (
                <div className="flex items-center gap-2 mt-1.5">
                  <p className="text-[10px] text-white/40 font-mono truncate select-text bg-black/40 px-2 py-1 rounded border border-white/5 flex-1">
                    {artifact.path}
                  </p>
                  <button
                    onClick={() => copyPath(artifact.path!)}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono bg-white/5 hover:bg-white/10 text-white/60 transition-colors flex-shrink-0"
                    title="Copy full path"
                  >
                    {copiedPath === artifact.path ? (
                      <>
                        <CheckCheck size={11} className="text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy size={11} />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              <div className="flex items-center gap-4 mt-2 text-[10px] text-white/30 font-mono">
                {artifact.size_bytes && <span>Size: {formatFileSize(artifact.size_bytes)}</span>}
                {artifact.sha256 && <span>SHA256: {artifact.sha256.slice(0, 16)}…</span>}
                {artifact.step_key && <span>Step: {artifact.step_key}</span>}
              </div>
            </div>

            <button
              onClick={() => setInspectArt(artifact)}
              className="p-1 rounded text-white/30 hover:text-white/70 hover:bg-white/5"
            >
              <Code size={12} />
            </button>
          </div>
        </div>
      ))}

      {inspectArt && (
        <RawDataDrawer
          title={`Artifact: ${inspectArt.name}`}
          data={inspectArt}
          isOpen={true}
          onClose={() => setInspectArt(null)}
        />
      )}
    </div>
  )
}

export function RunEvidence() {
  const { runState } = useOutletContext<RunTabContext>()
  const { verifications = [], observations = [] } = runState
  const [inspectItem, setInspectItem] = useState<{ title: string; data: any } | null>(null)

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Verifications Section */}
      <div>
        <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono mb-3">
          Postcondition Verifications ({verifications.length})
        </p>

        {verifications.length === 0 ? (
          <p className="text-[12px] text-white/30 px-1 italic">No verifications recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {verifications.map((v, idx) => {
              const isPassed = v.result === 'PASS' || v.status === 'passed'
              const resultText = v.result ?? (isPassed ? 'PASS' : 'FAIL')

              return (
                <div
                  key={v.verification_id || idx}
                  className={cn(
                    'px-4 py-3 rounded-xl border',
                    isPassed
                      ? 'border-emerald-500/20 bg-emerald-500/5'
                      : 'border-red-500/20 bg-red-500/5'
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {isPassed ? (
                      <Check size={13} className="text-emerald-400" />
                    ) : (
                      <AlertTriangle size={13} className="text-red-400" />
                    )}
                    <span className="text-[12px] text-white/80 font-mono font-medium">
                      {v.step_key || 'Step verification'}
                    </span>
                    <span
                      className={cn(
                        'ml-auto text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded',
                        isPassed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                      )}
                    >
                      {resultText}
                    </span>
                    <button
                      onClick={() => setInspectItem({ title: `Verification: ${v.step_key}`, data: v })}
                      className="p-1 rounded text-white/30 hover:text-white/70"
                    >
                      <Code size={11} />
                    </button>
                  </div>

                  {v.failure_reason && (
                    <p className="text-[11px] text-red-300/80 font-mono mt-1">{v.failure_reason}</p>
                  )}

                  {v.assertions && (
                    <div className="mt-2 p-2 rounded bg-black/40 border border-white/5 font-mono text-[10px] text-white/60 overflow-x-auto max-h-36">
                      <pre className="whitespace-pre-wrap leading-tight">
                        {JSON.stringify(v.assertions, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Observations Section */}
      {observations.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono mb-3">
            Captured Observations ({observations.length})
          </p>
          <div className="space-y-2">
            {observations.map((o, idx) => (
              <div
                key={o.observation_id || idx}
                className="px-4 py-3 rounded-xl border border-white/[0.05] bg-white/2 space-y-1"
              >
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <span className="text-white/40 uppercase">{o.observation_type || o.kind || 'observation'}</span>
                  {o.step_key && <span className="text-white/25">({o.step_key})</span>}
                  <span className="text-white/25 ml-auto">{formatTimestamp(o.captured_at || o.ts)}</span>
                </div>
                {o.content && (
                  <p className="text-[11px] text-white/65 select-text font-mono mt-1">{o.content}</p>
                )}
                {o.screenshot_path && (
                  <p className="text-[10px] text-blue-400 font-mono mt-1 truncate">
                    Screenshot: {o.screenshot_path}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {inspectItem && (
        <RawDataDrawer
          title={inspectItem.title}
          data={inspectItem.data}
          isOpen={true}
          onClose={() => setInspectItem(null)}
        />
      )}
    </div>
  )
}
