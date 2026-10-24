"""CLI registration and presentation for machine-level accounts, usage and telemetry."""
from __future__ import annotations

import json
import sys


def register(sub):
    p_met = sub.add_parser("metrics", help="attempt telemetry per agent/profile/model/effort (null = not reported)")
    p_met.add_argument("--by", help="group keys, comma separated: agent,profile,model,effort,kind,tier,project")
    p_met.add_argument("--advice", action="store_true", help="plain-language observations instead of the table")
    p_met.add_argument("--attempts", type=int, metavar="N", help="the last N attempts, each as a key/value table")
    p_met.add_argument("--origin", choices=["all", "real", "synthetic"], default="all",
                       help="only measurements of real work, or only smoke/matrix checks (untagged rows count as real)")
    p_met.add_argument("--why", action="store_true", help="how attempts ended per agent/model/effort/kind/complexity, "
                       "with the reasons they failed or worked")
    p_ag = sub.add_parser("agents", help="agent catalog: models, ladder, accounts and usage-limit state; route preview")
    p_ag.add_argument("action", nargs="?", choices=["list", "route", "brief", "quota-clear"], default="list")
    p_ag.add_argument("profile", nargs="?", help="quota-clear: profile id")
    p_ag.add_argument("--kind", choices=["implement", "test", "docs", "audit", "research", "design"], default="implement")
    from bt_role_policy import ROLES
    p_ag.add_argument("--role", choices=ROLES)
    p_ag.add_argument("--complexity", choices=["S", "M", "L"])
    p_ag.add_argument("--tier", type=int, choices=[0, 1, 2])
    p_usage = sub.add_parser("usage", help="subscription 5h/weekly quotas without model calls")
    p_usage.add_argument("action", choices=["poll", "show", "install-timer", "timer-status"], default="show", nargs="?")
    p_cfg = sub.add_parser("config", help="machine settings (.state/config.json): get | set KEY VALUE | unset KEY")
    p_cfg.add_argument("action", choices=["get", "set", "unset"])
    p_cfg.add_argument("key", nargs="?")
    p_cfg.add_argument("value", nargs="?")


def dispatch_machine(a) -> bool:
    if a.cmd == "usage":
        import bt_subscription_schedule as schedule
        import bt_subscriptions as usage
        action = {"poll": usage.poll, "show": usage.summary,
                  "install-timer": schedule.install, "timer-status": schedule.status}[a.action]
        print(json.dumps(action(), indent=1, ensure_ascii=False))
        return True
    if a.cmd == "config":
        import bt_config
        print(bt_config.cli(a.action, a.key, a.value))
        return True
    if a.cmd != "metrics":
        return False
    import bt_events
    rows = bt_events.read_all()
    if a.origin != "all":
        rows = [r for r in rows if (r.get("origin") or "real") == a.origin]
    if a.advice:
        print("\n".join(bt_events.advice(rows, defects=bt_events.read_defects())))
    elif a.attempts:
        for row in rows[-a.attempts:]:
            pairs = bt_events.key_values(row)
            width = max(len(k) for k, _ in pairs)
            print("\n".join(f"{k.ljust(width)} : {v}" for k, v in pairs) + "\n" + "-" * 60)
    elif a.why:
        print(json.dumps(bt_events.reasons(rows), indent=1, ensure_ascii=False))
    else:
        by = [k.strip() for k in (a.by or "").split(",") if k.strip()] or None
        print(json.dumps(bt_events.summary(rows, by, bt_events.read_defects()), indent=1, ensure_ascii=False))
    return True


def dispatch_agents(a, project: str | None):
    import bt_agents
    if a.action == "brief":
        print(bt_agents.brief(project))
    elif a.action == "quota-clear":
        print("cleared" if bt_agents.quota_clear(a.profile or "") else "nothing to clear")
    elif a.action == "route":
        if not project:
            sys.exit("agents route needs a project (--project <name>)")
        import bt_delegate
        print(json.dumps(bt_delegate.auto_route(project, a.kind, a.tier, role=a.role, complexity=a.complexity), indent=1, ensure_ascii=False))
    else:
        print(json.dumps(bt_agents.catalog(project), indent=1, ensure_ascii=False))
