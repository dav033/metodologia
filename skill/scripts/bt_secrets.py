"""Secret scanning with gitleaks: before every bitácora auto-commit, and as a pre-commit hook in workspace repos.

A finding never gets committed: the bitácora commit is skipped, the staged changes are unstaged, and a redacted
alert is left in .state/secret-alert.txt — SessionStart and the Stop hook surface it until it's fixed.
If gitleaks isn't installed, scanning is skipped (install: `winget install Gitleaks.Gitleaks`).
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
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


def scan_staged(repo: Path) -> tuple[bool, str]:
    """(clean, redacted report). Clean when gitleaks is missing — scanning is best-effort."""
    exe = find_gitleaks()
    if not exe:
        return True, ""
    try:
        res = subprocess.run([exe, "git", "--pre-commit", "--staged", "--redact", "--no-banner", "--no-color", "-v"], cwd=repo,
                             capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
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
    hook = repo / ".git" / "hooks" / "pre-commit"
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
