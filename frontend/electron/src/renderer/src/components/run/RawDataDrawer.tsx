import { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Copy, Check, Code } from 'lucide-react'

interface RawDataDrawerProps {
  title: string
  data: any
  isOpen: boolean
  onClose: () => void
}

export function RawDataDrawer({ title, data, isOpen, onClose }: RawDataDrawerProps) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs">
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 28, stiffness: 280 }}
        className="w-full max-w-xl h-full bg-[#0d0d0d] border-l border-white/10 flex flex-col shadow-2xl"
      >
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.05] bg-[#111]">
          <div className="flex items-center gap-2">
            <Code size={14} className="text-white/60" />
            <span className="text-[13px] font-semibold text-white/90">{title}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] text-white/50 hover:text-white/90 hover:bg-white/5 border border-white/[0.07] transition-colors"
            >
              {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded text-white/40 hover:text-white/80 hover:bg-white/5 transition-colors"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-y-auto">
          <pre className="p-4 rounded-lg bg-black/90 border border-white/[0.06] text-white/80 font-mono text-[11px] leading-relaxed overflow-x-auto select-text">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </motion.div>
    </div>
  )
}
