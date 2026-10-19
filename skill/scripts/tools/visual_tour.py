#!/usr/bin/env python3
"""Visual tour of the web service: every page, desktop and phone width, light and dark, as PNGs plus an overflow probe.

    python3 visual_tour.py [--base http://127.0.0.1:8765] [--out DIR] [--project P] [--req REQ-026] [--only PATTERN]

For each page it runs headless Chromium twice: once to take the screenshot and once with `?probe=1` to read
`<html data-overflow>` (pixels of horizontal overflow; > 0 is a defect). Pages are forced with `?theme=light|dark`
and kept static with `?live=0`. Writes `tour.json` next to the images. This script LOOKS; deciding whether a page is
right is the reviewer's job: open the PNGs. Headless Chromium starts with a 500 px minimum window: the overflow probe (`--dump-dom`)
measures at 500 px, and a 390 px screenshot is taken after the page loaded at 500 px (pages that size things at load can look off). Not part of the production package.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote

SIZES = {"desktop": (1280, 1400), "mobile": (390, 1400)}
THEMES = ("light", "dark")


def fetch_json(url: str):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode())


def pages(base: str, project: str | None, req: str | None) -> list[tuple[str, str]]:
    """(slug, path) for every page worth looking at, built from what the server actually has."""
    plans = fetch_json(f"{base}/api/plans").get("plans", [])
    plan = next((p for p in plans if p["project"] == project and p["req_id"] == req), None) or \
        next((p for p in plans if p["active"]), None) or (plans[0] if plans else None)
    project = project or (plan["project"] if plan else None)
    out = [("dashboard", "/"), ("plans", "/plans"), ("now", "/now"), ("flow", "/flow"), ("metrics", "/metrics")]
    if project:
        out += [(f"project-{tab}", f"/p/{quote(project)}?tab={tab}")
                for tab in ("overview", "pending", "plans", "requirements", "decisions", "summary")]
        out.append(("graph", f"/p/{quote(project)}/graph"))
    if plan:
        p, r = quote(plan["project"]), quote(plan["req_id"])
        out += [("plan-detail", f"/plans/{p}/{r}"), ("requirement", f"/p/{p}/req/{r}"),
                ("flow-run", f"/flow?scope=run:{p}/{r}")]
    return out


def framed(url: str, size: tuple[int, int], folder: Path) -> str:
    """A tiny page that shows `url` inside an iframe of exactly `size`: the page then lays out at that width from the
    first paint (headless Chromium would start at 500 px and shrink without a resize event)."""
    wrapper = folder / ".frame.html"
    wrapper.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#888}}'
                       f'iframe{{border:0;display:block}}</style><iframe src="{url}" width="{size[0]}" height="{size[1]}">'
                       f'</iframe>', encoding="utf-8")
    return wrapper.as_uri()


def shoot(chromium: str, url: str, png: Path, size: tuple[int, int]) -> bool:
    if size[0] < 500:
        url = framed(url, size, png.parent)
    cmd = [chromium, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
           f"--window-size={size[0]},{size[1]}", "--virtual-time-budget=4000", url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=90, check=False)
    except subprocess.TimeoutExpired:
        return False
    return png.exists()


def overflow(chromium: str, url: str, size: tuple[int, int]) -> int | None:
    cmd = [chromium, "--headless=new", "--no-sandbox", "--disable-gpu", "--dump-dom", f"--window-size={size[0]},{size[1]}",
           "--virtual-time-budget=5000", url + ("&" if "?" in url else "?") + "probe=1"]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False)
    except subprocess.TimeoutExpired:
        return None
    match = re.search(r'data-overflow="(-?\d+)"', done.stdout)
    return int(match.group(1)) if match else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="http://127.0.0.1:8765")
    parser.add_argument("--out", type=Path, default=Path.home() / "bitacora" / "metodologia" / "artifacts" /
                        f"superrr-visual-{dt.date.today().isoformat()}")
    parser.add_argument("--project")
    parser.add_argument("--req")
    parser.add_argument("--only", help="regex on the page slug")
    parser.add_argument("--chromium", default="chromium")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for slug, path in pages(args.base.rstrip("/"), args.project, args.req):
        if args.only and not re.search(args.only, slug):
            continue
        for size_name, size in SIZES.items():
            for theme in THEMES:
                sep = "&" if "?" in path else "?"
                url = f"{args.base.rstrip('/')}{path}{sep}theme={theme}&live=0"
                png = args.out / f"{slug}-{size_name}-{theme}.png"
                ok = shoot(args.chromium, url, png, size)
                over = overflow(args.chromium, url, size) if theme == "light" else None
                results.append({"page": slug, "path": path, "size": size_name, "theme": theme, "png": png.name,
                                "ok": ok, "overflow_px": over})
                print(f"{'ok ' if ok else 'ERR'} {png.name}" + (f"  overflow={over}" if over else ""), flush=True)
    index = args.out / "tour.json"
    if args.only and index.exists():                 # a partial run updates its own captures and keeps the rest
        try:
            kept = {r["png"]: r for r in json.loads(index.read_text(encoding="utf-8"))}
        except ValueError:
            kept = {}
        kept.update({r["png"]: r for r in results})
        results = list(kept.values())
    index.write_text(json.dumps(results, indent=1), encoding="utf-8")
    bad = [r for r in results if not r["ok"] or (r["overflow_px"] or 0) > 0]
    print(f"{len(results)} captures, {len(bad)} with a problem (screenshot failed or horizontal overflow)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
