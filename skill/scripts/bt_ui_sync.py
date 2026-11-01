"""Write `@bitacora/ui` into a child project's repository and commit it on its default branch (D-280).

Owner, 2026-10-31: the pool is the single source of UI components; a change in it reaches the project «directo, sin
paso intermedio». So `sync` writes the package (package.json, LICENSES.md, `src/**` and the project's own theme as
`themes/<project>.css`) into `<repo>/packages/bitacora-ui`, records what it wrote in `packages/bitacora-ui/SYNC.json`
(pool version, digest, the metodologia commit that last changed the pool) and commits only that path on the
project's default branch. No check gates it. It never touches the project's other files or its checked-out branch:

- when the default branch is checked out in some worktree, the files are written there and `git commit -- <path>`
  commits that path alone (refused when the path has uncommitted edits: they are someone's, never overwritten);
- otherwise the commit is built with plumbing (a temporary index from the branch, `commit-tree`, a compare-and-swap
  `update-ref`), so no checkout moves.

Same pool, same commit: a second sync finds the tree unchanged and commits nothing. A project opts in with
`"ui": {"sync": true, "repo": "<role>", "branch": "<default>", "push": false}` in its bitácora `project.json`;
`sync_all` (run by `bt_integrate` after a merge that changes `skill/ui/`) syncs every opted-in project. A new project
with a UI opts in by default (D-290): `adopt` writes the opt-in and does the first sync, or `first_sync` does it when
the repository is registered later; projects without the key keep the explicit opt-in.

Development (D-293): `write_dev` puts a pool under development (a worktree's `skill/ui`) into a project working tree
without committing, so its dev server hot-reloads; its `SYNC.json` says `"dev": true` and its `pool` is not a digest,
so the project's guard fails on it. A dev write is the only uncommitted content `sync` and `write_dev` overwrite;
`restore` puts the committed copy back. `bt_ui_watch` (`components watch`) drives both.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import bt_ui

TARGET = "packages/bitacora-ui"
STAMP = "SYNC.json"
REPO_ROOT = bt_ui.SKILL_ROOT.parent


class SyncError(RuntimeError):
    pass


def _git(repo: Path, *args: str, env: dict | None = None, input_: str | None = None, check: bool = True) -> str:
    base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, input=input_,
                          env={**base, **(env or {})}, check=False)
    if check and done.returncode:
        raise SyncError(f"git {' '.join(args[:3])} in {repo}: {(done.stderr or done.stdout).strip()[-400:]}")
    return done.stdout.strip() if done.returncode == 0 else ""


# ------------------------------------------------------------------------------------------------ what is written
def source_commit(ui: Path | None = None) -> str:
    """The metodologia commit that last changed the pool (stable across unrelated commits, so syncs stay idempotent)."""
    try:
        if ui is not None and Path(ui) != bt_ui.UI:
            return _git(Path(ui), "log", "-1", "--format=%H", "--", ".", check=False)
        return _git(REPO_ROOT, "log", "-1", "--format=%H", "--", "skill/ui", check=False)
    except (OSError, SyncError):
        return ""


def payload(project: str, ui: Path | None = None, dev: bool = False) -> dict[str, bytes]:
    """Relative path under `packages/bitacora-ui` → bytes, SYNC.json included. `ui`: another copy of the pool (default
    this checkout's). `dev`: a development copy (D-293): the stamp's `pool` is `dev-<digest>`, never a digest, so the
    project's guard (`packages/bitacora-ui` equals `SYNC.json`'s pool) fails on it."""
    base = Path(ui or bt_ui.UI)
    files = bt_ui.files(project, ui)
    out = {}
    for f in files:
        rel = f.relative_to(base).as_posix()
        out[rel] = f.read_bytes()
    pkg = bt_ui.package(ui)
    pool = bt_ui.digest(files, ui)
    stamp = {"name": pkg["name"], "version": pkg["version"], "pool": pool,
             "theme": f"themes/{project}.css" if bt_ui.theme_path(project, ui) else None,
             "source": "metodologia skill/ui", "source_commit": source_commit(ui),
             "note": "Written by `bitacora.py components sync`; change the pool in metodologia, never this copy (D-280)."}
    if dev:
        stamp.update(pool=f"dev-{pool}", dev=True, dev_pool=pool, dev_source=str(base), written=_content_digest(out),
                     note="DEVELOPMENT COPY written by `bitacora.py components watch --into` (D-293): never commit or "
                          "deploy it. `components watch --into <this tree> --restore` (or `components sync <project>` "
                          "on the default branch's worktree) puts the committed copy back.")
    out[STAMP] = (json.dumps(stamp, indent=1, ensure_ascii=False) + "\n").encode()
    return out


def _content_digest(data: dict[str, bytes]) -> str:
    """Digest of a package's files (SYNC.json and node_modules excluded): what a dev write wrote, to tell it from a
    later hand edit."""
    h = hashlib.sha256()
    for rel in sorted(r for r in data if r != STAMP and not _installed(r)):
        h.update(rel.encode() + b"\0" + data[rel] + b"\0")
    return h.hexdigest()[:16]


def _on_disk(dest: Path) -> dict[str, bytes]:
    return {p.relative_to(dest).as_posix(): p.read_bytes() for p in sorted(dest.rglob("*"))
            if p.is_file() and not _installed(p.relative_to(dest).as_posix())} if dest.is_dir() else {}


def dev_write(dest: Path) -> dict | None:
    """The stamp of an intact development copy at `dest` (`packages/bitacora-ui` of a working tree), else None: no
    stamp, a committed stamp, or files edited since the dev write (someone's work, never overwritten)."""
    try:
        stamp = json.loads((Path(dest) / STAMP).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(stamp, dict) or stamp.get("dev") is not True:
        return None
    return stamp if stamp.get("written") == _content_digest(_on_disk(Path(dest))) else None


def _dirty(tree: Path) -> bool:
    """Uncommitted changes under the package path of a working tree that are not npm's and not an intact dev write."""
    status = _git(tree, "status", "--porcelain", "--", TARGET).splitlines()
    foreign = [line for line in status if not _installed(line[3:].strip('"').removeprefix(TARGET + "/"))]
    return bool(foreign) and dev_write(tree / TARGET) is None


def recorded(repo: Path, branch: str) -> dict | None:
    """The SYNC.json the project's default branch holds, or None."""
    text = _git(repo, "show", f"{branch}:{TARGET}/{STAMP}", check=False)
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


# ------------------------------------------------------------------------------------------------ where
def project_meta(project: str, root: Path | None = None) -> dict:
    from bt_core import ROOT
    path = Path(root or ROOT) / project / "project.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def config(project: str, root: Path | None = None) -> dict:
    ui = project_meta(project, root).get("ui")
    return ui if isinstance(ui, dict) else {}


def repo_for(project: str, cfg: dict, root: Path | None = None) -> Path:
    import bt_workspace
    from bt_core import ROOT
    repos = bt_workspace.repos(Path(root or ROOT), project, discover=False)
    role = cfg.get("repo") or (next(iter(repos)) if len(repos) == 1 else "")
    path = repos.get(role) if role else None
    if not path or not Path(path).exists():
        raise SyncError(f"{project}: no repository for the pool (set \"ui\": {{\"repo\": \"<role>\"}} in project.json; "
                        f"roles: {', '.join(repos) or 'none'})")
    return Path(path)


def default_branch(repo: Path, wanted: str = "") -> str:
    if wanted:
        return wanted
    head = _git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    if head.startswith("origin/"):
        return head.split("/", 1)[1]
    for name in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", "-q", f"refs/heads/{name}", check=False):
            return name
    raise SyncError(f"{repo}: no default branch (origin/HEAD, main or master)")


def _checked_out(repo: Path, branch: str) -> Path | None:
    current = None
    for line in _git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            current = Path(line[9:])
        elif line == f"branch refs/heads/{branch}" and current is not None:
            return current
    return None


# ------------------------------------------------------------------------------------------------ commit
def _message(project: str, data: dict[str, bytes]) -> str:
    stamp = json.loads(data[STAMP])
    return (f"chore(ui): sync @bitacora/ui {stamp['version']}+{stamp['pool']} from metodologia (D-280)\n\n"
            f"Written by `bitacora.py components sync {project}`: the component pool is metodologia's (skill/ui) and\n"
            f"reaches this repository directly. Do not edit {TARGET} here; change the pool and it propagates.\n"
            + (f"Source: metodologia {stamp['source_commit'][:12]}\n" if stamp.get("source_commit") else ""))


def _installed(rel: str) -> bool:
    """A path the package manager writes inside the package (npm nests a dependency whose version the root cannot
    hoist under `packages/bitacora-ui/node_modules`): never the sync's, never deleted or counted as an edit."""
    return rel.split("/", 1)[0] == "node_modules"


def _write_tree(dest: Path, data: dict[str, bytes]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for old in sorted(dest.rglob("*"), reverse=True):
        rel = old.relative_to(dest).as_posix()
        if _installed(rel):
            continue
        if old.is_file() and rel not in data:
            old.unlink()
        elif old.is_dir() and not any(old.iterdir()):
            old.rmdir()
    for rel, blob in data.items():
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.is_file() or out.read_bytes() != blob:
            out.write_bytes(blob)


def _commit_in_worktree(worktree: Path, data: dict[str, bytes], message: str) -> str | None:
    if _dirty(worktree):
        raise SyncError(f"{worktree / TARGET} has uncommitted changes: not overwritten (commit or discard them first)")
    _write_tree(worktree / TARGET, data)
    # an ignored `node_modules` named in an exclude pathspec makes `git add` fail (pictures ignores
    # `/packages/*/node_modules`): ignored, it is never staged anyway; else it is excluded (D-294)
    ignored = bool(_git(worktree, "check-ignore", f"{TARGET}/node_modules", check=False))
    _git(worktree, "add", "-A", "--", TARGET, *([] if ignored else [f":(exclude){TARGET}/node_modules"]))
    if not _git(worktree, "diff", "--cached", "--name-only", "--", TARGET):
        return None
    _git(worktree, "commit", "-q", "-m", message, "--", TARGET, env=_identity(worktree))
    return _git(worktree, "rev-parse", "HEAD")


def _identity(repo: Path) -> dict:
    """The repository's own identity when it has one; else a neutral bitácora author (never the owner's name)."""
    env = {}
    if not _git(repo, "config", "user.name", check=False):
        env.update(GIT_AUTHOR_NAME="bitácora", GIT_COMMITTER_NAME="bitácora")
    if not _git(repo, "config", "user.email", check=False):
        env.update(GIT_AUTHOR_EMAIL="bitacora@localhost", GIT_COMMITTER_EMAIL="bitacora@localhost")
    return env


def _commit_plumbing(repo: Path, branch: str, data: dict[str, bytes], message: str) -> str | None:
    old = _git(repo, "rev-parse", f"refs/heads/{branch}")
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        _git(repo, "read-tree", old, env=env)
        # `-f`: the temporary index is the default branch's; without it git compares it with the checked-out branch's
        # HEAD and files and refuses whenever their package differs from the default branch's (D-294)
        _git(repo, "rm", "-r", "--cached", "-f", "-q", "--ignore-unmatch", "--", TARGET, env=env)
        staged = Path(tmp) / "files"
        lines = []
        for rel, blob in sorted(data.items()):
            f = staged / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(blob)
            lines.append(str(f))
        shas = _git(repo, "hash-object", "-w", "--stdin-paths", input_="\n".join(lines) + "\n").splitlines()
        info = "".join(f"100644 {sha}\t{TARGET}/{rel}\n" for sha, rel in zip(shas, sorted(data), strict=True))
        _git(repo, "update-index", "--index-info", env=env, input_=info)
        tree = _git(repo, "write-tree", env=env)
    if tree == _git(repo, "rev-parse", f"{old}^{{tree}}"):
        return None
    new = _git(repo, "commit-tree", tree, "-p", old, input_=message, env=_identity(repo))
    _git(repo, "update-ref", "-m", "bitacora-ui sync (D-280)", f"refs/heads/{branch}", new, old)
    return new


def sync(project: str, repo: Path | None = None, branch: str = "", push: bool | None = None,
         root: Path | None = None, ui: Path | None = None) -> dict:
    """Write and commit the pool into `project`'s repository. Returns {"status": "committed"|"unchanged", "commit",
    "branch", "repo", "pool", "pushed"}; raises SyncError when it cannot (nothing half-written is committed)."""
    if not bt_ui._PROJECT.match(project or ""):
        raise SyncError(f"invalid project {project!r}")
    cfg = config(project, root)
    repo = Path(repo) if repo else repo_for(project, cfg, root)
    if not _git(repo, "rev-parse", "--git-dir", check=False):
        raise SyncError(f"{repo} is not a git repository")
    branch = default_branch(repo, branch or cfg.get("branch", ""))
    if not _git(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False):
        raise SyncError(f"{repo}: branch {branch} does not exist")
    data = payload(project, ui)
    pool = json.loads(data[STAMP])["pool"]
    message = _message(project, data)
    worktree = _checked_out(repo, branch)
    commit = _commit_in_worktree(worktree, data, message) if worktree else _commit_plumbing(repo, branch, data, message)
    result = {"status": "committed" if commit else "unchanged", "commit": commit or _git(repo, "rev-parse", branch),
              "branch": branch, "repo": str(repo), "pool": pool, "pushed": None}
    if commit and (cfg.get("push") is True if push is None else push):
        done = subprocess.run(["git", "-C", str(repo), "push", "origin", branch], capture_output=True, text=True,
                              check=False)
        result["pushed"] = done.returncode == 0 or (done.stderr or done.stdout).strip()[-300:]
    return result


def _work_tree(tree: Path) -> Path:
    tree = Path(tree).expanduser().resolve()
    if _git(tree, "rev-parse", "--is-inside-work-tree", check=False) != "true":
        raise SyncError(f"{tree} is not a git working tree")
    top = Path(_git(tree, "rev-parse", "--show-toplevel"))
    if top.resolve() != tree:
        raise SyncError(f"{tree} is not the top of its working tree ({top})")
    return tree


def check_dev_target(tree: Path) -> Path:
    """The working tree a dev write may go into; refused when its package path holds someone's uncommitted changes."""
    tree = _work_tree(tree)
    if _dirty(tree):
        raise SyncError(f"{tree / TARGET} has uncommitted changes that are not a previous dev write: not overwritten "
                        "(commit or discard them first)")
    return tree


def write_dev(project: str, ui: Path, tree: Path) -> dict:
    """Write the pool at `ui` into `tree/packages/bitacora-ui` WITHOUT committing (D-293): a development copy marked
    `"dev": true`. Returns {"status": "written"|"unchanged", "pool", "path"}; raises SyncError when refused."""
    if not bt_ui._PROJECT.match(project or ""):
        raise SyncError(f"invalid project {project!r}")
    tree = check_dev_target(tree)
    data = payload(project, Path(ui), dev=True)
    dest = tree / TARGET
    before = _on_disk(dest)
    _write_tree(dest, data)
    stamp = json.loads(data[STAMP])
    return {"status": "unchanged" if before == data else "written", "pool": stamp["dev_pool"], "path": str(dest)}


def restore(tree: Path) -> str:
    """Put the committed `packages/bitacora-ui` of `tree` back over an intact dev write. Returns "restored" or
    "clean"; raises SyncError over anything else uncommitted (never someone's edit)."""
    tree = _work_tree(tree)
    status = [line for line in _git(tree, "status", "--porcelain", "--", TARGET).splitlines()
              if not _installed(line[3:].strip('"').removeprefix(TARGET + "/"))]
    if not status:
        return "clean"
    if dev_write(tree / TARGET) is None:
        raise SyncError(f"{tree / TARGET} has uncommitted changes that are not a dev write: not restored")
    if _git(tree, "ls-tree", "-d", "--name-only", "HEAD", TARGET, check=False):
        _git(tree, "checkout", "HEAD", "--", TARGET)
    _git(tree, "clean", "-fdq", "-e", "node_modules", "--", TARGET)
    return "restored"


def adopt(project: str, role: str = "", source: Path | None = None, mockup_fonts: list[str] | None = None,
          root: Path | None = None, off: bool = False) -> dict:
    """Opt `project` into the pool (D-290): the default for every project with a UI, answered «sí» in the
    requirements interview. Writes `"ui": {"sync": true, "repo": <role>, "push": false}` into its `project.json`
    (other keys kept), imports its theme when a token source is given (else the pool's default `theme.css` applies)
    and runs the first sync. With no repository registered yet (a greenfield plan creates it), the opt-in is
    recorded and the result is `pending`: `first_sync` runs when `workspace add <role>` registers it. `off` records
    the owner's «no» (`"sync": false`): nothing is synced and the question is not asked again."""
    if not bt_ui._PROJECT.match(project or ""):
        raise SyncError(f"invalid project {project!r}")
    from bt_core import ROOT
    path = Path(root or ROOT) / project / "project.json"
    data = project_meta(project, root)
    ui = {**(data.get("ui") if isinstance(data.get("ui"), dict) else {}), "sync": not off}
    if role:
        ui["repo"] = role
    ui.setdefault("push", False)
    data["ui"] = ui
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if off:
        return {"status": "declined", "theme": None}
    theme = bt_ui.import_theme(project, Path(source), mockup_fonts or []) if source else bt_ui.theme_path(project)
    try:
        repo = repo_for(project, ui, root)
    except SyncError as exc:
        return {"status": "pending", "reason": str(exc), "theme": str(theme) if theme else None}
    return {**sync(project, repo, root=root), "theme": str(theme) if theme else None}


def first_sync(project: str, role: str, root: Path | None = None) -> dict | None:
    """After `workspace add`: the first sync of an opted-in project whose pool repository was just registered and
    holds no `SYNC.json` yet. None when nothing applies (not opted in, another role, already synced)."""
    cfg = config(project, root)
    if cfg.get("sync") is not True or (cfg.get("repo") and cfg["repo"] != role):
        return None
    repo = repo_for(project, cfg, root)
    branch = default_branch(repo, cfg.get("branch", ""))
    if recorded(repo, branch) is not None:
        return None
    return sync(project, repo, branch, root=root)


def opted_in(root: Path | None = None) -> list[str]:
    from bt_core import ROOT
    base = Path(root or ROOT)
    return sorted(p.parent.name for p in base.glob("*/project.json") if config(p.parent.name, base).get("sync") is True)


def sync_all(note=print, root: Path | None = None) -> dict[str, dict | str]:
    """Sync every opted-in project; a failure is reported, never raised (a merge in metodologia is already done)."""
    out: dict[str, dict | str] = {}
    for project in opted_in(root):
        try:
            r = sync(project, root=root)
            out[project] = r
            note(f"@bitacora/ui → {project}: {r['status']} {r['commit'][:12]} on {r['branch']} (pool {r['pool']})"
                 + (f", push: {r['pushed']}" if r["pushed"] not in (None, True) else ", pushed" if r["pushed"] else ""))
        except (SyncError, OSError) as exc:
            out[project] = str(exc)
            note(f"WARNING @bitacora/ui not synced into {project}: {exc}")
    return out


def describe(result: dict) -> str:
    return (f"{result['status']}: {result['repo']} {result['branch']} {result['commit'][:12]} · pool {result['pool']}"
            + (f" · push {result['pushed']}" if result.get("pushed") is not None else ""))
