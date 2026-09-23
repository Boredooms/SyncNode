import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronRight, Cpu, Shield, Database, Globe } from 'lucide-react'
import { cn } from '../lib/utils'
import { createRun, listRuns } from '../lib/api/client'
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

  useEffect(() => {
    listRuns().then(setRunList).catch(() => {})
  }, [])

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

          {/* ── Greeting ── */}
          <div>
            <h1 className="text-[24px] font-light text-white/80 leading-tight">{GREETING}</h1>
            <p className="text-[13px] text-white/35 mt-1">What should I work on?</p>
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
