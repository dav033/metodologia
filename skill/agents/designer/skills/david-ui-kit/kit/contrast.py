"""WCAG 2.2 contrast of the kit's role tokens, in both themes.

  python3 contrast.py                 # the kit's tokens.css
  python3 contrast.py mockup.html     # the effective tokens of a mockup (kit block plus any project override after it)
  python3 contrast.py --all           # print every pair, not only failures

Text roles need 4.5:1 on every surface they sit on; control edges, focus rings, checked fills, chart marks and status dots
need 3:1 (WCAG 1.4.11). Blocks are applied in source order like the cascade: `:root` sets both themes, a selector with
`data-theme="dark"` (or light) sets that theme only; `@media` blocks are ignored (themes switch by `data-theme`, not by
`prefers-color-scheme`). Exit 1 when a pair fails or a role is missing."""
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT, EDGE = 4.5, 3.0
_TEXT_ON = {
    "foreground": ["background", "card", "popover", "muted", "accent", "secondary", "primary-soft", "destructive-soft",
                   "success-soft", "warning-soft", "info-soft"],
    "card-foreground": ["card"], "popover-foreground": ["popover"], "secondary-foreground": ["secondary"],
    "accent-foreground": ["accent"],
    "muted-foreground": ["background", "card", "popover", "muted", "accent", "sidebar"],
    "primary": ["background", "card", "popover", "muted", "primary-soft"],
    "primary-foreground": ["primary", "primary-hover"],
    "destructive": ["background", "card", "popover", "destructive-soft"],
    "destructive-foreground": ["destructive", "destructive-hover"],
    "success": ["background", "card", "popover", "success-soft"],
    "warning": ["background", "card", "popover", "warning-soft"],
    "info": ["background", "card", "popover", "info-soft"],
    "background": ["foreground"],                                      # tooltip: inverted surface
    "sidebar-foreground": ["sidebar", "sidebar-accent"], "sidebar-accent-foreground": ["sidebar-accent"],
    "sidebar-primary-foreground": ["sidebar-primary"], "sidebar-primary": ["sidebar"],
}
_EDGE_ON = {
    "input": ["background", "card", "popover", "muted", "sidebar"],    # outlined controls, unchecked boxes, switch track
    "ring": ["background", "card", "popover"], "sidebar-ring": ["sidebar"],
    "primary": ["background", "card", "popover", "muted"],             # checked fills, progress indicator on its track
    "chart-1": ["card", "background"], "chart-2": ["card", "background"], "chart-3": ["card", "background"],
    "chart-4": ["card", "background"], "chart-5": ["card", "background"],
    "success": ["card"], "warning": ["card"], "info": ["card"], "destructive": ["card"],
}
PAIRS = [(fg, bg, TEXT) for fg, bgs in _TEXT_ON.items() for bg in bgs] + \
        [(fg, bg, EDGE) for fg, bgs in _EDGE_ON.items() for bg in bgs]
ROLES = sorted({r for a, b, _ in PAIRS for r in (a, b)})


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(a: str, b: str) -> float:
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _blocks(css: str):
    """Top-level (selector, body) pairs in source order; @-rule blocks are skipped whole."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        open_ = css.find("{", i)
        if open_ < 0:
            return
        selector = css[i:open_].strip().split(";")[-1].strip()
        depth, j = 1, open_ + 1
        while j < n and depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        if not selector.startswith("@"):
            yield selector, css[open_ + 1:j - 1]
        i = j


def _themes(selector: str) -> set[str]:
    out = set()
    for part in selector.split(","):
        part = part.strip()
        m = re.search(r"data-theme\s*=\s*['\"]?(light|dark)", part)
        if m:
            out.add(m.group(1))
        elif re.fullmatch(r"(:root|html)", part):
            out.update(("light", "dark"))
    return out


def tokens(css: str) -> dict[str, dict[str, str]]:
    """Effective `--role: value` per theme after the cascade, with `var(--x)` references resolved."""
    out: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    for selector, body in _blocks(css):
        decls = dict(re.findall(r"--([\w-]+)\s*:\s*([^;]+)", body))
        for theme in _themes(selector):
            out[theme].update({k: v.strip() for k, v in decls.items()})
    for vals in out.values():
        for _ in range(4):
            for k, v in vals.items():
                m = re.fullmatch(r"var\(--([\w-]+)\)", v)
                if m and m.group(1) in vals:
                    vals[k] = vals[m.group(1)]
    return out


def css_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".html", ".htm"):
        return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S | re.I))
    return text


def check(css: str) -> tuple[list[tuple], list[str]]:
    """(rows, problems): rows are (theme, fg, bg, ratio, need) for every pair; problems name failures and missing roles."""
    rows, problems = [], []
    for theme, vals in tokens(css).items():
        missing = [r for r in ROLES if not re.fullmatch(r"#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", vals.get(r, ""))]
        problems += [f"{theme}: --{r} is missing or not a hex colour" for r in missing]
        for fg, bg, need in PAIRS:
            if fg in missing or bg in missing:
                continue
            got = ratio(vals[fg], vals[bg])
            rows.append((theme, fg, bg, got, need))
            if got < need:
                kind = "text" if need == TEXT else "non-text"
                problems.append(f"{theme}: --{fg} on --{bg} = {got:.2f}:1, {kind} needs {need}:1")
    return rows, problems


def main(argv: list[str]) -> int:
    show_all = "--all" in argv
    args = [a for a in argv if a != "--all"]
    path = Path(args[0]) if args else Path(__file__).with_name("tokens.css")
    rows, problems = check(css_of(path))
    if show_all:
        for theme, fg, bg, got, need in rows:
            print(f"{'ok  ' if got >= need else 'FAIL'} {theme:5} --{fg} on --{bg}: {got:.2f} (needs {need})")
    for p in problems:
        print("FAIL " + p)
    print(f"contrast: {len(rows)} pairs checked in light and dark, " +
          ("all pass" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
