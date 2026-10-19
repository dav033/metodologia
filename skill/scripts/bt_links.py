"""Clickable ids in the terminal: wraps REQ-005, P-013, D-045, LG-001 in OSC 8 hyperlinks to the web's `/go/<id>`.

Only for an interactive terminal that can show them: never in redirected output (a pipe, a file, `--json`). The id
itself is the visible text, so a terminal without OSC 8 support shows exactly what it showed before.
`BITACORA_LINKS=0` turns it off, `=1` forces it on (tests, `script`); the port is `BITACORA_PORT` (default 8765).
"""
from __future__ import annotations

import os
import re
import sys

_ID = re.compile(r"(?<![\w/#-])((?:REQ|P|D|LG)-\d{3,})(?![\w-])")
ESC, BEL = "\x1b", "\x07"


def enabled(stream=None, env=None) -> bool:
    env = os.environ if env is None else env
    flag = env.get("BITACORA_LINKS")
    if flag in ("0", "1"):
        return flag == "1"
    stream = sys.stdout if stream is None else stream
    try:
        tty = stream.isatty()
    except (AttributeError, ValueError):
        tty = False
    return bool(tty) and env.get("TERM", "dumb") not in ("dumb", "linux", "")


def url(ident: str, project: str | None = None, env=None) -> str:
    env = os.environ if env is None else env
    base = f"http://127.0.0.1:{env.get('BITACORA_PORT', '8765')}/go/"
    return base + (f"{project}/" if project else "") + ident


def osc8(text: str, target: str) -> str:
    return f"{ESC}]8;;{target}{BEL}{text}{ESC}]8;;{BEL}"


def linkify(text: str, project: str | None = None, *, stream=None, env=None) -> str:
    """`text` with every id as a hyperlink when the terminal can show them; unchanged otherwise."""
    if not enabled(stream, env):
        return text
    return _ID.sub(lambda m: osc8(m.group(1), url(m.group(1), project, env)), text)
