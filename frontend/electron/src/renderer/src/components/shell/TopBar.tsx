import { Minus, Square, X, Search, Command } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useUIStore } from '../../stores/uiStore'
import { useHealthStore } from '../../stores/healthStore'
import { useRunStore } from '../../stores/runStore'
import { StatusDot } from '../ui/primitives'

// Electron IPC bridge via preload
declare global {
  interface Window {
    api?: {
      window: {
        minimize: () => void
        maximize: () => void
        close: () => void
        isMaximized: () => Promise<boolean>
      }
    }
  }
}

export function TopBar() {
  const { setCommandPaletteOpen } = useUIStore()
  const health = useHealthStore((s) => s.overall)
  const { activeRunId, runs } = useRunStore()
  const activeRun = activeRunId ? runs[activeRunId]?.run : null

  const isHealthy = health?.status === 'healthy' || health?.status === 'ok'

  return (
    <header
      className={cn(
        'flex items-center justify-between h-11 px-3 border-b border-white/[0.05]',
        'bg-[#0d0d0d] flex-shrink-0 app-drag-region'
      )}
    >
      {/* Left — workspace identity */}
      <div className="flex items-center gap-3 app-no-drag">
        {activeRun && (
          <div className="flex items-center gap-2">
            <StatusDot status={activeRun.status} />
            <span className="text-[12px] text-white/60 truncate max-w-[200px]">
              {activeRun.goal}
            </span>
          </div>
        )}
        {!activeRun && (
          <span className="text-[12px] text-white/25">Local AI Workbench</span>
        )}
      </div>

      {/* Center — search trigger */}
      <button
        className={cn(
          'app-no-drag flex items-center gap-2 px-3 py-1.5 rounded',
          'bg-white/5 border border-white/[0.06] text-white/30',
          'hover:text-white/50 hover:bg-white/8 transition-colors',
          'text-[11px] min-w-[160px]'
        )}
        onClick={() => setCommandPaletteOpen(true)}
      >
        <Search size={11} />
        <span>Search commands…</span>
        <kbd className="ml-auto text-[9px] font-mono text-white/20 flex items-center gap-0.5">
          <Command size={9} />K
        </kbd>
      </button>

      {/* Right — health + window controls */}
      <div className="flex items-center gap-3 app-no-drag">
        {/* Health indicator */}
        <div className="flex items-center gap-1.5">
          <span className={cn('w-1.5 h-1.5 rounded-full', isHealthy ? 'bg-green-400' : 'bg-amber-400')} />
          <span className="text-[10px] text-white/30">
            {isHealthy ? 'Online' : health ? 'Degraded' : 'Connecting'}
          </span>
        </div>

        {/* Window controls */}
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={() => window.api?.window.minimize()}
            className="w-5 h-5 rounded flex items-center justify-center text-white/25 hover:text-white/60 hover:bg-white/8 transition-colors"
          >
            <Minus size={10} />
          </button>
          <button
            onClick={() => window.api?.window.maximize()}
            className="w-5 h-5 rounded flex items-center justify-center text-white/25 hover:text-white/60 hover:bg-white/8 transition-colors"
          >
            <Square size={9} />
          </button>
          <button
            onClick={() => window.api?.window.close()}
            className="w-5 h-5 rounded flex items-center justify-center text-white/25 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <X size={10} />
          </button>
        </div>
      </div>
    </header>
  )
}
