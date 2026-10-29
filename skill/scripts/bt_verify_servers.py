"""Start the test servers of a subplan version and open it in the browser («Probar esta versión»).

Owner, 2026-10-29 (pictures REQ-021): «quiero que cuando le doy click me arranque el servidor o servidores de pruebas y
que se me abra el navegador con la versión en específico». Opening a version only made a detached copy of its commit
(`bt_verification.open_local`); the owner then had to prepare it, start every server by hand and find the port.

A project describes its servers in `<bitácora>/<project>/verify-servers.json`, kept by the owner, with no secret
values::

    {"env_file": "~/dev/pictures/.env.local",
     "env": {"DATABASE_URL": "${PICTURES_REQ021_DATABASE_URL}", "PYTHON_BACKEND_URL": "http://127.0.0.1:{port:ai-api}"},
     "prepare": [{"unless": "node_modules", "run": "npm ci --prefer-offline --no-audit --no-fund"}],
     "servers": [{"name": "ai-api", "port": 8000, "ready": "/healthz", "run": "uv run … --port {port}"},
                 {"name": "web", "port": 3000, "ready": "/", "open": "/", "run": "npm run dev -- --port {port}"}]}

`${NAME}` is read from the owner's secret files (`verifier.secret_files`) when the servers start and lands only in a
0600 file next to the copy; `{port:<server>}` and `{port}` are the ports actually used: the recipe's when free, else
the next free one, so versions run side by side. The servers run in one tmux session (bt_agent_terminal), outside
every repository; closing the copy stops them. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import bt_agent_terminal as terminal
import bt_verification as verification

RECIPE = "verify-servers.json"
_NAME = re.compile(r"[a-z][a-z0-9-]{0,30}")
_SECRET = re.compile(r"\$\{([A-Z][A-Z0-9_]{0,80})\}")
_PORT = re.compile(r"\{port(?::([a-z][a-z0-9-]{0,30}))?\}")


def recipe(root: Path, project: str) -> dict | None:
    """The project's server recipe, or None when it has none or it is malformed (the page says which)."""
    try:
        data = json.loads((Path(root) / project / RECIPE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    servers = data.get("servers") if isinstance(data, dict) else None
    if not isinstance(servers, list) or not servers or not all(
            isinstance(s, dict) and _NAME.fullmatch(str(s.get("name", ""))) and isinstance(s.get("run"), str)
            and isinstance(s.get("port"), int) for s in servers):
        return None
    return data


def _files(root: Path, project: str, rdir: Path, sid: str, version: object) -> dict[str, Path]:
    copy = verification.workdir(root, project, verification._req(rdir), sid, version)
    base = copy.parent / f"{copy.name}"
    return {"copy": copy, "state": Path(f"{base}.servers.json"), "env": Path(f"{base}.env"),
            "script": Path(f"{base}.run.sh"), "logs": Path(f"{base}.logs")}


def session_name(project: str, rdir: Path, sid: str, version: object) -> str:
    return f"bv-{project}-{verification._req(rdir)}-{sid}-v{version}"[:80]


def _busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _ports(servers: list[dict]) -> dict[str, int]:
    chosen: dict[str, int] = {}
    for server in servers:
        port = int(server["port"])
        while _busy(port) or port in chosen.values():
            port += 1
        chosen[server["name"]] = port
    return chosen


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


def _script(paths: dict[str, Path], data: dict, ports: dict[str, int]) -> str:
    lines = ["set -u", f"cd {shlex.quote(str(paths['copy']))}", "set -a", f". {shlex.quote(str(paths['env']))}", "set +a",
             f"mkdir -p {shlex.quote(str(paths['logs']))}", 'echo "[bitácora] preparando la versión…"']
    for step in data.get("prepare") or []:
        if isinstance(step, dict) and isinstance(step.get("run"), str):
            guard = f"[ -e {shlex.quote(str(step['unless']))} ] || " if step.get("unless") else ""
            lines.append(f"{guard}{step['run']} || {{ echo '[bitácora] falló: {step['run'][:60]}'; exit 1; }}")
    for server in data["servers"]:
        log = shlex.quote(str(paths["logs"] / f"{server['name']}.log"))
        lines.append(f"echo \"[bitácora] {server['name']} en el puerto {ports[server['name']]}\"")
        lines.append(f"( {_fill(server['run'], ports, ports[server['name']], {})} ) > {log} 2>&1 &")
        lines.append(f"echo $! > {shlex.quote(str(paths['logs'] / (server['name'] + '.pid')))}")
    lines += ['echo "[bitácora] servidores en marcha; registros en ' + str(paths["logs"]) + '"', "wait"]
    return "\n".join(lines) + "\n"


def _url(data: dict, ports: dict[str, int]) -> str:
    server = next((s for s in data["servers"] if s.get("open")), data["servers"][-1])
    return f"http://localhost:{ports[server['name']]}{server.get('open') if isinstance(server.get('open'), str) else '/'}"


def start(root: Path, project: str, rdir: Path, sid: str) -> dict:
    """Open the copy if needed and start its servers (once: a running set is reused). {ok, message, url}."""
    data = recipe(root, project)
    if data is None:
        return {"ok": False, "message": f"El proyecto no tiene receta de servidores de prueba ({project}/{RECIPE}).", "url": ""}
    target, message = verification.open_local(root, project, rdir, sid)
    if target is None:
        return {"ok": False, "message": message, "url": ""}
    row = next(r for r in verification.state(rdir)["subplans"] if r["id"] == sid)
    paths, name = _files(root, project, rdir, sid, row["version"]), session_name(project, rdir, sid, row["version"])
    if terminal.exists(name):
        current = _load(paths["state"])
        return {"ok": True, "message": f"Los servidores de {sid} ya estaban en marcha.", "url": current.get("url", "")}
    _stop_strays(paths["copy"])         # a server left running in this copy holds its port and Next's one-dev-server lock
    ports = _ports(data["servers"])
    env, missing = environment(project, data, ports)
    if missing:
        return {"ok": False, "url": "", "message": f"Falta {', '.join(missing)} en tus archivos de secretos "
                "(verifier.secret_files): no arranco los servidores sin ella."}
    paths["env"].touch(mode=0o600, exist_ok=True)
    os.chmod(paths["env"], 0o600)
    paths["env"].write_text("".join(f"{k}={shlex.quote(v)}\n" for k, v in env.items()), encoding="utf-8")
    paths["script"].write_text(_script(paths, data, ports), encoding="utf-8")
    url = _url(data, ports)
    try:
        terminal.start(name, paths["copy"], f"bash {shlex.quote(str(paths['script']))}")
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "message": f"No pude arrancar los servidores: {exc}", "url": ""}
    ready = {s["name"]: s.get("ready", "/") for s in data["servers"]}
    paths["state"].write_text(json.dumps({"session": name, "ports": ports, "ready": ready, "url": url,
                                          "started_at": time.time()}, indent=1), encoding="utf-8")
    return {"ok": True, "message": f"Arrancando {', '.join(ports)} de {sid} (versión {row['version']}).", "url": url}


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as reply:          # noqa: S310 - loopback only, built here
            return reply.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except (OSError, ValueError):
        return False


def status(root: Path, project: str, rdir: Path, sid: str) -> dict:
    """{state: stopped|preparing|ready, url, servers: {name: bool}, log}: what the waiting page polls."""
    row = next((r for r in verification.state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row.get("version"):
        return {"state": "stopped", "url": "", "servers": {}, "log": ""}
    paths = _files(root, project, rdir, sid, row["version"])
    current, name = _load(paths["state"]), session_name(project, rdir, sid, row["version"])
    if not current or not terminal.exists(name):
        return {"state": "stopped", "url": current.get("url", ""), "servers": {}, "log": ""}
    up = {n: _answers(f"http://127.0.0.1:{p}{(current.get('ready') or {}).get(n, '/')}") for n, p in current["ports"].items()}
    dead = [n for n, ok in up.items() if not ok and _exited(paths["logs"] / f"{n}.pid")]
    if dead:                             # a server that died is reported with its own output, not waited for forever
        return {"state": "failed", "url": current.get("url", ""), "servers": up,
                "log": f"{dead[0]} se detuvo:\n" + _tail(paths["logs"] / f"{dead[0]}.log")}
    return {"state": "ready" if up and all(up.values()) else "preparing", "url": current.get("url", ""), "servers": up,
            "log": terminal.screen(name, 8)}


def _exited(pidfile: Path) -> bool:
    try:
        pid = int(pidfile.read_text().strip())
    except (OSError, ValueError):
        return False                     # not started yet: it is still preparing
    return not Path(f"/proc/{pid}").exists()


def _tail(path: Path, lines: int = 15) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def _listening_inodes() -> set[str]:
    inodes = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            cols = row.split()
            if len(cols) > 9 and cols[3] == "0A":          # LISTEN
                inodes.add(cols[9])
    return inodes


def _stop_strays(copy: Path) -> list[int]:
    """Stop the servers working inside the copy that no session of ours owns (one started by hand or left by a session
    that ended): they hold the version's port and Next's one-dev-server lock on its folder (pictures SP-1, 2026-10-29).
    Only processes that listen on a TCP port: an editor or a shell open in the copy is never touched. Returns pids."""
    found = []
    root = str(copy.resolve()) if copy.exists() else str(copy)
    listening = _listening_inodes()
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            cwd = os.readlink(proc / "cwd")
            sockets = {os.readlink(fd)[8:-1] for fd in (proc / "fd").iterdir() if os.readlink(fd).startswith("socket:[")}
        except OSError:
            continue
        if (cwd == root or cwd.startswith(root + "/")) and sockets & listening and int(proc.name) != os.getpid():
            try:
                os.kill(int(proc.name), signal.SIGTERM)
                found.append(int(proc.name))
            except OSError:
                pass
    return found


def stop(root: Path, project: str, rdir: Path, sid: str) -> str:
    """Stop the version's servers: the whole process group of its tmux pane, then the session."""
    row = next((r for r in verification.state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row.get("version"):
        return "No había servidores en marcha."
    name = session_name(project, rdir, sid, row["version"])
    strays = _stop_strays(_files(root, project, rdir, sid, row["version"])["copy"])
    if not terminal.exists(name):
        return f"Servidores de {sid} detenidos." if strays else "No había servidores en marcha."
    pane = terminal._run("list-panes", "-t", f"={name}:", "-F", "#{pane_pid}").stdout.split()
    for pid in pane[:1]:
        try:
            os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
        except (OSError, ValueError):
            pass
    terminal.kill(name)
    return f"Servidores de {sid} detenidos."
