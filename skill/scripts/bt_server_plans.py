"""Plan list, events and simulation HTTP handlers."""
from __future__ import annotations

import json
import re
from urllib.parse import quote

from bt_core import *


class PlanListActions:
    def simulate(self, q: dict) -> None:
        from bt_server import (
            ROOT,
            SIMULATE_MAX_BYTES,
            SIMULATE_MAX_TASKS,
        )
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

    def plans_get(self, parts: list[str], q: dict) -> None:
        import bt_page_plans as pp
        import bt_plans_api as api
        from bt_server import (
            ROOT,
            token,
        )
        try:
            if parts == ["api", "flow", "proposal"]:
                import bt_owner_proposal_api
                data = bt_owner_proposal_api.view(ROOT, q.get("project", ""), q.get("req", ""), q.get("attempt", ""))
                return self.send(json.dumps(data, ensure_ascii=False), 200, "application/json; charset=utf-8")
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
        from bt_server import (
            ROOT,
        )
        actions = {"run": lambda p, r: self.run_plan(api, p, r, form.get("expected", "")),
                   "decide": lambda p, r: api.decide(ROOT, p, r, form.get("request", ""), form.get("option", ""),
                                                     form.get("reason", "")),
                   "diagnose": lambda p, r: api.diagnose(ROOT, p, r, form.get("request", "")),
                   "attest": lambda p, r: api.attest(ROOT, p, r, form.get("task", ""), form.get("request", ""),
                                                     form.get("evidence", ""), by="owner"),
                   "recovery": lambda p, r: api.recovery_control(ROOT, p, r, form.get("action", ""), form.get("preview", ""),
                                                                 form.get("stop_generation", "")),
                   "heal": lambda p, r: api.heal_control(ROOT, p, r, form.get("action", ""), form.get("case", "")),
                   "rework": lambda p, r: api.rework(ROOT, p, r, form.get("tasks", "").replace(",", " ").split(), form.get("reason", ""),
                                                     form.get("confirm_cost") == "1"),
                   "retry-task": lambda p, r: api.retry_task(ROOT, p, r, form.get("task", ""), form.get("reason", "")),
                   "cancel": lambda p, r: api.cancel_plan(ROOT, p, r, form.get("confirm", "")),
                   "delete": lambda p, r: api.delete_plan(ROOT, p, r, form.get("confirm", ""))}
        try:
            if len(parts) == 3 and parts[2] == "restore":
                msg = api.restore_plan(ROOT, parts[1], form.get("entry", ""))
                return self.redirect(f"/plans?msg={quote(msg)}")
            if len(parts) == 4 and parts[3] in actions:
                msg = actions[parts[3]](parts[1], parts[2])
                dest = "/plans" if parts[3] == "delete" else f"/plans/{quote(parts[1])}/{quote(parts[2])}"
                return self.redirect(self._back(form, dest, msg))
        except api.PlanError as exc:
            back = f"/plans/{quote(parts[1])}/{quote(parts[2])}" if len(parts) == 4 else "/plans"
            return self.redirect(self._back(form, back, str(exc)))
        self.send("Not found", 404, "text/plain")

    @staticmethod
    def _back(form: dict, default: str, msg: str) -> str:
        """Where an action returns: the Plan tab view it was pressed in (`back`, a local /p/ path only), else the plans page."""
        back = str(form.get("back") or "")
        if back.startswith("/p/") and not back.startswith("//") and "\n" not in back and "\\" not in back:
            base = re.sub(r"([?&])msg=[^&]*&?", r"\1", back).rstrip("?&")
            return f"{base}{'&' if '?' in base else '?'}msg={quote(msg)}"
        return f"{default}?msg={quote(msg)}"

    def run_plan(self, api, project: str, rid: str, expected: str) -> str:
        from bt_server import (
            ROOT,
            commit,
        )
        msg = api.run_plan(ROOT, project, rid, expected)
        commit(ROOT, f"{project}: {rid} run from the plan page (web)")
        return msg
