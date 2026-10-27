"""The Designer's REAL component libraries, installed in a local workspace outside git (D-135).

  python3 bt_kit_workspace.py install [--force]       # official installers, idempotent (network)
  python3 bt_kit_workspace.py build [--only id,id]    # gallery bundles + reference mockups (offline)
  python3 bt_kit_workspace.py mockup build ENTRY.tsx --out design/<ref>@vN.html   (offline)
  python3 bt_kit_workspace.py status | path

`bitacora.py components install|build|mockup|status` call the same functions. The workspace defaults to
`~/.local/share/bitacora/kit-workspace` (`BITACORA_KIT_WORKSPACE` overrides it); the skill keeps only the manifest,
theme, runtime, demos and these scripts. Installers, in order: shadcn CLI (Vite template, Base UI base) for the 42
shadcn components, Animate UI's CLI swapping their primitives for its animated ones (+ its npm package for the 7
capabilities), the React Bits registry through the shadcn CLI, and Bencho's published method (copy a block folder from
its MIT repository at a pinned commit). Each step is skipped when its output is already there (`--force` redoes it).
Never prints secrets; uses no tokens."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REAL = SKILL_ROOT / "agents/designer/skills/david-ui-kit/real"
MANIFEST = REAL / "manifest.json"
SHADCN = "shadcn@4.22.1"
ANIMATE_CLI = "@animate-ui/cli@2.2.0"
NPM_PACKAGES = ["@animate-ui/react@2.3.0", "motion@^14", "esbuild@0.28.2", "@tanstack/react-table@^8", "gsap@^3.15",
                "@gsap/react@^2", "lucide-react", "framer-motion@^12",
                # self-hostable type for directions (inlined as data: URIs by the builder; never fetched at run time)
                "@fontsource-variable/fraunces", "@fontsource-variable/bricolage-grotesque",
                "@fontsource-variable/space-grotesk", "@fontsource-variable/instrument-sans",
                "@fontsource/instrument-serif", "@fontsource-variable/jetbrains-mono", "@fontsource-variable/manrope",
                "@fontsource-variable/syne", "@fontsource/dm-serif-display", "@fontsource-variable/geist",
                "@fontsource-variable/unbounded", "@fontsource-variable/newsreader"]
BENCHO_REPO = "cabralorenzo/bencho"
BENCHO_COMMIT = "30ab35a575eb83eed8f086a6893d4d6426f4fa91"


def workspace() -> Path:
    env = os.environ.get("BITACORA_KIT_WORKSPACE")
    if env:
        return Path(env).expanduser().resolve()
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return (base / "bitacora/kit-workspace").resolve()


def dist() -> Path:
    return workspace() / "dist/gallery"


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _run(cmd: list[str], cwd: Path, log: list[str], timeout: int = 900) -> None:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, "CI": "1", "npm_config_yes": "true", "npm_config_fund": "false",
                               "npm_config_audit": "false"})
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
    log.append(f"{' '.join(cmd[:4])} → exit {proc.returncode}")
    if proc.returncode:
        raise SystemExit(f"install step failed ({' '.join(cmd[:4])} …):\n" + "\n".join(tail))


def _items(source: str) -> list[dict]:
    return [e for e in manifest()["entries"] if e["source"] == source and e.get("install")]


def install(force: bool = False) -> dict:
    """Create or complete the workspace. Returns the install record written to `<ws>/install.json`."""
    ws = workspace()
    log: list[str] = []
    npx = shutil.which("npx")
    if not npx or not shutil.which("node"):
        raise SystemExit("node/npx not found: install Node 20+ (fnm) first")
    if force or not (ws / "components.json").is_file():
        ws.parent.mkdir(parents=True, exist_ok=True)
        if ws.exists() and force:
            shutil.rmtree(ws)
        _run([npx, "-y", SHADCN, "init", "-t", "vite", "-b", "base", "-p", "nova", "-n", ws.name, "-y", "--no-monorepo"],
             ws.parent, log)
    ui = [e["install"]["item"] for e in _items("shadcn") if e["install"]["via"] == "shadcn"]
    extra = [i for e in _items("animate-ui") if e["install"]["via"] == "shadcn-extra" for i in e["install"]["items"]]
    missing = [i for i in ui if force or not (ws / "src/components/ui" / f"{i}.tsx").is_file()]
    if missing:
        _run([npx, "-y", SHADCN, "add", *sorted(set(ui + ["label", "separator", "input-group", "button"])), "-y", "--overwrite"],
             ws, log)
    if missing or not any("@animate-ui/react/primitives" in p.read_text(encoding="utf-8")
                          for p in (ws / "src/components/ui").glob("*.tsx")):
        _run([npx, "-y", ANIMATE_CLI, "animate", "all"], ws, log)       # shadcn primitives → Animate UI's animated ones
    if extra and (force or not (ws / ".animate-extra").is_file()):
        _run([npx, "-y", SHADCN, "add", *extra, "-y", "--overwrite"], ws, log)
        (ws / ".animate-extra").write_text("\n".join(extra) + "\n")
    bits = [e["install"]["item"] for e in _items("react-bits")]
    target = ws / "src/components/react-bits"
    todo = [b for b in bits if force or not (target / f"{b.split('-')[0]}.tsx").is_file()]
    if todo:
        _run([npx, "-y", SHADCN, "add", *[f"@react-bits/{b}" for b in todo], "-y", "--overwrite"], ws, log)
        target.mkdir(parents=True, exist_ok=True)
        for b in todo:                          # the registry writes into src/components/: keep them in their own folder
            name = b.split("-")[0]
            for src in (ws / "src/components").glob(f"{name}.*"):
                shutil.move(str(src), target / src.name)
    _run(["npm", "install", "--no-fund", "--no-audit", *NPM_PACKAGES], ws, log)   # last: React Bits pins motion@12
    _bencho(ws, force, log)
    _write_index_css(ws)
    record = {"installed": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "workspace": str(ws), "shadcn": SHADCN,
              "animate_ui_cli": ANIMATE_CLI, "bencho_commit": BENCHO_COMMIT, "versions": _versions(ws), "log": log}
    (ws / "install.json").write_text(json.dumps(record, indent=1) + "\n")
    _make_readable(ws)
    return record


def _bencho(ws: Path, force: bool, log: list[str]) -> None:
    folders = [e["install"]["item"] for e in _items("bencho")]
    target = ws / "src/components/bencho"
    if not force and all((target / f).is_dir() for f in folders):
        return
    url = f"https://codeload.github.com/{BENCHO_REPO}/tar.gz/{BENCHO_COMMIT}"
    print(f"$ download {url}", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "bencho.tgz"
        with urllib.request.urlopen(url, timeout=120) as resp:      # noqa: S310 - fixed https URL at a pinned commit
            archive.write_bytes(resp.read())
        with tarfile.open(archive) as tar:
            tar.extractall(tmp, filter="data")
        root = next(Path(tmp).glob("bencho-*"))
        target.mkdir(parents=True, exist_ok=True)
        for f in folders:
            shutil.rmtree(target / f, ignore_errors=True)
            shutil.copytree(root / "blocks" / f, target / f)
        for name in ("tokens.css", "LICENSE", "THIRD_PARTY.md"):
            if (root / name).is_file():
                shutil.copy2(root / name, target / name)
    log.append(f"bencho {BENCHO_COMMIT[:12]}: {len(folders)} blocks copied")


def _write_index_css(ws: Path) -> None:
    """The workspace's own app (vite dev) uses the same theme as the builder."""
    (ws / "src/index.css").write_text('@import "tailwindcss";\n@import "tw-animate-css";\n@import "shadcn/tailwind.css";\n'
                                      f'@import "{REAL / "theme.css"}";\n@source "{REAL}";\n', encoding="utf-8")


def _versions(ws: Path) -> dict:
    try:
        lock = json.loads((ws / "package-lock.json").read_text())["packages"]
    except (OSError, ValueError, KeyError):
        return {}
    want = ["react", "react-dom", "@base-ui/react", "@animate-ui/react", "motion", "tailwindcss", "esbuild", "gsap",
            "recharts", "sonner", "shadcn", "lucide-react"]
    return {n: lock.get(f"node_modules/{n}", {}).get("version") for n in want if f"node_modules/{n}" in lock}


def _make_readable(ws: Path) -> None:
    """A sandboxed Designer (another account or a read-only mount) must read and execute the toolchain."""
    try:
        for p in [ws, *ws.rglob("*")]:
            mode = p.stat().st_mode
            p.chmod(mode | 0o044 | (0o011 if p.is_dir() or mode & 0o100 else 0))
    except OSError:
        pass


def _node(*args: str) -> int:
    node = shutil.which("node")
    if not node:
        print("BUILD FAILED: node not found")
        return 2
    return subprocess.run([node, str(REAL / "build.mjs"), *args, "--ws", str(workspace())]).returncode


def build(only: list[str] | None = None) -> int:
    if not (workspace() / "node_modules").is_dir():
        print(f"BUILD FAILED: kit workspace not installed at {workspace()}: run `bitacora.py components install`")
        return 2
    return _node("gallery", "--out", str(dist()), *(["--only", ",".join(only)] if only else []))


def mockup_build(entry: str, out: str, title: str = "") -> int:
    return _node("mockup", str(Path(entry).resolve()), "--out", str(Path(out).resolve()), *(["--title", title] if title else []))


def status() -> dict:
    """What the gallery and the Designer can rely on right now (read-only)."""
    ws = workspace()
    out = {"workspace": str(ws), "installed": (ws / "node_modules").is_dir(), "built": (dist() / "status.json").is_file(),
           "install": None, "entries": {}}
    try:
        out["install"] = json.loads((ws / "install.json").read_text())
    except (OSError, ValueError):
        pass
    try:
        built = json.loads((dist() / "status.json").read_text())
        out["entries"], out["built_at"] = built.get("entries", {}), built.get("built")
    except (OSError, ValueError):
        pass
    return out


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "install":
        install(force="--force" in argv)
        return build()
    if cmd == "build":
        only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
        return build(only)
    if cmd == "mockup" and len(argv) >= 2 and argv[1] == "build":
        rest = argv[2:]
        if "--out" not in rest or not rest or rest[0].startswith("--"):
            print("usage: mockup build ENTRY.tsx --out FILE.html [--title T]")
            return 2
        title = rest[rest.index("--title") + 1] if "--title" in rest else ""
        return mockup_build(rest[0], rest[rest.index("--out") + 1], title)
    if cmd == "status":
        st = status()
        ok = sum(1 for s in st["entries"].values() if s.get("ok"))
        print(f"workspace {st['workspace']}: installed={st['installed']} built={st['built']} entries ok={ok}/{len(st['entries'])}")
        return 0 if st["installed"] else 1
    if cmd == "path":
        print(workspace())
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
