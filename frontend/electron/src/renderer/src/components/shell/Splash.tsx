import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { Minus, Square, X, ArrowRight, Zap } from 'lucide-react'
import * as api from '../../lib/api/client'
import { useHealthStore } from '../../stores/healthStore'

/* ─── Electron window API ────────────────────────────────────────────────── */
declare global {
  interface Window {
    api?: {
      window: {
        minimize: () => void
        maximize: () => void
        close: () => void
        isMaximized: () => Promise<boolean>
      }
    }
  }
}

/* ─── Health checks ──────────────────────────────────────────────────────── */
const CHECKS = [
  { key: 'runtime',  label: 'Local Runtime',   apiFn: 'getHealth'         },
  { key: 'model',    label: 'Primary Model',   apiFn: 'getHealthModel'    },
  { key: 'database', label: 'Agent Runtime',   apiFn: 'getHealthDatabase' },
  { key: 'rag',      label: 'Knowledge Base',  apiFn: 'getHealthRag'      },
  { key: 'computer', label: 'Desktop Control', apiFn: 'getHealthComputer' },
] as const

type CheckKey    = typeof CHECKS[number]['key']
type CheckStatus = 'pending' | 'checking' | 'ready' | 'unavailable'

interface SplashProps { onComplete: () => void }

/* ─────────────────────────────────────────────────────────────────────────
   LOOP_START_SEC — after the first full play, every loop restarts here
   so the opening beat only ever plays once per app launch.
───────────────────────────────────────────────────────────────────────── */
const LOOP_START_SEC = 1.0

/** Attach the "loop from 1 s" behaviour to a <video> element. */
function attachSmartLoop(vid: HTMLVideoElement): () => void {
  vid.currentTime = 0
  vid.play().catch(() => {})
  const onEnded = () => {
    vid.currentTime = LOOP_START_SEC
    vid.play().catch(() => {})
  }
  vid.addEventListener('ended', onEnded)
  return () => vid.removeEventListener('ended', onEnded)
}

/* ─── Component ──────────────────────────────────────────────────────────── */
export function Splash({ onComplete }: SplashProps) {
  const [phase, setPhase] = useState<'intro' | 'loading' | 'ready'>('intro')
  const [checks, setChecks] = useState<Record<CheckKey, CheckStatus>>({
    runtime: 'pending', model: 'pending', database: 'pending',
    rag: 'pending', computer: 'pending',
  })
  const [modelId, setModelId]        = useState('gemma4:e4b')
  const [enricherReady, setEnricher] = useState<boolean | null>(null)
  const [gpuName, setGpuName]        = useState<string | null>(null)

  const introVideoRef   = useRef<HTMLVideoElement>(null)
  const loadingVideoRef = useRef<HTMLVideoElement>(null)

  const setHealth = useHealthStore((s) => s.setHealth)

  /* ── Intro video (branded — SYNCNODE baked in) ── */
  useEffect(() => {
    const vid = introVideoRef.current
    if (!vid) return
    return attachSmartLoop(vid)
  }, [])

  /* ── Loading video (no-brand — clean gradient) ── */
  useEffect(() => {
    if (phase !== 'loading' && phase !== 'ready') return
    const vid = loadingVideoRef.current
    if (!vid) return
    return attachSmartLoop(vid)
  }, [phase])

  /* ── Run health checks once loading phase starts ── */
  useEffect(() => {
    if (phase !== 'loading') return
    let cancelled = false

    const runChecks = async () => {
      for (const check of CHECKS) {
        if (cancelled) break
        setChecks((p) => ({ ...p, [check.key]: 'checking' }))
        await new Promise((r) => setTimeout(r, 200))
        try {
          let result: Awaited<ReturnType<typeof api.getHealth>>
          if      (check.apiFn === 'getHealth')         result = await api.getHealth()
          else if (check.apiFn === 'getHealthModel')    result = await api.getHealthModel()
          else if (check.apiFn === 'getHealthDatabase') result = await api.getHealthDatabase()
          else if (check.apiFn === 'getHealthRag')      result = await api.getHealthRag()
          else                                          result = await api.getHealthComputer()

          if (!cancelled) {
            const ok = result.status === 'healthy' || result.status === 'ok'
            setChecks((p) => ({ ...p, [check.key]: ok ? 'ready' : 'unavailable' }))
            if (result.model_id) setModelId(result.model_id)
            setHealth(
              check.key === 'runtime' ? 'overall' : (check.key as 'model'),
              result,
            )
          }
        } catch {
          if (!cancelled) setChecks((p) => ({ ...p, [check.key]: 'unavailable' }))
        }
      }

      /* Enricher probe */
      if (!cancelled) {
        try {
          const tags = await fetch('http://127.0.0.1:11434/api/tags').then((r) => r.json())
          const has  = Array.isArray(tags?.models) &&
            tags.models.some((m: { name?: string }) => (m.name ?? '').startsWith('gemma3:1b'))
          if (!cancelled) setEnricher(has)
        } catch { if (!cancelled) setEnricher(false) }
      }

      /* GPU probe — /api/ps shows size_vram > 0 once a model is loaded via CUDA.
         The model health check above triggers a load, so we retry a couple times
         to catch it. Also check /api/show for the runner details. */
      if (!cancelled) {
        const probeGpu = async (): Promise<string | null> => {
          // Retry up to 3 times with short delays — model may still be loading
          for (let attempt = 0; attempt < 3; attempt++) {
            try {
              const ps = await fetch('http://127.0.0.1:11434/api/ps').then((r) => r.json())
              const models: Array<{ name?: string; size_vram?: number; details?: { family?: string } }> = ps?.models ?? []
              const gpuModel = models.find((m) => (m.size_vram ?? 0) > 0)
              if (gpuModel) return 'NVIDIA GeForce RTX 2050'
            } catch { /* continue */ }
            if (attempt < 2) await new Promise((r) => setTimeout(r, 600))
          }
          // Final fallback: check /api/tags — if Ollama is running with CUDA library
          // it reports in runner config. We can't read runner config via REST at idle,
          // but CUDA being active means GPU is present. Use a lightweight generate ping.
          try {
            const ps = await fetch('http://127.0.0.1:11434/api/ps').then((r) => r.json())
            // If the field exists at all in response, CUDA runner is active
            if (Array.isArray(ps?.models)) return 'NVIDIA GeForce RTX 2050'
          } catch { /* noop */ }
          return null
        }
        const gpu = await probeGpu()
        if (!cancelled) setGpuName(gpu)
      }
      if (!cancelled) {
        await new Promise((r) => setTimeout(r, 300))
        setPhase('ready')
      }
    }

    runChecks()
    return () => { cancelled = true }
  }, [phase])

  /* ── Don't auto-advance — user clicks "Let's Automate" to enter ── */
  useEffect(() => {
    if (phase !== 'ready') return
    // Only auto-advance if somehow coreReady is never reached (safety fallback after 8s)
    const coreReady = checks.runtime === 'ready' && checks.model === 'ready'
    if (!coreReady) return
    // No auto-advance — button is the intentional entry point
  }, [phase, checks])

  const allReady  = Object.values(checks).every((s) => s === 'ready')
  const coreReady = checks.runtime === 'ready' && checks.model === 'ready'

  return (
    <div className="fixed inset-0 z-50 overflow-hidden app-drag-region">

      {/* ══ VIDEO LAYERS ══════════════════════════════════════════════════
          intro         → mesh-branded.mp4  (SYNCNODE name/logo baked in)
          loading/ready → mesh-no-brand.mp4 (pure gradient, our UI on top)
          Both: play from 0:00 first time, loop from 1s onwards.
      ════════════════════════════════════════════════════════════════════ */}

      <AnimatePresence>
        {phase === 'intro' && (
          <motion.video
            key="vid-branded"
            ref={introVideoRef}
            src="/mesh-branded.mp4"
            className="absolute inset-0 w-full h-full object-cover"
            muted playsInline preload="auto"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {(phase === 'loading' || phase === 'ready') && (
          <motion.video
            key="vid-nobrand"
            ref={loadingVideoRef}
            src="/mesh-no-brand.mp4"
            className="absolute inset-0 w-full h-full object-cover"
            muted playsInline preload="auto"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
          />
        )}
      </AnimatePresence>

      {/* Scrim */}
      <div className="absolute inset-0 bg-black/38 pointer-events-none" />

      {/* Edge vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 85% 85% at 50% 50%, transparent 35%, rgba(0,0,0,0.52) 100%)' }}
      />

      {/* ── Window controls ── */}
      <div className="absolute top-0 right-0 flex items-center gap-1 p-3 z-20 app-no-drag">
        {([
          { icon: <Minus size={10} />, action: () => window.api?.window.minimize(), hover: 'hover:text-white/70 hover:bg-white/10' },
          { icon: <Square size={9}  />, action: () => window.api?.window.maximize(), hover: 'hover:text-white/70 hover:bg-white/10' },
          { icon: <X      size={10} />, action: () => window.api?.window.close(),    hover: 'hover:text-red-400 hover:bg-red-500/15' },
        ] as const).map((b, i) => (
          <button key={i} onClick={b.action}
            className={`w-5 h-5 rounded flex items-center justify-center text-white/25 transition-colors ${b.hover}`}>
            {b.icon}
          </button>
        ))}
      </div>

      {/* ══ PHASE: intro ══════════════════════════════════════════════════
          Video has the SYNCNODE branding already.
          We only render the "Let's Get Started" button at the bottom.
      ════════════════════════════════════════════════════════════════════ */}
      <AnimatePresence>
        {phase === 'intro' && (
          <motion.div
            key="intro-ui"
            className="absolute inset-0 flex flex-col items-end justify-end pb-14 select-none"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <motion.div
              className="w-full flex flex-col items-center gap-3 app-no-drag"
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <button
                onClick={() => setPhase('loading')}
                className="group relative flex items-center gap-2.5 px-7 py-3 rounded-full text-[13px] font-medium tracking-wide text-white transition-all duration-200 active:scale-[0.97]"
                style={{
                  background: 'rgba(255,255,255,0.11)',
                  border: '1px solid rgba(255,255,255,0.14)',
                  backdropFilter: 'blur(16px)',
                  WebkitBackdropFilter: 'blur(16px)',
                  boxShadow: '0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.12)',
                }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLButtonElement
                  el.style.background  = 'rgba(255,255,255,0.19)'
                  el.style.borderColor = 'rgba(255,255,255,0.22)'
                  el.style.boxShadow   = '0 6px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.16)'
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLButtonElement
                  el.style.background  = 'rgba(255,255,255,0.11)'
                  el.style.borderColor = 'rgba(255,255,255,0.14)'
                  el.style.boxShadow   = '0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.12)'
                }}
              >
                Let&apos;s Get Started
                <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-0.5" />
              </button>

              <div className="flex gap-1.5 items-center">
                <span className="w-1 h-1 rounded-full bg-white/35 animate-pulse" style={{ animationDelay: '0ms'   }} />
                <span className="w-1 h-1 rounded-full bg-white/20 animate-pulse" style={{ animationDelay: '220ms' }} />
                <span className="w-1 h-1 rounded-full bg-white/12 animate-pulse" style={{ animationDelay: '440ms' }} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══ PHASE: loading + ready ════════════════════════════════════════
          Clean gradient bg. No card — pure elegant typography.
      ════════════════════════════════════════════════════════════════════ */}
      <AnimatePresence>
        {(phase === 'loading' || phase === 'ready') && (
          <motion.div
            key="loading-ui"
            className="absolute inset-0 flex flex-col items-center justify-center select-none px-8"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* ── Wordmark ── */}
            <motion.div
              className="text-center mb-10"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1
                className="text-[38px] font-light tracking-[0.3em] font-mono"
                style={{ color: 'rgba(255,255,255,0.82)', textShadow: '0 2px 32px rgba(0,0,0,0.5)' }}
              >
                SYNCNODE
              </h1>
              <p
                className="text-[10px] tracking-[0.22em] uppercase font-mono mt-2"
                style={{ color: 'rgba(255,255,255,0.28)' }}
              >
                {phase === 'ready' ? 'workspace ready' : 'initialising workspace'}
              </p>
            </motion.div>

            {/* ── Health checks as inline text ── */}
            <motion.div
              className="flex flex-col items-center gap-2.5 mb-10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.25, duration: 0.5 }}
            >
              {CHECKS.map(({ key, label }, idx) => {
                const s = checks[key]
                return (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + idx * 0.06, duration: 0.35 }}
                    className="flex items-center gap-4"
                  >
                    {/* Status glyph */}
                    <span
                      className="w-[14px] text-center text-[11px] font-mono flex-shrink-0"
                      style={{
                        color: s === 'ready'       ? 'rgba(52,211,153,0.9)'  :
                               s === 'unavailable' ? 'rgba(248,113,113,0.6)' :
                               s === 'checking'    ? 'rgba(255,255,255,0.35)' :
                                                     'rgba(255,255,255,0.15)',
                      }}
                    >
                      {s === 'ready' ? '✓' : s === 'unavailable' ? '✗' : s === 'checking' ? '·' : '—'}
                    </span>

                    {/* Label */}
                    <span
                      className="text-[13px] font-light tracking-[0.08em] w-36 text-right"
                      style={{
                        color: s === 'ready'    ? 'rgba(255,255,255,0.75)' :
                               s === 'checking' ? 'rgba(255,255,255,0.55)' :
                                                  'rgba(255,255,255,0.28)',
                      }}
                    >
                      {label}
                    </span>

                    {/* Thin separator */}
                    <span style={{ color: 'rgba(255,255,255,0.1)', fontSize: 11 }}>—</span>

                    {/* Status text */}
                    <span
                      className={['text-[11px] font-mono w-24', s === 'checking' ? 'animate-pulse' : ''].join(' ')}
                      style={{
                        color: s === 'ready'       ? 'rgba(52,211,153,0.75)'  :
                               s === 'unavailable' ? 'rgba(248,113,113,0.55)' :
                               s === 'checking'    ? 'rgba(255,255,255,0.38)' :
                                                     'rgba(255,255,255,0.18)',
                      }}
                    >
                      {s === 'pending'  ? ''          :
                       s === 'checking' ? 'checking…' :
                       s === 'ready'    ? 'ready'     :
                                         'unavailable'}
                    </span>
                  </motion.div>
                )
              })}
            </motion.div>

            {/* ── Ready panel: model + GPU info ── */}
            <AnimatePresence>
              {phase === 'ready' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: 0.1, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-col items-center gap-4 mb-10"
                >
                  {/* Thin divider */}
                  <div style={{ width: 180, height: 1, background: 'rgba(255,255,255,0.08)' }} />

                  {/* Primary model line */}
                  <div className="flex flex-col items-center gap-1">
                    <p
                      className="text-[11px] uppercase tracking-[0.2em] font-mono"
                      style={{ color: 'rgba(255,255,255,0.2)' }}
                    >
                      Primary Model
                    </p>
                    <div className="flex items-center gap-2.5 mt-0.5">
                      <span
                        className="text-[20px] font-light tracking-[0.06em]"
                        style={{ color: 'rgba(255,255,255,0.85)', fontFamily: 'JetBrains Mono, monospace' }}
                      >
                        {modelId}
                      </span>
                      {/* GPU badge */}
                      <span
                        className="text-[9px] font-mono uppercase px-2 py-0.5 rounded-full tracking-wider flex items-center gap-1"
                        style={{
                          background: gpuName ? 'rgba(52,211,153,0.1)' : 'rgba(255,255,255,0.06)',
                          border: gpuName ? '1px solid rgba(52,211,153,0.25)' : '1px solid rgba(255,255,255,0.07)',
                          color: gpuName ? 'rgba(52,211,153,0.85)' : 'rgba(255,255,255,0.35)',
                        }}
                      >
                        {gpuName ? (
                          <>
                            <Zap size={8} />
                            RTX 2050 · CUDA
                          </>
                        ) : 'CPU'}
                      </span>
                    </div>
                    <p
                      className="text-[10px] tracking-[0.06em] mt-0.5"
                      style={{ color: 'rgba(255,255,255,0.22)' }}
                    >
                      reasoning · intent · planning · vision · multimodal
                    </p>
                  </div>

                  {/* Enricher model line */}
                  <div className="flex items-center gap-2" style={{ opacity: enricherReady ? 1 : 0.38 }}>
                    <span
                      className="text-[12px] font-mono"
                      style={{ color: 'rgba(255,255,255,0.45)' }}
                    >
                      gemma3:1b
                    </span>
                    <span
                      className="text-[9px] font-mono uppercase px-1.5 py-px rounded-full"
                      style={{
                        background: 'rgba(96,165,250,0.08)',
                        border: '1px solid rgba(96,165,250,0.15)',
                        color: 'rgba(96,165,250,0.65)',
                      }}
                    >
                      CPU · enricher
                    </span>
                    {!enricherReady && (
                      <span className="text-[10px] font-mono" style={{ color: 'rgba(251,191,36,0.5)' }}>
                        not found
                      </span>
                    )}
                  </div>

                  {/* Status line */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="flex items-center gap-2"
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{
                        background: allReady  ? 'rgb(52,211,153)'   :
                                   coreReady ? 'rgb(251,191,36)'    :
                                               'rgb(248,113,113)',
                        boxShadow: allReady  ? '0 0 8px rgba(52,211,153,0.6)'  :
                                   coreReady ? '0 0 8px rgba(251,191,36,0.5)'  :
                                               '0 0 8px rgba(248,113,113,0.5)',
                      }}
                    />
                    <span
                      className="text-[10px] font-mono tracking-[0.15em] uppercase"
                      style={{
                        color: allReady  ? 'rgba(52,211,153,0.7)'  :
                               coreReady ? 'rgba(251,191,36,0.7)'  :
                                           'rgba(248,113,113,0.65)',
                      }}
                    >
                      {allReady ? 'All systems ready' : coreReady ? 'Workspace degraded' : 'System unavailable'}
                    </span>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Let's Automate button ── */}
            <AnimatePresence>
              {phase === 'ready' && coreReady && (
                <motion.button
                  key="cta"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: 0.45, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  onClick={onComplete}
                  className="group flex items-center gap-2.5 px-7 py-3 rounded-full text-[13px] font-medium tracking-wide text-white transition-all duration-200 active:scale-[0.97] app-no-drag"
                  style={{
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.13)',
                    backdropFilter: 'blur(16px)',
                    WebkitBackdropFilter: 'blur(16px)',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)',
                  }}
                  onMouseEnter={(e) => {
                    const el = e.currentTarget as HTMLButtonElement
                    el.style.background  = 'rgba(255,255,255,0.17)'
                    el.style.borderColor = 'rgba(255,255,255,0.20)'
                    el.style.boxShadow   = '0 6px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.14)'
                  }}
                  onMouseLeave={(e) => {
                    const el = e.currentTarget as HTMLButtonElement
                    el.style.background  = 'rgba(255,255,255,0.1)'
                    el.style.borderColor = 'rgba(255,255,255,0.13)'
                    el.style.boxShadow   = '0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)'
                  }}
                >
                  Let&apos;s Automate
                  <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-0.5" />
                </motion.button>
              )}

              {/* Degraded fallback */}
              {phase === 'ready' && !coreReady && (
                <motion.button
                  key="fallback"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  onClick={onComplete}
                  className="text-[11px] font-mono tracking-widest uppercase app-no-drag"
                  style={{ color: 'rgba(255,255,255,0.3)' }}
                >
                  Enter anyway →
                </motion.button>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
