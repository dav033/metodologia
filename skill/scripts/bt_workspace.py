"""Workspaces: a project is a named set of repos with roles (e.g. maros → frontend: maros-next, backend: maros-nest).

Portable across machines. <project>/project.json (synced) stores each repo by its git remote plus a home-relative
hint:   {"repos": {"frontend": {"remote": "https://github.com/x/maros-next", "hint": "~/maros-next"}},
         "root": "~/Desktop/eventos"}
Each machine keeps its own local paths in .state/paths.json (not synced) and the reverse index .state/repos.json
({"<normalized local path>": "<project>"}). Local paths are found from the hint, or by scanning the usual folders
for a clone with the same remote, or cloned on demand (`clone_missing`).
Must not import bt_core (bt_core imports this module).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

HOME = Path.home()
SCAN_SKIP = {"appdata", "node_modules", ".git", ".cache", ".npm", "onedrive", "music", "videos", "pictures",
             "saved games", "searches", "links", "favorites", "contacts", "3d objects", "chromescraperprofile"}


# ---------------------------------------------------------------- small helpers

def _key(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").lower().rstrip("/")


def _read(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write(f: Path, data: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def to_hint(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return "~/" + p.relative_to(HOME).as_posix()
    except ValueError:
        return p.as_posix()


def from_hint(hint: str) -> Path:
    return HOME / hint[2:] if hint.startswith("~/") else Path(hint)


def norm_remote(url: str) -> str:
    url = (url or "").strip().lower().rstrip("/")
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^git@([^:]+):", r"\1/", url)
    return re.sub(r"^(https?|ssh)://([^@/]+@)?", "", url)


def remote_of(repo: Path) -> str:
    """origin URL read straight from .git/config (fast: no git process)."""
    cfg = repo / ".git" / "config"
    try:
        text = cfg.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = re.search(r'\[remote "origin"\][^\[]*?url\s*=\s*(\S+)', text, re.S)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- stored model

def meta(root: Path, project: str) -> dict:
    data = _read(root / project / "project.json")
    if "repo" in data and "repos" not in data:  # legacy: single absolute path
        data["repos"] = {Path(data["repo"]).name: data.pop("repo")}
    repos = data.setdefault("repos", {})
    for role, spec in list(repos.items()):
        if isinstance(spec, str):  # legacy: absolute path → portable entry
            repos[role] = {"remote": remote_of(Path(spec)), "hint": to_hint(Path(spec))}
    if data.get("root") and not str(data["root"]).startswith("~/"):
        data["root"] = to_hint(Path(data["root"]))
    return data


def _save_meta(root: Path, project: str, data: dict) -> None:
    _write(root / project / "project.json", data)


def _local(root: Path) -> dict:
    return _read(root / ".state" / "paths.json")


def _remember(root: Path, project: str, role: str, path: Path) -> None:
    local = _local(root)
    local[f"{project}/{role}"] = Path(path).resolve().as_posix()
    _write(root / ".state" / "paths.json", local)
    index = _read(root / ".state" / "repos.json")
    index[_key(path)] = project
    _write(root / ".state" / "repos.json", index)


# ---------------------------------------------------------------- resolution

def _scan_for(remote: str, max_depth: int = 3) -> Path | None:
    want = norm_remote(remote)
    if not want:
        return None
    stack = [(HOME, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = [e for e in d.iterdir() if e.is_dir()]
        except OSError:
            continue
        for e in entries:
            if e.name.lower() in SCAN_SKIP or e.name.startswith("."):
                continue
            if (e / ".git").exists():
                if norm_remote(remote_of(e)) == want and "before" not in e.name.lower():
                    return e
                continue  # don't descend into repos
            if depth + 1 < max_depth:
                stack.append((e, depth + 1))
    return None


def repos(root: Path, project: str, discover: bool = True) -> dict[str, Path]:
    """role → local path on THIS machine. Missing clones come back as their hint path (not existing)."""
    data, local, out = meta(root, project), _local(root), {}
    for role, spec in data["repos"].items():
        known = local.get(f"{project}/{role}")
        if known and Path(known).exists():
            out[role] = Path(known)
            continue
        hinted = from_hint(spec.get("hint", ""))
        found = None
        if hinted.exists() and (not spec.get("remote") or norm_remote(remote_of(hinted)) == norm_remote(spec["remote"])):
            found = hinted
        elif discover and spec.get("remote"):
            found = _scan_for(spec["remote"])
        if found:
            _remember(root, project, role, found)
            out[role] = found
        else:
            out[role] = hinted
    return out


def missing(root: Path, project: str) -> list[str]:
    return [role for role, p in repos(root, project).items() if not p.exists()]


def clone_missing(root: Path, project: str) -> list[str]:
    """Clone every repo of the workspace this machine doesn't have, at its hint path."""
    done = []
    for role, spec in meta(root, project)["repos"].items():
        target = repos(root, project)[role]
        if target.exists() or not spec.get("remote"):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(["git", "clone", "-q", spec["remote"], str(target)], capture_output=True, text=True)
        if res.returncode == 0:
            _remember(root, project, role, target)
            done.append(role)
    return done


def reindex(root: Path) -> None:
    """Rebuild this machine's path → project index from every project's workspace."""
    index = {}
    for d in root.iterdir() if root.exists() else []:
        if d.is_dir() and not d.name.startswith(".") and (d / "project.json").exists():
            for p in repos(root, d.name).values():
                if p.exists():
                    index[_key(p)] = d.name
            r = meta(root, d.name).get("root")
            if r and from_hint(r).exists():
                index[_key(from_hint(r))] = d.name
    _write(root / ".state" / "repos.json", index)


# ---------------------------------------------------------------- edits

def add_repo(root: Path, project: str, path: Path, role: str | None = None) -> str:
    data = meta(root, project)
    path = Path(path).resolve()
    remote = remote_of(path)
    for existing, spec in list(data["repos"].items()):  # same repo under another role → replace
        if (remote and norm_remote(spec.get("remote", "")) == norm_remote(remote)) or spec.get("hint") == to_hint(path):
            del data["repos"][existing]
    role = role or re.sub(r"[^a-z0-9-]+", "-", path.name.lower()).strip("-") or "main"
    data["repos"][role] = {"remote": remote, "hint": to_hint(path)}
    _save_meta(root, project, data)
    _remember(root, project, role, path)
    return role


def remove_repo(root: Path, project: str, role: str) -> None:
    data = meta(root, project)
    data["repos"].pop(role, None)
    _save_meta(root, project, data)
    local = _local(root)
    gone = local.pop(f"{project}/{role}", None)
    _write(root / ".state" / "paths.json", local)
    if gone:
        index = _read(root / ".state" / "repos.json")
        index.pop(_key(gone), None)
        _write(root / ".state" / "repos.json", index)


def set_root(root: Path, project: str, workdir_path: Path | None) -> None:
    """The folder the user opens for this workspace (sessions there resolve to the project). Repos inside it still
    win by longest match, so a root never steals another project's repo."""
    data = meta(root, project)
    index = _read(root / ".state" / "repos.json")
    if data.get("root"):
        index.pop(_key(from_hint(data["root"])), None)
    if workdir_path:
        if _key(workdir_path) == _key(HOME):
            raise SystemExit("The home folder spans every project; it can't be a workspace root.")
        data["root"] = to_hint(workdir_path)
        index[_key(workdir_path)] = project
    else:
        data.pop("root", None)
    _save_meta(root, project, data)
    _write(root / ".state" / "repos.json", index)


def save_migrated(root: Path, project: str) -> None:
    """Persist the portable format for a project.json still in a legacy format."""
    data = meta(root, project)
    _save_meta(root, project, data)
    for role, p in repos(root, project).items():
        if p.exists():
            _remember(root, project, role, p)


# ---------------------------------------------------------------- queries

def workdir(root: Path, project: str) -> Path | None:
    """Where an executor session starts: the root, else the common parent of all local repos."""
    data = meta(root, project)
    if data.get("root"):
        return from_hint(data["root"])
    paths = [str(p) for p in repos(root, project).values()]
    if not paths:
        return None
    return Path(paths[0]) if len(paths) == 1 else Path(os.path.commonpath(paths))


def project_for_path(root: Path, path: str | Path) -> str | None:
    """Project whose registered repo (or root) contains `path` on this machine (longest match wins)."""
    index_file = root / ".state" / "repos.json"
    if not index_file.exists():
        reindex(root)
    k = _key(path)
    rk = _key(root)
    if k == rk or k.startswith(rk + "/"):  # inside the bitácora itself: its folder names the project
        first = k[len(rk):].strip("/").split("/")[0]
        return first if first and not first.startswith(".") else None
    best, best_len = None, -1
    for repo_key, project in _read(index_file).items():
        if (k == repo_key or k.startswith(repo_key + "/")) and len(repo_key) > best_len:
            best, best_len = project, len(repo_key)
    return best


def projects_in_transcript(root: Path, transcript: Path) -> set[str]:
    """Projects whose repos the session has touched (paths in tool inputs)."""
    found: set[str] = set()
    try:
        with transcript.open(encoding="utf-8") as fh:
            for line in fh:
                if '"tool_use"' not in line:
                    continue
                for m in re.finditer(r'"(?:file_path|notebook_path|path)":\s*"([^"]+)"', line):
                    p = project_for_path(root, m.group(1).replace("\\\\", "\\"))
                    if p:
                        found.add(p)
    except Exception:
        pass
    return found


def describe(root: Path, project: str) -> str:
    rs = repos(root, project, discover=False)
    return ", ".join(f"{role} → `{p.as_posix()}`{'' if p.exists() else ' (not cloned here)'}"
                     for role, p in rs.items()) or "no repos registered"
