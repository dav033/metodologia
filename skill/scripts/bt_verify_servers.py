"""Start the test servers of a subplan version, clean, and open it in the browser («Probar»).

Owner, 2026-10-29 (pictures REQ-021): «quiero que cuando le doy click me arranque el servidor o servidores de pruebas y
que se me abra el navegador con la versión en específico». Owner, 2026-10-30, at the machine: «la URL donde se prueba
debe aparecer directamente; al darle click debe matar todos los procesos asociados a esa URL y arrancar limpio el
worktree correcto».

A project describes its servers in `<bitácora>/<project>/verify-servers.json`, kept by the owner, with no secret
values; a requirement may carry its own `verify-servers.json` in its folder, which wins (a test database per REQ)::

    {"env_file": "~/dev/pictures/.env.local",
     "env": {"DATABASE_URL": "${PICTURES_REQ021_DATABASE_URL}", "PYTHON_BACKEND_URL": "http://127.0.0.1:{port:ai-api}"},
     "prepare": [{"unless": "node_modules", "run": "npm ci --prefer-offline --no-audit --no-fund"}],
     "servers": [{"name": "ai-api", "port": 8000, "ready": "/healthz", "run": "uv run … --port {port}"},
                 {"name": "web", "port": 3000, "ready": "/", "open": "/", "run": "npm run dev -- --port {port}"}],
     "accounts": "optional: who to sign in as and where the password comes from (never the password itself)"}

`${NAME}` is read from the owner's secret files (`verifier.secret_files`) when the servers start and lands only in a
0600 file next to the copy; `{port:<server>}` and `{port}` are the ports actually used.

Every start is clean (`start`): under the version's lock it stops everything of that version (its tmux session, every
process carrying its mark, servers listening inside its copy: `bt_verify_procs`), checks the copy is exactly the
published commit with no edits, drops the framework cache (`.next`) and the old logs, picks its ports (the ones it had,
else the recipe's; a port held by anything else — another version, an unrelated service — is skipped, never killed),
and runs prepare plus every server in one tmux session (bt_agent_terminal). The state file says the phase, so the
waiting tab shows progress and a failure with its log tail. Standard library only.
"""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import bt_agent_terminal as terminal
import bt_verification as verification
import bt_verify_procs as procs

RECIPE = "verify-servers.json"
_NAME = re.compile(r"[a-z][a-z0-9-]{0,30}")
_SECRET = re.compile(r"\$\{([A-Z][A-Z0-9_]{0,80})\}")
_PORT = re.compile(r"\{port(?::([a-z][a-z0-9-]{0,30}))?\}")
CACHES = (".next",)                       # framework build caches a dev server rebuilds; dropped on every clean start
STALE_START = 180                         # seconds a start may stay «stopping» before the page calls it interrupted


def recipe(root: Path, project: str, rdir: Path | None = None) -> dict | None:
    """The requirement's server recipe, else the project's; None when there is none or it is malformed."""
    for place in ([Path(rdir) / RECIPE] if rdir else []) + [Path(root) / project / RECIPE]:
        if not place.is_file():
            continue
        try:
            data = json.loads(place.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            return None
        servers = data.get("servers") if isinstance(data, dict) else None
        if not isinstance(servers, list) or not servers or not all(
                isinstance(s, dict) and _NAME.fullmatch(str(s.get("name", ""))) and isinstance(s.get("run"), str)
                and isinstance(s.get("port"), int) for s in servers):
            return None
        return data
    return None


def slug(sid: str, version: object) -> str:
    """A subplan version is `SP-8-v1`; a task snapshot is `T10.5-a1-098ef7ce` (the attempt that produced it)."""
    return f"{sid}-v{version}" if str(version).isdigit() else f"{sid}-{version}"


def _files(root: Path, project: str, rdir: Path, sid: str, version: object) -> dict[str, Path]:
    copy = verification.workdir(root, project, verification._req(rdir), sid, 0).parent / slug(sid, version)
    base = copy
    return {"copy": copy, "state": Path(f"{base}.servers.json"), "env": Path(f"{base}.env"),
            "script": Path(f"{base}.run.sh"), "logs": Path(f"{base}.logs"), "lock": Path(f"{base}.lock")}


def session_name(project: str, rdir: Path, sid: str, version: object) -> str:
    name = f"bv-{project}-{verification._req(rdir)}-{slug(sid, version)}"
    return re.sub(r"[.:]", "_", name)[:80]               # tmux reads «.» and «:» in a target as window and pane


def mark(project: str, rdir: Path, sid: str, version: object) -> str:
    """What every process of the version carries in its environment (`BITACORA_VERIFY_ID`)."""
    return f"{project}/{verification._req(rdir)}/{slug(sid, version)}"


_TASK = re.compile(r"T\d+(?:\.\d+)*")
_ATTEMPT = re.compile(r"-(a\d+-[0-9a-f]{4,})$")


def _row(rdir: Path, sid: str, root: Path | None = None, project: str = "") -> dict | None:
    """What «Probar» starts for `sid`: a subplan's published version, or — for a task whose open decision waits for the
    owner's manual evidence — the snapshot of the attempt that decision names. None when there is nothing to start."""
    if _TASK.fullmatch(sid or "") and root is not None:
        return task_target(root, project, rdir, sid)
    row = next((r for r in verification.state(rdir)["subplans"] if r["id"] == sid), None)
    return {**row, "kind": "subplan"} if row and row.get("version") else None


def task_target(root: Path, project: str, rdir: Path, task: str) -> dict | None:
    import bt_durable_panel
    for decision in bt_durable_panel.decisions(rdir):
        manual = decision.get("manual")
        if not manual or manual["task"] != task:
            continue
        commit = snapshot_of(root, project, manual["attempt"])
        found = _ATTEMPT.search(manual["attempt"])
        if commit:
            return {"id": task, "kind": "task", "commit": commit, "attempt": manual["attempt"], "decision": decision["id"],
                    "version": found.group(1) if found else manual["attempt"][-12:]}
    return None


def snapshot_of(root: Path, project: str, attempt: str) -> str | None:
    """The snapshot commit an attempt left (`refs/m3/handoff/…`, subject «m3 snapshot <attempt>»)."""
    import bt_workspace as ws
    for repo in ws.repos(root, project).values():
        listed = verification._git(Path(repo), "for-each-ref", "refs/m3/handoff/", "--format=%(objectname) %(contents:subject)")
        for line in listed.stdout.splitlines():
            sha, _, subject = line.partition(" ")
            if subject.strip() == f"m3 snapshot {attempt}" and verification.SHA.fullmatch(sha):
                return sha
    return None


def _open(root: Path, project: str, rdir: Path, sid: str, row: dict) -> tuple[Path | None, str]:
    """The copy to start: a subplan version through bt_verification; a task snapshot the same way, detached, outside
    every repository."""
    if row.get("kind") != "task":
        return verification.open_local(root, project, rdir, sid)
    target = _files(root, project, rdir, sid, row["version"])["copy"]
    repo = verification._repo_with(root, project, row["commit"])
    if repo is None:
        return None, "No encuentro el commit de ese intento en los repos del proyecto."
    if target.exists():
        return target, f"Ya estaba abierto en {target}."
    target.parent.mkdir(parents=True, exist_ok=True)
    verification._git(repo, "worktree", "prune")
    done = verification._git(repo, "worktree", "add", "--detach", str(target), row["commit"])
    if done.returncode != 0:
        return None, "No pude abrir el intento: " + (done.stderr or "").strip()[:200]
    return target, f"Intento {row['version']} de {sid} abierto en {target}."


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


@contextlib.contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


# ------------------------------------------------------------------ ports

def _reserved(copy: Path, own_state: Path) -> set[int]:
    """Ports of the project's other versions that run or are starting: never handed to this one."""
    taken: set[int] = set()
    for state in copy.parent.glob("*.servers.json"):
        if state == own_state:
            continue
        data = _load(state)
        live = data.get("phase") not in ("failed", "stopped") and isinstance(data.get("session"), str) and \
            terminal.exists(data["session"])
        starting = data.get("phase") in ("stopping", "preparing") and time.time() - float(data.get("started_at") or 0) < STALE_START
        if live or starting:
            taken.update(p for p in (data.get("ports") or {}).values() if isinstance(p, int))
    return taken


def choose_ports(servers: list[dict], preferred: dict[str, int], own: str, copy: Path, reserved: set[int],
                 table: dict[int, set[int]] | None = None) -> dict[str, int]:
    """A port per server: the preferred one (the version's earlier port, else the recipe's) when it is free or held only
    by this version's own processes; else the next such port. A port held by anything else is skipped, never taken."""
    table = procs.listeners() if table is None else table
    chosen: dict[str, int] = {}

    def usable(port: int) -> bool:
        if port in chosen.values() or port in reserved or not 0 < port < 65536:
            return False
        holders = table.get(port) or set()
        if holders:
            return all(procs.environ_mark(p) == own or procs.works_in(p, copy) for p in holders)
        return not procs.port_busy(port)

    for server in servers:
        port = int(preferred.get(server["name"]) or server["port"])
        for _ in range(200):
            if usable(port):
                break
            port += 1
        chosen[server["name"]] = port
    return chosen


def _url(data: dict, ports: dict[str, int]) -> str:
    server = next((s for s in data["servers"] if s.get("open")), data["servers"][-1])
    return f"http://localhost:{ports[server['name']]}{server.get('open') if isinstance(server.get('open'), str) else '/'}"


def planned(root: Path, project: str, rdir: Path, sid: str) -> dict:
    """Where the version will answer, before it is started: {url, ports}; empty when there is nothing to start."""
    data, row = recipe(root, project, rdir), _row(rdir, sid, root, project)
    if data is None or row is None:
        return {"url": "", "ports": {}}
    paths = _files(root, project, rdir, sid, row["version"])
    state = _load(paths["state"])
    if state.get("ports") and state.get("phase") in ("preparing", "servers", "stopping"):
        ports = {k: int(v) for k, v in state["ports"].items()}
    else:
        own = mark(project, rdir, sid, row["version"])
        ports = choose_ports(data["servers"], state.get("ports") or {}, own, paths["copy"], _reserved(paths["copy"], paths["state"]))
    return {"url": _url(data, ports), "ports": ports}


# ------------------------------------------------------------------ environment and script

def _secrets(project: str) -> dict[str, str]:
    import bt_config
    import bt_verifier_env
    found: dict[str, str] = {}
    for source in bt_config.get("verifier.secret_files", []) or []:
        found.update({k: v for k, v in bt_verifier_env.load(bt_verifier_env.path_for(source, project))[0] if k not in found})
    return found


def _fill(text: str, ports: dict[str, int], own: int | None, secrets: dict[str, str]) -> str:
    text = _PORT.sub(lambda m: str(ports[m.group(1)] if m.group(1) else own), text)
    return _SECRET.sub(lambda m: secrets.get(m.group(1), ""), text)


def environment(project: str, data: dict, ports: dict[str, int]) -> tuple[dict[str, str], list[str]]:
    """(the servers' environment, secret names not found): the recipe's env_file, then its `env` with ports and the
    owner's secrets filled in."""
    import bt_verifier_env
    env = dict(bt_verifier_env.load(os.path.expanduser(str(data.get("env_file") or "")))[0]) if data.get("env_file") else {}
    wanted = {n for v in (data.get("env") or {}).values() for n in _SECRET.findall(str(v))}
    secrets = _secrets(project) if wanted else {}
    env.update({str(k): _fill(str(v), ports, None, secrets) for k, v in (data.get("env") or {}).items()})
    return env, sorted(wanted - set(secrets))


def _script(paths: dict[str, Path], data: dict, ports: dict[str, int], own: str = "", login: bool = True) -> str:
    logs = paths["logs"]
    q = lambda p: shlex.quote(str(p))  # noqa: E731
    steps = [s for s in data.get("prepare") or [] if isinstance(s, dict) and isinstance(s.get("run"), str)]
    lines = ["set -u", "set -o pipefail", f"export {procs.MARK}={shlex.quote(own)}", f"cd {q(paths['copy'])}",
             "set -a", f". {q(paths['env'])}", "set +a", f"mkdir -p {q(logs)}",
             f"phase() {{ printf '%s\\n' \"$1\" > {q(logs / 'phase')}; }}",
             f'say() {{ echo "[bitácora] $1" | tee -a {q(logs / "prepare.log")}; }}',
             'say "preparando la versión…"']
    for number, step in enumerate(steps, 1):
        text = step["run"]
        label = shlex.quote(f"prepare {number}/{len(steps)} {text[:80]}")
        guard = f"[ -e {shlex.quote(str(step['unless']))} ] || " if step.get("unless") else ""
        failed = shlex.quote(f"failed {text[:80]}")
        lines.append(f"phase {label}")
        lines.append(f"{guard}{{ {text} ; }} 2>&1 | tee -a {q(logs / 'prepare.log')} || "
                     f"{{ phase {failed}; say {shlex.quote('falló: ' + text[:60])}; exit 1; }}")
    lines.append("phase servers")
    for server in data["servers"]:
        log = q(logs / f"{server['name']}.log")
        lines.append(f"say \"{server['name']} en el puerto {ports[server['name']]}\"")
        auth = "" if login else "".join(f"{k}={shlex.quote(str(v))} " for k, v in (server.get("local_auth") or {}).items()
                                         if re.fullmatch(r"[A-Z][A-Z0-9_]*", str(k)))
        lines.append(f"( {auth}{_fill(server['run'], ports, ports[server['name']], {})} ) > {log} 2>&1 &")
        lines.append(f"echo $! > {q(logs / (server['name'] + '.pid'))}")
    lines += [f'say "servidores en marcha; registros en {logs}"', "wait"]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ stop, clean, start

def _pane_pids(name: str) -> set[int]:
    if not terminal.exists(name):
        return set()
    try:
        out = terminal._run("list-panes", "-s", "-t", f"={name}", "-F", "#{pane_pid}").stdout
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return set()
    return {int(p) for p in out.split() if p.isdigit()}


def stop_version(paths: dict[str, Path], name: str, own: str) -> set[int]:
    """Stop everything of the version: its tmux session and every process it owns (bt_verify_procs.owned). Returns the
    pids stopped. Processes of other versions or unrelated services are never touched."""
    roots = _pane_pids(name)
    stopped = procs.terminate(procs.owned(own, paths["copy"], roots))
    terminal.kill(name)
    stopped |= procs.terminate(procs.owned(own, paths["copy"]))          # anything spawned while the rest was stopping
    return stopped


def _dirty(copy: Path, commit: str) -> str:
    """Why the copy is not exactly the published commit, or "" when it is."""
    head = verification._git(copy, "rev-parse", "HEAD").stdout.strip()
    if head != commit:
        return f"la copia está en {head[:10] or '¿?'} y la versión es {commit[:10]}"
    changed = [line[3:] for line in verification._git(copy, "status", "--porcelain", "--untracked-files=no").stdout.splitlines()]
    if changed:
        return "la copia tiene cambios en " + ", ".join(changed[:5]) + (" y más" if len(changed) > 5 else "")
    return ""


def _fail(paths: dict[str, Path], state: dict, message: str) -> dict:
    _save(paths["state"], {**state, "phase": "failed", "error": message, "failed_at": time.time()})
    return {"ok": False, "message": message, "url": state.get("url", "")}


def start(root: Path, project: str, rdir: Path, sid: str, run: str = "", login: bool = False) -> dict:
    """Stop everything of the version, then start it clean from its published commit. {ok, message, url}.

    Without `login` a server with `local_auth` in the recipe (pictures: `AUTH_LOCAL_SIN_RESTRICCIONES=1` on the web
    server, its own development-only local mode) starts with it, so the owner enters already signed in; `login` starts
    it as in production, for tests of a given account or role (owner, 2026-10-30: «que en local no pida login», D-202)."""
    data, row = recipe(root, project, rdir), _row(rdir, sid, root, project)
    if data is None:
        return {"ok": False, "message": f"El proyecto no tiene receta de servidores de prueba ({project}/{RECIPE}).", "url": ""}
    if row is None:
        return {"ok": False, "message": f"{sid} todavía no tiene una versión publicada que probar.", "url": ""}
    paths, name = _files(root, project, rdir, sid, row["version"]), session_name(project, rdir, sid, row["version"])
    own = mark(project, rdir, sid, row["version"])
    with _locked(paths["lock"]):
        previous = _load(paths["state"])
        state = {"session": name, "mark": own, "commit": row["commit"], "version": row["version"], "run": run or uuid.uuid4().hex,
                 "login": bool(login) or not has_local_auth(data),
                 "started_at": time.time(), "phase": "stopping", "ports": previous.get("ports") or {},
                 "url": previous.get("url", "")}
        _save(paths["state"], state)
        stopped = stop_version(paths, name, own)
        target, message = _open(root, project, rdir, sid, row)
        if target is None:
            return _fail(paths, state, message)
        why = _dirty(target, row["commit"])
        if why:
            return _fail(paths, state, f"No arranco sobre una copia que no es la versión publicada: {why}. Revísala o "
                                       "pulsa «Cerrar la copia» y vuelve a probar.")
        for cache in CACHES:
            shutil.rmtree(target / cache, ignore_errors=True)
        shutil.rmtree(paths["logs"], ignore_errors=True)
        paths["logs"].mkdir(parents=True)
        with _locked(paths["copy"].parent / ".ports.lock"):          # two versions starting at once never share a port
            ports = choose_ports(data["servers"], previous.get("ports") or {}, own, paths["copy"],
                                 _reserved(paths["copy"], paths["state"]))
            env, missing = environment(project, data, ports)
            if missing:
                return _fail(paths, state, f"Falta {', '.join(missing)} en tus archivos de secretos "
                                           "(verifier.secret_files): no arranco los servidores sin ella.")
            state.update(ports=ports, url=_url(data, ports), phase="preparing",
                         ready={s["name"]: s.get("ready", "/") for s in data["servers"]}, stopped=sorted(stopped))
            _save(paths["state"], state)
        paths["env"].touch(mode=0o600, exist_ok=True)
        os.chmod(paths["env"], 0o600)
        paths["env"].write_text("".join(f"{k}={shlex.quote(v)}\n" for k, v in env.items()), encoding="utf-8")
        paths["script"].write_text(_script(paths, data, ports, own, login=state["login"]), encoding="utf-8")
        try:
            terminal.start(name, paths["copy"], f"bash {shlex.quote(str(paths['script']))}")
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
            return _fail(paths, state, f"No pude arrancar los servidores: {exc}")
    told = f" Detuve {len(stopped)} procesos de la versión anterior." if stopped else ""
    return {"ok": True, "url": state["url"],
            "message": f"Arrancando {', '.join(ports)} de {sid} (versión {row['version']}) desde cero.{told}"}


def has_local_auth(data: dict | None) -> bool:
    """Does the recipe let a version start already signed in (a server with `local_auth`)?"""
    return any(isinstance(s, dict) and s.get("local_auth") for s in (data or {}).get("servers") or [])


def begin(root: Path, project: str, rdir: Path, sid: str, login: bool = False) -> dict:
    """What «Probar» does: mark the version as restarting right away (the waiting tab never mistakes the old servers for
    the new ones) and run `start` in the background; the tab follows its phases. {ok, message}."""
    if recipe(root, project, rdir) is None:
        return {"ok": False, "message": f"El proyecto no tiene receta de servidores de prueba ({project}/{RECIPE})."}
    row = _row(rdir, sid, root, project)
    if row is None:
        return {"ok": False, "message": f"{sid} todavía no tiene una versión publicada que probar."}
    paths, run = _files(root, project, rdir, sid, row["version"]), uuid.uuid4().hex
    _save(paths["state"], {**_load(paths["state"]), "phase": "stopping", "run": run, "started_at": time.time(), "error": ""})
    threading.Thread(target=start, args=(root, project, rdir, sid, run, login), name=f"probar-{sid}", daemon=True).start()
    return {"ok": True, "message": f"Reiniciando {sid} desde cero."}


def stop(root: Path, project: str, rdir: Path, sid: str) -> str:
    """Stop the version's servers and everything they started."""
    row = _row(rdir, sid, root, project)
    if row is None:
        return "No había servidores en marcha."
    paths, name = _files(root, project, rdir, sid, row["version"]), session_name(project, rdir, sid, row["version"])
    with _locked(paths["lock"]):
        had = terminal.exists(name)
        stopped = stop_version(paths, name, mark(project, rdir, sid, row["version"]))
        state = _load(paths["state"])
        if state:
            _save(paths["state"], {**state, "phase": "stopped"})
    return f"Servidores de {sid} detenidos." if had or stopped else "No había servidores en marcha."


# ------------------------------------------------------------------ status

def _answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as reply:          # noqa: S310 - loopback only, built here
            return reply.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except (OSError, ValueError):
        return False


def _exited(pidfile: Path) -> bool:
    try:
        pid = int(pidfile.read_text().strip())
    except (OSError, ValueError):
        return False                     # not started yet: it is still preparing
    return not procs.alive(pid)


def _tail(path: Path, lines: int = 20) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def _step(text: str) -> str:
    found = re.match(r"prepare (\d+)/(\d+) (.*)", text)
    return f"Preparando ({found.group(1)} de {found.group(2)}): {found.group(3)}" if found else "Preparando la versión…"


def status(root: Path, project: str, rdir: Path, sid: str) -> dict:
    """{state: stopped|preparing|ready|failed, step, url, servers: {name: bool}, log, elapsed}: what the tab polls."""
    row = _row(rdir, sid, root, project)
    out = {"state": "stopped", "step": "", "url": "", "servers": {}, "log": "", "elapsed": 0, "ports": {}}
    if row is None:
        return out
    paths = _files(root, project, rdir, sid, row["version"])
    current, name = _load(paths["state"]), session_name(project, rdir, sid, row["version"])
    out["login"] = bool(current.get("login", True))
    out.update(url=current.get("url", ""), ports=current.get("ports") or {},
               elapsed=int(time.time() - float(current.get("started_at") or time.time())))
    phase = current.get("phase", "servers" if current else "")
    if phase == "failed":
        return {**out, "state": "failed", "step": current.get("error", ""), "log": _tail(paths["logs"] / "prepare.log")}
    if phase == "stopping":
        if out["elapsed"] > STALE_START:
            return {**out, "state": "failed", "step": "El arranque se interrumpió (¿se reinició el panel?). Pulsa «Probar» otra vez."}
        return {**out, "state": "preparing", "step": "Deteniendo lo que quedaba de esta versión y abriendo su commit…"}
    if not current or phase == "stopped" or not terminal.exists(name):
        return out
    script = (_tail(paths["logs"] / "phase", 1) or ("prepare" if current.get("run") else "servers")).strip()  # no run: started before phases
    if script.startswith("failed"):
        return {**out, "state": "failed", "step": "Falló la preparación: " + script[7:],
                "log": _tail(paths["logs"] / "prepare.log")}
    if not script.startswith("servers"):
        return {**out, "state": "preparing", "step": _step(script), "log": _tail(paths["logs"] / "prepare.log", 8)}
    up = {n: _answers(f"http://127.0.0.1:{p}{(current.get('ready') or {}).get(n, '/')}") for n, p in current["ports"].items()}
    dead = [n for n, ok in up.items() if not ok and _exited(paths["logs"] / f"{n}.pid")]
    if dead:                             # a server that died is reported with its own output, not waited for forever
        return {**out, "state": "failed", "servers": up, "step": f"{dead[0]} se detuvo al arrancar.",
                "log": _tail(paths["logs"] / f"{dead[0]}.log")}
    ready = bool(up) and all(up.values())
    waiting = ", ".join(n for n, ok in up.items() if not ok)
    return {**out, "state": "ready" if ready else "preparing", "servers": up,
            "step": "Lista." if ready else f"Esperando a que respondan: {waiting}",
            "log": "" if ready else terminal.screen(name, 8)}
