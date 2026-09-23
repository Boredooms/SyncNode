import { useNavigate, useLocation, Link } from 'react-router-dom'
import {
  Home, Play, FolderOpen, BookOpen, Settings, ChevronLeft, ChevronRight,
  Terminal, Layers, Activity, Cpu, Network, MessageSquare
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useUIStore } from '../../stores/uiStore'
import { useRunStore } from '../../stores/runStore'
import { StatusDot } from '../ui/primitives'

const NAV = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: Play, label: 'Runs', path: '/runs' },
  { icon: MessageSquare, label: 'Chat', path: '/chat' },
  { icon: FolderOpen, label: 'Files', path: '/files' },
  { icon: BookOpen, label: 'Knowledge', path: '/knowledge' },
  { icon: Layers, label: 'Learning', path: '/learning' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar() {
  const { sidebarCollapsed, setSidebarCollapsed } = useUIStore()
  const location = useLocation()
  const navigate = useNavigate()
  const { runList, activeRunId } = useRunStore()
  const recentRuns = runList.slice(0, 5)

  return (
    <aside
      className={cn(
        'flex flex-col h-full border-r border-white/[0.05] bg-[#0d0d0d] transition-all duration-200 flex-shrink-0',
        sidebarCollapsed ? 'w-12' : 'w-56'
      )}
    >
      {/* Brand / toggle */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-white/[0.05] min-h-[44px] app-drag-region">
        {!sidebarCollapsed && (
          <span className="text-[13px] font-semibold tracking-[0.12em] text-white/80 font-mono app-no-drag">
            SYNCNODE
          </span>
        )}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={cn(
            'app-no-drag flex items-center justify-center w-6 h-6 rounded text-white/30',
            'hover:text-white/70 hover:bg-white/8 transition-colors',
            sidebarCollapsed && 'mx-auto'
          )}
        >
          {sidebarCollapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2">
        <div className="space-y-0.5 px-1.5">
          {NAV.map(({ icon: Icon, label, path }) => {
            const active = location.pathname === path || (path !== '/' && location.pathname.startsWith(path))
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  'flex items-center gap-2.5 px-2 py-1.5 rounded text-[12px] transition-colors duration-100',
                  active
                    ? 'bg-white/10 text-white/90'
                    : 'text-white/45 hover:text-white/75 hover:bg-white/5',
                  sidebarCollapsed && 'justify-center px-0'
                )}
                title={sidebarCollapsed ? label : undefined}
              >
                <Icon size={14} className="flex-shrink-0" />
                {!sidebarCollapsed && label}
              </Link>
            )
          })}
        </div>

        {/* Recent Runs */}
        {!sidebarCollapsed && recentRuns.length > 0 && (
          <div className="mt-4">
            <p className="px-3 pb-1 text-[10px] uppercase tracking-widest text-white/25 font-semibold">
              Recent
            </p>
            <div className="space-y-0.5 px-1.5">
              {recentRuns.map((run) => (
                <button
                  key={run.run_id}
                  onClick={() => navigate(`/runs/${run.run_id}`)}
                  className={cn(
                    'w-full flex items-center gap-2 px-2 py-1.5 rounded text-left transition-colors',
                    activeRunId === run.run_id
                      ? 'bg-white/10 text-white/80'
                      : 'text-white/40 hover:text-white/65 hover:bg-white/5'
                  )}
                >
                  <StatusDot status={run.status} className="flex-shrink-0" />
                  <span className="text-[11px] truncate">{run.goal}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Runtime status footer */}
      {!sidebarCollapsed && (
        <div className="px-3 py-2 border-t border-white/[0.05]">
          <div className="flex items-center gap-2">
            <Cpu size={10} className="text-white/25" />
            <span className="text-[10px] text-white/30">Ollama / Local</span>
          </div>
        </div>
      )}
    </aside>
  )
}
