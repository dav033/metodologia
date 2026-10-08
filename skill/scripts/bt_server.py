"""Local web server for the bitácora: dashboard, documents, artifacts, question rounds and plan approval.

Binds to 127.0.0.1 only. Every POST must carry the per-install token (embedded in the served forms) and come
from the same origin, so no other web page can approve a plan and launch an agent.
"""
from __future__ import annotations

import mimetypes
import secrets
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

import bt_pages as pages
import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_page_req import req_page
from bt_vcs import commit

ASSETS = SKILL_DIR / "assets"
DEFAULT_PORT = int(os.environ.get("BITACORA_PORT", "8765"))


def token() -> str:
    f = STATE / "server-token"
    if not f.exists():
        STATE.mkdir(parents=True, exist_ok=True)
        f.write_text(secrets.token_urlsafe(24), encoding="utf-8")
    return f.read_text(encoding="utf-8").strip()


def safe_path(base: Path, rel: str) -> Path | None:
    p = (base / unquote(rel)).resolve()
    try:
        p.relative_to(base.resolve())
    except ValueError:
        return None
    return p if p.is_file() else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    # ------------------------------------------------------------ helpers
    def send(self, body: str | bytes, status: int = 200, ctype: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, url: str) -> None:
        self.send_response(303)
        self.send_header("Location", url)
        self.end_headers()

    def file(self, p: Path | None) -> None:
        if not p:
            return self.send("Not found", 404, "text/plain")
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self.send(p.read_bytes(), 200, ctype)

    # ------------------------------------------------------------ GET
    def do_GET(self):
        try:
            self.route_get()
        except SystemExit as exc:
            self.send(pages.layout("Error", f"<p>{exc}</p>"), 404)
        except Exception as exc:  # never kill the server on one bad page
            self.send(pages.layout("Error", f"<pre>{type(exc).__name__}: {exc}</pre>"), 500)

    def route_get(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
        if not parts:
            return self.send(pages.dashboard())
        if parts[0] == "static" and len(parts) == 2:
            return self.file(safe_path(ASSETS, parts[1]))
        if parts[0] != "p" or len(parts) < 2 or not (ROOT / parts[1]).is_dir():
            return self.send("Not found", 404, "text/plain")
        project, rest = parts[1], parts[2:]
        if not rest:
            return self.send(pages.project_page(project, q.get("tab", "summary")))
        kind, sub = rest[0], "/".join(rest[1:])
        if kind == "doc" and sub.endswith(".md") and safe_path(ROOT / project, sub):
            return self.send(pages.doc_page(project, sub))
        if kind == "artifacts":
            return self.file(safe_path(ROOT / project / "artifacts", sub))
        if kind == "view" and safe_path(ROOT / project / "artifacts", sub):
            return self.send(pages.artifact_view(project, sub))
        if kind == "graph":
            from bt_page_graph import graph_page
            return self.send(graph_page(project))
        if kind == "req" and len(rest) == 2:
            return self.send(req_page(project, rest[1], q.get("tab", ""), token(), q.get("msg", "")))
        self.send("Not found", 404, "text/plain")

    # ------------------------------------------------------------ POST
    def do_POST(self):
        u = urlparse(self.path)
        parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)
        form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode("utf-8")).items()}
        origin = self.headers.get("Origin") or ""
        host = self.headers.get("Host") or ""
        if form.get("token") != token() or (origin and urlparse(origin).netloc != host):
            return self.send("Forbidden", 403, "text/plain")
        if len(parts) != 5 or parts[0] != "p" or parts[2] != "req":
            return self.send("Not found", 404, "text/plain")
        project, req, action = parts[1], parts[3], parts[4]
        try:
            rdir = find_req(ROOT / project, req)
            rid = req_id(rdir)
            base = pages.purl(project, "req", rid)
            if action == "answer":
                msg = self.answer(project, rid, rdir, form)
                return self.redirect(f"{base}?tab=rounds&msg={quote(msg)}")
            if action == "plan":
                msg = self.decide(project, rid, rdir, form)
                return self.redirect(f"{base}?tab=plan&msg={quote(msg)}")
        except SystemExit as exc:
            return self.send(pages.layout("Error", f"<p>{exc}</p>"), 400)
        self.send("Not found", 404, "text/plain")

    def answer(self, project: str, rid: str, rdir: Path, form: dict) -> str:
        f = rounds.rounds_dir(rdir) / form.get("round", "")
        if not f.is_file():
            raise SystemExit("Round not found")
        data = rounds.load(f)
        if data.get("status") != "open":
            return "Esa ronda ya estaba respondida."
        answers = {}
        for qn in data["questions"]:
            if qn["type"] == "choice":
                answers[qn["id"]] = {"choice": form.get(qn["id"], ""), "note": form.get(qn["id"] + "__note", "")}
            else:
                answers[qn["id"]] = {"text": form.get(qn["id"], "")}
        rounds.answer_round(f, answers, "web")
        commit(ROOT, f"{project}: {rid} answers to {f.stem} (web)")
        return "Respuestas guardadas. El agente las toma desde el archivo de la ronda."

    def decide(self, project: str, rid: str, rdir: Path, form: dict) -> str:
        from bt_core import _front
        if _front(rdir / "PLAN.md", "status") != "review":
            return "El plan no está esperando revisión."
        approve = form.get("decision") == "approve"
        if not approve and not form.get("comments", "").strip():
            return "Para pedir cambios escribe qué cambiar."
        rounds.plan_decide(rdir, approve, form.get("comments", ""), "web")
        commit(ROOT, f"{project}: {rid} plan {'approved' if approve else 'changes requested'} (web)")
        if not approve:
            return "Cambios pedidos. El agente del HQ los verá en PLAN.md."
        from bt_launch import launch
        info = launch(project, rid, agent=form.get("agent", "claude"))
        return f"Plan aprobado. Ejecutor lanzado ({info['agent']}) en {info['repo']}."


# ---------------------------------------------------------------- lifecycle

def url(port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}"


def is_running(port: int = DEFAULT_PORT) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def serve(port: int = DEFAULT_PORT) -> None:
    token()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Bitácora at {url(port)}  (Ctrl+C to stop)")
    httpd.serve_forever()


def ensure_server(port: int = DEFAULT_PORT) -> str:
    """Start the server detached in the background if it isn't running. Returns its URL."""
    if not is_running(port):
        exe = Path(sys.executable)
        pyw = exe.with_name("pythonw.exe")
        cmd = [str(pyw if pyw.exists() else exe), str(SCRIPT), "serve", "--port", str(port)]
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(cmd, creationflags=flags, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True, env={**os.environ, "BITACORA_ROOT": str(ROOT)})
    return url(port)
