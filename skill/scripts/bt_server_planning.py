"""Planning, Designer and subplan actions on the local owner's HTTP panel."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

from bt_core import find_req, req_id


class PlanningActions:
    def planning_get(self, project: str, req: str, what: str, q: dict) -> None:
        from bt_server import ROOT, token
        """Live fragment of the plan tab (and a nudge for the Designer and translator), or a sandboxed mockup."""
        import bt_design_drafts as drafts
        import bt_page_planning as planning
        rdir = find_req(ROOT / project, req)
        if what == "mockup":
            ref = q.get("contract", "")
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5}", ref):
                return self.send("Not found", 404, "text/plain")
            rev = int(q["rev"]) if planning._number(q.get("rev", "")) else None
            mockup = drafts.revision_file(rdir, ref, rev, ".html")
            if q.get("direction"):
                import bt_design_directions
                mockup = bt_design_directions.preview(rdir, ref, q["direction"], rev)
                if mockup is None:
                    return self.file(None)
            if not mockup.is_file():
                return self.file(None)
            import bt_mockup_bridge
            return self.send(bt_mockup_bridge.inject(mockup.read_text(encoding="utf-8", errors="replace")), 200,
                             "text/html; charset=utf-8", sandbox=True)
        opts = planning.options(rdir, q)
        planning.follow(project, rdir, opts["lang"])
        html = planning.fragment(project, req_id(rdir), rdir, planning.plan_status(rdir), token(),
                                 opts)
        return self.send(json.dumps({"html": html}, ensure_ascii=False), 200, "application/json; charset=utf-8")

    def planning_post(self, project: str, rdir: Path, action: str, form: dict, base: str) -> str:
        import bt_design_drafts as drafts
        import bt_planning_flow as flow
        from bt_server import ROOT, commit
        ref, comments = form.get("contract", ""), form.get("comments", "").strip()
        sid = form.get("anchor", "")
        if action == "planning-outline":
            msg = flow.confirm_outline(project, rdir, "owner")
        elif action == "planning-focus":
            msg = flow.focus(project, rdir, sid, "owner")
        elif action == "planning-confirm":
            msg = flow.confirm(project, rdir, sid, "owner")
        elif action == "design-answer":
            import bt_planning_notes as notes
            question = form.get("question", "")
            row = next((r for r in drafts.rows(rdir) if r.get("ref") == ref and r.get("id") == sid), None)
            if not comments:
                msg = "Escribe tu respuesta."
            elif not row or question not in (row.get("questions") or []):
                msg = "La pregunta cambió; actualiza la página antes de responder."
            else:
                answer = re.sub(r"[ \t]+", " ", f"Owner answer to Designer question ({sid}, {ref}): {question} — {comments}")
                if len(answer) > notes.MAX_TEXT:
                    msg = "La respuesta es demasiado larga; acórtala antes de enviarla."
                elif not any(n.get("text") == answer for n in notes.notes(rdir)):
                    notes.add(rdir, answer, kind="finding", by="owner")
                    self.tell_planner(project, req_id(rdir), answer + " Incorporate this requirement answer; do not treat it as design feedback.")
                    msg = "Respuesta guardada para el Planner."
                else:
                    msg = "Esta respuesta ya estaba guardada para el Planner."
        elif action == "design-choose":
            import bt_design_directions
            try:
                msg = bt_design_directions.choose(project, rdir, ref, form.get("direction", ""), "web")
                self.tell_planner(project, req_id(rdir), f"Owner chose design direction for {ref}: {msg}")
            except SystemExit as exc:
                msg = str(exc)
        elif action == "design-iterate":
            import bt_design_iterate
            try:
                msg = bt_design_iterate.iterate(project, rdir, ref, form.get("direction", ""), comments, "web")
                self.tell_planner(project, req_id(rdir), f"Owner asked to iterate design direction of {ref}: {msg}")
            except SystemExit as exc:
                msg = str(exc)
        elif action == "design-amend":
            import bt_design_amend
            try:
                msg = bt_design_amend.start(project, rdir, ref, comments, "web")
                self.tell_planner(project, req_id(rdir), f"Owner asked to amend the design of {ref} with the plan change: {msg}")
            except SystemExit as exc:
                msg = str(exc)
        elif action == "design-feedback" or comments:
            msg = drafts.add_feedback(project, rdir, ref, comments, "web", direction=form.get("direction") or None)
        else:
            started = drafts.request(project, rdir, [ref] if ref else None, force=bool(ref), fresh=bool(ref), reason="web")
            msg = f"Designer iniciado para {', '.join(started)}." if started else "No había diseños que iniciar."
        commit(ROOT, f"{project}: {req_id(rdir)} planning ({action}, web)", push=False)
        if action in ("planning-outline", "planning-focus", "planning-confirm") and (action == "planning-focus" or "confirmad" in msg):
            self.tell_planner(project, req_id(rdir), f"On the web the owner did «{action}» ({sid or 'skeleton'}): {msg} "
                              f"Run `planning resume {req_id(rdir)}` and continue.")
        sp = form.get("anchor", "") if re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", form.get("anchor", "")) else ""
        return f"{base}?tab=plan&lang={quote(form.get('lang', ''))}&sp={quote(sp)}&msg={quote(msg)}"

    def verify_post(self, project: str, rid: str, rdir: Path, action: str, form: dict, base: str) -> str:
        from bt_server import ROOT, commit
        """The owner's per-subplan checkpoint: open that exact version locally, approve it or reject it with a note."""
        import bt_verification as verification
        import bt_verify_servers as servers
        sid = form.get("anchor", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", sid):
            msg, sid = "Subplan no válido.", ""
        elif action in ("verify-run", "verify-stop") and self.client_address[0] not in ("127.0.0.1", "::1"):
            msg = "Los servidores de prueba solo se arrancan desde esta máquina."
        elif action == "verify-run":                  # «Probar esta versión»: start its servers, the new tab waits for them
            started = servers.start(ROOT, project, rdir, sid)
            if started["ok"]:
                return f"{base}/verify-run?sp={quote(sid)}"
            msg = started["message"]
        elif action == "verify-stop":
            msg = servers.stop(ROOT, project, rdir, sid)
        elif action == "verify-open":
            msg = verification.open_local(ROOT, project, rdir, sid)[1]
        elif action == "verify-close":
            servers.stop(ROOT, project, rdir, sid)
            msg = verification.close_local(ROOT, project, rdir, sid)
        else:
            msg = verification.decide(project, rdir, sid, "approved" if action == "verify-approve" else "rejected",
                                      form.get("comments", ""), "owner", "web")
            commit(ROOT, f"{project}: {rid} verification ({action}, web)", push=False)
        return f"{base}?tab=plan&mode=subplans&view=verify&sp={quote(sid)}&msg={quote(msg)}"

    def tell_planner(self, project: str, rid: str, text: str) -> None:
        """Best effort: wake the web-managed Planner with what the owner just did; never fails the owner's action."""
        try:
            import bt_agent_terminal as terminal
            terminal.notify_planner(project, rid, text)
        except Exception:  # noqa: BLE001, S110
            pass

    def agent_post(self, project: str, rid: str, rdir: Path, action: str, form: dict, base: str) -> str:
        from bt_server import ROOT
        """Talk to an agent from the web: start the dedicated Planner, or type a message into its tmux session."""
        import bt_agent_terminal as terminal
        import bt_planning_activity as activity
        import bt_subplan_sessions as sessions
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            msg = "Los agentes solo se manejan desde esta máquina."
        elif action == "agent-start":
            msg = terminal.start_planner(ROOT, project, rdir)[1]
        elif action == "agent-restart":
            msg = terminal.restart_planner(ROOT, project, rdir)[1]
        else:
            kind, anchor, text = form.get("kind", ""), form.get("anchor", ""), form.get("text", "")
            live = sessions.active(rdir, anchor) if kind == "session" and re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", anchor) else None
            name = terminal.name_for(project, rid, "planner") if kind == "planner" else (live or {}).get("tmux", "")
            if not name:
                msg = "No encuentro ese agente."
            else:
                msg = terminal.send(name, text)
                if msg == "Enviado.":
                    activity.record(rdir, "Tú", "Le escribiste al " + ("Planner" if kind == "planner" else f"agente de {anchor}")
                                    + ": «" + " ".join(text.split())[:100] + "»", kind="say", sp=anchor if kind == "session" else "")
        return f"{base}?tab=plan&msg={quote(msg)}"

    def stage_post(self, project: str, rid: str, rdir: Path, form: dict, base: str) -> str:
        from bt_server import ROOT, commit
        """«Ejecutar subplan» (D-134): approve the confirmed subplan as part of the next stage and have the Scheduler run
        it. Loopback only: it starts the Scheduler's agents."""
        import bt_stages
        sid = form.get("anchor", "")
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            msg = "La ejecución solo se lanza desde esta máquina."
        elif not re.fullmatch(r"SP-[1-9][0-9]{0,3}", sid):
            msg, sid = "Subplan no válido.", ""
        else:
            try:
                msg = bt_stages.run(project, rdir, [sid], by="owner", via="web")
                commit(ROOT, f"{project}: {rid} stage run {sid} (web)", push=False)
                self.tell_planner(project, rid, f"On the web the owner ran {sid} through the Scheduler: {msg} "
                                  "Keep defining the other subplans; do not edit the approved ones without telling him.")
            except bt_stages.StageError as exc:
                msg = f"No se pudo ejecutar {sid}: {exc.message} [{exc.code}]"
        return f"{base}?tab=plan&lang={quote(form.get('lang', ''))}&sp={quote(sid)}&msg={quote(msg)}"

    def session_post(self, project: str, rid: str, rdir: Path, action: str, form: dict, base: str) -> str:
        from bt_server import ROOT
        """Hands-on session for one subplan: open an interactive agent window in its own worktree, or record its end."""
        import bt_subplan_sessions as sessions
        sid = form.get("anchor", "")
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            msg = "Las sesiones solo se abren desde esta máquina."
        elif not re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", sid):
            msg, sid = "Subplan no válido.", ""
        elif action == "session-start":
            msg = sessions.start(ROOT, project, rdir, sid, form.get("model") or sessions.DEFAULT_MODEL, form.get("mode") or "hands")[1]
        else:
            msg = sessions.finish(rdir, sid, "owner")
        return f"{base}?tab=plan&mode=subplans&view=session&sp={quote(sid)}&msg={quote(msg)}"
