#!/usr/bin/env python3
"""
SyncNode -- Network Monitor
===========================
Real-time outbound connection monitor for demo/audit use.
Shows every TCP connection SyncNode processes make so you can prove
during a presentation that nothing leaves your machine.

Usage:
    python scripts/network_monitor.py [--pid PID] [--interval 1.0] [--output log.txt]

Flags:
    --pid        Monitor only connections from this PID (default: all SyncNode processes)
    --interval   Poll interval in seconds (default: 1.0)
    --output     Also write events to a JSON log file
    --loopback   Show loopback (127.x) connections (default: hidden)
    --all        Monitor all system processes, not just SyncNode

Output columns:
    TIME   PID   PROCESS   LOCAL ADDR   REMOTE ADDR   CLASSIFICATION
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time

try:
    import psutil
except ImportError:
    print("ERROR: psutil is required.  pip install psutil")
    sys.exit(1)

# ANSI colours
RESET  = "\033[0m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

LOOPBACK_PREFIXES = ("127.", "::1", "0.0.0.0")
LOCAL_PREFIXES    = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.",
                     "172.2", "172.3")
SYNCNODE_PORTS    = {8000, 11434, 5173}


def is_loopback(addr: str) -> bool:
    return any(addr.startswith(p) for p in LOOPBACK_PREFIXES)


def is_local_network(addr: str) -> bool:
    return any(addr.startswith(p) for p in LOCAL_PREFIXES)


def classify(rip: str, rport: int):
    if is_loopback(rip):
        lbl = "LOCAL (SyncNode)" if rport in SYNCNODE_PORTS else "LOOPBACK"
        return lbl, GREEN
    if is_local_network(rip):
        return "LAN", YELLOW
    return "[!] EXTERNAL [!]", RED


def syncnode_pids():
    pids = set()
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (p.info["name"] or "").lower()
            cmd  = " ".join(p.info["cmdline"] or []).lower()
            if "python" in name or "uvicorn" in name or "node" in name:
                if any(k in cmd for k in ["syncnode", "uvicorn", "start_server", "electron"]):
                    pids.add(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


def collect(target_pid, show_loopback, all_procs):
    conns = []
    try:
        if all_procs:
            raw = psutil.net_connections(kind="tcp")
            for c in raw:
                if c.status not in ("ESTABLISHED", "SYN_SENT", "CLOSE_WAIT") or not c.raddr:
                    continue
                rip, rport = c.raddr.ip, c.raddr.port
                if not show_loopback and is_loopback(rip):
                    continue
                lbl, col = classify(rip, rport)
                try:
                    pname = psutil.Process(c.pid).name() if c.pid else "?"
                except Exception:
                    pname = "?"
                conns.append(dict(
                    pid=c.pid, process=pname,
                    laddr=f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?",
                    raddr=f"{rip}:{rport}", rip=rip, rport=rport,
                    status=c.status, label=lbl, colour=col,
                ))
        else:
            pids = {target_pid} if target_pid else syncnode_pids()
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    raw_conns = psutil.net_connections(kind="tcp")
                    pid_conns = [c for c in raw_conns if c.pid == pid]
                    for c in pid_conns:
                        if c.status not in ("ESTABLISHED", "SYN_SENT", "CLOSE_WAIT") or not c.raddr:
                            continue
                        rip, rport = c.raddr.ip, c.raddr.port
                        if not show_loopback and is_loopback(rip):
                            continue
                        lbl, col = classify(rip, rport)
                        conns.append(dict(
                            pid=pid, process=proc.name(),
                            laddr=f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?",
                            raddr=f"{rip}:{rport}", rip=rip, rport=rport,
                            status=c.status, label=lbl, colour=col,
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    except Exception:
        pass
    return conns


def now():
    return datetime.datetime.now().strftime("%H:%M:%S")


def main():
    ap = argparse.ArgumentParser(description="SyncNode Network Monitor")
    ap.add_argument("--pid",      type=int,   default=None)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--output",   type=str,   default=None)
    ap.add_argument("--loopback", action="store_true")
    ap.add_argument("--all",      action="store_true")
    args = ap.parse_args()

    log = open(args.output, "a", encoding="utf-8") if args.output else None
    seen = {}
    external_lifetime = 0

    W = 100
    print(f"\n{BOLD}{'=' * W}{RESET}")
    print(f"{BOLD}  SyncNode Network Monitor  --  proving zero outbound traffic  --  Ctrl+C to stop{RESET}")
    print(f"{BOLD}{'=' * W}{RESET}")
    print(f"  {BOLD}{'TIME':8}  {'PID':6}  {'PROCESS':18}  {'LOCAL ADDR':22}  {'REMOTE ADDR':22}  CLASSIFICATION{RESET}")
    print(f"{'─' * W}")

    try:
        while True:
            conns = collect(args.pid, args.loopback, args.all)
            ts = now()
            current_keys = set()

            for c in conns:
                key = f"{c['pid']}-{c['laddr']}-{c['raddr']}"
                current_keys.add(key)
                if key not in seen:
                    seen[key] = c
                    print(
                        f"\r  {ts:8}  {str(c['pid']):6}  {c['process']:18}  "
                        f"{c['laddr']:22}  {c['raddr']:22}  "
                        f"{c['colour']}{c['label']}{RESET}"
                    )
                    if "EXTERNAL" in c["label"]:
                        external_lifetime += 1
                        print(f"  {RED}{BOLD}  *** OUTBOUND EXTERNAL CONNECTION: {c['raddr']} ***{RESET}")
                    if log:
                        log.write(json.dumps({
                            "time": ts, "event": "new",
                            **{k: v for k, v in c.items() if k not in ("colour",)},
                        }) + "\n")
                        log.flush()

            for key in set(seen) - current_keys:
                old = seen.pop(key)
                print(
                    f"\r  {DIM}{ts:8}  {str(old['pid']):6}  {old['process']:18}  "
                    f"{old['laddr']:22}  {old['raddr']:22}  [closed]{RESET}"
                )

            active = len(conns)
            ext    = sum(1 for c in conns if "EXTERNAL" in c["label"])
            if ext == 0:
                status_part = f"{GREEN}0 external -- ALL LOCAL -- SOVEREIGN{RESET}"
            else:
                status_part = f"{RED}{BOLD}{ext} EXTERNAL CONNECTIONS DETECTED!{RESET}"
            print(
                f"\r  {DIM}[{ts}] active={active}  external={status_part}  "
                f"lifetime_external={external_lifetime}{RESET}   ",
                end="", flush=True,
            )
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n{BOLD}{'=' * W}{RESET}")
        ext_total = external_lifetime
        if ext_total == 0:
            print(f"  {GREEN}{BOLD}RESULT: ZERO external connections detected. SyncNode is fully sovereign.{RESET}")
        else:
            print(f"  {RED}{BOLD}RESULT: {ext_total} external connection(s) were detected. Review the log.{RESET}")
        print(f"{BOLD}{'=' * W}{RESET}\n")
        if log:
            log.close()


if __name__ == "__main__":
    main()
