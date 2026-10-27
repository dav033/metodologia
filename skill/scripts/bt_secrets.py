"""Secret scanning with gitleaks: before every bitácora auto-commit, and as a pre-commit hook in workspace repos.

A finding never gets committed: the bitácora commit is skipped, the staged changes are unstaged, and a redacted
alert is left in .state/secret-alert.txt — SessionStart and the Stop hook surface it until it's fixed.
If gitleaks isn't installed, scanning is skipped (install: `winget install Gitleaks.Gitleaks`).
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import bt_nowindow  # noqa: F401  (no console windows on Windows)

HOOK_MARK = "metodologia: gitleaks secret scan"
HOOK = f"""#!/bin/sh
# {HOOK_MARK}
GL="__GITLEAKS__"
[ -x "$GL" ] || GL=$(command -v gitleaks 2>/dev/null)
if [ -z "$GL" ] && [ -n "$LOCALAPPDATA" ]; then
  LAD=$(printf '%s' "$LOCALAPPDATA" | sed 's#\\\\#/#g')
  GL=$(ls "$LAD"/Microsoft/WinGet/Links/gitleaks.exe "$LAD"/Microsoft/WinGet/Packages/Gitleaks.Gitleaks*/gitleaks.exe 2>/dev/null | head -1)
fi
if [ -z "$GL" ]; then
  echo "AVISO: gitleaks no encontrado; este commit NO fue escaneado (instala: winget install Gitleaks.Gitleaks)."
  exit 0
fi
"$GL" git --pre-commit --staged --redact --no-banner --no-color -v || {{
  echo "gitleaks: posible secreto en este commit. Quítalo del código (usa variables de entorno) y vuelve a intentar."
  echo "Si es un falso positivo: añade el hallazgo a .gitleaksignore o usa git commit --no-verify."
  exit 1
}}
"""


def find_gitleaks() -> str | None:
    exe = shutil.which("gitleaks")
    if exe:
        return exe
    local = os.environ.get("LOCALAPPDATA", "")
    for pattern in (rf"{local}\Microsoft\WinGet\Links\gitleaks.exe",
                    rf"{local}\Microsoft\WinGet\Packages\Gitleaks.Gitleaks*\gitleaks.exe"):
        hits = glob.glob(pattern)
        if hits:
            return hits[0]
    return None


# Generated artifacts that gitleaks cannot scan within the hook's time limit: self-contained design mockups embed
# base64 fonts in single huge lines (one revision is ~6 MB) and the translation cache is keyed by long hashes that
# the generic-api-key rule mistakes for tokens. Scanning them took minutes, so every bitácora commit timed out.
GENERATED = (re.compile(r"(^|/)design/[^/]+\.(?:html|tsx)$"), re.compile(r"(^|/)\.translations/cache\.json$"))
SCAN_TIMEOUT_SEC = 120


def _git_out(repo: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, input=stdin, capture_output=True, timeout=SCAN_TIMEOUT_SEC, check=False)


def scan_staged(repo: Path) -> tuple[bool, str]:
    """(clean, redacted report). Clean when gitleaks is missing — scanning is best-effort.

    Scans the STAGED content of every added/changed file except `GENERATED`, exported to a temporary directory laid
    out like the repository (checkout-index keeps repo-root paths), so finding fingerprints keep matching `.gitleaksignore`.
    """
    exe = find_gitleaks()
    if not exe:
        return True, ""
    try:
        listed = _git_out(repo, "diff", "--cached", "--name-only", "--relative", "--diff-filter=ACMR", "-z", "--", ".")
        if listed.returncode:
            return False, "gitleaks could not complete: git diff failed"
        names = [n for n in listed.stdout.decode("utf-8", "replace").split("\0") if n and not any(g.search(n) for g in GENERATED)]
        if not names:
            return True, ""
        with tempfile.TemporaryDirectory(prefix="bitacora-scan-") as tmp:
            exported = _git_out(repo, "checkout-index", f"--prefix={Path(tmp).as_posix()}/", "-z", "--stdin",
                                stdin=("\0".join(names) + "\0").encode())
            if exported.returncode:
                return False, "gitleaks could not complete: staged files could not be exported"
            cmd = [exe, "dir", ".", "--redact", "--no-banner", "--no-color", "-v"]
            for flag, name in (("-i", ".gitleaksignore"), ("-c", ".gitleaks.toml")):
                if (Path(repo) / name).is_file():
                    cmd += [flag, str(Path(repo) / name)]
            res = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=SCAN_TIMEOUT_SEC,
                                 encoding="utf-8", errors="replace", check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"gitleaks could not complete: {type(exc).__name__}"
    if res.returncode == 0:
        return True, ""
    return False, (res.stdout + res.stderr).strip()[-4000:]


def alert_file(root: Path) -> Path:
    return root / ".state" / "secret-alert.txt"


def set_alert(root: Path, report: str) -> None:
    f = alert_file(root)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(report, encoding="utf-8")


def clear_alert(root: Path) -> None:
    alert_file(root).unlink(missing_ok=True)


def alert(root: Path) -> str:
    f = alert_file(root)
    return f.read_text(encoding="utf-8") if f.exists() else ""


def install_hook(repo: Path) -> str:
    """Install the pre-commit hook in one repo. Never overwrites someone else's hook."""
    if not (repo / ".git").exists():
        return "not a git repo"
    hooks_path = subprocess.run(["git", "config", "core.hooksPath"], cwd=repo, capture_output=True, text=True)
    if hooks_path.stdout.strip():
        return f"skipped: uses core.hooksPath={hooks_path.stdout.strip()} (husky?) — add gitleaks there if wanted"
    located = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=repo, capture_output=True, text=True)
    hooks_dir = Path(located.stdout.strip()) if located.returncode == 0 and located.stdout.strip() else None
    if hooks_dir is not None and not hooks_dir.is_absolute():
        hooks_dir = repo / hooks_dir  # a linked worktree has a `.git` file; its hooks live in the common git dir
    hook = (hooks_dir or repo / ".git" / "hooks") / "pre-commit"
    if hook.exists() and HOOK_MARK not in hook.read_text(encoding="utf-8", errors="ignore"):
        return "skipped: has its own pre-commit hook"
    hook.parent.mkdir(parents=True, exist_ok=True)
    found = find_gitleaks() or ""
    hook.write_text(HOOK.replace("__GITLEAKS__", found.replace("\\", "/")), encoding="utf-8", newline="\n")
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    return "installed"
