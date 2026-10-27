"""The script that lets the plan page browse a Designer mockup (views, states, dialogs) without entering it.

Mockups are agent-written, self-contained HTML served sandboxed. The server appends `assets/mockup-bridge.js` to each one
at serving time; the page side is `assets/mockup-nav.js`. The mockup's own files are never rewritten.
"""
from __future__ import annotations

import re
from pathlib import Path

BRIDGE = Path(__file__).resolve().parent.parent / "assets" / "mockup-bridge.js"


def inject(html: str) -> str:
    """The mockup with the bridge appended before `</body>` (at the end when there is no body tag); idempotent."""
    if "__ppBridge" in html:
        return html
    try:
        script = f"<script>{BRIDGE.read_text(encoding='utf-8')}</script>"
    except OSError:
        return html
    found = list(re.finditer(r"</body\s*>", html, re.I))
    if found:
        at = found[-1].start()
        return html[:at] + script + html[at:]
    return html + script
