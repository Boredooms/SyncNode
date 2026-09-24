import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, ChevronDown, Cpu, Check, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { createRun, listRuns, listModels, getActiveModel, setActiveModel } from '../lib/api/client'
import type { ModelProfile } from '../lib/api/types'
import { useRunStore } from '../stores/runStore'
import { useHealthStore } from '../stores/healthStore'
import { StatusDot } from '../components/ui/primitives'
import { formatRelativeTime } from '../lib/utils'

const EXAMPLE_TASKS = [
  'Create a quarterly report and save it as report.docx',
  'Analyze the spreadsheet data and create an Excel summary',
  'Draft a professional email with the key findings attached',
  'Build a PowerPoint presentation from the report content',
]

const GREETING = (() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning.'
  if (h < 18) return 'Good afternoon.'
  return 'Good evening.'
})()

export function Home() {
  const [goal, setGoal] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { runList, setRunList, initRun, setActiveRunId } = useRunStore()
  const health = useHealthStore()

  // ── Model switcher state ─────────────────────────────────────────────
  const [models, setModels] = useState<ModelProfile[]>([])
  const [activeModel, setActiveModelState] = useState<ModelProfile | null>(null)
  const [modelDropOpen, setModelDropOpen] = useState(false)
  const [modelSwitching, setModelSwitching] = useState(false)
  const [modelSwitchMsg, setModelSwitchMsg] = useState<string | null>(null)
  const dropRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRuns().then(setRunList).catch(() => {})
    // Load available models
    listModels().then(setModels).catch(() => {})
    getActiveModel().then(setActiveModelState).catch(() => {})
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) {
        setModelDropOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSwitchModel = async (modelId: string) => {
    if (modelId === activeModel?.model_id) { setModelDropOpen(false); return }
    setModelSwitching(true)
    setModelSwitchMsg(null)
    try {
      const res = await setActiveModel(modelId)
      setModelSwitchMsg(`Switched to ${modelId}`)
      const updated = models.map(m => ({ ...m, is_active: m.model_id === modelId }))
      setModels(updated)
      setActiveModelState(updated.find(m => m.model_id === modelId) ?? null)
      setTimeout(() => setModelSwitchMsg(null), 3000)
    } catch (e: any) {
      setModelSwitchMsg(`Error: ${e.message}`)
      setTimeout(() => setModelSwitchMsg(null), 4000)
    } finally {
      setModelSwitching(false)
      setModelDropOpen(false)
    }
  }

  const handleSubmit = async (taskGoal: string) => {
    const g = taskGoal.trim()
    if (!g || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const run = await createRun({ goal: g })
      initRun(run.run_id, run)
      setActiveRunId(run.run_id)
      setRunList([run, ...runList])
      navigate(`/runs/${run.run_id}`)
    } catch (e: any) {
      setError(e.message ?? 'Failed to create run')
    } finally {
      setSubmitting(false)
    }
  }

  const isReady = (s?: { status: string } | null) =>
    s?.status === 'healthy' || s?.status === 'ok'

  const checks = [
    { label: 'Local AI',   ready: isReady(health.model)    },
    { label: 'Knowledge',  ready: isReady(health.rag)       },
    { label: 'Desktop',    ready: isReady(health.computer)  },
    { label: 'Runtime',    ready: isReady(health.overall)   },
  ]

  return (
    /* Full-height flex column: pushes content to vertical center but lets it
       scroll naturally if the window is very short. */
    <div className="flex-1 overflow-y-auto flex flex-col">
      <div className="flex-1 flex items-center justify-center px-6 py-10">

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-[620px] space-y-7"
        >

          {/* ── Greeting + model switcher ── */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-[24px] font-light text-white/80 leading-tight">{GREETING}</h1>
              <p className="text-[13px] text-white/35 mt-1">What should I work on?</p>
            </div>

            {/* Model switcher dropdown */}
            <div className="relative" ref={dropRef}>
              <button
                onClick={() => setModelDropOpen(v => !v)}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[11px] transition-all duration-150',
                  'border-white/[0.08] bg-white/[0.03] text-white/45',
                  'hover:bg-white/[0.07] hover:text-white/70 hover:border-white/[0.14]',
                  modelDropOpen && 'bg-white/[0.07] border-white/[0.14] text-white/70'
                )}
                title="Switch active model"
              >
                {modelSwitching ? (
                  <Loader2 size={11} className="animate-spin text-white/40" />
                ) : (
                  <Cpu size={11} className="text-white/40" />
                )}
                <span className="font-mono max-w-[160px] truncate">
                  {activeModel?.model_id ?? activeModel?.display_name ?? 'Loading…'}
                </span>
                <ChevronDown size={10} className={cn('transition-transform duration-150', modelDropOpen && 'rotate-180')} />
              </button>

              <AnimatePresence>
                {modelDropOpen && models.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.97 }}
                    transition={{ duration: 0.12 }}
                    className={cn(
                      'absolute right-0 top-full mt-1.5 z-50 min-w-[240px]',
                      'rounded-xl border border-white/[0.09] bg-[#111111]',
                      'shadow-[0_8px_32px_rgba(0,0,0,0.6)] overflow-hidden',
                    )}
                  >
                    <div className="px-3 py-2 border-b border-white/[0.05]">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-white/25 font-semibold">
                        Local Models
                      </p>
                    </div>
                    <div className="max-h-[280px] overflow-y-auto">
                      {models.map(m => (
                        <button
                          key={m.model_id}
                          onClick={() => handleSwitchModel(m.model_id)}
                          className={cn(
                            'w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition-colors',
                            'hover:bg-white/[0.05]',
                            m.is_active && 'bg-white/[0.04]',
                          )}
                        >
                          <div className="flex-1 min-w-0">
                            <p className={cn(
                              'text-[12px] font-mono truncate',
                              m.is_active ? 'text-white/85' : 'text-white/50',
                            )}>
                              {m.model_id}
                            </p>
                            <p className="text-[10px] text-white/25 mt-0.5">
                              {[
                                m.capabilities.parameter_size,
                                m.capabilities.quantization,
                                m.capabilities.vision && 'vision',
                                m.capabilities.context_window && `${(m.capabilities.context_window / 1024).toFixed(0)}k ctx`,
                              ].filter(Boolean).join(' · ')}
                            </p>
                          </div>
                          {m.is_active && <Check size={12} className="text-emerald-400 flex-shrink-0" />}
                        </button>
                      ))}
                    </div>
                    <div className="px-3 py-2 border-t border-white/[0.05]">
                      <p className="text-[9px] text-white/20">
                        Changes apply to new runs · ollama pull to add models
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Switch confirmation toast */}
              <AnimatePresence>
                {modelSwitchMsg && (
                  <motion.p
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="absolute right-0 top-full mt-1 text-[10px] text-emerald-400/80 whitespace-nowrap"
                  >
                    {modelSwitchMsg}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* ── Composer ── */}
          <div>
            <div className={cn(
              'rounded-2xl border bg-[#141414] transition-all duration-200',
              error
                ? 'border-red-500/30 ring-1 ring-red-500/15'
                : 'border-white/[0.07] focus-within:border-white/[0.07] focus-within:bg-[#181818]',
              'shadow-[0_4px_32px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.04)]'
            )}>
              <textarea
                value={goal}
                onChange={(e) => { setGoal(e.target.value); setError(null) }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit(goal)
                }}
                placeholder="Describe what you want to automate…"
                rows={3}
                className="w-full bg-transparent px-5 pt-4 pb-1 text-[13px] text-white/85 placeholder:text-white/22 resize-none outline-none rounded-t-2xl font-sans leading-relaxed"
              />
              <div className="flex items-center justify-between px-4 py-2.5 border-t border-white/[0.04]">
                <span className="text-[11px] text-white/20 font-mono select-none">⌘↵ to run</span>
                <button
                  onClick={() => handleSubmit(goal)}
                  disabled={!goal.trim() || submitting}
                  className={cn(
                    'flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[12px] font-semibold transition-all duration-200',
                    !goal.trim() || submitting
                      ? 'bg-white/5 text-white/20 cursor-not-allowed'
                      : 'bg-white text-black hover:bg-white/90 shadow-[0_2px_8px_rgba(255,255,255,0.12)]'
                  )}
                >
                  {submitting ? (
                    <span className="w-2 h-2 rounded-full bg-black/40 animate-pulse" />
                  ) : (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                  )}
                  Run
                </button>
              </div>
            </div>
            {error && <p className="mt-2 text-[11px] text-red-400/70 px-1">{error}</p>}
          </div>

          {/* ── Quick-start chips ── */}
          <div>
            <p className="text-[9px] uppercase tracking-[0.12em] text-white/22 mb-2.5 font-semibold">
              Quick start
            </p>
            <div className="grid grid-cols-2 gap-2">
              {EXAMPLE_TASKS.map((task) => (
                <button
                  key={task}
                  onClick={() => setGoal(task)}
                  className={cn(
                    'text-left px-3.5 py-2.5 rounded-xl border border-white/[0.05] bg-white/[0.015]',
                    'text-[11px] text-white/42 leading-snug',
                    'hover:text-white/70 hover:bg-white/[0.04] hover:border-white/[0.09]',
                    'transition-all duration-200'
                  )}
                >
                  {task}
                </button>
              ))}
            </div>
          </div>

          {/* ── System status bar ── */}
          <div className="flex items-center gap-5 px-0.5">
            {checks.map(({ label, ready }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className={cn(
                  'w-1.5 h-1.5 rounded-full',
                  ready ? 'bg-emerald-400' : 'bg-white/15'
                )} />
                <span className="text-[11px] text-white/35">{label}</span>
              </div>
            ))}
          </div>

          {/* ── Recent runs ── */}
          {runList.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <p className="text-[9px] uppercase tracking-[0.12em] text-white/22 font-semibold">
                  Recent runs
                </p>
                <button
                  onClick={() => navigate('/runs')}
                  className="text-[10px] text-white/25 hover:text-white/55 transition-colors"
                >
                  View all →
                </button>
              </div>

              <div className="rounded-xl border border-white/[0.05] bg-white/[0.01] overflow-hidden divide-y divide-white/[0.04]">
                {runList.slice(0, 5).map((run) => (
                  <button
                    key={run.run_id}
                    onClick={() => navigate(`/runs/${run.run_id}`)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-white/[0.04] transition-colors group"
                  >
                    <StatusDot status={run.status} />
                    <span className="flex-1 text-[12px] text-white/55 group-hover:text-white/80 truncate transition-colors leading-snug">
                      {run.goal}
                    </span>
                    <span className="text-[10px] text-white/22 whitespace-nowrap flex-shrink-0">
                      {run.created_at ? formatRelativeTime(run.created_at) : ''}
                    </span>
                    <ChevronRight size={11} className="text-white/15 group-hover:text-white/45 flex-shrink-0 transition-colors" />
                  </button>
                ))}
              </div>
            </div>
          )}

        </motion.div>
      </div>
    </div>
  )
}
