"""The Designer's component kits as data, for the `/components` gallery (D-135).

Two kits: the REAL libraries (shadcn/ui on Base UI, Animate UI, Bencho, React Bits) installed in the local workspace
(`bt_kit_workspace`), catalogued in `real/manifest.json` and built into one bundle per demo; and the plain-HTML fallback
kit (`kit/`), whose snippets the gallery renders as they are. Everything is read from the skill's files and the built
workspace; ids are checked against a manifest, so no request can name a path."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import bt_kit_workspace

ROOT = Path(__file__).resolve().parent.parent / "agents/designer/skills/david-ui-kit"
KIT = ROOT / "kit"
REAL = ROOT / "real"
THEMES = ("light", "dark")
SOURCES = (("shadcn", "shadcn/ui"), ("animate-ui", "Animate UI"), ("bencho", "Bencho UI"), ("react-bits", "React Bits"))
MOTIONS = ("subtle", "natural", "expressive")
_EXAMPLE = re.compile(r"<!-- example: ([a-z0-9-]+) \| ([^>]+?) -->\n(.*?)(?=<!-- example: |\Z)", re.S)
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")


# ---------------------------------------------------------------- fallback kit (plain HTML snippets)
def _stamp() -> tuple:
    """Changes whenever a kit file changes, so a running server never serves a stale cache."""
    files = [KIT / "tokens.css", KIT / "components.css", KIT / "kit.js", *sorted((KIT / "components").glob("*"))]
    return tuple((p.name, p.stat().st_mtime_ns) for p in files if p.is_file())


@lru_cache(maxsize=4)
def _load(stamp: tuple) -> dict:
    data = json.loads((KIT / "components/manifest.json").read_text(encoding="utf-8"))
    for row in data["components"]:
        text = (KIT / "components" / row["file"]).read_text(encoding="utf-8")
        row["examples"] = [{"id": m.group(1), "title": m.group(2).strip(), "html": m.group(3).strip()}
                           for m in _EXAMPLE.finditer(text)]
    return data


def manifest() -> dict:
    return _load(_stamp())


def component(cid: str) -> dict | None:
    return next((row for row in manifest()["components"] if row["id"] == cid), None)


def reference(rid: str) -> tuple[dict, Path] | None:
    row = next((r for r in manifest()["references"] if r["id"] == rid), None)
    return (row, KIT / row["file"]) if row else None


def css() -> str:
    return (KIT / "tokens.css").read_text(encoding="utf-8") + "\n" + (KIT / "components.css").read_text(encoding="utf-8")


def js() -> str:
    return (KIT / "kit.js").read_text(encoding="utf-8")


def theme(value: str | None) -> str:
    return value if value in THEMES else "light"


def motion(value: str | None) -> str:
    return value if value in MOTIONS else "natural"


# ---------------------------------------------------------------- real libraries
def real_manifest() -> dict:
    """The catalogue merged with the last build: an entry whose demo did not build or is missing is a gap, whatever the
    manifest says (the gallery never shows a status it did not get)."""
    data = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))
    st = bt_kit_workspace.status()
    built = st["entries"]
    for row in data["entries"]:
        b = built.get(row["id"])
        row["built"] = bool(b and b.get("ok") and (bt_kit_workspace.dist() / f"{row['id']}.js").is_file())
        if row["status"] == "done" and not row["built"]:
            row["status"] = "gap"
            row["reason"] = (f"la demo no compiló: {b['error'].splitlines()[0][:200]}" if b and not b.get("ok") else
                             "el workspace no está instalado o construido: `bitacora.py components install`"
                             if not st["built"] else "falta su demo en el último build: `bitacora.py components build`")
    for ref in data["references"]:
        ref["built"] = (bt_kit_workspace.dist() / "reference" / f"{ref['id']}.html").is_file()
    data["workspace"] = st
    return data


def real_entry(cid: str) -> dict | None:
    if not _ID.match(cid or ""):
        return None
    return next((r for r in json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))["entries"] if r["id"] == cid), None)


def live_doc(cid: str, theme_: str | None, motion_: str | None, reduced: str | None) -> str | None:
    """A standalone page that renders one entry's demo with the real components, or None (unknown id or not built).
    Everything is inline: the gallery serves previews under a sandbox CSP that allows no external script."""
    row = real_entry(cid)
    bundle = bt_kit_workspace.dist() / f"{cid}.js"
    sheet = bt_kit_workspace.dist() / "gallery.css"
    if row is None or not bundle.is_file() or not sheet.is_file():
        return None
    t, m = theme(theme_), motion(motion_)
    dark = ' class="dark"' if t == "dark" else ""
    rm = " data-reduced-motion" if reduced == "1" else ""
    frame_css = (".kit-frame{display:flex;flex-direction:column;gap:2.5rem;padding:1.5rem}"
                 "@media (max-width:640px){.kit-frame{padding:1rem;gap:2rem}}")
    return (f'<!doctype html><html lang="es"{dark} data-theme="{t}" data-motion="{m}"{rm}><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(row["name"])}</title>'
            f'<style>{sheet.read_text(encoding="utf-8")}</style><style>{frame_css}</style></head>'
            f'<body><div id="root"></div><script>{bundle.read_text(encoding="utf-8")}</script></body></html>')


def real_reference(rid: str) -> Path | None:
    if not _ID.match(rid or ""):
        return None
    refs = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))["references"]
    if not any(r["id"] == rid for r in refs):
        return None
    path = bt_kit_workspace.dist() / "reference" / f"{rid}.html"
    return path if path.is_file() else None


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
