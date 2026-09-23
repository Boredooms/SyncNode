import { useEffect } from 'react'
import { Command } from 'cmdk'
import { useNavigate } from 'react-router-dom'
import {
  Home, Play, BookOpen, Settings, Search, Plus,
  Layers, Terminal, X
} from 'lucide-react'
import { useUIStore } from '../../stores/uiStore'
import { useRunStore } from '../../stores/runStore'
import { cn } from '../../lib/utils'

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore()
  const navigate = useNavigate()
  const { runList } = useRunStore()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(!commandPaletteOpen)
      }
      if (e.key === 'Escape') setCommandPaletteOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [commandPaletteOpen])

  if (!commandPaletteOpen) return null

  const go = (path: string) => {
    navigate(path)
    setCommandPaletteOpen(false)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24"
      onClick={() => setCommandPaletteOpen(false)}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className={cn(
          'relative w-full max-w-lg mx-4',
          'bg-[#111] border border-white/[0.07] rounded-xl shadow-2xl overflow-hidden'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.05]">
            <Search size={14} className="text-white/30" />
            <Command.Input
              placeholder="Type a command or search…"
              className={cn(
                'flex-1 bg-transparent text-[13px] text-white/80 placeholder:text-white/25',
                'outline-none border-none'
              )}
              autoFocus
            />
            <button onClick={() => setCommandPaletteOpen(false)}>
              <X size={13} className="text-white/25 hover:text-white/50" />
            </button>
          </div>

          <Command.List className="max-h-80 overflow-y-auto py-1.5">
            <Command.Empty className="px-4 py-6 text-center text-[12px] text-white/30">
              No results
            </Command.Empty>

            <Command.Group heading="Navigation" className="[&>[cmdk-group-heading]]:px-3 [&>[cmdk-group-heading]]:py-1.5 [&>[cmdk-group-heading]]:text-[10px] [&>[cmdk-group-heading]]:uppercase [&>[cmdk-group-heading]]:tracking-widest [&>[cmdk-group-heading]]:text-white/25">
              {[
                { icon: Home, label: 'Go to Home', path: '/' },
                { icon: Play, label: 'Go to Runs', path: '/runs' },
                { icon: BookOpen, label: 'Go to Knowledge', path: '/knowledge' },
                { icon: Layers, label: 'Go to Learning', path: '/learning' },
                { icon: Settings, label: 'Go to Settings', path: '/settings' },
              ].map(({ icon: Icon, label, path }) => (
                <Command.Item
                  key={path}
                  value={label}
                  onSelect={() => go(path)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 cursor-pointer text-[12px] text-white/60',
                    'hover:bg-white/6 hover:text-white/85',
                    '[&[data-selected=true]]:bg-white/8 [&[data-selected=true]]:text-white/85'
                  )}
                >
                  <Icon size={13} className="text-white/35" />
                  {label}
                </Command.Item>
              ))}
            </Command.Group>

            {runList.length > 0 && (
              <Command.Group heading="Recent Runs" className="[&>[cmdk-group-heading]]:px-3 [&>[cmdk-group-heading]]:py-1.5 [&>[cmdk-group-heading]]:text-[10px] [&>[cmdk-group-heading]]:uppercase [&>[cmdk-group-heading]]:tracking-widest [&>[cmdk-group-heading]]:text-white/25">
                {runList.slice(0, 5).map((run) => (
                  <Command.Item
                    key={run.run_id}
                    value={run.goal}
                    onSelect={() => go(`/runs/${run.run_id}`)}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 cursor-pointer text-[12px] text-white/60',
                      'hover:bg-white/6 hover:text-white/85',
                      '[&[data-selected=true]]:bg-white/8 [&[data-selected=true]]:text-white/85'
                    )}
                  >
                    <Play size={13} className="text-white/25" />
                    <span className="truncate">{run.goal}</span>
                    <span className="ml-auto text-[10px] text-white/25">{run.status}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            <Command.Group heading="Actions" className="[&>[cmdk-group-heading]]:px-3 [&>[cmdk-group-heading]]:py-1.5 [&>[cmdk-group-heading]]:text-[10px] [&>[cmdk-group-heading]]:uppercase [&>[cmdk-group-heading]]:tracking-widest [&>[cmdk-group-heading]]:text-white/25">
              <Command.Item
                value="New Run Create Task"
                onSelect={() => go('/')}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 cursor-pointer text-[12px] text-white/60',
                  'hover:bg-white/6 hover:text-white/85',
                  '[&[data-selected=true]]:bg-white/8 [&[data-selected=true]]:text-white/85'
                )}
              >
                <Plus size={13} className="text-white/35" />
                New Run
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  )
}
