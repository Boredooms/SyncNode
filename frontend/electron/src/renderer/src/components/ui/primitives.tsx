import { type HTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

// ── StatusBadge ───────────────────────────────────────────
interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: string
  size?: 'sm' | 'md'
}

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ status, size = 'sm', className, ...props }, ref) => {
    const colors: Record<string, string> = {
      running: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      completed: 'bg-green-500/10 text-green-400 border-green-500/20',
      failed: 'bg-red-500/10 text-red-400 border-red-500/20',
      waiting_approval: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      waiting: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      queued: 'bg-white/5 text-white/40 border-white/10',
      cancelled: 'bg-white/5 text-white/30 border-white/10',
      passed: 'bg-green-500/10 text-green-400 border-green-500/20',
      failed_v: 'bg-red-500/10 text-red-400 border-red-500/20',
    }
    const color = colors[status] ?? 'bg-white/5 text-white/40 border-white/10'
    const sizes = {
      sm: 'text-[10px] px-1.5 py-0.5',
      md: 'text-[11px] px-2 py-0.5',
    }
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded border font-medium uppercase tracking-wide',
          sizes[size],
          color,
          className
        )}
        {...props}
      >
        {status.replace(/_/g, ' ')}
      </span>
    )
  }
)
StatusBadge.displayName = 'StatusBadge'

// ── StatusDot ─────────────────────────────────────────────
interface StatusDotProps {
  status: string
  className?: string
}

export function StatusDot({ status, className }: StatusDotProps) {
  const colors: Record<string, string> = {
    running: 'bg-blue-400 animate-pulse-dot',
    completed: 'bg-green-400',
    failed: 'bg-red-400',
    waiting_approval: 'bg-amber-400',
    waiting: 'bg-amber-400',
    queued: 'bg-white/30',
    idle: 'bg-white/20',
    spawned: 'bg-blue-400/60',
  }
  const color = colors[status] ?? 'bg-white/20'
  return (
    <span
      className={cn('inline-block w-1.5 h-1.5 rounded-full flex-shrink-0', color, className)}
    />
  )
}

// ── Skeleton ──────────────────────────────────────────────
interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded animate-pulse bg-white/5',
        className
      )}
      {...props}
    />
  )
}

// ── Divider ───────────────────────────────────────────────
export function Divider({ className }: { className?: string }) {
  return <div className={cn('h-px bg-white/8', className)} />
}

// ── EmptyState ────────────────────────────────────────────
interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-12 px-6 text-center', className)}>
      {icon && <div className="text-white/20 mb-1">{icon}</div>}
      <p className="text-[13px] font-medium text-white/50">{title}</p>
      {description && <p className="text-[11px] text-white/30 max-w-xs">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

// ── SectionHeader ─────────────────────────────────────────
interface SectionHeaderProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  className?: string
}

export function SectionHeader({ title, subtitle, action, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between px-3 py-2 border-b border-white/[0.05]', className)}>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-widest text-white/40">{title}</p>
        {subtitle && <p className="text-[10px] text-white/25 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="app-no-drag">{action}</div>}
    </div>
  )
}

// ── IconButton ────────────────────────────────────────────
interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  tooltip?: string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, children, tooltip, ...props }, ref) => (
    <button
      ref={ref}
      title={tooltip}
      className={cn(
        'app-no-drag inline-flex items-center justify-center w-7 h-7 rounded',
        'text-white/40 hover:text-white/80 hover:bg-white/8',
        'transition-colors duration-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/[0.08]',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
)
IconButton.displayName = 'IconButton'
