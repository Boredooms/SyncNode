// ────────────────────────────────────────────────────────
// SyncNode API Client
// Connects to http://127.0.0.1:8000 (local backend only)
// Implements defensive unwrapping, contract normalization,
// and zero-405 local run catalog management.
// ────────────────────────────────────────────────────────
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
  Agent,
  Tool,
  KnowledgeDoc,
  KnowledgeSearchResult,
  LearningMemory,
  LearningCandidate,
  HealthStatus,
  CreateRunRequest,
  ApprovalDecision,
} from './types'
import { parseDate } from '../utils'

const BASE_URL = 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`
  const isBodyLess = options?.method === 'GET' || options?.method === 'HEAD' || !options?.method
  
  const headers = new Headers(options?.headers)
  if (!isBodyLess && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(url, {
    ...options,
    headers,
  })
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = body.detail ?? body.message ?? msg
    } catch {}
    throw new ApiError(msg, res.status)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Local Run History (eliminates 405 GET /api/v1/runs) ──
const RUNS_STORAGE_KEY = 'syncnode:runs_catalog'

export function getLocalRuns(): Run[] {
  try {
    const raw = localStorage.getItem(RUNS_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveLocalRun(run: Run): void {
  try {
    const existing = getLocalRuns()
    const index = existing.findIndex((r) => r.run_id === run.run_id)
    if (index >= 0) {
      existing[index] = { ...existing[index], ...run }
    } else {
      existing.unshift(run)
    }
    // Keep max 50 runs
    localStorage.setItem(RUNS_STORAGE_KEY, JSON.stringify(existing.slice(0, 50)))
  } catch {
    // Ignore storage errors
  }
}

// ── Normalization Functions ──────────────────────────────

export function normalizeRun(raw: any): Run {
  if (!raw || typeof raw !== 'object') {
    return {
      run_id: 'unknown',
      goal: 'Unknown task',
      status: 'failed',
      created_at: Date.now() / 1000,
    }
  }
  return {
    run_id: String(raw.run_id ?? ''),
    goal: String(raw.goal ?? 'Untitled Run'),
    status: (raw.status as Run['status']) ?? 'queued',
    model_id: raw.model_id ?? null,
    failure_mode: raw.failure_mode ?? null,
    created_at: raw.created_at ?? Date.now() / 1000,
    started_at: raw.started_at ?? null,
    completed_at: raw.completed_at ?? null,
    error: raw.error ?? raw.error_message ?? null,
    error_message: raw.error_message ?? raw.error ?? null,
  }
}

export function normalizeStep(raw: any, runId?: string): RunStep {
  return {
    step_key: String(raw.step_key ?? raw.key ?? 'step'),
    run_id: raw.run_id ?? runId,
    action: raw.action ?? raw.description ?? null,
    agent: raw.agent ?? null,
    status: raw.status ?? 'pending',
    verification: raw.verification ?? null,
    retries: typeof raw.retries === 'number' ? raw.retries : 0,
    started_at: raw.started_at,
    completed_at: raw.completed_at,
    tool: raw.tool,
    inputs: raw.inputs,
    outputs: raw.outputs,
    error: raw.error,
  }
}

export function normalizeArtifact(raw: any, runId?: string): Artifact {
  const path = String(raw.path ?? '')
  const name = String(raw.name ?? (path ? path.split(/[/\\]/).pop() : 'artifact'))
  const type = String(raw.type ?? raw.kind ?? (name.includes('.') ? name.split('.').pop() : 'file'))
  return {
    artifact_id: raw.artifact_id ?? `${name}-${raw.sha256?.slice(0, 8) ?? 'item'}`,
    run_id: raw.run_id ?? runId,
    name,
    type,
    kind: type,
    path,
    size_bytes: raw.size_bytes,
    sha256: raw.sha256 ?? null,
    created_at: raw.created_at,
    step_key: raw.step_key,
    agent: raw.agent,
    verified: raw.verified === true || raw.verified === 'true',
  }
}

export function normalizeTool(raw: any, runId?: string): ToolCall {
  const toolKey = String(raw.tool_key ?? raw.key ?? raw.tool ?? 'unknown_tool')
  return {
    tool_call_id: raw.tool_call_id ?? `${toolKey}-${raw.step_key ?? 'call'}-${Math.random().toString(36).slice(2, 7)}`,
    run_id: raw.run_id ?? runId,
    step_key: raw.step_key ?? '',
    tool_key: toolKey,
    agent: raw.agent ?? (toolKey.includes('.') ? toolKey.split('.')[0] : undefined),
    status: raw.status ?? 'completed',
    side_effect_type: raw.side_effect_type ?? null,
    duration_ms: raw.duration_ms ?? null,
    error_message: raw.error_message ?? null,
    inputs: raw.inputs,
    outputs: raw.outputs,
    risk: raw.risk,
    started_at: raw.started_at,
    completed_at: raw.completed_at,
  }
}

export function normalizeObservation(raw: any, runId?: string): Observation {
  const obsType = String(raw.observation_type ?? raw.kind ?? 'observation')
  return {
    observation_id: raw.observation_id ?? `obs-${Math.random().toString(36).slice(2, 8)}`,
    run_id: raw.run_id ?? runId,
    step_key: raw.step_key ?? '',
    observation_type: obsType,
    kind: obsType,
    application: raw.application ?? null,
    window_title: raw.window_title ?? null,
    process_id: raw.process_id ?? null,
    content: raw.content ?? (raw.window_title ? `Window: ${raw.window_title}` : undefined),
    screenshot_path: raw.screenshot_path ?? null,
    screenshot_hash: raw.screenshot_hash ?? null,
    captured_at: raw.captured_at ?? raw.ts,
    ts: raw.captured_at ?? raw.ts,
    agent: raw.agent,
    tool: raw.tool,
  }
}

export function normalizeVerification(raw: any, runId?: string): Verification {
  const result = String(raw.result ?? (raw.status === 'passed' ? 'PASS' : 'FAIL')).toUpperCase()
  const status = result === 'PASS' ? 'passed' : result === 'FAIL' ? 'failed' : result.toLowerCase()
  return {
    verification_id: raw.verification_id ?? `verif-${Math.random().toString(36).slice(2, 8)}`,
    run_id: raw.run_id ?? runId,
    step_key: raw.step_key ?? '',
    result,
    status,
    assertions: raw.assertions,
    evidence: raw.evidence,
    failure_reason: raw.failure_reason ?? null,
    ts: raw.ts,
  }
}

export function normalizeApproval(raw: any, runId?: string): Approval {
  return {
    approval_id: String(raw.approval_id ?? `appr-${Math.random().toString(36).slice(2, 8)}`),
    run_id: raw.run_id ?? runId,
    step_id: raw.step_id ?? raw.step_key ?? null,
    step_key: raw.step_key ?? raw.step_id ?? undefined,
    action: raw.action ?? raw.action_summary ?? 'Action requires human approval',
    action_summary: raw.action_summary ?? raw.action,
    risk: raw.risk ?? raw.risk_class ?? 'high',
    risk_class: raw.risk_class ?? raw.risk ?? 'high',
    context: raw.context ?? {},
    artifacts: Array.isArray(raw.artifacts) ? raw.artifacts : [],
    status: raw.status ?? 'pending',
    decision: raw.decision,
    reason: raw.reason,
    created_at: raw.created_at ?? Date.now() / 1000,
    decided_at: raw.decided_at,
    expires_at: raw.expires_at ?? null,
  }
}

export function normalizeAuditEvent(raw: any, runId?: string): AuditEvent {
  const eventType = String(raw.type ?? raw.event_type ?? 'audit.event')
  return {
    event_id: raw.event_id ?? (raw.hash ? `audit-${raw.hash}` : undefined),
    seq: typeof raw.seq === 'number' ? raw.seq : undefined,
    run_id: raw.run_id ?? runId,
    event_type: eventType,
    type: eventType,
    hash: raw.hash,
    ts: raw.ts ?? Date.now() / 1000,
    agent: raw.agent ?? (eventType.includes('.') ? eventType.split('.')[0] : undefined),
    step_key: raw.step_key,
    payload: raw.payload,
    raw,
  }
}

// ── Health Endpoints ─────────────────────────────────────
export async function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health')
}
export async function getHealthReady(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/ready')
}
export async function getHealthModel(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/model')
}
export async function getHealthDatabase(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/database')
}
export async function getHealthRag(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/rag')
}
export async function getHealthComputer(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/computer')
}
export async function getHealthBrowser(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/browser')
}

// ── Runs Endpoints ───────────────────────────────────────
export async function createRun(req: CreateRunRequest): Promise<Run> {
  const res = await request<any>('/api/v1/runs', {
    method: 'POST',
    body: JSON.stringify(req),
  })
  const run = normalizeRun(res)
  saveLocalRun(run)
  return run
}

export async function listRuns(): Promise<Run[]> {
  // Try the backend list endpoint first; fall back to local catalog if it
  // fails (e.g. backend not running, network error).
  try {
    const res = await request<any>('/api/v1/runs')
    const arr: any[] = Array.isArray(res) ? res : (res?.runs ?? [])
    const backendRuns = arr.map((r: any) => normalizeRun(r))
    // Merge into local catalog so RunsList has them next time
    backendRuns.forEach(saveLocalRun)
    return backendRuns
  } catch {
    return getLocalRuns()
  }
}

export async function getRun(runId: string): Promise<Run> {
  const res = await request<any>(`/api/v1/runs/${runId}`)
  const run = normalizeRun(res)
  saveLocalRun(run)
  return run
}

export async function getRunSteps(runId: string): Promise<RunStep[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/steps`)
  const arr = Array.isArray(res) ? res : (res?.steps || [])
  return arr.map((s: any) => normalizeStep(s, runId))
}

export async function getRunArtifacts(runId: string): Promise<Artifact[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/artifacts`)
  const arr = Array.isArray(res) ? res : (res?.artifacts || [])
  return arr.map((a: any) => normalizeArtifact(a, runId))
}

export async function getRunTools(runId: string): Promise<ToolCall[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/tools`)
  const arr = Array.isArray(res) ? res : (res?.tool_calls || res?.tools || [])
  return arr.map((t: any) => normalizeTool(t, runId))
}

export async function getRunObservations(runId: string): Promise<Observation[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/observations`)
  const arr = Array.isArray(res) ? res : (res?.observations || [])
  return arr.map((o: any) => normalizeObservation(o, runId))
}

export async function getRunVerifications(runId: string): Promise<Verification[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/verifications`)
  const arr = Array.isArray(res) ? res : (res?.verifications || [])
  return arr.map((v: any) => normalizeVerification(v, runId))
}

export async function getRunContext(runId: string): Promise<RunContext> {
  const res = await request<any>(`/api/v1/runs/${runId}/context`)
  const rawCtx = res?.context ?? res ?? {}
  const ragDocs = rawCtx?.rag?.documents ?? rawCtx?.documents ?? []
  const docs = Array.isArray(ragDocs) ? ragDocs : []
  return {
    run_id: runId,
    query: rawCtx.query,
    documents: docs,
    rag: rawCtx.rag,
  }
}

export async function getRunAudit(runId: string): Promise<AuditEvent[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/audit`)
  const arr = Array.isArray(res) ? res : (res?.events || res?.audit_events || [])
  return arr.map((e: any) => normalizeAuditEvent(e, runId))
}

export async function terminateRun(runId: string): Promise<void> {
  return request<void>(`/api/v1/runs/${runId}/terminate`, { method: 'POST' })
}

// ── Approvals Endpoints ──────────────────────────────────
export async function getRunApprovals(runId: string): Promise<Approval[]> {
  const res = await request<any>(`/api/v1/runs/${runId}/approvals`)
  const arr = Array.isArray(res) ? res : (res?.approvals || [])
  return arr.map((a: any) => normalizeApproval(a, runId))
}

export async function decideApproval(
  runId: string,
  approvalId: string,
  decision: ApprovalDecision
): Promise<void> {
  return request<void>(`/api/v1/runs/${runId}/approvals/${approvalId}/decide`, {
    method: 'POST',
    body: JSON.stringify(decision),
  })
}

// ── Tools & Agents ───────────────────────────────────────
export async function listTools(): Promise<Tool[]> {
  const res = await request<any>('/api/v1/tools')
  return Array.isArray(res) ? res : (res.tools || [])
}

export async function getTool(key: string): Promise<Tool> {
  return request<Tool>(`/api/v1/tools/${key}`)
}

export async function listAgents(): Promise<Agent[]> {
  const res = await request<any>('/api/v1/agents')
  return Array.isArray(res) ? res : (res.agents || [])
}

// ── Knowledge ─────────────────────────────────────────────
// Normalize the backend knowledge summary shape ({id,type,path,title,trust,
// version,status,tags,content_hash}[+body]) to the fields the UI reads
// (doc_id, trust_tier, content). Without this the UI showed empty/placeholder
// fields even though the backend returns real data.
function normalizeKnowledgeDoc(d: any): KnowledgeDoc {
  return {
    ...d,
    doc_id: d.doc_id ?? d.id ?? 'unknown',
    id: d.id ?? d.doc_id,
    title: d.title ?? d.path ?? 'Untitled',
    path: d.path,
    kind: d.type ?? d.kind ?? 'reference',
    trust: d.trust,
    trust_tier: d.trust_tier ?? d.trust,          // backend sends `trust`
    tags: Array.isArray(d.tags) ? d.tags : [],
    content: d.content ?? d.body ?? undefined,     // backend sends `body`
    body: d.body ?? d.content ?? undefined,
  }
}

export async function listKnowledge(): Promise<KnowledgeDoc[]> {
  const res = await request<any>('/api/v1/knowledge')
  const docs = Array.isArray(res) ? res : (res.documents || [])
  return docs.map(normalizeKnowledgeDoc)
}

export async function getKnowledgeDoc(docId: string): Promise<KnowledgeDoc> {
  const res = await request<any>(`/api/v1/knowledge/${docId}`)
  return normalizeKnowledgeDoc({ ...res, doc_id: res.doc_id ?? res.id ?? docId })
}

export async function searchKnowledge(query: string): Promise<KnowledgeSearchResult[]> {
  // Backend search is POST /knowledge/search with {query}; response is
  // {query, results:[{...summary, score}]}. Map to the UI's result shape.
  const res = await request<any>('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
  const results = Array.isArray(res) ? res : (res.results || [])
  return results.map((r: any) => ({
    doc_id: r.doc_id ?? r.id ?? 'unknown',
    title: r.title ?? r.path ?? 'Untitled',
    path: r.path,
    snippet: r.snippet ?? r.body?.slice?.(0, 220) ?? '',
    relevance: typeof r.score === 'number' ? r.score : (r.relevance ?? 0),
    trust: r.trust ?? r.trust_tier,
  }))
}

export async function reindexKnowledge(docId: string): Promise<void> {
  return request<void>(`/api/v1/knowledge/${docId}/reindex`, { method: 'POST' })
}

// Create a knowledge document the user authored. `path` must end in .md and be
// relative to the knowledge root; `content` is the full markdown (front matter
// optional — the backend fills sensible defaults).
export async function createKnowledge(path: string, content: string): Promise<KnowledgeDoc> {
  const res = await request<any>('/api/v1/knowledge', {
    method: 'POST',
    body: JSON.stringify({ path, content }),
  })
  return { ...res, doc_id: res.doc_id ?? res.id ?? path }
}

export async function updateKnowledge(docId: string, path: string, content: string): Promise<KnowledgeDoc> {
  const res = await request<any>(`/api/v1/knowledge/${docId}`, {
    method: 'PUT',
    body: JSON.stringify({ path, content }),
  })
  return { ...res, doc_id: res.doc_id ?? res.id ?? docId }
}

export async function deleteKnowledge(docId: string): Promise<void> {
  return request<void>(`/api/v1/knowledge/${docId}`, { method: 'DELETE' })
}

// ── Learning ──────────────────────────────────────────────
export async function getLearningMemory(taskType: string): Promise<LearningMemory> {
  return request<LearningMemory>(`/api/v1/learning/memory/${taskType}`)
}

export async function getLearningCandidates(): Promise<LearningCandidate[]> {
  const res = await request<any>('/api/v1/learning/candidates')
  const list = Array.isArray(res) ? res : (res.candidates || [])
  return list.map((c: any) => ({
    ...c,
    candidate_id: c.candidate_id ?? c.id ?? 'unknown',
    // 'description' is now returned directly by the backend (mapped from 'summary').
    // Fall back gracefully for older records.
    description: c.description ?? c.summary ?? 'Workflow candidate',
    task_type: c.task_type,
    rationale: c.rationale ?? '',
    proposed_tool_sequence: c.proposed_tool_sequence ?? [],
    source_run_id: c.source_run_id ?? null,
  }))
}

export async function reviewLearningCandidate(
  candidateId: string,
  decision: { decision: 'approve' | 'reject'; reason?: string }
): Promise<void> {
  return request<void>(`/api/v1/learning/candidates/${candidateId}/review`, {
    method: 'POST',
    body: JSON.stringify(decision),
  })
}

// ── Chat ──────────────────────────────────────────────────────────────────────
import type { ChatSession, ChatSessionDetail, ChatStreamEvent } from './types'

export async function createChatSession(title = 'New Chat', runId?: string): Promise<ChatSession> {
  const body: Record<string, unknown> = { title }
  if (runId) body.run_id = runId
  const res = await request<any>('/api/v1/chat/sessions', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return { session_id: res.session_id, title: res.title, message_count: 0, created_at: res.created_at }
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const res = await request<any>('/api/v1/chat/sessions')
  return Array.isArray(res.sessions) ? res.sessions : []
}

export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/api/v1/chat/sessions/${sessionId}`)
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  return request<void>(`/api/v1/chat/sessions/${sessionId}`, { method: 'DELETE' })
}

export async function clearChatSession(sessionId: string): Promise<void> {
  return request<void>(`/api/v1/chat/sessions/${sessionId}/clear`, { method: 'POST' })
}

/**
 * Stream a chat message. Returns an async generator of parsed ChatStreamEvent objects.
 * Pass runId to attach full workflow context (steps, artifacts, workspace files).
 */
export async function* streamChatMessage(
  sessionId: string,
  content: string,
  enableTools = true,
  runId?: string,
): AsyncGenerator<ChatStreamEvent> {
  const body: Record<string, unknown> = { content, enable_tools: enableTools }
  if (runId) body.run_id = runId
  const res = await fetch(`${BASE_URL}/api/v1/chat/sessions/${sessionId}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new ApiError(`Chat stream failed: ${body}`, res.status)
  }
  const reader = res.body?.getReader()
  if (!reader) return
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6)) as ChatStreamEvent
          yield event
        } catch { /* skip malformed */ }
      }
    }
  }
}

// Inject a new step into a live run's plan (chat mid-run control)
export async function injectRunStep(
  runId: string,
  action: string,
  description: string,
  inputs: Record<string, unknown> = {},
): Promise<{ injected: boolean; step_key: string; step_index: number }> {
  return request(`/api/v1/runs/${runId}/inject-step`, {
    method: 'POST',
    body: JSON.stringify({ action, description, inputs }),
  })
}
