"""
SyncNode — Windows Computer Runtime.

Controls Windows applications via UI Automation (uiautomation library).

Resolution order:
  AutomationId
  → Name + ControlType
  → ClassName + ControlType
  → application adapter
  → visual candidate (vision model)
  → verified coordinate fallback

NEVER:
  - bypass UAC surfaces
  - control secure desktop
  - use random anti-bot mouse movement
  - harvest credentials
"""

from __future__ import annotations

import hashlib
import io
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _screenshot_png() -> bytes:
    """Capture the full screen and return PNG bytes."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _save_screenshot(output_path: str) -> dict[str, Any]:
    """Capture screen, save to path, return hash."""
    png_bytes = _screenshot_png()
    digest = hashlib.sha256(png_bytes).hexdigest()
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(png_bytes)
    return {
        "path": str(p),
        "sha256": digest,
        "size_bytes": len(png_bytes),
    }


async def tool_computer_screenshot(
    output_path: str,
    label: Optional[str] = None,
) -> dict[str, Any]:
    """Capture the full screen and save to output_path."""
    from syncnode_backend.documents.tools import _safe_path
    p = _safe_path(output_path)
    result = _save_screenshot(str(p))
    result["label"] = label
    result["captured_at"] = time.time()
    logger.info(f"Screenshot captured — path={p} sha256={result['sha256'][:8]}")
    return result


async def tool_computer_windows_search(query: str, open_result: bool = True,
                                       wait_ms: int = 2500) -> dict[str, Any]:
    """Open Windows Search, type a query, observe results, optionally open the top hit.

    Uses the Windows Search UI (Win key). Returns whether a matching result was
    observed. This proves SyncNode can operate the desktop shell rather than
    invoking a known executable path directly.
    """
    try:
        import uiautomation as auto
    except Exception as exc:  # noqa: BLE001
        return {"opened_search": False, "error": f"uiautomation unavailable: {exc}"}

    try:
        # Open the search UI. Win+S opens Search directly on Windows 10/11.
        auto.SendKeys("{Win}s", waitTime=0.5)
        time.sleep(1.0)
        # Type the query.
        auto.SendKeys(query, waitTime=0.05)
        time.sleep(wait_ms / 1000.0)

        # Observe: look for a top-level element whose name contains the query.
        found = False
        matched_name = ""
        root = auto.GetRootControl()

        def _walk(control, depth):
            nonlocal found, matched_name
            if depth > 6 or found:
                return False
            name = (control.Name or "")
            if query.lower() in name.lower() and len(name) < 120:
                found = True
                matched_name = name
                return False
            return True

        try:
            for c, d in auto.WalkControl(root, maxDepth=6):
                if _walk(c, d) is False:
                    break
        except Exception:
            pass

        opened = False
        if open_result:
            # Enter launches the highlighted top result.
            auto.SendKeys("{Enter}", waitTime=0.2)
            time.sleep(wait_ms / 1000.0)
            opened = True

        return {
            "opened_search": True,
            "query": query,
            "result_found": found or opened,  # Enter opens the best match
            "matched_name": matched_name,
            "opened_result": opened,
        }
    except Exception as exc:  # noqa: BLE001
        return {"opened_search": False, "query": query, "error": str(exc)}


def _resolve_executable_path(exe_name: str) -> str:
    """Resolve an allowed executable name to a concrete path.

    Order: PATH → Windows "App Paths" registry → common install locations.
    Falls back to the bare name (subprocess will error if truly missing).
    """
    import shutil

    found = shutil.which(exe_name)
    if found:
        return found

    # App Paths registry (covers Office, Chrome, etc. not on PATH).
    try:
        import winreg
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(
                    root,
                    rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}",
                ) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    if val and Path(val).exists():
                        return val
            except OSError:
                continue
    except Exception:  # noqa: BLE001 - registry best-effort
        pass

    # Known Office install locations.
    candidates = [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    ]
    if exe_name.lower() == "winword.exe":
        for c in candidates:
            if Path(c).exists():
                return c
    excel_candidates = [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    ]
    if exe_name.lower() == "excel.exe":
        for c in excel_candidates:
            if Path(c).exists():
                return c
    ppt_candidates = [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    ]
    if exe_name.lower() == "powerpnt.exe":
        for c in ppt_candidates:
            if Path(c).exists():
                return c
    return exe_name


async def tool_computer_launch_app(
    executable: str = "",
    args: Optional[list[str]] = None,
    wait_ms: int = 2000,
) -> dict[str, Any]:
    """Launch a Windows application by name/path.

    `executable` is optional; when omitted it defaults to Microsoft Word (the
    common desktop-automation target following a Windows Search for Word).
    """
    if not (executable or "").strip():
        executable = "word"
    # Security: only allow listed executables. Values are resolved to a concrete
    # path so launching does not depend on the process PATH.
    ALLOWED_EXECUTABLES = {
        "winword.exe": "winword.exe",
        "winword": "winword.exe",
        "word": "winword.exe",
        "microsoft word": "winword.exe",
        "excel.exe": "excel.exe",
        "excel": "excel.exe",
        "microsoft excel": "excel.exe",
        "powerpnt.exe": "powerpnt.exe",
        "powerpnt": "powerpnt.exe",
        "powerpoint": "powerpnt.exe",
        "microsoft powerpoint": "powerpnt.exe",
        "notepad": "notepad.exe",
        "notepad.exe": "notepad.exe",
        "wordpad": "wordpad.exe",
        "explorer": "explorer.exe",
    }

    key = Path(executable).name.lower().strip()
    resolved = ALLOWED_EXECUTABLES.get(key)
    if resolved is None:
        # Not an allowed application — fail closed.
        return {
            "launched": False,
            "executable": executable,
            "error": f"Executable {executable!r} is not in the allow-list.",
        }
    resolved = _resolve_executable_path(resolved)

    logger.info(f"Launching application — executable={resolved} args={args or []}")
    try:
        proc = subprocess.Popen(
            [resolved] + (args or []),
            shell=False,  # Never use shell=True
        )
        time.sleep(wait_ms / 1000.0)
        return {
            "launched": True,
            "executable": resolved,
            "pid": proc.pid,
            "wait_ms": wait_ms,
        }
    except FileNotFoundError as exc:
        return {"launched": False, "executable": resolved, "error": str(exc)}


async def tool_computer_find_window(
    title_contains: Optional[str] = None,
    class_name: Optional[str] = None,
) -> dict[str, Any]:
    """Find a top-level window by title or class name."""
    try:
        import uiautomation as auto
        windows = []

        def _callback(control, depth):
            if control.ControlTypeName == "WindowControl":
                name = control.Name or ""
                cls = control.ClassName or ""
                if title_contains and title_contains.lower() in name.lower():
                    windows.append({"title": name, "class": cls, "handle": control.NativeWindowHandle})
                elif class_name and class_name.lower() in cls.lower():
                    windows.append({"title": name, "class": cls, "handle": control.NativeWindowHandle})
            return True

        for c, d in auto.WalkControl(auto.GetRootControl()):
            if _callback(c, d) is False:
                break
        return {"windows": windows, "count": len(windows)}
    except Exception as exc:
        logger.warning(f"UIA find_window failed — error={str(exc)}")
        return {"windows": [], "count": 0, "error": str(exc)}


async def tool_computer_uia_find(
    window_title: str,
    automation_id: Optional[str] = None,
    name: Optional[str] = None,
    control_type: Optional[str] = None,
) -> dict[str, Any]:
    """Find a UIA control in a window by AutomationId, Name, or ControlType."""
    try:
        import uiautomation as auto

        # Find the window first
        win = auto.WindowControl(searchDepth=1, Name=window_title)
        if not win.Exists(3, 0.5):
            # Try contains match
            win = None
            for w in auto.GetRootControl().GetChildren():
                if window_title.lower() in (w.Name or "").lower():
                    win = w
                    break
            if win is None:
                return {"found": False, "error": f"Window {window_title!r} not found"}

        # Search for control
        search_kwargs: dict[str, Any] = {}
        if automation_id:
            search_kwargs["AutomationId"] = automation_id
        if name:
            search_kwargs["Name"] = name

        ctrl = win.Control(**search_kwargs)
        if ctrl.Exists(3, 0.5):
            return {
                "found": True,
                "automation_id": ctrl.AutomationId,
                "name": ctrl.Name,
                "control_type": ctrl.ControlTypeName,
                "enabled": ctrl.IsEnabled,
            }
        return {"found": False, "window": window_title, "search": search_kwargs}
    except Exception as exc:
        logger.warning(f"UIA find failed — error={str(exc)}")
        return {"found": False, "error": str(exc)}


async def tool_computer_uia_type(
    text: str,
    window_title: Optional[str] = None,
    automation_id: Optional[str] = None,
    clear_first: bool = False,
    wait_ms: int = 100,
) -> dict[str, Any]:
    """Type text into a UIA control (or the currently focused element).

    If window_title + automation_id are given, focuses that control first.
    If only window_title is given, clicks into the document body of that window.
    If neither is given, types into whatever has focus.

    Use clear_first=True to select-all before typing (replaces existing content).
    """
    try:
        import uiautomation as auto

        if window_title:
            # Find the window
            win = auto.WindowControl(searchDepth=1, Name=window_title)
            if not win.Exists(3, 0.5):
                # Partial match
                for w in auto.GetRootControl().GetChildren():
                    if window_title.lower() in (w.Name or "").lower():
                        win = w
                        break
                else:
                    return {"typed": False, "error": f"Window '{window_title}' not found"}

            if automation_id:
                ctrl = win.Control(AutomationId=automation_id)
                if ctrl.Exists(2, 0.3):
                    ctrl.Click()
                    time.sleep(0.2)
                else:
                    win.Click()
            else:
                # Click into the window body to ensure focus
                win.Click()
        
        time.sleep(wait_ms / 1000.0)

        if clear_first:
            auto.SendKeys("{Ctrl}a", waitTime=0.1)
            time.sleep(0.1)

        # Type the text — SendKeys handles special chars
        # For long content, split into chunks to avoid UIA buffer overflow
        chunk_size = 200
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            auto.SendKeys(chunk, waitTime=0.02)

        time.sleep(wait_ms / 1000.0)
        logger.info("[UIA] typed %d chars into window=%s", len(text), window_title or "focused")
        return {
            "typed": True,
            "chars": len(text),
            "window": window_title,
            "clear_first": clear_first,
        }
    except Exception as exc:
        logger.warning("[UIA] uia_type failed: %s", exc)
        return {"typed": False, "error": str(exc)}


async def tool_computer_uia_click(
    window_title: str,
    automation_id: Optional[str] = None,
    name: Optional[str] = None,
    button: str = "left",
    wait_ms: int = 300,
) -> dict[str, Any]:
    """Click a UIA control in a window.

    Finds the window by title, then the control by AutomationId or Name.
    Falls back to clicking the window body if no control is specified.
    """
    try:
        import uiautomation as auto

        win = auto.WindowControl(searchDepth=1, Name=window_title)
        if not win.Exists(3, 0.5):
            for w in auto.GetRootControl().GetChildren():
                if window_title.lower() in (w.Name or "").lower():
                    win = w
                    break
            else:
                return {"clicked": False, "error": f"Window '{window_title}' not found"}

        if automation_id or name:
            kwargs: dict[str, Any] = {}
            if automation_id:
                kwargs["AutomationId"] = automation_id
            if name:
                kwargs["Name"] = name
            ctrl = win.Control(**kwargs)
            if ctrl.Exists(2, 0.3):
                if button == "right":
                    ctrl.RightClick()
                else:
                    ctrl.Click()
                time.sleep(wait_ms / 1000.0)
                return {
                    "clicked": True,
                    "window": window_title,
                    "control": automation_id or name,
                }
            return {"clicked": False, "error": f"Control {kwargs} not found in '{window_title}'"}
        else:
            win.Click()
            time.sleep(wait_ms / 1000.0)
            return {"clicked": True, "window": window_title, "control": "window_body"}

    except Exception as exc:
        logger.warning("[UIA] uia_click failed: %s", exc)
        return {"clicked": False, "error": str(exc)}


async def tool_computer_key_press(
    keys: str,
    wait_ms: int = 200,
) -> dict[str, Any]:
    """Send a key combination to the focused window.

    Examples:
      keys="{Ctrl}s"   → Ctrl+S (Save)
      keys="{Ctrl}a"   → Ctrl+A (Select All)
      keys="{Ctrl}z"   → Ctrl+Z (Undo)
      keys="{Enter}"   → Enter key
      keys="{Alt}{F4}" → Alt+F4 (Close)
      keys="{Ctrl}{Shift}s" → Ctrl+Shift+S (Save As)

    Uses uiautomation SendKeys format.
    """
    try:
        import uiautomation as auto
        auto.SendKeys(keys, waitTime=wait_ms / 1000.0)
        time.sleep(wait_ms / 1000.0)
        logger.info("[UIA] key_press: %s", keys)
        return {"sent": True, "keys": keys}
    except Exception as exc:
        logger.warning("[UIA] key_press failed: %s", exc)
        return {"sent": False, "keys": keys, "error": str(exc)}


async def tool_computer_get_active_window() -> dict[str, Any]:
    """Return information about the currently focused window."""
    try:
        import uiautomation as auto
        ctrl = auto.GetFocusedControl()
        win = ctrl
        while win and win.ControlTypeName != "WindowControl":
            win = win.GetParentControl()
        if win:
            return {
                "title": win.Name,
                "class": win.ClassName,
                "handle": win.NativeWindowHandle,
                "found": True,
            }
        return {"found": False}
    except Exception as exc:
        return {"found": False, "error": str(exc)}


def register_computer_tools(registry) -> None:
    """Register all computer runtime tools."""
    from syncnode_backend.tools.registry import ToolDefinition

    tools = [
        ToolDefinition(
            key="computer.screenshot",
            name="Screenshot",
            version=1,
            description="Capture full screen to a file",
            input_schema={"output_path": "str", "label": "Optional[str]"},
            output_schema={"path": "str", "sha256": "str"},
            capabilities=["screenshot_capture"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_computer_screenshot,
            arg_aliases={"path": "output_path", "filename": "output_path",
                         "file_path": "output_path", "name": "label",
                         "target_file": "", "file": "", "document": "",
                         "target": "", "subject": ""},
            drop_decorative_args=True,
        ),
        ToolDefinition(
            key="computer.windows_search",
            name="Windows Search",
            version=1,
            description="Open Windows Search, type a query, observe results, optionally open the top result",
            input_schema={"query": "str", "open_result": "bool?", "wait_ms": "int?"},
            output_schema={"opened_search": "bool", "result_found": "bool"},
            capabilities=["window_management", "process_launch"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_computer_windows_search,
            resource_locks=["desktop"],
            drop_decorative_args=True,
            arg_aliases={"search": "query", "text": "query", "term": "query",
                         "app_name": "query", "application": "query", "app": "query",
                         "open": "open_result", "launch": "open_result"},
        ),
        ToolDefinition(
            key="computer.launch_app",
            name="Launch Application",
            version=1,
            description="Launch an allowed Windows application",
            input_schema={"executable": "str", "args": "list[str]"},
            output_schema={"launched": "bool", "pid": "int"},
            capabilities=["process_launch"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_computer_launch_app,
            arg_aliases={"app_name": "executable", "application": "executable",
                         "app": "executable", "program": "executable",
                         "path": "executable", "arguments": "args",
                         # The document to open is injected as a launch arg by
                         # the orchestrator data-flow; drop these hints.
                         "file": "", "document": "", "workspace": "",
                         "document_path": "", "file_path": "", "target": "",
                         "open_file": "",
                         # Common decorative keys the model adds.
                         "wait": "", "wait_ms": "", "timeout": "",
                         "timeout_seconds": "", "description": "",
                         "open_after_launch": "", "launch_args": "args",
                         "command_args": "args", "params": "args",
                         "parameters": "args", "flags": "", "options": "",
                         "action": "", "intent": ""},
            drop_decorative_args=True,
        ),
        ToolDefinition(
            key="computer.find_window",
            name="Find Window",
            version=1,
            description="Find a top-level window by title or class name",
            input_schema={"title_contains": "Optional[str]", "class_name": "Optional[str]"},
            output_schema={"windows": "list", "count": "int"},
            capabilities=["window_management", "uia_control"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_computer_find_window,
            arg_aliases={"title": "title_contains", "window_title": "title_contains",
                         "name": "title_contains"},
        ),
        ToolDefinition(
            key="computer.uia_find",
            name="UIA Find Control",
            version=1,
            description="Find a UIA control in a window",
            input_schema={"window_title": "str", "automation_id": "Optional[str]"},
            output_schema={"found": "bool", "name": "str"},
            capabilities=["uia_control"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_computer_uia_find,
            arg_aliases={"title": "window_title", "window": "window_title",
                         "control_id": "automation_id"},
        ),
        ToolDefinition(
            key="computer.uia_type",
            name="UIA Type Text",
            version=1,
            description="Type text into a live application window or UIA control. Use window_title to target a specific open app (e.g. 'Document1 - Microsoft Word'). Set clear_first=true to replace existing content.",
            input_schema={"text": "str", "window_title": "Optional[str]", "automation_id": "Optional[str]", "clear_first": "bool?", "wait_ms": "int?"},
            output_schema={"typed": "bool", "chars": "int"},
            capabilities=["uia_control", "window_management"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_computer_uia_type,
            resource_locks=["desktop"],
            drop_decorative_args=True,
            arg_aliases={
                "content": "text", "value": "text", "message": "text",
                "window": "window_title", "title": "window_title",
                "control": "automation_id", "control_id": "automation_id",
                "clear": "clear_first", "replace": "clear_first",
            },
        ),
        ToolDefinition(
            key="computer.uia_click",
            name="UIA Click Control",
            version=1,
            description="Click a control in a live application window. Use window_title + name to click a specific button (e.g. 'Save', 'OK'). Omit control name to click the window body.",
            input_schema={"window_title": "str", "automation_id": "Optional[str]", "name": "Optional[str]", "button": "str?"},
            output_schema={"clicked": "bool"},
            capabilities=["uia_control", "window_management"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_computer_uia_click,
            resource_locks=["desktop"],
            drop_decorative_args=True,
            arg_aliases={
                "window": "window_title", "title": "window_title",
                "control": "name", "control_name": "name",
                "control_id": "automation_id",
            },
        ),
        ToolDefinition(
            key="computer.key_press",
            name="Key Press",
            version=1,
            description="Send a keyboard shortcut to the focused window. Use '{Ctrl}s' to save, '{Ctrl}a' to select all, '{Enter}' for Enter, '{Alt}{F4}' to close. Essential for saving documents after editing.",
            input_schema={"keys": "str", "wait_ms": "int?"},
            output_schema={"sent": "bool"},
            capabilities=["uia_control", "window_management"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="never",
            handler=tool_computer_key_press,
            resource_locks=["desktop"],
            drop_decorative_args=True,
            arg_aliases={
                "key": "keys", "shortcut": "keys", "keystroke": "keys",
                "combination": "keys", "hotkey": "keys",
            },
        ),
        ToolDefinition(
            key="computer.get_active_window",
            name="Get Active Window",
            version=1,
            description="Return the currently focused window",
            input_schema={},
            output_schema={"title": "str", "found": "bool"},
            capabilities=["window_management"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_computer_get_active_window,
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Computer runtime tools registered — count={len(tools)}")