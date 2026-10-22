"""Journaled recovery revision application outside M1."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import bt_recovery_authorization as authorization
import bt_recovery_cycle

JOURNAL = "RUN.recovery-apply.json"
DEFAULT_BARRIER_SECONDS = 60.0


class RecoveryApplyError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryApplyError("JOURNAL_UNREADABLE", f"recovery journal is unreadable: {type(exc).__name__}") from exc
    if not isinstance(data, dict) or data.get("schema") != "recovery-apply/1":
        raise RecoveryApplyError("JOURNAL_UNREADABLE", "recovery journal schema is invalid")
    return data


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    if os.name != "nt":
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _record_blocker(path: Path, grant: dict, grant_key: str, reason: str) -> dict:
    journal = {"schema": "recovery-apply/1", "journal_path": str(path), "stage": "blocked",
               "grant_key": grant_key, "case_id": grant.get("case_id"), "cycle_token": grant.get("cycle_token"),
               "source_sha256": grant.get("source_sha256"), "target_sha256": grant.get("target_sha256"),
               "accepted_map_digest": grant.get("accepted_map_digest"), "base_digest": grant.get("base_digest"),
               "stop_generation": grant.get("stop_generation"), "blocker": reason}
    _write(path, journal)
    return {"status": "blocked", "reason": reason}


def journal_path(rdir: str | Path) -> Path:
    import bt_scheduler_adapter

    return bt_scheduler_adapter.run_db_path(Path(rdir)).with_name(JOURNAL)


def _plan_hash(plan: dict) -> str:
    import bt_plan_adapter

    return hashlib.sha256(bt_plan_adapter.planner_contract.dumps(plan).encode("utf-8")).hexdigest()


def _compiled_payload(compiled: Any) -> dict[str, Any] | None:
    if isinstance(compiled, dict):
        data = dict(compiled)
        verification_map = data.get("verification_map")
        mapped_paths = verification_map.get("changed_paths", []) if isinstance(verification_map, dict) else []
        if "actual_changed_paths" not in data and isinstance(mapped_paths, list):
            actual_paths = [row["path"] for row in mapped_paths if isinstance(row, dict)
                            and isinstance(row.get("path"), str)]
            if actual_paths:
                data["actual_changed_paths"] = actual_paths
        if not isinstance(data.get("verdicts"), list) or not data["verdicts"]:
            data["verdicts"] = _verification_verdict_ids(verification_map)
        return data
    plan = getattr(compiled, "plan", None)
    scope = getattr(compiled, "scope", None)
    verification_map = getattr(compiled, "verification_map", None)
    if not isinstance(plan, dict) or not isinstance(scope, (tuple, list)) or not isinstance(verification_map, dict):
        return None
    mapped_paths = verification_map.get("changed_paths", []) if isinstance(verification_map, dict) else []
    actual_paths = [row["path"] for row in mapped_paths if isinstance(row, dict) and isinstance(row.get("path"), str)]
    verdicts = getattr(compiled, "verdicts", None)
    if not isinstance(verdicts, list) or not verdicts:
        verdicts = _verification_verdict_ids(verification_map)
    return {"plan": plan, "scope": list(scope), "verification_map": verification_map,
            "changed_paths": actual_paths, "actual_changed_paths": actual_paths,
            "proposal_hash": getattr(compiled, "proposal_hash", None),
            "source_sha256": getattr(compiled, "source_sha256", None),
            "case_id": getattr(compiled, "case_id", None), "cycle_token": getattr(compiled, "cycle_token", None),
            "lineage": getattr(compiled, "lineage", {}), "verdicts": verdicts,
            "oracle_provenance": getattr(compiled, "oracle_provenance", None),
            "supplementary_audit_grant_key": getattr(compiled, "supplementary_audit_grant_key", None),
            "audit_lineage": getattr(compiled, "audit_lineage", None)}


def _verification_verdict_ids(verification_map: Any) -> list[str]:
    if not isinstance(verification_map, dict):
        return []
    checks = verification_map.get("checks", [])
    if isinstance(checks, list) and checks:
        return sorted({row["verdict_identity"] for row in checks if isinstance(row, dict)
                       and isinstance(row.get("verdict_identity"), str)})
    return sorted({identity for values in verification_map.values() if isinstance(values, list)
                   for identity in values if isinstance(identity, str)})


def _wait(reason: str, live_attempts: list[str], stop_generation: int, journal: dict) -> dict:
    journal.update(stage="frozen", wait={"reason": reason, "live_attempts": list(live_attempts),
                                         "stop_generation": stop_generation, "at": time.time()})
    _write(Path(journal["journal_path"]), journal)
    return {"status": "waiting", **journal["wait"]}


def _clear_stale_recovery_hold(rdir: Path) -> None:
    import bt_scheduler_ops

    hold = bt_scheduler_ops.hold_path(rdir)
    try:
        data = json.loads(hold.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return
    except (OSError, UnicodeError, json.JSONDecodeError):
        return
    if not isinstance(data, dict) or data.get("why") != "recovery revision" or type(data.get("pid")) is not int:
        return
    try:
        os.kill(data["pid"], 0)
    except ProcessLookupError:
        hold.unlink(missing_ok=True)
    except PermissionError:
        return


def apply_recovery_revision(rdir: str | Path, compiled: dict, grant_key: str, *,
                            current_base: Callable[[], str], barrier_seconds: float = DEFAULT_BARRIER_SECONDS,
                            crash_hook: Callable[[str], None] | None = None) -> dict:
    """Freeze and apply one grant-bound plan revision; retrying resumes from the durable journal."""
    import bt_plan_adapter
    import bt_scheduler_adapter
    import bt_scheduler_ops
    import bt_scheduler_run

    rdir = Path(rdir)
    path = journal_path(rdir)
    grant = authorization.open_for_run(rdir).get("task", grant_key)
    ledger = authorization.open_for_run(rdir)
    compiled_data = _compiled_payload(compiled)
    if compiled_data is None or not isinstance(compiled_data.get("plan"), dict):
        raise RecoveryApplyError("INVALID_COMPILED_PLAN", "compiled recovery input must contain a plan")
    compiled = compiled_data
    plan = compiled["plan"]
    scope = compiled.get("scope", grant.get("scope"))
    if not isinstance(scope, (list, tuple)) or not scope or any(not isinstance(item, str) for item in scope):
        raise RecoveryApplyError("INVALID_SCOPE", "compiled recovery scope is missing")
    scope = list(scope)
    if grant.get("scope") != scope:
        raise RecoveryApplyError("GRANT_SCOPE_MISMATCH", "compiled scope differs from its authorization")
    if compiled.get("proposal_hash") != grant.get("proposal_hash"):
        raise RecoveryApplyError("PROPOSAL_HASH_MISMATCH", "compiled proposal does not match its grant")
    if (compiled.get("source_sha256"), compiled.get("case_id"), compiled.get("cycle_token")) != \
            (grant.get("source_sha256"), grant.get("case_id"), grant.get("cycle_token")):
        raise RecoveryApplyError("COMPILED_IDENTITY_MISMATCH", "compiled case, cycle or source differs from its grant")
    audit_grant_key = compiled.get("supplementary_audit_grant_key")
    audit_grant = None
    if audit_grant_key is not None:
        audit_grant = ledger.get("supplementary_audit", audit_grant_key)
        expected_audit = {"case_id": grant.get("case_id"), "cycle_token": grant.get("cycle_token"),
                          "stop_generation": grant.get("stop_generation"),
                          "accepted_map_digest": grant.get("accepted_map_digest"),
                          "base_digest": grant.get("base_digest")}
        if any(audit_grant.get(name) != value for name, value in expected_audit.items()) or \
                audit_grant.get("audit_lineage") != compiled.get("audit_lineage"):
            raise RecoveryApplyError("AUDIT_GRANT_MISMATCH", "supplementary audit grant does not match this recovery cycle")
    if len(bt_recovery_cycle.corrective_tasks(plan)) > bt_recovery_cycle.POLICY["max_corrective_tasks"]:
        raise RecoveryApplyError("CORRECTIVE_LIMIT", "the plan adds more corrective tasks than a recovery cycle allows")
    plan_hash = _plan_hash(plan)
    if plan_hash != grant.get("target_sha256"):
        raise RecoveryApplyError("TARGET_HASH_MISMATCH", "compiled plan does not match its grant")
    _clear_stale_recovery_hold(rdir)
    if bt_scheduler_ops.on_hold(rdir):
        return {"status": "blocked", "reason": "run is already on hold"}

    identity = bt_scheduler_adapter.revision_identity(rdir)
    journal = _read(path)
    if journal and (journal.get("grant_key"), journal.get("source_sha256"), journal.get("target_sha256")) != \
            (grant_key, grant["source_sha256"], grant["target_sha256"]):
        return {"status": "blocked", "reason": "a different recovery revision owns the journal"}
    if journal and journal.get("stage") == "blocked":
        return {"status": "blocked", "reason": journal.get("blocker", "recovery application is blocked")}
    if journal is None:
        try:
            base = current_base()
        except Exception as error:  # noqa: BLE001 - failure to revalidate must not authorize a revision
            return _record_blocker(path, grant, grant_key,
                                  f"current integration base is unavailable ({type(error).__name__})")
        if base != grant.get("base_digest"):
            return _record_blocker(path, grant, grant_key, "current integration base differs from the grant")
        if identity["paused"] or identity["cancelled"]:
            return _record_blocker(path, grant, grant_key, "M1 is paused or cancelled")
        if (identity["source_sha256"], identity["accepted_map_digest"], identity["stop_generation"]) != \
                (grant.get("source_sha256"), grant.get("accepted_map_digest"), grant.get("stop_generation")):
            return _record_blocker(path, grant, grant_key, "stale source, accepted map or stop generation")
        journal = {"schema": "recovery-apply/1", "journal_path": str(path), "stage": "prepared",
                   "grant_key": grant_key, "case_id": grant["case_id"], "cycle_token": grant["cycle_token"],
                   "source_sha256": grant["source_sha256"], "target_sha256": grant["target_sha256"],
                   "accepted_map_digest": grant["accepted_map_digest"], "base_digest": grant["base_digest"],
                   "stop_generation": grant["stop_generation"], "scope": scope, "plan": plan,
                   "plan_hash": plan_hash, "barrier_expiries": 0}
        _write(path, journal)
        if crash_hook:
            crash_hook("prepared")
    elif journal.get("plan_hash") != plan_hash:
        journal.update(stage="blocked", blocker="compiled plan changed since journal preparation")
        _write(path, journal)
        return {"status": "blocked", "reason": journal["blocker"]}

    if journal.get("stage") not in {"applied", "rebound", "committed"} and (identity["paused"] or identity["cancelled"]):
        bt_scheduler_adapter.abort_revision_barrier(rdir, grant_key, "run_paused_or_cancelled")
        journal.update(stage="blocked", blocker="M1 is paused or cancelled")
        _write(path, journal)
        return {"status": "blocked", "reason": journal["blocker"]}

    if journal.get("stage") == "committed":
        return journal["receipt"]
    if journal.get("stage") not in {"applied", "rebound"} and identity["source_sha256"] == grant["target_sha256"]:
        journal["stage"] = "applied"
        journal["rebase_report"] = {"adopted_after_restart": True}
        _write(path, journal)
    elif journal.get("stage") not in {"applied", "rebound"} and (
            identity["source_sha256"] != grant.get("source_sha256") or
            identity["stop_generation"] != grant.get("stop_generation") or
            (not journal.get("wait") and identity["accepted_map_digest"] != grant.get("accepted_map_digest"))):
        bt_scheduler_adapter.abort_revision_barrier(rdir, grant_key, "stale_recovery_identity")
        journal.update(stage="blocked", blocker="stale source, accepted map or stop generation")
        _write(path, journal)
        return {"status": "blocked", "reason": "stale source, accepted map or stop generation"}
    if journal.get("stage") not in {"applied", "rebound"} and not journal.get("wait"):
        try:
            base_matches = current_base() == grant.get("base_digest")
        except Exception as error:  # noqa: BLE001 - persist a closed blocker for a failed external read
            base_matches, base_error = False, type(error).__name__
        else:
            base_error = ""
        if not base_matches:
            bt_scheduler_adapter.abort_revision_barrier(rdir, grant_key, "stale_integration_base")
            blocker = (f"current integration base is unavailable ({base_error})" if base_error
                       else "current integration base differs from the grant")
            journal.update(stage="blocked", blocker=blocker)
            _write(path, journal)
            return {"status": "blocked", "reason": blocker}

    revisions = bt_plan_adapter.revisions(rdir)
    frozen = next((item for item in revisions if item.get("sha256") == plan_hash), None)
    if journal.get("stage") == "prepared":
        frozen = frozen or bt_plan_adapter.freeze_revision(rdir, plan, "recovery")
        journal.update(stage="frozen", frozen_revision=frozen["revision"])
        _write(path, journal)
        if crash_hook:
            crash_hook("frozen")
    elif frozen is None:
        journal.update(stage="blocked", blocker="journaled frozen revision is missing")
        _write(path, journal)
        return {"status": "blocked", "reason": journal["blocker"]}

    latest = bt_plan_adapter.latest_plan(rdir)
    if not latest or _plan_hash(latest) != plan_hash:
        journal.update(stage="blocked", blocker="frozen recovery revision is not latest")
        _write(path, journal)
        return {"status": "blocked", "reason": journal["blocker"]}
    old_plan = bt_scheduler_adapter.revision_plan(rdir, identity["revision"], identity["source_sha256"], identity["plan_id"])
    new_plan = bt_scheduler_adapter.approved_plan(rdir)
    if journal.get("stage") in {"applied", "rebound", "committed"}:
        if identity["source_sha256"] == grant["target_sha256"]:
            applied = {"status": "applied", "report": journal.get("rebase_report", {})}
        else:
            return {"status": "blocked", "reason": "journal says applied but M1 identity does not match"}
    else:
        remaining_expiries = journal.get("barrier_expiries", 0)
        deadline = time.time() + max(0.1, barrier_seconds)
        if remaining_expiries:
            journal["barrier_expiries"] = remaining_expiries
        project = rdir.parent.parent.name if rdir.parent.name == "requirements" else ""
        req = rdir.name
        operator_stop = False
        _clear_stale_recovery_hold(rdir)
        if bt_scheduler_ops.on_hold(rdir):                 # a stop landed after the first check: it must not be overwritten
            journal.update(stage="blocked", blocker="operator stop requested during recovery application")
            _write(path, journal)
            return {"status": "blocked", "reason": journal["blocker"],
                    "stop_generation": bt_scheduler_adapter.revision_identity(rdir)["stop_generation"]}
        with bt_scheduler_ops.hold(rdir, "recovery revision") as recovery_hold_token:
            if project:
                bt_scheduler_ops.stop_owner(project, req)
            def guarded_base() -> str:
                nonlocal operator_stop
                value = current_base()
                if recovery_hold_token is not None and not bt_scheduler_ops.owns_hold(rdir, recovery_hold_token):
                    operator_stop = True
                    return "operator-hold-changed"
                return value

            applied = bt_scheduler_adapter.apply_plan_revision(rdir, old_plan, new_plan, {
                "operation_key": grant_key, "source_sha256": grant["source_sha256"],
                "target_sha256": grant["target_sha256"], "accepted_map_digest": grant["accepted_map_digest"],
                "base_digest": grant["base_digest"], "stop_generation": grant["stop_generation"],
                "scope": scope, "barrier_deadline": deadline, "current_base": guarded_base,
            })
        if operator_stop:
            bt_scheduler_adapter.apply_control(rdir, "stop", by=bt_scheduler_ops.OPERATOR)
            journal.update(stage="blocked", blocker="operator stop requested during recovery application")
            _write(path, journal)
            return {"status": "blocked", "reason": journal["blocker"],
                    "stop_generation": bt_scheduler_adapter.revision_identity(rdir)["stop_generation"]}
        if applied.get("status") == "waiting":
            if applied.get("reason") == "barrier_expired":
                count = int(journal.get("barrier_expiries", 0)) + 1
                journal["barrier_expiries"] = count
                if count >= 2:
                    bt_scheduler_adapter.abort_revision_barrier(rdir, grant_key, "revision_quiescence_timeout")
                    journal.update(stage="blocked", blocker="revision_quiescence_timeout")
                    _write(path, journal)
                    return {"status": "blocked", "reason": "revision_quiescence_timeout",
                            "live_attempts": applied.get("live_attempts", []),
                            "stop_generation": applied.get("stop_generation")}
                journal["wait"] = {"reason": "barrier_expired", "live_attempts": applied.get("live_attempts", []),
                                   "stop_generation": applied.get("stop_generation")}
                _write(path, journal)
                return {"status": "waiting", **journal["wait"]}
            return _wait(applied.get("reason", "live_attempts"), applied.get("live_attempts", []),
                         applied.get("stop_generation", identity["stop_generation"]), journal)
        if applied.get("status") not in {"applied", "adopted"}:
            journal.update(stage="blocked", blocker=applied.get("reason", "revision_application_refused"))
            _write(path, journal)
            return {"status": "blocked", "reason": journal["blocker"],
                    "stop_generation": applied.get("stop_generation", identity["stop_generation"])}
        if crash_hook:
            crash_hook("after_m1_apply_before_journal")
        journal.update(stage="applied", rebase_report=applied["report"].__dict__ if hasattr(applied.get("report"), "__dict__")
                       else applied.get("report", {}))
        _write(path, journal)
        if crash_hook:
            crash_hook("applied")

    ledger.consume("task", grant_key, "recovery-apply:" + grant_key)
    if audit_grant is not None:
        audit_consumer = f"supplementary-audit:{audit_grant['audit_lineage']}:{audit_grant['cycle_token']}"
        ledger.consume("supplementary_audit", audit_grant_key, audit_consumer)
    bt_scheduler_run.rebind_runtime(rdir)
    journal["stage"] = "rebound"
    _write(path, journal)
    if crash_hook:
        crash_hook("rebound")
    receipt = {"schema": "recovery-application-receipt/1", "grant_key": grant_key, "case_id": grant["case_id"],
               "cycle_token": grant["cycle_token"], "source_sha256": grant["source_sha256"],
               "target_sha256": grant["target_sha256"], "proposal_hash": grant["proposal_hash"],
               "accepted_map_digest": grant["accepted_map_digest"], "base_digest": grant["base_digest"],
               "stop_generation": grant["stop_generation"], "scope": scope,
               "supplementary_audit_grant_key": audit_grant_key,
               "lineage": compiled.get("lineage") or {"case_id": grant["case_id"],
                                                        "cycle_token": grant["cycle_token"],
                                                        "proposal_hash": grant["proposal_hash"]},
               "verdicts": compiled.get("verdicts", []),
               "changed_paths": compiled.get("changed_paths", []),
               "actual_changed_paths": compiled.get("actual_changed_paths", compiled.get("changed_paths", [])),
               "verification_map": compiled.get("verification_map", {}),
               "oracle_provenance": compiled.get("oracle_provenance")}
    journal.update(stage="committed", receipt=receipt)
    _write(path, journal)
    return receipt


def closure_problem(receipt: dict, verdicts: list[dict]) -> str | None:
    """Refuse closure unless every actual changed path has independent verification and oracle provenance."""
    if not isinstance(receipt, dict) or not isinstance(verdicts, list):
        return "receipt or verdicts are malformed"
    lineage = receipt.get("lineage")
    receipt_verdicts = receipt.get("verdicts")
    if not isinstance(lineage, dict) or not lineage or not isinstance(receipt_verdicts, list) or not receipt_verdicts:
        return "receipt lacks recovery lineage or verdict identities"
    recorded_ids = {item.get("identity") for item in receipt_verdicts if isinstance(item, dict)} | \
        {item for item in receipt_verdicts if isinstance(item, str)}
    if not recorded_ids:
        return "receipt lacks recovery lineage or verdict identities"
    mapping = receipt.get("verification_map")
    changed = receipt.get("actual_changed_paths", receipt.get("changed_paths"))
    if (not isinstance(mapping, dict) or not isinstance(changed, list) or not changed
            or any(not isinstance(path, str) or not path for path in changed)
            or len(changed) != len(set(changed))):
        return "changed paths or verification map are missing"
    by_id = {item.get("identity"): item for item in verdicts if isinstance(item, dict) and
             item.get("independent") is True and (item.get("accepted") is True or item.get("passed") is True)}
    if mapping.get("schema_version") == "recovery-verification-map/1":
        mapped_rows, checks = mapping.get("changed_paths"), mapping.get("checks")
        if (not isinstance(mapped_rows, list) or not isinstance(checks, list)
                or any(not isinstance(row, dict) or not isinstance(row.get("path"), str)
                       for row in mapped_rows)
                or {row["path"] for row in mapped_rows} != set(changed)
                or len(mapped_rows) != len(changed)):
            return "changed paths or verification map are missing"
        owners_by_path = {row["path"]: row.get("owner_task_id") for row in mapped_rows if isinstance(row, dict)}
        for path in changed:
            owner = owners_by_path[path]
            required = [row for row in checks if isinstance(row, dict) and row.get("owner_task_id") == owner]
            if not required or any(not isinstance(row.get("command"), str)
                                   or row.get("verdict_identity") not in by_id for row in required):
                return f"changed path lacks independent verification: {path}"
    else:
        uses_surface_checks = isinstance(mapping.get("surface_checks"), dict)
        surface_checks = mapping["surface_checks"] if uses_surface_checks else mapping
        for path in changed:
            required = surface_checks.get(path)
            if not isinstance(required, list) or not required:
                return f"changed path lacks independent verification: {path}"
            if uses_surface_checks and all(isinstance(item, str) for item in required):
                verified = {item.get("command") for item in by_id.values() if isinstance(item.get("command"), str)}
                if any(command not in verified for command in required):
                    return f"changed path lacks independent verification: {path}"
            elif any(identity not in by_id for identity in required):
                return f"changed path lacks independent verification: {path}"
    if not set(by_id) & recorded_ids:
        return "receipt verdict identities do not match independent verdicts"
    oracle = receipt.get("oracle_provenance")
    if not isinstance(oracle, dict):
        return "oracle red/green provenance is missing or unreproducible"
    red, green = oracle.get("red"), oracle.get("green")
    if not isinstance(red, dict) or not isinstance(green, dict):
        return "oracle red/green provenance is missing or unreproducible"
    valid_hash = lambda value: isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    if (not red.get("identity") or not green.get("identity") or not valid_hash(red.get("source_sha256")) or
            not valid_hash(green.get("source_sha256")) or not valid_hash(red.get("output_sha256")) or
            not valid_hash(green.get("output_sha256")) or type(red.get("exit_code")) is not int or red["exit_code"] == 0 or
            green.get("exit_code") != 0 or red.get("source") != "captured_broken_source" or
            red.get("overlay_only") is not True or green.get("source") != "corrected_integrated_tree"):
        return "oracle red/green provenance is missing or unreproducible"
    return None


def replan_closure_verification(receipt: dict, plan: dict) -> list[dict] | dict:
    """Ask T4b to add deterministic checks for newly observed paths, preserving the case and grant identities."""
    if not isinstance(receipt, dict) or not isinstance(plan, dict):
        return {"code": "INVALID_RECEIPT", "message": "receipt and plan are required"}
    import bt_recovery_compiler

    result = bt_recovery_compiler.replan_verification(
        plan, receipt.get("verification_map"), receipt.get("actual_changed_paths", receipt.get("changed_paths")))
    if isinstance(result, bt_recovery_compiler.RecoveryRefusal):
        return {"code": result.code, "message": result.message}
    return {"schema": "recovery-verification-replan/1", "case_id": receipt.get("case_id"),
            "cycle_token": receipt.get("cycle_token"), "grant_key": receipt.get("grant_key"),
            "checks": result, "criteria_preserved": True, "grant_preserved": True}
