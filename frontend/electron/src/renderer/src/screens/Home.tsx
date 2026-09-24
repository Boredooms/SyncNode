import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight, ChevronDown, Cpu, Check, Loader2,
  Upload, FileText, FileSpreadsheet, Presentation,
  File, X, CheckCircle2, AlertCircle, Database,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { createRun, listRuns, listModels, getActiveModel, setActiveModel } from '../lib/api/client'
import type { ModelProfile } from '../lib/api/types'
import { useRunStore } from '../stores/runStore'
import { useHealthStore } from '../stores/healthStore'
import { StatusDot } from '../components/ui/primitives'
import { formatRelativeTime } from '../lib/utils'
import { toast } from 'sonner'

// ── Accepted MIME types ───────────────────────────────────────────────────────
const ACCEPTED_EXTENSIONS = [
  '.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.md',
  '.csv', '.json', '.py', '.ts', '.js', '.html',
]
const ACCEPTED_MIME = [
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/pdf',
  'text/plain', 'text/markdown', 'text/csv', 'text/html',
  'application/json',
]

// ── Per-file state ────────────────────────────────────────────────────────────
type FileStatus = 'queued' | 'uploading' | 'parsing' | 'ingesting' | 'done' | 'error'

interface UploadedFile {
  id: string
  file: File
  status: FileStatus
  error?: string
  charCount?: number
  chunks?: number
  sha256?: string
  docId?: string
  preview?: string  // first 200 chars of parsed text
}

// ── File icon by extension ────────────────────────────────────────────────────
function FileIcon({ name, size = 14 }: { name: string; size?: number }) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['docx', 'doc'].includes(ext))        return <FileText size={size} className="text-blue-400/70" />
  if (['xlsx', 'xls', 'csv'].includes(ext)) return <FileSpreadsheet size={size} className="text-emerald-400/70" />
  if (['pptx', 'ppt'].includes(ext))        return <Presentation size={size} className="text-orange-400/70" />
  if (ext === 'pdf')                         return <FileText size={size} className="text-red-400/70" />
  return <File size={size} className="text-white/40" />
}

// ── Status pill ───────────────────────────────────────────────────────────────
function StatusPill({ status, error }: { status: FileStatus; error?: string }) {
  if (status === 'done') return (
    <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400/80">
      <CheckCircle2 size={10} /> ingested
    </span>
  )
  if (status === 'error') return (
    <span className="flex items-center gap-1 text-[10px] font-mono text-red-400/70" title={error}>
      <AlertCircle size={10} /> {error?.slice(0, 40) ?? 'error'}
    </span>
  )
  const labels: Record<FileStatus, string> = {
    queued: 'queued', uploading: 'uploading…', parsing: 'parsing…',
    ingesting: 'ingesting…', done: 'done', error: 'error',
  }
  return (
    <span className="flex items-center gap-1 text-[10px] font-mono text-white/35">
      <Loader2 size={9} className="animate-spin" /> {labels[status]}
    </span>
  )
}

// ── Quick tasks ───────────────────────────────────────────────────────────────
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

// ── API helpers (raw fetch — not in client.ts yet) ────────────────────────────
const BASE = 'http://127.0.0.1:8000'

async function apiParseFile(file: File): Promise<{ text: string; char_count: number; sha256: string }> {
  const form = new FormData()
  form.append('file', file)
  form.append('ingest', 'false')
  const r = await fetch(`${BASE}/api/v1/documents/upload`, { method: 'POST', body: form })
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail ?? `HTTP ${r.status}`) }
  return r.json()
}

async function apiIngestFile(file: File): Promise<{ doc_id: string; chunks: number; sha256: string; already_existed: boolean }> {
  const form = new FormData()
  form.append('file', file)
  form.append('ingest', 'true')
  const r = await fetch(`${BASE}/api/v1/documents/upload`, { method: 'POST', body: form })
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail ?? `HTTP ${r.status}`) }
  return r.json()
}

// ── Main component ────────────────────────────────────────────────────────────
export function Home() {
  const [goal, setGoal] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { runList, setRunList, initRun, setActiveRunId } = useRunStore()
  const health = useHealthStore()

  // ── Model switcher ────────────────────────────────────────────────────
  const [models, setModels] = useState<ModelProfile[]>([])
  const [activeModel, setActiveModelState] = useState<ModelProfile | null>(null)
  const [modelDropOpen, setModelDropOpen] = useState(false)
  const [modelSwitching, setModelSwitching] = useState(false)
  const [modelSwitchMsg, setModelSwitchMsg] = useState<string | null>(null)
  const dropRef = useRef<HTMLDivElement>(null)

  // ── Document upload state ─────────────────────────────────────────────
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [uploadPanelOpen, setUploadPanelOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listRuns().then(setRunList).catch(() => {})
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
      await setActiveModel(modelId)
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

  // ── Document processing ───────────────────────────────────────────────
  const processFile = useCallback(async (uf: UploadedFile) => {
    const update = (patch: Partial<UploadedFile>) =>
      setUploadedFiles(prev => prev.map(f => f.id === uf.id ? { ...f, ...patch } : f))

    try {
      // Step 1 — upload + parse (get text back)
      update({ status: 'uploading' })
      const parsed = await apiParseFile(uf.file)
      update({
        status: 'ingesting',
        charCount: parsed.char_count,
        sha256: parsed.sha256,
        preview: parsed.text?.slice(0, 220),
      })

      // Step 2 — ingest into ChromaDB RAG
      const ingested = await apiIngestFile(uf.file)
      update({
        status: 'done',
        docId: ingested.doc_id,
        chunks: ingested.chunks,
      })

      const existed = ingested.already_existed ? ' (already in knowledge base)' : ''
      toast.success(`${uf.file.name} ingested — ${ingested.chunks} chunks${existed}`)
    } catch (e: any) {
      update({ status: 'error', error: e.message ?? 'Failed' })
      toast.error(`Failed to ingest ${uf.file.name}: ${e.message}`)
    }
  }, [])

  const addFiles = useCallback((files: File[]) => {
    const valid = files.filter(f => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase()
      return ACCEPTED_EXTENSIONS.includes(ext) || ACCEPTED_MIME.includes(f.type)
    })
    if (valid.length < files.length) {
      toast.warning(`${files.length - valid.length} file(s) skipped — unsupported type`)
    }
    if (!valid.length) return

    const newEntries: UploadedFile[] = valid.map(f => ({
      id: `${f.name}-${f.size}-${Date.now()}`,
      file: f,
      status: 'queued',
    }))

    setUploadedFiles(prev => [...newEntries, ...prev])
    setUploadPanelOpen(true)

    // Process sequentially to avoid overloading the backend
    ;(async () => {
      for (const uf of newEntries) {
        await processFile(uf)
      }
    })()
  }, [processFile])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    addFiles(files)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    addFiles(files)
    e.target.value = ''
  }

  const removeFile = (id: string) =>
    setUploadedFiles(prev => prev.filter(f => f.id !== id))

  const doneCount   = uploadedFiles.filter(f => f.status === 'done').length
  const activeCount = uploadedFiles.filter(f => ['uploading','parsing','ingesting'].includes(f.status)).length

  const isReady = (s?: { status: string } | null) =>
    s?.status === 'healthy' || s?.status === 'ok'

  const checks = [
    { label: 'Local AI',   ready: isReady(health.model)    },
    { label: 'Knowledge',  ready: isReady(health.rag)       },
    { label: 'Desktop',    ready: isReady(health.computer)  },
    { label: 'Runtime',    ready: isReady(health.overall)   },
  ]

  return (
    <div
      className="flex-1 overflow-y-auto flex flex-col"
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragOver(false) }}
      onDrop={handleDrop}
    >
      {/* ── Global drag overlay ── */}
      <AnimatePresence>
        {dragOver && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
          >
            <div className="absolute inset-0 bg-white/[0.03] border-2 border-dashed border-white/20 rounded-2xl m-4" />
            <div className="relative flex flex-col items-center gap-3">
              <Upload size={32} className="text-white/50" />
              <p className="text-[14px] text-white/60 font-light tracking-wide">Drop to add to knowledge base</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS.join(',')}
        className="hidden"
        onChange={handleFileInput}
      />

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

            {/* Model switcher */}
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
                {modelSwitching
                  ? <Loader2 size={11} className="animate-spin text-white/40" />
                  : <Cpu size={11} className="text-white/40" />}
                <span className="font-mono max-w-[160px] truncate">
                  {activeModel?.model_id ?? 'Loading…'}
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
                    className="absolute right-0 top-full mt-1.5 z-50 min-w-[240px] rounded-xl border border-white/[0.09] bg-[#111111] shadow-[0_8px_32px_rgba(0,0,0,0.6)] overflow-hidden"
                  >
                    <div className="px-3 py-2 border-b border-white/[0.05]">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-white/25 font-semibold">Local Models</p>
                    </div>
                    <div className="max-h-[280px] overflow-y-auto">
                      {models.filter(m => !m.model_id.endsWith(':cloud')).map(m => (
                        <button
                          key={m.model_id}
                          onClick={() => handleSwitchModel(m.model_id)}
                          className={cn('w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-white/[0.05]', m.is_active && 'bg-white/[0.04]')}
                        >
                          <div className="flex-1 min-w-0">
                            <p className={cn('text-[12px] font-mono truncate', m.is_active ? 'text-white/85' : 'text-white/50')}>
                              {m.model_id}
                            </p>
                            <p className="text-[10px] text-white/25 mt-0.5">
                              {[m.capabilities.parameter_size, m.capabilities.quantization, m.capabilities.vision && 'vision', m.capabilities.context_window && `${(m.capabilities.context_window / 1024).toFixed(0)}k ctx`].filter(Boolean).join(' · ')}
                            </p>
                          </div>
                          {m.is_active && <Check size={12} className="text-emerald-400 flex-shrink-0" />}
                        </button>
                      ))}
                    </div>
                    <div className="px-3 py-2 border-t border-white/[0.05]">
                      <p className="text-[9px] text-white/20">Changes apply to new runs · ollama pull to add models</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {modelSwitchMsg && (
                  <motion.p
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
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
              error ? 'border-red-500/30 ring-1 ring-red-500/15'
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
                  {submitting
                    ? <span className="w-2 h-2 rounded-full bg-black/40 animate-pulse" />
                    : <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>}
                  Run
                </button>
              </div>
            </div>
            {error && <p className="mt-2 text-[11px] text-red-400/70 px-1">{error}</p>}
          </div>

          {/* ── Document upload panel ── */}
          <div className="space-y-2">
            {/* Header row */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setUploadPanelOpen(v => !v)}
                className="flex items-center gap-2 text-[9px] uppercase tracking-[0.12em] text-white/22 font-semibold hover:text-white/45 transition-colors"
              >
                <Database size={10} className="text-white/25" />
                Knowledge base
                {uploadedFiles.length > 0 && (
                  <span className={cn(
                    'text-[9px] font-mono px-1.5 py-px rounded-full',
                    activeCount > 0
                      ? 'bg-amber-500/15 text-amber-400/70'
                      : 'bg-emerald-500/12 text-emerald-400/60'
                  )}>
                    {activeCount > 0 ? `${activeCount} processing` : `${doneCount} indexed`}
                  </span>
                )}
                <ChevronDown size={9} className={cn('transition-transform', uploadPanelOpen && 'rotate-180')} />
              </button>

              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 text-[10px] text-white/30 hover:text-white/60 transition-colors"
              >
                <Upload size={10} />
                Add files
              </button>
            </div>

            <AnimatePresence initial={false}>
              {uploadPanelOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  {/* Drop zone */}
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                      'flex flex-col items-center justify-center gap-2 py-5 rounded-xl border border-dashed cursor-pointer transition-all duration-200',
                      dragOver
                        ? 'border-white/30 bg-white/[0.05]'
                        : 'border-white/[0.07] bg-white/[0.01] hover:border-white/[0.14] hover:bg-white/[0.03]'
                    )}
                  >
                    <Upload size={18} className="text-white/25" />
                    <div className="text-center">
                      <p className="text-[12px] text-white/40">Drop files or click to upload</p>
                      <p className="text-[10px] text-white/20 mt-0.5">
                        .docx .xlsx .pptx .pdf .txt .md .csv .json and more
                      </p>
                    </div>
                  </div>

                  {/* File list */}
                  {uploadedFiles.length > 0 && (
                    <div className="mt-2 space-y-1.5 max-h-[220px] overflow-y-auto">
                      {uploadedFiles.map(uf => (
                        <motion.div
                          key={uf.id}
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className={cn(
                            'flex items-start gap-2.5 px-3 py-2.5 rounded-xl border transition-colors',
                            uf.status === 'done'  && 'border-emerald-500/15 bg-emerald-500/5',
                            uf.status === 'error' && 'border-red-500/15 bg-red-500/5',
                            !['done','error'].includes(uf.status) && 'border-white/[0.06] bg-white/[0.02]',
                          )}
                        >
                          <div className="mt-0.5 flex-shrink-0">
                            <FileIcon name={uf.file.name} size={14} />
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-[12px] text-white/70 truncate font-mono">{uf.file.name}</p>
                              <StatusPill status={uf.status} error={uf.error} />
                            </div>

                            {/* Size + chunks */}
                            <p className="text-[10px] text-white/25 mt-0.5">
                              {(uf.file.size / 1024).toFixed(1)} KB
                              {uf.charCount != null && ` · ${uf.charCount.toLocaleString()} chars`}
                              {uf.chunks != null && ` · ${uf.chunks} chunks`}
                            </p>

                            {/* Text preview */}
                            {uf.preview && uf.status === 'done' && (
                              <p className="text-[10px] text-white/30 mt-1 leading-relaxed line-clamp-2 italic">
                                "{uf.preview}…"
                              </p>
                            )}
                          </div>

                          <button
                            onClick={() => removeFile(uf.id)}
                            className="flex-shrink-0 mt-0.5 p-0.5 rounded text-white/20 hover:text-white/55 transition-colors"
                          >
                            <X size={11} />
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {uploadedFiles.length === 0 && (
                    <p className="text-center text-[10px] text-white/18 mt-2">
                      Files added here are indexed into the local knowledge base and available to all workflows.
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
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
                <span className={cn('w-1.5 h-1.5 rounded-full', ready ? 'bg-emerald-400' : 'bg-white/15')} />
                <span className="text-[11px] text-white/35">{label}</span>
              </div>
            ))}
          </div>

          {/* ── Recent runs ── */}
          {runList.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <p className="text-[9px] uppercase tracking-[0.12em] text-white/22 font-semibold">Recent runs</p>
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
