import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Search, ChevronRight, ChevronDown, Copy, Check, Filter, Terminal } from 'lucide-react'
import type { SSEEvent } from '../../lib/api/types'
import { formatTimestamp } from '../../lib/utils'

interface LiveEventInspectorProps {
  runId: string
  events: SSEEvent[]
  isOpen: boolean
  onClose: () => void
}

export function LiveEventInspector({ runId, events, isOpen, onClose }: LiveEventInspectorProps) {
  const [filter, setFilter] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  if (!isOpen) return null

  const uniqueTypes = Array.from(new Set(events.map((e) => e.event_type)))

  const filteredEvents = events.filter((e) => {
    const matchesSearch =
      filter === '' ||
      e.event_type.toLowerCase().includes(filter.toLowerCase()) ||
      JSON.stringify(e).toLowerCase().includes(filter.toLowerCase())
    const matchesType = selectedType === 'all' || e.event_type === selectedType
    return matchesSearch && matchesType
  })

  const copyEventPayload = (event: SSEEvent, index: number) => {
    navigator.clipboard.writeText(JSON.stringify(event, null, 2))
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 1500)
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs">
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 28, stiffness: 280 }}
        className="w-full max-w-2xl h-full bg-[#0d0d0d] border-l border-white/10 flex flex-col shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.05] bg-[#111]">
          <div className="flex items-center gap-2">
            <Terminal size={14} className="text-white/60" />
            <span className="text-[13px] font-semibold text-white/90">Live SSE Event Inspector</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-white/8 text-white/50 font-mono">
              {events.length} events
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-white/40 hover:text-white/80 hover:bg-white/5 transition-colors"
          >
            <X size={15} />
          </button>
        </div>

        {/* Filters */}
        <div className="p-3 border-b border-white/[0.05] bg-[#0f0f0f] space-y-2">
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-black/40 border border-white/[0.06]">
            <Search size={12} className="text-white/30 flex-shrink-0" />
            <input
              type="text"
              placeholder="Search event type, step, tool, or payload contents…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="flex-1 bg-transparent text-[11px] text-white/80 placeholder:text-white/25 outline-none font-mono"
            />
            {filter && (
              <button onClick={() => setFilter('')} className="text-white/30 hover:text-white/60 text-[10px]">
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
            <button
              onClick={() => setSelectedType('all')}
              className={`px-2 py-0.5 rounded text-[10px] whitespace-nowrap transition-colors ${
                selectedType === 'all' ? 'bg-white/15 text-white/90 font-medium' : 'text-white/40 hover:bg-white/5'
              }`}
            >
              All ({events.length})
            </button>
            {uniqueTypes.map((type) => {
              const count = events.filter((e) => e.event_type === type).length
              return (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`px-2 py-0.5 rounded text-[10px] whitespace-nowrap transition-colors font-mono ${
                    selectedType === type ? 'bg-white/15 text-white/90 font-medium' : 'text-white/40 hover:bg-white/5'
                  }`}
                >
                  {type} ({count})
                </button>
              )
            })}
          </div>
        </div>

        {/* Events List */}
        <div className="flex-1 overflow-y-auto divide-y divide-white/5 font-mono text-[11px]">
          {filteredEvents.length === 0 ? (
            <div className="p-8 text-center text-white/30">
              <p className="text-[12px]">No events match the current filter.</p>
            </div>
          ) : (
            filteredEvents.map((event, idx) => {
              const isExpanded = expandedIndex === idx
              const agent = (event.agent as string) || (event.agent_id as string)
              const step = (event.step_key as string)
              const tool = (event.tool_key as string) || (event.tool as string)

              return (
                <div key={`${event.event_type}-${event.ts}-${idx}`} className="hover:bg-white/2 transition-colors">
                  <div
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="flex items-center gap-2.5 px-4 py-2 cursor-pointer select-none"
                  >
                    <span className="text-white/30">
                      {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </span>
                    <span className="text-white/25 text-[10px] w-14 flex-shrink-0">
                      {formatTimestamp(event.ts)}
                    </span>
                    <span className="text-white/80 font-semibold flex-1 truncate">
                      {event.event_type}
                    </span>
                    {agent && (
                      <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[9px] border border-blue-500/20">
                        {agent}
                      </span>
                    )}
                    {step && (
                      <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 text-[9px] border border-purple-500/20 truncate max-w-[120px]">
                        {step}
                      </span>
                    )}
                    {tool && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 text-[9px] border border-amber-500/20 truncate max-w-[120px]">
                        {tool}
                      </span>
                    )}
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-black/50 border-t border-white/5"
                      >
                        <div className="p-3 pl-8">
                          <div className="flex items-center justify-between mb-1.5 text-white/30 text-[10px]">
                            <span>RAW EVENT PAYLOAD</span>
                            <button
                              onClick={() => copyEventPayload(event, idx)}
                              className="flex items-center gap-1 hover:text-white/70 transition-colors"
                            >
                              {copiedIndex === idx ? (
                                <>
                                  <Check size={10} className="text-green-400" />
                                  <span className="text-green-400">Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy size={10} />
                                  <span>Copy JSON</span>
                                </>
                              )}
                            </button>
                          </div>
                          <pre className="p-3 rounded bg-black/80 border border-white/[0.06] text-white/70 text-[10px] overflow-x-auto leading-relaxed max-h-72 select-text">
                            {JSON.stringify(event, null, 2)}
                          </pre>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )
            })
          )}
        </div>
      </motion.div>
    </div>
  )
}
