"""Render built gallery demos in Chromium and report the ones that crash, log errors or draw nothing.

  uv run --with playwright python smoke.py [--dist DIR] [--browser /usr/bin/chromium] [id ...]

Each `<dist>/<id>.js` is loaded with `<dist>/gallery.css` in a page like the gallery's preview, in light and dark.
Exit 0 = every demo rendered without errors, 1 = failures, 2 = not run (no build, no Playwright, no browser)."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--dist", default=str(Path(os.environ.get("BITACORA_KIT_WORKSPACE") or
                                               Path.home() / ".local/share/bitacora/kit-workspace") / "dist/gallery"))
    ap.add_argument("--browser", default=os.environ.get("AUDIT_BROWSER") or shutil.which("chromium") or "")
    ap.add_argument("--themes", default="light,dark")
    args = ap.parse_args(argv)
    dist = Path(args.dist)
    css = dist / "gallery.css"
    ids = args.ids or sorted(p.stem for p in dist.glob("*.js"))
    if not css.is_file() or not ids:
        print(f"SMOKE NOT RUN: no build in {dist}")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SMOKE NOT RUN: Playwright is not installed (uv run --with playwright python smoke.py)")
        return 2
    bad = 0
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        try:
            browser = p.chromium.launch(**({"executable_path": args.browser} if args.browser else {}),
                                        args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        except Exception as exc:  # noqa: BLE001 - not run, never a pass
            print(f"SMOKE NOT RUN: could not start a browser ({str(exc).splitlines()[0]})")
            return 2
        sheet = css.read_text(encoding="utf-8")
        for cid in ids:
            js = dist / f"{cid}.js"
            if not js.is_file():
                print(f"FAIL {cid}: not built")
                bad += 1
                continue
            for theme in args.themes.split(","):
                page_file = Path(tmp) / f"{cid}-{theme}.html"
                dark = ' class="dark"' if theme == "dark" else ""
                page_file.write_text(f'<!doctype html><html lang="es"{dark} data-theme="{theme}"><head><meta charset="utf-8">'
                                     f'<style>{sheet}</style></head><body><div id="root"></div><script>{js.read_text(encoding="utf-8")}</script></body></html>',
                                     encoding="utf-8")
                page = browser.new_page(viewport={"width": 1100, "height": 800})
                errors: list[str] = []
                page.on("pageerror", lambda e, errors=errors: errors.append(f"pageerror: {str(e)[:240]}"))
                page.on("console", lambda m, errors=errors: errors.append(f"console: {m.text[:240]}") if m.type == "error" else None)
                page.goto(page_file.as_uri() + f"?theme={theme}")   # the frame runtime reads the theme from the query
                page.wait_for_timeout(700)
                drawn = page.evaluate("() => { const r = document.getElementById('root'); return r ? r.getBoundingClientRect().height : 0; }")
                page.close()
                if errors or drawn < 40:
                    bad += 1
                    print(f"FAIL {cid} [{theme}]: " + ("; ".join(errors[:3]) if errors else f"draws nothing ({drawn:.0f} px)"))
                    break
            else:
                print(f"ok   {cid}")
        browser.close()
    print(f"smoke: {len(ids) - bad}/{len(ids)} demos render cleanly")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
