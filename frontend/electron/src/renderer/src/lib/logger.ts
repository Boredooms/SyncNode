// ────────────────────────────────────────────────────────
// SyncNode Structured Frontend Observability Logger
// In-memory ring buffer + categorized dev console output.
// ────────────────────────────────────────────────────────

export type LogCategory =
  | 'API'
  | 'SSE'
  | 'STATE'
  | 'ROUTER'
  | 'RUN'
  | 'AGENT'
  | 'TOOL'
  | 'ARTIFACT'
  | 'VERIFICATION'
  | 'APPROVAL'
  | 'AUTOMATION'
  | 'ERROR'

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export interface LogEntry {
  id: string
  timestamp: number
  category: LogCategory
  level: LogLevel
  message: string
  data?: any
}

type LogListener = (entry: LogEntry) => void

class SyncNodeLogger {
  private buffer: LogEntry[] = []
  private maxBufferSize = 300
  private listeners: Set<LogListener> = new Set()

  private record(level: LogLevel, category: LogCategory, message: string, data?: any) {
    const entry: LogEntry = {
      id: Math.random().toString(36).slice(2, 9),
      timestamp: Date.now(),
      category,
      level,
      message,
      data,
    }

    this.buffer.push(entry)
    if (this.buffer.length > this.maxBufferSize) {
      this.buffer.shift()
    }

    // Format console prefix
    const prefix = `[SYNCNODE:${category}]`
    const consoleMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : level === 'info' ? console.info : console.debug

    if (data !== undefined) {
      consoleMethod(prefix, message, data)
    } else {
      consoleMethod(prefix, message)
    }

    // Notify live listeners
    for (const listener of this.listeners) {
      try {
        listener(entry)
      } catch {}
    }
  }

  debug(category: LogCategory, message: string, data?: any) {
    this.record('debug', category, message, data)
  }

  info(category: LogCategory, message: string, data?: any) {
    this.record('info', category, message, data)
  }

  warn(category: LogCategory, message: string, data?: any) {
    this.record('warn', category, message, data)
  }

  error(category: LogCategory, message: string, data?: any) {
    this.record('error', category, message, data)
  }

  getHistory(): LogEntry[] {
    return [...this.buffer]
  }

  clear() {
    this.buffer = []
  }

  subscribe(listener: LogListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }
}

export const syncLogger = new SyncNodeLogger()
