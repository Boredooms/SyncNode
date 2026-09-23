/**
 * Files screen — shows all artifacts produced across every run in the local
 * workspace. Organized by run, grouped by type (word/excel/powerpoint/other).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText, FolderOpen, RefreshCw, Copy, CheckCheck,
  ChevronRight, FileSpreadsheet, Presentation, File, ExternalLink,
} from 'lucide-react'
import { cn, formatRelativeTime, formatFileSize } from '../lib/utils'
import { listRuns, getRunArtifacts } from '../lib/api/client'
import type { Run, Artifact } from '../lib/api/types'
import { StatusDot, EmptyState, Skeleton } from '../components/ui/primitives'
import { useRunStore } from '../stores/runStore'
import { toast } from 'sonner'

interface RunArtifactGroup {
  run: Run
  artifacts: Artifact[]
}

function ArtifactIcon({ type }: { type?: string | null }) {
  const t = (type ?? '').toLowerCase()
  if (t === 'word' || t === 'docx')
    return <FileText size={16} className="text-blue-400 flex-shrink-0" />
  if (t === 'excel' || t === 'xlsx')
    return <FileSpreadsheet size={16} className="text-emerald-400 flex-shrink-0" />
  if (t === 'powerpoint' || t === 'pptx')
    return <Presentation size={16} className="text-amber-400 flex-shrink-0" />
  return <File size={16} className="text-white/40 flex-shrink-0" />
}

export function Files() {
  const [groups, setGroups] = useState<RunArtifactGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [copiedPath, setCopiedPath] = useState<string | null>(null)
  const [openingPath, setOpeningPath] = useState<string | null>(null)
  const navigate = useNavigate()
  const { runList } = useRunStore()

  const load = async (quiet = false) => {
    if (!quiet) setLoading(true)
    else setRefreshing(true)
    try {
      const runs = await listRuns()
      const results: RunArtifactGroup[] = []
      await Promise.allSettled(
        runs.map(async (run) => {
          try {
            const arts = await getRunArtifacts(run.run_id)
            if (arts.length > 0) results.push({ run, artifacts: arts })
          } catch {}
        })
      )
      // Sort most-recent run first
      results.sort((a, b) => {
        const ta = Number(a.run.created_at ?? 0)
        const tb = Number(b.run.created_at ?? 0)
        return tb - ta
      })
      setGroups(results)
    } catch {}
    finally { setLoading(false); setRefreshing(false) }
  }

  useEffect(() => { load() }, [])

  // Also pick up runs created this session from the store
  useEffect(() => {
    if (runList.length > 0 && !loading) load(true)
  }, [runList.length])

  const copyPath = (path: string) => {
    navigator.clipboard.writeText(path)
    setCopiedPath(path)
    setTimeout(() => setCopiedPath(null), 1500)
  }

  const openFile = async (path: string) => {
    setOpeningPath(path)
    try {
      const result = await (window as any).api?.shell?.openPath(path)
      if (result && result !== '') {
        // openPath returns error string on failure, empty string on success
        toast.error(`Could not open file: ${result}`)
      }
    } catch (e: any) {
      toast.error(`Failed to open: ${e?.message ?? 'unknown error'}`)
    } finally {
      setTimeout(() => setOpeningPath(null), 1000)
    }
  }

  const totalArtifacts = groups.reduce((n, g) => n + g.artifacts.length, 0)

  return (
    <div className="flex-1 overflow-y-auto bg-[#0a0a0a]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/[0.05] px-8 py-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[18px] font-semibold text-white/90 flex items-center gap-2">
              <FolderOpen size={18} className="text-white/50" />
              Workspace Files
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">
              {loading ? 'Loading…' : `${totalArtifacts} artifact${totalArtifacts !== 1 ? 's' : ''} across ${groups.length} run${groups.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <button
            onClick={() => load(true)}
            disabled={refreshing || loading}
            className="p-2 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-colors disabled:opacity-30"
            title="Refresh"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="px-8 py-6 max-w-5xl space-y-6">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-6 w-48 rounded" />
                <Skeleton className="h-16 rounded-xl" />
                <Skeleton className="h-16 rounded-xl" />
              </div>
            ))}
          </div>
        ) : groups.length === 0 ? (
          <EmptyState
            icon={<FolderOpen size={24} />}
            title="No files yet"
            description="Artifacts produced by runs (documents, spreadsheets, presentations) will appear here."
            action={
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 rounded-lg text-[12px] bg-white/10 text-white/70 hover:bg-white/15 transition-colors"
              >
                Start a run →
              </button>
            }
          />
        ) : (
          groups.map(({ run, artifacts }) => (
            <div key={run.run_id}>
              {/* Run header */}
              <button
                onClick={() => navigate(`/runs/${run.run_id}`)}
                className="flex items-center gap-2.5 mb-3 group w-full text-left"
              >
                <StatusDot status={run.status} />
                <span className="text-[12px] text-white/65 group-hover:text-white/90 font-medium truncate flex-1 transition-colors leading-snug">
                  {run.goal}
                </span>
                <span className="text-[10px] text-white/25 font-mono whitespace-nowrap flex-shrink-0">
                  {run.created_at ? formatRelativeTime(run.created_at) : ''}
                </span>
                <ChevronRight size={12} className="text-white/20 group-hover:text-white/55 flex-shrink-0 transition-colors" />
              </button>

              {/* Artifact cards */}
              <div className="space-y-2 ml-4 pl-2 border-l border-white/[0.05]">
                {artifacts.map((art, i) => (
                  <div
                    key={art.artifact_id ?? i}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl border border-white/[0.06] bg-white/[0.015] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all group"
                  >
                    <ArtifactIcon type={art.type ?? art.kind} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-[12px] text-white/80 font-medium truncate">{art.name}</p>
                        {art.verified && (
                          <span className="text-[9px] font-mono text-emerald-400/80 bg-emerald-500/8 px-1 py-0.2 rounded border border-emerald-500/15 flex-shrink-0">
                            verified
                          </span>
                        )}
                      </div>
                      {art.path && (
                        <p className="text-[10px] text-white/25 font-mono truncate mt-0.5">{art.path}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1 text-[10px] text-white/25 font-mono">
                        {art.size_bytes != null && <span>{formatFileSize(art.size_bytes)}</span>}
                        {art.sha256 && <span>{art.sha256.slice(0, 12)}…</span>}
                      </div>
                    </div>
                    {art.path && (
                      <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1.5 flex-shrink-0 transition-all">
                        {/* Open in default app */}
                        <button
                          onClick={() => openFile(art.path!)}
                          className={cn(
                            'flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono transition-all',
                            openingPath === art.path
                              ? 'bg-emerald-500/15 text-emerald-400'
                              : 'bg-white/5 hover:bg-white/10 text-white/50'
                          )}
                          title="Open file in default application"
                        >
                          <ExternalLink size={11} />
                          <span>{openingPath === art.path ? 'Opening…' : 'Open'}</span>
                        </button>

                        {/* Copy path */}
                        <button
                          onClick={() => copyPath(art.path!)}
                          className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono bg-white/5 hover:bg-white/10 text-white/50 transition-all"
                          title="Copy file path"
                        >
                          {copiedPath === art.path ? (
                            <><CheckCheck size={11} className="text-emerald-400" /><span className="text-emerald-400">Copied</span></>
                          ) : (
                            <><Copy size={11} /><span>Copy</span></>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
