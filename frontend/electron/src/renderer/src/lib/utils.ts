import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseDate(ts: string | number | undefined | null): Date | null {
  if (ts === undefined || ts === null || ts === '') return null
  if (typeof ts === 'number') {
    if (isNaN(ts)) return null
    // If it's seconds (< 1e11), multiply by 1000. If ms, use directly.
    const ms = ts < 1e11 ? ts * 1000 : ts
    const d = new Date(ms)
    return isNaN(d.getTime()) ? null : d
  }
  if (typeof ts === 'string') {
    const num = Number(ts)
    if (!isNaN(num) && num > 0) {
      const ms = num < 1e11 ? num * 1000 : num
      const d = new Date(ms)
      if (!isNaN(d.getTime())) return d
    }
    // String like "2026-09-19 15:41:39.401614"
    let normalized = ts.trim().replace(' ', 'T')
    if (!normalized.endsWith('Z') && !normalized.includes('+') && !normalized.slice(10).includes('-')) {
      normalized += 'Z'
    }
    const d = new Date(normalized)
    if (!isNaN(d.getTime())) return d
    const dFallback = new Date(ts)
    return isNaN(dFallback.getTime()) ? null : dFallback
  }
  return null
}

export function formatTimestamp(ts: string | number | undefined | null): string {
  const d = parseDate(ts)
  if (!d) return '--:--:--'
  try {
    return d.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return '--:--:--'
  }
}

export function formatRelativeTime(ts: string | number | undefined | null): string {
  const d = parseDate(ts)
  if (!d) return ''
  const diffSec = Math.floor((Date.now() - d.getTime()) / 1000)
  if (diffSec < 0) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  return `${Math.floor(diffSec / 86400)}d ago`
}

export function formatDuration(ms: number | string | undefined | null): string {
  if (ms === undefined || ms === null) return ''
  const num = typeof ms === 'number' ? ms : Number(ms)
  if (isNaN(num)) return ''
  if (num < 1000) return `${Math.round(num)}ms`
  return `${(num / 1000).toFixed(1)}s`
}

export function formatFileSize(bytes: number | string | undefined | null): string {
  if (bytes === undefined || bytes === null) return ''
  const num = typeof bytes === 'number' ? bytes : Number(bytes)
  if (isNaN(num)) return ''
  if (num < 1024) return `${num} B`
  if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`
  return `${(num / (1024 * 1024)).toFixed(1)} MB`
}

export function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len) + '…'
}

export function fileExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() ?? ''
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'running': return 'text-[hsl(var(--info))]'
    case 'completed': return 'text-[hsl(var(--success))]'
    case 'failed': return 'text-[hsl(var(--danger))]'
    case 'waiting_approval':
    case 'waiting': return 'text-[hsl(var(--warning))]'
    case 'queued': return 'text-[hsl(var(--text-tertiary))]'
    case 'cancelled': return 'text-[hsl(var(--text-disabled))]'
    default: return 'text-[hsl(var(--text-tertiary))]'
  }
}

export function getStatusDotClass(status: string): string {
  switch (status) {
    case 'running': return 'status-dot running'
    case 'completed': return 'status-dot completed'
    case 'failed': return 'status-dot failed'
    case 'waiting_approval':
    case 'waiting': return 'status-dot waiting'
    case 'queued': return 'status-dot queued'
    default: return 'status-dot idle'
  }
}

export function getEventLabel(eventType: string): string {
  const labels: Record<string, string> = {
    'stream.connected': 'Connected',
    'run.created': 'Run Created',
    'run.started': 'Run Started',
    'run.completed': 'Completed',
    'run.failed': 'Failed',
    'run.cancelled': 'Cancelled',
    'run.waiting_approval': 'Waiting Approval',
    'rag.query': 'RAG Query',
    'rag.retrieval.completed': 'Context Retrieved',
    'intent.completed': 'Intent Extracted',
    'plan.created': 'Plan Created',
    'plan.validated': 'Plan Validated',
    'plan.wave_dispatched': 'Wave Dispatched',
    'agent.spawned': 'Agent Spawned',
    'agent.plan_summary': 'Agent Summary',
    'agent.started': 'Agent Started',
    'agent.waiting': 'Agent Waiting',
    'agent.completed': 'Agent Completed',
    'agent.failed': 'Agent Failed',
    'tool.proposed': 'Tool Proposed',
    'tool.validated': 'Tool Validated',
    'tool.authorized': 'Tool Authorized',
    'tool.started': 'Tool Started',
    'tool.invoked': 'Tool Invoked',
    'tool.completed': 'Tool Completed',
    'tool.failed': 'Tool Failed',
    'observation.captured': 'Observed',
    'verification.started': 'Verifying',
    'verification.passed': 'Verified ✓',
    'verification.failed': 'Verify Failed',
    'recovery.triggered': 'Recovery',
    'approval.requested': 'Approval Required',
    'approval.decided': 'Approval Decided',
    'workflow.memory_recorded': 'Memory Recorded',
  }
  return labels[eventType] ?? eventType
}
