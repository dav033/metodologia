"""A «Probar» copy left at an older publication of its version moves to the published commit by itself (D-278).

Owner evidence, pictures REQ-021, 2026-10-31: «Probar SP-2» answered «…/SP-2-v2 existe pero no está en el commit
publicado; ciérralo primero». A subplan keeps its version number while its line moves (other accepted work lands on
it), so `<base>/<project>/<REQ>/<SP>-v<N>` can hold an older commit of the same «versión N». Copies are internal: the
owner never has to close one. `heal` (called by `bt_verification.open_local`, and so by `bt_verify_servers.start`)
brings the copy to the published commit, under the version's `.lock` (the one `start` and D-270's disk pass take;
`start` already holds it and has stopped the version's servers, so it passes `held`):

- the version's servers are stopped through `bt_verify_servers.halt` (they serve the stale tree; `start` restarts
  them on the new commit right after);
- something else still using the copy refuses, named (D-270's checks: a process carrying the version's
  `BITACORA_VERIFY_ID`, a process working inside it, its tmux session);
- edits or new files git would keep refuse, listing them; the owner then chooses `discard` (drop them and open the
  published commit) or `keep_aside` (the copy moves to `<SP>-v<N>-kept-<sha7>`, which no disk pass collects, and a
  fresh copy opens). Ignored files (dependencies, builds, logs) are not edits;
- otherwise the copy is checked out, detached, at the published commit. When the two commits differ in a dependency
  manifest or lockfile, ignored files are dropped so the recipe's `prepare` (`unless: node_modules`) redoes them as on
  a fresh copy; framework caches always go. If the checkout fails, the copy is removed and added again from the repo
  that holds the commit. The activity log records the move.

Messages name a version with its commit («versión 2 (commit abc1234)»): the number alone does not tell two
publications apart. Standard library only.
"""
from __future__ import annotations

import contextlib
import os
import shutil
from pathlib import Path

DEPENDENCY_FILES = frozenset({
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "yarn.lock",
    "bun.lock", "bun.lockb", ".npmrc", ".nvmrc", ".node-version", ".tool-versions", ".python-version",
    "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "Gemfile", "Gemfile.lock", "composer.json", "composer.lock",
})
SHOWN = 20                                # edited files named in a refusal before «y N más»


def label(row: dict) -> str:
    """«versión 2 (commit abc1234)»."""
    commit = str(row.get("commit") or "")
    return f"versión {row.get('version')}" + (f" (commit {commit[:7]})" if commit else "")


def _vs():
    import bt_verify_servers
    return bt_verify_servers


def _git(cwd: Path, *args: str):
    import bt_verification
    return bt_verification._git(cwd, *args)


def head(copy: Path) -> str:
    done = _git(copy, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    return done.stdout.strip() if done.returncode == 0 else ""


def edited(copy: Path) -> list[str] | None:
    """`git status` lines (`XY path`) of what git would keep in the copy; None when git cannot read it."""
    from bt_durable import gc_verify
    done = gc_verify._git(copy, "status", "--porcelain", "--untracked-files=normal")
    if done.returncode:
        return None
    return [line for line in done.stdout.splitlines() if line.strip()]


def describe(lines: list[str]) -> str:
    """«a.txt (modificado), nuevo.txt (nuevo)», at most SHOWN of them."""
    def one(line: str) -> str:
        code, path = line[:2], line[3:]
        kind = "nuevo" if code == "??" else "borrado" if "D" in code else "renombrado" if "R" in code else "modificado"
        return f"{path} ({kind})"
    shown = ", ".join(one(line) for line in lines[:SHOWN])
    return shown + (f" y {len(lines) - SHOWN} más" if len(lines) > SHOWN else "")


def _working_inside(copy: Path, proc: Path = Path("/proc")) -> list[str]:
    """«pid 123 (bash)» for each process of this user working inside the copy, never this process."""
    from bt_durable.scratch import processes_inside
    if not processes_inside([copy], proc):          # D-270's check; the scan below only names who
        return []
    real, found = os.path.realpath(copy), []
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            cwd = os.readlink(entry / "cwd")
            comm = (entry / "comm").read_text().strip()
        except OSError:
            continue
        if cwd == real or cwd.startswith(real + os.sep):
            found.append(f"pid {entry.name} ({comm})")
    return found


def in_use(copy: Path, own: str, session: str, proc: Path = Path("/proc")) -> str:
    """'' when nothing uses the copy, else who does (D-270's checks)."""
    from bt_durable import gc_verify
    why = []
    if own in gc_verify.marks_in_use(proc):
        why.append("un proceso de sus servidores sigue vivo")
    if gc_verify._session_alive(session):
        why.append(f"su sesión de terminal {session} sigue abierta")
    if inside := _working_inside(copy, proc):
        why.append("trabajan dentro de ella " + ", ".join(inside[:5]))
    return "; ".join(why)


def _parts(root: Path, project: str, rdir: Path, sid: str, version) -> tuple[dict, str, str]:
    vs = _vs()
    return (vs._files(root, project, rdir, sid, version), vs.session_name(project, rdir, sid, version),
            vs.mark(project, rdir, sid, version))


def _common_repo(copy: Path) -> Path | None:
    common = _git(copy, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    repo = Path(common).parent if common else None
    return repo if repo is not None and repo.is_dir() else None


def _drop(copy: Path, repo: Path | None) -> bool:
    """Remove a copy git reported clean (or the owner chose to discard); True when it is gone."""
    owner = _common_repo(copy) or repo
    if owner is not None:
        _git(owner, "worktree", "remove", "--force", str(copy))
    if copy.exists():
        shutil.rmtree(copy, ignore_errors=True)
    if owner is not None:
        _git(owner, "worktree", "prune")
    return not copy.exists()


def _deps_changed(copy: Path, old: str, new: str) -> bool:
    done = _git(copy, "diff", "--name-only", old, new)
    if done.returncode:
        return True                                  # cannot tell: redo them, as on a fresh copy
    return any(Path(p).name in DEPENDENCY_FILES or (Path(p).name.startswith("requirements") and p.endswith(".txt"))
               for p in done.stdout.splitlines())


def _move(copy: Path, repo: Path, old: str, new: str) -> str:
    """Bring a clean copy from `old` to `new`; '' or why not."""
    moved = _git(copy, "checkout", "--detach", "--quiet", new)
    if moved.returncode == 0 and head(copy) == new:
        if _deps_changed(copy, old, new):
            _git(copy, "clean", "-ffdXq")            # installed dependencies and builds of the old commit
        for cache in _vs().CACHES:
            shutil.rmtree(copy / cache, ignore_errors=True)
        return ""
    if not _drop(copy, repo):                        # e.g. the copy belongs to another repo of the project
        return "no pude quitar la copia anterior: " + (moved.stderr or "").strip()[:160]
    _git(repo, "worktree", "prune")
    added = _git(repo, "worktree", "add", "--detach", str(copy), new)
    return "" if added.returncode == 0 else "no pude abrir el commit publicado: " + (added.stderr or "").strip()[:160]


def heal(root: Path, project: str, rdir: Path, sid: str, row: dict, target: Path, repo: Path, *,
         held: bool = False) -> tuple[Path | None, str]:
    """`target` exists: open it at the published commit (see the module docstring). (copy or None, message)."""
    import bt_planning_activity as activity
    commit, name = row["commit"], label(row)
    if head(target) == commit:
        return target, f"Ya estaba abierto en {target}."
    paths, session, own = _parts(root, project, rdir, sid, row["version"])
    with contextlib.nullcontext() if held else _vs()._locked(paths["lock"]):
        old = head(target)
        if old == commit:                            # another start moved it while this one waited for the lock
            return target, f"Ya estaba abierto en {target}."
        if not old:
            return None, (f"{target} no es una copia de git válida, así que no sé si guarda algo tuyo: no la toco. "
                          f"Revísala y bórrala a mano para abrir la {name} de {sid}.")
        stopped = set() if held else _vs().halt(paths, session, own)[1]
        busy = in_use(target, own, session)
        if busy:
            return None, f"No puedo mover la copia de {sid} a la {name}: {busy}. Ciérralo y vuelve a pulsar."
        lines = edited(target)
        if lines is None:
            return None, f"Git no pudo leer la copia {target}: no la toco."
        if lines:
            return None, (f"La copia de {sid} está en el commit {old[:7]}, una publicación anterior de la versión "
                          f"{row['version']}, y tiene cambios tuyos: {describe(lines)}. No la muevo a la {name} sin "
                          f"preguntarte: en Plan → Probar elige «Descartar los cambios» (se borran y se abre la "
                          f"publicada) o «Guardar la copia aparte» (queda en {kept_path(target, old)} y se abre la "
                          f"publicada).")
        why = _move(target, repo, old, commit)
        if why:
            return None, f"No pude mover la copia de {sid} a la {name}: {why}"
    activity.record(rdir, "Probar", f"la copia de {sid} v{row['version']} estaba en un commit anterior ({old[:7]}); "
                    f"se movió al publicado ({commit[:7]})", kind="verify", sp=sid)
    told = f" Detuve {len(stopped)} procesos que servían la anterior." if stopped else ""
    return target, (f"La copia de {sid} estaba en un commit anterior ({old[:7]}); la moví a la {name} en "
                    f"{target}.{told}")


# ------------------------------------------------------------------ the owner's choice when the copy has edits

def kept_path(target: Path, old: str) -> Path:
    place, n = target.with_name(f"{target.name}-kept-{old[:7]}"), 2
    while place.exists():
        place, n = target.with_name(f"{target.name}-kept-{old[:7]}-{n}"), n + 1
    return place


def _version(root: Path, project: str, rdir: Path, sid: str):
    import bt_verification as verification
    row = next((r for r in verification.state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row.get("commit") or not verification.SAFE_ID.fullmatch(sid or ""):
        return None
    target = verification.workdir(root, project, verification._req(rdir), sid, row["version"])
    return row, target, verification._repo_with(root, project, row["commit"])


def _settle(root: Path, project: str, rdir: Path, sid: str, keep: bool) -> str:
    import bt_planning_activity as activity
    import bt_verification as verification
    found = _version(root, project, rdir, sid)
    if found is None:
        return f"{sid or 'Ese subplan'} todavía no tiene una versión publicada."
    row, target, repo = found
    if repo is None:
        return "No encuentro el commit de esa versión en los repos del proyecto."
    if not target.exists():
        return verification.open_local(root, project, rdir, sid)[1]
    paths, session, own = _parts(root, project, rdir, sid, row["version"])
    with _vs()._locked(paths["lock"]):
        old = head(target)
        _vs().halt(paths, session, own)
        busy = in_use(target, own, session)
        if busy:
            return f"No puedo tocar la copia de {sid}: {busy}. Ciérralo y vuelve a pulsar."
        lines = edited(target) or []
        if keep:
            place = kept_path(target, old or "0000000")
            owner = _common_repo(target) or repo
            moved = _git(owner, "worktree", "move", str(target), str(place))
            if moved.returncode:
                return f"No pude guardar la copia aparte: {(moved.stderr or '').strip()[:160]}"
            done = f"guardaste la copia de {sid} ({old[:7]}) en {place}"
        else:
            if not _drop(target, repo):
                return f"No pude borrar la copia {target}."
            done = f"descartaste los cambios de la copia de {sid} ({old[:7]})" + \
                (f": {describe(lines)}" if lines else "")
        activity.record(rdir, "Tú", done, kind="verify", sp=sid)
        opened, message = verification.open_local(root, project, rdir, sid, held=True)
    return (f"Listo: {done}. " if opened else f"{done[:1].upper()}{done[1:]}, pero: ") + message


def discard(root: Path, project: str, rdir: Path, sid: str) -> str:
    """The owner chose to drop the copy's edits: stop its servers, remove it and open the published commit."""
    return _settle(root, project, rdir, sid, keep=False)


def keep_aside(root: Path, project: str, rdir: Path, sid: str) -> str:
    """The owner chose to keep the copy's edits: move it to `<SP>-v<N>-kept-<sha7>` and open the published commit."""
    return _settle(root, project, rdir, sid, keep=True)


def stale(target: Path, row: dict) -> dict | None:
    """For the page: None when the copy is at the published commit (or absent), else {old, edits}."""
    if not target.exists() or not row.get("commit"):
        return None
    old = head(target)
    if old == row["commit"]:
        return None
    return {"old": old, "edits": (edited(target) or []) if old else []}
