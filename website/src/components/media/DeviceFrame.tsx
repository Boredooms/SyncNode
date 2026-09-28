import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Workbench window frame — echoes the Electron app chrome. */
export function DeviceFrame({
  children,
  className,
  label,
}: {
  children: ReactNode;
  className?: string;
  label?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-line bg-ink-900 shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]",
        className
      )}
    >
      <div className="flex items-center gap-2 border-b border-line bg-ink-800 px-4 py-2.5">
        <span className="h-2 w-2 rounded-full bg-[#2E2E2E]" />
        <span className="h-2 w-2 rounded-full bg-[#252525]" />
        <span className="h-2 w-2 rounded-full bg-[#1E1E1E]" />
        {label && (
          <span className="ml-3 font-mono text-[10px] uppercase tracking-wider2 text-fg-dim">
            {label}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

/** Browser chrome frame. */
export function BrowserFrame({
  children,
  className,
  url = "localhost — syncnode",
}: {
  children: ReactNode;
  className?: string;
  url?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-line bg-ink-900",
        className
      )}
    >
      <div className="flex items-center gap-3 border-b border-line bg-ink-800 px-4 py-2.5">
        <span className="h-2 w-2 rounded-full bg-[#2E2E2E]" />
        <span className="h-2 w-2 rounded-full bg-[#252525]" />
        <span className="h-2 w-2 rounded-full bg-[#1E1E1E]" />
        <span className="ml-2 flex-1 rounded-sm bg-ink-950 px-3 py-1 font-mono text-[10px] text-fg-dim">
          {url}
        </span>
      </div>
      {children}
    </div>
  );
}
