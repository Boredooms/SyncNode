// ────────────────────────────────────────────────────────
// SyncNode Defensive SSE Stream Manager
// Ultra-defensive parsing, envelope normalization,
// exponential backoff reconnects, and single-stream guarantees.
// ────────────────────────────────────────────────────────
import type { SSEEvent } from '../api/types'
import { syncLogger } from '../logger'

const BASE_URL = 'http://127.0.0.1:8000'
const MAX_RECONNECT_DELAY = 15_000

export type StreamState = 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'terminal'

export interface StreamCallbacks {
  onEvent: (event: SSEEvent) => void
  onStateChange: (state: StreamState) => void
  onError?: (error: Error) => void
}

const TERMINAL_EVENTS = new Set(['run.completed', 'run.failed', 'run.cancelled'])

export class RunStream {
  private runId: string
  private callbacks: StreamCallbacks
  private eventSource: EventSource | null = null
  private reconnectDelay = 1000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private closed = false
  private seenEventKeys = new Set<string>()

  constructor(runId: string, callbacks: StreamCallbacks) {
    this.runId = runId
    this.callbacks = callbacks
    this.connect()
  }

  private connect() {
    if (this.closed) return
    const url = `${BASE_URL}/api/v1/runs/${this.runId}/events`
    this.callbacks.onStateChange('connecting')
    syncLogger.debug('SSE', `Connecting to stream for run=${this.runId}`)

    try {
      this.eventSource = new EventSource(url)
    } catch (err: any) {
      syncLogger.error('SSE', `Failed to construct EventSource: ${err?.message}`, err)
      this.scheduleReconnect()
      return
    }

    this.eventSource.onopen = () => {
      this.reconnectDelay = 1000
      this.callbacks.onStateChange('connected')
      syncLogger.info('SSE', `Stream connected for run=${this.runId}`)
    }

    this.eventSource.onmessage = (raw) => {
      this.handleMessage(raw.data)
    }

    // Transport keepalives
    this.eventSource.addEventListener('heartbeat', () => {
      syncLogger.debug('SSE', `Heartbeat received for run=${this.runId}`)
    })

    this.eventSource.onerror = (err) => {
      if (this.closed) return
      syncLogger.warn('SSE', `Stream error on run=${this.runId}, will reconnect`, err)
      this.cleanupEventSource()
      this.callbacks.onStateChange('reconnecting')
      this.scheduleReconnect()
    }
  }

  private handleMessage(data: string | undefined | null) {
    if (!data || typeof data !== 'string' || data.trim() === '') return

    let rawObj: any
    try {
      rawObj = JSON.parse(data.trim())
    } catch (err: any) {
      syncLogger.warn('SSE', `Malformed JSON in SSE chunk for run=${this.runId}: ${err?.message}`, { rawChunk: data })
      return
    }

    if (!rawObj || typeof rawObj !== 'object') return

    // Defensive envelope normalization
    const eventType = String(rawObj.event_type ?? rawObj.type ?? 'unknown.event')
    const ts = rawObj.ts ?? Date.now() / 1000
    const eventId = rawObj.event_id ?? rawObj.id

    // Deduplication key
    const dedupeKey = eventId
      ? `id:${eventId}`
      : `${eventType}-${ts}-${rawObj.step_key ?? ''}-${rawObj.tool_key ?? rawObj.tool ?? ''}`

    if (this.seenEventKeys.has(dedupeKey)) {
      syncLogger.debug('SSE', `Deduplicated event ${dedupeKey}`)
      return
    }
    this.seenEventKeys.add(dedupeKey)

    const normalizedEvent: SSEEvent = {
      ...rawObj,
      event_type: eventType,
      run_id: String(rawObj.run_id ?? this.runId),
      ts,
    }

    syncLogger.debug('SSE', `Received event=${eventType} run=${this.runId}`, normalizedEvent)

    try {
      this.callbacks.onEvent(normalizedEvent)
    } catch (err: any) {
      syncLogger.error('SSE', `Error in onEvent callback for ${eventType}: ${err?.message}`, err)
    }

    // Close stream gracefully on terminal events
    if (TERMINAL_EVENTS.has(eventType)) {
      syncLogger.info('SSE', `Terminal event ${eventType} encountered. Closing stream for run=${this.runId}`)
      this.callbacks.onStateChange('terminal')
      this.close()
    }
  }

  private scheduleReconnect() {
    if (this.closed) return
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, MAX_RECONNECT_DELAY)
      this.connect()
    }, this.reconnectDelay)
  }

  private cleanupEventSource() {
    if (this.eventSource) {
      this.eventSource.onopen = null
      this.eventSource.onmessage = null
      this.eventSource.onerror = null
      this.eventSource.close()
      this.eventSource = null
    }
  }

  close() {
    this.closed = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.cleanupEventSource()
    this.callbacks.onStateChange('disconnected')
    syncLogger.debug('SSE', `Closed stream for run=${this.runId}`)
  }
}

// ── Singleton Manager: One stream per active run ─────────
const activeStreams = new Map<string, RunStream>()

export function openRunStream(runId: string, callbacks: StreamCallbacks): RunStream {
  const existing = activeStreams.get(runId)
  if (existing) {
    existing.close()
    activeStreams.delete(runId)
  }
  const stream = new RunStream(runId, callbacks)
  activeStreams.set(runId, stream)
  return stream
}

export function closeRunStream(runId: string) {
  const existing = activeStreams.get(runId)
  if (existing) {
    existing.close()
    activeStreams.delete(runId)
  }
}

export function closeAllStreams() {
  for (const [runId, stream] of activeStreams) {
    stream.close()
    activeStreams.delete(runId)
  }
}
