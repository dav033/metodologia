#!/usr/bin/env python3
"""Set up (or repair) the metodologia skill on this machine. Idempotent: run it after cloning and whenever in doubt.

  git clone https://github.com/dav033/metodologia ~/metodologia
  python ~/metodologia/install.py

What it does, with this machine's paths:
  1. Links  ~/.claude/skills/metodologia → skill/   ~/.agents/skills/metodologia → skill/   ~/bitacora → bitacora/
  2. Claude Code hooks in ~/.claude/settings.json and Codex hooks in ~/.codex/hooks.json (other hooks are kept)
  3. Always-on loading: @import of SKILL.md in ~/.claude/CLAUDE.md, pointer in ~/.codex/AGENTS.md
  4. Subagent roles for both (skill/scripts/install_agents.py)
  5. Rebuilds the local workspace index (where each project's repos are cloned on this machine)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
PY = Path(sys.executable).as_posix()
SKILL_LINK = HOME / ".claude" / "skills" / "metodologia"
SCRIPTS = SKILL_LINK.as_posix() + "/scripts"
MARK = "metodologia"  # any hook whose command mentions this is ours and gets replaced


def say(msg: str) -> None:
    print(f"  {msg}")


# ---------------------------------------------------------------- 1. links

def link(path: Path, target: Path) -> None:
    if path.is_symlink() or _is_junction(path):
        if path.resolve() == target.resolve():
            return say(f"ok      {path}")
        _unlink(path)
    elif path.exists():
        sys.exit(f"ABORT: {path} exists and is a real folder. Move its content into {target} (or rename it) "
                 f"and run install.py again.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], check=True, capture_output=True)
    else:
        path.symlink_to(target, target_is_directory=True)
    say(f"linked  {path} → {target}")


def _is_junction(p: Path) -> bool:
    try:
        return bool(os.readlink(p))
    except (OSError, ValueError):
        return False


def _unlink(p: Path) -> None:
    if os.name == "nt":
        os.rmdir(p)  # removes a junction without touching its target
    else:
        p.unlink()


# ---------------------------------------------------------------- 2. hooks

def _merge_hooks(current: dict, ours: dict) -> dict:
    hooks = current.setdefault("hooks", {})
    for event, groups in list(hooks.items()):
        kept = [g for g in groups if not any(MARK in h.get("command", "") for h in g.get("hooks", []))]
        hooks[event] = kept
    for event, groups in ours.items():
        hooks.setdefault(event, []).extend(groups)
    current["hooks"] = {e: g for e, g in hooks.items() if g}
    return current


def _cmd(script: str, *args: str) -> str:
    return f'"{PY}" "{SCRIPTS}/{script}"' + "".join(f" {a}" for a in args)


def claude_hooks() -> None:
    f = HOME / ".claude" / "settings.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    ours = {
        "SessionStart": [{"matcher": "startup|resume|clear|compact",
                          "hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "start"), "timeout": 20}]}],
        "Stop": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "stop"), "timeout": 20}]}],
        "SessionEnd": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "end"), "timeout": 15}]}],
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit",
                         "hooks": [{"type": "command", "command": _cmd("file_guard.py"), "timeout": 10}]}],
    }
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(_merge_hooks(data, ours), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"hooks   {f}")


def codex_hooks() -> None:
    f = HOME / ".codex" / "hooks.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    ours = {
        "SessionStart": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "start", "--harness",
                                                                        "codex"), "timeout": 20}]}],
        "Stop": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "stop", "--harness", "codex"),
                             "timeout": 20}]}],
        "SessionEnd": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "end"), "timeout": 3}]}],
        "PostToolUse": [{"hooks": [{"type": "command", "command": _cmd("file_guard.py"), "timeout": 10}]}],
    }
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(_merge_hooks(data, ours), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"hooks   {f}  (Codex: approve them once with /hooks)")


# ---------------------------------------------------------------- 3. always-on loading

CLAUDE_BLOCK = """
<!-- metodologia:start -->
# Metodología de trabajo

La skill `metodologia` se carga completa en cada sesión:

@~/.claude/skills/metodologia/SKILL.md

Preguntar al inicio, aprobar el plan, y después trabajar autónomo hasta terminar.
Conversación en español; bitácora en inglés; código en el idioma del repositorio (inglés si es nuevo).
<!-- metodologia:end -->
"""

CODEX_BLOCK = """
<!-- metodologia:start -->
# Metodología de trabajo

Siempre usa la skill `metodologia` (requerimientos por rondas + plan aprobado + ejecución con /goal + bitácora en
`~/bitacora/<proyecto>/` + estándares de ingeniería). Los hooks de Codex inyectan la skill y el contexto al iniciar.
Bitácora en inglés; código en el idioma del repositorio (inglés si es nuevo).
<!-- metodologia:end -->
"""


def ensure_block(f: Path, block: str, already: str) -> None:
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    if already in text:
        return say(f"ok      {f}")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8")
    say(f"added   {f}")


# ---------------------------------------------------------------- main

def main() -> None:
    print(f"metodologia install · repo {REPO}")
    print("1. links")
    link(SKILL_LINK, REPO / "skill")
    link(HOME / ".agents" / "skills" / "metodologia", REPO / "skill")
    link(HOME / "bitacora", REPO / "bitacora")
    print("2. hooks")
    claude_hooks()
    codex_hooks()
    print("3. always-on")
    ensure_block(HOME / ".claude" / "CLAUDE.md", CLAUDE_BLOCK, "@~/.claude/skills/metodologia/SKILL.md")
    ensure_block(HOME / ".codex" / "AGENTS.md", CODEX_BLOCK, "skill `metodologia`")
    print("4. subagents")
    subprocess.run([sys.executable, str(REPO / "skill" / "scripts" / "install_agents.py")], check=False)
    print("5. workspaces on this machine")
    sys.path.insert(0, str(REPO / "skill" / "scripts"))
    import bt_workspace as ws
    root = HOME / "bitacora"
    ws.reindex(root)
    for d in sorted(root.iterdir()):
        if (d / "project.json").exists():
            gone = ws.missing(root, d.name)
            say(f"{d.name}: {'all repos found' if not gone else 'not cloned here: ' + ', '.join(gone)}")
    print("6. secret scanning (gitleaks)")
    import bt_secrets
    if not bt_secrets.find_gitleaks() and os.name == "nt":
        subprocess.run(["winget", "install", "--id", "Gitleaks.Gitleaks", "-e", "--accept-source-agreements",
                        "--accept-package-agreements", "--disable-interactivity"], check=False, capture_output=True)
    say(f"gitleaks: {bt_secrets.find_gitleaks() or 'NOT installed — winget install Gitleaks.Gitleaks'}")
    for d in sorted(root.iterdir()):
        if (d / "project.json").exists():
            for role, path in ws.repos(root, d.name).items():
                if path.exists() and path.resolve() != REPO.resolve():
                    say(f"{d.name}/{role}: pre-commit {bt_secrets.install_hook(path)}")
    if (REPO / ".git").exists():
        subprocess.run(["git", "-C", str(REPO), "config", "pull.rebase", "true"], check=False)
    print("Done. Missing repos are cloned on demand (launch) or with: bitacora.py --project <p> workspace clone")


if __name__ == "__main__":
    main()
