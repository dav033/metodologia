"""`python -m bt_durable …` (or `bt-durable …`): the operator's commands for the durable runtime.

  engine                                  run the engine service (systemd: deploy/bt-durable.service)
  start PROJECT REQ                       start the latest frozen revision of a NEW run under the durable runtime
  migrate PROJECT REQ [--apply|--rollback]  move a legacy run (dry run by default; see bt_durable.migrate)
  status PROJECT REQ                      run summary, task states, open decisions
  answer PROJECT REQ TASK REQUEST ACTION  answer an open decision (retry|retry_with_note|retry_other_route|stop)
  pause|resume PROJECT REQ                stop/allow starting new tasks (running agents continue)
  retry-task PROJECT REQ TASK             start a blocked task again (new round)
  cancel PROJECT REQ                      cancel every workflow of the run; the engine's reaper stops their units
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import bt_config
import bt_core
import bt_run_owner
from bt_contracts.execution import Backend, OwnerRecord, Route, RunRef
from bt_contracts.owner import OwnerAnswer

from . import migrate
from .settings import EngineConfig, Settings


ENV_FILE = Path.home() / ".config" / "bitacora" / "durable.env"   # 0600; the engine unit reads the same file


def database_url() -> str:
    """BT_DURABLE_DATABASE_URL (environment, or ~/.config/bitacora/durable.env) > execution.database_url > SQLite.
    The PostgreSQL password lives only in that 0600 file, never in the shared config."""
    import os
    url = os.environ.get("BT_DURABLE_DATABASE_URL", "")
    if not url and ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("BT_DURABLE_DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
    configured = url or bt_config.get("execution.database_url", "")
    return configured or f"sqlite:///{(Path(bt_core.STATE) / 'durable' / 'dbos.sqlite3').resolve()}"


def engine_config() -> EngineConfig:
    return EngineConfig(system_database_url=database_url(), state_dir=Path(bt_core.STATE) / "durable",
                        agent_concurrency=int(bt_config.get("execution.agent_concurrency", 2)),
                        verify_concurrency=int(bt_config.get("execution.verify_concurrency", 1)))


def routes() -> list[Route]:
    """`execution.routes`: "provider:profile:model[:effort]" entries, in preference order (validated at launch again)."""
    out = []
    for item in bt_config.get("execution.routes", []) or []:
        provider, profile, model, effort = (item.split(":") + ["", "", ""])[:4]
        out.append(Route(provider=provider, profile=profile, model=model, effort=effort))
    return out


def requirement_dir(project: str, req: str) -> Path:
    hits = sorted((Path(bt_core.ROOT) / project / "requirements").glob(f"{req}-*"))
    if not hits:
        raise SystemExit(f"{project}/{req}: no requirement folder")
    return hits[0]


def latest_frozen(rdir: Path, project: str, req: str) -> RunRef:
    manifest = json.loads((rdir / "plan-revisions" / "MANIFEST.json").read_text(encoding="utf-8"))
    last = max(manifest["revisions"], key=lambda r: r["revision"])
    path = rdir / "plan-revisions" / f"PLAN.r{last['revision']}.json"
    if hashlib.sha256(path.read_bytes()).hexdigest() != last["sha256"]:
        raise SystemExit(f"{path.name} does not match its frozen hash")
    plan_id = json.loads(path.read_text())["plan_id"]
    return RunRef(project=project, req=req, plan_id=plan_id, revision=int(last["revision"]),
                  plan_sha256=last["sha256"], plan_path=path)


def preflight(run: RunRef, rdir: Path) -> None:
    """Refuse a run whose frozen plan has structural defects (bt_planner.preflight) before anything is enqueued."""
    import bt_plan_adapter
    import bt_verifier_env
    from bt_scheduler_verification_authority import owner_verification_authority
    roots = bt_plan_adapter.repo_roots(rdir) or {}
    environment, _ = bt_verifier_env.for_run(run.project, rdir)
    names = {name for name, _ in environment}
    authority = owner_verification_authority(rdir, run.project)
    report = bt_plan_adapter.preflight_check(json.loads(run.plan_path.read_text(encoding="utf-8")), roots,
                                             env_available=lambda n: n in names or authority.resource_available(n))
    for warning in report.warnings[:10]:
        print(f"warning: {warning}", file=sys.stderr)
    if not report.ok:
        raise SystemExit("PLAN_PREFLIGHT: " + "; ".join(report.errors[:6]))


def _client():
    from .client import Client
    return Client(database_url())


def _run_of(project: str, req: str) -> RunRef:
    rdir = requirement_dir(project, req)
    owner = bt_run_owner.read(rdir)
    if not owner or owner.get("backend") != "dbos":
        raise SystemExit(f"{project}/{req} is not owned by the durable runtime")
    return latest_frozen(rdir, project, req) if not (rdir / "RUN.durable-run.json").exists() else \
        RunRef.model_validate_json((rdir / "RUN.durable-run.json").read_text())


def cmd_engine(_args) -> int:
    from bt_scheduler_executor_adapter import MethodologyDriver, repositories

    from .service import serve, wire
    cfg = engine_config()
    from .adapters.routes import LiveQuota
    serve(cfg, wire(cfg, repositories_for=lambda project: repositories(project),
                    driver_for=lambda project: MethodologyDriver(project), routes=routes(), capacity=LiveQuota()))
    return 0


def cmd_start(args) -> int:
    rdir = requirement_dir(args.project, args.req)
    if (Path(bt_core.STATE) / "scheduler" / f"{args.project}-{args.req}.db").exists():
        raise SystemExit("this run has legacy Scheduler state: use `migrate`, not `start`")
    run = latest_frozen(rdir, args.project, args.req)
    preflight(run, rdir)
    current = bt_run_owner.read(rdir)
    if not current:
        record = OwnerRecord(run_id=run.run_id, backend=Backend.DBOS, workflow_id=f"bt:{run.run_id}",
                             since=time.time(), by="bt-durable start")
        bt_run_owner.write(rdir, record.model_dump(mode="json"), expect=None)
    elif current.get("backend") != "dbos":
        raise SystemExit("the run is owned by the legacy runtime")
    (rdir / "RUN.durable-run.json").write_text(run.model_dump_json(indent=1), encoding="utf-8")
    client = _client()
    try:
        print(client.start(run, Settings()))
    finally:
        client.close()
    return 0


def cmd_migrate(args) -> int:
    import bt_scheduler_ops as ops
    rdir = requirement_dir(args.project, args.req)
    inv = migrate.inventory(state_dir=Path(bt_core.STATE), rdir=rdir, project=args.project, req=args.req,
                            owner_pids=ops.owner_pids(args.project, args.req))
    if args.rollback:
        client = _client()
        try:
            cancelled = client.cancel(migrate.run_ref(inv))
        finally:
            client.close()
        print(json.dumps({"cancelled": cancelled, "owner": migrate.release(rdir, by="bt-durable migrate --rollback")},
                         indent=1))
        return 0
    report = migrate.diff(inv, rdir)
    if not args.apply:
        print(json.dumps(report, indent=1, ensure_ascii=False))
        return 2 if inv.blockers else 0
    preflight(migrate.run_ref(inv), rdir)
    backup = migrate.backup(Path(bt_core.STATE), rdir, inv, Path(bt_core.STATE) / "durable" / "migrations")
    record = migrate.claim(rdir, inv, by="bt-durable migrate --apply")
    run = migrate.run_ref(inv)
    (rdir / "RUN.durable-run.json").write_text(run.model_dump_json(indent=1), encoding="utf-8")
    client = _client()
    try:
        workflow = client.start(run, Settings(), migrate.legacy_progress(inv))
    finally:
        client.close()
    print(json.dumps({"owner": record.model_dump(mode="json"), "backup": str(backup), "workflow": workflow,
                      "counts": report["counts"]}, indent=1))
    return 0


def cmd_status(args) -> int:
    client = _client()
    try:
        print(json.dumps(client.status(_run_of(args.project, args.req)), indent=1, default=str, ensure_ascii=False))
    finally:
        client.close()
    return 0


def cmd_answer(args) -> int:
    client = _client()
    try:
        answer = OwnerAnswer(request_id=args.request_id, action=args.action, note=args.note or "", by="owner")
        print(client.answer(_run_of(args.project, args.req), args.task, answer))
    finally:
        client.close()
    return 0


def cmd_command(args) -> int:
    client = _client()
    try:
        kind = {"pause": "pause", "resume": "resume", "retry-task": "retry_task"}[args.cmd]
        sent = client.command(_run_of(args.project, args.req), kind, task_id=getattr(args, "task", None),
                              note=getattr(args, "note", "") or "")
        print(sent.model_dump_json())
    finally:
        client.close()
    return 0


def cmd_cancel(args) -> int:
    client = _client()
    try:
        print(json.dumps(client.cancel(_run_of(args.project, args.req))))
    finally:
        client.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bt-durable", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("engine")
    for name in ("start", "status", "pause", "resume", "cancel"):
        p = sub.add_parser(name)
        p.add_argument("project")
        p.add_argument("req")
    m = sub.add_parser("migrate")
    m.add_argument("project")
    m.add_argument("req")
    group = m.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", action="store_true")
    a = sub.add_parser("answer")
    for name in ("project", "req", "task", "request_id"):
        a.add_argument(name)
    a.add_argument("action", choices=("retry", "retry_with_note", "retry_other_route", "stop"))
    a.add_argument("--note", default="")
    r = sub.add_parser("retry-task")
    for name in ("project", "req", "task"):
        r.add_argument(name)
    r.add_argument("--note", default="")
    args = parser.parse_args(argv)
    handlers = {"engine": cmd_engine, "start": cmd_start, "migrate": cmd_migrate, "status": cmd_status,
                "answer": cmd_answer, "pause": cmd_command, "resume": cmd_command, "retry-task": cmd_command,
                "cancel": cmd_cancel}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
