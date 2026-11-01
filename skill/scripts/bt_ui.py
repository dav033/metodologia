"""`@bitacora/ui`: metodologia's component pool as one package, the single source of UI components (D-280).

The package lives in this repository at `skill/ui/` (package.json, `src/` with the shadcn/Base UI, Animate UI, Bencho
and React Bits sources, `src/styles.css` for structure, `src/theme.css` for the default role values) and project
themes at `skill/ui/themes/<project>.css`. Everything else consumes it:

- the kit workspace (`bt_kit_workspace`) is only the toolchain (node_modules, official installers); `real/build.mjs`
  resolves `@bitacora/ui/…` and the legacy `@/…` to this package;
- the local web serves the built pool at `/ui/<digest>/bitacora-ui.{js,css,json}` and a project's theme at
  `/ui/theme/<project>.css`; a mockup with a TSX source is rebuilt at view time against them (`live_mockup`), so an
  old mockup restyles when the pool or the theme changes. The self-contained HTML the Designer writes is the export
  and audit copy;
- child projects get the package written into their repository at `packages/bitacora-ui` (`bt_ui_sync`).

A project theme maps the project's own tokens and fonts onto the shadcn roles (`--background`, `--primary`, …,
`--ui-font-sans`); `import_theme` extracts it from the project's token source. Approval covers structure (the
contract); the look comes from the pool and the theme and may change without reapproval.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
UI = SKILL_ROOT / "ui"
SRC = UI / "src"
THEMES = UI / "themes"
NAME = "@bitacora/ui"
REAL = SKILL_ROOT / "agents/designer/skills/david-ui-kit/real"
BUILDER = REAL / "build.mjs"
_PROJECT = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
_DIGEST = re.compile(r"[0-9a-f]{12}\Z")
SKIP = {"README.md", ".DS_Store"}
# what a pool import is rewritten from: the workspace's `@/` alias (shadcn's) becomes a relative path inside the
# package, so a project whose own `@/` means its `src/` (pictures) never resolves a pool import into its own tree
_ALIAS = re.compile(r"""(from\s+|import\s+|import\(\s*)(["'])@/([^"']+)\2""")


# ------------------------------------------------------------------------------------------------ package
def package() -> dict:
    return json.loads((UI / "package.json").read_text(encoding="utf-8"))


def files(project: str | None = None) -> list[Path]:
    """The distributable files: package.json, LICENSES, `src/**` and, for a project, only its own theme."""
    out = [UI / "package.json"] + [p for p in sorted(SRC.rglob("*")) if p.is_file() and p.name not in SKIP]
    if (UI / "LICENSES.md").is_file():
        out.append(UI / "LICENSES.md")
    if project and (theme := theme_path(project)):
        out.append(theme)
    return out


def digest(paths: list[Path] | None = None) -> str:
    """12 hex of SHA-256 over every relative path and its bytes: changes with any edit to the pool."""
    h = hashlib.sha256()
    for p in paths if paths is not None else files():
        h.update(p.relative_to(UI).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:12]


def version() -> str:
    return f"{package()['version']}+{digest()}"


def rewrite_imports(text: str, file_dir: Path, src: Path = SRC) -> str:
    """`@/x` → the relative path from `file_dir` to `src/x` (extension dropped)."""
    def sub(m: re.Match) -> str:
        target = re.sub(r"\.(tsx?|jsx?)$", "", m.group(3))
        rel = os.path.relpath(src / target, file_dir).replace(os.sep, "/")
        return f"{m.group(1)}{m.group(2)}{rel if rel.startswith('.') else './' + rel}{m.group(2)}"
    return _ALIAS.sub(sub, text)


def import_sources(ws: Path | None = None, dest: Path = SRC) -> list[str]:
    """Copy the components the official installers wrote into the kit workspace (`components install`) into the
    package: `src/components/**`, `src/lib`, `src/hooks`, with `@/` imports made relative and each Bencho block
    importing its own stylesheet. The upstream refresh path; the package is the source afterwards."""
    import bt_kit_workspace
    ws = Path(ws or bt_kit_workspace.workspace())
    written = []
    for sub in ("components", "lib", "hooks"):
        base = ws / "src" / sub
        for f in sorted(base.rglob("*")) if base.is_dir() else []:
            if not f.is_file() or f.name in SKIP:
                continue
            out = dest / sub / f.relative_to(base)
            out.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix in (".ts", ".tsx"):
                text = rewrite_imports(f.read_text(encoding="utf-8"), out.parent, dest)
                css = f.with_suffix(".css")
                if "/bencho/" in f.as_posix() and css.is_file() and f'"./{css.name}"' not in text:
                    text = f'import "./{css.name}";\n' + text
                out.write_text(text, encoding="utf-8")
            else:
                shutil.copy2(f, out)
            written.append(out.relative_to(dest).as_posix())
    return written


def registry_key(spec: str) -> str | None:
    """The pool module a mockup import names: `@bitacora/ui/components/ui/button` or the legacy
    `@/components/ui/button` → `@bitacora/ui/components/ui/button`; anything else None."""
    if spec.startswith(NAME + "/"):
        rest = spec[len(NAME) + 1:]
    elif spec.startswith("@/"):
        rest = spec[2:]
    else:
        return None
    return f"{NAME}/" + re.sub(r"\.(tsx?|jsx?)$", "", rest)


# ------------------------------------------------------------------------------------------------ themes
def theme_path(project: str) -> Path | None:
    if not _PROJECT.match(project or ""):
        return None
    path = THEMES / f"{project}.css"
    return path if path.is_file() else None


def _fonts_of(text: str) -> list[str]:
    m = re.search(r"@mockup-fonts:\s*([^*]+)\*/", text)
    return [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []


def font_faces(packages: list[str]) -> str:
    """`@font-face` rules of fontsource packages installed in the kit workspace, latin subsets inlined as data: URIs
    (mockups are served sandboxed: no font request may leave the page)."""
    import bt_kit_workspace
    nm = bt_kit_workspace.workspace() / "node_modules"
    out = []
    for name in packages:
        if not re.fullmatch(r"@fontsource(-variable)?/[a-z0-9-]+", name):
            continue
        index = nm / name / "index.css"
        if not index.is_file():
            continue
        for block in re.findall(r"@font-face\s*{[^}]*}", index.read_text(encoding="utf-8")):
            if "latin" not in block or "latin-ext" in block:
                continue
            def inline(m: re.Match) -> str:
                f = (index.parent / m.group(1)).resolve()
                if not f.is_file() or nm.resolve() not in f.parents:
                    return "url()"
                return f"url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()})"
            out.append(re.sub(r"url\(\.?/?([^)]+\.woff2)\)", inline, re.sub(r",\s*url\([^)]+\.woff\)[^;]*", "", block)))
    return "\n".join(out)


def theme_css(project: str, *, fonts: bool = True) -> str:
    """A project's theme as served to mockups: the theme file plus its mockup fonts. Unknown project: empty (the
    pool's default roles apply)."""
    path = theme_path(project)
    if path is None:
        return ""
    text = path.read_text(encoding="utf-8")
    return (font_faces(_fonts_of(text)) + "\n" if fonts else "") + text


def _blocks(css: str, selector: re.Pattern) -> dict[str, str]:
    """Custom properties declared directly in the top-level blocks whose selector matches (in order; later wins)."""
    out: dict[str, str] = {}
    depth, start, head = 0, 0, ""
    clean = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for i, ch in enumerate(clean):
        if ch == "{":
            if depth == 0:
                head = clean[start:i].split(";")[-1].strip()
                body_start = i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                if selector.fullmatch(head):
                    for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", clean[body_start:i]):
                        out[name] = value.strip()
                start = i + 1
    return out


# the roles a theme also states as `r, g, b` triplets, for blocks that compose alpha themselves (Bencho, D-280)
TRIPLET_ROLES = ("--foreground", "--card", "--muted", "--primary-foreground")
_VAR = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)\Z")


def _triplet(value: str, *scopes: dict[str, str], depth: int = 0) -> str | None:
    """`r, g, b` of a colour value, following `var()` through the scopes (first wins); None when it is not a plain
    sRGB colour (hex or rgb()) — then the role gets no triplet rather than a wrong one."""
    value = value.strip()
    m = _VAR.match(value)
    if m and depth < 8:
        name, fallback = m.group(1), m.group(2)
        for scope in scopes:
            if name in scope:
                return _triplet(scope[name], *scopes, depth=depth + 1)
        return _triplet(fallback, *scopes, depth=depth + 1) if fallback else None
    hexa = re.fullmatch(r"#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value)
    if hexa:
        h = hexa.group(1)
        h = "".join(c * 2 for c in h) if len(h) <= 4 else h
        return ", ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    rgb = re.fullmatch(r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})\s*(?:[,/][^)]*)?\)", value)
    return ", ".join(rgb.groups()) if rgb else None


def _with_triplets(props: dict[str, str], *scopes: dict[str, str]) -> None:
    """Add `<role>-rgb` for each of TRIPLET_ROLES the theme resolves, unless the project states it."""
    for role in TRIPLET_ROLES:
        if f"{role}-rgb" in props:
            continue
        for scope in scopes:
            if role in scope:
                triplet = _triplet(scope[role], *scopes)
                if triplet:
                    props[f"{role}-rgb"] = triplet
                break


def import_theme(project: str, source: Path, mockup_fonts: list[str] | None = None,
                 sans: str = "", mono: str = "") -> Path:
    """Write `themes/<project>.css` from the project's token source (e.g. pictures' `src/app/globals.css`): every
    custom property of its top-level light block (`:root`) and dark block (`:root[data-theme="dark"]`,
    `[data-theme="dark"]` or `.dark`), so the project's own tokens and its role aliases come along. `sans`/`mono` set
    the font roles (default: the project's `@theme` `--font-sans`/`--font-mono` with system fallbacks)."""
    if not _PROJECT.match(project or ""):
        raise SystemExit(f"invalid project name: {project!r}")
    css = Path(source).read_text(encoding="utf-8")
    light = _blocks(css, re.compile(r":root"))
    dark = _blocks(css, re.compile(r":root\[data-theme=\"dark\"\]|\[data-theme=\"dark\"\]|\.dark"))
    themed = _blocks(css, re.compile(r"@theme(\s+inline)?"))
    if not light:
        raise SystemExit(f"{source}: no top-level :root block with custom properties")
    sans = sans or (themed.get("--font-sans", "") + ", " if themed.get("--font-sans") else "") + \
        "ui-sans-serif, system-ui, sans-serif"
    mono = mono or (themed.get("--font-mono", "") + ", " if themed.get("--font-mono") else "") + \
        "ui-monospace, SFMono-Regular, Menlo, monospace"
    light.setdefault("--ui-font-sans", sans)
    light.setdefault("--ui-font-mono", mono)
    light.setdefault("color-scheme", "light")
    _with_triplets(light, light)
    if dark:                                          # a dark role may be the light alias of a dark token
        dark.setdefault("color-scheme", "dark")
        _with_triplets(dark, dark, light)
    blob = Path(source).read_bytes()

    def block(selector: str, props: dict[str, str]) -> str:
        lines = [f"  {k}: {v};" for k, v in props.items() if k != "color-scheme"]
        lines.append(f"  color-scheme: {props.get('color-scheme', 'light')};")
        return selector + " {\n" + "\n".join(lines) + "\n}\n"

    header = (f"/* {NAME} theme for {project}: the project's tokens mapped onto the shadcn roles (D-280).\n"
              f"   Imported {date.today().isoformat()} from {Path(source).name} (sha256 {hashlib.sha256(blob).hexdigest()[:12]}) by\n"
              f"   `bitacora.py components theme import {project} --from <path>`. The project owns these values:\n"
              "   re-import when its tokens change. Structure and behaviour come from the pool, never from here. */\n"
              + (f"/* @mockup-fonts: {', '.join(mockup_fonts)} */\n" if mockup_fonts else ""))
    out = THEMES / f"{project}.css"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + block(':root, [data-theme="light"]', light) +
                   block('.dark, [data-theme="dark"]', dark) if dark else header + block(':root, [data-theme="light"]', light),
                   encoding="utf-8")
    return out


# ------------------------------------------------------------------------------------------------ builds
def _ws() -> Path:
    import bt_kit_workspace
    return bt_kit_workspace.workspace()


def build_root() -> Path:
    return _ws() / "dist" / "ui"


def build_dir(d: str | None = None) -> Path:
    return build_root() / (d or digest())


@contextmanager
def _lock(name: str):
    build_root().mkdir(parents=True, exist_ok=True)
    with open(build_root() / f".{name}.lock", "a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def _node(*args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    node = shutil.which("node")
    if not node:
        raise FileNotFoundError("node not found")
    return subprocess.run([node, str(BUILDER), *args, "--ws", str(_ws()), "--ui", str(UI)], capture_output=True, text=True,
                          timeout=timeout, check=False)


def ensure_build(d: str | None = None) -> Path | None:
    """The built pool for the current sources (`<ws>/dist/ui/<digest>/`), building it once when missing. None when
    the toolchain is not installed or the build failed (callers fall back to the frozen export)."""
    d = d or digest()
    out = build_dir(d)
    if (out / "bitacora-ui.json").is_file():
        return out
    if not (_ws() / "node_modules").is_dir():
        return None
    with _lock("pool"):
        if (out / "bitacora-ui.json").is_file():
            return out
        tmp = out.with_name(out.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            done = _node("pool", "--out", str(tmp), "--version", f"{package()['version']}+{d}")
        except (OSError, subprocess.TimeoutExpired):
            return None
        if done.returncode or not (tmp / "bitacora-ui.json").is_file():
            (build_root() / "last-error.txt").write_text(done.stdout[-4000:] + done.stderr[-4000:], encoding="utf-8")
            shutil.rmtree(tmp, ignore_errors=True)
            return None
        shutil.rmtree(out, ignore_errors=True)
        tmp.rename(out)
        _prune(keep=d)
    return out


def _prune(keep: str, older_than_days: int = 7) -> None:
    import time
    cutoff = time.time() - older_than_days * 86400
    for p in build_root().iterdir():
        if p.is_dir() and _DIGEST.match(p.name) and p.name != keep and p.stat().st_mtime < cutoff:
            shutil.rmtree(p, ignore_errors=True)


def pool_file(d: str, name: str) -> Path | None:
    """A built pool file for `/ui/<digest>/<name>`; `current` is the current digest. Only the three known names."""
    if name not in ("bitacora-ui.js", "bitacora-ui.css", "bitacora-ui.json"):
        return None
    if d == "current":
        out = ensure_build()
    elif _DIGEST.match(d or ""):
        out = build_dir(d) if (build_dir(d) / name).is_file() else (ensure_build() if d == digest() else None)
    else:
        return None
    path = out / name if out else None
    return path if path and path.is_file() else None


def live_mockup(project: str, tsx: Path) -> str | None:
    """The live page of a mockup: its TSX rebuilt against the CURRENT pool (`/ui/<digest>/…`) with the project's
    theme linked last, cached by (source, pool, project). None when it cannot be built (no TSX, no toolchain, a
    compile error): the caller serves the frozen export instead."""
    tsx = Path(tsx)
    if not tsx.is_file() or not _PROJECT.match(project or ""):
        return None
    pool = ensure_build()
    if pool is None:
        return None
    d = pool.name
    key = hashlib.sha256(tsx.read_bytes() + f"\0{d}\0{project}\0{BUILDER.stat().st_mtime_ns}".encode()).hexdigest()[:24]
    cache = build_root() / "live" / f"{key}.html"
    if cache.is_file():
        return cache.read_text(encoding="utf-8")
    failed = cache.with_suffix(".failed")
    import time
    if failed.is_file() and time.time() - failed.stat().st_mtime < 600:     # a broken source is retried every 10 min
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    with _lock("live"):
        if cache.is_file():
            return cache.read_text(encoding="utf-8")
        try:
            done = _node("mockup", str(tsx), "--live", "--registry", str(pool), "--project", project,
                         "--out", str(cache), "--title", tsx.stem, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            failed.write_text(str(exc), encoding="utf-8")
            return None
        if done.returncode or not cache.is_file():
            failed.write_text(done.stdout[-3000:] + done.stderr[-3000:], encoding="utf-8")
            return None
    return cache.read_text(encoding="utf-8")


def with_theme(html: str, project: str) -> str:
    """A frozen mockup (no TSX source) with the project's current theme linked after its own styles, so its colours,
    fonts and radius follow the theme. Idempotent."""
    if not _PROJECT.match(project or "") or "data-ui-theme" in html:
        return html
    tag = f'<link rel="stylesheet" href="/ui/theme/{project}.css" data-ui-theme>'
    found = list(re.finditer(r"</head\s*>", html, re.I))
    return html[:found[-1].start()] + tag + html[found[-1].start():] if found else tag + html


def source_tsx(html: Path) -> Path | None:
    """The TSX a mockup HTML was built from, when the Designer kept it beside the HTML (`<name>.tsx`)."""
    html = Path(html)
    candidate = html.with_suffix(".tsx")
    return candidate if candidate.is_file() else None


def main(argv: list[str]) -> int:
    """`bitacora.py components pool|theme …` (see bitacora.py)."""
    if argv[:1] == ["version"]:
        print(version())
        return 0
    if argv[:1] == ["build"]:
        out = ensure_build()
        print(out or f"BUILD FAILED: see {build_root() / 'last-error.txt'}")
        return 0 if out else 1
    if argv[:1] == ["import-sources"]:
        written = import_sources()
        print(f"{len(written)} file(s) written into {SRC}")
        return 0
    print("usage: components pool version|build|import-sources")
    return 2
