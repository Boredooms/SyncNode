import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Download, Menu, X, ArrowUpRight } from "lucide-react";
import { navGroups } from "@/data/navigation";
import { GITHUB_URL } from "@/data/videos";
import { cn } from "@/lib/utils";

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeTimer = useRef<number>();
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    setOpenGroup(null);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const enter = (label: string) => {
    window.clearTimeout(closeTimer.current);
    setOpenGroup(label);
  };
  const leave = () => {
    closeTimer.current = window.setTimeout(() => setOpenGroup(null), 120);
  };

  return (
    <>
      <header
        className={cn(
          "fixed inset-x-0 top-0 z-[80] transition-all duration-300",
          scrolled
            ? "border-b border-line bg-ink-950/85 backdrop-blur-md"
            : "border-b border-transparent bg-transparent"
        )}
      >
        <div className="container-page flex h-16 items-center justify-between">
          {/* Wordmark */}
          <Link
            to="/"
            className="font-sans text-[13px] font-semibold tracking-[0.32em] text-fg-primary"
            aria-label="SyncNode home"
          >
            SYNCNODE
          </Link>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
            {navGroups.map((group) => (
              <div
                key={group.label}
                className="relative"
                onMouseEnter={() => enter(group.label)}
                onMouseLeave={leave}
              >
                <button
                  className={cn(
                    "flex items-center gap-1.5 rounded-[4px] px-3.5 py-2 text-[13px] text-fg-mute transition-colors hover:text-fg-primary",
                    openGroup === group.label && "text-fg-primary"
                  )}
                  aria-expanded={openGroup === group.label}
                  onClick={() =>
                    setOpenGroup(openGroup === group.label ? null : group.label)
                  }
                >
                  {group.label}
                  <ChevronDown
                    className={cn(
                      "h-3 w-3 transition-transform duration-200",
                      openGroup === group.label && "rotate-180"
                    )}
                  />
                </button>

                <AnimatePresence>
                  {openGroup === group.label && (
                    <motion.div
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 4 }}
                      transition={{ duration: 0.18 }}
                      className="absolute left-0 top-full mt-2 w-72 overflow-hidden rounded-md border border-line bg-ink-900/95 shadow-2xl backdrop-blur-md"
                    >
                      <div className="p-1.5">
                        {group.items.map((item) => (
                          <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                              cn(
                                "block rounded-[4px] px-3.5 py-2.5 transition-colors",
                                isActive
                                  ? "bg-ink-700 text-fg-primary"
                                  : "text-fg-mute hover:bg-ink-800 hover:text-fg-primary"
                              )
                            }
                          >
                            <div className="text-[13px]">{item.label}</div>
                            {item.desc && (
                              <div className="mt-0.5 text-[11px] text-fg-dim">
                                {item.desc}
                              </div>
                            )}
                          </NavLink>
                        ))}
                        {group.label === "Resources" && (
                          <a
                            href={GITHUB_URL}
                            target="_blank"
                            rel="noreferrer noopener"
                            className="block rounded-[4px] px-3.5 py-2.5 text-[13px] text-fg-mute transition-colors hover:bg-ink-800 hover:text-fg-primary"
                          >
                            <div className="flex items-center gap-1.5">
                              GitHub <ArrowUpRight className="h-3 w-3" />
                            </div>
                            <div className="mt-0.5 text-[11px] text-fg-dim">
                              Source and releases
                            </div>
                          </a>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </nav>

          {/* Right side */}
          <div className="hidden items-center gap-3 lg:flex">
            <Link
              to="/download"
              className="btn-primary btn-md"
            >
              <Download className="h-3.5 w-3.5" />
              Download for Windows
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="flex h-10 w-10 items-center justify-center text-fg-primary lg:hidden"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-[70] flex flex-col overflow-y-auto bg-ink-950/98 backdrop-blur-sm lg:hidden"
          >
            <div className="flex-1 px-6 pb-10 pt-24">
              {navGroups.map((group) => (
                <div key={group.label} className="mb-8">
                  <div className="eyebrow mb-3">{group.label}</div>
                  <div className="space-y-1">
                    {group.items.map((item) => (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        className="block py-2 text-2xl font-light text-fg-body transition-colors hover:text-fg-primary"
                      >
                        {item.label}
                      </NavLink>
                    ))}
                  </div>
                </div>
              ))}
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer noopener"
                className="flex items-center gap-1.5 py-2 text-2xl font-light text-fg-body"
              >
                GitHub <ArrowUpRight className="h-5 w-5" />
              </a>
            </div>
            <div className="border-t border-line px-6 py-6">
              <Link to="/download" className="btn-primary btn-lg w-full">
                <Download className="h-4 w-4" />
                Download for Windows
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
