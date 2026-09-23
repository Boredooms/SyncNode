import { useEffect, useState } from 'react'
import { Search, BookOpen, RotateCcw, FileText, Plus, X, Trash2, Save, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '../lib/utils'
import {
  listKnowledge, searchKnowledge, getKnowledgeDoc, reindexKnowledge,
  createKnowledge, updateKnowledge, deleteKnowledge,
} from '../lib/api/client'
import type { KnowledgeDoc } from '../lib/api/types'
import { Skeleton, EmptyState } from '../components/ui/primitives'

function slugify(title: string): string {
  const s = title.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return (s || 'note') + '.md'
}

type PanelMode = 'view' | 'compose' | 'edit'

export function Knowledge() {
  const [docs, setDocs]           = useState<KnowledgeDoc[]>([])
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState('')
  const [selected, setSelected]   = useState<KnowledgeDoc | null>(null)
  const [searching, setSearching] = useState(false)
  const [mode, setMode]           = useState<PanelMode>('view')

  // Shared compose / edit state
  const [editTitle, setEditTitle] = useState('')
  const [editBody, setEditBody]   = useState('')
  const [saving, setSaving]       = useState(false)

  const refresh = () => listKnowledge().then(setDocs).catch(() => {})

  useEffect(() => {
    listKnowledge()
      .then(setDocs)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // ── Handlers ────────────────────────────────────────────────────────────

  const handleSearch = async () => {
    if (!search.trim()) { listKnowledge().then(setDocs); return }
    setSearching(true)
    try {
      const results = await searchKnowledge(search)
      setDocs(results.map((r) => ({
        doc_id: r.doc_id, title: r.title, path: r.path,
        kind: 'reference', trust_tier: (r as any).trust, content: r.snippet,
      })))
    } catch {}
    finally { setSearching(false) }
  }

  const handleSelect = async (doc: KnowledgeDoc) => {
    setMode('view')
    setSelected(doc)
    try {
      const full = await getKnowledgeDoc(doc.doc_id)
      setSelected(full)
    } catch {}
  }

  const handleReindex = async (docId: string) => {
    try {
      await reindexKnowledge(docId)
      toast.success('Document reindexed')
    } catch (e: any) {
      toast.error(`Reindex failed: ${e?.message ?? 'unknown'}`)
    }
  }

  const handleDelete = async (doc: KnowledgeDoc) => {
    try {
      await deleteKnowledge(doc.doc_id)
      toast.success(`Deleted "${doc.title}"`)
      if (selected?.doc_id === doc.doc_id) { setSelected(null); setMode('view') }
      await refresh()
    } catch (e: any) {
      toast.error(`Delete failed: ${e?.message ?? 'unknown'}`)
    }
  }

  const startCompose = () => {
    setMode('compose')
    setSelected(null)
    setEditTitle('')
    setEditBody('')
  }

  const startEdit = (doc: KnowledgeDoc) => {
    setMode('edit')
    setEditTitle(doc.title ?? '')
    // Strip front-matter for editing convenience
    const body = (doc.content ?? doc.body ?? '').replace(/^---[\s\S]*?---\n*/m, '').trimStart()
    setEditBody(body)
  }

  const handleSave = async () => {
    if (!editTitle.trim() || !editBody.trim()) {
      toast.error('Title and content are required')
      return
    }
    setSaving(true)
    const md = `---\ntitle: ${editTitle.trim()}\ntrust: reference\n---\n\n${editBody.trim()}\n`
    try {
      if (mode === 'compose') {
        const path = slugify(editTitle)
        await createKnowledge(path, md)
        toast.success(`Added "${editTitle.trim()}"`)
      } else if (mode === 'edit' && selected) {
        await updateKnowledge(selected.doc_id, selected.path ?? slugify(editTitle), md)
        toast.success(`Updated "${editTitle.trim()}"`)
      }
      setMode('view')
      setEditTitle('')
      setEditBody('')
      await refresh()
    } catch (e: any) {
      toast.error(`Save failed: ${e?.message ?? 'unknown error'}`)
    } finally {
      setSaving(false)
    }
  }

  const cancelEdit = () => {
    setMode('view')
    setEditTitle('')
    setEditBody('')
  }

  const TRUST_COLORS: Record<string, string> = {
    authoritative: 'text-green-400',
    reference:     'text-blue-400',
    workflow:      'text-purple-400',
    untrusted:     'text-red-400/60',
  }

  return (
    <div className="flex-1 flex min-h-0 overflow-hidden">

      {/* ── Sidebar ── */}
      <div className="w-64 flex-shrink-0 border-r border-white/[0.05] flex flex-col">
        <div className="p-3 border-b border-white/[0.05]">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-[13px] font-medium text-white/70">Knowledge</h2>
            <button
              onClick={startCompose}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono bg-white/8 hover:bg-white/14 text-white/70 border border-white/[0.07] transition-colors"
              title="Add knowledge document"
            >
              <Plus size={11} /> New
            </button>
          </div>
          <div className="flex gap-1">
            <div className="flex-1 flex items-center gap-2 px-2 py-1.5 rounded border border-white/[0.07] bg-white/3">
              <Search size={11} className="text-white/30 flex-shrink-0" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search…"
                className="flex-1 bg-transparent text-[11px] text-white/70 placeholder:text-white/25 outline-none selectable"
              />
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-3 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 rounded" />)}
            </div>
          ) : docs.length === 0 ? (
            <EmptyState icon={<BookOpen size={18} />} title="No documents" />
          ) : (
            docs.map((doc) => (
              <div
                key={doc.doc_id}
                className={cn(
                  'group w-full flex items-start gap-2 px-3 py-2.5 border-b border-white/[0.04] transition-colors cursor-pointer',
                  selected?.doc_id === doc.doc_id
                    ? 'bg-white/8 text-white/85'
                    : 'text-white/50 hover:bg-white/4 hover:text-white/70'
                )}
                onClick={() => handleSelect(doc)}
              >
                <FileText size={11} className="mt-0.5 flex-shrink-0 text-white/25" />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] truncate">{doc.title}</p>
                  {doc.trust_tier && (
                    <p className={cn('text-[9px] uppercase tracking-wide mt-0.5', TRUST_COLORS[doc.trust_tier] ?? 'text-white/25')}>
                      {doc.trust_tier}
                    </p>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(doc) }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded text-white/25 hover:text-red-400 hover:bg-red-500/10 transition-all flex-shrink-0"
                  title="Delete document"
                >
                  <Trash2 size={11} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Main panel ── */}
      <div className="flex-1 overflow-y-auto">

        {/* ── Compose / Edit form ── */}
        {(mode === 'compose' || mode === 'edit') && (
          <div className="p-6 max-w-3xl mx-auto">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-[15px] font-medium text-white/80">
                {mode === 'compose' ? 'New Knowledge Document' : `Editing: ${selected?.title ?? editTitle}`}
              </h3>
              <button
                onClick={cancelEdit}
                className="p-1.5 rounded text-white/30 hover:text-white/70 hover:bg-white/5 transition-colors"
                title="Cancel"
              >
                <X size={14} />
              </button>
            </div>

            <label className="block text-[10px] uppercase tracking-widest text-white/30 font-mono mb-1">Title</label>
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="e.g. Company Brand Voice Guidelines"
              className="w-full mb-4 px-3 py-2 rounded-lg border border-white/[0.07] bg-white/3 text-[13px] text-white/85 outline-none focus:border-white/[0.08] transition-colors"
            />

            <label className="block text-[10px] uppercase tracking-widest text-white/30 font-mono mb-1">Content (Markdown)</label>
            <textarea
              value={editBody}
              onChange={(e) => setEditBody(e.target.value)}
              placeholder="Write the knowledge SyncNode should use during runs. Plain text or Markdown."
              rows={18}
              className="w-full px-3 py-2 rounded-lg border border-white/[0.07] bg-white/3 text-[12px] text-white/80 font-mono leading-relaxed outline-none focus:border-white/[0.08] resize-y transition-colors"
            />

            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] bg-white/90 text-black font-medium hover:bg-white disabled:opacity-40 transition-colors"
              >
                <Save size={13} />
                {saving ? 'Saving…' : mode === 'compose' ? 'Save to Knowledge Base' : 'Save Changes'}
              </button>
              <span className="text-[10px] text-white/25 font-mono">
                {mode === 'compose'
                  ? `Saved as ${editTitle.trim() ? slugify(editTitle) : 'note.md'} · indexed for RAG`
                  : `Updating ${selected?.path ?? '—'}`}
              </span>
            </div>
          </div>
        )}

        {/* ── Empty state ── */}
        {mode === 'view' && !selected && (
          <div className="flex items-center justify-center h-full">
            <EmptyState
              icon={<BookOpen size={22} />}
              title="Select a document"
              description="Choose a document from the list to view its content, or create a new one."
            />
          </div>
        )}

        {/* ── Document view ── */}
        {mode === 'view' && selected && (
          <div className="p-6 max-w-3xl mx-auto">
            {/* Header */}
            <div className="flex items-start justify-between mb-5 gap-3">
              <div className="flex-1 min-w-0">
                <h3 className="text-[16px] font-medium text-white/85 leading-snug">{selected.title}</h3>
                {selected.path && (
                  <p className="text-[11px] text-white/28 font-mono mt-0.5">{selected.path}</p>
                )}
                {selected.trust_tier && (
                  <span className={cn('text-[10px] uppercase tracking-wide mt-1 inline-block', TRUST_COLORS[selected.trust_tier] ?? 'text-white/25')}>
                    {selected.trust_tier}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => startEdit(selected)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] border border-white/[0.07] text-white/40 hover:text-white/70 hover:bg-white/5 transition-all"
                  title="Edit document"
                >
                  <Pencil size={11} />
                  Edit
                </button>
                <button
                  onClick={() => handleReindex(selected.doc_id)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] border border-white/[0.07] text-white/40 hover:text-white/70 hover:bg-white/5 transition-all"
                  title="Re-index for RAG"
                >
                  <RotateCcw size={11} />
                  Reindex
                </button>
              </div>
            </div>

            {/* Content — strip front-matter before display */}
            {selected.content || selected.body ? (
              <div className="text-[12px] text-white/62 leading-relaxed whitespace-pre-wrap selectable font-mono bg-white/[0.02] rounded-xl p-4 border border-white/[0.05]">
                {(selected.content ?? selected.body ?? '').replace(/^---[\s\S]*?---\n*/m, '').trimStart()}
              </div>
            ) : (
              <p className="text-[12px] text-white/28 italic">No content available.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
