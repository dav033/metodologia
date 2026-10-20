"""Authenticated, versioned HTTP surface for the laptop's remote gateway."""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import re
import sqlite3
import stat
import subprocess
from urllib.parse import parse_qs, urlparse

PREFIX = "/api/remote/v1"
MAX_BODY = 256 * 1024
_ATTEMPT_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
_REVIEW_FILE_MAX = 1 << 20
_REVIEW_OUTPUT_MAX = 256 * 1024
_REVIEW_DIFF_TIMEOUT = 3


def _json(handler, payload: dict, status: int = 200, content_type: str = "application/json; charset=utf-8") -> None:
    handler.send(json.dumps(payload, ensure_ascii=False), status, content_type)


def _problem(handler, status: int, code: str, message: str) -> None:
    _json(handler, {"code": code, "message": message}, status, "application/problem+json; charset=utf-8")


def _authorized(handler) -> bool:
    expected = os.environ.get("FLOW_GATEWAY_KEY", "")
    supplied = handler.headers.get("Authorization", "")
    scheme, _, value = supplied.partition(" ")
    if not expected or scheme.lower() != "bearer" or not value:
        return False
    return hmac.compare_digest(value.encode("utf-8"), expected.encode("utf-8"))


def _path(handler) -> tuple[str, dict[str, str]]:
    parsed = urlparse(handler.path)
    query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
    return parsed.path, query


def _runs() -> list[dict]:
    import bt_live_api as live
    return [_mobile_run(run) for run in live.run_summaries(None, "global")]


def _mobile_run(run: dict) -> dict:
    """Translate the live API vocabulary to the stable mobile snapshot v1 contract."""
    attempts = [task.get("attempt") for task in run.get("tasks", []) if task.get("attempt")]
    active = next((attempt for attempt in attempts if attempt.get("live")), None)
    return {**run, "req": run.get("req_id"), "state": run.get("status"),
            "activeAttempt": active, "lastSeenAt": run.get("updated_at"),
            "tasks": [{**task, "activeAttempt": task.get("attempt")} for task in run.get("tasks", [])]}


def _shared_now_items() -> list[dict]:
    """Read live attempts from the same cached now frame used by the local SSE clients."""
    import bt_live_api as live
    frame = live._now_frame(None).decode("utf-8")
    for line in frame.splitlines():
        if line.startswith("data: "):
            payload = json.loads(line[6:])
            return payload.get("items", [])
    return []


def _snapshot_runs() -> list[dict]:
    """Add live task and liveness data to run summaries using the shared now read model."""
    runs = [_mobile_run(run) for run in _runs()]
    now_by_run = {}
    for item in _shared_now_items():
        key = f'{item.get("project", "")}/{item.get("req_id", "")}'
        now_by_run.setdefault(key, []).append(item)

    for run in runs:
        live_items = now_by_run.get(run.get("run"), [])
        active = live_items[0] if live_items else None
        task_by_id = {task.get("id"): task for task in run.get("tasks", [])}
        active_task = task_by_id.get(active.get("task")) if active else None
        attempts = [attempt for task in run.get("tasks", [])
                    for attempt in [task.get("attempt"), *(task.get("history") or [])]]
        last_activity = [attempt.get("last_activity_at") for attempt in attempts
                         if attempt and attempt.get("last_activity_at")]
        run["active_task"] = ({"id": active_task.get("id"), "title": active_task.get("title")}
                              if active_task else None)
        run["last_sign_of_life"] = max(last_activity, default=run.get("updated_at"))
    return runs


def _plans() -> list[dict]:
    import bt_plans_api as plans
    from bt_core import ROOT
    rows = plans.plans_payload(ROOT)
    enriched = []
    for row in rows:
        item = {**row, "req": row.get("req_id"), "state": row.get("plan_status"),
                "updatedAt": row.get("updated_at"), "revision": row.get("revision")}
        try:
            status = plans.status_of(ROOT, row["project"], row["req_id"])
            item["state"] = status.get("plan", {}).get("status", row.get("plan_status"))
            item["revision"] = status.get("plan", {}).get("revision")
            item["decisions"] = status.get("decisions", [])
            item["rounds"] = status.get("open_rounds", [])
            item["tasks"] = status.get("tasks", [])
            item["acceptanceCriteria"] = status.get("acceptance_criteria", [])
        except (KeyError, OSError, ValueError):
            item.update(decisions=[], rounds=[])
        enriched.append(item)
    return enriched


def _planning_detail() -> tuple[list[dict], list[dict]]:
    """Project open rounds and owner decisions into the snapshot fields consumed by mobile clients."""
    import bt_core
    import bt_plans_api
    import bt_rounds
    rounds, decisions = [], []
    for plan in _plans():
        project, req = plan.get("project"), plan.get("req_id")
        if not isinstance(project, str) or not isinstance(req, str):
            continue
        try:
            rdir = bt_plans_api.req_dir(bt_core.ROOT, project, req)
        except (ValueError, bt_plans_api.PlanError, OSError):
            continue
        for path in bt_rounds.list_rounds(rdir):
            try:
                value = bt_rounds.load(path)
            except (OSError, ValueError):
                continue
            rounds.append({**value, "project": project, "req": req})
        for decision in plan.get("decisions", []):
            if isinstance(decision, dict):
                decisions.append({**decision, "project": project, "req": req})
    return rounds, decisions


def _read_review_file(path, limit: int = _REVIEW_FILE_MAX) -> bytes | None:
    """Read a bounded regular artifact without following symlinks."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
    except OSError:
        return None
    finally:
        os.close(fd)
    return data if len(data) <= limit else None


def _review_executor_attempt(rdir, attempt_id: str):
    """Find the M3 attempt artifact under this run's executor roots, verifying its ledger identity."""
    import bt_scheduler_adapter as scheduler

    db = scheduler.run_db_path(rdir)
    roots = db.parent.parent / "executor"
    try:
        candidates = list(roots.glob(f"{db.stem}-r*"))
    except OSError:
        return None
    for root in candidates:
        if root.is_symlink() or not root.is_dir():
            continue
        ledger = root / "ledger.db"
        if not ledger.is_file() or ledger.is_symlink():
            continue
        try:
            connection = sqlite3.connect(f"{ledger.resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
            try:
                row = connection.execute(
                    "SELECT dirname,request FROM attempts WHERE attempt_id=?", (attempt_id,)
                ).fetchone()
            finally:
                connection.close()
        except (sqlite3.Error, OSError):
            continue
        if not row:
            continue
        try:
            request = json.loads(row[1])
        except (TypeError, ValueError):
            continue
        if not isinstance(request, dict) or request.get("attempt_id") != attempt_id:
            continue
        dirname = row[0]
        if not isinstance(dirname, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", dirname):
            continue
        attempt_dir = root / "attempts" / dirname
        try:
            if attempt_dir.resolve().is_relative_to(root.resolve()) and attempt_dir.is_dir():
                return attempt_dir.resolve()
        except OSError:
            continue
    return None


def _review_quality_result(rdir, attempt_id: str) -> tuple[dict | None, dict[str, bytes]]:
    """Read M6 verification result and output artifacts for an attempt without opening a writer store."""
    import bt_run_stores

    db = bt_run_stores.paths(rdir).get("m6")
    if not db or not db.is_file() or db.is_symlink():
        return None, {}
    try:
        connection = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute("SELECT request_json,result_json FROM requests WHERE result_json IS NOT NULL").fetchall()
            for row in rows:
                request = json.loads(row["request_json"])
                if not isinstance(request, dict) or request.get("attempt_id") != attempt_id:
                    continue
                result = json.loads(row["result_json"])
                if not isinstance(result, dict) or not isinstance(result.get("checks"), list):
                    return None, {}
                output: dict[str, bytes] = {}
                for check in result["checks"]:
                    if not isinstance(check, dict):
                        continue
                    for key in ("stdout_ref", "stderr_ref"):
                        reference = check.get(key)
                        if not isinstance(reference, str) or not re.fullmatch(r"m6://artifact/[a-f0-9]{64}", reference):
                            continue
                        digest = reference.rsplit("/", 1)[-1]
                        artifact = connection.execute("SELECT content FROM artifacts WHERE digest=?", (digest,)).fetchone()
                        if artifact and hashlib.sha256(bytes(artifact[0])).hexdigest() == digest:
                            output[reference] = bytes(artifact[0])
                return result, output
        finally:
            connection.close()
    except (sqlite3.Error, OSError, UnicodeError, ValueError):
        return None, {}
    return None, {}


def _verification_section(result: dict | None, artifacts: dict[str, bytes]) -> dict:
    checks = []
    for item in (result or {}).get("checks", []):
        if not isinstance(item, dict):
            continue
        stdout = artifacts.get(item.get("stdout_ref"), b"").decode("utf-8", errors="replace")
        stderr = artifacts.get(item.get("stderr_ref"), b"").decode("utf-8", errors="replace")
        checks.append({"command": item.get("command", ""), "exitCode": item.get("exit_code"),
                       "output": (stdout + stderr)[:_REVIEW_OUTPUT_MAX]})
    failed = next((item for item in checks if item.get("exitCode") != 0), None)
    return {"command": failed.get("command") if failed else (checks[0].get("command") if checks else None),
            "output": failed.get("output") if failed else (checks[0].get("output") if checks else ""),
            "checks": checks}


def _diff_section(attempt_dir) -> dict:
    handoff_dir = attempt_dir / "handoff" if attempt_dir else None
    if handoff_dir and (handoff_dir.is_symlink() or not handoff_dir.resolve().is_relative_to(attempt_dir.resolve())):
        handoff_dir = None
    manifest_raw = _read_review_file(handoff_dir / "manifest.json") if handoff_dir else None
    try:
        manifest = json.loads(manifest_raw.decode("utf-8")) if manifest_raw else {}
    except (UnicodeError, ValueError):
        manifest = {}
    changed = manifest.get("changed") if isinstance(manifest, dict) else None
    files = [str(item) for item in changed if isinstance(item, str)] if isinstance(changed, list) else []
    patch_path = handoff_dir / "changes.patch" if handoff_dir else None
    stat_text = None
    patch = _read_review_file(patch_path, _REVIEW_OUTPUT_MAX) if patch_path else None
    if patch is not None:
        try:
            result = subprocess.run(["git", "apply", "--stat"], input=patch, capture_output=True,
                                    timeout=_REVIEW_DIFF_TIMEOUT, check=False)
            if result.returncode == 0:
                stat_text = result.stdout.decode("utf-8", errors="replace").strip()[-4000:]
        except (OSError, subprocess.TimeoutExpired):
            pass
    if stat_text is None and isinstance(manifest, dict) and isinstance(manifest.get("changed_total"), int):
        count = manifest["changed_total"]
        stat_text = f"{count} files changed" if count != 1 else "1 file changed"
    return {"stat": stat_text, "files": files}


def _failure_review(attempt_id: str) -> dict | None:
    """Compose the frontend's four-section view from the authoritative live read model and durable M1/M3/M6 records."""
    import bt_attempt_facts
    import bt_live_api as live

    for _, rdir in live.runs(None):
        facts = bt_attempt_facts.attempt_facts(rdir)
        match = next(((task_id, item) for task_id, history in facts.items()
                      for item in history if item.get("attempt") == attempt_id), None)
        if match is None:
            continue
        _, attempt = match
        if attempt.get("state") not in {"failed", "rejected"} and not attempt.get("failure"):
            return None
        attempt_dir = _review_executor_attempt(rdir, attempt_id)
        result, artifacts = _review_quality_result(rdir, attempt_id)
        log_bytes = _read_review_file(attempt_dir / "output.tail", _REVIEW_OUTPUT_MAX) if attempt_dir else None
        log_lines = (log_bytes.decode("utf-8", errors="replace").splitlines() if log_bytes else [])[-200:]
        cause = attempt.get("failure") or attempt.get("state") or "unknown"
        return {"attemptId": attempt_id, "cause": cause,
                "verification": _verification_section(result, artifacts),
                "diff": _diff_section(attempt_dir), "logTail": "\n".join(log_lines)}
    return None


def route_get(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    path, query = _path(handler)
    if path == f"{PREFIX}/health":
        from bt_server import code_version
        return _json(handler, {"schemaVersion": 1, "status": "ok",
                               "version": code_version(),
                               "checkedAt": dt.datetime.now(dt.UTC).isoformat()})
    try:
        if path == f"{PREFIX}/snapshot":
            from bt_remote_events import redact
            rounds, decisions = _planning_detail()
            return _json(handler, redact({"schemaVersion": 1, "runs": _snapshot_runs(), "plans": _plans(),
                                   "rounds": rounds, "decisionRequests": decisions,
                                   "generatedAt": dt.datetime.now(dt.UTC).isoformat(), "cursor": ""}))
        if path == f"{PREFIX}/runs":
            return _json(handler, {"runs": _runs()})
        if path == f"{PREFIX}/routes":
            target, task = query.get("target", ""), query.get("task", "")
            if not target or not re.fullmatch(r"[A-Za-z0-9_-]+/REQ-[0-9]+", target) or \
                    not re.fullmatch(r"T[0-9A-Za-z_-]{1,79}", task):
                return _problem(handler, 400, "INVALID_ROUTE_QUERY", "Se requieren target y task válidos.")
            import bt_remote_commands as commands
            import bt_remote_recovery as recovery
            try:
                project, _, rdir = commands._run_target(target)
                return _json(handler, {"routes": recovery.route_options(project, rdir, task)})
            except ValueError as exc:
                return _problem(handler, 404, "ROUTES_UNAVAILABLE", str(exc))
        if path == f"{PREFIX}/plans":
            return _json(handler, {"plans": _plans()})
        if path == f"{PREFIX}/history":
            import bt_remote_commands as commands
            return _json(handler, {"history": commands.Ledger().rows()})
        if path == f"{PREFIX}/challenges":
            return _problem(handler, 503, "CHALLENGES_UNAVAILABLE", "Los desafíos aún no están disponibles.")
        if path == f"{PREFIX}/quotas":
            import bt_quota_live
            import bt_remote_events as remote_events
            checked_at = dt.datetime.now(dt.UTC).isoformat()
            accounts = bt_quota_live.read_all_live()
            return _json(handler, remote_events.redact({"accounts": accounts, "checkedAt": checked_at}))
        if path == f"{PREFIX}/events":
            import bt_live_api as live
            import bt_remote_events as remote_events
            try:
                limit = int(query.get("limit", "200"))
            except ValueError:
                return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
            if limit < 1:
                return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
            limit = min(limit, 1000)
            after = query.get("after", "")
            if after and not re.fullmatch(r"evt_[a-f0-9]{64}", after):
                return _problem(handler, 400, "INVALID_CURSOR", "El cursor no es válido.")
            rows, _, _ = live.flow_events(None, "global", limit=5000)
            events = [event for row in rows if (event := remote_events.from_flow(row)) is not None]
            plans = _plans()
            events.extend(remote_events.decision_events(plans))
            rounds, _ = _planning_detail()
            import bt_quota_live
            import bt_remote_commands as commands
            events.extend(remote_events.from_snapshot(_snapshot_runs(), rounds,
                                                       quotas=bt_quota_live.read_all_live(),
                                                       commands=commands.Ledger().rows()))
            if after and all(event["cursor"] != after for event in events):
                return _problem(handler, 400, "INVALID_CURSOR", "El cursor no es válido.")
            page, cursor, has_more = remote_events.page(events, after, limit)
            return _json(handler, remote_events.redact({"events": page, "nextCursor": cursor, "hasMore": has_more}))
        if path == f"{PREFIX}/commands":
            import bt_remote_commands as commands
            return _json(handler, {"commands": commands.Ledger().rows()})
        match = re.fullmatch(re.escape(PREFIX) + r"/attempts/([^/]+)/review", path)
        if match:
            if not _ATTEMPT_ID.fullmatch(match.group(1)):
                return _problem(handler, 400, "INVALID_ID", "El identificador del intento no es válido.")
            import bt_remote_events as remote_events
            review = _failure_review(match.group(1))
            if review is None:
                return _problem(handler, 404, "ATTEMPT_NOT_FOUND", "No se encontró el intento.")
            return _json(handler, remote_events.redact(review))
    except (ValueError, OSError):
        return _problem(handler, 503, "STARTING", "La API remota aún no está disponible.")
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")


HANDLERS: dict = {}     # additional command handlers supplied by later dispatch layers
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "COMMAND_NOT_IMPLEMENTED": 501, "STALE_PRECONDITION": 409,
                   "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409, "EFFECT_FAILED": 500,
                   "STATE_UNAVAILABLE": 503, "CONFIRMATION_REQUIRED": 409}


def _target_state(target: str) -> dict | None:
    import bt_remote_commands as commands
    return commands.target_state(target)


def _submit_command(handler, length: int) -> None:
    import bt_remote_commands as commands
    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_COMMAND", "El cuerpo debe ser JSON válido.")
    handlers = commands.dispatch_handlers()
    handlers.update(HANDLERS)
    result = commands.Ledger().submit(request, handlers, _target_state)
    _json(handler, result, _COMMAND_STATUS.get(result.get("code") or result["status"], 200))


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    path, _ = _path(handler)
    if path == f"{PREFIX}/commands":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_COMMAND", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        return _submit_command(handler, length)
    if path == f"{PREFIX}/challenges":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_CHALLENGE", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        try:
            body = json.loads(handler.rfile.read(length) or b"null")
        except (ValueError, OSError):
            return _problem(handler, 400, "INVALID_CHALLENGE", "El cuerpo debe ser JSON válido.")
        if not isinstance(body, dict) or set(body) not in ({"target", "typed_req"}, {"target", "typedReq"}) \
                or not isinstance(body.get("target"), str):
            return _problem(handler, 400, "INVALID_CHALLENGE", "Se requieren target y typedReq.")
        import bt_remote_commands as commands
        try:
            challenge = commands.Ledger().issue_challenge(body["target"], body.get("typed_req", body.get("typedReq")))
        except ValueError as exc:
            return _problem(handler, 400, "INVALID_CHALLENGE", str(exc))
        return _json(handler, challenge, 201)
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
