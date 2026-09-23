import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  FileText,
  ShieldCheck,
  Eye,
  Wrench,
  Bot,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import type { RunState } from '../../stores/runStore'
import { formatTimestamp, formatDuration } from '../../lib/utils'
import { RawDataDrawer } from '../../components/run/RawDataDrawer'

interface RunTabContext {
  runId: string
  runState: RunState
}

export function RunAutomation() {
  const { runId, runState } = useOutletContext<RunTabContext>()
  const { run, steps, tools, verifications, observations, artifacts, auditEvents, workflowMemory } = runState
  const [inspectData, setInspectData] = useState<{ title: string; data: any } | null>(null)

  const isCompleted = run?.status === 'completed'
  const isFailed = run?.status === 'failed'
  const isWaitingApproval = run?.status === 'waiting_approval'

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Execution Pipeline Header */}
      <div className="flex items-center justify-between pb-4 border-b border-white/[0.05]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity size={14} className="text-emerald-400" />
            <h3 className="text-[13px] font-semibold text-white/90">Automation & Execution Engine</h3>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-white/5 text-white/50 uppercase">
              {run?.status ?? 'queued'}
            </span>
          </div>
          <p className="text-[11px] text-white/40">
            Real-time multi-agent automation chain: Action → Tool → Observation → Verification → Artifact.
          </p>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono">
          <span className="px-2 py-1 rounded bg-white/4 border border-white/[0.06] text-white/60">
            {steps.length} Steps
          </span>
          <span className="px-2 py-1 rounded bg-white/4 border border-white/[0.06] text-white/60">
            {tools.length} Tools
          </span>
          <span className="px-2 py-1 rounded bg-white/4 border border-white/[0.06] text-white/60">
            {verifications.filter((v) => v.result === 'PASS' || v.status === 'passed').length} Verified
          </span>
        </div>
      </div>

      {/* Execution State Pipeline */}
      <div className="grid grid-cols-5 gap-2 text-center">
        {[
          { label: 'PLAN', status: steps.length > 0 ? 'completed' : 'waiting', icon: Clock },
          { label: 'DISPATCH', status: tools.length > 0 ? 'completed' : 'waiting', icon: Bot },
          { label: 'EXECUTE', status: tools.some((t) => t.status === 'completed') ? 'completed' : 'waiting', icon: Wrench },
          { label: 'OBSERVE', status: observations.length > 0 ? 'completed' : 'waiting', icon: Eye },
          {
            label: 'VERIFY',
            status: verifications.some((v) => v.result === 'PASS' || v.status === 'passed')
              ? 'completed'
              : verifications.some((v) => v.result === 'FAIL' || v.status === 'failed')
              ? 'failed'
              : 'waiting',
            icon: ShieldCheck,
          },
        ].map(({ label, status, icon: Icon }) => (
          <div
            key={label}
            className={`p-3 rounded-lg border transition-all ${
              status === 'completed'
                ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400'
                : status === 'failed'
                ? 'border-red-500/30 bg-red-500/5 text-red-400'
                : 'border-white/8 bg-white/2 text-white/30'
            }`}
          >
            <Icon size={14} className="mx-auto mb-1.5 opacity-80" />
            <p className="text-[10px] font-mono font-semibold tracking-wider">{label}</p>
            <p className="text-[9px] uppercase mt-0.5 opacity-60 font-mono">{status}</p>
          </div>
        ))}
      </div>

      {/* Steps Execution Chain */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-[11px] uppercase tracking-widest text-white/30 font-semibold font-mono">
            Execution Steps & Verified Proof
          </h4>
          <span className="text-[10px] text-white/30 font-mono">Run ID: {runId}</span>
        </div>

        {steps.length === 0 ? (
          <div className="p-8 text-center rounded-lg border border-white/[0.06] bg-white/2">
            <Clock size={20} className="mx-auto mb-2 text-white/20 animate-spin" />
            <p className="text-[12px] text-white/40">Waiting for planner to dispatch automation steps…</p>
          </div>
        ) : (
          <div className="space-y-3">
            {steps.map((step, idx) => {
              const matchedTool = tools.find((t) => t.step_key === step.step_key)
              const matchedVerif = verifications.find((v) => v.step_key === step.step_key)
              const matchedObs = observations.filter((o) => o.step_key === step.step_key)

              const isStepPassed =
                step.verification === 'PASS' ||
                matchedVerif?.result === 'PASS' ||
                matchedVerif?.status === 'passed'

              return (
                <div
                  key={step.step_key || idx}
                  className="rounded-lg border border-white/[0.06] bg-[#0e0e0e] p-4 space-y-3 transition-colors hover:border-white/[0.09]"
                >
                  {/* Step header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full flex items-center justify-center bg-white/8 text-[11px] font-mono text-white/70">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="text-[13px] text-white/90 font-medium">
                          {step.action ?? step.step_key}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          {step.agent && (
                            <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-1.5 py-0.2 rounded border border-blue-500/20">
                              agent: {step.agent}
                            </span>
                          )}
                          <span className="text-[10px] text-white/30 font-mono">
                            step_key: {step.step_key}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {isStepPassed ? (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 size={11} /> VERIFIED PASS
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 text-white/40 border border-white/[0.07]">
                          {step.status}
                        </span>
                      )}

                      <button
                        onClick={() =>
                          setInspectData({
                            title: `Step: ${step.step_key}`,
                            data: { step, tool: matchedTool, verification: matchedVerif, observations: matchedObs },
                          })
                        }
                        className="px-2 py-1 rounded text-[10px] text-white/40 hover:text-white/80 hover:bg-white/5 font-mono"
                      >
                        inspect
                      </button>
                    </div>
                  </div>

                  {/* Tool execution row */}
                  {matchedTool && (
                    <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-2">
                        <Wrench size={12} className="text-amber-400/70" />
                        <span className="font-mono text-white/70">{matchedTool.tool_key}</span>
                        {matchedTool.duration_ms && (
                          <span className="text-white/30 text-[10px]">
                            ({formatDuration(matchedTool.duration_ms)})
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] uppercase font-mono text-white/40">
                        status: {matchedTool.status}
                      </span>
                    </div>
                  )}

                  {/* Verification evidence */}
                  {matchedVerif && (
                    <div className="p-3 rounded bg-emerald-950/10 border border-emerald-500/20 space-y-1.5">
                      <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-medium">
                        <ShieldCheck size={13} />
                        <span>Verification Assertions Passed</span>
                      </div>
                      {matchedVerif.assertions && (
                        <div className="text-[10px] font-mono text-white/60 bg-black/40 p-2 rounded border border-white/5 overflow-x-auto max-h-32">
                          <pre className="whitespace-pre-wrap leading-tight">
                            {JSON.stringify(matchedVerif.assertions, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Generated Artifacts Section */}
      <div className="space-y-3 pt-2">
        <h4 className="text-[11px] uppercase tracking-widest text-white/30 font-semibold font-mono">
          Artifacts Produced ({artifacts.length})
        </h4>

        {artifacts.length === 0 ? (
          <p className="text-[12px] text-white/30 italic">No artifacts registered yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {artifacts.map((art, i) => (
              <div
                key={art.artifact_id || i}
                className="p-4 rounded-lg border border-white/[0.07] bg-[#111] space-y-2"
              >
                <div className="flex items-center gap-2">
                  <FileText size={15} className="text-blue-400" />
                  <span className="text-[12px] font-medium text-white/90 truncate flex-1">
                    {art.name}
                  </span>
                  {art.verified && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      verified
                    </span>
                  )}
                </div>

                <p className="text-[10px] font-mono text-white/40 break-all">{art.path}</p>

                {art.sha256 && (
                  <p className="text-[9px] font-mono text-white/25 truncate">
                    SHA256: {art.sha256}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Workflow Memory Confirmation */}
      {workflowMemory && (
        <div className="p-4 rounded-lg border border-purple-500/20 bg-purple-950/10 flex items-center gap-3">
          <Sparkles size={16} className="text-purple-400 flex-shrink-0" />
          <div className="flex-1 text-[11px]">
            <p className="font-medium text-purple-300">Workflow Memory Recorded</p>
            <p className="text-white/40 mt-0.5">
              Trajectory and verified tool sequence stored in local learning memory for sovereign recall.
            </p>
          </div>
          <button
            onClick={() => setInspectData({ title: 'Workflow Memory', data: workflowMemory })}
            className="px-2.5 py-1 rounded text-[10px] font-mono bg-purple-500/15 text-purple-300 hover:bg-purple-500/25 transition-colors"
          >
            View Memory
          </button>
        </div>
      )}

      {/* Raw Data Inspection Modal */}
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
