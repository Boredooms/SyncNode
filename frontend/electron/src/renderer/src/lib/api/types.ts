// ────────────────────────────────────────────────────────
// SyncNode API Types
// Strictly aligned with shared/schemas/entities.json,
// shared/events/events.json, and backend FastAPI contracts.
// ────────────────────────────────────────────────────────

export type RunStatus = 'queued' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'cancelled'

export interface Run {
  run_id: string
  goal: string
  status: RunStatus
  model_id?: string | null
  failure_mode?: string | null
  created_at: string | number
  started_at?: string | number | null
  completed_at?: string | number | null
  error?: string | null
  error_message?: string | null
}

export interface RunStep {
  step_key: string
  run_id?: string
  action?: string | null
  agent?: string | null
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'waiting_approval' | string
  verification?: 'PASS' | 'FAIL' | string | null
  retries?: number
  started_at?: string | number
  completed_at?: string | number
  tool?: string
  inputs?: Record<string, unknown>
  outputs?: Record<string, unknown>
  error?: string
}

export interface Artifact {
  artifact_id?: string
  run_id?: string
  name: string
  type: string // "word", "excel", "file", etc.
  kind?: string // normalized alias for UI
  path: string
  size_bytes?: number
  sha256?: string | null
  created_at?: string | number
  step_key?: string
  agent?: string
  verified?: boolean
}

export interface ToolCall {
  tool_call_id?: string
  run_id?: string
  step_key?: string
  tool_key: string
  agent?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | string
  side_effect_type?: string | null
  duration_ms?: number | null
  error_message?: string | null
  inputs?: Record<string, unknown>
  outputs?: Record<string, unknown>
  risk?: string
  started_at?: string | number
  completed_at?: string | number
}

export interface Observation {
  observation_id?: string
  run_id?: string
  step_key?: string
  observation_type: string // "tool_result", "screenshot", etc.
  kind?: string // normalized alias
  application?: string | null
  window_title?: string | null
  process_id?: number | null
  content?: string
  screenshot_path?: string | null
  screenshot_hash?: string | null
  captured_at?: string | number
  ts?: string | number
  agent?: string
  tool?: string
}

export interface VerificationAssertion {
  assertion_type?: string
  target?: string
  expected?: unknown
  actual?: unknown
  passed?: boolean
  evidence?: unknown
  error?: string | null
}

export interface Verification {
  verification_id?: string
  run_id?: string
  step_key?: string
  result: 'PASS' | 'FAIL' | 'STALE' | 'UNAVAILABLE' | string
  status: 'passed' | 'failed' | 'stale' | 'unavailable' | string // normalized
  assertions?: VerificationAssertion[] | { items?: VerificationAssertion[] } | unknown
  evidence?: unknown
  failure_reason?: string | null
  ts?: string | number
}

export interface Approval {
  approval_id: string
  run_id?: string
  step_id?: string | null
  step_key?: string
  action: string
  action_summary?: string
  risk?: string
  risk_class?: string
  context?: Record<string, unknown>
  artifacts?: string[]
  status: 'pending' | 'approved' | 'rejected' | 'expired' | string
  decision?: string
  reason?: string
  created_at?: string | number
  decided_at?: string | number
  expires_at?: string | null
}

export interface ContextDoc {
  doc_id: string
  source?: string
  path?: string
  snippet?: string
  relevance?: number
  trust?: string
  score?: number
  content_hash?: string
  provenance?: string
}

export interface RunContext {
  run_id: string
  query?: string
  documents: ContextDoc[]
  rag?: {
    required?: boolean
    reason?: string
    documents?: ContextDoc[]
  }
}

export interface AuditEvent {
  event_id?: string
  seq?: number
  run_id?: string
  event_type: string // normalized
  type?: string
  hash?: string
  ts: string | number
  agent?: string
  step_key?: string
  payload?: Record<string, unknown>
  raw?: Record<string, unknown>
}

export interface Agent {
  agent_id: string
  name: string
  description?: string
  capabilities?: string[]
  allowed_tools?: string[]
  risk_class?: string
  status?: string
}

export interface Tool {
  key: string
  name: string
  description?: string
  category?: string
  risk_class?: string
  side_effect_type?: string
  capabilities?: string[]
  timeout_seconds?: number
}

export interface KnowledgeDoc {
  doc_id: string
  id?: string
  title: string
  path?: string
  type?: string
  kind?: string
  trust?: string
  trust_tier?: string
  content?: string
  body?: string
  created_at?: string | number
  updated_at?: string | number
}

export interface KnowledgeSearchResult {
  doc_id: string
  title: string
  snippet: string
  relevance: number
  path?: string
}

export interface LearningMemory {
  task_type: string
  entries?: unknown[]
  tool_sequence?: string[]
  success?: boolean
  total_reward?: number
}

export interface LearningCandidate {
  candidate_id: string
  id?: string
  task_type: string
  summary?: string
  description?: string
  confidence?: number
  rationale?: string
  lifecycle?: string
  status?: string
}

// Health
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable' | 'ok' | string
  component?: string
  model_id?: string
  error?: string
}

// SSE Event envelope (from shared/events/events.json)
export interface SSEEvent {
  event_type: string
  run_id: string
  ts?: string | number
  event_id?: string
  [key: string]: any
}

// Create run request
export interface CreateRunRequest {
  goal: string
  failure_mode?: string
  model_id?: string
}

// Approval decision
export interface ApprovalDecision {
  decision: 'approved' | 'rejected'
  reason?: string
}

// ── Models ────────────────────────────────────────────────────────────────────

export interface ModelCapabilities {
  completion: boolean
  vision: boolean
  audio: boolean
  tools: boolean
  thinking: boolean
  streaming: boolean
  structured_output: boolean
  context_window: number
  parameter_size?: string | null
  quantization?: string | null
}

export interface ModelProfile {
  model_id: string
  display_name: string
  provider: string
  capabilities: ModelCapabilities
  size_bytes?: number | null
  digest?: string | null
  is_active: boolean
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface ChatSession {
  session_id: string
  title: string
  summary?: string | null
  message_count: number
  created_at?: number | null
  updated_at?: number | null
}

export interface ChatMessage {
  message_id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: Array<{ tool: string; args: Record<string, unknown> }> | null
  tool_results?: Array<{ tool: string; success: boolean; result: unknown }> | null
  seq: number
  created_at?: number | null
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

// SSE events emitted by the chat stream endpoint
export type ChatStreamEvent =
  | { type: 'delta';       content: string }
  | { type: 'tool_start';  tool: string; args: Record<string, unknown> }
  | { type: 'tool_result'; tool: string; success: boolean; result: string }
  | { type: 'summary';     text: string }
  | { type: 'status';      text: string }
  | { type: 'done';        message_id: string; usage: { in: number; out: number } }
  | { type: 'error';       message: string }
