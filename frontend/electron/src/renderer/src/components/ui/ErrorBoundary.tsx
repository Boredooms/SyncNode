import React, { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp, Bug } from 'lucide-react'
import { syncLogger } from '../../lib/logger'

interface Props {
  panelName?: string
  children: ReactNode
  onReset?: () => void
  onRefreshRun?: () => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
  showRaw: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showRaw: false,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo })
    syncLogger.error('ERROR', `Error in panel [${this.props.panelName ?? 'Generic'}]: ${error.message}`, {
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    })
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, showRaw: false })
    this.props.onReset?.()
  }

  render() {
    if (this.state.hasError) {
      const panel = this.props.panelName ?? 'Panel'
      const errorMsg = this.state.error?.message ?? 'Unknown error'
      const stack = this.state.error?.stack ?? this.state.errorInfo?.componentStack ?? ''

      return (
        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#0a0a0a] text-white select-none">
          <div className="w-full max-w-md p-5 rounded-lg border border-red-500/20 bg-red-950/10 shadow-2xl backdrop-blur-sm">
            <div className="flex items-center gap-2 mb-2 text-red-400">
              <AlertTriangle size={15} />
              <span className="text-[10px] font-mono tracking-widest uppercase text-red-400 font-semibold">
                SYNCNODE // {panel.toUpperCase()}
              </span>
            </div>

            <p className="text-[13px] text-white/80 font-medium mb-1">
              This panel encountered an unexpected state.
            </p>
            <p className="text-[11px] text-white/40 mb-4 leading-relaxed">
              The rest of SyncNode remains active. You can reload this panel or inspect the raw diagnostics.
            </p>

            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={this.handleReload}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] bg-white/10 hover:bg-white/15 text-white/90 border border-white/[0.07] transition-colors"
              >
                <RefreshCw size={11} />
                Reload panel
              </button>

              {this.props.onRefreshRun && (
                <button
                  onClick={this.props.onRefreshRun}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] bg-white/5 hover:bg-white/10 text-white/70 border border-white/[0.06] transition-colors"
                >
                  Refresh run
                </button>
              )}

              <button
                onClick={() => this.setState((s) => ({ showRaw: !s.showRaw }))}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[11px] text-white/40 hover:text-white/70 hover:bg-white/5 ml-auto transition-colors"
              >
                <Bug size={11} />
                <span>{this.state.showRaw ? 'Hide error' : 'View raw error'}</span>
                {this.state.showRaw ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              </button>
            </div>

            {this.state.showRaw && (
              <div className="mt-3 p-3 rounded bg-black/80 border border-white/[0.06] font-mono text-[10px] text-red-300/80 overflow-x-auto max-h-48 select-text">
                <p className="font-semibold text-red-400 mb-1">{errorMsg}</p>
                {stack && <pre className="whitespace-pre-wrap text-white/30 text-[9px] leading-tight">{stack}</pre>}
              </div>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Specialized Boundaries for specific zones
export function ApplicationErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Application">{children}</ErrorBoundary>
}

export function RunErrorBoundary({ children, onRefresh }: { children: ReactNode; onRefresh?: () => void }) {
  return <ErrorBoundary panelName="Run View" onRefreshRun={onRefresh}>{children}</ErrorBoundary>
}

export function TimelineErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Timeline">{children}</ErrorBoundary>
}

export function AgentPanelErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Agent Intelligence">{children}</ErrorBoundary>
}

export function ArtifactPanelErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Artifacts">{children}</ErrorBoundary>
}

export function ApprovalPanelErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Approvals">{children}</ErrorBoundary>
}

export function KnowledgePanelErrorBoundary({ children }: { children: ReactNode }) {
  return <ErrorBoundary panelName="Knowledge Base">{children}</ErrorBoundary>
}
