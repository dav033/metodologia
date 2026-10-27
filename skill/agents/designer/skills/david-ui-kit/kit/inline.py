"""Put the current kit inside a mockup, in place, so the file stays self-contained (no network, no links).

  python3 inline.py mockup.html [more.html ...]     # rewrite each file
  python3 inline.py --check mockup.html             # exit 1 when the file carries an outdated kit or none

Write `<!-- kit:css -->` inside <head> and `<!-- kit:js -->` before </body> once; the first run replaces each marker with a
`<style data-kit="css">` (tokens.css + components.css) or `<script data-kit="js">` (kit.js) block, and every later run
refreshes those blocks. Your own <style> for project tokens or screen layout goes AFTER the kit block, so it wins."""
from __future__ import annotations

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
CSS_BLOCK = re.compile(r'<!-- kit:css -->|<style data-kit="css">.*?</style>', re.S)
JS_BLOCK = re.compile(r'<!-- kit:js -->|<script data-kit="js">.*?</script>', re.S)


def kit_css() -> str:
    return (KIT / "tokens.css").read_text(encoding="utf-8") + "\n" + (KIT / "components.css").read_text(encoding="utf-8")


def kit_js() -> str:
    return (KIT / "kit.js").read_text(encoding="utf-8")


def inline(html: str) -> str:
    """The page with its kit markers or kit blocks replaced by the current kit; ValueError when it has no CSS marker."""
    if not CSS_BLOCK.search(html):
        raise ValueError('no <!-- kit:css --> marker or <style data-kit="css"> block')
    css = f'<style data-kit="css">\n{kit_css()}</style>'
    html = CSS_BLOCK.sub(lambda _: css, html, count=1)
    js = f'<script data-kit="js">\n{kit_js()}</script>'
    return JS_BLOCK.sub(lambda _: js, html, count=1)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = [Path(a) for a in argv if a != "--check"]
    if not files:
        print(__doc__)
        return 2
    bad = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        try:
            fresh = inline(text)
        except ValueError as exc:
            print(f"{path}: {exc}")
            bad += 1
            continue
        if check:
            if fresh != text:
                print(f"{path}: kit block is missing or outdated; run inline.py {path}")
                bad += 1
            continue
        if fresh != text:
            path.write_text(fresh, encoding="utf-8")
        print(f"{path}: kit inlined ({len(fresh) // 1024} KiB)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
