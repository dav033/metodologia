"""Local web server for the bitácora: dashboard, documents, artifacts, question rounds and plan approval.

Binds to 127.0.0.1 only. Every POST must carry the per-install token (embedded in the served forms) and come
from the same origin, so no other web page can approve a plan and launch an agent.
"""
from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets
import signal
import shutil
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

import bt_pages as pages
import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_page_req import req_page
from bt_platform import detached_options, platform, systemd_listener
from bt_vcs import commit

ASSETS = SKILL_DIR / "assets"
DEFAULT_PORT = int(os.environ.get("BITACORA_PORT", "8765"))
REMOTE_PORT = int(os.environ.get("BITACORA_REMOTE_PORT", "8766"))
SIMULATE_MAX_BYTES = 256 * 1024     # a demonstration, not a way to make the server grind on any plan
SIMULATE_MAX_TASKS = 60

MAX_FORM_BYTES = 64 * 1024

def _local_host(host: str) -> bool:
    """The server answers only to its own loopback names: a page served under an attacker's DNS name (rebinding) can neither
    read the token nor post with it."""
    name = host.rsplit(":", 1)[0].strip("[]").lower() if not host.startswith("[") else host.split("]")[0].strip("[").lower()
    return name in {"127.0.0.1", "localhost", "::1"}

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
    strict_host = True          # the local panel answers only to its own loopback names (the remote handler has its own login)

    def log_message(self, *args):  # quiet
        pass

    # ------------------------------------------------------------ helpers
    def send(self, body: str | bytes, status: int = 200, ctype: str = "text/html; charset=utf-8",
             sandbox: bool = False) -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        if sandbox:  # generated or agent-written HTML must not reach the dashboard origin or its token
            self.send_header("Content-Security-Policy", "sandbox allow-scripts; default-src 'none'; "
                             "script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:")
        else:
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; "
                             "style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; "
                             "base-uri 'self'; frame-ancestors 'self'")
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
        self.send(p.read_bytes(), 200, ctype, sandbox=p.suffix == ".html")

    # ------------------------------------------------------------ GET
    def do_GET(self):
        if self.strict_host and not _local_host(self.headers.get("Host") or ""):
            return self.send("Forbidden", 403, "text/plain")
        try:
            self.route_get()
        except SystemExit as exc:
            self.send(pages.layout("Error", f"<p>{pages.e(str(exc))}</p>"), 404)
        except Exception as exc:  # never kill the server on one bad page
            self.send(pages.layout("Error", f"<pre>{pages.e(type(exc).__name__ + ': ' + str(exc))}</pre>"), 500)

    def route_get(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
        if not parts:
            return self.send(pages.dashboard())
        if parts[:2] == ["metrics", "model"] and len(parts) in (4, 5):
            import bt_page_model
            return self.send(bt_page_model.model_page(parts[2], parts[3], parts[4] if len(parts) == 5 else None,
                                                      bt_page_model.all_rows()))
        if parts == ["metrics"]:
            from bt_page_metrics import metrics_page
            return self.send(metrics_page())
        if parts == ["live"]:
            import bt_live_api as live
            return live.stream(self, ROOT, q.get("scope", "global"),
                               self.headers.get("Last-Event-ID") or q.get("last", ""))
        if parts and parts[0] == "go":
            return self.go(parts[1:])
        if parts == ["learnings"]:
            return self.send(pages.layout("Aprendizajes", pages.md("doc", pages.read(ROOT / "LEARNINGS.md")),
                                          [("Aprendizajes", "/learnings")]))
        if parts == ["flow"]:
            import bt_page_flow
            scope = q.get("scope", "global")
            sim = "/".join(scope.split(":", 1)[1].split("/")[:2]) if scope.startswith(("run:", "task:")) else \
                "metodologia/REQ-026"
            return self.send(bt_page_flow.flow_page(scope, sim, token()))
        if parts == ["flow", "review"]:
            import bt_page_flow_review
            return self.send(bt_page_flow_review.review_page(ROOT, q))
        if parts == ["now"]:
            import bt_live_api as live
            import bt_page_now
            return self.send(bt_page_now.now_page(live.now_items(ROOT), live.sessions(ROOT)))
        if parts == ["api", "now"]:
            import bt_live_api as live
            return self.send(json.dumps({"items": live.now_items(ROOT), "sessions": live.sessions(ROOT)}), 200, "application/json; charset=utf-8")
        if parts == ["api", "simulate"]:
            return self.simulate(q)
        if parts == ["api", "flow"]:
            import bt_live_api as live
            scope = q.get("scope", "global")
            events, digests, _ = live.flow_events(ROOT, scope, q.get("after", ""),
                                                  limit=min(int(q.get("limit", "2000") or 2000), 5000))
            return self.send(json.dumps({"events": events, "digests": digests, "runs": live.run_summaries(ROOT, scope)}),
                             200, "application/json; charset=utf-8")
        if parts == ["api", "flow", "agent"]:
            import bt_live_api as live
            return self.send(json.dumps({"attempts": live.agent_activity(ROOT, q.get("run", ""))}, ensure_ascii=False), 200,
                             "application/json; charset=utf-8")
        if parts == ["api", "flow", "runs"]:
            import bt_live_api as live
            return self.send(json.dumps({"runs": live.run_summaries(ROOT, q.get("scope", "global"))}), 200,
                             "application/json; charset=utf-8")
        if parts and parts[0] in ("plans", "events", "api"):
            return self.plans_get(parts, q)
        if parts[0] == "static" and len(parts) >= 2:            # nested for vendored libraries (static/vendor/<lib>/…)
            return self.file(safe_path(ASSETS, "/".join(parts[1:])))
        if parts[0] != "p" or len(parts) < 2 or not (ROOT / parts[1]).is_dir():
            return self.send("Not found", 404, "text/plain")
        project, rest = parts[1], parts[2:]
        if not rest:
            return self.send(pages.project_page(project, q.get("tab", "overview")))
        kind, sub = rest[0], "/".join(rest[1:])
        if kind == "doc" and sub.endswith(".md") and safe_path(ROOT / project, sub):
            return self.send(pages.doc_page(project, sub))
        if kind == "artifacts":                                   # the bare folder is the project's artifacts tab
            return self.file(safe_path(ROOT / project / "artifacts", sub)) if sub else self.redirect(f"/p/{quote(project)}?tab=artifacts")
        if kind == "view" and safe_path(ROOT / project / "artifacts", sub):
            return self.send(pages.artifact_view(project, sub))
        if kind == "graph":
            from bt_page_graph import graph_page
            return self.send(graph_page(project))
        if kind == "req" and len(rest) == 2:
            return self.send(req_page(project, rest[1], q.get("tab", ""), token(), q.get("msg", ""), q.get("lang", "")))
        if kind == "req" and len(rest) == 3 and rest[2] in ("planning", "mockup"):
            return self.planning_get(project, rest[1], rest[2], q)
        if kind == "req" and len(rest) == 3 and rest[2] == "preview":
            import bt_design_web
            rdir = find_req(ROOT / project, rest[1])
            preview = bt_design_web.preview_file(ROOT, project, rdir, q.get("contract", ""))
            if preview is None:
                return self.send("Preview not found", 404, "text/plain")
            return self.file(preview)
        self.send("Not found", 404, "text/plain")

    # ------------------------------------------------------------ POST
    def do_POST(self):
        u = urlparse(self.path)
        parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        host = self.headers.get("Host") or ""
        if not 0 <= length <= MAX_FORM_BYTES or (self.strict_host and not _local_host(host)):            # before reading anything the caller sent
            return self.send("Forbidden", 403, "text/plain")
        form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode("utf-8", "replace")).items()}
        origin = self.headers.get("Origin") or ""
        if not hmac.compare_digest(form.get("token", ""), token()) or (origin and urlparse(origin).netloc != host):
            return self.send("Forbidden", 403, "text/plain")
        if parts == ["api", "flow", "decision"]:
            import bt_plans_api as api
            try:
                message = api.decide(ROOT, form.get("project", ""), form.get("req", ""),
                                     form.get("request", ""), form.get("option", ""), form.get("reason", ""),
                                     by="flow")
            except api.PlanError as exc:
                return self.send(json.dumps({"error": str(exc)}), 409, "application/json; charset=utf-8")
            return self.send(json.dumps({"message": message}), 200, "application/json; charset=utf-8")
        if parts == ["api", "flow", "diagnose"]:
            import bt_plans_api as api
            try:
                message = api.diagnose(ROOT, form.get("project", ""), form.get("req", ""), form.get("request", ""))
            except api.PlanError as exc:
                return self.send(json.dumps({"error": str(exc)}), 409, "application/json; charset=utf-8")
            return self.send(json.dumps({"message": message}), 202, "application/json; charset=utf-8")
        if parts and parts[0] == "plans":
            return self.plans_post(parts, form)
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
            if action == "review":
                msg = self.review(project, rid, rdir, form)
                return self.redirect(f"{base}?tab=review&msg={quote(msg)}")
            if action == "run":
                msg = self.run_control(project, rid, rdir, form)
                return self.redirect(f"{base}?tab=run&msg={quote(msg)}")
            if action == "plan":
                msg = self.decide(project, rid, rdir, form)
                return self.redirect(f"{base}?tab=plan&msg={quote(msg)}")
            if action in ("design-draft", "design-feedback"):
                return self.redirect(self.planning_post(project, rdir, action, form, base))
            if action == "design":
                import bt_design_web
                msg = bt_design_web.decide(ROOT, project, rid, rdir, form,
                                           lambda path, text: commit(path, text, push=False))
                return self.redirect(f"{base}?tab=plan&msg={quote(msg)}")
        except (SystemExit, ValueError) as exc:
            return self.send(pages.layout("Error", f"<p>{pages.e(str(exc))}</p>"), 400)
        self.send("Not found", 404, "text/plain")

    def planning_get(self, project: str, req: str, what: str, q: dict) -> None:
        """Live fragment of the plan tab (and a nudge for the Designer and translator), or a sandboxed mockup."""
        import bt_design_drafts as drafts
        import bt_page_planning as planning
        rdir = find_req(ROOT / project, req)
        if what == "mockup":
            ref = q.get("contract", "")
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5}", ref):
                return self.send("Not found", 404, "text/plain")
            return self.file(drafts.paths(rdir, ref)[1] if drafts.paths(rdir, ref)[1].is_file() else None)
        planning.follow(project, rdir)
        html = planning.fragment(project, req_id(rdir), rdir, planning.plan_status(rdir), token(),
                                 q.get("lang") or planning.default_lang(rdir))
        return self.send(json.dumps({"html": html}, ensure_ascii=False), 200, "application/json; charset=utf-8")

    def planning_post(self, project: str, rdir: Path, action: str, form: dict, base: str) -> str:
        import bt_design_drafts as drafts
        ref, comments = form.get("contract", ""), form.get("comments", "").strip()
        if action == "design-feedback" or comments:
            msg = drafts.add_feedback(project, rdir, ref, comments, "web")
        else:
            started = drafts.request(project, rdir, [ref] if ref else None, force=bool(ref), reason="web")
            msg = f"Designer iniciado para {', '.join(started)}." if started else "No había diseños que iniciar."
        commit(ROOT, f"{project}: {req_id(rdir)} design drafts ({action}, web)", push=False)
        anchor = f"#{form.get('anchor')}" if re.fullmatch(r"SP-[\w-]+", form.get("anchor", "")) else ""
        return f"{base}?tab=plan&lang={quote(form.get('lang', ''))}&msg={quote(msg)}{anchor}"

    def simulate(self, q: dict) -> None:
        """A demonstration run of one plan on the core's doubles (read-only: nothing is created or executed)."""
        import bt_flow_bus
        import bt_plans_api as api
        import bt_scheduler_adapter as scheduler_adapter
        try:
            rdir = api.req_dir(ROOT, q.get("project", ""), q.get("req", ""))
            plan = rdir / "PLAN.json"
            if not plan.exists():
                raise api.PlanError("Ese requerimiento no tiene PLAN.json.")
            if plan.stat().st_size > SIMULATE_MAX_BYTES:
                raise api.PlanError("El PLAN.json es demasiado grande para simularlo.")
            tasks = [t["id"] for t in json.loads(plan.read_text(encoding="utf-8")).get("tasks", [])]
            if len(tasks) > SIMULATE_MAX_TASKS:
                raise api.PlanError("El plan tiene demasiadas tareas para simularlo.")
        except (api.PlanError, ValueError) as exc:
            return self.send(str(exc), 404, "text/plain; charset=utf-8")
        script = {"fail": {tasks[1]: 1} if len(tasks) > 1 else {}, "reject": {tasks[2]: 1} if len(tasks) > 2 else {}}
        audit = scheduler_adapter.simulate_audit(plan, **script)
        events = bt_flow_bus.simulated(f"simulación/{q.get('project', '')}/{rdir.name}", audit)
        return self.send(json.dumps({"events": events, "script": script}), 200, "application/json; charset=utf-8")

    def go(self, parts: list[str]) -> None:
        import bt_go
        found = bt_go.resolve(ROOT, parts)
        if "url" in found:
            return self.redirect(found["url"])
        if "choices" in found:
            links = "".join(f'<li><a href="{quote(url, safe="/#?=&:")}">{pages.e(project)}</a></li>'
                            for project, url in found["choices"])
            return self.send(pages.layout(found["id"], f'<h1>{pages.e(found["id"])}</h1><p>Existe en varios proyectos:</p>'
                                                         f'<ul>{links}</ul>'))
        self.send(pages.layout("No encontrado", f'<h1>No encontrado</h1><p>{pages.e(found["error"])}</p>'), 404)

    def plans_get(self, parts: list[str], q: dict) -> None:
        import bt_page_plans as pp
        import bt_plans_api as api
        try:
            if parts == ["plans"]:
                filt = "active" if q.get("filter") == "active" else "all"
                return self.send(pp.index_page(api.plans_payload(ROOT), filt, api.all_trash(ROOT), token(),
                                               q.get("msg", "")))
            if len(parts) == 3 and parts[0] == "plans":
                return self.send(pp.detail_page(api.status_of(ROOT, parts[1], parts[2]), token(), q.get("msg", "")))
            if parts == ["events"]:
                plan = tuple(q["plan"].split("/", 1)) if "/" in q.get("plan", "") else None
                return api.stream(self, ROOT, plan, "active" if q.get("filter") == "active" else "all")
            if parts == ["api", "plans"]:
                filt = "active" if q.get("filter") == "active" else "all"
                rows = api.plans_payload(ROOT, filt)
                data = {"plans": rows, **({"html": pp.index_fragment(rows, filt)} if q.get("html") else {})}
                return self.send(json.dumps(data), 200, "application/json; charset=utf-8")
            if len(parts) == 4 and parts[:2] == ["api", "plans"]:
                status = api.status_of(ROOT, parts[2], parts[3])
                data = {**status, **({"html": pp.detail_fragment(status)} if q.get("html") else {})}
                return self.send(json.dumps(data), 200, "application/json; charset=utf-8")
        except api.PlanError as exc:
            return self.send(str(exc), 404, "text/plain; charset=utf-8")
        self.send("Not found", 404, "text/plain")

    def plans_post(self, parts: list[str], form: dict) -> None:
        import bt_plans_api as api
        actions = {"run": lambda p, r: self.run_plan(api, p, r, form.get("expected", "")),
                   "decide": lambda p, r: api.decide(ROOT, p, r, form.get("request", ""), form.get("option", ""),
                                                     form.get("reason", "")),
                   "diagnose": lambda p, r: api.diagnose(ROOT, p, r, form.get("request", "")),
                   "recovery": lambda p, r: api.recovery_control(ROOT, p, r, form.get("action", ""), form.get("preview", ""),
                                                                 form.get("stop_generation", "")),
                   "heal": lambda p, r: api.heal_control(ROOT, p, r, form.get("action", ""), form.get("case", "")),
                   "cancel": lambda p, r: api.cancel_plan(ROOT, p, r, form.get("confirm", "")),
                   "delete": lambda p, r: api.delete_plan(ROOT, p, r, form.get("confirm", ""))}
        try:
            if len(parts) == 3 and parts[2] == "restore":
                msg = api.restore_plan(ROOT, parts[1], form.get("entry", ""))
                return self.redirect(f"/plans?msg={quote(msg)}")
            if len(parts) == 4 and parts[3] in actions:
                msg = actions[parts[3]](parts[1], parts[2])
                dest = "/plans" if parts[3] == "delete" else f"/plans/{quote(parts[1])}/{quote(parts[2])}"
                return self.redirect(f"{dest}?msg={quote(msg)}")
        except api.PlanError as exc:
            back = f"/plans/{quote(parts[1])}/{quote(parts[2])}" if len(parts) == 4 else "/plans"
            return self.redirect(f"{back}?msg={quote(str(exc))}")
        self.send("Not found", 404, "text/plain")

    def run_plan(self, api, project: str, rid: str, expected: str) -> str:
        msg = api.run_plan(ROOT, project, rid, expected)
        commit(ROOT, f"{project}: {rid} run from the plan page (web)")
        return msg

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
        info = launch(project, rid)
        return f"Plan aprobado. Ejecución Scheduler lanzada en {info['workdir']}."

    def run_control(self, project: str, rid: str, rdir: Path, form: dict) -> str:
        from bt_page_run import apply_control
        return apply_control(rdir, form.get("action", ""))

    def review(self, project: str, rid: str, rdir: Path, form: dict) -> str:
        import bt_review as rv
        decision, comments = form.get("decision", ""), form.get("comments", "").strip()
        plan = rdir / "PLAN.md"
        stamp = f"{dt.datetime.now():%Y-%m-%d %H:%M}"
        if decision == "changes":
            if not comments:
                return "Para pedir cambios escribe qué cambiar."
            with plan.open("a", encoding="utf-8") as fh:
                fh.write(f"- {stamp} REVIEW: changes requested (web): {comments}\n")
            commit(ROOT, f"{project}: {rid} review — changes requested (web)")
            return "Cambios anotados en el plan. Revisa y aprueba una nueva revisión antes de iniciar otra ejecución."
        lines = rv.merge(project, rdir, push=decision == "merge_push")
        merged = any("fusionada" in l for l in lines)
        with plan.open("a", encoding="utf-8") as fh:
            fh.write(f"- {stamp} REVIEW ({decision}, web): " + " | ".join(lines)
                     + (f" — {comments}" if comments else "") + "\n")
        if merged:
            set_front(plan, "status", "merged")
            set_front(rdir / "SPEC.md", "status", "done")
        commit(ROOT, f"{project}: {rid} review — {decision} (web)")
        return " · ".join(lines)

# ---------------------------------------------------------------- lifecycle

class RemoteHandler(Handler):
    strict_host = False
    """Expose only the versioned machine API on the separately forwarded listener."""

    def _remote_path_allowed(self) -> bool:
        path = urlparse(self.path).path
        return path == "/api/remote/v1" or path.startswith("/api/remote/v1/")

    def do_GET(self):
        if not self._remote_path_allowed():
            return self.send("Not found", 404, "text/plain")
        return self.remote_api_get()

    def do_POST(self):
        if not self._remote_path_allowed():
            return self.send("Not found", 404, "text/plain")
        return self.remote_api_post()

    def remote_api_get(self):
        """Dispatch to the versioned API; never fall through to panel routes."""
        import bt_remote_api
        return bt_remote_api.route_get(self)

    def remote_api_post(self):
        """Dispatch to the versioned API; never fall through to panel controls."""
        import bt_remote_api
        return bt_remote_api.route_post(self)

def url(port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}"

def is_running(port: int = DEFAULT_PORT) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0

def code_version() -> str:
    """Changes whenever the server's code or assets change (newest mtime), so a stale server can be replaced."""
    files = list(Path(__file__).parent.glob("*.py")) + list(ASSETS.glob("*"))
    return str(int(max(f.stat().st_mtime for f in files)))

def serve(port: int = DEFAULT_PORT) -> None:
    token()
    (STATE / "server.json").write_text(json.dumps({"pid": os.getpid(), "port": port, "version": code_version(),
                                                   "root": str(ROOT)}), encoding="utf-8")
    httpd = create_http_server(port)
    import bt_live_api
    bt_live_api.warm(ROOT)
    print(f"Bitácora at {url(port)}  (Ctrl+C to stop)")
    httpd.serve_forever()

def create_http_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build the panel server around systemd's listener when socket activation is configured."""
    listener = systemd_listener(port)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler, bind_and_activate=listener is None)
    if listener is not None:
        httpd.socket.close()
        httpd.socket = listener
        httpd.server_address = listener.getsockname()
    return httpd

def serve_remote(port: int = REMOTE_PORT) -> None:
    """Serve the gateway-only API on loopback, without exposing the browser panel routes."""
    httpd = ThreadingHTTPServer(("127.0.0.1", port), RemoteHandler)
    import bt_live_api
    bt_live_api.warm(ROOT)
    print(f"Bitácora remote API at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    httpd.serve_forever()

def _server_stale(port: int) -> bool:
    """Check server metadata without stopping the process that owns the listener."""
    try:
        info = json.loads((STATE / "server.json").read_text(encoding="utf-8"))
    except Exception:
        return True
    return (info.get("port") == port and (info.get("version") != code_version()
                                           or info.get("root") != str(ROOT)))

def _stale(port: int) -> bool:
    """A running server on our port that runs old code or serves another bitácora."""
    try:
        info = json.loads((STATE / "server.json").read_text(encoding="utf-8"))
    except Exception:
        return True
    if info.get("port") != port or info.get("version") == code_version() and info.get("root") == str(ROOT):
        return False
    pid = info.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1 or pid == os.getpid():
        return False
    try:
        if platform() == "windows":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=10, check=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        return False
    for _ in range(20):
        if not is_running(port):
            return True
        import time
        time.sleep(0.2)
    return True

WEB_UNIT = "bitacora-web.service"            # the user's systemd unit for the panel on the default port, if installed
WEB_SOCKET_UNIT = "bitacora-web.socket"      # optional socket-activation unit that owns the listening port

def _unit_enabled() -> bool:
    if platform() != "linux":
        return False
    if not shutil.which("systemctl"):
        return False
    for unit in (WEB_UNIT, WEB_SOCKET_UNIT):
        try:
            out = subprocess.run(["systemctl", "--user", "is-enabled", unit], capture_output=True, text=True,
                                 timeout=5)
        except (OSError, subprocess.SubprocessError):
            return True  # Cannot prove systemd does not own the port; keep the loose path closed.
        if out.stdout.strip() in {"enabled", "enabled-runtime", "linked", "linked-runtime"}:
            return True
    return False

def ensure_server(port: int = DEFAULT_PORT) -> str:
    """Start the server detached in the background if it isn't running (or restart it if its code is stale)."""
    if port == DEFAULT_PORT and _unit_enabled():
        # systemd owns the panel: (re)start it there; a loose copy would hold the port and leave the unit failing
        if not is_running(port) or _server_stale(port):
            subprocess.run(["systemctl", "--user", "restart", WEB_UNIT], capture_output=True,
                           timeout=30, check=True)
        return url(port)
    if is_running(port):
        _stale(port)
    if not is_running(port):
        exe = Path(sys.executable)
        pyw = exe.with_name("pythonw.exe")
        cmd = [str(pyw if pyw.exists() else exe), str(SCRIPT), "serve", "--port", str(port)]
        subprocess.Popen(cmd, **detached_options(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True, env={**os.environ, "BITACORA_ROOT": str(ROOT)})
    return url(port)
