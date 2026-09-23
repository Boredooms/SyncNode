import { useEffect, useState } from 'react'
import { Layers, Check, X, ChevronDown, ChevronUp, Wrench } from 'lucide-react'
import { cn } from '../lib/utils'
import { getLearningCandidates, reviewLearningCandidate } from '../lib/api/client'
import type { LearningCandidate } from '../lib/api/types'
import { EmptyState, Skeleton } from '../components/ui/primitives'

export function Learning() {
  const [candidates, setCandidates] = useState<LearningCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [reviewing, setReviewing] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  useEffect(() => {
    getLearningCandidates()
      .then(setCandidates)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleReview = async (id: string, decision: 'approve' | 'reject') => {
    setReviewing(id)
    try {
      await reviewLearningCandidate(id, { decision })
      setCandidates((prev) => prev.filter((c) => c.candidate_id !== id))
    } catch {}
    finally { setReviewing(null) }
  }

  const toggle = (id: string) =>
    setExpanded((p) => ({ ...p, [id]: !p[id] }))

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl">
        <h2 className="text-[16px] font-medium text-white/80 mb-1">Workflow Memory</h2>
        <p className="text-[12px] text-white/35 mb-6">
          SyncNode can learn from successful runs to accelerate future similar tasks.
          Review and approve memory candidates below.
        </p>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20 rounded" />)}
          </div>
        ) : candidates.length === 0 ? (
          <EmptyState
            icon={<Layers size={22} />}
            title="No learning candidates"
            description="Successful run trajectories will appear here for review before being committed to memory."
          />
        ) : (
          <div className="space-y-3">
            {candidates.map((c) => {
              const isOpen = expanded[c.candidate_id]
              const tools: string[] = (c as any).proposed_tool_sequence ?? []
              const rationale: string = (c as any).rationale ?? ''

              return (
                <div
                  key={c.candidate_id}
                  className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
                >
                  {/* Header row */}
                  <div className="flex items-start gap-3 p-4 pb-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] text-white/80 font-medium leading-snug">
                        {c.description ?? 'Workflow candidate'}
                      </p>
                      <div className="flex items-center gap-3 mt-1 flex-wrap">
                        {c.task_type && (
                          <span className="text-[10px] font-mono text-white/35 bg-white/5 px-1.5 py-0.5 rounded">
                            {c.task_type}
                          </span>
                        )}
                        {tools.length > 0 && (
                          <span className="text-[10px] text-white/30 flex items-center gap-1">
                            <Wrench size={9} /> {tools.length} tool{tools.length > 1 ? 's' : ''}
                          </span>
                        )}
                        {c.confidence !== undefined && (
                          <span className="text-[10px] text-white/30">
                            {(c.confidence * 100).toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                    {(rationale || tools.length > 0) && (
                      <button
                        onClick={() => toggle(c.candidate_id)}
                        className="text-white/25 hover:text-white/60 transition-colors flex-shrink-0 mt-0.5"
                      >
                        {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    )}
                  </div>

                  {/* Expanded detail */}
                  {isOpen && (
                    <div className="px-4 pb-3 space-y-2 border-t border-white/5 pt-3">
                      {rationale && (
                        <div>
                          <p className="text-[9px] uppercase tracking-widest text-white/25 mb-1 font-mono">Rationale</p>
                          <p className="text-[11px] text-white/55 leading-relaxed">{rationale}</p>
                        </div>
                      )}
                      {tools.length > 0 && (
                        <div>
                          <p className="text-[9px] uppercase tracking-widest text-white/25 mb-1.5 font-mono">Proposed Tool Sequence</p>
                          <div className="flex flex-wrap gap-1.5">
                            {tools.map((t, i) => (
                              <span key={i} className="text-[10px] font-mono text-amber-300/70 bg-amber-500/8 border border-amber-500/15 px-1.5 py-0.5 rounded">
                                {i + 1}. {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex gap-2 px-4 pb-4">
                    <button
                      onClick={() => handleReview(c.candidate_id, 'reject')}
                      disabled={reviewing === c.candidate_id}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px]',
                        'border border-white/[0.07] text-white/40 hover:text-white/65 hover:bg-white/5',
                        'transition-all disabled:opacity-40'
                      )}
                    >
                      <X size={11} /> Discard
                    </button>
                    <button
                      onClick={() => handleReview(c.candidate_id, 'approve')}
                      disabled={reviewing === c.candidate_id}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px]',
                        'bg-white/10 text-white/70 hover:bg-white/16 hover:text-white/90',
                        'transition-all disabled:opacity-40'
                      )}
                    >
                      <Check size={11} /> Accept
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
