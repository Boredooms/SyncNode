import { useRef, useState } from 'react'
import { Settings as SettingsIcon, Cpu, Eye, Keyboard, Shield, Info, Monitor, Sun } from 'lucide-react'
import { cn } from '../lib/utils'
import { useUIStore } from '../stores/uiStore'
import { useHealthStore } from '../stores/healthStore'

const SECTIONS = [
  { id: 'general',     label: 'General',     icon: SettingsIcon },
  { id: 'runtime',     label: 'Runtime',     icon: Cpu          },
  { id: 'appearance',  label: 'Appearance',  icon: Eye          },
  { id: 'shortcuts',   label: 'Shortcuts',   icon: Keyboard     },
  { id: 'security',    label: 'Security',    icon: Shield       },
  { id: 'about',       label: 'About',       icon: Info         },
]

export function Settings() {
  const { density, setDensity } = useUIStore()
  const health = useHealthStore()
  const [active, setActive] = useState('general')

  // Ref map for each section heading so we can scroll to it
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({})

  const scrollTo = (id: string) => {
    setActive(id)
    sectionRefs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const modelStatus = health.overall?.status ?? 'unknown'
  const isOnline = modelStatus === 'ok' || modelStatus === 'healthy'

  return (
    <div className="flex-1 flex min-h-0 overflow-hidden">

      {/* ── Section nav ── */}
      <div className="w-48 flex-shrink-0 border-r border-white/[0.05] pt-4">
        {SECTIONS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => scrollTo(id)}
            className={cn(
              'w-full flex items-center gap-2.5 px-4 py-2 text-[12px] text-left transition-colors',
              active === id
                ? 'text-white/80 bg-white/6'
                : 'text-white/38 hover:text-white/65 hover:bg-white/4'
            )}
          >
            <Icon size={13} className={active === id ? 'text-white/60' : 'text-white/25'} />
            {label}
          </button>
        ))}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-lg space-y-10">

          {/* ── General ── */}
          <section ref={(el) => { sectionRefs.current['general'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">General</h3>
            <div className="space-y-px rounded-xl border border-white/[0.06] overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Information Density</p>
                  <p className="text-[11px] text-white/30 mt-0.5">Compact fits more; comfort gives more breathing room</p>
                </div>
                <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1">
                  {(['compact', 'comfort'] as const).map((d) => (
                    <button
                      key={d}
                      onClick={() => setDensity(d)}
                      className={cn(
                        'px-3 py-1 rounded-md text-[11px] capitalize transition-all',
                        density === d ? 'bg-white/14 text-white/80' : 'text-white/35 hover:text-white/60'
                      )}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* ── Runtime ── */}
          <section ref={(el) => { sectionRefs.current['runtime'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">Runtime</h3>
            <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
              {[
                { label: 'Backend URL',    value: 'http://127.0.0.1:8000',                mono: true  },
                { label: 'Model',          value: health.model?.model_id ?? '—',           mono: true  },
                { label: 'Provider',       value: 'Ollama / Local',                        mono: true  },
                { label: 'Model Latency',  value: health.model?.latency_ms != null ? `${Math.round(health.model.latency_ms)} ms` : '—', mono: true },
                { label: 'RAG',            value: health.rag?.status ?? '—',               mono: false },
                { label: 'Desktop Control',value: health.computer?.status ?? '—',          mono: false },
                { label: 'Database',       value: health.database?.status ?? '—',          mono: false },
                { label: 'Status',         value: modelStatus,                             mono: false },
              ].map(({ label, value, mono }) => (
                <div key={label} className="flex items-center justify-between px-4 py-3">
                  <span className="text-[12px] text-white/45">{label}</span>
                  <span className={cn(
                    'text-[12px]',
                    mono ? 'font-mono text-white/70' : '',
                    !mono && (value === 'ok' || value === 'healthy') ? 'text-emerald-400' :
                    !mono && (value === 'error' || value === 'unavailable') ? 'text-red-400/70' :
                    !mono ? 'text-white/50' : ''
                  )}>
                    {value}
                  </span>
                </div>
              ))}
            </div>

            {/* Live status indicator */}
            <div className="flex items-center gap-2 mt-3 px-1">
              <span className={cn(
                'w-1.5 h-1.5 rounded-full',
                isOnline ? 'bg-emerald-400' : 'bg-amber-400'
              )} />
              <span className="text-[11px] text-white/30">
                {isOnline ? 'Backend connected · local inference active' : 'Backend offline or connecting…'}
              </span>
            </div>
          </section>

          {/* ── Appearance ── */}
          <section ref={(el) => { sectionRefs.current['appearance'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">Appearance</h3>
            <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
              {/* Theme — always dark for now */}
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Theme</p>
                  <p className="text-[11px] text-white/30 mt-0.5">UI colour scheme</p>
                </div>
                <div className="flex items-center gap-1.5">
                  <Monitor size={13} className="text-white/35" />
                  <span className="text-[12px] text-white/55 font-mono">Dark</span>
                  <span className="text-[10px] text-white/20 ml-1">(system default)</span>
                </div>
              </div>

              {/* Font size */}
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">UI Font</p>
                  <p className="text-[11px] text-white/30 mt-0.5">Interface + monospace typefaces</p>
                </div>
                <div className="flex flex-col items-end gap-0.5">
                  <span className="text-[12px] text-white/55 font-mono">Inter</span>
                  <span className="text-[10px] text-white/25 font-mono">JetBrains Mono (code)</span>
                </div>
              </div>

              {/* Animations */}
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Animations</p>
                  <p className="text-[11px] text-white/30 mt-0.5">Framer Motion transitions</p>
                </div>
                <span className="text-[12px] text-white/55">Enabled</span>
              </div>
            </div>
          </section>

          {/* ── Shortcuts ── */}
          <section ref={(el) => { sectionRefs.current['shortcuts'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">Keyboard Shortcuts</h3>
            <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
              {[
                { action: 'Command Palette',  keys: ['Ctrl', 'K'] },
                { action: 'Go to Home',        keys: ['Ctrl', '1'] },
                { action: 'Go to Runs',        keys: ['Ctrl', '2'] },
                { action: 'Go to Knowledge',   keys: ['Ctrl', '3'] },
                { action: 'Go to Files',       keys: ['Ctrl', '4'] },
                { action: 'Toggle Sidebar',    keys: ['Ctrl', '\\'] },
                { action: 'New Run',           keys: ['Ctrl', 'N'] },
              ].map(({ action, keys }) => (
                <div key={action} className="flex items-center justify-between px-4 py-2.5">
                  <span className="text-[12px] text-white/55">{action}</span>
                  <div className="flex items-center gap-1">
                    {keys.map((k, i) => (
                      <span key={k} className="flex items-center gap-1">
                        <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-white/8 text-white/45 font-mono border border-white/[0.07]">{k}</kbd>
                        {i < keys.length - 1 && <span className="text-[10px] text-white/20">+</span>}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ── Security ── */}
          <section ref={(el) => { sectionRefs.current['security'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">Security</h3>
            <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Execution Mode</p>
                  <p className="text-[11px] text-white/30 mt-0.5">All inference is local — no data sent to external servers</p>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Sovereign
                </span>
              </div>

              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Human Approval Gate</p>
                  <p className="text-[11px] text-white/30 mt-0.5">External actions require manual authorisation before execution</p>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Enabled
                </span>
              </div>

              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Audit Trail</p>
                  <p className="text-[11px] text-white/30 mt-0.5">Cryptographic hash chain stored for every run event</p>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Active
                </span>
              </div>

              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-[12px] text-white/70">Desktop Control Sandbox</p>
                  <p className="text-[11px] text-white/30 mt-0.5">UIA automation isolated to user session</p>
                </div>
                <span className={cn(
                  'text-[11px] font-mono px-2 py-0.5 rounded-full border',
                  health.computer?.status === 'ok'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-white/5 text-white/35 border-white/[0.07]'
                )}>
                  {health.computer?.status === 'ok' ? 'Ready' : 'Unavailable'}
                </span>
              </div>
            </div>
          </section>

          {/* ── About ── */}
          <section ref={(el) => { sectionRefs.current['about'] = el }}>
            <h3 className="text-[13px] font-semibold text-white/55 mb-4 uppercase tracking-wider">About</h3>
            <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
              {[
                { label: 'Product',   value: 'SyncNode',          mono: true  },
                { label: 'Version',   value: '1.0.0',             mono: true  },
                { label: 'Runtime',   value: 'Electron + React',  mono: true  },
                { label: 'Backend',   value: 'FastAPI + Python',  mono: true  },
                { label: 'Inference', value: 'Ollama (local)',     mono: true  },
                { label: 'License',   value: 'Proprietary',       mono: false },
              ].map(({ label, value, mono }) => (
                <div key={label} className="flex items-center justify-between px-4 py-3">
                  <span className="text-[12px] text-white/38">{label}</span>
                  <span className={cn('text-[12px] text-white/65', mono && 'font-mono')}>{value}</span>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-white/20 mt-4 italic px-1">Think locally. Act intelligently.</p>
          </section>

        </div>
      </div>
    </div>
  )
}
