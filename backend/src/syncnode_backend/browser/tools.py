"""
SyncNode — Playwright Browser Runtime.

Controls a local Chromium session for web automation.

Uses semantic locators:
  role, label, text, test-id, stable DOM attributes

Visual coordinate fallback only when semantic mechanisms fail.

POLICY:
  - Never click Send/Submit for external communication without approval
  - Never navigate to disallowed external URLs autonomously
  - All actions must be observable and verifiable
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_browser_context = None
_playwright_instance = None
_page = None
_browser = None


def _page_is_alive(page) -> bool:
    """True if the cached page/context is still usable (not closed/crashed)."""
    if page is None:
        return False
    try:
        if page.is_closed():
            return False
        ctx = page.context
        if ctx is None:
            return False
        browser = ctx.browser
        if browser is not None and not browser.is_connected():
            return False
        return True
    except Exception:  # noqa: BLE001 - any probe error => treat as dead
        return False


async def _launch_new_page():
    """Start Playwright + launch a fresh browser/context/page."""
    global _browser_context, _playwright_instance, _page, _browser
    from playwright.async_api import async_playwright

    from syncnode_backend.config.settings import settings
    browser_type = settings.syncnode_browser_type
    headless = settings.syncnode_browser_headless

    _playwright_instance = await async_playwright().start()
    browser_obj = getattr(_playwright_instance, browser_type)
    _browser = await browser_obj.launch(headless=headless)
    _browser_context = await _browser.new_context()
    _page = await _browser_context.new_page()
    logger.info(f"Browser started — browser_type={browser_type} headless={headless}")
    return _page


async def get_browser_page(force_new: bool = False, require_existing: bool = False):
    """Get or create the Playwright browser page.

    Self-heals: if the cached page/context/browser has been closed or crashed
    (a prior run left it dead), tear the stale objects down and launch a fresh
    session instead of returning a dead handle whose goto() raises
    "Target page, context or browser has been closed".

    require_existing=True: return the cached page only if it is alive; never
    relaunch. Returns None if the page is dead. Used by verification so it
    never reads a freshly-launched blank page as evidence.
    """
    if not force_new and _page_is_alive(_page):
        return _page
    if require_existing:
        return None  # dead page — caller handles gracefully
    await close_browser()
    return await _launch_new_page()


async def close_browser() -> None:
    """Gracefully tear down the browser session (best-effort, never raises)."""
    global _browser_context, _playwright_instance, _page, _browser
    for closer in (
        lambda: _page.close() if _page else None,
        lambda: _browser_context.close() if _browser_context else None,
        lambda: _browser.close() if _browser else None,
        lambda: _playwright_instance.stop() if _playwright_instance else None,
    ):
        try:
            res = closer()
            if res is not None:
                await res
        except Exception:  # noqa: BLE001 - stale handle; ignore during teardown
            pass
    _page = None
    _browser_context = None
    _browser = None
    _playwright_instance = None
    logger.info("Browser closed")


_MAIL_COMPOSE_HINTS = ("mail", "compose", "webmail", "gmail", "outlook", "draft")


def _resolve_navigation_url(url: str) -> str:
    """Redirect mail-compose destinations to the configured local compose page.

    When redirecting, preserve any Gmail compose query parameters (to, subject,
    body) by appending them to the local fixture URL so compose.html can
    pre-fill the fields on load.
    """
    from syncnode_backend.config.settings import settings
    local = settings.syncnode_mail_compose_url
    if not local:
        return url
    low = (url or "").lower()
    if any(h in low for h in _MAIL_COMPOSE_HINTS):
        # Extract Gmail compose params and forward them to the local fixture.
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urljoin
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=False)
            # Gmail uses 'to', 'subject', 'body' directly; some clients use 'fs','view' etc. — keep only compose fields
            forward = {}
            for key in ("to", "subject", "body", "cc", "bcc"):
                if key in params:
                    forward[key] = params[key][0]  # take first value
            if forward:
                target = local + ("&" if "?" in local else "?") + urlencode(forward)
                logger.info(f"Redirecting mail-compose navigation {url!r} -> local fixture (with {list(forward.keys())} params)")
                return target
        except Exception:
            pass
        logger.info(f"Redirecting mail-compose navigation {url!r} -> local fixture")
        return local
    return url


async def tool_browser_navigate(url: str) -> dict[str, Any]:
    """Navigate to a URL (mail-compose targets redirect to the local fixture).

    If the cached browser turns out to be dead mid-call (Playwright raises
    "Target page, context or browser has been closed"), relaunch a fresh page
    once and retry — so a stale session from a prior run never fails the step.
    """
    target = _resolve_navigation_url(url)
    page = await get_browser_page()
    try:
        await page.goto(target, wait_until="domcontentloaded", timeout=30000)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "closed" in msg or "crash" in msg or "disconnected" in msg:
            logger.warning("Browser was dead on navigate; relaunching and retrying")
            page = await get_browser_page(force_new=True)
            await page.goto(target, wait_until="domcontentloaded", timeout=30000)
        else:
            raise
    return {"url": page.url, "title": await page.title(), "navigated": True,
            "requested_url": url}


async def tool_browser_get_url() -> dict[str, Any]:
    """Return the current page URL and title."""
    page = await get_browser_page()
    return {"url": page.url, "title": await page.title()}


async def tool_browser_screenshot(output_path: str, label: Optional[str] = None) -> dict[str, Any]:
    """Take a screenshot of the current browser page."""
    from syncnode_backend.documents.tools import _safe_path
    p = _safe_path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    page = await get_browser_page()
    await page.screenshot(path=str(p), full_page=False)
    data = p.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return {"path": str(p), "sha256": digest, "size_bytes": len(data), "label": label}


async def tool_browser_find_element(
    role: Optional[str] = None,
    name: Optional[str] = None,
    text: Optional[str] = None,
    selector: Optional[str] = None,
) -> dict[str, Any]:
    """Find an element using semantic locators."""
    page = await get_browser_page()
    try:
        if role and name:
            locator = page.get_by_role(role, name=name)
        elif role:
            locator = page.get_by_role(role)
        elif name:
            locator = page.get_by_label(name)
        elif text:
            locator = page.get_by_text(text, exact=False)
        elif selector:
            locator = page.locator(selector)
        else:
            return {"found": False, "error": "No locator specified"}

        count = await locator.count()
        if count > 0:
            el = locator.first
            is_visible = await el.is_visible()
            return {"found": True, "count": count, "visible": is_visible}
        return {"found": False, "count": 0}
    except Exception as exc:
        return {"found": False, "error": str(exc)}


async def tool_browser_click(
    role: Optional[str] = None,
    name: Optional[str] = None,
    text: Optional[str] = None,
    selector: Optional[str] = None,
) -> dict[str, Any]:
    """Click an element using semantic locators."""
    page = await get_browser_page()
    try:
        if role and name:
            locator = page.get_by_role(role, name=name)
        elif name:
            locator = page.get_by_label(name)
        elif text:
            locator = page.get_by_text(text)
        elif selector:
            locator = page.locator(selector)
        else:
            return {"clicked": False, "error": "No locator specified"}

        await locator.first.click(timeout=10000)
        return {"clicked": True}
    except Exception as exc:
        return {"clicked": False, "error": str(exc)}


async def tool_browser_type(
    text: str,
    role: Optional[str] = None,
    name: Optional[str] = None,
    selector: Optional[str] = None,
    _fill_fields: Optional[dict] = None,
) -> dict[str, Any]:
    """Type text into an element, resolving the target robustly.

    When `_fill_fields` is provided (a dict of field_id -> text), each field is
    filled sequentially. This is used internally when a planner collapses
    To/Subject/Body into a single step.
    """
    page = await get_browser_page()

    # ── Multi-field fill (collapsed compose step) ──────────────────────────
    if _fill_fields:
        filled = {}
        for field_id, field_text in _fill_fields.items():
            if not field_text:
                continue
            try:
                loc = page.locator(f"#{field_id}")
                if await loc.count() > 0:
                    await loc.first.fill(str(field_text), timeout=4000)
                    filled[field_id] = len(str(field_text))
            except Exception:  # noqa: BLE001
                pass
        total = sum(filled.values())
        return {"typed": True, "chars": total, "fields": list(filled.keys())}

    # ── Single-field fill (normal case) ────────────────────────────────────
    def _looks_like_css(s: str) -> bool:
        s = s.strip()
        return bool(s) and (s[0] in "#.[" or s.split()[0].islower() and " " not in s)

    # Map common semantic field names to concrete field ids (compose form).
    # Order matters: check body/subject BEFORE generic "email" so that
    # "email_body" resolves to "body" not "to".
    def _semantic_id(s: str) -> Optional[str]:
        low = s.lower().strip()
        # Body must come first — "email_body" contains "body" AND "email";
        # we want body, not to.
        if any(k in low for k in ("body", "message")) and "subject" not in low:
            return "body"
        if "subject" in low:
            return "subject"
        # Only match "to" / recipient when it's clearly the recipient field,
        # not a substring of "email_body" or "email_content".
        if low in ("to", "to_field", "recipient", "email_address", "email address"):
            return "to"
        if low.startswith("to ") or low.startswith("to_") or low == "email":
            return "to"
        if "recipient" in low or "address" in low:
            return "to"
        return None

    # Build an ordered list of candidate locators from whatever hints we have.
    candidates = []
    hints = [h for h in (name, selector) if h]
    if role and name:
        candidates.append(page.get_by_role(role, name=name))
    for h in hints:
        sem = _semantic_id(h)
        if sem:
            candidates.append(page.locator(f"#{sem}"))
        if _looks_like_css(h):
            candidates.append(page.locator(h))
        else:
            # Human phrasing like "To field" -> label "To".
            base = h.replace(" field", "").replace(" input", "").strip()
            candidates.append(page.get_by_label(base, exact=False))
            candidates.append(page.get_by_placeholder(base))
    try:
        for locator in candidates:
            try:
                await locator.first.fill(text, timeout=4000)
                return {"typed": True, "chars": len(text)}
            except Exception:  # noqa: BLE001 - try the next strategy
                continue
        # Last resort: type into the focused element.
        await page.keyboard.type(text)
        return {"typed": True, "chars": len(text), "fallback": "focused"}
    except Exception as exc:
        return {"typed": False, "error": str(exc)}


async def tool_browser_attach_file(
    file_path: str,
    selector: str = "",
) -> dict[str, Any]:
    """Attach one or more files to a file input.

    `file_path` may be a single path or several separated by ``|`` (or a JSON
    list). All must exist inside the workspace. selector is optional (falls back
    to the page's file input).
    """
    from syncnode_backend.documents.tools import _safe_path

    # Parse one-or-many paths.
    raw = file_path
    parts: list[str]
    if isinstance(raw, list):
        parts = [str(x) for x in raw]
    elif "|" in raw:
        parts = [x.strip() for x in raw.split("|") if x.strip()]
    else:
        parts = [raw]

    resolved = []
    for part in parts:
        p = _safe_path(part)
        if not p.exists():
            return {"attached": False, "error": f"File not found: {part}"}
        resolved.append(str(p))

    page = await get_browser_page()
    candidates = []
    if selector:
        candidates.append(selector)
    candidates.append("input[type=file]")
    last_err: Optional[str] = None
    for sel in candidates:
        try:
            file_input = page.locator(sel).first
            await file_input.set_input_files(resolved, timeout=5000)
            total = sum(_safe_path(r).stat().st_size for r in resolved)
            return {"attached": True, "files": resolved, "count": len(resolved),
                    "size_bytes": total, "selector": sel}
        except Exception as exc:  # noqa: BLE001 - try next candidate
            last_err = str(exc)
    return {"attached": False, "error": last_err}


async def tool_browser_get_dom_text(selector: Optional[str] = None) -> dict[str, Any]:
    """Get visible text from the page or a specific element."""
    page = await get_browser_page()
    try:
        if selector:
            el = page.locator(selector).first
            text = await el.inner_text(timeout=5000)
        else:
            text = await page.inner_text("body", timeout=5000)
        return {"text": text[:2000], "found": True}  # Truncate for safety
    except Exception as exc:
        return {"text": "", "found": False, "error": str(exc)}


def register_browser_tools(registry) -> None:
    """Register all browser tools."""
    from syncnode_backend.tools.registry import ToolDefinition

    tools = [
        ToolDefinition(
            key="browser.navigate",
            name="Browser Navigate",
            version=1,
            description="Navigate the browser to a URL",
            input_schema={"url": "str"},
            output_schema={"url": "str", "title": "str"},
            capabilities=["browser_navigation"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="idempotent",
            verification_strategy="always",
            handler=tool_browser_navigate,
            arg_aliases={"link": "url", "address": "url", "website": "url"},
        ),
        ToolDefinition(
            key="browser.screenshot",
            name="Browser Screenshot",
            version=1,
            description="Take a browser screenshot",
            input_schema={"output_path": "str"},
            output_schema={"path": "str", "sha256": "str"},
            capabilities=["browser_navigation"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_browser_screenshot,
            arg_aliases={"path": "output_path", "filename": "output_path",
                         "file_path": "output_path"},
        ),
        ToolDefinition(
            key="browser.find_element",
            name="Browser Find Element",
            version=1,
            description="Find a DOM element using semantic locators",
            input_schema={"role": "Optional[str]", "name": "Optional[str]", "text": "Optional[str]"},
            output_schema={"found": "bool", "visible": "bool"},
            capabilities=["dom_interaction"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_browser_find_element,
        ),
        ToolDefinition(
            key="browser.click",
            name="Browser Click",
            version=1,
            description="Click a DOM element",
            input_schema={"role": "Optional[str]", "name": "Optional[str]"},
            output_schema={"clicked": "bool"},
            capabilities=["dom_interaction"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_browser_click,
            arg_aliases={"label": "name", "button": "name", "element": "name",
                         "css_selector": "selector"},
            drop_decorative_args=True,
        ),
        ToolDefinition(
            key="browser.type",
            name="Browser Type",
            version=1,
            description="Type text into an element",
            input_schema={"text": "str", "name": "Optional[str]"},
            output_schema={"typed": "bool"},
            capabilities=["dom_interaction"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="non_idempotent",
            verification_strategy="always",
            handler=tool_browser_type,
            arg_aliases={"value": "text", "content": "text", "body": "text",
                         "message": "text", "label": "name", "field": "name",
                         "field_name": "name", "target": "name",
                         "placeholder": "name", "css_selector": "selector",
                         # Contextual hints the handler doesn't accept.
                         "field_type": "", "type": "", "action_sequence": "",
                         "actions": "", "steps": "", "sequence": ""},
            drop_decorative_args=True,
        ),
        ToolDefinition(
            key="browser.attach_file",
            name="Browser Attach File",
            version=1,
            description="Attach a local file to a file input",
            input_schema={"selector": "str", "file_path": "str"},
            output_schema={"attached": "bool"},
            capabilities=["file_attachment"],
            risk_class="medium",
            side_effect_type="REVERSIBLE_LOCAL",
            idempotency="idempotent",
            verification_strategy="always",
            handler=tool_browser_attach_file,
            arg_aliases={"path": "file_path", "filename": "file_path",
                         "file": "file_path", "document": "file_path",
                         "attachment": "file_path", "css_selector": "selector",
                         "attachment_selector": "selector", "input_selector": "selector",
                         "element": "selector", "field": "selector",
                         # Model sometimes emits a symbolic artifact reference
                         # alongside the real injected file_path. Drop these extras
                         # so the validator doesn't reject the whole call.
                         "file_artifact": "",
                         "artifact": "",
                         "artifact_path": "file_path",
                         "document_path": "file_path",
                         "attachment_path": "file_path",
                         },
            drop_decorative_args=True,
        ),
        ToolDefinition(
            key="browser.get_url",
            name="Browser Get URL",
            version=1,
            description="Get the current page URL",
            input_schema={},
            output_schema={"url": "str", "title": "str"},
            capabilities=["browser_navigation"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_browser_get_url,
        ),
        ToolDefinition(
            key="browser.get_dom_text",
            name="Browser Get DOM Text",
            version=1,
            description="Get visible text from the page",
            input_schema={"selector": "Optional[str]"},
            output_schema={"text": "str", "found": "bool"},
            capabilities=["dom_interaction"],
            risk_class="low",
            side_effect_type="READ_ONLY",
            idempotency="idempotent",
            verification_strategy="never",
            handler=tool_browser_get_dom_text,
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Browser tools registered — count={len(tools)}")