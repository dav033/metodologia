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

`auto_login` (D-205, D-231) opens every link signed in as a real test account: `mint` prints a session token for
`BT_LOGIN_ACCOUNT` and exits MISSING_ACCOUNT (3) when the account does not exist; an optional idempotent `seed` then
creates `BT_TEST_ACCOUNTS` with `BT_TEST_PASSWORD` (the owner's secret named by `password_secret`) and `mint` runs once
more. The full contract, with an example for any app: references/requirements.md «Test servers recipe».

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


# ------------------------------------------------------------------ automatic sign-in (D-205, D-231)

MISSING_ACCOUNT = 3                       # `mint` exit code: the account does not exist yet (the panel runs `seed`)
_COOKIE = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]{0,80}")
_EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_LOCAL_ROLE = re.compile(r"[^+@]+\+([^@]+)@")          # test+<role>@… names its role


def login_accounts(login: dict | None) -> list[dict]:
    """The recipe's test accounts as [{email, role, label, aliases}]: an entry is an e-mail («test+<role>@…» names its
    role) or {email, role?, label?, aliases?}. Malformed entries are left out (auto_login_problem says why)."""
    out = []
    for item in (login or {}).get("accounts") or []:
        if isinstance(item, str):
            item = {"email": item}
        if not isinstance(item, dict) or not isinstance(item.get("email"), str) or not _EMAIL.fullmatch(item["email"]):
            continue
        found = _LOCAL_ROLE.match(item["email"])
        role = item.get("role") if isinstance(item.get("role"), str) else (found.group(1) if found else "")
        aliases = [str(a) for a in item.get("aliases") or [] if isinstance(a, str)] if isinstance(item.get("aliases"), list) else []
        out.append({"email": item["email"], "role": role, "label": str(item.get("label") or ""), "aliases": aliases})
    return out


def auto_login_problem(data: dict | None) -> str:
    """Why the recipe's `auto_login` cannot be used, in Spanish, or "" (also when there is none)."""
    if not isinstance(data, dict) or "auto_login" not in data:
        return ""
    value = data["auto_login"]
    if not isinstance(value, dict):
        return "«auto_login» debe ser un objeto con cookie, accounts y mint."
    if not _COOKIE.fullmatch(str(value.get("cookie") or "")):
        return "«auto_login.cookie» debe ser el nombre de la cookie de sesión de la app (letras, números y «_.-»)."
    if not isinstance(value.get("mint"), str) or not value["mint"].strip():
        return "«auto_login.mint» debe ser el comando que imprime el token de sesión de BT_LOGIN_ACCOUNT."
    if "seed" in value and (not isinstance(value["seed"], str) or not value["seed"].strip()):
        return "«auto_login.seed» debe ser el comando que crea las cuentas de BT_TEST_ACCOUNTS (o no estar)."
    if "password_secret" in value and not _ENV_NAME.fullmatch(str(value["password_secret"])):
        return "«auto_login.password_secret» debe ser el NOMBRE de una variable de tus archivos de secretos, no su valor."
    raw = value.get("accounts")
    if not isinstance(raw, list) or not raw:
        return "«auto_login.accounts» debe ser una lista de cuentas de prueba."
    for number, item in enumerate(raw, 1):
        entry = {"email": item} if isinstance(item, str) else item
        ok = isinstance(entry, dict) and isinstance(entry.get("email"), str) and _EMAIL.fullmatch(entry["email"]) and \
            all(isinstance(entry.get(k, ""), str) for k in ("role", "label")) and \
            (isinstance(entry.get("aliases", []), list) and all(isinstance(a, str) for a in entry.get("aliases", [])))
        if not ok:
            return (f"La cuenta n.º {number} de «auto_login.accounts» no es válida: debe ser un correo o "
                    "{email, role, label, aliases}.")
    emails = [a["email"] for a in login_accounts(value)]
    if value.get("default") and value["default"] not in emails:
        return "«auto_login.default» debe ser una de las cuentas de «auto_login.accounts»."
    return ""


def auto_login(data: dict | None) -> dict:
    """The recipe's `auto_login` ({cookie, accounts, default, mint, seed?, password_secret?}) or {} when there is none or
    it is malformed (D-205, D-231)."""
    value = (data or {}).get("auto_login")
    return value if isinstance(value, dict) and not auto_login_problem(data) else {}


TOKEN = re.compile(r"[A-Za-z0-9_\-]{20,200}")


def _version_env(paths: dict[str, Path]) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in paths["env"].read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            env[key] = shlex.split(value)[0] if value.strip() else ""
    return env


def _masked(text: str, hidden: list[str]) -> str:
    """The last line of a command's output, with every secret value of the version replaced by ***."""
    line = ((text or "").strip().splitlines()[-1:] or ["sin salida"])[0]
    for value in sorted({h for h in hidden if len(h) >= 8}, key=len, reverse=True):
        line = line.replace(value, "***")
    return line[:200]


def _record(paths: dict[str, Path], **entries: dict) -> None:
    """The outcome of a sign-in (and of a seed) in the version's state and its login.log; never a secret or a token."""
    stamp = time.time()
    lock = paths.get("lock")
    with (_locked(lock) if lock else contextlib.nullcontext()):
        state = _load(paths["state"])
        state.update({k: {**v, "at": stamp} for k, v in entries.items()})
        _save(paths["state"], state)
    if paths.get("logs"):
        paths["logs"].mkdir(parents=True, exist_ok=True)
        with open(paths["logs"] / "login.log", "a", encoding="utf-8") as log:
            when = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stamp))
            log.writelines(f"{when} {kind} {'ok' if entry.get('ok') else 'failed'} {entry.get('account') or ''} "
                           f"{entry.get('message') or ''}\n" for kind, entry in entries.items())


def mint_session(root: Path, project: str, rdir: Path, sid: str, account: str = "") -> dict:
    """A real session of a test account for the running version: the recipe's `mint` command runs in the version's copy
    with its environment and `BT_LOGIN_ACCOUNT`, and prints the session token. {ok, token, cookie, account, url, message}.
    Owner, 2026-10-30: «que se inicie sesión automáticamente» — a real account (menus and roles as in production), not
    the local administrator shortcut; the panel hands the cookie to the browser (localhost cookies hold for every port).

    When `mint` exits MISSING_ACCOUNT and the recipe has `seed`, the seed runs once in the same copy with the same
    environment, `BT_TEST_ACCOUNTS` (JSON [{email, role}]) and `BT_TEST_PASSWORD` (from the owner's secret named by
    `password_secret`), and `mint` is tried once more («que funcione en cualquier entorno», D-231)."""
    data, row = recipe(root, project, rdir), _row(rdir, sid, root, project)
    problem = auto_login_problem(data)
    if problem:
        return {"ok": False, "message": f"Inicio de sesión automático desactivado: {problem}"}
    login = auto_login(data)
    if not login or row is None:
        return {"ok": False, "configured": False, "message": "Esta versión no tiene inicio de sesión automático."}
    accounts = login_accounts(login)
    emails = [a["email"] for a in accounts]
    account = account if account in emails else str(login.get("default") or (emails[0] if emails else ""))
    paths = _files(root, project, rdir, sid, row["version"])
    if not _load(paths["state"]).get("url"):
        return {"ok": False, "message": "La versión no está en marcha."}
    try:
        version_env = _version_env(paths)
    except (OSError, ValueError) as exc:
        return {"ok": False, "message": f"No pude leer el entorno de la versión: {exc.__class__.__name__}."}
    hidden = [v for v in version_env.values() if v]
    env = {**os.environ, **version_env, "BT_LOGIN_ACCOUNT": account}

    def run(command: str, extra: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", "-c", command], cwd=paths["copy"], env={**env, **(extra or {})},
                              capture_output=True, text=True, timeout=timeout)

    def fail(message: str, seed: str = "") -> dict:
        _record(paths, auto_login={"ok": False, "account": account, "message": message},
                **({"seed": {"ok": False, "account": account, "message": seed}} if seed else {}))
        return {"ok": False, "message": message}

    try:
        done = run(login["mint"])
        if done.returncode == MISSING_ACCOUNT:
            if not login.get("seed"):
                return fail(f"No pude iniciar sesión como {account}: {_masked(done.stderr or done.stdout, hidden)}. "
                            "La receta no tiene «seed» para crear las cuentas de prueba; créalas a mano o añádelo.")
            extra = {"BT_TEST_ACCOUNTS": json.dumps([{"email": a["email"], "role": a["role"]} for a in accounts])}
            name = str(login.get("password_secret") or "")
            if name:
                password = _secrets(project).get(name, "")
                if not password:
                    return fail(f"Falta {name} en tus archivos de secretos (verifier.secret_files): no creo las cuentas "
                                "de prueba sin su contraseña.", seed=f"falta {name}")
                extra["BT_TEST_PASSWORD"] = password
                hidden.append(password)
            seeded = run(login["seed"], extra, timeout=180)
            if seeded.returncode:
                why = _masked(seeded.stderr or seeded.stdout, hidden)
                return fail(f"No pude crear las cuentas de prueba (seed, salida {seeded.returncode}): {why}",
                            seed=why)
            _record(paths, seed={"ok": True, "account": account, "message": f"{len(accounts)} cuentas aseguradas"})
            done = run(login["mint"])
    except subprocess.TimeoutExpired as exc:
        return fail(f"No pude iniciar sesión como {account}: la receta tardó más de {exc.timeout:.0f} s.")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return fail(f"No pude iniciar sesión como {account}: {exc.__class__.__name__}.")
    token = (done.stdout or "").strip()
    if done.returncode or not TOKEN.fullmatch(token):
        return fail(f"No pude iniciar sesión como {account}: {_masked(done.stderr or done.stdout, hidden)}")
    _record(paths, auto_login={"ok": True, "account": account, "message": ""})
    return {"ok": True, "token": token, "cookie": login["cookie"], "account": account, "url": _load(paths["state"]).get("url", ""),
            "message": ""}


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
    _save(paths["state"], {**_load(paths["state"]), "phase": "stopping", "run": run, "started_at": time.time(), "error": "",
                           "auto_login": {}})
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
    tried = current.get("auto_login") if isinstance(current.get("auto_login"), dict) else {}
    out["login_error"] = "" if tried.get("ok", True) else str(tried.get("message") or "")
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
