import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { navGroups } from "@/data/navigation";
import { GITHUB_URL } from "@/data/videos";

export function Footer() {
  return (
    <footer className="border-t border-line bg-ink-950">
      <div className="container-page py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <div className="font-sans text-[13px] font-semibold tracking-[0.32em] text-fg-primary">
              SYNCNODE
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-fg-dim">
              Think locally. Act intelligently.
            </p>
            <p className="mt-2 max-w-xs text-sm leading-relaxed text-fg-faint">
              A sovereign local AI workbench for confidential work.
            </p>
          </div>

          {navGroups.map((group) => (
            <nav key={group.label} aria-label={`${group.label} footer`}>
              <div className="eyebrow mb-4">{group.label}</div>
              <ul className="space-y-2.5">
                {group.items.map((item) => (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className="text-sm text-fg-mute transition-colors hover:text-fg-primary"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
                {group.label === "Resources" && (
                  <li>
                    <a
                      href={GITHUB_URL}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-1 text-sm text-fg-mute transition-colors hover:text-fg-primary"
                    >
                      GitHub <ArrowUpRight className="h-3 w-3" />
                    </a>
                  </li>
                )}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-16 flex flex-col gap-2 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
          <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
            © 2026 SyncNode
          </span>
          <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
            LOCAL AI · REAL EXECUTION · VERIFIED OUTCOMES
          </span>
        </div>
      </div>
    </footer>
  );
}
