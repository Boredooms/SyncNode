import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Play, Search, Plus, ChevronRight, Hash, ArrowRight } from 'lucide-react'
import { cn, formatRelativeTime } from '../lib/utils'
import { listRuns, saveLocalRun, getRun } from '../lib/api/client'
import type { Run } from '../lib/api/types'
import { useRunStore } from '../stores/runStore'
import { StatusDot, StatusBadge, EmptyState } from '../components/ui/primitives'

type FilterStatus = 'all' | Run['status']

const SEED_RUN_ID = '242d6142-1470-4ce2-99fa-73f075f076e6'

export function RunsList() {
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [manualRunId, setManualRunId] = useState('')
  const [manualLoading, setManualLoading] = useState(false)
  const [manualError, setManualError] = useState('')

  const navigate = useNavigate()
  const runList = useRunStore((s) => s.runList)
  const setRunList = useRunStore((s) => s.setRunList)

  useEffect(() => {
    // Load local run catalog without making any 405 requests
    listRuns().then((runs) => {
      if (runs.length === 0) {
        getRun(SEED_RUN_ID)
          .then((r) => setRunList([r]))
          .catch(() => setRunList([]))
      } else {
        setRunList(runs)
      }
    })
  }, [])

  const handleOpenManualRun = async (e: React.FormEvent) => {
    e.preventDefault()
    const id = manualRunId.trim()
    if (!id) return

    setManualLoading(true)
    setManualError('')
    try {
      const run = await getRun(id)
      saveLocalRun(run)
      const updated = await listRuns()
      setRunList(updated)
      navigate(`/runs/${id}`)
    } catch (err: any) {
      setManualError(`Run not found: ${err.message || 'Invalid Run ID'}`)
    } finally {
      setManualLoading(false)
    }
  }

  const filtered = runList.filter((r) => {
    const matchSearch = search === '' || r.goal.toLowerCase().includes(search.toLowerCase()) || r.run_id.includes(search)
    const matchStatus = filterStatus === 'all' || r.status === filterStatus
    return matchSearch && matchStatus
  })

  const statuses: FilterStatus[] = ['all', 'running', 'waiting_approval', 'completed', 'failed', 'cancelled']

  return (
    <div className="flex-1 overflow-y-auto bg-[#0a0a0a]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/[0.05] px-8 py-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-[18px] font-semibold text-white/90">Workflows & Runs</h2>
            <p className="text-[11px] text-white/40 mt-0.5">
              Local workflow execution catalog.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] bg-white text-black font-semibold hover:bg-white/90 transition-all shadow-xs"
            >
              <Plus size={13} />
              New Run
            </button>
          </div>
        </div>

        {/* Direct Run Opener Bar */}
        <form onSubmit={handleOpenManualRun} className="mb-4 flex gap-2">
          <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/[0.07] bg-white/2 focus-within:border-white/[0.07] transition-colors">
            <Hash size={13} className="text-white/30 flex-shrink-0" />
            <input
              value={manualRunId}
              onChange={(e) => {
                setManualRunId(e.target.value)
                setManualError('')
              }}
              placeholder="Paste Run ID to open directly (e.g. 242d6142-1470-4ce2-99fa-73f075f076e6)…"
              className="flex-1 bg-transparent text-[11px] text-white/80 placeholder:text-white/25 outline-none font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={manualLoading || !manualRunId.trim()}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-medium bg-white/10 hover:bg-white/15 text-white/80 border border-white/[0.07] transition-colors disabled:opacity-30"
          >
            <span>Open</span>
            <ArrowRight size={11} />
          </button>
        </form>
        {manualError && <p className="text-[10px] text-red-400 font-mono mb-2">{manualError}</p>}

        {/* Search + Filter */}
        <div className="flex items-center gap-3">
          <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/[0.06] bg-white/2">
            <Search size={12} className="text-white/30 flex-shrink-0" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search runs by goal or run ID…"
              className="flex-1 bg-transparent text-[12px] text-white/70 placeholder:text-white/25 outline-none"
            />
          </div>

          <div className="flex items-center gap-1">
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={cn(
                  'px-2.5 py-1 rounded text-[10px] uppercase font-mono tracking-wide transition-colors',
                  filterStatus === s
                    ? 'bg-white/12 text-white/90 font-medium'
                    : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                )}
              >
                {s === 'all' ? 'All' : s.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Run List */}
      <div className="px-8 py-5 max-w-5xl">
        {filtered.length === 0 ? (
          <EmptyState
            icon={<Play size={24} />}
            title="No runs in local catalog"
            description={
              search
                ? 'No runs match your search.'
                : 'Execute a goal from the home screen or open a run using its Run ID.'
            }
          />
        ) : (
          <div className="space-y-2">
            {filtered.map((run, i) => (
              <motion.button
                key={run.run_id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
                onClick={() => navigate(`/runs/${run.run_id}`)}
                className={cn(
                  'w-full flex items-center gap-4 px-4 py-3.5 rounded-xl border border-white/[0.05] bg-[#0e0e0e]',
                  'text-left hover:bg-white/3 hover:border-white/[0.09] transition-all group shadow-xs'
                )}
              >
                <StatusDot status={run.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-white/85 font-medium truncate group-hover:text-white transition-colors">
                    {run.goal}
                  </p>
                  <p className="text-[10px] text-white/30 mt-0.5 font-mono">
                    {run.run_id}
                  </p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <StatusBadge status={run.status} />
                  <span className="text-[10px] text-white/30 font-mono">
                    {run.created_at ? formatRelativeTime(run.created_at) : ''}
                  </span>
                  <ChevronRight size={13} className="text-white/20 group-hover:text-white/60 transition-colors" />
                </div>
              </motion.button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
