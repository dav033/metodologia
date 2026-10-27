"""Render a planning mockup and measure what the owner sees: contrast, alignment, padding, overflow and focus.

  uv run --with playwright python audit_mockup.py mockup.html [--browser /usr/bin/chromium] [--json out.json]

Measurements run with prefers-reduced-motion emulated, so animated mockups are judged in their settled state. It drives
the mockup's own selects (ids view, state, scene, theme; without a theme select it sets <html data-theme>)
through every view x state x theme, every dialog scene, at 1280 px and 390 px, and fails on:
  contrast     text under 4.5:1 (3:1 when large), placeholders included, in every theme
  non-text     a form control whose edge or fill is under 3:1 against what surrounds it
  focus        a keyboard stop whose look does not change on focus, or changes under 3:1 (Tab walk at desktop width
               on every rendered view, state, dialog and theme; no stop reached at all is a failure)
  alignment    a centred column with text on another x outside it, or one lone centred line among left-aligned lines
               of the same frame (the «¿Olvidaste tu contraseña?» case)
  padding      a framed box (visible border or fill) whose content comes closer than 12 px to its edge (8 px for
               controls, 6 px for badges), field text under 6 px from its edge, text under 12 px from a phone's edge
  unmeasured   a text colour the browser reports in a form that could not be read
  overflow     horizontal scrolling of the page, with the elements that stick out
  motion       a finite animation still running 120 ms after load under prefers-reduced-motion (no reduced-motion handling)
  layout-shift cumulative layout shift over 0.1 while the page loads with motion (content jumping as it animates in)
  static       network references (http/https src, href, url(), @import); the kit block missing or outdated is a warning
The planning chrome (the block holding the selects) is left out. Exit 0 = measured and clean, 1 = problems found,
2 = not measured (no Playwright, no browser, nothing rendered): never report a pass you did not get."""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import shutil
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent

PROBES = (KIT / "audit_probes.js").read_text(encoding="utf-8")   # window.__audit.measure() / .focus()
FOCUS_CAP = 60

# measure the end state, not a frame of an entrance animation (infinite loaders cannot finish: leave them)
SETTLE = """() => { document.documentElement.style.scrollBehavior = 'auto';
  for (const a of document.getAnimations()) { try { if (a.effect && a.effect.getComputedTiming().iterations !== Infinity) a.finish(); } catch (e) {} } }"""

NETWORK = re.compile(r"""(?:\bsrc\s*=\s*["']?\s*(?:https?:)?//|<link[^>]+href\s*=\s*["']?\s*(?:https?:)?//|url\(\s*["']?\s*(?:https?:)?//|@import\s+["']?(?:url\()?\s*["']?\s*(?:https?:)?//)""", re.I)


def static_checks(html: str) -> tuple[list[str], list[str]]:
    """(failures, warnings) found without a browser."""
    fails, warns = [], []
    for m in NETWORK.finditer(html):
        fails.append(f"network reference: {html[m.start():m.start() + 70]!r}")
    if 'data-kit="real"' in html:
        pass                                      # built by real/build.mjs from the installed libraries: nothing to inline
    elif 'data-kit="css"' not in html:
        warns.append("no kit block: build the mockup with real/build.mjs (or, fallback kit, write <!-- kit:css --> and run kit/inline.py)")
    else:
        sys.path.insert(0, str(KIT))
        import inline  # noqa: PLC0415 - the sibling tool
        if inline.inline(html) != html:
            warns.append("kit block is older than the kit: run kit/inline.py on the mockup")
    for sel in ("view", "state", "theme") if 'data-kit="real"' not in html else ():   # real mockups draw them at load
        if not re.search(rf'<select[^>]*\bid=["\']{sel}["\']', html):
            warns.append(f"no <select id=\"{sel}\">: the plan page cannot drive this axis")
    return fails, warns


def find_browser(explicit: str) -> str | None:
    if explicit:
        return explicit
    for env in ("AUDIT_BROWSER", "CHROME_PATH"):
        if os.environ.get(env):
            return os.environ[env]
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None                                   # Playwright's own bundled Chromium, if installed


def options(page, sel: str) -> list[str]:
    if not page.query_selector(f"select#{sel}"):
        return []
    return page.eval_on_selector(f"select#{sel}", "s => [...s.options].filter(o => !o.disabled).map(o => o.value)")


def combos(views, states, scenes, themes, cap: int) -> tuple[list[tuple], int, object]:
    """Every theme x view x state with no scene, plus every scene on each view's first state; trimmed evenly to `cap`."""
    views, states, scenes, themes = views or [None], states or [None], scenes or [None], themes or [None]
    base_scene = "" if "" in scenes else scenes[0]
    out = [(t, v, s, base_scene) for t, v, s in itertools.product(themes, views, states)]
    out += [(t, v, states[0], c) for t, v, c in itertools.product(themes, views, scenes) if c not in ("", None, base_scene)]
    total = len(out)
    if len(out) > cap:
        step = len(out) / cap
        out = [out[int(i * step)] for i in range(cap)]
    return out, total, base_scene


def set_axis(page, sel: str, value) -> None:
    """Set a planning select the way the plan page does (value + input/change events), even when the mockup disables it."""
    if value is None:
        return
    page.evaluate("""([id, v]) => { const s = document.getElementById(id);
      if (!s || s.tagName !== 'SELECT' || ![...s.options].some(o => o.value === v)) return;
      s.value = v; s.dispatchEvent(new Event('input', {bubbles: true})); s.dispatchEvent(new Event('change', {bubbles: true})); }""", [sel, value])


def walk_focus(page, stats: dict, note, tag: str) -> None:
    """Tab through the screen from the top; every stop must show an indicator that changes on focus and reaches 3:1."""
    page.evaluate("() => { document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); }")
    first, stops, seen = None, 0, set()
    for _ in range(FOCUS_CAP):
        page.keyboard.press("Tab")
        info = page.evaluate("() => window.__audit.focus()")
        if not info:
            return
        if info.get("skip"):
            continue
        if first == info["key"] or info["key"] in seen:   # focus cycled (a toast region hands focus back by script)
            return
        first = first or info["key"]
        seen.add(info["key"])
        stops += 1
        stats["focus_stops"] += 1
        if info["ratio"] < 3:
            note("focus", {"el": info["el"], "ratio": info["ratio"],
                           "detail": "no visible change on focus" if not info["changed"] else f"focus indicator {info['ratio']}:1 (needs 3:1)"}, tag)
    stats["focus_capped"] += 1


def run(path: Path, browser_path: str | None, widths: list[int], cap: int) -> dict:
    try:
        from playwright.sync_api import Error as PwError, sync_playwright
    except ImportError:
        raise SystemExit("AUDIT NOT RUN: Playwright is not installed. Run it as "
                         f"`uv run --with playwright python {Path(__file__).name} {path}` (or pip install playwright).")
    found: dict[tuple, dict] = {}
    stats = {"combos": 0, "planned": 0, "texts": 0, "unknown": 0, "focus_stops": 0, "focus_capped": 0, "no_main": False}

    def note(kind, item, tag):
        key = (kind, item.get("el"), item.get("detail") or item.get("ratio") or item.get("px"))
        row = found.setdefault(key, {"kind": kind, **item, "where": tag, "times": 0})
        row["times"] += 1

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=browser_path) if browser_path else p.chromium.launch()
        except PwError as exc:
            raise SystemExit(f"AUDIT NOT RUN: could not start a browser ({str(exc).splitlines()[0]}). "
                             "Install Chromium or pass --browser /path/to/chromium.")
        for width in widths:
            page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
            page.goto(path.resolve().as_uri())
            page.wait_for_timeout(250)
            page.evaluate(PROBES)
            views, states, scenes, themes = (options(page, s) for s in ("view", "state", "scene", "theme"))
            if not themes:
                themes = ["light", "dark"]
                manual_theme = True
            else:
                manual_theme = False
            plan, total, base_scene = combos(views, states, scenes, themes, cap)
            stats["planned"] += total
            for t, v, s, c in plan:
                if manual_theme:
                    page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", t)
                else:
                    set_axis(page, "theme", t)
                set_axis(page, "view", v)
                set_axis(page, "state", s)
                if scenes:
                    set_axis(page, "scene", c)
                page.wait_for_timeout(150)                  # React re-renders after the change event; then settle twice
                page.evaluate(SETTLE)
                page.wait_for_timeout(30)
                page.evaluate(SETTLE)
                res = page.evaluate("() => window.__audit.measure()")
                stats["combos"] += 1
                stats["texts"] += res["texts"]
                stats["unknown"] += res["unknown"]
                stats["no_main"] = stats["no_main"] or not res["hasMain"]
                tag = f"{width}px theme={t} view={v} state={s}" + (f" scene={c}" if c and c != base_scene else "")
                for kind in ("contrast", "nontext", "alignment", "padding", "overflow", "unmeasured"):
                    for item in res[kind]:
                        note(kind, item, tag)
                if t == "dark":
                    for item in res["native"]:
                        note("advice", {"el": item["el"], "detail": "native checkbox/radio drawn by the browser; use the kit's .checkbox/.radio"}, tag)
                if width == max(widths):                  # every view, state and dialog is walked with Tab at desktop width
                    walk_focus(page, stats, note, tag)
            page.close()
        motion_pass(browser, path, max(widths), note)
        browser.close()
    return {"stats": stats, "findings": list(found.values())}


SHIFTS = """(() => { window.__cls = 0; try { new PerformanceObserver(l => { for (const e of l.getEntries())
  if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: 'layout-shift', buffered: true }); } catch (e) {} })();"""
RUNNING = """() => document.getAnimations().filter(a => { try { const t = a.effect.getComputedTiming();
  return a.playState === 'running' && t.iterations !== Infinity && t.duration > 150; } catch (e) { return false; } })
  .map(a => { const el = a.effect && a.effect.target; return el ? (el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
  (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : '')) : 'animation'; }).slice(0, 5)"""


def motion_pass(browser, path: Path, width: int, note) -> None:
    """Load once with motion (layout shift while it plays) and once with reduced motion (nothing finite may still be
    animating: entrance choreography must collapse to its end state)."""
    page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="no-preference")
    page.add_init_script(SHIFTS)
    page.goto(path.resolve().as_uri())
    page.wait_for_timeout(1600)
    cls = page.evaluate("() => window.__cls || 0")
    if cls > 0.1:
        note("layout-shift", {"el": "page load", "detail": f"cumulative layout shift {cls:.2f} while loading (needs ≤ 0.1): "
                              "reserve the space of what animates in"}, f"{width}px motion")
    page.close()
    page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
    page.goto(path.resolve().as_uri())
    page.wait_for_timeout(120)
    for el in page.evaluate(RUNNING):
        note("motion", {"el": el, "detail": "still animating under prefers-reduced-motion: show the end state instead"},
             f"{width}px reduced")
    page.close()


def report(path: Path, result: dict, fails: list[str], warns: list[str]) -> int:
    st, rows = result["stats"], result["findings"]
    problems = [r for r in rows if r["kind"] != "advice"]
    print(f"audit: {path.name} — {st['combos']} renders ({st['planned']} combinations planned), "
          f"{st['texts']} text measurements, {st['focus_stops']} focus stops")
    if st["unknown"]:
        warns = warns + [f"{st['unknown']} text measurements skipped: a gradient or image sits behind the text; check them by eye"]
    if st["planned"] > st["combos"]:
        warns = warns + [f"sampled {st['combos']} of {st['planned']} combinations; pass --max-combos {st['planned']} to render all"]
    if st["focus_capped"]:
        warns = warns + [f"{st['focus_capped']} focus walks stopped at {FOCUS_CAP} stops; later controls were not checked"]
    if st["no_main"]:
        warns = warns + ['no <main> or #app: wrap the product in <main id="app"> so the planning chrome is told apart']
    order = ["static", "contrast", "nontext", "focus", "alignment", "padding", "overflow", "unmeasured", "motion", "layout-shift", "advice"]
    for f in fails:
        print(f"- static: {f}")
    for kind in order[1:]:
        items = [r for r in rows if r["kind"] == kind]
        for r in items[:12]:
            detail = r.get("detail") or (f"{r['ratio']}:1 (needs {r['need']}:1)" if "need" in r else
                                         f"{r['ratio']}:1 (needs 3:1)" if "ratio" in r else f"{r.get('px')} px wider: {r.get('el')}")
            print(f"- {kind}: {r.get('el', '')} — {detail}  [{r['where']}{', ×' + str(r['times']) if r['times'] > 1 else ''}]")
        if len(items) > 12:
            print(f"  … and {len(items) - 12} more {kind} findings")
    for w in warns:
        print(f"warning: {w}")
    counts = {k: sum(r["kind"] == k for r in problems) for k in order[1:-1]}
    bad = {k: n for k, n in counts.items() if n}
    if fails:
        bad["static"] = len(fails)
    if st["focus_stops"] == 0:
        bad["focus not measured (no keyboard stop reached)"] = 1
    print("RESULT: " + ("FAIL — " + ", ".join(f"{k} {n}" for k, n in bad.items()) if bad else
                        "PASS — no contrast, non-text, focus, alignment, padding or overflow problems"))
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("html")
    ap.add_argument("--browser", default="")
    ap.add_argument("--widths", default="1280,390")
    ap.add_argument("--max-combos", type=int, default=240, help="renders per width (default 240)")
    ap.add_argument("--json", help="write the findings as JSON here")
    args = ap.parse_args(argv)
    path = Path(args.html)
    if not path.is_file():
        print(f"AUDIT NOT RUN: {path} does not exist")
        return 2
    fails, warns = static_checks(path.read_text(encoding="utf-8", errors="replace"))
    try:
        result = run(path, find_browser(args.browser), [int(w) for w in args.widths.split(",")], args.max_combos)
    except SystemExit as exc:
        print(exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - a crash is "not measured", never a pass
        print(f"AUDIT NOT RUN: {type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}")
        return 2
    if result["stats"]["combos"] == 0 or result["stats"]["texts"] == 0:
        print("AUDIT NOT RUN: nothing rendered or no text measured")
        return 2
    if args.json:
        Path(args.json).write_text(json.dumps({**result, "static": fails, "warnings": warns}, ensure_ascii=False, indent=1))
    return report(path, result, fails, warns)


if __name__ == "__main__":
    sys.exit(main())
