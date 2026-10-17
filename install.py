#!/usr/bin/env python3
"""Set up (or repair) the metodologia skill on this machine. Idempotent: run it after cloning and whenever in doubt.

  git clone https://github.com/dav033/metodologia ~/metodologia
  python ~/metodologia/install.py

What it does, with this machine's paths:
  1. Links  <claude dir>/skills/metodologia → skill/   ~/.agents/skills/metodologia → skill/; ~/bitacora is created
     as a plain folder (or $BITACORA_ROOT), never linked into this repo
  2. Claude Code hooks in <claude dir>/settings.json and Codex hooks in <codex dir>/hooks.json (other hooks are kept)
  3. Always-on loading: @import of SKILL.md in <claude dir>/CLAUDE.md, pointer in <codex dir>/AGENTS.md
  <claude dir>/<codex dir> are ~/.claude and ~/.codex plus every existing CLAUDE_CONFIG_DIR / CODEX_HOME of the
  account profiles (bitacora.py profiles list), so each account gets the same skill, hooks and subagents.
  4. Subagent roles for Claude Code, Codex and Antigravity (skill/scripts/install_agents.py)
  5. Rebuilds the local workspace index (where each project's repos are cloned on this machine)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
PY = Path(sys.executable).as_posix()
CLAUDE_HOME = HOME / ".claude"
CODEX_HOME = HOME / ".codex"
SKILL_LINK = CLAUDE_HOME / "skills" / "metodologia"
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
    # Hook commands may run under bash OR PowerShell. A quoted program path ("C:/x/python.exe" args) is a parse
    # error in PowerShell, so the interpreter goes unquoted (fine in both); with spaces, fall back to `python`.
    exe = PY if " " not in PY else "python"
    return f'{exe} "{SCRIPTS}/{script}"' + "".join(f" {a}" for a in args)


def claude_hooks(config: Path = CLAUDE_HOME) -> None:
    f = config / "settings.json"
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


def codex_hooks(config: Path = CODEX_HOME) -> None:
    f = config / "hooks.json"
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

@{skill}

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


# ---------------------------------------------------------------- transactional plan (dry-run, journal, rollback)

def _owned_hook(item: object) -> bool:
    """A hook GROUP (or a bare hook command) is ours when a command runs a script through the skill link. The relay
    hooks have their own installer (`bitacora.py relay install`) and are never touched here. As in the original
    installer, a group that holds one of our commands is replaced as a whole."""
    if not isinstance(item, dict):
        return False
    commands = [item["command"]] if isinstance(item.get("command"), str) else [
        h.get("command") for h in item.get("hooks", []) if isinstance(h, dict) and isinstance(h.get("command"), str)]
    return any("/skills/metodologia/scripts/" in c.replace("\\", "/") and " hook relay" not in c for c in commands)


def _claude_hooks_value() -> dict:
    return {
        "SessionStart": [{"matcher": "startup|resume|clear|compact",
                          "hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "start"), "timeout": 20}]}],
        "Stop": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "stop"), "timeout": 20}]}],
        "SessionEnd": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "end"), "timeout": 15}]}],
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit",
                         "hooks": [{"type": "command", "command": _cmd("file_guard.py"), "timeout": 10}]}],
    }


def _codex_hooks_value() -> dict:
    return {
        "SessionStart": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "start", "--harness",
                                                                        "codex"), "timeout": 20}]}],
        "Stop": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "stop", "--harness", "codex"),
                             "timeout": 20}]}],
        "SessionEnd": [{"hooks": [{"type": "command", "command": _cmd("bitacora.py", "hook", "end"), "timeout": 3}]}],
        "PostToolUse": [{"hooks": [{"type": "command", "command": _cmd("file_guard.py"), "timeout": 10}]}],
    }


def _merge_owned(ours: dict):
    def merge(current: dict) -> dict:
        hooks = current.setdefault("hooks", {})
        for event, groups in ours.items():
            hooks.setdefault(event, []).extend(groups)
        return current
    return merge


def _inner(block: str) -> str:
    return "\n".join(line for line in block.strip("\n").splitlines()
                     if not line.startswith("<!-- metodologia:"))


def build_operations(claude_dirs: list[Path], codex_dirs: list[Path]):
    """Steps 1-3 (links, hooks, always-on blocks) as one reversible plan."""
    import bt_install_tx as tx
    ops = [tx.symlink(config / "skills" / "metodologia", REPO / "skill") for config in claude_dirs]
    ops.append(tx.symlink(HOME / ".agents" / "skills" / "metodologia", REPO / "skill"))
    ops += [tx.json_merge(config / "settings.json", _merge_owned(_claude_hooks_value()), is_owned=_owned_hook)
            for config in claude_dirs]
    ops += [tx.json_merge(config / "hooks.json", _merge_owned(_codex_hooks_value()), is_owned=_owned_hook)
            for config in codex_dirs]
    def block_op(path: Path, inner: str, already: str):
        real = path.resolve() if path.is_symlink() else path  # write through a link, like the original did
        text = real.read_text(encoding="utf-8") if real.exists() else ""
        if already in text:  # the import/pointer is already there (inside or outside our markers): never duplicate
            return None
        return tx.ensure_block(real, inner, "metodologia")

    for config in claude_dirs:
        skill = f"{tilde(config)}/skills/metodologia/SKILL.md"
        ops.append(block_op(config / "CLAUDE.md", _inner(CLAUDE_BLOCK.format(skill=skill)), skill))
    for config in codex_dirs:
        ops.append(block_op(config / "AGENTS.md", _inner(CODEX_BLOCK), "skill `metodologia`"))
    return [op for op in ops if op is not None]


# ---------------------------------------------------------------- main

def tilde(path: Path) -> str:
    """~/x form when under HOME (what the @import in CLAUDE.md expects), absolute otherwise."""
    try:
        return "~/" + path.relative_to(HOME).as_posix()
    except ValueError:
        return path.as_posix()


def bitacora_root() -> Path:
    return Path(os.environ.get("BITACORA_ROOT") or HOME / "bitacora")


def account_dirs() -> tuple[list[Path], list[Path]]:
    """Config directories to install into: the defaults plus one per account profile (CLAUDE_CONFIG_DIR / CODEX_HOME)."""
    import bt_profiles
    claude, codex = [CLAUDE_HOME], [CODEX_HOME]
    for spec in bt_profiles.load().values():
        env = {k: Path(os.path.expanduser(v)) for k, v in (spec.get("env") or {}).items()}
        for key, found in (("CLAUDE_CONFIG_DIR", claude), ("CODEX_HOME", codex)):
            if key in env and env[key] not in found and env[key].exists():
                found.append(env[key])
    return claude, codex


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtk-only", action="store_true",
                        help="Install only the pinned RTK binary; leave hooks/settings/workspaces untouched")
    parser.add_argument("--with-rtk", action="store_true",
                        help="Include the pinned RTK binary in the normal methodology setup")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what steps 1-3 (links, hooks, always-on blocks) would change; write nothing")
    parser.add_argument("--core-only", action="store_true",
                        help="Apply only steps 1-3 (links, hooks, always-on blocks) and stop (tests, repair)")
    parser.add_argument("--rollback", metavar="JOURNAL",
                        help="Undo a previous install using its journal (only files still in the state it left)")
    parser.add_argument("--legacy", action="store_true",
                        help="Apply steps 1-3 with the original in-place code (no journal, no preimages)")
    args = parser.parse_args(argv)
    if args.rollback:
        sys.path.insert(0, str(REPO / "skill" / "scripts"))
        import bt_install_tx as tx
        print(json.dumps(tx.rollback(args.rollback), indent=1, ensure_ascii=False))
        return
    if args.rtk_only or args.with_rtk:
        sys.path.insert(0, str(REPO / "skill" / "scripts"))
        import install_rtk
        say(f"RTK {install_rtk.VERSION}: {install_rtk.install()}")
        if args.rtk_only:
            return
    print(f"metodologia install · repo {REPO}")
    sys.path.insert(0, str(REPO / "skill" / "scripts"))
    claude_dirs, codex_dirs = account_dirs()
    root = bitacora_root()
    if args.dry_run or not args.legacy:
        import bt_install_tx as tx
        transaction = tx.plan(build_operations(claude_dirs, codex_dirs), allowed_roots=(HOME,))
        report = tx.dry_run(transaction)
        if args.dry_run:
            print(json.dumps(report, indent=1, ensure_ascii=False))
            return
        conflicts = [row for row in report["operations"] if row["action"] == "conflict"]
        if conflicts:
            sys.exit("ABORT: " + "; ".join(f"{row['path']}: {row.get('reason', 'conflict')}" for row in conflicts))
        stamp = __import__("datetime").datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = HOME / ".local" / "share" / "metodologia-migration" / "installs" / stamp
        print("1-3. links, hooks, always-on (journaled)")
        result = tx.apply(transaction, backup)
        for row in report["operations"]:
            say(f"{row['action']:<9} {row['path']}")
        say(f"journal {backup / 'journal.jsonl'}  (undo: install.py --rollback <that file>)")
        del result
        root.mkdir(parents=True, exist_ok=True)  # the live bitácora is a real folder, never a link into this repo
        say(f"ok      {root}")
        if args.core_only:
            return
    else:
        print("1. links")
        for config in claude_dirs:
            link(config / "skills" / "metodologia", REPO / "skill")
        link(HOME / ".agents" / "skills" / "metodologia", REPO / "skill")
        root.mkdir(parents=True, exist_ok=True)
        say(f"ok      {root}")
        print("2. hooks")
        for config in claude_dirs:
            claude_hooks(config)
        for config in codex_dirs:
            codex_hooks(config)
        print("3. always-on")
        for config in claude_dirs:
            skill = f"{tilde(config)}/skills/metodologia/SKILL.md"
            ensure_block(config / "CLAUDE.md", CLAUDE_BLOCK.format(skill=skill), skill)
        for config in codex_dirs:
            ensure_block(config / "AGENTS.md", CODEX_BLOCK, "skill `metodologia`")
    print("4. subagents")
    agents = [sys.executable, str(REPO / "skill" / "scripts" / "install_agents.py")]
    for config in claude_dirs:
        agents += ["--claude-dir", str(config / "agents")]
    for config in codex_dirs:
        agents += ["--codex-dir", str(config / "agents")]
    subprocess.run(agents, check=False)
    print("5. workspaces on this machine")
    import bt_workspace as ws
    ws.reindex(root)
    for d in sorted(root.iterdir()):
        if (d / "project.json").exists():
            gone = ws.missing(root, d.name)
            say(f"{d.name}: {'all repos found' if not gone else 'not cloned here: ' + ', '.join(gone)}")
    print("6. secret scanning (gitleaks)")
    import bt_platform
    import bt_secrets
    if not bt_secrets.find_gitleaks() and os.name == "nt":
        subprocess.run(["winget", "install", "--id", "Gitleaks.Gitleaks", "-e", "--accept-source-agreements",
                        "--accept-package-agreements", "--disable-interactivity"], check=False, capture_output=True)
    say(f"gitleaks: {bt_secrets.find_gitleaks() or 'NOT installed — ' + bt_platform.gitleaks_install_hint()}")
    for d in sorted(root.iterdir()):
        if (d / "project.json").exists():
            for role, path in ws.repos(root, d.name).items():
                if path.exists() and path.resolve() != REPO.resolve():
                    say(f"{d.name}/{role}: pre-commit {bt_secrets.install_hook(path)}")
    print("6b. guard for this repo (no commits mixing bitacora/ with the skill; gitleaks)")
    if (REPO / ".git").exists():
        hook = REPO / ".git" / "hooks" / "pre-commit"
        hook.write_bytes((REPO / "skill" / "githooks" / "pre-commit").read_bytes())
        try:
            hook.chmod(0o755)
        except OSError:
            pass
        say(f"installed {hook}")
    print("7. optional: CodeGraph (code-graph MCP, see skill/references/codegraph.md)")
    npm = shutil.which("npm")
    if shutil.which("codegraph"):
        say("codegraph: already installed")
    elif npm:
        r = subprocess.run([npm, "i", "-g", "@colbymchenry/codegraph"], check=False, capture_output=True)
        say("codegraph: installed (register the MCP by hand, see codegraph.md)" if r.returncode == 0
            else "codegraph: npm install failed (optional, skipped)")
    else:
        say("codegraph: npm not found (optional, skipped)")
    if (REPO / ".git").exists():
        subprocess.run(["git", "-C", str(REPO), "config", "pull.rebase", "true"], check=False)
    print("Done. Missing repos are cloned on demand (launch) or with: bitacora.py --project <p> workspace clone")


if __name__ == "__main__":
    main()
