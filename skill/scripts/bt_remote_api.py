"""Authenticated v1 health endpoint for the remote gateway listener."""
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

import bt_remote_commands as _commands

PREFIX = "/api/remote/v1"
MAX_BODY = 256 * 1024
_ATTEMPT_ID = re.compile(r"[A-Za-z0-9._:-]{1,120}\Z")
_REVIEW_FILE_MAX = 1 << 20
_REVIEW_OUTPUT_MAX = 256 * 1024
_REVIEW_DIFF_TIMEOUT = 3


def _send_json(handler, payload: dict, status: int, content_type: str = "application/json; charset=utf-8") -> None:
    handler.send(json.dumps(payload, ensure_ascii=False), status, content_type)


def _problem(handler, status: int, code: str, message: str) -> None:
    _send_json(handler, {"code": code, "message": message}, status,
               "application/problem+json; charset=utf-8")


def _authorized(handler) -> bool:
    expected = os.environ.get("FLOW_GATEWAY_KEY", "")
    authorization = handler.headers.get("Authorization", "")
    scheme, separator, supplied = authorization.partition(" ")
    if not expected or not separator or scheme.lower() != "bearer" or not supplied:
        return False
    return hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))


def _path(handler) -> str:
    return urlparse(handler.path).path


def _query(handler) -> dict[str, str]:
    parsed = urlparse(handler.path)
    return {key: values[0] for key, values in parse_qs(parsed.query).items()}


def route_get(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")

    path = _path(handler)
    if path == f"{PREFIX}/snapshot":
        return _snapshot(handler)
    review_match = re.fullmatch(re.escape(f"{PREFIX}/attempts/") + r"([^/]+)/review", path)
    if review_match:
        attempt_id = review_match.group(1)
        target = _query(handler).get("target", "")
        if not _ATTEMPT_ID.fullmatch(attempt_id):
            return _problem(handler, 400, "INVALID_ID", "El identificador del intento no es válido.")
        if not re.fullmatch(r"[A-Za-z0-9_-]+/REQ-[0-9]+", target):
            return _problem(handler, 400, "INVALID_TARGET", "Se requiere un target válido.")
        review = _failure_review(target, attempt_id)
        if review is None:
            return _problem(handler, 404, "ATTEMPT_NOT_FOUND", "No se encontró el intento fallido en esa ejecución.")
        return _send_json(handler, review, 200)
    if path in (f"{PREFIX}/commands", f"{PREFIX}/history"):
        return _command_history(handler)
    if path == f"{PREFIX}/quotas":
        return _quotas(handler)
    if path == f"{PREFIX}/routes":
        return _routes(handler)
    if path == f"{PREFIX}/events":
        import bt_remote_events as feed
        try:
            limit = int(_query(handler).get("limit", "200"))
        except ValueError:
            return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
        if limit < 1:
            return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
        query = _query(handler)
        try:
            feed.page([], query.get("after", ""), min(limit, 1000))
        except feed.CursorError as exc:
            return _problem(handler, 400, "INVALID_CURSOR", str(exc))
        import bt_core
        import bt_live_api as live
        import bt_plans_api
        import bt_subscriptions
        import bt_remote_commands as commands

        try:
            runs = live.run_summaries(bt_core.ROOT, "global")
            plans = bt_plans_api.plans_payload(bt_core.ROOT)
            quotas = bt_subscriptions.summary()
            ledger = commands.Ledger()
            rows = ledger.rows()
            events = feed.collect(bt_core.ROOT, runs, plans, quotas, rows)
            return _send_json(handler, feed.page(events, query.get("after", ""), min(limit, 1000)), 200)
        except feed.CursorError as exc:
            return _problem(handler, 400, "INVALID_CURSOR", str(exc))
        except (OSError, ValueError, bt_plans_api.PlanError):
            return _problem(handler, 503, "EVENTS_UNAVAILABLE", "El feed remoto aún no está disponible.")
    if path != f"{PREFIX}/health":
        return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")

    from bt_server import code_version

    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "status": "ok", "version": code_version(),
                                "checkedAt": checked_at}, 200)


def _snapshot(handler) -> None:
    """Compact run read model, with live task signals taken from the panel's shared now frame."""
    import bt_core
    import bt_live_api as live

    root = bt_core.ROOT
    try:
        summaries = live.run_summaries(root, "global")
        now = live.now_frame_data(root)
        import bt_plans_api
        import bt_rounds
        plan_summaries = bt_plans_api.plans_payload(root)
    except Exception:
        return _problem(handler, 503, "SNAPSHOT_UNAVAILABLE", "La vista remota aún no está disponible.")

    active_by_run: dict[str, dict] = {}
    for item in now["items"]:
        active_by_run.setdefault(f'{item["project"]}/{item["req_id"]}', item)

    runs = []
    for run in summaries:
        active = active_by_run.get(run["run"])
        attempts = [attempt for task in run["tasks"] for attempt in task["history"]]
        last_activity = max((a.get("last_activity_at") for a in attempts if a.get("last_activity_at")), default=None)
        if last_activity is None:
            last_activity = run.get("updated_at")
        tasks = []
        for task in run["tasks"]:
            review = next((a for a in reversed(task["history"]) if a.get("state") == "rejected"), None)
            current = task.get("attempt")
            tasks.append({"id": task["id"], "title": task["title"], "state": task["state"],
                          "activeAttempt": live._attempt(current) if current and current.get("live") else None,
                          "reviewAttempt": live._attempt(review),
                          "history": [live._attempt(a) for a in task["history"]]})
        runs.append({"id": run["run"], "project": run["project"], "req": run["req_id"],
                     "reqId": run["req_id"],
                     "state": run.get("status") or ("running" if run.get("active") else "idle"),
                     "title": run["title"], "status": run["status"], "active": run["active"],
                     "activeTask": ({"id": active["task"], "title": active["task_title"],
                                     "state": active["state"], "attempt": live._attempt(active["attempt"])}
                                    if active else None),
                     "lastActivityAt": last_activity, "tasks": tasks})
    plans, rounds, decisions = [], [], []
    for plan in plan_summaries:
        project, req = plan["project"], plan["req_id"]
        rdir = bt_plans_api.req_dir(root, project, req)
        plans.append({"id": f"{project}/{req}", "project": project, "req": req,
                      "state": plan.get("plan_status") or "unknown", "revision": plan.get("revision"),
                      "updatedAt": plan.get("updated_at")})
        decisions.extend({**request, "project": project, "req": req,
                          "options": [{"id": option, "label": option.replace("_", " "),
                                       "consequence": option.replace("_", " ")}
                                      for option in request.get("options", []) if isinstance(option, str)]}
                         for request in bt_plans_api.open_decisions(rdir))
        for number in bt_plans_api.open_rounds(rdir):
            try:
                data = bt_rounds.load(bt_rounds.rounds_dir(rdir) / f"round-{number:02d}.json")
            except (OSError, ValueError):
                continue
            rounds.append({"project": project, "req": req, "round": number,
                           **{key: data[key] for key in ("id", "title", "intro", "coverage", "status", "questions")
                              if key in data}})
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at,
                                "runs": runs, "plans": plans, "rounds": rounds,
                                "decisionRequests": decisions}, 200)


def _command_history(handler) -> None:
    query = _query(handler)
    try:
        limit = int(query.get("limit", "200"))
    except ValueError:
        limit = 0
    if not 1 <= limit <= 1000:
        return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
    try:
        import bt_remote_commands as commands
        items, cursor = commands.Ledger().history(query.get("after", ""), limit)
    except ValueError:
        return _problem(handler, 400, "INVALID_CURSOR", "El cursor no es válido.")
    return _send_json(handler, {"commands": items, "nextCursor": cursor}, 200)


def _quotas(handler) -> None:
    import bt_quota_live

    try:
        rows = bt_quota_live.read_all_live()
    except Exception:
        rows = []
    accounts = []
    for row in rows:
        windows = []
        for name, window in sorted((row.get("windows") or {}).items()):
            if not isinstance(window, dict) or window.get("used_percent") is None:
                continue
            reset = window.get("resets_at")
            windows.append({"window": name, "usedPercent": window["used_percent"],
                            "resetsAt": dt.datetime.fromtimestamp(reset, dt.UTC).isoformat()
                            if isinstance(reset, (int, float)) else None})
        observed = row.get("observed_at")
        accounts.append({"account": row.get("profile"), "provider": row.get("provider"),
                         "status": row.get("status"),
                         "observedAt": dt.datetime.fromtimestamp(observed, dt.UTC).isoformat()
                         if isinstance(observed, (int, float)) else None, "windows": windows})
    if not accounts:
        return _problem(handler, 503, "QUOTAS_UNAVAILABLE", "Las cuotas aún no están disponibles.")
    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"accounts": accounts, "checkedAt": checked_at}, 200)


def _routes(handler) -> None:
    query = _query(handler)
    target, task = query.get("target", ""), query.get("task", "")
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+/REQ-[0-9]+", target) or \
            not re.fullmatch(r"T[0-9A-Za-z_-]{1,79}", task):
        return _problem(handler, 400, "INVALID_ROUTE_QUERY", "Se requieren target y task válidos.")
    try:
        import bt_plans_api
        import bt_remote_commands as commands
        import bt_remote_recovery as recovery
        project, _, rdir = commands._run_target(target)
        routes = recovery.route_options(project, rdir, task)
    except (ValueError, OSError, sqlite3.Error, bt_plans_api.PlanError):
        return _problem(handler, 404, "ROUTES_UNAVAILABLE", "Las rutas no están disponibles para esta ejecución.")
    return _send_json(handler, {"routes": routes}, 200)


HANDLERS: dict[str, _commands.Handler] = _commands.dispatch_handlers()
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "CONFIRMATION_REQUIRED": 400,
                   "COMMAND_NOT_IMPLEMENTED": 501, "STALE_PRECONDITION": 409,
                   "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409,
                   "EFFECT_FAILED": 500, "ROUTE_UNAVAILABLE": 409, "STATE_UNAVAILABLE": 503}
def _read_review_file(path, limit: int = _REVIEW_FILE_MAX) -> bytes | None:
    """Read a bounded regular artifact without following symlinks or blocking on special files."""
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


def _tail_review_file(path, limit: int = _REVIEW_OUTPUT_MAX) -> bytes | None:
    """Read at most the final `limit` bytes of a regular artifact without following symlinks."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        size = os.lseek(fd, 0, os.SEEK_END)
        os.lseek(fd, max(0, size - limit), os.SEEK_SET)
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read(limit)
    except OSError:
        return None
    finally:
        os.close(fd)


def _review_executor_attempt(rdir, attempt_id: str):
    """Find the attempt directory only after its executor ledger confirms the exact id."""
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
        if ledger.is_symlink() or not ledger.is_file():
            continue
        try:
            connection = sqlite3.connect(f"{ledger.resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
            try:
                row = connection.execute("SELECT dirname,request FROM attempts WHERE attempt_id=?",
                                         (attempt_id,)).fetchone()
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
        dirname = row[0]
        if not isinstance(request, dict) or request.get("attempt_id") != attempt_id \
                or not isinstance(dirname, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", dirname):
            continue
        attempts_dir = root / "attempts"
        attempt_dir = attempts_dir / dirname
        if attempts_dir.is_symlink() or attempt_dir.is_symlink():
            continue
        try:
            resolved_root = root.resolve(strict=True)
            resolved_dir = attempt_dir.resolve(strict=True)
            if resolved_dir.is_relative_to(resolved_root) and resolved_dir.is_dir():
                return resolved_dir
        except OSError:
            continue
    return None


def _review_quality_result(rdir, attempt_id: str) -> tuple[dict | None, dict[str, bytes]]:
    """Read the correlated M6 result and its referenced outputs through a read-only connection."""
    import bt_run_stores

    db = bt_run_stores.paths(rdir).get("m6")
    if not db or not db.is_file() or db.is_symlink():
        return None, {}
    try:
        connection = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT substr(request_json,1,65537) AS request_json,"
                "substr(result_json,1,1048577) AS result_json FROM requests "
                "WHERE result_json IS NOT NULL AND json_extract(request_json,'$.attempt_id')=? "
                "ORDER BY created_at DESC LIMIT 8",
                (attempt_id,)).fetchall()
            for row in rows:
                if len(row["request_json"] or "") > 65536 or len(row["result_json"] or "") > _REVIEW_FILE_MAX:
                    continue
                request = json.loads(row["request_json"])
                result = json.loads(row["result_json"])
                if not isinstance(request, dict) or request.get("attempt_id") != attempt_id \
                        or not isinstance(result, dict) or not isinstance(result.get("checks"), list):
                    continue
                output: dict[str, bytes] = {}
                for check in result["checks"]:
                    if not isinstance(check, dict):
                        continue
                    for key in ("stdout_ref", "stderr_ref"):
                        reference = check.get(key)
                        if not isinstance(reference, str) or not re.fullmatch(r"m6://artifact/[a-f0-9]{64}", reference):
                            continue
                        digest = reference.rsplit("/", 1)[-1]
                        artifact = connection.execute("SELECT coalesce(substr(content,1,?),x'') FROM artifacts WHERE digest=?",
                                                      (_REVIEW_OUTPUT_MAX + 1, digest)).fetchone()
                        if artifact and artifact[0] is not None and len(artifact[0]) <= _REVIEW_OUTPUT_MAX \
                                and hashlib.sha256(bytes(artifact[0])).hexdigest() == digest:
                            output[reference] = bytes(artifact[0])
                return result, output
        finally:
            connection.close()
    except (sqlite3.Error, OSError, UnicodeError, ValueError, TypeError):
        return None, {}
    return None, {}


def _review_verification(result: dict | None, artifacts: dict[str, bytes]) -> dict:
    checks = []
    for check in (result or {}).get("checks", []):
        if not isinstance(check, dict):
            continue
        stdout_ref, stderr_ref = check.get("stdout_ref"), check.get("stderr_ref")
        stdout = artifacts.get(stdout_ref, b"").decode("utf-8", errors="replace") if isinstance(stdout_ref, str) else ""
        stderr = artifacts.get(stderr_ref, b"").decode("utf-8", errors="replace") if isinstance(stderr_ref, str) else ""
        checks.append({"command": check.get("command") if isinstance(check.get("command"), str) else None,
                       "exitCode": check.get("exit_code"), "output": (stdout + stderr)[:_REVIEW_OUTPUT_MAX]})
    failed = next((check for check in checks if check.get("exitCode") != 0), None)
    selected = failed or (checks[0] if checks else {})
    return {"command": selected.get("command"), "output": selected.get("output", "")}


def _review_diff(attempt_dir) -> dict:
    if attempt_dir is None:
        return {"stat": None}
    handoff = attempt_dir / "handoff"
    if handoff.is_symlink():
        return {"stat": None}
    manifest_raw = _read_review_file(handoff / "manifest.json")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8")) if manifest_raw else {}
    except (UnicodeError, ValueError):
        manifest = {}
    patch = _read_review_file(handoff / "changes.patch", _REVIEW_OUTPUT_MAX)
    stat_text = None
    if patch is not None:
        try:
            result = subprocess.run(["git", "apply", "--stat"], input=patch, capture_output=True,
                                    timeout=_REVIEW_DIFF_TIMEOUT, check=False)
            if result.returncode == 0:
                stat_text = result.stdout.decode("utf-8", errors="replace").strip()[:4000]
        except (OSError, subprocess.TimeoutExpired):
            pass
    changed = manifest.get("changed") if isinstance(manifest, dict) else None
    files = [item for item in changed[:200] if isinstance(item, str)] if isinstance(changed, list) else []
    total = manifest.get("changed_total") if isinstance(manifest, dict) else None
    if stat_text is None and isinstance(total, int) and not isinstance(total, bool) and total >= 0:
        stat_text = f"{total} files changed" if total != 1 else "1 file changed"
    return {"stat": stat_text, "files": files}


def _failure_review(target: str, attempt_id: str) -> dict | None:
    """Build the failure read model from Scheduler facts and the attempt's durable evidence."""
    import bt_attempt_facts
    import bt_plans_api
    import bt_remote_events

    try:
        _, _, rdir = _commands._run_target(target)
    except (ValueError, OSError, bt_plans_api.PlanError):
        return None
    facts = bt_attempt_facts.attempt_facts(rdir)
    found = next(((task_id, row) for task_id, rows in facts.items()
                  for row in rows if row.get("attempt") == attempt_id), None)
    if found is None:
        return None
    _, attempt = found
    if attempt.get("state") not in {"failed", "rejected"} and not attempt.get("failure"):
        return None
    attempt_dir = _review_executor_attempt(rdir, attempt_id)
    result, artifacts = _review_quality_result(rdir, attempt_id)
    log_bytes = _tail_review_file(attempt_dir / "output.tail") if attempt_dir else None
    if log_bytes is None and attempt_dir:
        log_bytes = _tail_review_file(attempt_dir / "output.log")
    log_tail = (log_bytes or b"").decode("utf-8", errors="replace").splitlines()[-200:]
    review = {"attemptId": attempt_id, "cause": attempt.get("failure") or attempt.get("state") or "unknown",
              "verification": _review_verification(result, artifacts), "diff": _review_diff(attempt_dir),
              "logTail": "\n".join(log_tail)}
    return bt_remote_events.redact(review)

HANDLERS: dict = _commands.dispatch_handlers()
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "COMMAND_NOT_IMPLEMENTED": 501,
                   "STALE_PRECONDITION": 409, "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409,
                   "EFFECT_FAILED": 500, "ROUTE_UNAVAILABLE": 422, "STATE_UNAVAILABLE": 503,
                   "CONFIRMATION_REQUIRED": 409}


def _target_state(target: str, command: str | None = None, params: dict | None = None) -> dict | None:
    """Resolve the live target state used to validate remote command preconditions."""
    return _commands.target_state(target, command, params)


def _submit_command(handler, length: int) -> None:
    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_COMMAND", "El cuerpo debe ser JSON válido.")
    result = _commands.Ledger().submit(request, HANDLERS, _target_state)
    status = _COMMAND_STATUS.get(result.get("code") or result["status"], 200)
    _send_json(handler, result, status)


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    if _path(handler) == f"{PREFIX}/commands":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except (AttributeError, ValueError):
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_COMMAND", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        return _submit_command(handler, length)
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
