import { create } from 'zustand'
import type {
  Run,
  RunStep,
  Artifact,
  ToolCall,
  Observation,
  Verification,
  Approval,
  RunContext,
  AuditEvent,
  SSEEvent,
} from '../lib/api/types'
import type { StreamState } from '../lib/sse/stream'
import { syncLogger } from '../lib/logger'
import { getLocalRuns } from '../lib/api/client'

export interface ActiveAgentState {
  agent_id: string
  status: string
  step_key?: string
  action?: string
  lastSummary?: string
}

export interface RunState {
  run: Run | null
  steps: RunStep[]
  artifacts: Artifact[]
  tools: ToolCall[]
  observations: Observation[]
  verifications: Verification[]
  approvals: Approval[]
  context: RunContext | null
  auditEvents: AuditEvent[]
  sseEvents: SSEEvent[]
  streamState: StreamState | null
  intent: Record<string, unknown> | null
  plan: {
    total_steps?: number
    steps?: Array<string | { key?: string; step_key?: string; action?: string; agent?: string; tool?: string; status?: string }>
    [key: string]: any
  } | null
  activeAgents: Record<string, ActiveAgentState>
  workflowMemory?: any
}

interface RunStore {
  runs: Record<string, RunState>
  runList: Run[]
  activeRunId: string | null

  setRunList: (runs: Run[]) => void
  setActiveRunId: (runId: string | null) => void
  initRun: (runId: string, run: Run) => void
  updateRun: (runId: string, run: Partial<Run>) => void
  hydrateRunState: (runId: string, partial: Partial<RunState>) => void
  appendEvent: (runId: string, event: SSEEvent) => void
  setStreamState: (runId: string, state: StreamState) => void
  getRunState: (runId: string) => RunState | undefined
}

function defaultRunState(run: Run): RunState {
  return {
    run,
    steps: [],
    artifacts: [],
    tools: [],
    observations: [],
    verifications: [],
    approvals: [],
    context: null,
    auditEvents: [],
    sseEvents: [],
    streamState: null,
    intent: null,
    plan: null,
    activeAgents: {},
  }
}

function applyEvent(state: RunState, event: SSEEvent): Partial<RunState> {
  const updates: Partial<RunState> = {
    sseEvents: [...state.sseEvents, event],
  }

  const eventType = event.event_type || 'unknown'

  switch (eventType) {
    case 'run.created':
    case 'run.started':
    case 'run.completed':
    case 'run.failed':
    case 'run.cancelled':
    case 'run.waiting_approval': {
      const statusMap: Record<string, Run['status']> = {
        'run.created': 'queued',
        'run.started': 'running',
        'run.completed': 'completed',
        'run.failed': 'failed',
        'run.cancelled': 'cancelled',
        'run.waiting_approval': 'waiting_approval',
      }
      if (state.run) {
        updates.run = {
          ...state.run,
          status: statusMap[eventType] ?? state.run.status,
          completed_at: eventType === 'run.completed' ? (event.ts ?? Date.now() / 1000) : state.run.completed_at,
          error: event.error ?? state.run.error,
        }
      }
      // On terminal events: mark every active agent as completed/failed
      // so the panel never shows stale "spawned" badges after the run ends.
      if (eventType === 'run.completed' || eventType === 'run.failed' || eventType === 'run.cancelled') {
        const terminalAgentStatus = eventType === 'run.completed' ? 'completed' : 'failed'
        const updatedAgents: Record<string, any> = {}
        for (const [id, agent] of Object.entries(state.activeAgents)) {
          updatedAgents[id] = {
            ...agent,
            status: agent.status === 'completed' || agent.status === 'failed' ? agent.status : terminalAgentStatus,
          }
        }
        if (Object.keys(updatedAgents).length > 0) updates.activeAgents = updatedAgents
      }
      // run.waiting_approval: push Approval if event carries approval_id.
      if (eventType === 'run.waiting_approval' && event.approval_id) {
        const approvalId = event.approval_id as string
        const alreadyPresent = state.approvals.some((a) => a.approval_id === approvalId)
        if (!alreadyPresent) {
          const syntheticApproval: Approval = {
            approval_id: approvalId,
            run_id: event.run_id,
            action: (event.action ?? 'External communication requires approval') as string,
            action_summary: (event.action ?? 'External communication requires approval') as string,
            risk: 'EXTERNAL_COMMUNICATION',
            risk_class: 'EXTERNAL_COMMUNICATION',
            status: 'pending',
            created_at: event.ts ?? Date.now() / 1000,
          }
          updates.approvals = [...state.approvals, syntheticApproval]
        }
      }
      break
    }

    case 'intent.completed': {
      updates.intent = (event.intent as Record<string, unknown>) ?? event
      break
    }

    case 'enricher.completed': {
      // Store enriched fields alongside intent for display
      const existing = (state.intent as any) ?? {}
      updates.intent = {
        ...existing,
        _enriched_recipient: event.recipient,
        _enriched_subject: event.subject,
        _enriched_filename: event.filename,
        _enriched_goal_type: event.goal_type_hint,
      }
      break
    }

    case 'plan.created':
    case 'plan.validated': {
      updates.plan = event as any
      // If plan specifies steps as string array, normalize into step objects if steps is empty
      if (Array.isArray(event.steps) && state.steps.length === 0) {
        updates.steps = event.steps.map((s: any) => ({
          step_key: typeof s === 'string' ? s : s.step_key ?? s.key ?? 'step',
          action: typeof s === 'string' ? s : s.action ?? s.description,
          status: 'pending',
        }))
      }
      break
    }

    case 'agent.spawned':
    case 'agent.started':
    case 'agent.waiting':
    case 'agent.completed':
    case 'agent.failed':
    case 'agent.cancelled': {
      const agentId = (event.agent_id ?? event.agent) as string | undefined
      if (agentId) {
        const statusMap: Record<string, string> = {
          'agent.spawned': 'spawned',
          'agent.started': 'running',
          'agent.waiting': 'waiting',
          'agent.completed': 'completed',
          'agent.failed': 'failed',
          'agent.cancelled': 'cancelled',
        }
        const existing = state.activeAgents[agentId]
        updates.activeAgents = {
          ...state.activeAgents,
          [agentId]: {
            agent_id: agentId,
            status: statusMap[eventType] ?? 'unknown',
            step_key: (event.step_key as string) ?? existing?.step_key,
            action: (event.action as string) ?? existing?.action,
            lastSummary: existing?.lastSummary,
          },
        }
      }
      break
    }

    case 'agent.plan_summary': {
      const agentId = (event.agent_id ?? event.agent) as string | undefined
      if (agentId && state.activeAgents[agentId]) {
        updates.activeAgents = {
          ...state.activeAgents,
          [agentId]: {
            ...state.activeAgents[agentId],
            lastSummary: event.summary as string,
          },
        }
      }
      break
    }

    case 'tool.proposed':
    case 'tool.authorized':
    case 'tool.invoked':
    case 'tool.started':
    case 'tool.completed':
    case 'tool.failed': {
      const toolKey = (event.tool_key ?? event.tool) as string | undefined
      if (toolKey) {
        const status = eventType.replace('tool.', '')
        const stepKey = (event.step_key as string) ?? ''
        const agent = (event.agent ?? (toolKey.includes('.') ? toolKey.split('.')[0] : undefined)) as string | undefined

        const existingIdx = state.tools.findIndex((t) => t.tool_key === toolKey && t.step_key === stepKey)
        if (existingIdx >= 0) {
          const updated = [...state.tools]
          updated[existingIdx] = {
            ...updated[existingIdx],
            status,
            agent: agent ?? updated[existingIdx].agent,
            risk: (event.risk as string) ?? updated[existingIdx].risk,
            completed_at: status === 'completed' || status === 'failed' ? (event.ts ?? Date.now() / 1000) : undefined,
          }
          updates.tools = updated
        } else {
          const newTool: ToolCall = {
            tool_call_id: `${stepKey}-${toolKey}-${event.ts ?? Date.now()}`,
            run_id: event.run_id,
            step_key: stepKey,
            tool_key: toolKey,
            agent,
            status,
            risk: event.risk as string | undefined,
            started_at: event.ts,
          }
          updates.tools = [...state.tools, newTool]
        }
      }
      break
    }

    case 'observation.captured':
    case 'screenshot.created': {
      const newObs: Observation = {
        observation_id: event.observation_id ?? `obs-${Date.now()}`,
        run_id: event.run_id,
        step_key: (event.step_key as string) ?? '',
        observation_type: eventType === 'screenshot.created' ? 'screenshot' : (event.observation_type ?? 'observation'),
        kind: eventType === 'screenshot.created' ? 'screenshot' : (event.observation_type ?? 'observation'),
        screenshot_path: event.path ?? event.screenshot_path,
        screenshot_hash: event.sha256 ?? event.screenshot_hash,
        content: event.content,
        captured_at: event.ts ?? Date.now() / 1000,
        ts: event.ts ?? Date.now() / 1000,
      }
      updates.observations = [...state.observations, newObs]
      break
    }

    case 'verification.started':
    case 'verification.passed':
    case 'verification.failed': {
      const status = eventType === 'verification.passed' ? 'passed' : eventType === 'verification.failed' ? 'failed' : 'running'
      const result = status === 'passed' ? 'PASS' : status === 'failed' ? 'FAIL' : 'VERIFYING'
      const stepKey = (event.step_key as string) ?? ''

      const existingIdx = state.verifications.findIndex((v) => v.step_key === stepKey)
      const newV: Verification = {
        verification_id: `verif-${stepKey}-${event.ts ?? Date.now()}`,
        run_id: event.run_id,
        step_key: stepKey,
        status,
        result,
        assertions: event.assertions,
        failure_reason: event.failure_reason as string | undefined,
        ts: event.ts,
      }

      if (existingIdx >= 0) {
        const updated = [...state.verifications]
        updated[existingIdx] = newV
        updates.verifications = updated
      } else {
        updates.verifications = [...state.verifications, newV]
      }

      // Also update step status in steps list if present
      if (stepKey && state.steps.length > 0) {
        updates.steps = state.steps.map((s) =>
          s.step_key === stepKey
            ? { ...s, verification: result, status: status === 'passed' ? 'completed' : status === 'failed' ? 'failed' : s.status }
            : s
        )
      }
      break
    }

    case 'approval.requested': {
      const newApproval: Approval = {
        approval_id: (event.approval_id as string) ?? `${event.run_id}-${event.ts}`,
        run_id: event.run_id,
        step_key: event.step_key as string | undefined,
        action: (event.action ?? event.action_summary ?? 'Approval required') as string,
        risk: (event.risk ?? event.risk_class ?? 'high') as string,
        context: event.context as Record<string, unknown> | undefined,
        artifacts: event.artifacts as string[] | undefined,
        status: 'pending',
        created_at: event.ts ?? Date.now() / 1000,
      }
      updates.approvals = [...state.approvals, newApproval]
      break
    }

    case 'approval.decided': {
      updates.approvals = state.approvals.map((a) =>
        a.approval_id === event.approval_id
          ? { ...a, status: (event.decision as string) ?? 'approved', decided_at: event.ts ?? Date.now() / 1000 }
          : a
      )
      break
    }

    case 'workflow.memory_recorded': {
      updates.workflowMemory = event
      break
    }

    default: {
      // Unknown event type: record and do not crash
      syncLogger.debug('STATE', `Safely recorded unmapped event type: ${eventType}`, event)
      break
    }
  }

  return updates
}

export const useRunStore = create<RunStore>((set, get) => ({
  runs: {},
  runList: getLocalRuns(),
  activeRunId: null,

  setRunList: (runs) => set({ runList: Array.isArray(runs) ? runs : [] }),
  setActiveRunId: (runId) => set({ activeRunId: runId }),

  initRun: (runId, run) =>
    set((s) => ({
      runs: { ...s.runs, [runId]: defaultRunState(run) },
    })),

  updateRun: (runId, run) =>
    set((s) => {
      const existing = s.runs[runId]
      if (!existing) return s
      return {
        runs: {
          ...s.runs,
          [runId]: { ...existing, run: { ...existing.run!, ...run } },
        },
      }
    }),

  hydrateRunState: (runId, partial) =>
    set((s) => {
      const existing = s.runs[runId]
      if (!existing && !partial.run) return s

      const base = existing ?? defaultRunState(partial.run!)
      const merged: RunState = {
        ...base,
        ...partial,
        run: partial.run ? { ...base.run, ...partial.run } : base.run,
        steps: partial.steps ? (Array.isArray(partial.steps) ? partial.steps : base.steps) : base.steps,
        artifacts: partial.artifacts ? (Array.isArray(partial.artifacts) ? partial.artifacts : base.artifacts) : base.artifacts,
        tools: partial.tools ? (Array.isArray(partial.tools) ? partial.tools : base.tools) : base.tools,
        observations: partial.observations ? (Array.isArray(partial.observations) ? partial.observations : base.observations) : base.observations,
        verifications: partial.verifications ? (Array.isArray(partial.verifications) ? partial.verifications : base.verifications) : base.verifications,
        approvals: partial.approvals ? (Array.isArray(partial.approvals) ? partial.approvals : base.approvals) : base.approvals,
        auditEvents: partial.auditEvents ? (Array.isArray(partial.auditEvents) ? partial.auditEvents : base.auditEvents) : base.auditEvents,
      }

      // Reconstruct active agents from steps / tools if activeAgents is empty
      if (Object.keys(merged.activeAgents).length === 0) {
        const derivedAgents: Record<string, ActiveAgentState> = {}
        for (const step of merged.steps) {
          if (step.agent) {
            derivedAgents[step.agent] = {
              agent_id: step.agent,
              status: step.status,
              step_key: step.step_key,
              action: step.action ?? undefined,
            }
          }
        }
        for (const tool of merged.tools) {
          if (tool.agent && !derivedAgents[tool.agent]) {
            derivedAgents[tool.agent] = {
              agent_id: tool.agent,
              status: tool.status,
              step_key: tool.step_key,
            }
          }
        }
        if (Object.keys(derivedAgents).length > 0) {
          merged.activeAgents = derivedAgents
        }
      }

      return {
        runs: { ...s.runs, [runId]: merged },
      }
    }),

  appendEvent: (runId, event) =>
    set((s) => {
      const existing = s.runs[runId]
      if (!existing) return s
      const updates = applyEvent(existing, event)
      return {
        runs: { ...s.runs, [runId]: { ...existing, ...updates } },
      }
    }),

  setStreamState: (runId, state) =>
    set((s) => ({
      runs: {
        ...s.runs,
        [runId]: { ...(s.runs[runId] ?? ({} as RunState)), streamState: state },
      },
    })),

  getRunState: (runId) => get().runs[runId],
}))
