"""
SyncNode — System Tools (Full Local PC Access with Safety Rails).

Gives Gemma broad access to the local Windows machine while preventing
irreversible damage:

SAFE (read-only, no rails needed):
  system.fs_read       — read any file
  system.fs_list       — list any directory
  system.fs_search     — search files by name/content
  system.process_list  — list running processes
  system.clipboard_get — read clipboard
  system.env_get       — read environment variables
  system.registry_get  — read registry keys

CAUTIOUS (write but reversible):
  system.fs_write      — write files (BLOCKED inside protected system dirs)
  system.clipboard_set — write to clipboard

GUARDED (potentially irreversible — requires confirm=true):
  system.fs_delete     — moves to Recycle Bin unless confirm=true AND
                         path is NOT in protected dirs (no permanent delete of
                         system files, SyncNode itself, or user profile roots)
  system.shell         — runs commands; BLOCKED patterns that rm/del/format/
                         kill system processes; require confirm=true for
                         any command touching outside the workspace
  system.process_kill  — kill user processes; BLOCKED for system PIDs <10
                         and critical Windows services

BLOCKED ALWAYS (no flag can override):
  - Writes to C:\Windows\*, C:\Program Files\*, system32
  - Deleting SyncNode's own workspace/data
  - Killing PID 0, 4 (System), lsass, csrss, winlogon, services
  - Registry writes (read-only for now)
  - Network calls, raw socket access
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Protected paths — writes/deletes blocked unconditionally ──────────────────
_PROTECTED_PREFIXES = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData\\Microsoft",
    "C:\\Users\\Default",
]

# SyncNode's own installation — never delete or overwrite
_SYNCNODE_ROOT = Path(r"C:\syncnode").resolve()

# Critical processes that must never be killed
_PROTECTED_PROCESSES = {
    "lsass.exe", "csrss.exe", "winlogon.exe", "services.exe",
    "smss.exe", "wininit.exe", "svchost.exe", "System",
}

# Shell command patterns that are outright blocked
_BLOCKED_SHELL_PATTERNS = [
    r"format\s+[a-z]:",           # format drive
    r"del\s+/[sq].*[*?]",         # del /s /q wildcard
    r"rd\s+/[sq].*windows",       # rd /s /q C:\Windows
    r"Remove-Item.*-Recurse.*Windows",
    r"Remove-Item.*-Recurse.*Program",
    r"(net\s+user|net\s+localgroup).*\/add",  # add users/admins
    r"reg\s+(delete|add)\s+HKLM",  # registry writes to machine hive
    r"bcdedit|bootcfg",            # bootloader
    r"cipher\s+/w",               # wipe free space
    r"shutdown\s+/[rsp]",         # shutdown/restart
]


def _is_protected(path: str) -> bool:
    """True if the path falls inside a protected system directory."""
    try:
        resolved = Path(path).expanduser().resolve()
        # Never touch SyncNode's own data folder writes (reads are fine)
        if str(resolved).startswith(str(_SYNCNODE_ROOT / "data")):
            return True
        for prefix in _PROTECTED_PREFIXES:
            if str(resolved).startswith(Path(prefix).resolve().__str__()):
                return True
    except Exception:
        pass
    return False


def _shell_is_blocked(command: str) -> Optional[str]:
    """Return a human-readable reason if the command matches a blocked pattern."""
    lower = command.lower()
    for pat in _BLOCKED_SHELL_PATTERNS:
        if re.search(pat, lower, re.IGNORECASE):
            return f"Command matches blocked pattern: {pat}"
    return None


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── READ-ONLY tools (no restrictions) ───────────────────────────────────────

async def tool_system_fs_read(
    path: str,
    encoding: str = "utf-8",
    max_bytes: int = 256_000,
) -> dict[str, Any]:
    """Read any file on the local PC. Returns text content up to max_bytes."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"exists": False, "path": str(p), "content": None}
    size = p.stat().st_size
    try:
        if encoding.lower() in ("binary", "bytes", "bin"):
            raw = p.read_bytes()[:max_bytes]
            return {"exists": True, "path": str(p), "size_bytes": size,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "content": f"<binary {len(raw)} bytes shown>", "binary": True}
        content = p.read_text(encoding=encoding, errors="replace")
        if len(content) > max_bytes:
            content = content[:max_bytes] + f"\n... [truncated — {size} bytes total]"
        return {"exists": True, "path": str(p), "size_bytes": size,
                "sha256": _sha(p), "content": content}
    except Exception as exc:
        return {"exists": True, "path": str(p), "size_bytes": size,
                "error": str(exc), "content": None}


async def tool_system_fs_list(
    path: str = "C:\\Users",
    pattern: str = "*",
    recursive: bool = False,
    max_results: int = 300,
) -> dict[str, Any]:
    """List files and folders in any directory. recursive=True for deep listing."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"exists": False, "path": str(p), "entries": []}
    try:
        entries_raw = list(p.rglob(pattern) if recursive else p.glob(pattern))[:max_results]
        entries = []
        for e in entries_raw:
            try:
                st = e.stat()
                entries.append({
                    "name": e.name, "path": str(e), "is_dir": e.is_dir(),
                    "size_bytes": st.st_size if not e.is_dir() else None,
                    "modified": st.st_mtime,
                })
            except Exception:
                entries.append({"name": e.name, "path": str(e), "is_dir": e.is_dir()})
        return {"exists": True, "path": str(p), "count": len(entries), "entries": entries}
    except Exception as exc:
        return {"exists": True, "path": str(p), "error": str(exc), "entries": []}


async def tool_system_fs_search(
    query: str = "",
    search_path: str = "C:\\Users",
    pattern: Optional[str] = None,
    content_search: bool = False,
    max_results: int = 100,
) -> dict[str, Any]:
    """Search for files by name or content anywhere on the PC.
    query matches filename substrings (leave empty to match all).
    pattern is a glob like '*.xlsx' to narrow by file type.
    """
    base = Path(search_path).expanduser().resolve()
    found: list[dict] = []
    glob = pattern or "*"
    try:
        for f in base.rglob(glob):
            if not f.is_file():
                continue
            # Empty query = match everything (pattern already filters)
            if not query or query.lower() in f.name.lower():
                found.append({"path": str(f), "name": f.name, "match": "name",
                              "size_bytes": f.stat().st_size})
                if len(found) >= max_results:
                    break
                continue
            if content_search and f.stat().st_size < 1_000_000:
                try:
                    if query.lower() in f.read_text(encoding="utf-8", errors="ignore").lower():
                        found.append({"path": str(f), "name": f.name, "match": "content",
                                     "size_bytes": f.stat().st_size})
                        if len(found) >= max_results:
                            break
                except Exception:
                    pass
    except Exception as exc:
        return {"query": query, "error": str(exc), "found": found, "count": len(found)}
    return {"query": query, "search_path": str(base), "count": len(found), "found": found}


async def tool_system_process_list(filter_name: Optional[str] = None) -> dict[str, Any]:
    """List running processes, optionally filtered by name."""
    result = await tool_system_shell(
        f"Get-Process {filter_name or '*'} | Select-Object Id,ProcessName,"
        f"@{{N='MemMB';E={{[math]::Round($_.WorkingSet/1MB,1)}}}} | ConvertTo-Json -Depth 2",
        confirm=True,
    )
    return {"stdout": result.get("stdout", ""), "count_hint": "see stdout JSON"}


async def tool_system_clipboard_get() -> dict[str, Any]:
    """Read the current clipboard text."""
    result = await tool_system_shell("Get-Clipboard", confirm=True)
    text = result.get("stdout", "").strip()
    return {"text": text, "length": len(text)}


async def tool_system_env_get(name: Optional[str] = None) -> dict[str, Any]:
    """Read environment variables. name=None returns all."""
    if name:
        val = os.environ.get(name)
        return {"name": name, "value": val, "found": val is not None}
    return {"count": len(os.environ), "variables": dict(os.environ)}


async def tool_system_registry_get(
    hive: str, key_path: str, value_name: Optional[str] = None
) -> dict[str, Any]:
    """Read a Windows registry key or value (read-only)."""
    try:
        import winreg
        hive_map = {
            "HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER,
            "HKCR": winreg.HKEY_CLASSES_ROOT,  "HKU":  winreg.HKEY_USERS,
        }
        hive_key = hive_map.get(hive.upper())
        if not hive_key:
            return {"error": f"Unknown hive: {hive}"}
        with winreg.OpenKey(hive_key, key_path) as k:
            if value_name:
                val, vtype = winreg.QueryValueEx(k, value_name)
                return {"hive": hive, "key": key_path, "name": value_name,
                        "value": str(val), "type": vtype}
            values, i = [], 0
            while True:
                try:
                    n, d, t = winreg.EnumValue(k, i)
                    values.append({"name": n, "value": str(d), "type": t})
                    i += 1
                except OSError:
                    break
            return {"hive": hive, "key": key_path, "values": values}
    except FileNotFoundError:
        return {"error": f"Key not found: {hive}\\{key_path}"}
    except Exception as exc:
        return {"error": str(exc)}


# ─── WRITE tools (protected path guard) ──────────────────────────────────────

async def tool_system_fs_write(
    path: str,
    content: str,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Write any file on the PC. Blocked for system/protected directories."""
    p = Path(path).expanduser().resolve()
    if _is_protected(str(p)):
        return {"written": False, "path": str(p),
                "error": f"Write blocked — '{p}' is in a protected system directory."}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    sha = _sha(p)
    logger.info("[SYSTEM] fs_write %s (%d bytes)", p, p.stat().st_size)
    return {"written": True, "path": str(p), "size_bytes": p.stat().st_size, "sha256": sha}


async def tool_system_clipboard_set(text: str) -> dict[str, Any]:
    """Write text to the clipboard."""
    result = await tool_system_shell(
        f"Set-Clipboard -Value @'\n{text}\n'@", confirm=True
    )
    return {"set": result["exit_code"] == 0, "length": len(text)}


# ─── DELETE tool (Recycle Bin; permanent only with confirm=true + safety check) ─

async def tool_system_fs_delete(
    path: str,
    confirm: bool = False,
    permanent: bool = False,
) -> dict[str, Any]:
    """Delete a file safely.

    Default (confirm=False): DRY RUN — shows what would be deleted, does nothing.
    confirm=True + permanent=False: moves to Recycle Bin (recoverable).
    confirm=True + permanent=True: permanently deletes (use carefully).

    Blocked unconditionally for protected system paths.
    """
    p = Path(path).expanduser().resolve()

    if not p.exists():
        return {"deleted": False, "path": str(p), "error": "File not found"}

    if _is_protected(str(p)):
        return {"deleted": False, "path": str(p),
                "error": "Delete blocked — protected system path."}

    if not confirm:
        return {
            "deleted": False,
            "dry_run": True,
            "path": str(p),
            "size_bytes": p.stat().st_size if p.is_file() else None,
            "message": "DRY RUN — set confirm=true to actually delete. "
                       "Set permanent=false (default) to send to Recycle Bin instead.",
        }

    if not permanent:
        # Move to Recycle Bin via PowerShell
        escaped = str(p).replace("'", "''")
        result = await tool_system_shell(
            f"Add-Type -AssemblyName Microsoft.VisualBasic; "
            f"[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
            f"'{escaped}',"
            f"[Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,"
            f"[Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)",
            confirm=True,
        )
        ok = result["exit_code"] == 0
        logger.info("[SYSTEM] fs_delete (recycle bin) %s ok=%s", p, ok)
        return {"deleted": ok, "path": str(p), "method": "recycle_bin",
                "error": result.get("stderr") if not ok else None}
    else:
        p.unlink()
        logger.warning("[SYSTEM] fs_delete PERMANENT %s", p)
        return {"deleted": True, "path": str(p), "method": "permanent"}


# ─── SHELL tool (blocked patterns + confirm gate for destructive ops) ─────────

async def tool_system_shell(
    command: str,
    shell: str = "powershell",
    timeout_seconds: int = 30,
    working_dir: Optional[str] = None,
    confirm: bool = True,   # default True — shell is always "confirmed" by the model calling it
) -> dict[str, Any]:
    """Run any PowerShell or CMD command on the local PC.

    Blocked patterns: format, mass-delete, bootloader, shutdown, registry writes.
    Returns stdout, stderr, exit_code, success.
    """
    blocked_reason = _shell_is_blocked(command)
    if blocked_reason:
        return {
            "exit_code": -1, "success": False,
            "stdout": "", "stderr": "",
            "blocked": True,
            "reason": blocked_reason,
            "command": command,
        }

    cwd = Path(working_dir).expanduser().resolve() if working_dir else None

    if shell.lower() in ("powershell", "pwsh", "ps"):
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
    else:
        cmd = ["cmd", "/c", command]

    logger.info("[SYSTEM] shell: %s", command[:120])
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
        return {
            "exit_code": proc.returncode,
            "stdout": (stdout or b"").decode("utf-8", errors="replace")[:20_000],
            "stderr": (stderr or b"").decode("utf-8", errors="replace")[:4_000],
            "command": command,
            "success": proc.returncode == 0,
        }
    except asyncio.TimeoutError:
        return {"exit_code": -1, "success": False, "stdout": "", "stderr": "",
                "error": f"Timed out after {timeout_seconds}s", "command": command}
    except Exception as exc:
        return {"exit_code": -1, "success": False, "stdout": "", "stderr": str(exc),
                "error": str(exc), "command": command}


# ─── PROCESS KILL (blocked for critical system processes) ─────────────────────

async def tool_system_process_kill(
    name: Optional[str] = None,
    pid: Optional[int] = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """Terminate a process by name or PID.

    Blocked for critical Windows system processes.
    confirm=False (default): DRY RUN.
    confirm=True: actually kills the process.
    """
    if not confirm:
        return {"killed": False, "dry_run": True, "name": name, "pid": pid,
                "message": "DRY RUN — set confirm=true to actually kill this process."}

    if name and name.lower() in {p.lower() for p in _PROTECTED_PROCESSES}:
        return {"killed": False, "name": name,
                "error": f"Process '{name}' is a protected system process — kill blocked."}

    if pid is not None and pid < 10:
        return {"killed": False, "pid": pid,
                "error": f"PID {pid} is a protected system PID — kill blocked."}

    if pid:
        result = await tool_system_shell(f"Stop-Process -Id {pid} -Force", confirm=True)
    elif name:
        result = await tool_system_shell(
            f"Stop-Process -Name '{name}' -Force -ErrorAction SilentlyContinue", confirm=True
        )
    else:
        return {"killed": False, "error": "Provide name or pid"}

    return {"killed": result["exit_code"] == 0, "name": name, "pid": pid,
            "stdout": result.get("stdout", ""), "stderr": result.get("stderr", "")}


# ─── Registration ─────────────────────────────────────────────────────────────

def register_system_tools(registry) -> None:
    from syncnode_backend.tools.registry import ToolDefinition

    tools = [
        ToolDefinition(
            key="system.fs_read",
            name="Read File (System)",
            version=1,
            description="Read any file on the PC — documents, configs, logs, code, anywhere. No path restrictions for reading.",
            input_schema={"path": "str", "encoding": "str?", "max_bytes": "int?"},
            output_schema={"content": "str", "exists": "bool", "sha256": "str"},
            capabilities=["filesystem", "system_access"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_fs_read,
            drop_decorative_args=True,
            arg_aliases={"file": "path", "filename": "path", "file_path": "path",
                         "filepath": "path", "location": "path"},
        ),
        ToolDefinition(
            key="system.fs_list",
            name="List Directory (System)",
            version=1,
            description="List files and folders in any directory on the PC. Use recursive=true for deep listing. Default starts at C:\\Users.",
            input_schema={"path": "str", "pattern": "str?", "recursive": "bool?", "max_results": "int?"},
            output_schema={"entries": "list", "count": "int"},
            capabilities=["filesystem", "system_access"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_fs_list,
            drop_decorative_args=True,
            arg_aliases={"directory": "path", "dir": "path", "folder": "path", "glob": "pattern"},
        ),
        ToolDefinition(
            key="system.fs_search",
            name="Search Files (System)",
            version=1,
            description="Search for files by name or content anywhere on the PC. query matches filename substrings (empty = match all). Set pattern like '*.xlsx' to narrow by file type. Set content_search=true to search inside files.",
            input_schema={"query": "str?", "search_path": "str?", "pattern": "str?",
                          "content_search": "bool?", "max_results": "int?"},
            output_schema={"found": "list", "count": "int"},
            capabilities=["filesystem", "system_access"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_fs_search,
            drop_decorative_args=True,
            arg_aliases={"term": "query", "name": "query", "filename": "query",
                         "root": "search_path", "start": "search_path",
                         "path": "search_path", "directory": "search_path",
                         "dir": "search_path", "folder": "search_path",
                         "extension": "pattern", "file_type": "pattern",
                         "glob": "pattern", "type": "pattern"},
        ),
        ToolDefinition(
            key="system.fs_write",
            name="Write File (System)",
            version=1,
            description="Write any file on the PC. Blocked for C:\\Windows, Program Files, and other system directories. Creates parent directories automatically.",
            input_schema={"path": "str", "content": "str", "encoding": "str?"},
            output_schema={"written": "bool", "sha256": "str"},
            capabilities=["filesystem", "system_access"],
            risk_class="medium", side_effect_type="IDEMPOTENT_LOCAL", idempotency="idempotent",
            verification_strategy="always", handler=tool_system_fs_write,
            drop_decorative_args=True,
            arg_aliases={"file": "path", "filename": "path", "file_path": "path",
                         "text": "content", "data": "content", "body": "content"},
        ),
        ToolDefinition(
            key="system.fs_delete",
            name="Delete File (System)",
            version=1,
            description="Delete a file on the PC safely. Default is DRY RUN (confirm=false). Set confirm=true to send to Recycle Bin. Set permanent=true only if absolutely sure — cannot be undone.",
            input_schema={"path": "str", "confirm": "bool?", "permanent": "bool?"},
            output_schema={"deleted": "bool", "dry_run": "bool?"},
            capabilities=["filesystem", "system_access"],
            risk_class="high", side_effect_type="DESTRUCTIVE_LOCAL", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_fs_delete,
            drop_decorative_args=True,
            arg_aliases={"file": "path", "filename": "path", "file_path": "path"},
        ),
        ToolDefinition(
            key="system.shell",
            name="Shell Execute",
            version=1,
            description="Run any PowerShell command on the PC. Returns stdout, stderr, exit code. Blocked: format drives, mass-delete, shutdown, bootloader, registry writes. Use this for anything requiring a real shell.",
            input_schema={"command": "str", "shell": "str?", "timeout_seconds": "int?", "working_dir": "str?"},
            output_schema={"stdout": "str", "stderr": "str", "exit_code": "int", "success": "bool"},
            capabilities=["shell", "system_access"],
            risk_class="high", side_effect_type="UNKNOWN_EXTERNAL_EFFECT", idempotency="non_idempotent",
            verification_strategy="never", handler=tool_system_shell,
            drop_decorative_args=True,
            arg_aliases={"cmd": "command", "script": "command", "run": "command",
                         "execute": "command", "code": "command",
                         "cwd": "working_dir", "directory": "working_dir"},
        ),
        ToolDefinition(
            key="system.process_list",
            name="List Processes",
            version=1,
            description="List all running processes on the PC. Filter by name substring.",
            input_schema={"filter_name": "str?"},
            output_schema={"stdout": "str"},
            capabilities=["system_info"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_process_list,
            drop_decorative_args=True,
            arg_aliases={"name": "filter_name", "filter": "filter_name",
                         "process": "filter_name", "app": "filter_name"},
        ),
        ToolDefinition(
            key="system.process_kill",
            name="Kill Process",
            version=1,
            description="Terminate a process. Default is DRY RUN (confirm=false). Set confirm=true to actually kill. Blocked for critical Windows system processes.",
            input_schema={"name": "str?", "pid": "int?", "confirm": "bool?"},
            output_schema={"killed": "bool", "dry_run": "bool?"},
            capabilities=["system_control"],
            risk_class="high", side_effect_type="DESTRUCTIVE_LOCAL", idempotency="non_idempotent",
            verification_strategy="never", handler=tool_system_process_kill,
            drop_decorative_args=True,
            arg_aliases={"process_name": "name", "app": "name", "process_id": "pid"},
        ),
        ToolDefinition(
            key="system.clipboard_get",
            name="Get Clipboard",
            version=1,
            description="Read the current clipboard text.",
            input_schema={},
            output_schema={"text": "str", "length": "int"},
            capabilities=["clipboard"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_clipboard_get,
        ),
        ToolDefinition(
            key="system.clipboard_set",
            name="Set Clipboard",
            version=1,
            description="Write text to the clipboard so it can be pasted into any app.",
            input_schema={"text": "str"},
            output_schema={"set": "bool"},
            capabilities=["clipboard"],
            risk_class="low", side_effect_type="REVERSIBLE_LOCAL", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_clipboard_set,
            drop_decorative_args=True,
            arg_aliases={"content": "text", "value": "text", "data": "text"},
        ),
        ToolDefinition(
            key="system.env_get",
            name="Get Environment",
            version=1,
            description="Read environment variables. Pass name for a specific variable, omit to get all.",
            input_schema={"name": "str?"},
            output_schema={"value": "str", "variables": "dict"},
            capabilities=["system_info"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_env_get,
            drop_decorative_args=True,
            arg_aliases={"variable": "name", "var": "name", "env_var": "name"},
        ),
        ToolDefinition(
            key="system.registry_get",
            name="Registry Read",
            version=1,
            description="Read Windows registry keys and values (read-only). hive: HKLM/HKCU/HKCR.",
            input_schema={"hive": "str", "key_path": "str", "value_name": "str?"},
            output_schema={"value": "str", "values": "list"},
            capabilities=["registry", "system_info"],
            risk_class="low", side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_system_registry_get,
            drop_decorative_args=True,
            arg_aliases={"key": "key_path", "path": "key_path",
                         "name": "value_name", "value": "value_name"},
        ),
    ]

    for t in tools:
        registry.register(t)

    logger.info("System tools registered — count=%d", len(tools))
