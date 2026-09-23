import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { EmptyState, StatusDot, StatusBadge } from '../../components/ui/primitives'
import { Brain, Map, Users, Code } from 'lucide-react'
import type { RunState } from '../../stores/runStore'
import { RawDataDrawer } from '../../components/run/RawDataDrawer'
import { cn } from '../../lib/utils'

interface RunTabContext {
  runId: string
  runState: RunState
}

export function RunIntent() {
  const { runState } = useOutletContext<RunTabContext>()
  const { intent } = runState
  const [inspectIntent, setInspectIntent] = useState<any>(null)

  if (!intent) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <EmptyState
          icon={<Brain size={22} />}
          title="Intent not yet extracted"
          description="The structured intent will appear here once the RAG and intent analysis phases complete."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
          Structured Intent & Constraints
        </p>
        <button
          onClick={() => setInspectIntent(intent)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono text-white/50 hover:text-white/80 hover:bg-white/5 border border-white/[0.06] transition-colors"
        >
          <Code size={11} />
          <span>Raw Intent</span>
        </button>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-[#0d0d0d] overflow-hidden divide-y divide-white/5">
        {Object.entries(intent).map(([key, val]) => (
          <div key={key} className="flex gap-4 px-4 py-3 text-[11px]">
            <span className="text-white/40 w-36 flex-shrink-0 font-mono font-medium">{key}</span>
            <span className="text-white/80 select-text font-mono flex-1 leading-relaxed">
              {typeof val === 'object' ? (
                <pre className="whitespace-pre-wrap text-[10px] text-white/60 bg-black/40 p-2 rounded border border-white/5">
                  {JSON.stringify(val, null, 2)}
                </pre>
              ) : (
                String(val)
              )}
            </span>
          </div>
        ))}
      </div>

      {inspectIntent && (
        <RawDataDrawer
          title="Structured Intent"
          data={inspectIntent}
          isOpen={true}
          onClose={() => setInspectIntent(null)}
        />
      )}
    </div>
  )
}

export function RunPlan() {
  const { runState } = useOutletContext<RunTabContext>()
  const { plan, steps = [] } = runState
  const [inspectPlan, setInspectPlan] = useState<any>(null)

  // Build a live status map from the REST-hydrated steps array.
  // plan.steps (from SSE plan.created) only carries 'pending' initially;
  // steps[] (from REST hydration + SSE verification events) has real statuses.
  const liveStatusMap: Record<string, string> = {}
  for (const s of steps) {
    if (s.step_key) liveStatusMap[s.step_key] = s.status ?? 'pending'
  }

  // Plan steps could be inside plan.steps or state.steps
  const planStepsRaw = (plan as any)?.steps ?? steps
  const planSteps = Array.isArray(planStepsRaw) ? planStepsRaw : []

  if (!plan && steps.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <EmptyState
          icon={<Map size={22} />}
          title="Plan not yet created"
          description="The execution plan will appear here once planning is complete."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono">
            Execution Plan
          </p>
          {(plan as any)?.total_steps && (
            <p className="text-[11px] text-white/50 mt-0.5">
              {(plan as any).total_steps} total steps planned
            </p>
          )}
        </div>

        {plan && (
          <button
            onClick={() => setInspectPlan(plan)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono text-white/50 hover:text-white/80 hover:bg-white/5 border border-white/[0.06] transition-colors"
          >
            <Code size={11} />
            <span>Raw Plan</span>
          </button>
        )}
      </div>

      <div className="space-y-2">
        {planSteps.map((step: any, i: number) => {
          const stepKey = typeof step === 'string' ? step : (step.step_key ?? step.key ?? `step-${i}`)
          const action = typeof step === 'string' ? step : (step.action ?? step.description ?? stepKey)
          const agent = typeof step === 'object' ? step.agent : undefined
          const tool = typeof step === 'object' ? step.tool : undefined
          // Use live status from the REST/SSE-updated steps array; fall back to
          // what the plan event carried (which starts as 'pending' for all steps).
          const status = liveStatusMap[stepKey] ?? (typeof step === 'object' ? step.status : undefined) ?? 'pending'

          return (
            <div
              key={`${stepKey}-${i}`}
              className="flex items-start gap-3.5 px-4 py-3 rounded-xl border border-white/[0.06] bg-[#0e0e0e] hover:border-white/[0.09] transition-colors"
            >
              <div className="w-6 h-6 rounded-md flex items-center justify-center bg-white/8 text-[10px] text-white/60 font-mono flex-shrink-0 mt-0.5">
                {i + 1}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-[12px] text-white/85 font-medium">{action}</p>
                <div className="flex items-center gap-3 mt-1 text-[10px] text-white/35 font-mono">
                  <span>key: {stepKey}</span>
                  {agent && <span className="text-blue-400">agent: {agent}</span>}
                  {tool && <span className="text-amber-300">tool: {tool}</span>}
                </div>
              </div>

              {status && (
                <span
                  className={cn(
                    'text-[10px] font-mono px-2 py-0.5 rounded uppercase',
                    status === 'completed'
                      ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
                      : status === 'running'
                      ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                      : status === 'failed'
                      ? 'text-red-400 bg-red-500/10 border border-red-500/20'
                      : 'text-white/30 bg-white/5 border border-white/[0.06]'
                  )}
                >
                  {status}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {inspectPlan && (
        <RawDataDrawer
          title="Planner Execution Plan"
          data={inspectPlan}
          isOpen={true}
          onClose={() => setInspectPlan(null)}
        />
      )}
    </div>
  )
}

export function RunAgents() {
  const { runState } = useOutletContext<RunTabContext>()
  const { activeAgents = {} } = runState
  const agents = Object.values(activeAgents)

  if (agents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <EmptyState
          icon={<Users size={22} />}
          title="No agents spawned yet"
          description="Agents will appear here as the planner dispatches execution waves."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-3 max-w-5xl mx-auto">
      <p className="text-[10px] uppercase tracking-widest text-white/30 font-semibold font-mono mb-2">
        Active Agents ({agents.length})
      </p>

      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent.agent_id}
            className="flex items-center gap-4 px-4 py-3 rounded-xl border border-white/[0.06] bg-[#0e0e0e] hover:border-white/[0.09] transition-colors"
          >
            <StatusDot status={agent.status} />
            <div className="flex-1 min-w-0">
              <p className="text-[12px] text-white/90 font-medium">{agent.agent_id}</p>
              {agent.action && (
                <p className="text-[11px] text-white/40 mt-0.5">{agent.action}</p>
              )}
              {agent.lastSummary && (
                <p className="text-[10px] text-white/30 italic mt-0.5 font-mono">
                  Summary: {agent.lastSummary}
                </p>
              )}
            </div>
            {agent.step_key && (
              <span className="text-[10px] text-white/30 font-mono">{agent.step_key}</span>
            )}
            <StatusBadge status={agent.status} />
          </div>
        ))}
      </div>
    </div>
  )
}
